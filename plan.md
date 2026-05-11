# Supremacy Remake Implementation Plan (Python/MariaDB) - V3.0 (Final Draft)
## Context & Goal
The objective is a full-stack remake of *Supremacy*, using Python for logic and MariaDB for persistence, modeling the complex mechanics described across all gameplay screens. The core principle remains: **SQL manages state; Python handles transactions and business logic.**

**Core Technologies:**
*   **Language:** Python 3+
*   **Database:** MariaDB (MariaDB functions will be used where stored procedures are beneficial).
*   **Architecture Goal:** Decouple the Game Engine (Simulation Logic) from the Presentation Layer (CLI/Web UI). The game operates on a **turn-based, time-advancing model**.

## Phase 1: Data Model & Schema Design (SQL Focus) - Finalized Structure
The schema must be highly accurate to support all mechanics.

**Key Tables:**

1.  **`users`**: Player identification and main state metrics.
    *   `user_id` (PK), `username`, `credits`.
2.  **`systems`**: Galaxy regions.
    *   `system_id` (PK), `name`, `difficulty_level`.
3.  **`planets`**: Details of every world in the system.
    *   `planet_id` (PK), `system_id` (FK), `name`, `owner_user_id` (FK to `users`). *Removed 'is\_starbase' boolean, ownership is determined by `owner_user_id`.*
4.  **`planetary_stats`**: Tracks key metrics for a planet.
    *   `planet_id` (PK, FK)
    *   `population`, `morale`, `tax_rate`.
    *   `food_level`, `mineral_level`, `energy_level`, `fuel_level`: Current reserves in tonnes.
5.  **`colonies`**: Tracks established infrastructure on a planet.
    *   `colony_id` (PK), `planet_id` (FK)
    *   `farming_stations`, `mining_stations`, `solar_satellites`: Counts of installed infrastructure.
6.  **`ships`**: Tracks all movable assets.
    *   `ship_id` (PK), `owner_user_id`, `planet_id`, `docking_bay_slot` (1-3).
    *   `ship_type`: Enum (BattleCruiser, CargoShip, FarmingShip, MineralShip).
    *   `cargo_manifest`: JSON/table tracking resource/crew load.
7.  **`military_platoon`**: Details of military readiness on a planet.
    *   `platoon_id` (PK), `planet_id` (FK)
    *   `troops_available`, `equipment_strength`, `weapon_strength`.

## Phase 2: Core Simulation Logic (Python Engine Focus) - Finalized Mechanics
The simulation runs as a continuous, turn-based loop (`run_turn(user_id)`).

**Simulation Flow:**
1.  **Resource Update & Survival Check:** Calculates net resource change based on infrastructure and population needs. Low resources severely degrade morale/tax rate.
2.  **Economic Cycle (Taxation & Growth):** Taxes are calculated, updating credits. Population growth is highly dependent on sustained resource surplus.
3.  **AI Opponent (`ai_opponent_turn()`):** A dedicated, complex function that simulates the enemy. It acts autonomously to:
    *   Self-resource and terraform available planets it controls.
    *   Build infrastructure and military assets strategically.
    *   Analyze player weakness and attempt takeovers (attacking uncolonized/weak planets).
4.  **Movement & Combat:** Handles all movements. **CRITICAL FIX:** Troop movement must *only* occur via Battle Cruisers. Cargo Ships are for raw materials only. Combat resolution uses `military_platoon` strength metrics.

## Phase 3: CLI Frontend Design (Python Scripting) - Screen Mirroring
The CLI will guide the user through the 8 game screens, providing a test harness for the core logic. The state must be saved/loaded via the database transactionally on every screen change.

**Screen Focus:**
*   **Home Screen (Initial):** Planet selection and basic status view.
*   **Screen 2 (Purchase Assets):** Buy ships (`assets_catalog`), infrastructure, and handle unique purchases like the one-time Terraformer usage.
*   **Screen 3 (Planet Details):** Read all stats (population, morale, resources).
*   **Screen 4 (Military Platoon):** Manage troop training and equipment purchasing.
*   **Screen 5 & 6 (Cargo & Assignment):** Load/unload cargo onto ships; assign farming/mining workers to surface infrastructure.
*   **Screen 7 (Battle Screen):** Visualize and input battle aggression values, triggering combat resolution when necessary.

## Phase 4: Web UI Backend API Design (Python/FastAPI) - Transactional Endpoints
The backend must expose robust REST endpoints that treat every action as a database transaction to prevent race conditions and data corruption. All actions are routed to the central `process_turn` or specific screen handlers.

**Critical Point:** The entire simulation loop (`run_turn`) must be exposed as an API endpoint, ensuring AI activity and player turns are atomic units of work for the web application.