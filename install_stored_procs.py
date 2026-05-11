#!/usr/bin/env python3
"""
Installation script for Supremacy Game stored procedures.
Run: python install_stored_procs.py
"""

import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "supremacy",
    "password": "",  # Empty password per your setup
    "database": "supremacy_game"
}

# Stored procedure SQL content - refactored for MariaDB compatibility
PROCEDURE_SQL = """
DROP PROCEDURE IF EXISTS process_player_turns_batch;

DELIMITER //

CREATE PROCEDURE process_player_turns_batch(IN p_user_id INT)
BEGIN
    -- Process turn for all player planets in a single UPDATE statement
    -- Calculates and applies food, energy, fuel, and population changes

    UPDATE planetary_stats ps
    JOIN planets p ON ps.planet_id = p.planet_id
    LEFT JOIN colonies c ON p.planet_id = c.planet_id
    WHERE p.owner_user_id = p_user_id

    SET
        -- Food: production from farms minus population consumption
        food_level = FLOOR(ps.food_level + 15 * COALESCE(c.farming_stations, 0) - ps.population * 0.5),
        -- Energy: solar satellites output minus machinery consumption
        energy_level = FLOOR(ps.energy_level + 12 * COALESCE(c.solar_satellites, 0) - ps.population * 0.3),
        -- Fuel: from mineral byproducts
        fuel_level = FLOOR(ps.fuel_level + 8 * COALESCE(c.mining_stations, 0)),

        -- Population: growth based on morale when food adequate (>= -20), starvation decline otherwise
        population = CASE
            WHEN ps.food_level >= -20 THEN
                MAX(0, ps.population + ROUND(ps.population * (COALESCE(ps.morale, 5) / 10.0) * 0.005, 0))
            ELSE
                MAX(0, ps.population - ROUND(ps.population * ABS(ps.food_level) / 25.0, 0))
            END;

END//

DELIMITER ;
"""


def main():
    print("Installing stored procedures...")

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        cursor.execute(PROCEDURE_SQL)
        conn.commit()

        # Verify procedure was created
        cursor.execute("SHOW PROCEDURE STATUS WHERE Db = 'supremacy_game'")
        procedures = cursor.fetchall()

        print(f"\nStored procedures installed successfully!")
        print(f"Found {len(procedures)} procedure(s):")
        for proc in procedures:
            if isinstance(proc, dict):
                print(f"  - {proc.get('Name', 'N/A')}")
            else:
                print(f"  - {proc[0]}")

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
