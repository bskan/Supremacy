#!/usr/bin/env python3
"""
Supremacy Game CLI Interface
=============================
Main command-line interface for the Supremacy Game simulation.

Screens (as per original design):
1. Docking Bay - Ship movement and fleet management
2. Purchase Assets & Infrastructure - Browse catalog and buy items
3. Planet Details View - Full planet information with resources
4. Military Platoon Management - Equipment and military training
5. Cargo Management / Assignment - Ship loading and fuel transfer
6. Surface Assignments - Farming/mining ship deployment
7. Battle Screen - Combat resolution
8. Save & Exit - Persist game state

Usage:
    python3 supremacy_cli.py
"""

import os
from game_engine import (
    get_db_connection,
    calculate_resource_flow,
    process_ship_movement,
    resolve_combat,
    init_default_game,
    get_planet_state,
    get_player_overview,
    get_all_planets,
    get_fleet_inventory,
    get_astro_survey,
    get_system_planet_list,
    DEFAULT_DB_CONFIG,
    # New helper functions
    run_turn,
    get_player_credits,
    get_player_assets,
    get_first_owned_planet_id,
    get_asset_by_name,
    has_player_owned_asset,
    adjust_resource_level,
    add_credits_to_player,
    get_player_over_planets,
    get_all_systems,
    get_fleet_at_planet,
)


# Global game state - will be populated on first connection
game_state = {
    "conn": None,
    "active_planet_id": 1,
    "player_credits": None,
    "active_system_id": 1
}


def connect_to_database():
    """Establish database connection and initialize game state."""
    from mysql.connector import Error

    conn = get_db_connection(
        host=DEFAULT_DB_CONFIG["host"],
        user=DEFAULT_DB_CONFIG["user"],
        password=None,
        port=DEFAULT_DB_CONFIG["port"],
        database="supremacy_game"
    )

    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM supremacy_game.planets LIMIT 1")
        except Exception:
            cursor.execute("USE supremacy_game")
        cursor.fetchall()
        cursor.close()

        game_state["conn"] = conn
        return game_state["conn"]
    return None


def handle_docking_bay():
    """
    Screen 1: Docking Bay Management

    Handle ship movement, fleet assignment, and docking operations.
    """
    print("\n" + "=" * 50)
    print("      DOCKING BAY (Screen 1)")
    print("=" * 50)

    cursor = game_state["conn"].cursor()

    # Get fleet inventory at active planet
    active_planet_id = game_state.get('active_planet_id', 1)
    cursor.execute("""
        SELECT s.ship_type, COUNT(*) as count
        FROM ships s
        WHERE s.planet_id = %s
        GROUP BY s.ship_type
    """, (active_planet_id,))

    fleet = cursor.fetchall()

    if fleet:
        print("\nCurrent Fleet at Planet:")
        for ship_type, count in fleet:
            print(f"  {ship_type:<20}: {count} ships")
    else:
        print("  No ships currently docked here.")

    cursor.close()

    # Show available docking bays (all planets)
    cursor = game_state["conn"].cursor()
    cursor.execute("""
        SELECT p.planet_id, p.name FROM planets p
        WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
    """)

    planets = cursor.fetchall()
    print("\nYour Planets:")
    for planet_data in planets:
        planet_id, name = planet_data
        print(f"  - {name} (ID: {planet_id})")

    cursor.close()

    print("\nAvailable Actions:")
    print("  [1] View fleet at all planets")
    print("  [2] Return to Home Menu")
    action = input("\nEnter choice: ").strip()

    if action == "1":
        # View fleet at all planets
        cursor = game_state["conn"].cursor()
        cursor.execute("""
            SELECT s.planet_id, p.name as planet_name, ship_type, COUNT(*) as count
            FROM ships s
            JOIN planets p ON s.planet_id = p.planet_id
            WHERE s.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            GROUP BY s.planet_id, p.name, s.ship_type
            ORDER BY s.planet_id, ship_type
        """)

        all_fleet = cursor.fetchall()
        if all_fleet:
            print("\nFleet Overview:")
            for data in all_fleet:
                planet_id, name, ship_type, count = data
                print(f"  {name}: {count}x {ship_type}")
        else:
            print("\nNo ships owned yet. Use Purchase Assets to acquire ships.")

    elif action == "2":
        pass

    cursor.close()


def handle_purchase_assets():
    """
    Screen 2: Purchase Assets & Infrastructure

    Browse asset catalog and purchase ships, infrastructure, equipment.
    """
    cursor = game_state["conn"].cursor()

    print("\n" + "=" * 50)
    print("   PURCHASE ASSETS & INFRASTRUCTURE (Screen 2)")
    print("=" * 50)

    # Show player credits
    cursor.execute("SELECT credits FROM users WHERE username = 'Player'")
    row = cursor.fetchone()
    credits = row[0] if row else 0
    print(f"\nAvailable Credits: {credits:,}")
    cursor.close()

    # Display available assets (ships)
    cursor = game_state["conn"].cursor()
    cursor.execute("""
        SELECT name, category, base_cost FROM supremacy_game.assets_catalog
        WHERE category = 'Ship' ORDER BY base_cost
    """)
    ships = cursor.fetchall()

    print("\n--- Available Ships ---")
    for ship in ships:
        name, category, cost = ship
        available = credits >= cost
        status = "[AVAILABLE]" if available else "[OUT OF CREDITS]"
        print(f"  {name:<20} ({category}): ${cost:>6,}{status}")

    # Display infrastructure options
    cursor.execute("""
        SELECT name, category, base_cost FROM supremacy_game.assets_catalog
        WHERE category = 'Infrastructure' ORDER BY base_cost
    """)
    infra = cursor.fetchall()

    print("\n--- Available Infrastructure ---")
    for item in infra:
        name, category, cost = item
        available = credits >= cost
        status = "[AVAILABLE]" if available else "[OUT OF CREDITS]"
        print(f"  {name:<20} ({category}): ${cost:>6,}{status}")

    # Display equipment options
    cursor.execute("""
        SELECT name, category, base_cost FROM supremacy_game.equipment_catalog ORDER BY base_cost
    """)
    equipment = cursor.fetchall()

    print("\n--- Available Equipment ---")
    for item in equipment:
        name, category, cost = item
        available = credits >= cost
        status = "[AVAILABLE]" if available else "[OUT OF CREDITS]"
        print(f"  {name:<20} ({category}): ${cost:>6,}{status}")

    print("\nAvailable Actions:")
    print("  [1] Purchase a Ship")
    print("  [2] Purchase Infrastructure")
    print("  [3] Purchase Equipment")
    print("  [4] Return to Home Menu")

    action = input("\nEnter choice: ").strip()

    if action == "1":
        # Pick a ship to purchase
        cursor.execute("""
            SELECT name, base_cost FROM supremacy_game.assets_catalog
            WHERE category = 'Ship' ORDER BY base_cost
        """)
        ships = cursor.fetchall()
        print("\nAvailable Ships:")
        for i, (name, cost) in enumerate(ships, 1):
            available = credits >= cost
            status = "[AVAILABLE]" if available else "[OUT OF CREDITS]"
            print(f"  {i}. {name:<20} ({cost:>8,} credits) {status}")
        choice = input(f"\nEnter ship number [1-{len(ships)}] (or 0 to cancel): ").strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(ships):
                name, cost = ships[idx - 1]
                if credits >= cost:
                    # Get the first owned planet to attach the asset to
                    cursor.execute("""
                        SELECT planet_id FROM planets
                        WHERE owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
                        ORDER BY planet_id LIMIT 1
                    """)
                    planet_row = cursor.fetchone()
                    planet_id = planet_row[0] if planet_row else 1

                    cursor.execute("UPDATE users SET credits = credits - %s WHERE username = 'Player'", (cost,))
                    game_state["conn"].commit()

                    cursor.execute("""
                        INSERT INTO planetary_assets (planet_id, asset_name, asset_type, quantity, base_cost)
                        VALUES (%s, %s, %s, 1, %s)
                        ON DUPLICATE KEY UPDATE quantity = quantity + 1
                    """, (planet_id, name, 'Ship', cost))
                    game_state["conn"].commit()

                    # Update local credits
                    cursor.execute("SELECT credits FROM users WHERE username = 'Player'")
                    credits = cursor.fetchone()[0]
                    print(f"\nPurchased {name}! Remaining credits: {credits:,}")
                else:
                    print("Not enough credits!")
        except (ValueError, IndexError):
            pass

    elif action == "2":
        # Pick infrastructure to purchase
        cursor.execute("""
            SELECT name, base_cost FROM supremacy_game.assets_catalog
            WHERE category = 'Infrastructure' ORDER BY base_cost
        """)
        infra = cursor.fetchall()
        print("\nAvailable Infrastructure:")
        for i, (name, cost) in enumerate(infra, 1):
            available = credits >= cost
            status = "[AVAILABLE]" if available else "[OUT OF CREDITS]"
            print(f"  {i}. {name:<20} ({cost:>8,} credits) {status}")
        choice = input(f"\nEnter infrastructure number [1-{len(infra)}] (or 0 to cancel): ").strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(infra):
                name, cost = infra[idx - 1]
                if credits >= cost:
                    # Check if Terraformer is already owned (one-time purchase)
                    if name == 'Terraformer':
                        cursor.execute("""
                            SELECT COUNT(*) FROM planetary_assets pa
                            JOIN planets p ON pa.planet_id = p.planet_id
                            WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
                            AND pa.asset_name = 'Terraformer'
                        """)
                        owned_count = cursor.fetchone()[0]
                        if owned_count > 0:
                            print("You already own a Terraformer. It cannot be purchased again.")
                            action = "4"
                        else:
                            # Update infrastructure on the player's colonies
                            cursor.execute("""
                                INSERT INTO colonies (planet_id, solar_satellites)
                                VALUES (1, 1)
                                ON DUPLICATE KEY UPDATE solar_satellites = solar_satellites + 1
                            """)
                            game_state["conn"].commit()

                            cursor.execute("UPDATE users SET credits = credits - %s WHERE username = 'Player'", (cost,))
                            game_state["conn"].commit()

                            cursor.execute("""
                                SELECT planet_id FROM planets
                                WHERE owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
                                ORDER BY planet_id LIMIT 1
                            """)
                            planet_row = cursor.fetchone()
                            planet_id = planet_row[0] if planet_row else 1

                            cursor.execute("""
                                INSERT INTO planetary_assets (planet_id, asset_name, asset_type, quantity, base_cost)
                                VALUES (%s, %s, %s, 1, %s)
                                ON DUPLICATE KEY UPDATE quantity = quantity + 1
                            """, (planet_id, name, 'Infrastructure', cost))
                            game_state["conn"].commit()

                            cursor.execute("SELECT credits FROM users WHERE username = 'Player'")
                            credits = cursor.fetchone()[0]
                            print(f"\nPurchased {name}! Remaining credits: {credits:,}")
                    else:
                        print("Not enough credits!")
        except (ValueError, IndexError):
            pass

    elif action == "3":
        # Pick equipment to purchase
        cursor.execute("""
            SELECT name, base_cost FROM supremacy_game.equipment_catalog ORDER BY base_cost
        """)
        equipment = cursor.fetchall()
        print("\nAvailable Equipment:")
        for i, (name, cost) in enumerate(equipment, 1):
            available = credits >= cost
            status = "[AVAILABLE]" if available else "[OUT OF CREDITS]"
            print(f"  {i}. {name:<20} ({cost:>8,} credits) {status}")
        choice = input(f"\nEnter equipment number [1-{len(equipment)}] (or 0 to cancel): ").strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(equipment):
                name, cost = equipment[idx - 1]
                if credits >= cost:
                    cursor.execute("UPDATE users SET credits = credits - %s WHERE username = 'Player'", (cost,))
                    game_state["conn"].commit()

                    cursor.execute("""
                        SELECT planet_id FROM planets
                        WHERE owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
                        ORDER BY planet_id LIMIT 1
                    """)
                    planet_row = cursor.fetchone()
                    planet_id = planet_row[0] if planet_row else 1

                    cursor.execute("""
                        INSERT INTO planetary_assets (planet_id, asset_name, asset_type, quantity, base_cost)
                        VALUES (%s, %s, %s, 1, %s)
                        ON DUPLICATE KEY UPDATE quantity = quantity + 1
                    """, (planet_id, name, 'Equipment', cost))
                    game_state["conn"].commit()

                    cursor.execute("SELECT credits FROM users WHERE username = 'Player'")
                    credits = cursor.fetchone()[0]
                    print(f"\nPurchased {name}! Remaining credits: {credits:,}")
                else:
                    print("Not enough credits!")
        except (ValueError, IndexError):
            pass


def handle_simulate_turn():
    """
    Screen 4: Simulate Turn

    Advance time and update planetary data (resource changes, etc.).
    """
    print("\n" + "=" * 50)
    print("      SIMULATE TURN (Screen 4)")
    print("=" * 50)
    print("\nSimulating game turn...")
    # TODO: Implement resource updates, ship arrivals, etc.

    cursor.close()

    print("\nReturning to main menu...")


def handle_planet_details():
    """
    Screen 3: Planet Details View

    Shows all owned planets, then displays detailed information about the selected planet.
    """
    # Get player's planets for selection
    cursor = game_state["conn"].cursor()
    cursor.execute("""
        SELECT p.planet_id, p.name, s.name as system_name
        FROM planets p
        JOIN systems s ON p.system_id = s.system_id
        WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
        ORDER BY s.name, p.planet_id
    """)

    player_planets = cursor.fetchall()

    if not player_planets:
        print("No planets owned yet. Use purchase assets screen to acquire planets.")
        return

    print("\n--- Your Planets ---")
    for idx, (planet_id, name, system_name) in enumerate(player_planets, 1):
        print(f"  [{idx}] {system_name}-{name} (ID: {planet_id})")

    selection = input("\nEnter planet number to view details: ").strip()

    if selection.isdigit():
        selected_idx = int(selection) - 1
        if 0 <= selected_idx < len(player_planets):
            planet_id = player_planets[selected_idx][0]
            display_planet_details(planet_id)


def display_planet_details(planet_id: int):
    """Display detailed information about a single planet."""
    db_conn = game_state["conn"]

    # Get complete planet state
    planet_info = get_planet_state(planet_id, db_conn)
    if not planet_info:
        print("Could not retrieve planet data.")
        return

    cursor = db_conn.cursor()

    # Header with navigation
    print("\n" + "=" * 50)
    print(f"     PLANET: {planet_info['name']} (ID: {planet_id})")
    print("=" * 50)

    # Ownership info
    owner_name = planet_info.get('owner_name', 'Neutral')
    is_owned = owner_name != 'Neutral'
    status_icon = "[OWNED]" if is_owned else "[NEUTRAL/ENEMY]"

    print(f"\nStatus: {status_icon}")

    # Population & Economy
    print(f"Population:   {planet_info.get('population', 0):,}")
    print(f"Morale:       {planet_info.get('morale', 'N/A')}")
    print(f"Tax Rate:     {planet_info.get('tax_rate', 0)*100:.1f}%")

    # Resources (from planetary_stats)
    resources = planet_info.get('resources', {})
    for res, value in resources.items():
        if value is not None:
            print(f"{res.title()} Level:   {value:,}")

    # Infrastructure (from colonies table)
    infra = planet_info.get('infrastructure', {})
    if infra:
        print("\nInfrastructure:")
        farms = infra.get('farming_stations', 0)
        mines = infra.get('mining_stations', 0)
        solar = infra.get('solar_satellites', 0)

        if farms > 0:
            print(f"  Farming Stations:   {farms}")
        if mines > 0:
            print(f"  Mining Stations:    {mines}")
        if solar > 0:
            print(f"  Solar Satellites:   {solar}")

        # Show detailed production/consumption breakdown
        cursor.execute("""
            SELECT farming_stations, mining_stations, solar_satellites, COUNT(s.ship_id) as ship_count
            FROM colonies c
            JOIN planets p ON c.planet_id = p.planet_id
            LEFT JOIN ships s ON p.planet_id = s.planet_id AND s.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            WHERE c.planet_id = %s GROUP BY c.planet_id, farming_stations, mining_stations, solar_satellites
        """, (planet_id,))
        row = cursor.fetchone()

        farming_stations = int(row[0]) if row and row[0] else 0
        mining_stations = int(row[1]) if row and row[1] else 0
        solar_satellites = int(row[2]) if row and row[2] else 0
        ship_count = int(row[3]) if row and row[3] else 0

        # Calculate detailed production/consumption
        food_produced = farming_stations * 15.0
        minerals_produced = mining_stations * 8.0
        energy_produced = solar_satellites * 12.0
        fuel_from_minerals = minerals_produced * 0.5
        fuel_from_food = food_produced * 0.2
        total_fuel_produced = fuel_from_minerals + fuel_from_food

        population = planet_info.get('population', 100)
        food_consumed = float(population) * 0.5
        energy_consumed = float(population) * 0.3 + ship_count * 2.0
        minerals_consumed = ship_count * 1.0
        fuel_consumed = ship_count * 0.8

        print(f"\nProduction per turn:")
        print(f"  Food:         +{food_produced:>6,.1f} units (from {farming_stations} farms @ 15/farm)")
        print(f"  Minerals:     +{minerals_produced:>6,.1f} units (from {mining_stations} mines @ 8/mine)")
        print(f"  Energy:       +{energy_produced:>6,.1f} units (from {solar_satellites} solar @ 12/satellite)")
        print(f"  Fuel:         +{total_fuel_produced:>6,.1f} units (from minerals & food byproducts)")

        print(f"\nConsumption per turn:")
        print(f"  Food:         {food_consumed:>6,.1f} units (population survival @ 0.5/person)")
        print(f"  Energy:       {energy_consumed:>6,.1f} units (machinery @ 0.3/person + ships @ 2/unit)")
        print(f"  Minerals:     {minerals_consumed:>6,.1f} units (ship operations @ 1/ship)")
        print(f"  Fuel:         {fuel_consumed:>6,.1f} units (ship maintenance @ 0.8/ship)")

        cursor.close()


def handle_battle_screen():
    """
    Screen 7: Battle Simulation

    Resolve combat between two planets.
    """
    print("\n" + "=" * 50)
    print("       BATTLE SIMULATION (Screen 7)")
    print("=" * 50)

    # Get all player planets via game_engine helper
    planets = get_player_over_planets(db_conn=game_state["conn"])
    if not planets:
        print("\nNo combat data available.")
        return

    # Generate battle pairs
    battle_idx = 0
    for i, attacker in enumerate(planets):
        for defender in planets:
            if attacker['id'] != defender['id']:
                battle_idx += 1
                att_fleet = get_fleet_at_planet(attacker['id'], game_state["conn"])
                att_ship_count = sum(f['count'] for f in att_fleet)

                print(f"\nBattle {battle_idx}:")
                print(f"  Attacker: {attacker['name']} (Population: {attacker['population']:,}, Ships: {att_ship_count})")
                print(f"  Defender: {defender['name']} (Population: {defender['population']:,})")

                print("\nResolved Combat:")
                result = resolve_combat(attacker['id'], defender['id'], game_state["conn"])
                for line in result.split('\n'):
                    print(f"  {line}")


def handle_fleet_overview():
    """
    Screen 9: Fleet Overview

    View all ships across your fleet.
    """
    print("\n" + "=" * 50)
    print("       FLEET OVERVIEW (Screen 9)")
    print("=" * 50)

    cursor = game_state["conn"].cursor()
    cursor.execute("""
        SELECT s.planet_id, p.name as planet_name, ship_type, COUNT(*) as count
        FROM ships s
        JOIN planets p ON s.planet_id = p.planet_id
        WHERE s.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
        GROUP BY s.planet_id, p.name, s.ship_type
        ORDER BY s.planet_id, ship_type
    """)

    all_fleet = cursor.fetchall()

    if not all_fleet:
        print("\nNo ships currently in fleet.")
    else:
        for data in all_fleet:
            planet_id, name, ship_type, count = data
            print(f"  {name}: {count}x {ship_type}")

    cursor.close()


def handle_system_list():
    """
    Screen 10: System List

    Browse all systems and planets.
    """
    print("\n" + "=" * 50)
    print("      SYSTEM LIST (Screen 10)")
    print("=" * 50)

    cursor = game_state["conn"].cursor()
    cursor.execute("""
        SELECT s.system_id, s.name, p.planet_id, p.name as planet_name
        FROM systems s
        LEFT JOIN planets p ON s.system_id = p.system_id
        WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
        ORDER BY s.name, p.planet_id
    """)

    all_planets = cursor.fetchall()

    if not all_planets:
        print("\nNo planets discovered in any system.")
    else:
        for idx, (system_id, sys_name, planet_id, pname) in enumerate(all_planets, 1):
            print(f"  [{idx}] {sys_name} (Planet {pname}, ID: {planet_id})")

    cursor.close()


def save_and_exit():
    """
    Screen 8: Save & Exit

    Persist game state and exit.
    """
    print("\nSaving game...")
    # TODO: Implement save functionality

    cursor = game_state["conn"].cursor()
    cursor.execute("SELECT 1")
    cursor.fetchall()
    cursor.close()

    print("Game saved. Exiting...")


def handle_my_assets():
    """
    Screen 12: My Assets - View all purchased assets across player planets.
    """
    print("\n" + "=" * 60)
    print("       MY PURCHASED ASSETS")
    print("=" * 60)

    cursor = game_state["conn"].cursor()
    cursor.execute("""
        SELECT pa.asset_name, pa.asset_type, pa.quantity, pa.base_cost,
               pa.planet_id, p.name as planet_name
        FROM planetary_assets pa
        JOIN planets p ON pa.planet_id = p.planet_id
        WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
        ORDER BY pa.asset_type, pa.asset_name
    """)
    rows = cursor.fetchall()
    cursor.close()

    if not rows:
        print("\nNo assets purchased yet. Visit the Purchase Assets screen to buy ships, infrastructure, or equipment.")
        return

    # Group by type
    grouped: dict[str, list] = {}
    for asset_name, asset_type, quantity, base_cost, planet_id, planet_name in rows:
        if asset_type not in grouped:
            grouped[asset_type] = []
        grouped[asset_type].append((asset_name, asset_type, quantity, base_cost, planet_id, planet_name))

    total_items = sum(len(v) for v in grouped.values())
    total_value = sum(r[2] * r[3] for r in rows)

    icons = {'Ship': '[Ship]', 'Infrastructure': '[Infra]', 'Equipment': '[Equip]'}

    for asset_type, items in sorted(grouped.items()):
        icon = icons.get(asset_type, '[?]')
        print(f"\n  --- {icon} {asset_type.upper()} ({len(items)} unique, {sum(it[2] for it in items)} total) ---")
        for name, atype, qty, cost, pid, pname in items:
            print(f"      - {name} x{qty}    ({cost:>10,} credits each) -> Planet {pid}: {pname}")

    print(f"\n  Total asset value: {total_value:>12,} credits")
    print("=" * 60)


def handle_debug_menu():
    """
    Screen 9.5: Debug Menu - Manual level setting and diagnostics

    Allows manual adjustment of resource levels for debugging purposes.
    """
    print("\n" + "=" * 60)
    print("       DEBUG MENU (Manual Level Setting)")
    print("=" * 60)

    # Get all owned planets
    cursor = game_state["conn"].cursor()
    cursor.execute("""
        SELECT p.planet_id, p.name, ps.population,
               ps.food_level, ps.energy_level, ps.fuel_level,
               ps.morale, ps.tax_rate
        FROM planets p
        JOIN planetary_stats ps ON p.planet_id = ps.planet_id
        WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
    """)

    planets = cursor.fetchall()

    if not planets:
        print("\nNo owned planets found.")
        return

    print("\n--- Owned Planets ---")
    for idx, planet in enumerate(planets, 1):
        planet_id, name, pop, food, energy, fuel, morale, tax_rate = planet
        print(f"  [{idx}] {name} (ID: {planet_id})")
        print(f"       Pop: {pop}, Food: {food}, Energy: {energy}, Fuel: {fuel}")

    cursor.close()

    # Show available debug actions
    print("\n--- Debug Actions ---")
    print("  [1] Set population manually")
    print("  [2] Set food level manually")
    print("  [3] Set energy level manually")
    print("  [4] Set fuel level manually")
    print("  [5] Reset all levels to zero")
    print("  [6] List all planets with current state")
    print("  [7] Return to Home Menu")

    action = input("\nSelect debug action [1-7]: ").strip()

    if action == "1":
        set_population()
    elif action == "2":
        set_food_level()
    elif action == "3":
        set_energy_level()
    elif action == "4":
        set_fuel_level()
    elif action == "5":
        reset_all_levels()
    elif action == "6":
        list_all_planets()
    # [7] return to menu, handled in main loop


def set_population():
    """Set population for a specific planet."""
    print("\n" + "=" * 50)
    print("  SET POPULATION")
    print("=" * 50)

    planets = get_player_over_planets(db_conn=game_state["conn"])

    if not planets:
        print("No owned planets found.")
        return

    for idx, planet in enumerate(planets, 1):
        print(f"  [{idx}] {planet['name']} (ID: {planet['id']})")

    selection = input("\nSelect planet [1-7]: ").strip()

    if selection.isdigit():
        idx = int(selection) - 1
        if 0 <= idx < len(planets):
            planet_id = planets[idx][0]

            pop_str = input(f"Enter new population for {planets[idx][1]}: ").strip()
            try:
                new_pop = int(pop_str)
                cursor.execute("UPDATE planetary_stats SET population = %s WHERE planet_id = %s", (new_pop, planet_id))
                game_state["conn"].commit()
                print(f"✓ Population set to {new_pop:,}")
            except ValueError:
                print("✗ Invalid population value. Please enter an integer.")

    cursor.close()


def set_food_level():
    """Set food level for a specific planet."""
    print("\n" + "=" * 50)
    print("  SET FOOD LEVEL")
    print("=" * 50)

    cursor = game_state["conn"].cursor()
    cursor.execute("""
        SELECT p.planet_id, p.name, ps.food_level as current_food
        FROM planets p
        JOIN planetary_stats ps ON p.planet_id = ps.planet_id
        WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
    """)
    planets = cursor.fetchall()

    for idx, planet in enumerate(planets, 1):
        pid, name, current_food = planet
        print(f"  [{idx}] {name} - Current: {current_food}")

    selection = input("\nSelect planet [1-7]: ").strip()

    if selection.isdigit():
        idx = int(selection) - 1
        if 0 <= idx < len(planets):
            planet_id = planets[idx][0]

            food_str = input(f"Enter new food level for {planets[idx][1]}: ").strip()
            try:
                new_food = float(food_str)
                cursor.execute("UPDATE planetary_stats SET food_level = %s WHERE planet_id = %s", (new_food, planet_id))
                game_state["conn"].commit()
                print(f"✓ Food level set to {new_food:.1f}")
            except ValueError:
                print("✗ Invalid food level. Please enter a number.")

    cursor.close()


def set_energy_level():
    """Set energy level for a specific planet."""
    print("\n" + "=" * 50)
    print("  SET ENERGY LEVEL")
    print("=" * 50)

    cursor = game_state["conn"].cursor()
    cursor.execute("""
        SELECT p.planet_id, p.name, ps.energy_level as current_energy
        FROM planets p
        JOIN planetary_stats ps ON p.planet_id = ps.planet_id
        WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
    """)
    planets = cursor.fetchall()

    for idx, planet in enumerate(planets, 1):
        pid, name, current_energy = planet
        print(f"  [{idx}] {name} - Current: {current_energy}")

    selection = input("\nSelect planet [1-7]: ").strip()

    if selection.isdigit():
        idx = int(selection) - 1
        if 0 <= idx < len(planets):
            planet_id = planets[idx][0]

            energy_str = input(f"Enter new energy level for {planets[idx][1]}: ").strip()
            try:
                new_energy = float(energy_str)
                cursor.execute("UPDATE planetary_stats SET energy_level = %s WHERE planet_id = %s", (new_energy, planet_id))
                game_state["conn"].commit()
                print(f"✓ Energy level set to {new_energy:.1f}")
            except ValueError:
                print("✗ Invalid energy level. Please enter a number.")

    cursor.close()


def set_fuel_level():
    """Set fuel level for a specific planet."""
    print("\n" + "=" * 50)
    print("  SET FUEL LEVEL")
    print("=" * 50)

    cursor = game_state["conn"].cursor()
    cursor.execute("""
        SELECT p.planet_id, p.name, ps.fuel_level as current_fuel
        FROM planets p
        JOIN planetary_stats ps ON p.planet_id = ps.planet_id
        WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
    """)
    planets = cursor.fetchall()

    for idx, planet in enumerate(planets, 1):
        pid, name, current_fuel = planet
        print(f"  [{idx}] {name} - Current: {current_fuel}")

    selection = input("\nSelect planet [1-7]: ").strip()

    if selection.isdigit():
        idx = int(selection) - 1
        if 0 <= idx < len(planets):
            planet_id = planets[idx][0]

            fuel_str = input(f"Enter new fuel level for {planets[idx][1]}: ").strip()
            try:
                new_fuel = float(fuel_str)
                cursor.execute("UPDATE planetary_stats SET fuel_level = %s WHERE planet_id = %s", (new_fuel, planet_id))
                game_state["conn"].commit()
                print(f"✓ Fuel level set to {new_fuel:.1f}")
            except ValueError:
                print("✗ Invalid fuel level. Please enter a number.")

    cursor.close()


def reset_all_levels():
    """Reset all resource levels to zero for all owned planets."""
    print("\n" + "=" * 50)
    print("  RESET ALL LEVELS")
    print("=" * 50)
    response = input("This will set food, energy, and fuel to 0 for all planets. Continue? [y/N]: ").strip().lower()

    if response == "y":
        cursor = game_state["conn"].cursor()
        cursor.execute("""
            UPDATE planetary_stats
            SET food_level = 0,
                energy_level = 0,
                fuel_level = 0
            WHERE planet_id IN (
                SELECT p.planet_id FROM planets p
                WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            )
        """)
        game_state["conn"].commit()
        rows_updated = cursor.rowcount
        print(f"✓ Reset {rows_updated} planets to zero resource levels.")
    else:
        print("Cancelled.")

    cursor.close()


def list_all_planets():
    """List all owned planets with current resource state."""
    print("\n" + "=" * 50)
    print("  ALL PLANETS STATUS")
    print("=" * 50)

    cursor = game_state["conn"].cursor()
    cursor.execute("""
        SELECT p.planet_id, p.name,
               ps.population, ps.food_level, ps.energy_level, ps.fuel_level,
               ps.morale
        FROM planets p
        JOIN planetary_stats ps ON p.planet_id = ps.planet_id
        WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
    """)

    planets = cursor.fetchall()

    for planet in planets:
        planet_id, name, pop, food, energy, fuel, morale = planet
        print(f"\n[{planet_id}] {name}")
        print(f"  Population:   {pop:,}")
        print(f"  Food Level:   {food:.1f}")
        print(f"  Energy Level: {energy:.1f}")
        print(f"  Fuel Level:   {fuel:.1f}")
        print(f"  Morale:       {morale}")

    cursor.close()


def simulate_turn():
    """
    Internal function to actually perform a turn (not shown in menu).

    Updates resources, handles ship arrivals, etc.
    """
    print("\nProcessing game turn...")

    result = run_turn(user_id=1, db_conn=game_state["conn"])
    print(f"\n{result.get('message', 'Turn simulation complete.')}")


def display_home_menu():
    """Display the main menu and route to appropriate handler."""
    print("\n" + "=" * 50)
    print("       SUPREMACY GAME - MAIN MENU")
    print("=" * 50)

    # Get player overview for stats
    cursor = game_state["conn"].cursor()
    cursor.execute("SELECT credits FROM users WHERE username = 'Player'")
    row = cursor.fetchone()
    credits = row[0] if row else 0

    cursor.execute("""
        SELECT p.planet_id FROM planets p
        WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
    """)
    owned_planets = cursor.fetchall()

    # Total assets owned across all planets (sum quantities)
    cursor.execute("""
        SELECT COALESCE(SUM(quantity), 0) as asset_count FROM planetary_assets pa
        JOIN planets p ON pa.planet_id = p.planet_id
        WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
    """)
    asset_count = cursor.fetchone()[0]

    cursor.close()

    print("\n=== Player Status ===")
    print(f"Owned Planets: {len(owned_planets)}")
    print(f"Assets Owned:  {asset_count}")
    print(f"Credits: {credits:,}")

    # Show available screens and newly implemented ones
    print("\n--- Available Screens ---")
    print("  [1] Docking Bay            - Ship movement & fleet management")
    print("  [2] Purchase Assets        - Browse catalog & buy ships/infrastructure")
    print("  [3] Planet Details         - View planet resources & infrastructure")
    print("  [4] Simulate Turn          - Advance time & update planetary data")
    print("  [5] Military Platoons      - Equipment training (not yet implemented)")
    print("  [6] Cargo Management       - Ship loading (not yet implemented)")
    print("  [7] Surface Assignments    - Farming/mining deployment (not yet implemented)")
    print("  [8] Battle Simulation      - Combat between planets")
    print("  [9] Save & Exit            - Persist game state")

    # Data Browsing section
    print("\n--- Data Browsing ---")
    print("  [10] Fleet Overview        - View all ships across your fleet")
    print("  [11] System List           - Browse all systems and planets")
    print("  [12] My Assets             - View all purchased assets")

    # Debug Tools (Development only)
    print("\n--- Debug Tools ---")
    print("  [13] Debug Menu            - Manual level setting & diagnostics")

    print("=" * 50)
    print("Enter screen number: ")
    print("=" * 50)

    choice = input().strip()

    # Route to appropriate handler
    handlers = {
        "1": handle_docking_bay,
        "2": handle_purchase_assets,
        "3": handle_planet_details,
        "4": simulate_turn,
        "7": handle_battle_screen,
        "9": handle_fleet_overview,
        "10": handle_fleet_overview,
        "11": handle_system_list,
        "12": handle_my_assets,
        "13": handle_debug_menu
    }

    if choice in handlers:
        handlers[choice]()
    elif choice == "9":
        save_and_exit()


def main():
    """Main CLI loop."""
    # Connect to database and initialize game state
    connect_to_database()

    # Main game loop
    while True:
        display_home_menu()


if __name__ == "__main__":
    main()
