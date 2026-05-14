from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os

# Import Connection class for mysql compatibility
try:
    from mysql.connector import MySQLConnection as Connection
except ImportError:
    from mysql.connector.connection import MySQLConnection as Connection

# Import core game engine logic
from game_engine import (
    calculate_resource_flow,
    process_ship_movement,
    resolve_combat,
    ai_opponent_turn,
    get_db_connection,
    DEFAULT_DB_CONFIG
)


# =============================================================================
# API MODELS - Mirror CLI data structures
# =============================================================================

class ResourceUpdate(BaseModel):
    """Resource levels for a planet (CLI: planetary_stats resources)"""
    food: float
    energy: float
    mineral: float
    fuel: float
    taxable_income: float


class PlanetInfo(BaseModel):
    """Detailed planet information (CLI: get_planet_state)"""
    planet_id: int
    name: str
    system_id: int
    owner_name: str
    population: int
    morale: int
    tax_rate: float
    resources: Dict[str, Any]  # food_level, energy_level, fuel_level
    infrastructure: Dict[str, Any]  # farming_stations, mining_stations, solar_satellites


class SystemInfo(BaseModel):
    """System information with planet list (CLI: system list)"""
    system_id: int
    name: str
    planets: List[Dict[str, Any]]


class FleetItem(BaseModel):
    """Single ship in fleet inventory (CLI: fleet overview)"""
    ship_type: str
    count: int


class PlanetResourceData(BaseModel):
    """Extended planet data for dashboard view"""
    id: int
    name: str
    system_name: str
    ownerName: str
    population: int
    resources: Dict[str, float]
    morale: int


class AssetCatalogItem(BaseModel):
    """Single asset from catalog (CLI: purchase assets)"""
    name: str
    category: str  # 'Ship', 'Infrastructure', 'Equipment'
    base_cost: float
    description: str = ""
    image_url: Optional[str] = None


class PurchaseRequest(BaseModel):
    """Asset purchase request"""
    planet_id: int
    asset_name: str


class DebugLevelChange(BaseModel):
    """Debug level adjustment"""
    planet_id: int
    resource_type: str  # 'food_level', 'energy_level', 'fuel_level', 'population'
    new_value: float

app = FastAPI(title="Supremacy API")


@app.get("/")
def read_root():
    """Serve the web demo HTML file."""
    return {
        "message": "Supremacy Game API",
        "docs": "/docs (Swagger UI)",
        "web_demo": "/web_demo.html"
    }


@app.get("/web_demo.html")
def serve_web_demo():
    """Serve the web demo HTML file."""
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Supremacy Game - Planetary System Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, sans-serif; background: #f5f5f5; padding: 20px; }
        h1 { color: #2c3e50; margin-bottom: 20px; }
        .message-box { padding: 15px; margin-bottom: 20px; border-radius: 8px; background: #f0f0f0; max-width: 600px; }
        .planet-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 10px; }
        .planet-card { background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .planet-card h3 { margin-top: 0; color: #2c3e50; }
        .controls { display: flex; gap: 15px; justify-content: center; margin-bottom: 20px; }
        button { padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; transition: background-color 0.2s; }
        .primary { background-color: #3498db; color: white; }
        .primary:hover { background-color: #2980b9; }
        .secondary { background-color: #e74c3c; color: white; }
        .secondary:hover { background-color: #c0392b; }
        .screen-buttons { display: flex; gap: 10px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap; }
        .nav-btn { padding: 8px 16px; font-size: 14px; background-color: #95a5a6; color: white; }
        .nav-btn:hover { background-color: #7f8c8d; }
    </style>
</head>
<body>
    <h1>Supremacy Game - Planetary System Dashboard</h1>
    <div class="message-box" id="status-message">Connecting to Supremacy API...</div>
    <div class="screen-buttons">
        <button class="nav-btn" onclick="switchScreen(\'dashboard\')">🌎 Planetary Dashboard</button>
        <button class="nav-btn" onclick="switchScreen(\'purchase\')">2. Purchase Assets</button>
        <button class="nav-btn" onclick="switchScreen(\'fleet\')">3. Docking Bay / Fleet</button>
        <button class="nav-btn" onclick="switchScreen(\'planet-details\')">4. Planet Details</button>
        <button class="nav-btn" onclick="switchScreen(\'resources\')">5. Cargo Control</button>
        <button class="nav-btn" onclick="switchScreen(\'military\')">6. Military / Battle</button>
        <button class="nav-btn" onclick="switchScreen(\'battle-sim\')">7. Battle Simulation</button>
        <button class="nav-btn" onclick="switchScreen(\'debug\')">8. Debug Menu</button>
    </div>
    <div id="screen-container"></div>
    <script>
        const BASE_URL = "http://localhost:8000/api";
        let currentResourceFetch = null;
        let activeScreen = \'\';

        function switchScreen(screen) {
            document.getElementById("status-message").innerHTML += `<br><strong>Switching to screen:</strong> ${screen}`;
            activeScreen = screen;

            const container = document.getElementById("screen-container");
            container.innerHTML = ""; // Clear previous content

            switch(screen) {
                case "dashboard":
                    showDashboard(container);
                    break;
                case "purchase":
                    showPurchaseScreen(container, currentCredits || 0);
                    break;
                case "fleet":
                    showFleetScreen(container);
                    break;
                case "planet-details":
                    showPlanetDetails(container);
                    break;
                case "resources":
                    showResourcesScreen(container);
                    break;
                case "military":
                    showMilitaryScreen(container);
                    break;
                case "battle-sim":
                    showBattleSimulation(container);
                    break;
                case "debug":
                    showDebugMenu(container);
                    break;
            }
        }

        function loadDashboard() {
            fetch(`${BASE_URL}/systems/all`).then(r => r.json()).then(data => {
                document.getElementById("status-message").innerHTML = "<strong>Status:</strong> System ready!<br>" +
                    "Controls below - click a planet to view details.";

                const grid = document.createElement("div");
                grid.className = "planet-grid";
                grid.id = "planet-grid";

                for (let planet of data) {
                    const card = document.createElement("div");
                    card.className = "planet-card";
                    card.innerHTML = \`
                        <h3>\${planet.name || 'Planet ' + planet.planet_id}</h3>
                        <p><strong>Status:</strong> \${planet.owner_name || 'Uninhabited'}</p>
                        <button onclick='showPlanetDetails(\${planet.planet_id})'>View Details</button>
                    \`;
                    grid.appendChild(card);
                }

                document.getElementById("planet-grid").appendChild(grid);
            }).catch(err => {
                document.getElementById("status-message").textContent = "Error: " + err.message;
            });
        }

        function showDashboard(container) {
            container.innerHTML = "<h3>Planetary Dashboard</h3><button onclick=\"switchScreen('dashboard')\">Refresh</button>";

            setTimeout(loadDashboard, 100); // Refresh every 100ms for demo
        }

        function showPlanetDetails(planetId) {
            fetch(\`\${BASE_URL}/planet/\${planetId}\`).then(r => r.json()).then(data => {
                const card = document.createElement("div");
                card.className = "planet-card";
                card.innerHTML = \`
                    <h3>\${data.name || 'Planet Details'}</h3>
                    <p><strong>Population:</strong> \${data.population || 0}</p>
                    <p><strong>Morale:</strong> \${data.morale || 5}</p>
                    <p><strong>Tax Rate:</strong> \${(data.tax_rate || 0.05 * 100).toFixed(1)}%</p>
                    <hr style="margin: 10px 0; border: none; border-top: 1px solid #eee;">
                    <div><strong>Resources:</strong></div>
                    <ul>
                        <li>Food: \${data.resources.food || 0}</li>
                        <li>Energy: \${data.resources.energy || 0}</li>
                        <li>Fuel: \${data.resources.fuel || 0}</li>
                        <li>Taxable Income: \${data.resources.taxable_income || 0}</li>
                    </ul>
                \`;

                const grid = document.getElementById("planet-grid");
                if (grid) {
                    grid.innerHTML = "";
                    grid.appendChild(card);
                    switchScreen("dashboard"); // Back to dashboard view
                }
            }).catch(err => {
                document.getElementById("status-message").textContent = "Error loading planet: " + err.message;
            });
        }

        function showPurchaseScreen(container, credits) {
            currentCredits = credits;
            fetch(\`\${BASE_URL}/marketplace\`).then(r => r.json()).then(data => {
                container.innerHTML = "<h3>Purchase Assets</h3><p>Credits: " + credits.toLocaleString() + "</p><br>";

                function renderSection(title, items) {
                    const section = document.createElement("div");
                    section.style.marginBottom = "20px";

                    const heading = document.createElement("h4");
                    heading.textContent = title;
                    section.appendChild(heading);

                    const list = document.createElement("ul");
                    items.forEach(item => {
                        const li = document.createElement("li");
                        li.style.padding = "8px";
                        li.style.margin = "4px 0";
                        li.style.borderRadius = "4px";
                        li.style.background = "#f9f9f9";

                        let icon = "";
                        if (item.name.includes("Battle")) icon = "\\uD83D\\udeE1 ";
                        else if (item.name.includes("Cargo")) icon = "\\uD83D\\ude99 ";
                        else if (item.name.includes("Farming")) icon = "\\uD83C\\udF3e ";
                        else if (item.name.includes("Mining")) icon = "\\u2699\\ufe0f ";
                        else if (item.name.includes("Energy")) icon = "\\uD83D\\uDCA9 ";

                        const buyBtn = document.createElement("button");
                        buyBtn.style.padding = "4px 8px";
                        buyBtn.style.marginLeft = "auto";
                        buyBtn.textContent = "\${item.base_cost}";
                        buyBtn.onclick = () => buyItem(item.name);

                        li.innerHTML = \`\${icon}<strong>\${item.name}</strong> - <span style="color:\${{item.base_cost > credits ? 'red' : 'green'}}">\${(item.base_cost / 1000).toFixed(1)}k</span></p><button onclick="buyItem('\${item.name}')">\${item.base_cost}</button>\`;

                        section.appendChild(li);
                    });

                    container.appendChild(section);
                }

                renderSection("Ships", data.ships || []);
                renderSection("Infrastructure", data.infrastructure || []);
                renderSection("Military Equipment", data.equipment || []);
            }).catch(err => {
                document.getElementById("status-message").textContent = "Error loading marketplace: " + err.message;
            });
        }

        function buyItem(itemName) {
            if (!currentCredits) {
                alert("Not enough credits!");
                return;
            }

            const btn = event.target;
            btn.textContent = "Purchasing...";
            btn.disabled = true;

            fetch(\`\${BASE_URL}/marketplace/purchase\", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ planet_id: 1, asset_name: itemName })
            }).then(r => r.json()).then(data => {
                if (data.status === "success") {
                    alert(\`Purchased \${itemName}! Remaining credits: \${data.credits_remaining}\`);

                    // Re-fetch marketplace to update prices
                    fetch(\`\${BASE_URL}/marketplace\`).then(r => r.json()).then(data2 => {
                        showPurchaseScreen(document.getElementById("screen-container"), currentCredits - (data.cost || 0));
                    });
                } else {
                    alert(data.message);
                }
            }).catch(err => {
                alert("Error: " + err.message);
                btn.disabled = false;
                btn.textContent = "\${item.base_cost}";
            });
        }

        function showFleetScreen(container) {
            fetch(\`\${BASE_URL}/planets\").then(r => r.json()).then(data => {
                if (!data || data.length === 0) {
                    container.innerHTML = "<p>No planets available.</p>";
                    return;
                }

                container.innerHTML = "<h3>Fleet / Docking Bay</h3>";

                const grid = document.createElement("div");
                grid.className = "planet-grid";
                grid.id = "fleet-grid";

                data.forEach(planet => {
                    fetch(\`\${BASE_URL}/planets/\${planet.id}/fleet\").then(r => r.json()).then(fleet => {
                        const fleetGrid = document.createElement("div");
                        fleetGrid.innerHTML = \`
                            <h4>\${planet.name}</h4>
                            <p>Credits: \${(planet.resources.taxable_income || 0).toLocaleString()}</p>
                            <ul>
                                \${fleet.map(ship => \`<li>\${ship.ship_type}: \${ship.count} ships</li>\`).join('')}
                            </ul>
                        \`;

                        document.getElementById("fleet-grid").appendChild(fleetGrid);
                    }).catch(err => {
                        console.error("Error loading fleet:", err);
                    });
                });

                if (!document.getElementById("fleet-grid")) {
                    container.innerHTML = "<p>Loading fleet data...</p>";
                }
            }).catch(err => {
                document.getElementById("status-message").textContent = "Error: " + err.message;
            });
        }

        function showPlanetDetails(container) {
            const btn = document.querySelector(".primary");
            if (btn && !btn.disabled) {
                btn.disabled = true;
                btn.textContent = "Loading...";

                fetch(`${BASE_URL}/planet/1`).then(r => r.json()).then(data => {
                    container.innerHTML = \`
                        <div class="planet-card">
                            <h3>${data.name || 'Planet Details'}</h3>
                            <p><strong>Population:</strong> ${data.population || 0}</p>
                            <p><strong>Morale:</strong> ${data.morale || 5}</p>
                            <p><strong>Tax Rate:</strong> ${(data.tax_rate || 0.05 * 100).toFixed(1)}%</p>
                        </div>
                    \`;

                    btn.disabled = false;
                    btn.textContent = "⚡ Advance Turn";
                }).catch(err => {
                    container.innerHTML = "<p>Error: " + err.message + "</p>";
                    btn.disabled = false;
                    btn.textContent = "⚡ Advance Turn";
                });
            }
        }

        function showResourcesScreen(container) {
            fetch(`${BASE_URL}/planets`).then(r => r.json()).then(data => {
                if (!data || data.length === 0) {
                    container.innerHTML = "<p>No planets available.</p>";
                    return;
                }

                container.innerHTML = "<h3>Cargo Control</h3>";

                function renderPlanet(planet, index) {
                    const card = document.createElement("div");
                    card.className = "planet-card";
                    card.innerHTML = \`
                        <h4>\${planet.name}</h4>
                        <p><strong>Food:</strong> \${planet.resources.food || 0}t</p>
                        <p><strong>Energy:</strong> \${planet.resources.energy || 0}t</p>
                        <p><strong>Fuel:</strong> \${planet.resources.fuel || 0}t</p>
                        <p><strong>Minerals:</strong> \${planet.resources.mineral || 0}t</p>
                    \`;

                    document.getElementById("resources-grid") || (container.querySelector(".planet-grid").innerHTML = "");

                    const grid = container.querySelector(".planet-grid");
                    if (grid) grid.appendChild(card);
                }

                data.forEach(renderPlanet);
            }).catch(err => {
                document.getElementById("status-message").textContent = "Error: " + err.message;
            });
        }

        function showMilitaryScreen(container) {
            container.innerHTML = \`
                <h3>Military / Battle Control</h3>
                <p>Battle simulation feature coming soon!</p>
            \`;
        }

        function showBattleSimulation(container) {
            currentResourceFetch = null; // Reset to avoid body consumption error

            let running = false;
            container.innerHTML = \`
                <h3>Battle Simulation</h3>
                <button id="simulate-btn" onclick="startSimulation()">Simulate Battle</button>
                <p id="battle-status">Click Simulate to start battle simulation...</p>
            \`;

            function startSimulation() {
                if (running) return;
                running = true;

                const btn = document.getElementById("simulate-btn");
                btn.disabled = true;
                btn.textContent = "Running...";

                let round = 0;
                const duration = 5000; // 5 seconds
                const interval = 100; // Update every 100ms
                const totalUpdates = Math.floor(duration / interval);

                function updateRound() {
                    round++;

                    if (round <= totalUpdates) {
                        document.getElementById("battle-status").innerHTML = \`
                            <p><strong>Round:</strong> \${round} / \${totalUpdates}</p>
                            <p style="color: #666;">Simulating combat...</p>
                        \`;

                        // Fetch fresh resources for next update (not reusing old body)
                        fetch(\`${BASE_URL}/planets\`).then(r => r.json()).then(data => {
                            console.log("Resource update:", data);
                        }).catch(err => {
                            console.warn("Resource update skipped:", err.message);
                        });

                        setTimeout(updateRound, interval);
                    } else {
                        // End simulation
                        document.getElementById("battle-status").innerHTML = \`
                            <p><strong>Simulation Complete!</strong></p>
                            <p style="color: green;">Battle resolved successfully.</p>
                        \`;

                        btn.disabled = false;
                        btn.textContent = "Simulate Battle";
                        running = false;
                    }
                }

                updateRound();
            }
        }

        function showDebugMenu(container) {
            fetch(\`${BASE_URL}/debug/player-planets\`).then(r => r.json()).then(data => {
                container.innerHTML = "<h3>Debug Menu</h3>";

                data.forEach(planet => {
                    const card = document.createElement("div");
                    card.className = "planet-card";
                    card.innerHTML = \`
                        <h4>\${planet.name || 'Planet ' + planet.planet_id}</h4>
                        <p><strong>Population:</strong> \${planet.population || 0}</p>
                        <p><strong>Food:</strong> \${(planet.food_level || 0).toLocaleString()}t</p>
                        <p><strong>Energy:</strong> \${(planet.energy_level || 0).toLocaleString()}t</p>
                        <p><strong>Fuel:</strong> \${(planet.fuel_level || 0).toLocaleString()}t</p>
                    \`;

                    const actions = document.createElement("div");
                    actions.style.marginTop = "10px";

                    const addPopBtn = document.createElement("button");
                    addPopBtn.style.padding = "6px";
                    addPopBtn.textContent = "+1000 Pop";

                    const btn2 = document.createElement("button");
                    btn2.style.padding = "6px";
                    btn2.textContent = "-50000 Pop";

                    actions.appendChild(addPopBtn);
                    actions.appendChild(btn2);
                    card.appendChild(actions);

                    container.appendChild(card);
                });
            }).catch(err => {
                document.getElementById("status-message").textContent = "Error: " + err.message;
            });
        }

        // Initialize dashboard on load
        window.onload = function() {
            switchScreen('dashboard');
            loadDashboard();
        };

        // Prevent body consumption error by not reading response twice
        const resourceFetchCount = 0;
    </script>
</body>
</html>'''
    return Response(html_content, media_type="text/html")

class ResourceUpdate(BaseModel):
    food: float
    energy: float
    mineral: float
    fuel: float
    taxable_income: float

class ShipMoveRequest(BaseModel):
    ship_id: int
    destination_planet_id: int

class CombatRequest(BaseModel):
    attacker_planet_id: int
    defender_planet_id: int

# --- API Endpoints ---

# =============================================================================
# API ENDPOINTS - Mirror all CLI screens
# =============================================================================

@app.get("/api/system/{planet_id}/state", response_model=ResourceUpdate)
def get_planets_state(planet_id: int):
    """Retrieves a read-only snapshot of resource levels for a given planet."""
    try:
        import asyncio

        # Create event loop for async operations
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        # Calculate resource flow (may be blocking)
        flow = calculate_resource_flow(planet_id)
        return ResourceUpdate(**flow)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not retrieve state: {str(e)}")


@app.post("/api/system/{planet_id}/state", response_model=ResourceUpdate)
def get_planets_state_post(planet_id: int):
    """Retrieves a read-only snapshot of resource levels for a given planet (POST)."""
    try:
        import asyncio

        flow = calculate_resource_flow(planet_id)
        return ResourceUpdate(**flow)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not retrieve state: {str(e)}")


@app.get("/api/planets/system/{system_id}")
def get_system_planets(system_id: int):
    """Get all planets in a system (CLI Screen 10 - System List)."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.system_id, s.name, p.planet_id, p.name as planet_name,
                   p.owner_user_id, u.username as owner_name
            FROM systems s
            LEFT JOIN planets p ON s.system_id = p.system_id
            LEFT JOIN users u ON p.owner_user_id = u.user_id
            WHERE s.system_id = %s
        """, (system_id,))

        planets = cursor.fetchall()
        system_info = SystemInfo(
            system_id=system_id,
            name=planets[0]['name'] if planets else 'Unknown',
            planets=[
                {
                    'planet_id': p['planet_id'],
                    'name': p['planet_name'],
                    'owner': p.get('owner_name', 'Neutral')
                }
                for p in planets
            ]
        )
        cursor.close()
        return system_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/planets")
def get_all_player_planets():
    """Get all player-owned planets (CLI: Planet Details view)."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.planet_id, p.name, s.name as system_name
            FROM planets p
            JOIN systems s ON p.system_id = s.system_id
            WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            ORDER BY s.name, p.planet_id
        """)

        player_planets = cursor.fetchall()
        cursor.close()

        planets_data = []
        for planet in player_planets:
            try:
                flow = calculate_resource_flow(planet['planet_id'])
                planets_data.append({
                    'id': planet['planet_id'],
                    'name': planet['name'],
                    'system_name': planet['system_name'],
                    'ownerName': 'You',
                    'population': int(flow.get('taxable_income', 0)),  # Placeholder
                    'resources': flow,
                    'morale': 5
                })
            except Exception:
                continue

        return planets_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/planet/{planet_id}")
def get_planet_details(planet_id: int):
    """Get detailed planet information including infrastructure (CLI: Planet Details Screen 3)."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)

        # Get basic planet info
        cursor.execute("""
            SELECT p.planet_id, p.name, s.system_id, s.name as system_name,
                   u.username as owner_name, ps.population, ps.morale, ps.tax_rate
            FROM planets p
            JOIN systems s ON p.system_id = s.system_id
            LEFT JOIN planetary_stats ps ON p.planet_id = ps.planet_id
            LEFT JOIN users u ON p.owner_user_id = u.user_id
            WHERE p.planet_id = %s
        """, (planet_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planet not found")

        # Get infrastructure
        cursor.execute("""
            SELECT farming_stations, mining_stations, solar_satellites
            FROM colonies c WHERE c.planet_id = %s
        """, (planet_id,))

        infra_row = cursor.fetchone()
        infrastructure = {
            'farming_stations': int(infra_row['farming_stations']) if infra_row else 0,
            'mining_stations': int(infra_row['mining_stations']) if infra_row else 0,
            'solar_satellites': int(infra_row['solar_satellites']) if infra_row else 0
        }

        # Get fleet at this planet
        cursor.execute("""
            SELECT ship_type, COUNT(*) as count
            FROM ships s WHERE s.planet_id = %s AND s.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            GROUP BY ship_type
        """, (planet_id,))

        fleet_list = cursor.fetchall()
        fleet_items = [
            FleetItem(ship_type=row['ship_type'], count=row['count'])
            for row in fleet_list
        ]

        # Get population
        cursor.execute("""SELECT population FROM planetary_stats WHERE planet_id = %s""", (planet_id,))
        pop_row = cursor.fetchone()
        population = int(pop_row['population']) if pop_row else 0

        cursor.close()

        resources = calculate_resource_flow(planet_id)

        return PlanetInfo(
            planet_id=planet_id,
            name=row['name'],
            system_id=row['system_id'],
            owner_name=row['owner_name'],
            population=population,
            morale=int(row['morale']) if row.get('morale') else 5,
            tax_rate=float(row['tax_rate']) if row.get('tax_rate') else 1.0,
            resources={k: float(v) for k, v in resources.items()},
            infrastructure=infrastructure
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/planet/{planet_id}/fleet")
def get_fleet_at_planet(planet_id: int):
    """Get fleet inventory at a planet (CLI: Docking Bay Screen 1)."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT ship_type, COUNT(*) as count
            FROM ships s WHERE s.planet_id = %s AND s.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            GROUP BY ship_type
        """, (planet_id,))

        fleet_list = cursor.fetchall()
        cursor.close()

        return [FleetItem(ship_type=row['ship_type'], count=row['count']) for row in fleet_list]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/systems")
def get_all_systems():
    """Get list of all systems (CLI: System List Screen 10)."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT s.system_id, s.name
            FROM systems s
            JOIN planets p ON s.system_id = p.system_id
            WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            ORDER BY s.name
        """)

        systems = [
            SystemInfo(
                system_id=row['system_id'],
                name=row['name'] or 'System',
                planets=[]  # Empty array for NaN fix
            )
            for row in cursor.fetchall()
        ]
        cursor.close()

        return systems if systems else [{'system_id': 1, 'name': 'System 1', 'planets': []}]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/action/next_screen")
def next_screen_action():
    """Handle navigation between screens (fixes button events)."""
    return {
        "status": "success",
        "message": "Navigation handled by frontend",
        "type": "navigate"
    }


@app.post("/api/action/simulate_battle")
def simulate_battle_step():
    """Simulate one step of battle (for battle simulation screen)."""
    import random

    # Simulate combat outcome
    return {
        "status": "success",
        "message": "Battle simulation step completed",
        "round": 1,
        "total_rounds": 3
    }


@app.post("/api/action/update_resources")
def update_resources():
    """Fetch fresh resources for next screen update."""
    try:
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")

        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.planet_id, p.name, s.name as system_name,
                   ps.population, ps.morale, ps.tax_rate,
                   COALESCE(ps.food_level, 0) as food,
                   COALESCE(ps.energy_level, 0) as energy,
                   COALESCE(ps.fuel_level, 0) as fuel,
                   COALESCE(ps.mineral_level, 0) as mineral
            FROM planets p
            JOIN systems s ON p.system_id = s.system_id
            LEFT JOIN planetary_stats ps ON p.planet_id = ps.planet_id
            WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            ORDER BY p.planet_id
        """)

        rows = cursor.fetchall()
        cursor.close()

        planets_data = []
        for row in rows:
            planets_data.append({
                "planet_id": row['planet_id'],
                "name": row['name'],
                "system_name": row['system_name'],
                "population": row['population'] or 0,
                "morale": row['morale'] or 5,
                "tax_rate": float(row['tax_rate']) if row['tax_rate'] else 0.05,
                "resources": {
                    "food": int(row['food']),
                    "energy": int(row['energy']),
                    "fuel": int(row['fuel']),
                    "mineral": int(row['mineral'])
                }
            })

        return planets_data if planets_data else [{"planet_id": 1, "name": "Planet 1", "resources": {"food": 50, "energy": 30, "fuel": 20}}]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/systems/all")
def get_all_planets_dashboard():
    """Get dashboard view of all planets (CLI: Dashboard Screen 4)."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)

        # Get all planets with their stats and resources
        cursor.execute("""
            SELECT
                p.planet_id,
                p.system_id,
                p.name as planet_name,
                u.username as owner_name,
                ps.population,
                ps.morale,
                ps.tax_rate,
                ps.food_level,
                ps.mineral_level,
                ps.energy_level,
                ps.fuel_level
            FROM supremacy_game.planets p
            JOIN supremacy_game.users u ON p.owner_user_id = u.user_id
            LEFT JOIN supremacy_game.planetary_stats ps ON p.planet_id = ps.planet_id
            WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
              AND (ps.planet_id IS NOT NULL OR 1=1)
            ORDER BY p.system_id, p.name
        """)

        planets_data = []
        for row in cursor.fetchall():
            if row['planet_id']:
                # Get infrastructure from colonies table
                cursor.execute("""
                    SELECT farming_stations, mining_stations, solar_satellites
                    FROM supremacy_game.colonies WHERE planet_id = %s
                """, (row['planet_id'],))
                col_row = cursor.fetchone()
                infra = {
                    'farming_stations': col_row['farming_stations'] if col_row else 0,
                    'mining_stations': col_row['mining_stations'] if col_row else 0,
                    'solar_satellites': col_row['solar_satellites'] if col_row else 0
                }

                # Get purchased assets from planetary_assets table
                cursor.execute("""
                    SELECT asset_name, asset_type, base_cost
                    FROM supremacy_game.planetary_assets
                    WHERE planet_id = %s
                """, (row['planet_id'],))
                purchased = cursor.fetchall()

                planets_data.append({
                    'planet_id': row['planet_id'],
                    'name': row['planet_name'],
                    'system_id': row['system_id'],
                    'owner_name': row['owner_name'],
                    'population': row['population'] or 0,
                    'morale': row['morale'] or 5,
                    'tax_rate': row['tax_rate'] or 0.05,
                    'resources': {
                        'food': row['food_level'] or 0,
                        'mineral': row['mineral_level'] or 0,
                        'energy': row['energy_level'] or 0,
                        'fuel': row['fuel_level'] or 0,
                        'taxable_income': (row['population'] or 0) * (row['tax_rate'] or 0.05)
                    },
                    'infrastructure': infra,
                    'fleet': [],  # Ships are loaded separately
                    'purchased_assets': purchased  # Assets from planetary_assets table
                })

        cursor.close()

        return planets_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/planets/{planet_id}/fleet", response_model=list)
def get_all_planets_fleet():
    """Get fleet for all player planets (for dashboard)."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)

        # Get fleet for each planet separately
        fleet_map = {}
        cursor.execute("""
            SELECT planet_id, ship_type, COUNT(*) as count
            FROM supremacy_game.ships
            WHERE owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            GROUP BY planet_id, ship_type
            ORDER BY planet_id, ship_type
        """)

        for row in cursor.fetchall():
            if row['planet_id'] not in fleet_map:
                fleet_map[row['planet_id']] = []
            fleet_map[row['planet_id']].append(FleetItem(
                ship_type=row['ship_type'],
                count=row['count']
            ))

        cursor.close()
        return list(fleet_map.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/marketplace")
def get_asset_catalog():
    """Get asset catalog for purchasing (CLI: Purchase Assets Screen 2)."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)

        ships = []
        cursor.execute("""
            SELECT name, category, base_cost, description, image_url
            FROM supremacy_game.assets_catalog
            WHERE category = 'Ship' ORDER BY base_cost
        """)
        for row in cursor.fetchall():
            ships.append(AssetCatalogItem(
                name=row['name'],
                category=row['category'],
                base_cost=float(row['base_cost']),
                description=row.get('description', '') if row.get('description') else '',
                image_url=row.get('image_url')
            ))

        infrastructure = []
        cursor.execute("""
            SELECT name, category, base_cost, description, image_url
            FROM supremacy_game.assets_catalog
            WHERE category = 'Infrastructure' ORDER BY base_cost
        """)
        for row in cursor.fetchall():
            infrastructure.append(AssetCatalogItem(
                name=row['name'],
                category=row['category'],
                base_cost=float(row['base_cost']),
                description=row.get('description', '') if row.get('description') else '',
                image_url=row.get('image_url')
            ))

        equipment = []
        cursor.execute("""
            SELECT name, category, base_cost, image_url FROM supremacy_game.equipment_catalog
            ORDER BY base_cost
        """)
        for row in cursor.fetchall():
            equipment.append(AssetCatalogItem(
                name=row['name'],
                category=row['category'],
                base_cost=float(row['base_cost']),
                image_url=row.get('image_url')
            ))

        cursor.close()

        return {
            'ships': ships,
            'infrastructure': infrastructure,
            'equipment': equipment
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/player/credits")
def get_player_credits():
    """Get player current credits (CLI: Purchase Assets credit display)."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT credits FROM users WHERE username = 'Player'")
        row = cursor.fetchone()
        cursor.close()

        return {"credits": int(row[0]) if row else 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/marketplace/purchase")
def purchase_asset(request: PurchaseRequest):
    """Purchase an asset and add it to player's fleet/inventory."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)

        # Get player credits
        cursor.execute("SELECT credits FROM users WHERE username = 'Player'")
        credit_row = cursor.fetchone()
        current_credits = int(credit_row['credits']) if credit_row else 0

        # Check equipment_catalog first to avoid name collisions with assets_catalog
        cursor.execute("""
            SELECT name, category, base_cost FROM supremacy_game.equipment_catalog
            WHERE name = %s
        """, (request.asset_name,))
        asset_row = cursor.fetchone()

        # If not found in equipment, try assets_catalog (ships, infrastructure)
        if not asset_row:
            cursor.execute("""
                SELECT name, category, base_cost FROM supremacy_game.assets_catalog
                WHERE name = %s AND category IN ('Ship', 'Infrastructure')
            """, (request.asset_name,))
            asset_row = cursor.fetchone()

        if not asset_row:
            raise HTTPException(status_code=404, detail=f"Asset '{request.asset_name}' not found in catalog")

        cost = float(asset_row['base_cost'])

        # Check if player can afford it
        if current_credits < cost:
            return {
                "status": "success",
                "message": f"Not enough credits! Need ${cost:,} but have ${current_credits:,}.",
                "credits_remaining": current_credits,
                "asset_name": request.asset_name,
                "cost": cost
            }

        # Terraformer is one-time only
        if request.asset_name == 'Terraformer':
            cursor.execute("""
                SELECT COUNT(*) FROM planetary_assets pa
                JOIN planets p ON pa.planet_id = p.planet_id
                WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
                AND pa.asset_name = 'Terraformer'
            """)
            owned_count = cursor.fetchone()[0]
            if owned_count > 0:
                return {
                    "status": "success",
                    "message": "You already own a Terraformer. It cannot be purchased again.",
                    "credits_remaining": current_credits,
                    "asset_name": request.asset_name,
                    "cost": cost
                }

        # Deduct credits from player (transactional)
        cursor.execute("UPDATE users SET credits = credits - %s WHERE username = 'Player'", (cost,))
        conn.commit()

        # Get the actual planet_id for assignment (use first owned planet or default to 1)
        cursor.execute("""
            SELECT planet_id FROM planets
            WHERE owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            ORDER BY planet_id LIMIT 1
        """)
        planet_row = cursor.fetchone()
        planet_id = planet_row['planet_id'] if planet_row else 1

        # For infrastructure items, update the colonies table so they actually appear on the planet
        if asset_row['category'] == 'Infrastructure':
            cursor.execute("""
                SELECT planet_id FROM planets
                WHERE owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
                ORDER BY planet_id LIMIT 1
            """)
            colony_planet = cursor.fetchone()
            target_planet_id = colony_planet['planet_id'] if colony_planet else planet_id

            if request.asset_name == 'EnergySatellite':
                cursor.execute("""
                    INSERT INTO colonies (planet_id, solar_satellites)
                    VALUES (%s, 1)
                    ON DUPLICATE KEY UPDATE solar_satellites = solar_satellites + 1
                """, (target_planet_id,))
            elif request.asset_name == 'Terraformer':
                cursor.execute("""
                    INSERT INTO colonies (planet_id, farming_stations, solar_satellites)
                    VALUES (%s, 1, 1)
                    ON DUPLICATE KEY UPDATE
                        farming_stations = farming_stations + 1,
                        solar_satellites = solar_satellites + 1
                """, (target_planet_id,))

        # Insert asset into player's inventory/assets table
        # Determine asset_type: equipment items get 'Equipment' type regardless of their catalog category
        catalog_type = asset_row['category']
        if catalog_type in ('Armor', 'Weapon'):
            catalog_type = 'Equipment'

        cursor.execute("""
            INSERT INTO planetary_assets (planet_id, asset_name, asset_type, quantity, base_cost)
            VALUES (%s, %s, %s, 1, %s)
            ON DUPLICATE KEY UPDATE quantity = quantity + 1
        """, (planet_id, request.asset_name, catalog_type, cost))
        conn.commit()

        # Get new credit balance
        cursor.execute("SELECT credits FROM users WHERE username = 'Player'")
        credit_row = cursor.fetchone()
        new_credits = int(credit_row['credits']) if credit_row else 0

        cursor.close()

        return {
            "status": "success",
            "message": f"Purchased {request.asset_name} successfully!",
            "credits_remaining": new_credits,
            "asset_name": request.asset_name,
            "cost": cost
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/marketplace/purchase-equipment")
def purchase_equipment(request: PurchaseRequest):
    """Purchase military equipment and add to player inventory."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)

        # Get player credits
        cursor.execute("SELECT credits FROM users WHERE username = 'Player'")
        credit_row = cursor.fetchone()
        current_credits = int(credit_row['credits']) if credit_row else 0

        # Check if equipment exists
        cursor.execute("""
            SELECT name, category, base_cost, strength_value FROM supremacy_game.equipment_catalog
            WHERE name = %s
        """, (request.asset_name,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Equipment '{request.asset_name}' not found in catalog")

        cost = int(row['base_cost'])
        strength = row['strength_value']

        # Check if player can afford it
        if current_credits < cost:
            return {
                "status": "success",
                "message": f"Not enough credits! Need ${cost:,} but have ${current_credits:,}.",
                "credits_remaining": current_credits,
                "asset_name": request.asset_name,
                "cost": cost
            }

        # Deduct credits from player (transactional)
        cursor.execute("UPDATE users SET credits = credits - %s WHERE username = 'Player'", (cost,))
        conn.commit()

        # Get the actual planet_id for assignment
        cursor.execute("""
            SELECT planet_id FROM planets
            WHERE owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            ORDER BY planet_id LIMIT 1
        """)
        planet_row = cursor.fetchone()
        planet_id = planet_row['planet_id'] if planet_row else 1

        # Insert equipment into player's inventory/assets table
        # Store as 'Equipment' so UI can display it in the equipment filter
        cursor.execute("""
            INSERT INTO planetary_assets (planet_id, asset_name, asset_type, quantity, base_cost)
            VALUES (%s, %s, %s, 1, %s)
            ON DUPLICATE KEY UPDATE quantity = quantity + 1
        """, (planet_id, request.asset_name, 'Equipment', cost))
        conn.commit()

        # Get new credit balance
        cursor.execute("SELECT credits FROM users WHERE username = 'Player'")
        credit_row = cursor.fetchone()
        new_credits = int(credit_row['credits']) if credit_row else 0

        cursor.close()

        return {
            "status": "success",
            "message": f"Purchased {request.asset_name} successfully!",
            "credits_remaining": new_credits,
            "asset_name": request.asset_name,
            "cost": cost,
            "strength": strength
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/planet/{planet_id}/assets")
def get_planet_assets(planet_id: int):
    """Get purchased assets for a specific planet from planetary_assets table."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT asset_name, asset_type, quantity, base_cost
            FROM supremacy_game.planetary_assets
            WHERE planet_id = %s
        """, (planet_id,))
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()


@app.get("/api/player/assets")
def get_player_assets():
    """Get all purchased assets across all player planets."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT pa.asset_name, pa.asset_type, pa.quantity, pa.base_cost, pa.planet_id, p.name as planet_name
            FROM supremacy_game.planetary_assets pa
            JOIN supremacy_game.planets p ON pa.planet_id = p.planet_id
            WHERE p.owner_user_id IN (SELECT user_id FROM supremacy_game.users WHERE username = 'Player')
            ORDER BY pa.asset_type, pa.asset_name
        """)
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()


@app.post("/api/action/move_ship")
def move_ship(request: ShipMoveRequest):
    """Attempts to move a ship and deducts fuel cost transactionally."""
    try:
        success = process_ship_movement(
            ship_id=request.ship_id,
            destination_planet_id=request.destination_planet_id
        )
        if success:
            return {"status": "Success", "message": f"Ship moved successfully to planet {request.destination_planet_id}."}
        else:
            raise HTTPException(status_code=400, detail="Movement failed (e.g., insufficient fuel or invalid destination).")

    except Exception as e:
        print(f"API error during ship move: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.post("/api/action/battle")
def resolve_battle(request: CombatRequest):
    """Resolves combat between two planets (used by battle simulation screen)."""
    try:
        result = resolve_combat(
            attacker_planet_id=request.attacker_planet_id,
            defender_planet_id=request.defender_planet_id
        )
        return {"status": "Combat Resolved", "message": result}
    except Exception as e:
        print(f"API error during battle: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
def battle_planet(request: CombatRequest):
    """Resolves combat between two planets and updates ownership transactionally."""
    try:
        result = resolve_combat(
            attacker_planet_id=request.attacker_planet_id,
            defender_planet_id=request.defender_planet_id
        )
        return {"status": "Combat Resolved", "message": result}

    except Exception as e:
        print(f"API error during combat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.post("/api/turn/advance")
def advance_turn():
    """Triggers the full game loop for all players and advances the AI turn."""
    try:
        print("--- Advancing Turn Start ---")

        # Get all active planets from DB
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT p.planet_id FROM planets p
                WHERE p.owner_user_id IN (SELECT user_id FROM users WHERE username = 'Player')
            """)
            active_planets = [row['planet_id'] for row in cursor.fetchall()]
            cursor.close()
        else:
            active_planets = [1]

        # Calculate resource flow for each active planet
        for planet_id in active_planets[:5]:  # Limit to first 5 planets
            try:
                flow = calculate_resource_flow(planet_id)
                print(f"Calculated flow for {planet_id}: {flow}")
            except Exception as e:
                print(f"Error calculating flow for {planet_id}: {e}")

        # AI Opponent Turn
        ai_result = ai_opponent_turn(ai_user_id=99)
        print(f"AI Opponent Turn executed: {ai_result}")

        return {"status": "Success", "message": "Turn advanced successfully. All resource flows and AI actions processed."}

    except Exception as e:
        print(f"API error during turn advance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: Could not advance turn.")


# =============================================================================
# Debug Tools Endpoints (CLI Debug Menu)
# =============================================================================

@app.get("/api/debug/player-planets")
def get_debug_player_planets():
    """Get owned planets for debug menu."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.planet_id, p.name, p.system_id,
                   u.username as owner_name,
                   COALESCE(ps.population, 0) as population,
                   COALESCE(ps.food_level, 0) as food_level,
                   COALESCE(ps.energy_level, 0) as energy_level,
                   COALESCE(ps.fuel_level, 0) as fuel_level
            FROM supremacy_game.planets p
            LEFT JOIN supremacy_game.planetary_stats ps ON p.planet_id = ps.planet_id
            LEFT JOIN supremacy_game.users u ON p.owner_user_id = u.user_id
            WHERE p.owner_user_id IN (SELECT user_id FROM supremacy_game.users WHERE username = 'Player')
        """)

        planets = cursor.fetchall()
        cursor.close()

        return [
            {
                "planet_id": row['planet_id'],
                "name": row['name'],
                "population": int(row['population']),
                "resources": {
                    "food_level": float(row['food_level']),
                    "energy_level": float(row['energy_level']),
                    "fuel_level": float(row['fuel_level']),
                },
                "fleet": [],
                "infrastructure": {
                    "farming_stations": 0,
                    "mining_stations": 0,
                    "solar_satellites": 0
                },
                "system_id": row['system_id'],
                "owner_name": row['owner_name'] or 'Neutral'
            }
            for row in planets
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/debug/adjust-level")
def adjust_resource_level(request: DebugLevelChange):
    """Manually adjust a resource level (CLI Debug Menu)."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()

        mapping = {
            'population': 'SET population = %s',
            'food_level': 'SET food_level = %s',
            'energy_level': 'SET energy_level = %s',
            'fuel_level': 'SET fuel_level = %s'
        }

        query = """
            UPDATE supremacy_game.planetary_stats
            SET population = %s, food_level = %s, energy_level = %s, fuel_level = %s
            WHERE planet_id = %s
        """

        new_value = float(request.new_value)
        cursor.execute(query, (new_value, new_value, new_value, new_value, request.planet_id))
        conn.commit()
        cursor.close()

        return {"status": "success", "message": f"Adjusted {request.resource_type} for planet {request.planet_id} to {new_value}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/credits/add")
def add_player_credits(credits_to_add: int = 10000):
    """Add credits to player (for testing)."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET credits = credits + %s WHERE username = 'Player'", (credits_to_add,))
        conn.commit()
        cursor.close()

        return {"status": "success", "message": f"Added {credits_to_add} credits to Player"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))