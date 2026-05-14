-- Complete database initialization for Supremacy Game
-- DROPS AND RECREATES the entire database for a clean slate

-- =============================================
-- 1. DROP EXISTING DATABASE (clean slate)
-- =============================================
DROP DATABASE IF EXISTS supremacy_game;
CREATE DATABASE supremacy_game CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE supremacy_game;

-- =============================================
-- 2. CREATE USERS (players)
-- =============================================
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    credits BIGINT DEFAULT 0
);

INSERT INTO users (username, credits) VALUES ('Player', 5000);

-- =============================================
-- 3. CREATE SYSTEMS (galaxy regions)
-- =============================================
CREATE TABLE systems (
    system_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    difficulty_level TINYINT NOT NULL DEFAULT 1
);

INSERT INTO systems (name, difficulty_level) VALUES
('System 1', 1),
('System 2', 2);

-- =============================================
-- 4. CREATE PLANETS (all worlds in systems)
-- =============================================
CREATE TABLE planets (
    planet_id INT PRIMARY KEY AUTO_INCREMENT,
    system_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    owner_user_id INT DEFAULT NULL,
    CONSTRAINT fk_planets_system FOREIGN KEY (system_id) REFERENCES systems(system_id),
    CONSTRAINT fk_planets_owner FOREIGN KEY (owner_user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

INSERT INTO planets (system_id, name, owner_user_id) VALUES
(1, 'System 1-Alpha', 1),   -- Owned by Player
(1, 'System 1-Beta', NULL),    -- Neutral
(1, 'System 1-Gamma', NULL),   -- Neutral
(1, 'System 1-Delta', NULL),   -- Neutral
(1, 'System 1-Epsilon', NULL), -- Neutral
(1, 'System 1-Zeta', NULL),    -- Neutral
(1, 'System 1-Eta', NULL),     -- Neutral
(1, 'System 1-Theta', NULL);   -- Neutral

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

-- =============================================
-- 5. CREATE PLANETARY_STATS (planet metrics)
-- =============================================
CREATE TABLE planetary_stats (
    planet_id INT PRIMARY KEY,
    population SMALLINT DEFAULT 0,
    morale TINYINT DEFAULT 5,
    tax_rate DECIMAL(4,2) DEFAULT 0.0,
    food_level SMALLINT DEFAULT 0,
    mineral_level SMALLINT DEFAULT 0,
    energy_level SMALLINT DEFAULT 0,
    fuel_level SMALLINT DEFAULT 0
);

INSERT INTO planetary_stats (planet_id, population, morale, tax_rate, food_level, mineral_level, energy_level, fuel_level) VALUES
(1, 100, 8, 0.05, 50, 30, 25, 10),  -- Planet Alpha has population and resources
(2, 0, 5, 0, 0, 0, 0, 0);             -- Other planets are uninhabited

-- =============================================
-- 6. CREATE COLONIES (infrastructure on planets)
-- =============================================
CREATE TABLE colonies (
    planet_id INT PRIMARY KEY,
    farming_stations TINYINT DEFAULT 0,
    mining_stations TINYINT DEFAULT 0,
    solar_satellites TINYINT DEFAULT 0
);

INSERT INTO colonies (planet_id, farming_stations, mining_stations, solar_satellites) VALUES
(1, 1, 0, 0),   -- Alpha has basic farming
(2, 0, 0, 0);   -- Beta has nothing (uninhabited)

-- =============================================
-- 7. CREATE ASSETS CATALOG (ships, infrastructure)
-- =============================================
CREATE TABLE assets_catalog (
    asset_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    category ENUM('Ship', 'Infrastructure') NOT NULL,
    base_cost BIGINT NOT NULL,
    is_unique BOOLEAN DEFAULT FALSE,
    image_url VARCHAR(255) NOT NULL
);

-- Clean catalog with 6 items (4 ships + 2 infrastructure), all images match actual files
INSERT INTO assets_catalog (name, category, base_cost, is_unique, image_url) VALUES
('FarmingShip', 'Ship', 5000, FALSE, 'farmingship.png'),
('CargoShip', 'Ship', 8500, FALSE, 'deep_space_cargo_ship.png'),
('MineralShip', 'Ship', 12000, FALSE, 'mineralship.png'),
('BattleCruiser', 'Ship', 45000, TRUE, 'battle_cruiser.png'),
('EnergySatellite', 'Infrastructure', 25000, FALSE, 'energy_satellite.png'),
('Terraformer', 'Infrastructure', 180000, TRUE, 'terraformer.png');

-- =============================================
-- 8. CREATE SHIP_TYPES (specific ship catalog with costs)
-- =============================================
CREATE TABLE ship_types (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ship_type_name VARCHAR(100) NOT NULL,
    base_purchase_cost INT NOT NULL
);

INSERT INTO ship_types (ship_type_name, base_purchase_cost) VALUES
('BattleCruiser', 500),
('CargoShip', 300),
('FarmingShip', 150),
('MineralShip', 180);

-- =============================================
-- 9. CREATE EQUIPMENT CATALOG (armor, weapons)
-- =============================================
CREATE TABLE equipment_catalog (
    equipment_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    category ENUM('Armor', 'Weapon') NOT NULL,
    base_cost BIGINT NOT NULL,
    strength_value INT NOT NULL,
    image_url VARCHAR(255) NOT NULL
);

INSERT INTO equipment_catalog (name, category, base_cost, strength_value, image_url) VALUES
('Light Armor', 'Armor', 100, 3, 'lightarmour.png'),
('Medium Armor', 'Armor', 250, 6, 'mediumarmour.png'),
('SmallCannon', 'Weapon', 300, 8, 'canon.png'),
('Pistol', 'Weapon', 450, 1, 'pistol.png'),
('Heavy Armor', 'Armor', 500, 10, 'heavyarmour.png'),
('Heavy Cannon', 'Weapon', 600, 12, 'heavycannon.png'),
('Plasteel Armor', 'Armor', 800, 15, 'plasteelarmor.png'),
('Rifle', 'Weapon', 800, 3, 'rifle.png');

-- =============================================
-- 10. CREATE SHIPS (movable fleet assets)
-- =============================================
CREATE TABLE ships (
    ship_id INT PRIMARY KEY AUTO_INCREMENT,
    owner_user_id INT NOT NULL,
    planet_id INT NOT NULL,
    docking_bay_slot TINYINT CHECK (docking_bay_slot BETWEEN 1 AND 3),
    ship_type ENUM('BattleCruiser', 'CargoShip', 'FarmingShip', 'MineralShip') NOT NULL,
    heading TINYINT DEFAULT 0,
    CONSTRAINT fk_ships_owner FOREIGN KEY (owner_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_ships_planet FOREIGN KEY (planet_id) REFERENCES planets(planet_id)
);

-- =============================================
-- 11. CREATE SHIP_CARGO (cargo manifest for ships)
-- =============================================
CREATE TABLE ship_cargo (
    ship_id INT NOT NULL,
    resource_type ENUM('Food', 'Energy', 'Mineral', 'Fuel') NOT NULL,
    quantity BIGINT DEFAULT 0,
    PRIMARY KEY (ship_id, resource_type),
    CONSTRAINT fk_shipc_ship FOREIGN KEY (ship_id) REFERENCES ships(ship_id) ON DELETE CASCADE
);

-- =============================================
-- 12. CREATE MILITARY_PLATOON (equipped military forces)
-- =============================================
CREATE TABLE military_platoon (
    platoon_id INT PRIMARY KEY AUTO_INCREMENT,
    planet_id INT NOT NULL,
    unit_type ENUM('Infantry', 'Vehicle', 'Air') DEFAULT 'Infantry',
    count TINYINT DEFAULT 100,
    CONSTRAINT fk_mil_planet FOREIGN KEY (planet_id) REFERENCES planets(planet_id) ON DELETE CASCADE
);

-- =============================================
-- VERIFICATION SUMMARY
-- =============================================
SELECT 'users' as tbl, COUNT(*) as count FROM supremacy_game.users
UNION ALL SELECT 'systems', COUNT(*) FROM supremacy_game.systems
UNION ALL SELECT 'planets', COUNT(*) FROM supremacy_game.planets
UNION ALL SELECT 'assets_catalog', COUNT(*) FROM supremacy_game.assets_catalog;
