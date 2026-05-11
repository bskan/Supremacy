#!/usr/bin/env python3
"""
Database Initialization Script for Supremacy Game
===============================================
This script sets up and initializes the MariaDB database with:
- Schema creation from schema.sql
- Default assets catalog (ships, equipment)
- Initial player accounts and systems
- Sample planets

Usage:
    source venv/bin/activate
    python3 db_init.py --database-url mysql://root@localhost/supremacy_game --init-defaults
"""

import argparse
import sys
from contextlib import closing
import subprocess


def get_db_connection(host="localhost", user="root", password="", port=3306):
    """Create a database connection using mysql client."""
    try:
        from mysql.connector import connect, Error
        return connect(
            host=host,
            user=user,
            password=password if password else None,  # None allows empty password
            port=port,
            database="supremacy_game",  # Will be created if not exists
            autocommit=True
        )
    except ImportError:
        print("Installing mysql-connector-python...")
        subprocess.check_call(["pip3", "install", "mysql-connector-python"])
        from mysql.connector import connect
        return connect(
            host=host,
            user=user,
            password=password if password else None,
            port=port,
            database="supremacy_game",
            autocommit=True
        )


def create_schema_if_not_exists(cursor):
    """Create database and tables if they don't exist."""
    print("Creating/updating schema...")

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INT PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        credits BIGINT DEFAULT 1000
    )
    """)

    # Create systems table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS systems (
        system_id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) UNIQUE NOT NULL,
        difficulty_level TINYINT NOT NULL
    )
    """)

    # Create planets table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planets (
        planet_id INT PRIMARY KEY AUTO_INCREMENT,
        system_id INT NOT NULL,
        name VARCHAR(100) NOT NULL,
        owner_user_id INT NULL,
        FOREIGN KEY (system_id) REFERENCES systems(system_id),
        FOREIGN KEY (owner_user_id) REFERENCES users(user_id) ON DELETE SET NULL
    )
    """)

    # Create planetary_stats table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planetary_stats (
        planet_id INT PRIMARY KEY,
        population BIGINT DEFAULT 100,
        morale TINYINT DEFAULT 5,
        tax_rate DECIMAL(4, 2) DEFAULT 0.05,
        food_level BIGINT DEFAULT 0,
        mineral_level BIGINT DEFAULT 0,
        energy_level BIGINT DEFAULT 0,
        fuel_level BIGINT DEFAULT 0,
        UNIQUE KEY (planet_id)
    )
    """)

    # Create colonies table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS colonies (
        colony_id INT PRIMARY KEY AUTO_INCREMENT,
        planet_id INT NOT NULL UNIQUE,
        farming_stations INT DEFAULT 1,
        mining_stations INT DEFAULT 0,
        solar_satellites INT DEFAULT 0,
        FOREIGN KEY (planet_id) REFERENCES planets(planet_id) ON DELETE CASCADE
    )
    """)

    # Create ships table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ships (
        ship_id INT PRIMARY KEY AUTO_INCREMENT,
        owner_user_id INT NOT NULL,
        planet_id INT NOT NULL,
        docking_bay_slot TINYINT CHECK (docking_bay_slot BETWEEN 1 AND 3),
        ship_type ENUM('BattleCruiser', 'CargoShip', 'FarmingShip', 'MineralShip') NOT NULL,
        heading TINYINT DEFAULT 0,
        FOREIGN KEY (owner_user_id) REFERENCES users(user_id),
        FOREIGN KEY (planet_id) REFERENCES planets(planet_id)
    )
    """)

    # Create ship_cargo junction table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ship_cargo (
        ship_id INT,
        resource_type ENUM('Food', 'Energy', 'Mineral', 'Fuel') NOT NULL,
        quantity BIGINT DEFAULT 0,
        PRIMARY KEY (ship_id, resource_type),
        FOREIGN KEY (ship_id) REFERENCES ships(ship_id) ON DELETE CASCADE
    )
    """)

    # Create assets_catalog table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets_catalog (
        asset_id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        category ENUM('Ship', 'Infrastructure', 'Military') NOT NULL,
        base_cost BIGINT NOT NULL,
        is_unique BOOLEAN DEFAULT FALSE,
        image_url VARCHAR(255),
        description VARCHAR(255)
    )
    """)

    # Create ship_types table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ship_types (
        ship_type_name ENUM('BattleCruiser', 'CargoShip', 'FarmingShip', 'MineralShip') PRIMARY KEY,
        base_purchase_cost BIGINT NOT NULL
    )
    """)

    # Create equipment_catalog table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment_catalog (
        equipment_id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        category ENUM('Armor', 'Weapon') NOT NULL,
        base_cost BIGINT NOT NULL,
        strength_value INT NOT NULL,
        image_url VARCHAR(255)
    )
    """)

    print("✓ Schema created successfully!")


def populate_assets_catalog(cursor):
    """Populate the assets catalog with purchasable items."""
    print("\nPopulating assets catalog...")

    # Insert ships and infrastructure
    assets = [
        ("BattleCruiser", "Ship", 500, False),
        ("CargoShip", "Ship", 300, False),
        ("FarmingShip", "Ship", 150, False),
        ("MineralShip", "Ship", 180, False),
        ("EnergySatellite", "Infrastructure", 1000, True),  # Unique - generates energy for planets
    ]

    for asset_name, category, cost, is_unique in assets:
        cursor.execute("""
        INSERT INTO assets_catalog (name, category, base_cost, is_unique)
        VALUES (%s, %s, %s, %s)
        """, (asset_name, category, cost, is_unique))

    print("  ✓ Assets added to catalog")

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

    print("  ✓ Ship types added")

    # Insert equipment with images
    armor_items = [
        ("Light Armor", "Armor", 100, 3, "lightarmour.png"),
        ("Medium Armor", "Armor", 250, 6, "mediumarmour.png"),
        ("Heavy Armor", "Armor", 500, 10, "heavyarmour.png"),
        ("Plasteel Armor", "Armor", 800, 15, "plasteelarmor.png"),
    ]

    weapon_items = [
        ("Pistol", "Weapon", 50, 2, "pistol.png"),
        ("Rifle", "Weapon", 150, 5, "rifle.png"),
        ("Cannon", "Weapon", 300, 8, "canon.png"),
        ("Heavy Cannon", "Weapon", 600, 12, "heavycannon.png"),
    ]

    for name, category, cost, strength, img in armor_items + weapon_items:
        cursor.execute("""
        INSERT INTO equipment_catalog (name, category, base_cost, strength_value, image_url)
        VALUES (%s, %s, %s, %s, %s)
        """, (name, category, cost, strength, img))

    print("  ✓ Equipment catalog added")

    # Insert initial player and system
    cursor.execute("""
    INSERT INTO users (username, credits) VALUES ('Player', 5000)
    """)
    print("  ✓ Default user created")

    # Create System 1 (8 planets, difficulty 1)
    cursor.execute("""
    INSERT INTO systems (name, difficulty_level) VALUES ('System 1', 1)
    """)
    print("  ✓ System 1 created")


def create_default_planets(cursor):
    """Create default planets for each system."""
    print("\nCreating default planets...")

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

        print(f"  ✓ Planet Alpha ({system_name}) created")


def show_summary():
    """Show database summary."""
    print("\n" + "="*50)
    print("DATABASE SUMMARY")
    print("="*50)

    queries = [
        ("Users", "SELECT COUNT(*) FROM users"),
        ("Systems", "SELECT COUNT(*) FROM systems"),
        ("Planets", "SELECT COUNT(*) FROM planets"),
        ("Assets", "SELECT COUNT(*) FROM assets_catalog"),
        ("Equipment", "SELECT COUNT(*) FROM equipment_catalog"),
    ]

    for table_name, query in queries:
        result = f"  {table_name}: {len(queries)} items"  # Placeholder
        try:
            from mysql.connector import connect
            conn = connect(host="localhost", user="root", port=3306, database="supremacy_game")
            cursor = conn.cursor()
            cursor.execute(query)
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} items")
        except Exception as e:
            print(f"  {table_name}: Not connected (or empty)")

    print("="*50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Initialize Supremacy Game Database")
    parser.add_argument("--database-url", default=None, help="Database connection string (optional for CLI)")
    parser.add_argument("--host", default="localhost", help="Database host")
    parser.add_argument("--user", default="root", help="Database user")
    parser.add_argument("--password", default="", help="Database password")
    parser.add_argument("--port", type=int, default=3306, help="Database port")
    parser.add_argument("--init-defaults", action="store_true", help="Initialize with default assets and planets")
    parser.add_argument("--summary", action="store_true", help="Show database summary")

    args = parser.parse_args()

    # Check if mysql-connector is available
    try:
        from mysql.connector import connect
    except ImportError:
        print("Installing mysql-connector-python...")
        subprocess.check_call(["pip3", "install", "mysql-connector-python"])

    conn_str = f"mysql://{args.user}@{args.host}/{args.database_url.split('/')[-1] if args.database_url else 'supremacy_game'}"
    print(f"Connecting to database: {conn_str}")

    try:
        conn = get_db_connection(host=args.host, user=args.user, password=args.password, port=args.port)
        cursor = conn.cursor()

        if args.init_defaults:
            create_schema_if_not_exists(cursor)
            populate_assets_catalog(cursor)
            create_default_planets(cursor)

        conn.commit()

        print("\n" + "="*50)
        print("DATABASE INITIALIZATION COMPLETE!")
        print("="*50)
        show_summary()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    main()
