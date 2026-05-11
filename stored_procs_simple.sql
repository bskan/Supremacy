-- Simple stored procedure for batch turn processing - MariaDB compatible

DELIMITER //

DROP PROCEDURE IF EXISTS process_player_turns_batch//

CREATE PROCEDURE process_player_turns_batch(IN p_user_id INT)
BEGIN
    -- Process turn for all player planets in a single UPDATE statement
    -- Calculates and applies food, energy, fuel, and population changes

    UPDATE planetary_stats ps
    JOIN planets p ON ps.planet_id = p.planet_id
    LEFT JOIN colonies c ON p.planet_id = c.planet_id
    SET
        -- Food: production from farms minus population consumption
        food_level = FLOOR(ps.food_level + 15 * COALESCE(c.farming_stations, 0) - ps.population * 0.5),
        -- Energy: solar satellites output minus machinery consumption
        energy_level = FLOOR(ps.energy_level + 12 * COALESCE(c.solar_satellites, 0) - ps.population * 0.3),
        -- Fuel: from mineral byproducts
        fuel_level = FLOOR(ps.fuel_level + 8 * COALESCE(c.mining_stations, 0)),

        -- Population: growth based on morale when food adequate (>= -20), starvation decline otherwise
        population = CASE
            WHEN ps.food_level >= -20 THEN
                GREATEST(0, ps.population + ROUND(ps.population * (COALESCE(ps.morale, 5) / 10.0) * 0.005, 0))
            ELSE
                GREATEST(0, ps.population - ROUND(ps.population * ABS(ps.food_level) / 25.0, 0))
            END
    WHERE p.owner_user_id = p_user_id;

END//

DELIMITER ;
