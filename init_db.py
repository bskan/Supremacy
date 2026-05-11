#!/usr/bin/env python3
"""
Database Initialization Verification Script for Supremacy Game.
Verifies that the database is properly initialized with all data.

Usage:
  python init_db.py        # Verify current state, reinitialize if empty
  python init_db.py --clear  # Clear and reinitialize from scratch
"""

import subprocess
import sys


def run_query(query_sql):
    """Run a SQL query using MySQL CLI via pipe."""
    result = subprocess.run(
        ['cat', '-'],
        capture_output=True,
        text=True,
        input=query_sql
    )
    mysql_result = subprocess.run(
        ['mysql', '--database=supremacy_game'],
        input=result.stdout,
        capture_output=True,
        text=True
    )
    return mysql_result


def run_sql_file(sql_file):
    """Run a SQL file using MySQL CLI via stdin pipe."""
    result = subprocess.run(
        ['cat', sql_file],
        capture_output=True,
        text=True
    )
    mysql_result = subprocess.run(
        ['mysql', '--database=supremacy_game'],
        input=result.stdout,
        capture_output=True,
        text=True
    )
    return mysql_result


def verify_database():
    """Verify the database is initialized with expected data."""

    sql = """SELECT 'users' as tbl, COUNT(*) as count FROM supremacy_game.users
    UNION ALL SELECT 'systems', COUNT(*) FROM supremacy_game.systems
    UNION ALL SELECT 'planets', COUNT(*) FROM supremacy_game.planets
    UNION ALL SELECT 'assets_catalog', COUNT(*) FROM supremacy_game.assets_catalog
    ORDER BY tbl;"""

    result = run_query(sql)

    if result.returncode != 0:
        print(f"Error querying database:")
        print(result.stderr)
        return False

    # Parse output - lines are separated by tabs (MySQL default format)
    # Skip header line if present
    lines = result.stdout.strip().split('\n')

    counts = {'users': 0, 'systems': 0, 'planets': 0, 'assets_catalog': 0}
    for line in lines:
        # Split by first tab (MySQL separates columns with tabs)
        if '\t' in line:
            parts = line.split('\t', 1)  # Split only on first tab
            if len(parts) >= 2:
                tbl = parts[0].strip()
                count_str = parts[1].strip()
                # Skip header row (tbl, count)
                if tbl.lower() != 'tbl':
                    try:
                        counts[tbl] = int(count_str)
                    except ValueError:
                        pass

    print("Database Status:")
    for tbl, expected in [('users', 1), ('systems', 2), ('planets', 24), ('assets_catalog', 5)]:
        actual = counts.get(tbl, 0)
        status = "OK" if actual == expected else f"EMPTY (expected {expected})"
        print(f"  {tbl}: {status}")

    # If planets is empty, reinitialize from scratch
    if counts['planets'] == 0:
        sql_init = '/Users/benskan/Documents/ClaudeDev/init_db.sql'

        print("\nReinitializing database...")
        result = run_sql_file(sql_init)

        if result.returncode != 0:
            print(f"Failed to reinitialize:")
            print(result.stderr[:1000] if result.stderr else "(empty)")
            return False

        print("\nReinitialized database from init_db.sql")

    # Show summary
    print("\n" + "=" * 50)
    print("DATABASE INITIALIZATION COMPLETE!")
    print("=" * 50)

    # Show assets list
    assets_sql = "SELECT name, category, base_cost FROM supremacy_game.assets_catalog ORDER BY base_cost;"
    result = run_query(assets_sql)

    print("\nAssets in catalog:")
    for line in result.stdout.strip().split('\n'):
        if line.strip():
            print(f"  {line}")

    return True


def clear_database():
    """Clear the database and reinitialize from scratch."""

    sql_clear = "DROP DATABASE IF EXISTS supremacy_game; CREATE DATABASE supremacy_game CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

    result = subprocess.run(
        ['mysql', '--database=supremacy_game', '--execute', sql_clear],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("Cleared database successfully")
    else:
        print(f"Failed to clear database:")
        print(result.stderr)
        return False

    # Now run initialization
    sql_init = '/Users/benskan/Documents/ClaudeDev/init_db.sql'

    print(f"\nInitializing database from {sql_init}...")
    result = subprocess.run(
        ['mysql', '--database=supremacy_game'] + ['--execute', f'cat {sql_init}'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Failed to initialize:")
        print(result.stderr[:1000] if result.stderr else "(empty)")
        return False

    # Show verification summary
    verify_database()
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize and verify Supremacy Game database")
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing data and reinitialize'
    )

    args = parser.parse_args()

    if args.clear:
        sql_clear = "DROP DATABASE IF EXISTS supremacy_game; CREATE DATABASE supremacy_game CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        result = subprocess.run(['mysql', '--database=supremacy_game', '--execute', sql_clear])
        if result.returncode != 0:
            print("Failed to clear database")
            sys.exit(1)

        with open('/Users/benskan/Documents/ClaudeDev/init_db.sql') as f:
            init_sql = f.read()
        mysql_result = subprocess.run(
            ['mysql', '--database=supremacy_game'],
            input=init_sql,
            capture_output=True,
            text=True
        )
        if mysql_result.returncode != 0:
            print(f"Failed to initialize:\n{mysql_result.stderr}")
            sys.exit(1)

        print("Database initialized successfully!")
        verify_database()
        success = True
    else:
        success = verify_database()

    sys.exit(0 if success else 1)
