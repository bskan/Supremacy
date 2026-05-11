-- =============================================
-- Supremacy Game Schema (MariaDB/SQL)
-- Version 3.0 - Reflects detailed gameplay mechanics.
-- =============================================

-- 1. USERS: Stores player identification and main state metrics.
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    credits BIGINT DEFAULT 1000 -- Initial starting money
);

-- 2. SYSTEMS: Defines the galaxy regions.
CREATE TABLE systems (
    system_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    difficulty_level TINYINT NOT NULL -- 1 to 4
);

-- 3. PLANETS: Details of every world in the system.
CREATE TABLE planets (
    planet_id INT PRIMARY KEY AUTO_INCREMENT,
    system_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    owner_user_id INT NULL, -- NULL for neutral/unclaimed planets
    FOREIGN KEY (system_id) REFERENCES systems(system_id),
    FOREIGN KEY (owner_user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- 4. PLANETARY_STATS: Tracks key metrics for a planet.
CREATE TABLE planetary_stats (
    planet_id INT PRIMARY KEY,
    population BIGINT DEFAULT 100,
    morale TINYINT DEFAULT 5 -- Scale of 1-10
        FOREIGN KEY (planet_id) REFERENCES planets(planet_id),
    tax_rate DECIMAL(4, 2) DEFAULT 0.05, -- Percentage tax rate
    food_level BIGINT DEFAULT 0,
    mineral_level BIGINT DEFAULT 0,
    energy_level BIGINT DEFAULT 0,
    fuel_level BIGINT DEFAULT 0,
    -- Constraints to ensure one stats record per planet
    UNIQUE KEY (planet_id)
);

-- 5. COLONIES: Tracks established infrastructure on a planet.
CREATE TABLE colonies (
    colony_id INT PRIMARY KEY AUTO_INCREMENT,
    planet_id INT NOT NULL UNIQUE, -- One colony entry per planet
    farming_stations INT DEFAULT 1,
    mining_stations INT DEFAULT 0,
    solar_satellites INT DEFAULT 0,
    FOREIGN KEY (planet_id) REFERENCES planets(planet_id) ON DELETE CASCADE
);

-- 6. SHIPS: Tracks all movable assets.
CREATE TABLE ships (
    ship_id INT PRIMARY KEY AUTO_INCREMENT,
    owner_user_id INT NOT NULL,
    planet_id INT NOT NULL,
    docking_bay_slot TINYINT CHECK (docking_bay_slot BETWEEN 1 AND 3), -- 1, 2, or 3
    ship_type ENUM('BattleCruiser', 'CargoShip', 'FarmingShip', 'MineralShip') NOT NULL,
    heading TINYINT DEFAULT 0, -- Direction/Heading
    FOREIGN KEY (owner_user_id) REFERENCES users(user_id),
    FOREIGN KEY (planet_id) REFERENCES planets(planet_id)
);

-- Junction table for detailed cargo manifest per ship.
CREATE TABLE ship_cargo (
    ship_id INT,
    resource_type ENUM('Food', 'Energy', 'Mineral', 'Fuel') NOT NULL,
    quantity BIGINT DEFAULT 0,
    PRIMARY KEY (ship_id, resource_type),
    FOREIGN KEY (ship_id) REFERENCES ships(ship_id) ON DELETE CASCADE
);

-- 7. MILITARY_PLATOON: Details of military readiness on a planet.
-- 8. ASSETS CATALOG: Lookup for all purchasable equipment and ships.
CREATE TABLE assets_catalog (
    asset_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    category ENUM('Ship', 'Infrastructure', 'Military') NOT NULL,
    base_cost BIGINT NOT NULL, -- Cost in credits
    is_unique BOOLEAN DEFAULT FALSE -- True for one-time purchases like Terraformer
);

-- 9. SHIP TYPES: Specific catalog for ships (could also live in assets_catalog)
CREATE TABLE ship_types (
    ship_type_name ENUM('BattleCruiser', 'CargoShip', 'FarmingShip', 'MineralShip') PRIMARY KEY,
    base_purchase_cost BIGINT NOT NULL
);

-- 10. EQUIPMENT CATALOG: Defines purchasable military gear and training costs.
CREATE TABLE equipment_catalog (
    equipment_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    category ENUM('Armor', 'Weapon') NOT NULL,
    base_cost BIGINT NOT NULL,
    strength_value INT NOT NULL -- Base strength contribution (e.g., +5 armor)
);

-- Linking tables for better data integrity and flexibility:
-- For example, ships can be linked to asset catalog items if needed in the future.
-- We will rely on `assets_catalog` for general costs.
