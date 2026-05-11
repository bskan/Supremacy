            unit = "units" if res != "Taxable Income" else "credits"
            print(f"  {res.title()}:     {sign}{net:>7,.1f} {unit}")

    # Fleet (ships at this planet)
    ships = planet_info.get('ships', {})
    if ships and len(ships) > 0:
        print("\nDocked Fleet:")
        for ship_type, count in ships.items():
            print(f"  {ship_type:<15}: {count} ship(s)")

    # Resource flow (from database)
    resource_flow = calculate_resource_flow(planet_id, db_conn)
    if resource_flow:
        print("\nNet Resource Flow (per turn):")
        for res, net in resource_flow.items():
            sign = "+" if net >= 0 else ""
            unit = "tonnes" if res != 'taxable_income' else "credits"
            print(f"  {res.title()}:     {sign}{net:,.1f} {unit}")

    # Footer with actions
    print("\n" + "=" * 50)
    print("Available Actions:")
    print("  [1] Return to Home Menu")
    print("  [2] View other planets")
    action = input("\nEnter choice: ").strip()

    if action == "2":
        # Show list of all player planets
        cursor.execute("""
            SELECT p.planet_id, s.name as system_name, p.name as planet_name
            FROM planets p
            JOIN systems s ON p.system_id = s.system_id
            WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
        """)
        all_planets = cursor.fetchall()

        if all_planets:
            for idx, (pid, sys_name, pname) in enumerate(all_planets, 1):
                print(f"  [{idx}] {sys_name}-{pname}")
            choice = input("\nEnter planet number to view: ").strip()
            if choice.isdigit():
                select_idx = int(choice) - 1
                if 0 <= select_idx < len(all_planets):
                    display_planet_details(all_planets[select_idx][0])

    elif action == "1":
        pass


def handle_battle_screen():
