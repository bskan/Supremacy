#!/usr/bin/env python3
"""
Installation script for Supremacy Game stored procedures.
Run: python install_stored_procs.py

Uses mysql CLI to install (DELIMITER is a client-side command).
"""

import mysql.connector
import subprocess
import sys
import os

DB_CONFIG = {
    "host": "localhost",
    "user": "supremacy",
    "password": "",
    "database": "supremacy_game"
}

PROCEDURE_SQL = """
DROP PROCEDURE IF EXISTS process_player_turns_batch;

DELIMITER //

CREATE PROCEDURE process_player_turns_batch(IN p_user_id INT)
BEGIN
    UPDATE planetary_stats ps
    JOIN planets p ON ps.planet_id = p.planet_id
    LEFT JOIN colonies c ON p.planet_id = c.planet_id
    SET
        food_level = FLOOR(ps.food_level + 15 * COALESCE(c.farming_stations, 0) - ps.population * 0.5),
        energy_level = FLOOR(ps.energy_level + 12 * COALESCE(c.solar_satellites, 0) - ps.population * 0.3),
        fuel_level = FLOOR(ps.fuel_level + 8 * COALESCE(c.mining_stations, 0)),
        population = CASE
            WHEN ps.food_level >= -20 THEN
                GREATEST(0, ps.population + ROUND(ps.population * (COALESCE(ps.morale, 5) / 10.0) * 0.005, 0))
            ELSE
                GREATEST(0, ps.population - ROUND(ps.population * ABS(ps.food_level) / 25.0, 0))
            END;
END//

DELIMITER ;
"""


def main():
    print("Installing stored procedures...")

    # Write procedure SQL to a temp file (DELIMITER requires mysql CLI)
    sql_file = "/tmp/_supremacy_procs.sql"
    with open(sql_file, 'w') as f:
        f.write(PROCEDURE_SQL)

    try:
        cmd = [
            "mysql",
            f"-h{DB_CONFIG['host']}", f"-u{DB_CONFIG['user']}",
            f"-p{DB_CONFIG['password']}", f"{DB_CONFIG['database']}",
            f"<{sql_file}"
        ]
        result = subprocess.run(" ".join(cmd), shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error: {result.stderr.strip()}")
            sys.exit(1)

        # Verify procedure was created via mysql-connector
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SHOW PROCEDURE STATUS WHERE Db = 'supremacy_game'")
        procedures = cursor.fetchall()
        cursor.close()
        conn.close()

        names = [p[1] for p in procedures]
        print(f"\nStored procedures installed successfully!")
        print(f"Found {len(names)} procedure(s): {names}")

    except subprocess.CalledProcessError as e:
        print(f"Error running mysql CLI: {e}")
        sys.exit(1)
    finally:
        try:
            os.unlink(sql_file)
        except OSError:
            pass


if __name__ == "__main__":
    main()
