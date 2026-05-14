-- Complete database initialization for Supremacy Game
-- Run with: mysql supremacy_game < run_init.sql

-- =============================================
-- 1. ASSETS CATALOG (ships, infrastructure)
-- =============================================
INSERT IGNORE INTO assets_catalog (name, category, base_cost, is_unique, image_url) VALUES
('FarmingShip', 'Ship', 5000, FALSE, 'farmingship.png'),
('CargoShip', 'Ship', 8500, FALSE, 'deep_space_cargo_ship.png'),
('MineralShip', 'Ship', 12000, FALSE, 'mineralship.png'),
('BattleCruiser', 'Ship', 45000, TRUE, 'battle_cruiser.png'),
('EnergySatellite', 'Infrastructure', 25000, FALSE, 'energy_satellite.png'),
('Terraformer', 'Infrastructure', 180000, TRUE, 'terraformer.png');

-- =============================================
-- 3. EQUIPMENT CATALOG (armor, weapons)
-- =============================================
INSERT IGNORE INTO equipment_catalog (name, category, base_cost, strength_value, image_url) VALUES
('Light Armor', 'Armor', 100, 3, 'lightarmour.png'),
('Medium Armor', 'Armor', 250, 6, 'mediumarmour.png'),
('SmallCannon', 'Weapon', 300, 8, 'canon.png'),
('Pistol', 'Weapon', 450, 1, 'pistol.png'),
('Heavy Armor', 'Armor', 500, 10, 'heavyarmour.png'),
('Heavy Cannon', 'Weapon', 600, 12, 'heavycannon.png'),
('Plasteel Armor', 'Armor', 800, 15, 'plasteelarmor.png'),
('Rifle', 'Weapon', 800, 3, 'rifle.png');

-- =============================================
-- 4. SYSTEMS (galaxy regions)
-- =============================================
INSERT IGNORE INTO systems (name, difficulty_level) VALUES
('System 1', 1),
('System 2', 2);

-- =============================================
-- 5. USERS (players)
-- =============================================
INSERT IGNORE INTO users (username, credits) VALUES ('Player', 5000);

-- =============================================
-- 6. PLANETS (System 1 - 8 planets)
-- =============================================
INSERT INTO planets (system_id, name, owner_user_id) VALUES
(1, 'System 1-Alpha', 1),   -- Owned by Player
(1, 'System 1-Beta', NULL),    -- Neutral
(1, 'System 1-Gamma', NULL),   -- Neutral
(1, 'System 1-Delta', NULL),   -- Neutral
(1, 'System 1-Epsilon', NULL), -- Neutral
(1, 'System 1-Zeta', NULL),    -- Neutral
(1, 'System 1-Eta', NULL),     -- Neutral
(1, 'System 1-Theta', NULL);   -- Neutral

-- =============================================
-- 7. PLANETARY STATS (System 1)
-- =============================================
INSERT INTO planetary_stats (planet_id, population, morale, tax_rate, food_level, mineral_level, energy_level, fuel_level) VALUES
(1, 100, 8, 0.05, 50, 30, 25, 10),  -- Planet Alpha has population and resources
(2, 0, 5, 0, 0, 0, 0, 0);             -- Other planets are uninhabited

-- =============================================
-- 8. COLONIES (System 1)
-- =============================================
INSERT INTO colonies (planet_id, farming_stations, mining_stations, solar_satellites) VALUES
(1, 1, 0, 0),   -- Alpha has basic farming
(2, 0, 0, 0);   -- Beta has nothing (uninhabited)

-- =============================================
-- 9. PLANETS (System 2 - 16 planets)
-- =============================================
INSERT INTO planets (system_id, name, owner_user_id) VALUES
(2, 'System 2-Alpha', 1),    -- Owned by Player
(2, 'System 2-Beta', NULL),   -- Neutral
(2, 'System 2-Gamma', NULL),  -- Neutral
(2, 'System 2-Delta', NULL),  -- Neutral
(2, 'System 2-Epsilon', NULL),-- Neutral
(2, 'System 2-Zeta', NULL),   -- Neutral
(2, 'System 2-Eta', NULL),    -- Neutral
(2, 'System 2-Theta', NULL),  -- Neutral
(2, 'System 2-Iota', NULL),   -- Neutral
(2, 'System 2-Kappa', NULL),  -- Neutral
(2, 'System 2-Lambda', NULL), -- Neutral
(2, 'System 2-Mu', NULL),     -- Neutral
(2, 'System 2-Nu', NULL),     -- Neutral
(2, 'System 2-Xi', NULL),     -- Neutral
(2, 'System 2-Omicron', NULL),-- Neutral
(2, 'System 2-Pi', NULL);     -- Neutral
