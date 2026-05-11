# Stored Procedure Migration Plan

## Overview
Migrate game simulation logic from Python to MySQL stored procedures for efficient batch processing when scaling planets.

## Core Logic Functions (Python) -> Stored Procedures (MySQL)

### 1. `simulate_planet_turn` (Currently in supremacy_cli.py and game_engine.py)
**Current Implementation:** Loop through planets, calculate resource flows, apply changes individually.

**Stored Procedure Equivalent:** Single procedure that:
- Accepts player_user_id
- Uses table-level operations with JOINs
- Applies MAX() constraints to prevent negative values
- Returns aggregated statistics

### 2. `calculate_resource_flow` (game_engine.py)
Calculates production/consumption per planet.

**Migration Strategy:** 
- Keep in Python for flexibility (infrastructure lookups, equipment stats)
- OR: Create stored function that queries database and returns resource deltas

### 3. `run_turn` (game_engine.py)  
Runs simulation across all owned planets.

**Stored Procedure Equivalent:**
```sql
CREATE PROCEDURE process_all_player_turns (IN p_user_id INT)
BEGIN
    -- Simulate production for all player planets in one query
    UPDATE planetary_stats ps
    JOIN (
        SELECT c.planet_id,
               SUM(c.farming_stations * 15.0) as total_food_produced,
               SUM(c.mining_stations * 8.0) as total_mineral_produced,
               SUM(c.solar_satellites * 12.0) as total_energy_produced,
               SUM(cm.strength_value) as total_weapons_value, -- For fuel calc
               (SELECT COUNT(*) FROM ships s 
                WHERE s.planet_id = c.planet_id) as ship_count
        FROM colonies c
        JOIN planets p ON c.planet_id = p.planet_id
        WHERE p.owner_user_id = %s
    ) prod ON ps.planet_id = prod.planet_id,
    (SELECT population FROM planetary_stats WHERE planet_id = ps.planet_id) pop,
    equipment e ON 1=0 -- Subquery for equipment stats
    SET 
        -- Calculate changes using derived values from JOIN
        -- Apply MAX(0, ...) constraints
    
    -- Update in single batch operation
    SELECT @stats.total_food_produced as total_produced, ...;
END
```

### 4. `get_planet_state` (game_engine.py)
Reads planet information and current state.

**Keep as-is:** This is a READ operation - no need for stored procedure. Use simple queries.

## Database Schema Needed for Stored Procedures

We need to track equipment on planets currently. Let me check the schema:
