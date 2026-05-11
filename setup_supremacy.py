#!/usr/bin/env python3
"""Setup script for Supremacy game - installs dependencies and initializes database."""

import subprocess
import sys
import os

# Activate venv
venv_path = '/home/bskan/Supremacy/venv'
activate_script = f'{venv_path}/bin/activate'

def run_command(cmd, desc):
    """Run a command and print progress."""
    print(f"\n[{desc}]")
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(result.stdout.strip())
    else:
        print(f"Error: {result.stderr.strip()}")
    return result.returncode == 0

def main():
    # Install Python dependencies
    success = run_command(
        f"source {activate_script} && pip install fastapi uvicorn mysql-connector-python pydantic",
        "Installing Python dependencies"
    )

    if not success:
        print("Failed to install dependencies. Continuing anyway...")

    # Test connection to MariaDB
    print("\n[Testing MariaDB connection]")
    test_result = run_command(
        f"source {activate_script} && python3 -c "
        "\"import mysql.connector; c=mysql.connector.connect(host='localhost',user='supremacy',password='Supremacy2024'); "
        "print('Connected:', c.server_version)\" 2>&1",
        "Testing DB connection"
    )

    # Initialize database with init_db.sql
    print("\n[Initializing MariaDB database]")
    db_result = run_command(
        f"source {activate_script} && python3 -c "
        "\"import mysql.connector; "
        "from pathlib import Path; sql=Path('init_db.sql').read_text(); "
        "c=mysql.connector.connect(host='localhost',user='supremacy',password='Supremacy2024'); "
        "c.execute('DROP DATABASE IF EXISTS supremacy_game'); "
        "c.execute('CREATE DATABASE supremacy_game CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'); "
        "c.database='supremacy_game'; c.execute(sql); "
        "print('\\nDatabase initialized successfully!')\"",
        "Creating Supremacy database"
    )

    if db_result:
        print("\n" + "="*50)
        print("SUPREMACY SETUP COMPLETE!")
        print("="*50)
        print("\nTo start the API server:")
        print("  source venv/bin/activate")
        print("  python3 api_backend.py uvicorn --app/api_backend:app --host 0.0.0.0 --port 8000")
        print("\nAPI Documentation available at: http://localhost:8000/docs")
    else:
        print("\nDatabase setup failed - check error messages above")

if __name__ == "__main__":
    main()
