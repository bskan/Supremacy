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
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_planet_id INT;
    DECLARE v_farming INT;
    DECLARE v_mining INT;
    DECLARE v_solar INT;
    DECLARE v_population INT;
    DECLARE v_morale DECIMAL(10,2);
    DECLARE v_tax_rate DECIMAL(10,2);
    DECLARE v_food_level DECIMAL(10,2);
    DECLARE v_energy_level DECIMAL(10,2);
    DECLARE v_fuel_level DECIMAL(10,2);
    DECLARE v_fleet_count INT;
    DECLARE v_food_prod INT;
    DECLARE v_fuel_prod INT;
    DECLARE v_food_consume DECIMAL(10,2);
    DECLARE v_energy_consume DECIMAL(10,2);
    DECLARE v_fuel_consume DECIMAL(10,2);
    DECLARE v_minerals INT;
    DECLARE v_mining INT;
    DECLARE v_pop_delta INT;
    DECLARE v_morale_delta DECIMAL(10,2);
    DECLARE v_taxable_income DECIMAL(10,2);
    DECLARE v_fleet_consumption INT;

    DECLARE planet_cursor CURSOR FOR
        SELECT ps.planet_id,
               COALESCE(c.farming_stations, 0) AS farming,
               COALESCE(c.mining_stations, 0) AS mining,
               COALESCE(c.solar_satellites, 0) AS solar,
               ps.population, ps.morale, ps.tax_rate,
               ps.food_level, ps.energy_level, ps.fuel_level
        FROM planetary_stats ps
        JOIN planets p ON ps.planet_id = p.planet_id
        LEFT JOIN colonies c ON p.planet_id = c.planet_id
        WHERE p.owner_user_id = p_user_id
        ORDER BY ps.planet_id;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN planet_cursor;

    planet_loop: LOOP
        FETCH planet_cursor INTO v_planet_id, v_farming, v_mining, v_solar, v_population, v_morale, v_tax_rate, v_food_level, v_energy_level, v_fuel_level;
        IF done THEN LEAVE planet_loop; END IF;

        -- Get fleet count for this planet (all ships, regardless of owner)
        SELECT COALESCE((SELECT COUNT(*) FROM ships s WHERE s.planet_id = v_planet_id), 0)
        INTO v_fleet_count;

        -- Production
        SET v_food_prod = 15 * v_farming;
        SET v_minerals = 8 * v_mining;
        SET v_fuel_prod = FLOOR(v_minerals * 0.5 + v_food_prod * 0.2);

        -- Consumption (population + ships)
        SET v_food_consume = v_population * 0.5 + v_fleet_count * 1;
        SET v_energy_consume = v_population * 0.3 + v_fleet_count * 2;
        SET v_fuel_consume = v_fleet_count * 0.8;

        -- Net changes
        SET v_pop_delta = 0;
        SET v_morale_delta = 0;

        IF v_food_level >= 0 AND v_energy_level >= 0 AND v_fuel_level >= 0 THEN
            -- Positive morale: gain with taxable income
            SET v_taxable_income = GREATEST(0, v_food_prod - v_food_consume + v_fuel_prod - v_fuel_consume);
            SET v_pop_delta = ROUND(v_population * (v_morale / 10.0) * 0.005 * (1 + v_taxable_income / 10000.0), 0);
            SET v_morale_delta = ROUND(v_taxable_income / 500.0, 2);
        ELSE
            -- Under deficit: lose morale and population
            SET v_morale_delta = -0.5;
            IF v_food_level < 0 THEN
                SET v_pop_delta = -FLOOR(v_population * ABS(v_food_level) / 50.0);
            END IF;
        END IF;

        -- Apply updates
        UPDATE planetary_stats
        SET
            food_level = FLOOR(v_food_level + v_food_prod - v_food_consume),
            energy_level = FLOOR(v_energy_level + v_solar * 12 - v_energy_consume),
            fuel_level = FLOOR(v_fuel_level + v_fuel_prod - v_fuel_consume),
            mineral_level = COALESCE(mineral_level, 0) + v_minerals,
            morale = GREATEST(0, LEAST(10, v_morale + v_morale_delta)),
            population = GREATEST(0, v_population + v_pop_delta)
        WHERE planet_id = v_planet_id;
    END LOOP;

    CLOSE planet_cursor;
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
