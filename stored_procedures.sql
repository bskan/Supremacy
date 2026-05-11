-- =============================================
-- Supremacy Game - MySQL Stored Procedures
-- Migrate Python simulation logic to MySQL for batch processing
-- =============================================

-- Drop existing procedures if they exist (for clean migration)
DROP PROCEDURE IF EXISTS process_all_player_turns;
DROP PROCEDURE IF EXISTS simulate_single_planet_turn;
DROP FUNCTION IF EXISTS calculate_resource_flow;

-- =====================================================
-- PROCEDURE 1: Simulate Single Planet Turn (Detailed)
-- =====================================================
DELIMITER //

CREATE PROCEDURE simulate_single_planet_turn(
    IN p_planet_id INT,
    OUT p_population_delta BIGINT,
    OUT p_food_change BIGINT,
    OUT p_energy_change BIGINT,
    OUT p_fuel_change BIGINT
)
BEGIN
    DECLARE v_population BIGINT;
    DECLARE v_morale TINYINT;
    DECLARE v_food_level BIGINT;
    DECLARE v_mineral_level BIGINT;
    DECLARE v_farming_stations INT;
    DECLARE v_mining_stations INT;
    DECLARE v_solar_satellites INT;
    DECLARE v_ship_count INT;
    DECLARE v_total_weapons INT DEFAULT 0;

    DECLARE v_food_produced DECIMAL(10,2);
    DECLARE v_food_consumed DECIMAL(10,2);
    DECLARE v_energy_produced DECIMAL(10,2);
    DECLARE v_energy_consumed DECIMAL(10,2);
    DECLARE v_fuel_from_minerals DECIMAL(10,2);
    DECLARE v_fuel_from_food DECIMAL(10,2);
    DECLARE v_total_fuel_produced DECIMAL(10,2);

    -- Step 1: Get planet state
    SELECT ps.population, ps.morale, c.farming_stations, c.mining_stations,
           c.solar_satellites, SUM(s.ship_count)
    INTO v_population, v_morale, v_farming_stations, v_mining_stations,
         v_solar_satellites, v_ship_count
    FROM planets p
    JOIN colonies c ON p.planet_id = c.planet_id
    LEFT JOIN (
        SELECT planet_id, COUNT(*) as ship_count
        FROM ships WHERE owner_user_id IN (
            SELECT user_id FROM users WHERE username = 'Player'
        )
        GROUP BY planet_id
    ) s ON p.planet_id = s.planet_id
    JOIN planetary_stats ps ON p.planet_id = ps.planet_id
    WHERE p.planet_id = p_planet_id;

    -- Set defaults if subquery returned NULL
    SET v_ship_count = IFNULL(v_ship_count, 0);

    -- Step 2: Calculate production
    SET v_food_produced = v_farming_stations * 15.0;
    SET v_mineral_production = v_mining_stations * 8.0;
    SET v_energy_produced = v_solar_satellites * 12.0;

    -- Step 3: Calculate fuel (byproducts)
    SET v_fuel_from_minerals = v_mineral_production * 0.5;
    SET v_fuel_from_food = v_food_produced * 0.2;
    SET v_total_fuel_produced = v_fuel_from_minerals + v_fuel_from_food;

    -- Step 4: Calculate consumption
    SET v_food_consumed = v_population * 0.5;
    SET v_energy_consumed = v_population * 0.3 + (v_ship_count * 2.0);
    SET v_mineral_consumed = v_ship_count * 1.0;
    SET v_fuel_consumed = v_ship_count * 0.8;

    -- Step 5: Calculate net resource changes
    SET p_food_change = ROUND(v_food_produced - v_food_consumed, 0);
    SET p_energy_change = ROUND(v_energy_produced - v_energy_consumed, 0);
    SET p_fuel_change = ROUND(v_total_fuel_produced - v_fuel_consumed, 0);

    -- Step 6: Calculate population change
    -- Growth: pop * (morale / 10) * 0.5% when food adequate
    SET v_population_growth_rate = (v_morale / 10.0) * 0.005;
    SET v_natural_population_increase = v_population * v_population_growth_rate;

    -- Decline from starvation if food deficit < -20
    IF p_food_change < -20 THEN
        SET v_starvation_factor = ABS(p_food_change) / 25.0;
        SET v_population_decrease_from_starvation = ROUND(v_population * v_starvation_factor, 0);
    ELSE
        SET v_population_decrease_from_starvation = 0;
    END IF;

    SET p_population_delta = v_natural_population_increase - v_population_decrease_from_starvation;
END //

DELIMITER ;

-- =====================================================
-- PROCEDURE 2: Process All Player Planets (Batch Mode)
-- Single UPDATE for all planets owned by a player
-- =====================================================
DROP PROCEDURE IF EXISTS process_all_player_turns;

CREATE PROCEDURE process_all_player_turns(
    IN p_user_id INT
)
BEGIN
    -- Simulate production and consumption across all player planets
    -- Returns: planet_id, pop_delta, food_change, energy_change, fuel_change

    SELECT
        p.planet_id,
        (ps.population +
            CASE
                -- Population growth based on morale (when food adequate)
                WHEN pr.food_net >= 0 THEN
                    ROUND(ps.population * (pr.morale / 10.0) * 0.005, 0)
                -- Starvation decline when food runs low
                ELSE FLOOR(ps.population * (ABS(pr.food_net) / 25.0))
            END
        ) as new_population,
        ROUND(pr.food_net, 0) as food_change,
        ROUND(pr.energy_net, 0) as energy_change,
        ROUND(pr.fuel_net, 0) as fuel_change
    FROM planets p
    JOIN colonies c ON p.planet_id = c.planet_id
    LEFT JOIN (
        SELECT planet_id, COUNT(*) as ship_count
        FROM ships
        WHERE owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
        GROUP BY planet_id
    ) s ON p.planet_id = s.planet_id
    JOIN planetary_stats ps ON p.planet_id = ps.planet_id
    CROSS JOIN (
        SELECT SUM(c2.farming_stations * 15.0) as food_produced,
               SUM(c2.mining_stations * 8.0) as minerals_produced,
               SUM(c2.solar_satellites * 12.0) as energy_produced
        FROM colonies c2
        JOIN planets p2 ON c2.planet_id = p2.planet_id
        WHERE p2.owner_user_id = p_user_id
    ) prod ON 1=1
    WHERE p.owner_user_id = p_user_id

    -- Calculate derived values in subquery for readability
    AS pr (
        food_produced,
        minerals_produced,
        energy_produced,
        ship_count
    );

    -- Now perform the actual batch update with inline calculations
    UPDATE planetary_stats ps
    JOIN planets p ON ps.planet_id = p.planet_id
    LEFT JOIN colonies c ON ps.planet_id = c.planet_id
    LEFT JOIN (
        SELECT planet_id, COUNT(*) as ship_count
        FROM ships
        WHERE owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
        GROUP BY planet_id
    ) s ON p.planet_id = s.planet_id
    WHERE p.owner_user_id = p_user_id

    SET
    -- Food: production minus consumption, floored to integer
        food_level = LFSOR(ps.food_level + c.farming_stations * 15.0 - ps.population * 0.5),

    -- Energy: solar satellites minus population machinery cost and ship operations
        energy_level = FLOOR(
            ps.energy_level +
            COALESCE(c.solar_satellites, 0) * 12.0 -
            ps.population * 0.3 -
            COALESCE(s.ship_count, 0) * 2.0
        ),

    -- Fuel: byproducts from production minus ship maintenance
        fuel_level = FLOOR(
            ps.fuel_level +
            (COALESCE(c.mining_stations, 0) * 8.0 * 0.5) +      -- mineral fuel
            (COALESCE(c.farming_stations, 1) * 15.0 * 0.2) +   -- food fuel byproduct
            - COALESCE(s.ship_count, 0) * 0.8                   -- ship maintenance
        ),

    -- Population: growth or starvation (with max 0 constraint)
        population = CASE
            WHEN ps.food_level >= 0 THEN
                MAX(0, ps.population + ROUND(ps.population * (COALESCE(ps.morale, 5) / 10.0) * 0.005, 0))
            ELSE
                MAX(0, ps.population - FLOOR(ps.population * ABS(ps.food_level) / 25.0))
            END;

    -- Reset food level to 0 if depleted (prevents starvation spiral)
    WHERE ps.food_level < 0 AND (ps.food_level + c.farming_stations * 15.0 - ps.population * 0.5) < 0;

END //

DELIMITER ;

-- =====================================================
-- VIEWS for Quick Analytics (Optional)
-- =====================================================

-- Create view showing resource status of all planets
DROP VIEW IF EXISTS v_planet_resource_status;
CREATE VIEW v_planet_resource_status AS
SELECT
    p.planet_id,
    p.name,
    ps.population,
    ps.morale,
    CASE WHEN ps.food_level < 0 THEN 'CRITICAL'
         WHEN ps.food_level < 20 THEN 'LOW'
         ELSE 'ADEQUATE' END as food_status,
    c.farming_stations,
    c.mining_stations,
    c.solar_satellites,
    SUM(s.ship_count) as ship_count
FROM planets p
JOIN planetary_stats ps ON p.planet_id = ps.planet_id
JOIN colonies c ON p.planet_id = c.planet_id
LEFT JOIN ships s ON p.planet_id = s.planet_id AND s.owner_user_id IS NOT NULL
GROUP BY p.planet_id, p.name, ps.population, ps.morale, ps.food_level, ps.energy_level,
         ps.fuel_level, ps.tax_rate, c.farming_stations, c.mining_stations, c.solar_satellites;

-- =====================================================
-- TRIGGERS for Data Integrity (Optional)
-- =====================================================

-- Trigger to ensure food_level doesn't go below -100 (prevents spiral of death)
DROP TRIGGER IF EXISTS before_planet_stats_update;
CREATE TRIGGER before_planet_stats_update
BEFORE UPDATE ON planetary_stats
FOR EACH ROW
BEGIN
    -- Prevent catastrophic resource collapse
    IF NEW.food_level < -100 THEN
        SET NEW.food_level = -100;
    END IF;

    IF NEW.energy_level < -100 THEN
        SET NEW.energy_level = -100;
    END IF;

    IF NEW.fuel_level < 0 THEN
        SET NEW.fuel_level = 0;
    END IF;
END;
