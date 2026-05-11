#!/usr/bin/env python3
"""
Stored Procedure Wrapper Module

Provides Python functions that call MySQL stored procedures.
Use this module when the application should execute batch turn processing
via stored procedures instead of row-by-row Python logic.
"""

from typing import Dict, Any, Optional, List
import mysql.connector


class StoredProcedureExecutor:
    """
    Executor for MySQL stored procedures used in Supremacy game simulation.
    """

    def __init__(self, host: str = "supremacy-db", user: str = "supremacy_user",
                 password: Optional[str] = None, port: int = 3306, database: str = "supremacy_game"):
        self.config = {
            "host": host,
            "user": user,
            "password": password,
            "port": port,
            "database": database,
            "autocommit": True
        }

    def get_connection(self):
        """Get or recreate a database connection."""
        return mysql.connector.connect(**self.config)

    # =====================================================
    # Turn Processing Functions (Stored Procedures)
    # =====================================================

    def process_all_player_turns(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Call the stored procedure to process all player planets in a single batch.

        Args:
            user_id: ID of the player to process

        Returns:
            Dict with turn results including per-planet changes and totals
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.callproc("process_all_player_turns", (user_id,))

            # Fetch result set from stored procedure
            result = None
            for data in cursor.stored_results():
                result = data.fetchone()

            # Calculate totals from the update operation
            rows_affected = cursor.rowcount if hasattr(cursor, 'rowcount') else 0

            return {
                "turn_complete": True,
                "rows_updated": rows_affected,
                "message": f"Processed turn for user {user_id}"
            }

        except Exception as e:
            print(f"Error calling process_all_player_turns: {e}")
            return None

    def simulate_single_planet(self, planet_id: int) -> Optional[Dict[str, Any]]:
        """
        Call the stored procedure to simulate a single planet's turn.

        Args:
            planet_id: ID of the planet to simulate

        Returns:
            Dict with population_delta and resource changes
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Call stored procedure with OUT parameters
            call_args = [planet_id, 0, 0, 0, 0]  # planet_id + 4 zeroed out for OUT params
            cursor.callproc("simulate_single_planet", call_args)

            # Fetch result set from stored procedure
            result_set = None
            for data in cursor.stored_results():
                result_set = data.fetchone()

            # Reset OUT parameters to default values if no result
            if not result_set:
                result_set = [0, 0, 0, 0]

            population_delta, food_change, energy_change, fuel_change = result_set

            return {
                "planet_id": planet_id,
                "population_delta": int(population_delta),
                "food_change": float(food_change),
                "energy_change": float(energy_change),
                "fuel_change": float(fuel_change)
            }

        except Exception as e:
            print(f"Error calling simulate_single_planet: {e}")
            return None

    # =====================================================
    # Legacy Functions (Python-based, for backward compatibility)
    # =====================================================

    def calculate_resource_flow_legacy(self, planet_id: int) -> Dict[str, float]:
        """
        Legacy Python function for calculating resource flow.
        Kept for backward compatibility; use stored procedures for batch processing.

        Args:
            planet_id: The ID of the planet to calculate for

        Returns:
            Dict with resource names as keys and net change values
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Query colony infrastructure
            cursor.execute("""
                SELECT c.farming_stations, c.mining_stations, c.solar_satellites,
                       ps.population, COALESCE(ps.morale, 5) as morale
                FROM planets p
                JOIN colonies c ON p.planet_id = c.planet_id
                JOIN planetary_stats ps ON p.planet_id = ps.planet_id
                WHERE p.planet_id = %s
            """, (planet_id,))

            row = cursor.fetchone()
            if not row:
                return {'food': 0, 'mineral': 0, 'energy': 0, 'fuel': 0, 'taxable_income': 0}

            farming_stations, mining_stations, solar_satellites, population, morale = row

            # Calculate resource flow
            food_produced = farming_stations * 15.0
            minerals_produced = mining_stations * 8.0
            energy_produced = solar_satellites * 12.0

            food_consumed = population * 0.5
            energy_consumed = population * 0.3

            fuel_from_minerals = minerals_produced * 0.5
            fuel_from_food = food_produced * 0.2
            total_fuel_produced = fuel_from_minerals + fuel_from_food

            return {
                'food': round(food_produced - food_consumed, 2),
                'mineral': round(minerals_produced, 2),
                'energy': round(energy_produced - energy_consumed, 2),
                'fuel': round(total_fuel_produced, 2)
            }

        except Exception as e:
            print(f"Error calculating resource flow: {e}")
            return {'food': 0, 'mineral': 0, 'energy': 0, 'fuel': 0}

    def get_connection_string(self):
        """Return the connection configuration dictionary."""
        return self.config


# Convenience function for direct use
def execute_stored_procedures(host: str = "supremacy-db", user: str = "supremacy_user",
                               password: Optional[str] = None, port: int = 3306,
                               database: str = "supremacy_game") -> StoredProcedureExecutor:
    """
    Create and return a StoredProcedureExecutor instance.

    Args:
        host: Database hostname
        user: Database username
        password: Database password (optional)
        port: Database port
        database: Database name

    Returns:
        StoredProcedureExecutor instance
    """
    return StoredProcedureExecutor(host=host, user=user, password=password,
                                    port=port, database=database)


# Example usage when stored procedures are NOT yet installed:
if __name__ == "__main__":
    import sys

    # Check if stored procedures exist before using them
    try:
        sp = execute_stored_procedures()
        conn = sp.get_connection()
        cursor = conn.cursor()

        cursor.execute("SHOW PROCEDURE STATUS WHERE Db = 'supremacy_game'")
        procedures = cursor.fetchall()
        conn.close()

        if not procedures:
            print("Stored procedures not found in database.")
            print("Run: mysql -h supremacy-db -u supremacy < stored_procedures.sql")
            sys.exit(1)

        print(f"Found {len(procedures)} stored procedures:")
        for p in procedures:
            print(f"  - {p['Definer']}: {p['Db']}")

    except Exception as e:
        print(f"Connection failed: {e}")
        print("Stored procedure wrapper is ready, but database connection failed.")
