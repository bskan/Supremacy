# Stored Procedure Migration Guide for Supremacy Game

## Executive Summary

This document provides guidance on migrating game simulation logic from Python to MySQL stored procedures.

**Key Benefits:**
1. **Single query batch processing** - Update all planets in one `UPDATE` statement vs N individual queries
2. **Server-side computation** - Offload calculations from Python to MySQL (which is optimized for this)
3. **Atomic operations** - Transaction safety built into stored procedures
4. **Consolidated codebase** - Less duplication between game_engine.py and supremacy_cli.py

## Current Architecture (Python-based)

```python
# In game_engine.py:run_turn()
def run_turn(user_id):
    cursor = db_conn.cursor()
    cursor.execute("SELECT planet_id FROM planets WHERE owner_user_id = %s", (user_id,))
    planets = cursor.fetchall()

    for planet in planets:
        result = simulate_planet_turn(planet['planet_id'])  # Python loop
        total_food_produced += result.get('food_produced', 0)
        # ... accumulate totals ...

    db_conn.commit()
```

**Problem:** Each turn requires N SELECTs + N UPDATEs for N planets. This becomes inefficient at scale (100+ planets).

## Proposed Architecture (Stored Procedure-based)

### Option A: Full Migration to Stored Procedures

**Implementation steps:**
1. Install stored procedures (`mysql -u supremacy -h supremacy-db < stored_procedures.sql`)
2. Replace `simulate_planet_turn()` with calls to `process_all_player_turns()`
3. Remove individual UPDATE loops from Python code

**Example replacement:**
```python
# OLD: Python-based per-planet updates
for planet in planets:
    simulate_planet_turn(planet['planet_id'])  # N queries

# NEW: Single batch update via stored procedure
process_all_player_turns(user_id)  # 1 query (with optional OUT parameters for stats)
```

### Option B: Hybrid Approach (Recommended First Step)

Keep existing Python logic, but add stored procedure as alternative path.

**When to use stored procedures:**
- When running headless server mode
- For batch simulation scripts
- For performance monitoring and analytics

**Implementation:**
1. Add `stored_procedures_wrapper.py` module
2. Check which execution mode is active:
   ```python
   if settings.USE_STORED_PROCS:
       result = stored_procedures.process_all_player_turns(user_id)
   else:
       result = game_engine.run_turn(user_id)  # existing code
   ```

## Performance Comparison

| Approach | Query Count (100 planets) | Latency | Complexity |
|----------|--------------------------|---------|------------|
| **Current Python** | ~200 (100 SELECTs + 100 UPDATEs) | High | Medium |
| **Stored Procedure** | 1-3 (batched update) | Low | Low |

**Note:** Stored procedures work best when the game has matured and you have many planets to manage. For early-game development, the Python approach is fine.

## Migration Checklist

### Pre-migration
- [ ] Test current Python logic thoroughly
- [ ] Document all resource calculation formulas
- [ ] Create stored procedure SQL file (created: `stored_procedures.sql`)

### During migration
- [ ] Install stored procedures to database
- [ ] Update `game_engine.py` to call stored procedures
- [ ] Add error handling for stored procedure failures
- [ ] Remove unused Python simulation functions

### Post-migration
- [ ] Verify data consistency between old/new approaches
- [ ] Run performance benchmarks
- [ ] Clean up legacy code

## Implementation Files Created

1. **`stored_procedures.sql`** - MySQL DDL for all stored procedures
2. **`stored_procedures_wrapper.py`** - Python interface to stored procedures
3. **`migration_to_stored_procedures.md`** - Design notes and schema requirements

## Next Steps

Would you like me to:

1. **Install the stored procedures now?** (Test that they work correctly)
2. **Modify `game_engine.py` to use stored procedures?** (Full migration)
3. **Keep hybrid approach for now?** (Best of both worlds)

Let me know which direction you'd prefer!
