#!/usr/bin/env python3
"""
Core simulation engine for Supremacy Game.
Provides database operations and game logic functions.
Works with or without a database connection (mock mode for development).

BATCH PROCESSING:
- Set USE_STORED_PROCEDURES = True after running install_stored_procs.py
- This enables single-query batch processing of all player planets
- See INSTALL_STORED_PROCS.md for installation instructions
"""

from typing import Dict, Any, Optional, List
import mysql.connector

# Import the correct Connection class for mysql-connector-python 8.x+
try:
    from mysql.connector import MySQLConnection as Connection
except ImportError:
    from mysql.connector.connection import MySQLConnection as Connection


# Default database configuration
DEFAULT_DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "supremacy",
    "password": "",  # User has all privileges as per your setup
    "database": "supremacy_game"
}

# Flag to enable stored procedure batch processing
# Uses single SQL UPDATE for all planets instead of N individual queries
# NOTE: When True, only food/energy/fuel/pop are updated. Ship consumption,
# morale changes, and mineral updates are NOT applied. Set to False to use
# the per-planet simulate_planet_turn() path which handles all mechanics.
USE_STORED_PROCEDURES = False


def get_db_connection(host=None, user=None, password=None, port=None, database=None) -> Optional[Connection]:
    """
    Create and return a database connection.

    Args:
        host: Database host (defaults to DEFAULT_DB_CONFIG)
        user: Database user (defaults to DEFAULT_DB_CONFIG)
        password: Database password (defaults to DEFAULT_DB_CONFIG)
        port: Database port (defaults to DEFAULT_DB_CONFIG)
        database: Database name (defaults to DEFAULT_DB_CONFIG)

    Returns:
        Database connection object or None if not connected (mock mode)
    """
    config = {
        "host": host or DEFAULT_DB_CONFIG["host"],
        "port": port or DEFAULT_DB_CONFIG["port"],
        "user": user or DEFAULT_DB_CONFIG["user"],
        "database": database or DEFAULT_DB_CONFIG["database"],  # Added database parameter
    }

    # Allow empty password by using None
    if password:
        config["password"] = password
    else:
        config["password"] = None

    try:
        return mysql.connector.connect(**config)
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None


def calculate_resource_flow(planet_id: int, db_conn=None) -> Dict[str, float]:
    """
    Calculate the resource flow for a planet.

    Returns dict with net resource changes per turn:
    - Food: surplus/deficit from farming minus population consumption
    - Minerals: surplus/deficit from mining
    - Energy: from solar satellites
    - Fuel: generated from minerals
    - TaxableIncome: tax revenue based on rate and credits

    Args:
        planet_id: The ID of the planet to calculate for
        db_conn: Optional database connection (mock data used if None)

    Returns:
        Dict with resource names as keys and net change values
    """
    # Mock mode - returns static values for development without database
    if not db_conn:
        return {
            'food': 50.0,
            'mineral': 30.0,
            'energy': 25.0,
            'fuel': 10.0,
            'taxable_income': 1000.0
        }

    # Database mode - would query actual planet data and infrastructure
    try:
        cursor = db_conn.cursor()

        # Query colony infrastructure
        cursor.execute("""
            SELECT farming_stations, mining_stations, solar_satellites, population, tax_rate
            FROM planets p
            JOIN colonies c ON p.planet_id = c.planet_id
            JOIN planetary_stats ps ON p.planet_id = ps.planet_id
            WHERE p.planet_id = %s
        """, (planet_id,))

        row = cursor.fetchone()
        if not row:
            return {'food': 0, 'mineral': 0, 'energy': 0, 'fuel': 0, 'taxable_income': 0}

        farming_stations, mining_stations, solar_satellites, population, tax_rate = row

        # Calculate resource flow (simplified formulas)
        food_produced = farming_stations * 15.0  # Each station produces 15 food
        minerals_produced = mining_stations * 8.0  # Each station produces 8 minerals
        energy_produced = solar_satellites * 12.0  # Each satellite produces 12 energy
        fuel_from_minerals = (minerals_produced * 0.5)  # 0.5 fuel per mineral

        # Population consumption
        food_consumed = population * 0.5  # 0.5 food per person
        energy_consumed = population * 0.3  # 0.3 energy per person (for machinery)

        # Calculate net flow
        food_net = food_produced - food_consumed
        mineral_net = minerals_produced
        energy_net = energy_produced - energy_consumed

        # Tax revenue (simplified)
        tax_rate_decimal = float(tax_rate) if tax_rate else 0.05
        tax_revenue = population * 10.0 * tax_rate_decimal  # Base 10 credits per person

        return {
            'food': round(food_net, 2),
            'mineral': round(mineral_net, 2),
            'energy': round(energy_net, 2),
            'fuel': round(fuel_from_minerals, 2),
            'taxable_income': round(tax_revenue, 2)
        }

    except Exception as e:
        print(f"Error calculating resource flow: {e}")
        return {'food': 0, 'mineral': 0, 'energy': 0, 'fuel': 0, 'taxable_income': 0}


def process_ship_movement(ship_id: int, destination_planet_id: int, db_conn=None) -> bool:
    """
    Process movement of a ship to another planet.

    Args:
        ship_id: ID of the ship to move
        destination_planet_id: Destination planet ID
        db_conn: Optional database connection (mock mode if None)

    Returns:
        True if movement succeeded, False otherwise
    """
    # Mock mode - always succeeds for development
    if not db_conn:
        return True

    try:
        cursor = db_conn.cursor()

        # Check if destination planet exists and can accept the ship
        cursor.execute("SELECT owner_user_id FROM planets WHERE planet_id = %s", (destination_planet_id,))
        result = cursor.fetchone()

        if not result:
            print(f"Error: Destination planet {destination_planet_id} does not exist")
            return False

        # Deduct fuel cost from origin (would need to track fuel per planet or ship)
        # For now, we'll assume ships have their own fuel tanks

        # Update ship location
        cursor.execute("""
            UPDATE ships
            SET heading = %s, planet_id = %s
            WHERE ship_id = %s
        """, (destination_planet_id, destination_planet_id, ship_id))

        if cursor.rowcount == 0:
            print(f"Error: Ship {ship_id} not found")
            return False

        db_conn.commit()
        return True

    except Exception as e:
        print(f"Error processing ship movement: {e}")
        return False


def resolve_combat(attacker_planet_id: int, defender_planet_id: int, db_conn=None) -> str:
    """
    Resolve combat between two planets.

    Combat power = ships * 10 + mining_stations * 20 + population

    Outcomes:
    - Power ratio > 1.5: Victory
    - Power ratio < 0.6: Defeat
    - Total resources ratio > 1.2: Victory
    - Total resources ratio < 0.8: Defeat
    - Otherwise: Stalemate

    If attacker wins and defender is not player-owned, transfers ownership.

    Args:
        attacker_planet_id: Planet whose troops are attacking
        defender_planet_id: Planet being attacked
        db_conn: Optional database connection (mock mode if None)

    Returns:
        Battle log string describing the outcome
    """
    if not db_conn:
        return "Battle simulation complete (no database connection)."

    try:
        cursor = db_conn.cursor(dictionary=True)

        # Get attacker info
        cursor.execute("""
            SELECT p.planet_id, p.name as name, ps.population, ps.food_level, ps.energy_level, ps.fuel_level,
                   COALESCE(c.mining_stations, 0) as mining_stations
            FROM planets p
            JOIN planetary_stats ps ON p.planet_id = ps.planet_id
            LEFT JOIN colonies c ON p.planet_id = c.planet_id
            WHERE p.planet_id = %s
        """, (attacker_planet_id,))
        att_row = cursor.fetchone()

        # Get defender info
        cursor.execute("""
            SELECT p.planet_id, p.name as name, ps.population, ps.food_level, ps.energy_level, ps.fuel_level,
                   COALESCE(c.mining_stations, 0) as mining_stations
            FROM planets p
            JOIN planetary_stats ps ON p.planet_id = ps.planet_id
            LEFT JOIN colonies c ON p.planet_id = c.planet_id
            WHERE p.planet_id = %s
        """, (defender_planet_id,))
        def_row = cursor.fetchone()

        # Get fleet counts
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM ships
            WHERE planet_id = %s AND owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
        """, (attacker_planet_id,))
        att_fleet = cursor.fetchone()['count'] or 0

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM ships
            WHERE planet_id = %s AND owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
        """, (defender_planet_id,))
        def_fleet = cursor.fetchone()['count'] or 0

        cursor.close()

        # Calculate combat power
        power_attacker = att_fleet * 10 + att_row['mining_stations'] * 20 + att_row['population']
        power_defender = def_fleet * 10 + def_row['mining_stations'] * 20 + def_row['population']

        ratio = power_attacker / power_defender if power_defender > 0 else 999

        # Total resource reserves
        res_att = (att_row['food_level'] or 0) + (att_row['energy_level'] or 0) + (att_row['fuel_level'] or 0)
        res_def = (def_row['food_level'] or 0) + (def_row['energy_level'] or 0) + (def_row['fuel_level'] or 0)

        if ratio > 1.5:
            return (f"Combat Report: {att_row['name']} attacks {def_row['name']}!\n"
                    f"Attacker combat power: {power_attacker} (fleet: {att_fleet}, mining: {att_row['mining_stations']}, pop: {att_row['population']})\n"
                    f"Defender combat power: {power_defender} (fleet: {def_fleet}, mining: {def_row['mining_stations']}, pop: {def_row['population']})\n"
                    f"Attacker wins decisively!")
        elif ratio < 0.6:
            return (f"Combat Report: {att_row['name']} attacks {def_row['name']}!\n"
                    f"Attacker combat power: {power_attacker}\n"
                    f"Defender combat power: {power_defender}\n"
                    f"Attacker is overwhelmed by the defenses!")
        else:
            if res_att > res_def * 1.2:
                return (f"Combat Report: {att_row['name']} attacks {def_row['name']}!\n"
                        f"Combat power was roughly equal. Attacker wins through superior resource reserves.")
            elif res_att < res_def * 0.8:
                return (f"Combat Report: {att_row['name']} attacks {def_row['name']}!\n"
                        f"Combat power was roughly equal. Attacker's resources deplete against the defender's defenses.")
            else:
                return (f"Combat Report: {att_row['name']} attacks {def_row['name']}!\n"
                        f"Combat power and resources were nearly equal. The battle ends in a stalemate.")

    except Exception as e:
        print(f"Error resolving combat: {e}")
        return f"Battle simulation failed: {str(e)}"


def run_turn(user_id: int, db_conn=None) -> Dict[str, Any]:
    """
    Run one game turn for a player across all owned planets.

    Args:
        user_id: ID of the player whose turn it is
        db_conn: Optional database connection (mock mode if None)

    Returns:
        Turn result summary dict with global totals and messages
    """
    # Mock mode
    if not db_conn:
        return {"turn_complete": True, "message": "Turn simulated (no DB)"}

    try:
        cursor = db_conn.cursor()

        # Use stored procedure for batch processing if enabled
        if USE_STORED_PROCEDURES:
            # Call the stored procedure for batch turn processing
            cursor.callproc("process_player_turns_batch", (user_id,))
            rows_updated = cursor.rowcount if hasattr(cursor, 'rowcount') else 0

            return {
                "turn_complete": True,
                "message": f"Turn simulated via stored procedure ({rows_updated} planets updated)",
                "method": "stored_procedure"
            }
        else:
            # Legacy per-planet processing (original implementation)
            # Get player's owned planets
            cursor.execute("SELECT planet_id FROM planets WHERE owner_user_id = %s", (user_id,))
            planets = cursor.fetchall()

            total_food_produced = 0
            total_food_consumed = 0
            total_mineral_produced = 0
            total_mineral_consumed = 0
            total_energy_produced = 0
            total_energy_consumed = 0
            total_fuel_produced = 0
            total_fuel_consumed = 0
            population_changes = []

            for planet in planets:
                result = simulate_planet_turn(planet['planet_id'])
                total_food_produced += result.get('food_produced', 0)
                total_food_consumed += result.get('food_consumed', 0)
                total_mineral_produced += result.get('minerals_produced', 0)
                total_mineral_consumed += result.get('minerals_consumed', 0)
                total_energy_produced += result.get('energy_produced', 0)
                total_energy_consumed += result.get('energy_consumed', 0)
                total_fuel_produced += result.get('fuel_produced', 0)
                total_fuel_consumed += result.get('fuel_consumed', 0)
                if result.get('population_delta') != 0:
                    population_changes.append(f"{planet['planet_id']}: pop {result.get('population_delta', 0)}")

            cursor.close()
            db_conn.commit()

            return {
                "turn_complete": True,
                "message": "Turn simulated",
                "method": "legacy" if not USE_STORED_PROCEDURES else "stored_procedure"
            }

        return {
            "turn_complete": True,
            "message": "Turn processed successfully",
            "total_food_produced": round(total_food_produced, 2),
            "total_food_consumed": round(total_food_consumed, 2),
            "total_mineral_produced": round(total_mineral_produced, 2),
            "total_mineral_consumed": round(total_mineral_consumed, 2),
            "total_energy_produced": round(total_energy_produced, 2),
            "total_energy_consumed": round(total_energy_consumed, 2),
            "total_fuel_produced": round(total_fuel_produced, 2),
            "total_fuel_consumed": round(total_fuel_consumed, 2),
            "population_changes": population_changes or ["No population changes"]
        }

    except Exception as e:
        print(f"Error running turn: {e}")
        return {"turn_complete": False, "message": str(e)}


def ai_opponent_turn(db_conn=None, ai_user_id=99) -> Dict[str, Any]:
    """
    Simulate AI opponent's turn.

    Args:
        db_conn: Optional database connection (mock mode if None)
        ai_user_id: The user ID of the AI opponent

    Returns:
        Dict with AI actions summary
    """
    # Mock mode
    return {"ai_actions": f"simulated for user {ai_user_id}", "message": "AI turn simulated (no DB)"}


def create_user(username: str, initial_credits: int = 1000, db_conn=None) -> Optional[int]:
    """Create a new user account."""
    if not db_conn:
        return 1  # Mock success

    try:
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, credits) VALUES (%s, %s)
        """, (username, initial_credits))
        user_id = cursor.lastrowid
        db_conn.commit()
        return user_id
    except Exception as e:
        print(f"Error creating user {username}: {e}")
        return None


def create_system(name: str, difficulty: int, db_conn=None) -> Optional[int]:
    """Create a new planetary system."""
    if not db_conn:
        return 1  # Mock success

    try:
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO systems (name, difficulty_level) VALUES (%s, %s)
        """, (name, difficulty))
        system_id = cursor.lastrowid
        db_conn.commit()
        return system_id
    except Exception as e:
        print(f"Error creating system {name}: {e}")
        return None


def init_default_game(db_conn=None):
    """Initialize the game with default data if tables exist but are empty."""
    if not db_conn:
        return {"initialized": True, "message": "Mock initialization complete"}

    try:
        cursor = db_conn.cursor()

        # Check if assets_catalog is empty
        cursor.execute("SELECT COUNT(*) FROM assets_catalog")
        asset_count = cursor.fetchone()[0]

        if asset_count == 0:
            populate_assets_catalog(cursor)

        # Check if default player exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'Player'")
        player_exists = cursor.fetchone()[0]

        if player_exists == 0:
            create_user("Player", initial_credits=5000, db_conn=db_conn)

        # Check for System 1
        cursor.execute("SELECT COUNT(*) FROM systems WHERE name = 'System 1'")
        system_exists = cursor.fetchone()[0]

        if system_exists == 0:
            create_system("System 1", difficulty=1, db_conn=db_conn)

        db_conn.commit()
        return {"initialized": True, "message": "Default game data initialized"}

    except Exception as e:
        print(f"Error initializing default game: {e}")
        return {"initialized": False, "error": str(e)}


def populate_assets_catalog(db_conn) -> None:
    """Populate the assets catalog with purchasable items."""
    try:
        cursor = db_conn.cursor()

        # Insert ships
        ships = [
            ("BattleCruiser", "Ship", 500),
            ("CargoShip", "Ship", 300),
            ("FarmingShip", "Ship", 150),
            ("MineralShip", "Ship", 180),
            ("Terraformer", "Infrastructure", 2000, True),  # Unique purchase
        ]

        for ship_name, category, cost, *is_unique in ships:
            cursor.execute("""
                INSERT INTO assets_catalog (name, category, base_cost, is_unique)
                VALUES (%s, %s, %s, %s)
            """, (ship_name, category, cost, is_unique[0] if len(is_unique) > 0 else False))

        # Insert ship types with costs
        ship_types = [
            ("BattleCruiser", 500),
            ("CargoShip", 300),
            ("FarmingShip", 150),
            ("MineralShip", 180),
        ]

        for ship_name, cost in ship_types:
            cursor.execute("""
                INSERT INTO ship_types (ship_type_name, base_purchase_cost)
                VALUES (%s, %s)
            """, (ship_name, cost))

        # Insert equipment
        armor_items = [
            ("Light Armor", "Armor", 100, 3),
            ("Medium Armor", "Armor", 250, 6),
            ("Heavy Armor", "Armor", 500, 10),
            ("Plasteel Armor", "Armor", 800, 15),
        ]

        weapon_items = [
            ("Pistol", "Weapon", 50, 2),
            ("Rifle", "Weapon", 150, 5),
            ("Cannon", "Weapon", 300, 8),
            ("Heavy Cannon", "Weapon", 600, 12),
        ]

        for name, category, cost, strength in armor_items + weapon_items:
            cursor.execute("""
                INSERT INTO equipment_catalog (name, category, base_cost, strength_value)
                VALUES (%s, %s, %s, %s)
            """, (name, category, cost, strength))

        db_conn.commit()
        print("Assets catalog populated successfully")

    except Exception as e:
        print(f"Error populating assets catalog: {e}")


def create_default_planets(db_conn) -> None:
    """Create default planets for each system."""
    try:
        cursor = db_conn.cursor()

        systems = ["System 1", "System 2"]
        planet_counts = [8, 16]

        for i, (system_name, count) in enumerate(zip(systems, planet_counts), 1):
            # First planet is owned by Player
            cursor.execute("""
                INSERT INTO planets (system_id, name, owner_user_id) VALUES (%s, %s, 1)
            """, (i, f"{system_name}-Alpha"))

            # Create stats and colonies for the first planet
            cursor.execute("""
                INSERT INTO planetary_stats (planet_id, population, morale, tax_rate, food_level, mineral_level, energy_level, fuel_level)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (1, 100, 8, 0.05, 50, 30, 25, 10))

            cursor.execute("""
                INSERT INTO colonies (planet_id, farming_stations, mining_stations, solar_satellites)
                VALUES (%s, %s, %s, %s)
            """, (1, 1, 0, 0))

            print(f"Created planet Alpha ({system_name})")

        db_conn.commit()

    except Exception as e:
        print(f"Error creating default planets: {e}")


def get_planet_state(planet_id: int, db_conn=None) -> Optional[Dict[str, Any]]:
    """Get the complete state of a planet."""
    if not db_conn:
        return {
            "planet_id": 1,
            "name": "System 1-Alpha",
            "owner_name": "Player",
            "population": 100,
            "morale": 8,
            "tax_rate": 5.0,
            "resources": {
                "food": 50,
                "mineral": 30,
                "energy": 25,
                "fuel": 10
            }
        }

    try:
        cursor = db_conn.cursor()

        # Get planet info
        cursor.execute("""
            SELECT p.planet_id, p.name, ps.population, ps.morale, ps.tax_rate, ps.food_level,
                   ps.mineral_level, ps.energy_level, ps.fuel_level, u.username as owner_name
            FROM planets p
            JOIN planetary_stats ps ON p.planet_id = ps.planet_id
            LEFT JOIN users u ON p.owner_user_id = u.user_id
            WHERE p.planet_id = %s
        """, (planet_id,))

        row = cursor.fetchone()

        if not row:
            return None

        planet_id, name, population, morale, tax_rate, food_level, mineral_level, energy_level, fuel_level, owner_name = row

        # Get colony infrastructure
        cursor.execute("""
            SELECT farming_stations, mining_stations, solar_satellites
            FROM colonies WHERE planet_id = %s
        """, (planet_id,))

        colony_row = cursor.fetchone()
        farming_stations, mining_stations, solar_satellites = colony_row if colony_row else (1, 0, 0)

        # Get ships at this planet
        cursor.execute("""
            SELECT ship_type, COUNT(*) as count
            FROM ships WHERE planet_id = %s GROUP BY ship_type
        """, (planet_id,))

        ships = dict(cursor.fetchall()) or {}

        return {
            "planet_id": planet_id,
            "name": name,
            "owner_name": owner_name or "Neutral",
            "population": population,
            "morale": morale,
            "tax_rate": round(float(tax_rate), 2) if tax_rate else 5.0,
            "resources": {
                "food": food_level,
                "mineral": mineral_level,
                "energy": energy_level,
                "fuel": fuel_level
            },
            "infrastructure": {
                "farming_stations": farming_stations,
                "mining_stations": mining_stations,
                "solar_satellites": solar_satellites
            },
            "ships": ships
        }

    except Exception as e:
        print(f"Error getting planet state: {e}")
        return None


def get_player_overview(db_conn=None) -> Optional[Dict[str, Any]]:
    """Get player overview with credits and owned systems."""
    if not db_conn:
        return {
            "username": "Player",
            "credits": 5000,
            "owned_systems": ["System 1", "System 2"],
            "total_planets": 24
        }

    try:
        cursor = db_conn.cursor()

        # Get player credits
        cursor.execute("SELECT credits FROM users WHERE username = %s", ("Player",))
        result = cursor.fetchone()
        credits = result[0] if result else 5000

        # Get owned systems list
        cursor.execute("""
            SELECT DISTINCT s.name as system_name, COUNT(p.planet_id) as planet_count
            FROM planets p
            JOIN systems s ON p.system_id = s.system_id
            WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            GROUP BY s.name
            ORDER BY s.name
        """)

        owned_systems = cursor.fetchall()
        total_planets = sum(r[1] for r in owned_systems)

        return {
            "username": "Player",
            "credits": credits,
            "owned_systems": [(r[0], r[1]) for r in owned_systems],
            "total_planets": total_planets
        }

    except Exception as e:
        print(f"Error getting player overview: {e}")
        return None


def simulate_planet_turn(planet_id: int, db_conn=None) -> Dict[str, float]:
    """
    Simulate one turn for a planet and apply resource changes.

    Production rates:
    - Food: farming_stations * 15 per station
    - Minerals: mining_stations * 8 per station
    - Energy: solar_satellites * 12 per satellite
    - Fuel: (minerals_produced * 0.5) + (food_produced * 0.2)

    Consumption rates:
    - Food: population * 0.5 (survival requirement)
    - Energy: population * 0.3 + ships_at_planet * 2 per ship
    - Minerals: ships_at_planet * 1 per ship (mineral consumption)
    - Fuel: ships_at_planet * 0.8 per ship

    Population growth:
    - Grows when food surplus > 0 (rate depends on morale and tax_rate)

    Morale changes:
    - Decreases if under any resource deficit
    - Increases with positive taxable income surplus

    Args:
        planet_id: The ID of the planet to simulate
        db_conn: Optional database connection (mock mode if None)

    Returns:
        Dict with net change values for each resource
    """
    # Mock mode - returns default values for development without database
    if not db_conn:
        return {
            'food': 50.0,
            'mineral': 30.0,
            'energy': 25.0,
            'fuel': 10.0,
            'taxable_income': 1000.0,
            'population_delta': 0,
            'morale_delta': 0,
            'food_produced': 75.0,
            'minerals_produced': 40.0,
            'energy_produced': 60.0,
            'fuel_produced': 25.0,
            'food_consumed': 40.0,
            'minerals_consumed': 10.0,
            'energy_consumed': 50.0,
            'fuel_consumed': 8.0,
            'turn_complete': True
        }

    try:
        cursor = db_conn.cursor()
    except Exception as e:
        print(f"Error getting database connection: {e}")
        return {'food': 0, 'mineral': 0, 'energy': 0, 'fuel': 0, 'taxable_income': 0}

    # Get current planet state (planet must exist)
    cursor.execute("""
        SELECT p.planet_id, u.username as owner_name
        FROM planets p
        LEFT JOIN users u ON p.owner_user_id = u.user_id
        WHERE p.planet_id = %s
    """, (planet_id,))

    planet_row = cursor.fetchone()
    if not planet_row:
        print(f"Error: Planet {planet_id} not found")
        return {'food': 0, 'mineral': 0, 'energy': 0, 'fuel': 0, 'taxable_income': 0}

    # Try to get stats - some planets may not have stats yet
    cursor.execute("""
        SELECT ps.population, ps.morale, ps.tax_rate,
               ps.food_level, ps.mineral_level, ps.energy_level, ps.fuel_level
        FROM planetary_stats ps
        WHERE ps.planet_id = %s
    """, (planet_id,))

    stats_row = cursor.fetchone()

    if stats_row:
        population, morale, tax_rate, food_level, mineral_level, energy_level, fuel_level = stats_row
    else:
        # No stats yet - initialize defaults for new planets
        population = 100
        morale = 5
        tax_rate = 0.05
        food_level = 50
        mineral_level = 30
        energy_level = 25
        fuel_level = 10

    # Get colony infrastructure
    cursor.execute("""
        SELECT farming_stations, mining_stations, solar_satellites
        FROM colonies WHERE planet_id = %s
    """, (planet_id,))

    colony_row = cursor.fetchone()

    if colony_row:
        farming_stations = int(colony_row[0]) if colony_row[0] else 0
        mining_stations = int(colony_row[1]) if len(colony_row) > 1 and colony_row[1] else 0
        solar_satellites = int(colony_row[2]) if len(colony_row) > 2 and colony_row[2] else 0
    else:
        # Default infrastructure for planets without colonies entry
        farming_stations = 0
        mining_stations = 0
        solar_satellites = 0

    owner_name = planet_row[1] if planet_row[1] else 'Neutral'

    # Get ships at this planet (player ships only)
    cursor.execute("""
        SELECT COUNT(*) as count, SUM(CASE WHEN ship_type = 'BattleCruiser' THEN 1 ELSE 0 END) as bc_count,
               SUM(CASE WHEN ship_type = 'CargoShip' THEN 1 ELSE 0 END) as cs_count,
               SUM(CASE WHEN ship_type = 'FarmingShip' THEN 1 ELSE 0 END) as fs_count,
               SUM(CASE WHEN ship_type = 'MineralShip' THEN 1 ELSE 0 END) as ms_count
        FROM ships WHERE planet_id = %s AND owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
    """, (planet_id,))

    ship_row = cursor.fetchone()
    ship_count = ship_row[0] if ship_row else 0
    bc_count = ship_row[1] if len(ship_row) > 1 else 0
    cs_count = ship_row[2] if len(ship_row) > 2 else 0
    fs_count = ship_row[3] if len(ship_row) > 3 else 0
    ms_count = ship_row[4] if len(ship_row) > 4 else 0

    # Production rates (per turn production amounts)
    food_produced = farming_stations * 15.0
    minerals_produced = mining_stations * 8.0
    energy_produced = solar_satellites * 12.0
    fuel_from_minerals = minerals_produced * 0.5
    fuel_from_food = food_produced * 0.2
    total_fuel_produced = fuel_from_minerals + fuel_from_food

    # Consumption rates (per turn consumption amounts)
    food_consumed = population * 0.5
    energy_consumed = population * 0.3 + ship_count * 2.0
    minerals_consumed = ship_count * 1.0
    fuel_consumed = ship_count * 0.8

    # Net production (what accumulates on the planet)
    food_net = round(food_produced - food_consumed, 2)
    mineral_net = round(minerals_produced - minerals_consumed, 2)
    energy_net = round(energy_produced - energy_consumed, 2)
    fuel_net = round(total_fuel_produced - fuel_consumed, 2)

    # Population growth (only grows if food surplus > 0)
    food_surplus = food_produced - food_consumed
    morale_bonus = float(morale) / 10.0  # Lower morale = slower growth
    tax_multiplier = 1.0 + float(tax_rate) * 5.0  # Higher tax = faster growth but more income
    new_population = population + int(round(food_surplus * 0.1 * (1 - morale_bonus) * tax_multiplier, 2)) if food_surplus > 0 else population

    # Morale changes based on resource deficits and taxable income
    deficit_count = sum([food_net < 0, mineral_net < 0, energy_net < 0, fuel_net < 0])
    has_deficits = any(r < -50 for r in [food_net, mineral_net, energy_net, fuel_net])

    # Taxable income (credits generated from taxation)
    tax_rate_decimal = float(tax_rate) if tax_rate else 0.05
    taxable_income = round(population * 10.0 * tax_rate_decimal * (1 + has_deficits * 0.2), 2)

    # Morale adjustment: decreases with deficits, increases with stability
    morale_delta = -deficit_count * 2 if deficit_count else 1
    if not has_deficits and food_surplus > 50:
        morale_delta += 2  # Boost morale with good conditions
    new_morale = max(1, min(10, morale + morale_delta))

    # Update planetary stats with new values
    cursor.execute("""
        UPDATE planetary_stats
        SET population = %s, morale = %s, food_level = %s, mineral_level = %s,
            energy_level = %s, fuel_level = %s
        WHERE planet_id = %s
    """, (new_population, new_morale, food_level + food_net,
          mineral_level + mineral_net, energy_level + energy_net,
          fuel_level + fuel_net, planet_id))

    db_conn.commit()

    cursor.close()

    return {
        'food': food_net,
        'mineral': mineral_net,
        'energy': energy_net,
        'fuel': fuel_net,
        'taxable_income': taxable_income,
        'population_delta': round(new_population - population, 2),
        'morale_delta': new_morale - morale,
        'food_produced': round(food_produced, 2),
        'minerals_produced': round(minerals_produced, 2),
        'energy_produced': round(energy_produced, 2),
        'fuel_produced': round(total_fuel_produced, 2),
        'food_consumed': round(food_consumed, 2),
        'minerals_consumed': round(minerals_consumed, 2),
        'energy_consumed': round(energy_consumed, 2),
        'fuel_consumed': round(fuel_consumed, 2)
    }


def get_all_planets(db_conn=None) -> List[Dict[str, Any]]:
    """Get all planets for browsing across both systems."""
    if not db_conn:
        # Return mock data for System 1 (8 planets) and System 2 (16 planets)
        return [
            {"planet_id": i+1, "system_id": 1, "name": f"System 1-{chr(65+(i%8))}", "owner_name": "Player" if i==0 else "Neutral"}
            for i in range(8)
        ] + [
            {"planet_id": 9+i, "system_id": 2, "name": f"System 2-{chr(65+((i%16)%13))}", "owner_name": "Neutral"}
            for i in range(16)
        ]

    try:
        cursor = db_conn.cursor()

        # Get all systems first
        cursor.execute("SELECT system_id, name FROM systems ORDER BY system_id")
        systems = cursor.fetchall()

        all_planets = []
        for sys_id, sys_name in systems:
            # Query planets for this system with their details
            cursor.execute("""
                SELECT p.planet_id, ps.population, ps.morale, ps.tax_rate,
                       ps.food_level, ps.mineral_level, ps.energy_level, ps.fuel_level,
                       u.username as owner_name
                FROM planets p
                JOIN planetary_stats ps ON p.planet_id = ps.planet_id
                LEFT JOIN users u ON p.owner_user_id = u.user_id
                WHERE p.system_id = %s
                ORDER BY p.planet_id
            """, (sys_id,))

            for row in cursor.fetchall():
                all_planets.append({
                    "planet_id": row[0],
                    "system_id": sys_id,
                    "name": f"{sys_name}-Planet-{row[0]}",
                    "population": int(row[1]) if row[1] else 0,
                    "morale": int(row[2]) if row[2] else 5,
                    "tax_rate": round(float(row[3]), 2) if row[3] else 0.05,
                    "food_level": int(row[4]) if row[4] else 0,
                    "mineral_level": int(row[5]) if row[5] else 0,
                    "energy_level": int(row[6]) if row[6] else 0,
                    "fuel_level": int(row[7]) if row[7] else 0,
                    "owner_name": row[8] or "Neutral"
                })

        return all_planets

    except Exception as e:
        print(f"Error getting all planets: {e}")
        return []


def get_fleet_inventory(db_conn=None) -> Dict[str, List[Dict[str, Any]]]:
    """Get complete fleet inventory across all planets for a player."""
    if not db_conn:
        # Return mock fleet data
        return {
            "System 1-Alpha": [
                {"ship_id": 1, "ship_type": "BattleCruiser", "docking_bay_slot": 1}
            ]
        }

    try:
        cursor = db_conn.cursor()

        # Get fleet overview by planet
        cursor.execute("""
            SELECT p.planet_id, p.name as planet_name, ps.population,
                   s.ship_type, COUNT(s.ship_id) as count
            FROM planets p
            JOIN planetary_stats ps ON p.planet_id = ps.planet_id
            LEFT JOIN ships s ON p.planet_id = s.planet_id
            LEFT JOIN systems sy ON p.system_id = sy.system_id
            WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            GROUP BY p.planet_id, p.name, ps.population, s.ship_type
            ORDER BY p.planet_id
        """)

        fleet_data = cursor.fetchall()

        # Organize by planet
        fleet_by_planet = {}
        for row in fleet_data:
            planet_id, planet_name, population, ship_type, count = row
            if planet_id not in fleet_by_planet:
                fleet_by_planet[planet_id] = {
                    "planet_id": planet_id,
                    "planet_name": planet_name,
                    "population": population,
                    "ships": []
                }

        for planet_id, planet_info in fleet_by_planet.items():
            ships = [
                {"ship_id": sid, "ship_type": stype, "docking_bay_slot": slot}
                for sid, stype, slot in [
                    (planet_info["planet_id"] + i*10, stype, (i % 3) + 1)
                    for i in range(count)
                ]
            ]
            planet_info["ships"] = ships

        # Convert to dict keyed by system name
        systems_data = cursor.execute("SELECT system_id, name FROM systems ORDER BY system_id").fetchall()
        system_map = {s[0]: s[1] for s in systems_data}

        result = {}
        for planet_id, planet_info in fleet_by_planet.items():
            # Get system name
            cursor.execute("SELECT name FROM systems WHERE system_id = %s", (planet_info["system_id"],))
            row = cursor.fetchone()
            sys_name = row[0] if row else f"Unknown-{planet_id}"
            result.setdefault(sys_name, [])
            result[sys_name].append(planet_info)

        return result

    except Exception as e:
        print(f"Error getting fleet inventory: {e}")
        return {}


def get_ship_cargo_manifest(ship_id: int, db_conn=None) -> Optional[List[Dict[str, Any]]]:
    """Get cargo manifest for a specific ship."""
    if not db_conn:
        # Mock cargo data
        return [
            {"resource_type": "Food", "quantity": 50},
            {"resource_type": "Energy", "quantity": 25}
        ]

    try:
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT resource_type, quantity FROM ship_cargo WHERE ship_id = %s
        """, (ship_id,))

        manifest = [
            {"resource_type": r[0], "quantity": int(r[1])}
            for r in cursor.fetchall()
        ]

        return manifest if manifest else None

    except Exception as e:
        print(f"Error getting ship cargo: {e}")
        return None


def get_system_planet_list(db_conn=None) -> List[Dict[str, Any]]:
    """Get list of all systems with their planets for navigation."""
    if not db_conn:
        # Mock system/planet data
        return [
            {"system_id": 1, "name": "System 1", "difficulty": 1, "planets": 8},
            {"system_id": 2, "name": "System 2", "difficulty": 2, "planets": 16}
        ]

    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT system_id, name, difficulty_level FROM systems ORDER BY system_id")

        system_list = []
        for row in cursor.fetchall():
            sys_id, sys_name, difficulty = row
            cursor.execute("""
                SELECT p.name, ps.population
                FROM planets p
                JOIN planetary_stats ps ON p.planet_id = ps.planet_id
                WHERE p.system_id = %s
                ORDER BY p.planet_id
            """, (sys_id,))

            planets = [
                {
                    "planet_id": r[0].split('-')[1] if '-' in str(r[0]) else r[0],
                    "name": r[0],
                    "population": int(r[1]) if r[1] else 0
                }
                for r in cursor.fetchall()
            ]

            system_list.append({
                "system_id": sys_id,
                "name": sys_name,
                "difficulty": difficulty,
                "planets": planets
            })

        return system_list

    except Exception as e:
        print(f"Error getting system/planet list: {e}")
        return []


def get_astro_survey(db_conn=None) -> Optional[Dict[str, Any]]:
    """Get current resource flow and planetary data for detailed view."""
    if not db_conn:
        # Mock astro survey data
        return {
            "planet_id": 1,
            "population": 100,
            "food_produced": 15.0,
            "minerals_produced": 8.0,
            "energy_produced": 12.0,
            "fuel_generated": 4.0
        }

    try:
        cursor = db_conn.cursor()
        planet_id = 1  # Default active planet

        # Get colony infrastructure
        cursor.execute("""
            SELECT farming_stations, mining_stations, solar_satellites
            FROM colonies WHERE planet_id = %s
        """, (planet_id,))

        row = cursor.fetchone()
        farming_stations, mining_stations, solar_satellites = row if row else (1, 0, 0)

        # Calculate resource flows
        food_produced = farming_stations * 15.0
        minerals_produced = mining_stations * 8.0
        energy_produced = solar_satellites * 12.0
        fuel_generated = (minerals_produced * 0.5) + (farming_stations * 0.5)

        return {
            "planet_id": planet_id,
            "population": 100,
            "food_produced": round(food_produced, 2),
            "minerals_produced": round(minerals_produced, 2),
            "energy_produced": round(energy_produced, 2),
            "fuel_generated": round(fuel_generated, 2)
        }

    except Exception as e:
        print(f"Error getting astro survey: {e}")
        return None


def get_player_credits(username: str = "Player", db_conn=None) -> int:
    """Get player's current credits."""
    if not db_conn:
        return 0
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT credits FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        cursor.close()
        return row[0] if row else 0
    except Exception as e:
        print(f"Error getting credits: {e}")
        return 0


def get_player_assets(username: str = "Player", db_conn=None) -> List[Dict[str, Any]]:
    """Get all purchased assets across all player planets."""
    if not db_conn:
        return []
    try:
        cursor = db_conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT pa.asset_name, pa.asset_type, pa.quantity, pa.base_cost, pa.planet_id, p.name as planet_name
            FROM planetary_assets pa
            JOIN planets p ON pa.planet_id = p.planet_id
            WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = %s)
            ORDER BY pa.asset_type, pa.asset_name
        """, (username,))
        rows = cursor.fetchall()
        cursor.close()
        return rows
    except Exception as e:
        print(f"Error getting player assets: {e}")
        return []


def get_first_owned_planet_id(username: str = "Player", db_conn=None) -> Optional[int]:
    """Get the first owned planet ID for the player."""
    if not db_conn:
        return 1
    try:
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT p.planet_id FROM planets
            WHERE owner_user_id IN (SELECT user_id FROM users WHERE username = %s)
            ORDER BY planet_id LIMIT 1
        """, (username,))
        row = cursor.fetchone()
        cursor.close()
        return row[0] if row else 1
    except Exception as e:
        print(f"Error getting first owned planet: {e}")
        return 1


def get_asset_by_name(name: str, db_conn=None) -> Optional[Dict[str, Any]]:
    """Look up an asset by name, checking equipment_catalog first, then assets_catalog."""
    if not db_conn:
        return None
    try:
        cursor = db_conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT name, category, base_cost, strength_value, image_url
            FROM equipment_catalog WHERE name = %s
        """, (name,))
        row = cursor.fetchone()
        if row:
            cursor.close()
            return row

        cursor.execute("""
            SELECT name, category, base_cost, description, image_url
            FROM assets_catalog WHERE name = %s AND category IN ('Ship', 'Infrastructure')
        """, (name,))
        row = cursor.fetchone()
        cursor.close()
        return row
    except Exception as e:
        print(f"Error getting asset by name: {e}")
        return None


def has_player_owned_asset(player_user_id: int, asset_name: str, db_conn=None) -> bool:
    """Check if the player already owns an asset (e.g., Terraformer uniqueness check)."""
    if not db_conn:
        return False
    try:
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM planetary_assets pa
            JOIN planets p ON pa.planet_id = p.planet_id
            WHERE p.owner_user_id = %s AND pa.asset_name = %s
        """, (player_user_id, asset_name))
        count = cursor.fetchone()[0]
        cursor.close()
        return count > 0
    except Exception as e:
        print(f"Error checking owned asset: {e}")
        return False


def get_debug_planet_info(planet_id: int, db_conn=None) -> Optional[Dict[str, Any]]:
    """Get a single planet's debug info (population, resources)."""
    if not db_conn:
        return None
    try:
        cursor = db_conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.planet_id, p.name, p.system_id,
                   u.username as owner_name,
                   COALESCE(ps.population, 0) as population,
                   COALESCE(ps.food_level, 0) as food_level,
                   COALESCE(ps.energy_level, 0) as energy_level,
                   COALESCE(ps.fuel_level, 0) as fuel_level
            FROM planets p
            LEFT JOIN planetary_stats ps ON p.planet_id = ps.planet_id
            LEFT JOIN users u ON p.owner_user_id = u.user_id
            WHERE p.planet_id = %s
        """, (planet_id,))
        row = cursor.fetchone()
        cursor.close()
        return row
    except Exception as e:
        print(f"Error getting debug planet info: {e}")
        return None


def get_debug_player_planets(username: str = "Player", db_conn=None) -> List[Dict[str, Any]]:
    """Get all owned planets for debug panel."""
    if not db_conn:
        return []
    try:
        cursor = db_conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.planet_id, p.name, p.system_id,
                   u.username as owner_name,
                   COALESCE(ps.population, 0) as population,
                   COALESCE(ps.food_level, 0) as food_level,
                   COALESCE(ps.energy_level, 0) as energy_level,
                   COALESCE(ps.fuel_level, 0) as fuel_level
            FROM planets p
            LEFT JOIN planetary_stats ps ON p.planet_id = ps.planet_id
            LEFT JOIN users u ON p.owner_user_id = u.user_id
            WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = %s)
        """, (username,))
        rows = cursor.fetchall()
        cursor.close()

        result = []
        for row in rows:
            result.append({
                "planet_id": row['planet_id'],
                "name": row['name'],
                "system_id": row['system_id'],
                "owner_name": row['owner_name'] or 'Neutral',
                "population": int(row['population']),
                "resources": {
                    "food_level": float(row['food_level']),
                    "energy_level": float(row['energy_level']),
                    "fuel_level": float(row['fuel_level']),
                },
                "fleet": [],
                "infrastructure": {
                    "farming_stations": 0,
                    "mining_stations": 0,
                    "solar_satellites": 0
                },
            })
        return result
    except Exception as e:
        print(f"Error getting debug player planets: {e}")
        return []


def adjust_resource_level(planet_id: int, resource_type: str, new_value: float, db_conn=None) -> bool:
    """Adjust a single resource level for a planet."""
    if not db_conn:
        return False
    try:
        cursor = db_conn.cursor()
        update_map = {
            'population': 'SET population = %s',
            'food_level': 'SET food_level = %s',
            'energy_level': 'SET energy_level = %s',
            'fuel_level': 'SET fuel_level = %s',
        }
        query = f"""
            UPDATE planetary_stats
            {update_map.get(resource_type, '')}
            WHERE planet_id = %s
        """
        cursor.execute(query, (new_value, planet_id))
        db_conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error adjusting resource level: {e}")
        return False


def add_credits_to_player(amount: int, username: str = "Player", db_conn=None) -> bool:
    """Add credits to a player."""
    if not db_conn:
        return False
    try:
        cursor = db_conn.cursor()
        cursor.execute("UPDATE users SET credits = credits + %s WHERE username = %s", (amount, username))
        db_conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error adding credits: {e}")
        return False


def get_player_over_planets(username: str = "Player", db_conn=None) -> List[Dict[str, Any]]:
    """Get all player-owned planets with stats (mirrors GET /api/planets)."""
    if not db_conn:
        return []
    try:
        cursor = db_conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.planet_id, p.name, s.name as system_name
            FROM planets p
            JOIN systems s ON p.system_id = s.system_id
            WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = %s)
            ORDER BY s.name, p.planet_id
        """, (username,))
        planets = cursor.fetchall()
        cursor.close()

        result = []
        for planet in planets:
            flow = calculate_resource_flow(planet['planet_id'], db_conn)
            result.append({
                'id': planet['planet_id'],
                'name': planet['name'],
                'system_name': planet['system_name'],
                'ownerName': 'You',
                'population': int(flow.get('taxable_income', 0)),
                'resources': flow,
                'morale': 5
            })
        return result
    except Exception as e:
        print(f"Error getting player planets: {e}")
        return []


def get_dashboard_planets(username: str = "Player", db_conn=None) -> List[Dict[str, Any]]:
    """Get all planets for dashboard view (mirrors GET /api/systems/all)."""
    if not db_conn:
        return []
    try:
        cursor = db_conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.planet_id, p.system_id, p.name as planet_name,
                   u.username as owner_name, ps.population, ps.morale, ps.tax_rate,
                   COALESCE(ps.food_level, 0) as food_level,
                   COALESCE(ps.mineral_level, 0) as mineral_level,
                   COALESCE(ps.energy_level, 0) as energy_level,
                   COALESCE(ps.fuel_level, 0) as fuel_level
            FROM planets p
            JOIN users u ON p.owner_user_id = u.user_id
            LEFT JOIN planetary_stats ps ON p.planet_id = ps.planet_id
            WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = %s)
            ORDER BY p.system_id, p.name
        """, (username,))
        rows = cursor.fetchall()

        result = []
        for row in rows:
            if row['planet_id']:
                # Get infrastructure
                cursor.execute("""
                    SELECT farming_stations, mining_stations, solar_satellites
                    FROM colonies WHERE planet_id = %s
                """, (row['planet_id'],))
                col_row = cursor.fetchone()
                infra = {
                    'farming_stations': col_row[0] if col_row and col_row[0] else 0,
                    'mining_stations': col_row[1] if col_row and col_row[1] else 0,
                    'solar_satellites': col_row[2] if col_row and col_row[2] else 0,
                }

                # Get purchased assets
                cursor.execute("""
                    SELECT asset_name, asset_type, base_cost
                    FROM planetary_assets WHERE planet_id = %s
                """, (row['planet_id'],))
                purchased = cursor.fetchall()

                result.append({
                    'planet_id': row['planet_id'],
                    'name': row['planet_name'],
                    'system_id': row['system_id'],
                    'owner_name': row['owner_name'],
                    'population': row['population'] or 0,
                    'morale': row['morale'] or 5,
                    'tax_rate': row['tax_rate'] or 0.05,
                    'resources': {
                        'food': row['food_level'] or 0,
                        'mineral': row['mineral_level'] or 0,
                        'energy': row['energy_level'] or 0,
                        'fuel': row['fuel_level'] or 0,
                        'taxable_income': (row['population'] or 0) * (row['tax_rate'] or 0.05)
                    },
                    'infrastructure': infra,
                    'fleet': [],
                    'purchased_assets': purchased
                })

        cursor.close()
        return result
    except Exception as e:
        print(f"Error getting dashboard planets: {e}")
        return []


def get_all_systems(username: str = "Player", db_conn=None) -> List[Dict[str, Any]]:
    """Get all systems with owned planet count."""
    if not db_conn:
        return []
    try:
        cursor = db_conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT s.system_id, s.name
            FROM systems s
            JOIN planets p ON s.system_id = p.system_id
            WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = %s)
            ORDER BY s.name
        """, (username,))
        rows = cursor.fetchall()
        cursor.close()

        result = []
        for row in rows:
            result.append({
                'system_id': row['system_id'],
                'name': row['name'] or 'System',
                'planets': []
            })
        return result if result else [{'system_id': 1, 'name': 'System 1', 'planets': []}]
    except Exception as e:
        print(f"Error getting all systems: {e}")
        return []


def get_fleet_at_planet(planet_id: int, db_conn=None) -> List[Dict[str, Any]]:
    """Get fleet inventory at a specific planet."""
    if not db_conn:
        return []
    try:
        cursor = db_conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT ship_type, COUNT(*) as count
            FROM ships WHERE planet_id = %s AND owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            GROUP BY ship_type
        """, (planet_id,))
        rows = cursor.fetchall()
        cursor.close()
        return [{'ship_type': row['ship_type'], 'count': row['count']} for row in rows]
    except Exception as e:
        print(f"Error getting fleet at planet: {e}")
        return []


if __name__ == "__main__":
    # Test functions when run directly
    conn = get_db_connection()
    if conn:
        print("Database connected. Initializing game...")
        init_default_game(conn)
        print(get_planet_state(1, conn))
    else:
        print("Running in mock mode - no database connection")
