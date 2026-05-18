import React, { useState, useCallback, useEffect } from 'react';
// Assuming api_service.ts handles all API interactions
import * as ApiService from '../services/api_service';
import EventLog from './EventLog';

/** Helper to format large numbers with commas */
const formatNumber = (num: any): string => {
  if (num === null || num === undefined) return '0';
  const n = typeof num === 'string' ? parseFloat(num) : num;
  return Math.abs(n) >= 1000000 ? (n / 1000000).toFixed(2) + 'M'
    : Math.abs(n) >= 1000 ? (n / 1000).toFixed(1) + 'K'
    : n.toLocaleString();
};

/**
 * Component to display the user's planetary status and allow action execution.
 * This is the main dashboard component for the player's experience - loads ALL data from database.
 */
const Dashboard: React.FC = () => {
    // State management for key game elements
    const [isLoading, setIsLoading] = useState(false);
    const [planets, setPlanets] = useState<any[]>([]); // Array of planet state objects from database
    const [message, setMessage] = useState("");
    const [playerCredits, setPlayerCredits] = useState<number | null>(null);
    const [assetCount, setAssetCount] = useState<number | null>(null);

    useEffect(() => {
        loadPlayerCredits();
        loadAssetCount();
    }, []);

    const loadPlayerCredits = async () => {
        try {
            const res = await fetch('/api/player/credits');
            if (res.ok) {
                const data = await res.json();
                setPlayerCredits(data.credits || 0);
            }
        } catch (error) {
            console.error('Error loading player credits:', error);
        }
    };

    const loadAssetCount = async () => {
        try {
            const res = await fetch('/api/player/assets');
            if (res.ok) {
                const data = await res.json();
                setAssetCount(Array.isArray(data) ? data.length : 0);
            }
        } catch (error) {
            console.error('Error loading asset count:', error);
        }
    };

    // --- Fetching Data (Golden Path) ---
    const fetchPlanetData = useCallback(async () => {
        setIsLoading(true);
        setMessage("Loading planetary system data from database...");
        try {
            // Fetch all planets with full data from /api/systems/all endpoint
            const planetStates = await ApiService.getDashboardState();

            // Also fetch fleet for each planet
            const fleetMap: Record<number, any[]> = {};
            const fleetResponse = await fetch('/api/planets/*/fleet');
            if (fleetResponse.ok) {
                const fleets: any[] = await fleetResponse.json();
                fleets.forEach((fleet: any) => {
                    if (fleet.planet_id !== undefined) fleetMap[fleet.planet_id] = fleet;
                });
            }

            // Merge fleet data into planet objects
            const planetsWithFleet: any[] = planetStates.map((planet: any) => ({
                ...planet,
                fleet: fleetMap[planet.planet_id] || []
            }));

            setPlanets(planetsWithFleet);
            setMessage(`System ready. ${planetsWithFleet.length} planets monitored. Ready to advance turn or issue commands.`);
        } catch (error: any) {
            console.error("Error fetching state:", error);
            setMessage(`Error loading map data: ${error.message || 'Unknown error'}. Please check your API connection.`);
        } finally {
            setIsLoading(false);
        }
    }, []);

    // --- Action Handlers ---

    const handleAdvanceTurn = useCallback(async () => {
        if (isLoading) return;
        setIsLoading(true);
        setMessage("Advancing turn... Calculating resource flows and AI actions...");
        try {
            await ApiService.advanceTurn();
            setMessage("✅ Turn advanced successfully! Check the planet states for updates.");
            fetchPlanetData(); // Refetch data after successful turn
        } catch (error: any) {
            console.error("Error advancing turn:", error);
            setMessage(`❌ Failed to advance turn: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    }, [fetchPlanetData, isLoading]);

    const handleShipMovement = useCallback(async (shipId: number, destPlanetId: number) => {
        if (isLoading) return;
        setMessage(`Attempting to move ship ${shipId} to planet ${destPlanetId}...`);
        try {
            await ApiService.moveShip(shipId, destPlanetId);
            setMessage("✅ Ship movement successful! The map will refresh shortly.");
            fetchPlanetData(); // Refetch data after successful action
        } catch (error: any) {
            console.error("Error moving ship:", error);
            setMessage(`❌ Failed to move ship: ${error.message}. Check fuel or pathfinding.`);
        } finally {
            setIsLoading(false);
        }
    }, [fetchPlanetData, isLoading]);

    // Effect to load data on initial mount
    React.useEffect(() => {
        fetchPlanetData();
    }, [fetchPlanetData]);

    return (
        <div className="dashboard-container">
            <h1>Planetary System Dashboard</h1>

            {/* Credits & Assets Display */}
            <div className="credits-display">
                <span>&#8363; {formatNumber(playerCredits || 0)} Credits</span>
                {assetCount !== null && (
                    <span>&#128722; {assetCount} Assets</span>
                )}
            </div>

            {/* Global Status Message Box */}
            <div className={`message-box ${isLoading ? 'loading' : ''}`}>
                <strong>Status:</strong> {message}
            </div>

            {/* Action Buttons Area */}
            <div className="controls">
                <button
                    onClick={handleAdvanceTurn}
                    disabled={isLoading}
                    className="primary-action"
                >
                    {isLoading ? 'Processing...' : '⚡ Advance Turn (Process All Systems)'}
                </button>
                <button
                    onClick={() => { /* Placeholder for initiating combat */ }}
                    disabled={isLoading}
                    className="secondary-action"
                >
                    🚀 Initiate Combat
                </button>
            </div>

            {/* Planet Map/List */}
            <h2>Planets in System ({planets.length})</h2>
            <div className="planet-grid">
                {planets.map((planet) => (
                    <PlanetCard key={planet.planet_id} planet={planet} onMove={() => { /* Logic to prompt user for ship/destination */ }} />
                ))}
            </div>

            {/* Random Events Log */}
            <EventLog />
        </div>
    );
};

// Component to display individual planet info with full database data
const PlanetCard: React.FC<{ planet: any, onMove: () => void }> = ({ planet, onMove }) => {
    const purchased = planet.purchased_assets || [];
    const ships = purchased.filter((a: any) => a.asset_type === 'Ship');
    const infra = purchased.filter((a: any) => a.asset_type === 'Infrastructure');
    const equipment = purchased.filter((a: any) => a.asset_type === 'Equipment');
    const owned = planet.owner_name === 'Player';
    const planetTotal = purchased.reduce((s: number, a: any) => s + (a.quantity || 1), 0);

    return (
        <div className={`planet-card ${owned ? 'owned' : ''}`} style={{ cursor: 'pointer' }}>
            {/* Planet Header */}
            <h3>{planet.name}</h3>

            {/* System ID Badge */}
            <span className="system-tag">System {planet.system_id}</span>

            {/* Ownership Status */}
            <span className={`owner-badge ${owned ? 'owned' : 'neutral'}`}>
                {owned ? 'OWNED' : planet.owner_name || 'Neutral'}
            </span>

            {/* Population & Tax Info */}
            <div className="planet-meta">
                <span><strong>Population:</strong> {formatNumber(planet.population || 0)}</span>
                <span><strong>Tax Income:</strong> &#8363;{formatNumber((planet.resources?.taxable_income || 0))}/turn</span>
            </div>

            {/* Resource Levels - Full database data */}
            <div className="resource-levels">
                <span title="Food production for population"><strong>&#127851; Food:</strong> {Math.floor(planet.resources?.food || 0)}</span>
                <span title="Energy for ships and operations"><strong>&#9889; Energy:</strong> {Math.floor(planet.resources?.energy || 0)}</span>
                <span title="Fuel from mining/processing"><strong>&#128172; Fuel:</strong> {Math.floor(planet.resources?.fuel || 0)}</span>
                <span title="Raw minerals from mines"><strong>&#9874; Minerals:</strong> {Math.floor(planet.resources?.mineral || 0)}</span>
            </div>

            {/* Infrastructure - Direct database values */}
            <div className="infrastructure-stats">
                <span title="Food production: +15 food per station"><strong>&#127950; Farms:</strong> {planet.infrastructure?.farming_stations || 0}</span>
                <span title="Mineral extraction: +8 minerals per station"><strong>&#9874; Mines:</strong> {planet.infrastructure?.mining_stations || 0}</span>
                <span title="Energy generation: +12 energy per satellite"><strong>&#9650; Solar:</strong> {planet.infrastructure?.solar_satellites || 0}</span>
            </div>

            {/* Fleet Display - Shows all ships docked at this planet */}
            {planet.fleet && planet.fleet.length > 0 && (
                <div className="fleet-display">
                    <strong>&#9851; Fleet Docked:</strong>
                    <div className="fleet-list">
                        {planet.fleet.map((ship: any, idx: number) => (
                            <span key={idx} title={`${ship.ship_type}: ${ship.count} ships`}>
                                &#9851; &times;{ship.count} ({ship.ship_type})
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Purchased Assets */}
            {planetTotal > 0 && (
                <div className="purchased-assets">
                    {ships.length > 0 && (
                        <div className="purchased-section">
                            <strong>&#9851; Ships:</strong>
                            {ships.map((a: any, i: number) => (
                                <span key={i} className="purchased-item">{a.asset_name} x{a.quantity}</span>
                            ))}
                        </div>
                    )}
                    {infra.length > 0 && (
                        <div className="purchased-section">
                            <strong>&#128736; Infrastructure:</strong>
                            {infra.map((a: any, i: number) => (
                                <span key={i} className="purchased-item">{a.asset_name} x{a.quantity}</span>
                            ))}
                        </div>
                    )}
                    {equipment.length > 0 && (
                        <div className="purchased-section">
                            <strong>&#128663; Equipment:</strong>
                            {equipment.map((a: any, i: number) => (
                                <span key={i} className="purchased-item">{a.asset_name} x{a.quantity}</span>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Action Button */}
            <button onClick={onMove}>View Details / Move Ship</button>
        </div>
    );
};

export default Dashboard;