# run_tests.py - Updated for MySQL/MariaDB with empty password
import os
import subprocess
from mysql.connector import connect  # Use the 'connect' function instead of importing objects directly
from game_engine import calculate_resource_flow, process_ship_movement, resolve_combat, ai_opponent_turn

DATABASE_URL = "mysql://root@localhost/supremacy_game"  # Updated for MySQL/MariaDB with empty password

def get_connection():
    """Create a database connection."""
    try:
        return connect(
            host="localhost",
            user="supremacy",  # Use supremacy user (no password)
            port=3306,
            database="supremacy_game"
        )
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None


def setup_database():
    """Initializes the database and runs the schema/seed script."""
    print("--- 1. Setting up Database Schema and Initial Data ---")

    # Initialize using init_db.py for clean slate
    result = subprocess.run(
        ["python3", "init_db.py"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

    if result.returncode != 0:
        print(f"FATAL: Database initialization failed:\n{result.stderr}")
        return False

    print("Database initialized successfully!")
    return True


def run_integration_test():
    """Simulates a full turn cycle to test the interaction between components."""
    import subprocess

    print("\n\n================================================")
    print("   STARTING END-TO-END INTEGRATION TEST CYCLE")
    print("================================================\n")

    # 0. SETUP (Must run first)
    if not setup_database():
        return

    conn = get_connection()
    if not conn:
        print("Skipping tests - cannot connect to database")
        return

    cursor = conn.cursor()

    # Assume Planet 1 exists and is owned by User 1 (The player).
    PLAYER_ID = 1
    PLANET_START_ID = 1  # Must match the seeded start planet ID

    print("\n--- PHASE 1: Player Initial State Check & Resource Flow Test ---")
    initial_flow = calculate_resource_flow(PLANET_START_ID, conn)
    print(f"Resource Flow (Planet {PLANET_START_ID}):")
    for res, val in initial_flow.items():
        print(f"  {res}: {val}")


    # Verify database state
    print("\n--- PHASE 1b: Database State Verification ---")
    cursor.execute("SELECT COUNT(*) FROM planets WHERE owner_user_id = %s", (PLAYER_ID,))
    player_planets_count = cursor.fetchone()[0]
    print(f"Player's planets: {player_planets_count}")

    cursor.execute("""
        SELECT p.planet_id, p.name, ps.population
        FROM planets p
        JOIN planetary_stats ps ON p.planet_id = ps.planet_id
        ORDER BY p.planet_id LIMIT 3
    """)
    sample_planets = cursor.fetchall()
    for p in sample_planets:
        print(f"  Planet {p[0]}: {p[1]} (pop: {p[2]})")


    # --- Action Sequence Simulation ---

    print("\n--- PHASE 2: Simulate Player Action - Ship Movement Test (Screen 1) ---")
    # Move ship 1 from Planet 1 to a hypothetical planet 2.
    move_result = process_ship_movement(ship_id=1, destination_planet_id=PLANET_START_ID + 1)
    print(f"Ship movement result: {move_result}")


    print("\n--- PHASE 3: Simulate Player Action - Battle Test (Screen 7) ---")
    # Resolve combat on Planet 1 vs enemy on Planet 2.
    battle_result = resolve_combat(attacker_planet_id=PLAYER_ID, defender_planet_id=PLANET_START_ID + 1)
    print(f"Battle result: {battle_result}")


    print("\n--- PHASE 4: Simulate AI Opponent Turn (Full Game Loop Test) ---")
    # This call triggers the entire complex AI simulation logic.
    ai_result = ai_opponent_turn(db_conn=conn, ai_user_id=99)
    print(f"AI Simulation Report: {ai_result}")


    # Get final state of player's planets
    print("\n--- PHASE 5: Final State Check ---")
    cursor.execute("""
        SELECT p.planet_id, p.name, ps.population, ps.morale
        FROM planets p
        JOIN planetary_stats ps ON p.planet_id = ps.planet_id
        WHERE p.owner_user_id = %s
        ORDER BY p.planet_id
    """, (PLAYER_ID,))

    final_planets = cursor.fetchall()
    for p in final_planets:
        print(f"  Planet {p[0]} ({p[1]}): pop={p[2]}, morale={p[3]}")


    print("\n\n================================================")
    print("   INTEGRATION TEST COMPLETE.")
    print("================================================\n")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    run_integration_test()
