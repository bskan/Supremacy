import React, { useState, useEffect } from 'react';
// Mirror CLI Screen 1: Docking Bay - Ship movement and fleet management

interface FleetManagementProps {
  onBack: () => void;
  setActivePlanetId?: (id: number) => void;
}

// Helper to format large numbers with commas
const formatNumber = (num: any): string => {
  if (num === null || num === undefined) return '0';
  const n = typeof num === 'string' ? parseFloat(num) : num;
  return Math.abs(n) >= 1000000 ? (n / 1000000).toFixed(2) + 'M'
    : Math.abs(n) >= 1000 ? (n / 1000).toFixed(1) + 'K'
    : n.toLocaleString();
};

const FleetManagement: React.FC<FleetManagementProps> = ({ onBack, setActivePlanetId }) => {
  const [fleet, setFleet] = useState<Array<{ ship_type: string; count: number }>>([]);
  const [allPlanets, setAllPlanets] = useState<any[]>([]);
  const [activePlanet, setActivePlanet] = useState<number | null>(null);
  const [purchasedShips, setPurchasedShips] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState("Loading fleet data...");
  const [playerCredits, setPlayerCredits] = useState<number | null>(null);

  useEffect(() => {
    loadPlayerCredits();
  }, []);

  // Load player credits
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

  // Load fleet at active planet (or first owned planet if none selected)
  useEffect(() => {
    loadFleet();
  }, [activePlanet]);

  const loadFleet = async () => {
    try {
      setIsLoading(true);
      let planetId = activePlanet;

      // If no planet selected, show dock (no fleet) and list all planets
      if (!planetId) {
        fetch('/api/planets')
          .then(res => res.ok ? res.json() : [])
          .then(setAllPlanets)
          .catch(() => setAllPlanets([]))
          .finally(() => setIsLoading(false));
        return;
      }

      // Get fleet at active planet
      const res = await fetch('/api/planet/' + planetId);
      if (res.ok) {
        const data = await res.json();
        setFleet(data.resources?.fleet || []);
        setAllPlanets([]);
        setMessage(`At ${data.name}: Fleet loaded.`);

        // Fetch purchased ships for this planet
        const assetsRes = await fetch(`/api/planet/${planetId}/assets`);
        if (assetsRes.ok) {
          const assets = await assetsRes.json();
          setPurchasedShips(assets.filter((a: any) => a.asset_type === 'Ship'));
        }
      }

    } catch (error: any) {
      console.error('Error loading fleet:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Show all planets list view with fleet data
  const showAllPlanets = async () => {
    try {
      setIsLoading(true);
      const res = await fetch('/api/planets');
      if (res.ok) {
        const data = await res.json();
        setAllPlanets(data);

        // Build fleet summary with owner info
        const planetWithFleet: any[] = data.map(planet => {
          const totalShips = planet.resources?.fleet?.reduce((sum: number, ship: any) => sum + ship.count, 0) || 0;
          return {
            ...planet,
            totalShips,
            fleetCount: totalShips
          };
        });

        setMessage(`Viewing fleet across ${planetWithFleet.length} planets`);
      }
    } catch (error: any) {
      console.error('Error:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // View fleet overview across all systems
  const showFleetOverview = async () => {
    try {
      setIsLoading(true);
      // Simulated fleet overview (would aggregate from multiple planets)
      const sampleFleet: any[] = [
        { ship_type: 'Destroyer', count: 5 },
        { ship_type: 'Cruiser', count: 3 },
        { ship_type: 'Battleship', count: 2 },
      ];
      setFleet(sampleFleet);
      setMessage("Fleet overview mode - showing all ships across systems.");
    } catch (error: any) {
      console.error('Error:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Move ship handler (mirrors process_ship_movement logic)
  const moveShip = async () => {
    if (!activePlanet) {
      setMessage("Please select a planet to view fleet first.");
      return;
    }

    try {
      setIsLoading(true);
      const res = await fetch('/api/action/move_ship', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ship_id: 1, destination_planet_id: activePlanet }),
      });

      const data = await res.json();
      if (res.ok) {
        setMessage(data.message || "Ship moved successfully!");
        loadFleet(); // Refresh fleet
      } else {
        setMessage(`Move failed: ${data.detail}`);
      }
    } catch (error: any) {
      console.error('Error moving ship:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Render fleet view at single planet
  const renderFleetView = () => (
    <div className="screen docking-bay-screen">
      <button onClick={onBack} className="back-btn">&larr; Main Menu</button>

      <h2>Docking Bay - Fleet Management</h2>

      <div className={`message-box ${isLoading ? 'loading' : ''}`}>
        <strong>Status:</strong> {message}
      </div>

      <div className="fleet-view">
        <div className="section-header">
          <span className="section-title">&#128663; Fleet at Planet</span>
          <div className="planet-info" onClick={showAllPlanets} style={{cursor: 'pointer'}}>
            {activePlanet ? (
              <><span>Fleet:</span><strong>{fleet.length > 0 ? fleet.length : 'None'}</strong></>
            ) : (
              <span>Select a planet to view fleet</span>
            )}
          </div>
        </div>

        {/* Fleet List */}
        {fleet.length > 0 && (
          <div className="fleet-list">
            {fleet.map((ship, idx) => (
              <div key={idx} className="fleet-item">
                <span className="fleet-icon">&#9851;</span>
                <strong>{ship.ship_type}</strong>
                <span className="fleet-count">&times;{ship.count}</span>
              </div>
            ))}
          </div>
        )}

        {/* Purchased Ships */}
        {purchasedShips.length > 0 && (
          <div className="fleet-list">
            <div className="section-header">
              <span className="section-title">&#9876; Purchased Ships</span>
            </div>
            {purchasedShips.map((ship: any, idx: number) => {
              const qty = ship.quantity || 1;
              return (
              <div key={idx} className="fleet-item">
                <span className="fleet-icon">&#9851;</span>
                <strong>{ship.asset_name} x{qty}</strong>
                <span className="fleet-count" title={`${Math.floor(ship.base_cost).toLocaleString()} credits each`}>
                  {Math.floor(ship.base_cost).toLocaleString()} credits
                </span>
              </div>
            );
            })}
          </div>
        )}

        {/* Dock status */}
        {!fleet.length && (
          <div className="dock-status">
            <span className="dock-icon">&#128176;</span>
            <strong>Dock is clear</strong>
            <span>No ships currently docked here.</span>
          </div>
        )}

        {/* Actions */}
        <div className="fleet-actions">
          <button onClick={moveShip} disabled={!activePlanet || fleet.length === 0} className="btn btn-secondary">
            &#10147; Move Ship to Dock
          </button>

          <button onClick={showAllPlanets} className="btn btn-secondary">
            &#128083; View All Planets Fleet Status
          </button>

          <button onClick={onBack} className="btn btn-secondary">
            &#9654; Return to Main Menu
          </button>
        </div>

        {/* Instructions - Mirror CLI dock actions */}
        <div className="fleet-instructions">
          <h4>Docking Bay Actions:</h4>
          <ul>
            <li>&#128663; View fleet inventory at current planet</li>
            <li>&#10147; Move ships to/from dock (requires fuel)</li>
            <li>&#128083; View fleet status across all planets</li>
          </ul>
        </div>
      </div>
    </div>
  );

  // Render all planets list view with fleet data
  const renderAllPlanetsView = () => (
    <div className="screen docking-bay-screen">
      <button onClick={onBack} className="back-btn">&larr; Main Menu</button>

      <h2>Fleet at All Planets</h2>

      {/* Credits Display */}
      {allPlanets.length === 0 && (
        <div className="credits-display">
          &#8363; {formatNumber(playerCredits || 0)} Credits Available
        </div>
      )}

      <div className={`message-box ${isLoading ? 'loading' : ''}`}>
        <strong>Status:</strong> {message}
      </div>

      {allPlanets.length === 0 && (
        <div className="no-fleet">
          No ships owned yet. Use <strong>Purchase Assets</strong> to acquire ships.
        </div>
      )}

      {allPlanets.length > 0 && (
        <>
          <div className="fleet-overview">
            <h3>Fleet Overview by System</h3>
            {allPlanets.map((planet) => {
              const fleetCount = planet.resources?.fleet?.reduce((sum: number, ship: any) => sum + ship.count, 0) || 0;
              return (
                <div key={planet.id} className="fleet-system">
                  <div className="fleet-header">
                    <strong>{planet.name}</strong>
                    <span className="system-name">{planet.system_name}</span>
                    {planet.infrastructure?.farming_stations && (
                      <span className="inf-stats" title="Production Stats">
                        Farm: {planet.infrastructure.farming_stations} | Mine: {planet.infrastructure.mining_stations} | Solar: {planet.infrastructure.solar_satellites}
                      </span>
                    )}
                  </div>
                  {fleetCount > 0 && (
                    <div className="fleet-grid">
                      {planet.resources.fleet.map((ship: any, idx: number) => {
                        const pop = planet.population || 1;
                        const shipsHere = ship.count;
                        return (
                          <div key={idx} className="fleet-card">
                            <span className="fleet-icon">&#9851;</span>
                            <strong>{ship.ship_type}</strong>
                            <span className="fleet-count">&times;{ship.count}</span>
                            {/* Ship consumption stats */}
                            <div className="ship-stats">
                              Fuel: &ndash;{(ship.fuel_consumption?.fuel || 0) * shipsHere.toFixed(1)} |
                              Minerals: &ndash;{(ship.fuel_consumption?.minerals || 0) * shipsHere.toFixed(1)}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Actions */}
          <div className="fleet-actions">
            <button onClick={() => { setActivePlanet(null); loadFleet(); }} className="btn btn-primary">
              &#128663; Back to Single Planet View
            </button>
            <button onClick={onBack} className="btn btn-secondary">
              &#9654; Return to Main Menu
            </button>
          </div>
        </>
      )}
    </div>
  );

  // Render fleet overview view
  const renderFleetOverviewView = () => (
    <div className="screen docking-bay-screen">
      <button onClick={onBack} className="back-btn">&larr; Main Menu</button>

      <h2>&#128640; Fleet Overview - All Ships Across Systems</h2>

      {/* Credits Display */}
      {allPlanets.length === 0 && (
        <div className="credits-display">
          &#8363; {formatNumber(playerCredits || 0)} Credits Available
        </div>
      )}

      <div className={`message-box ${isLoading ? 'loading' : ''}`}>
        <strong>Status:</strong> {message}
      </div>

      <div className="fleet-overview">
        <h3>Total Fleet: {formatNumber(fleet.reduce((acc, ship) => acc + ship.count, 0))} ships</h3>
        {fleet.length === 0 && (
          <div className="no-fleet">No ships currently in fleet. Purchase assets from the marketplace.</div>
        )}

        {fleet.length > 0 && (
          <div className="fleet-list">
            {fleet.map((ship, idx) => (
              <div key={idx} className="fleet-item">
                <span className="fleet-icon">&#9851;</span>
                <strong>{ship.ship_type}</strong>
                <span className="fleet-count">&times;{ship.count}</span>
              </div>
            ))}
          </div>
        )}

        {/* Fleet by System breakdown */}
        {allPlanets.length > 0 && (
          <div className="fleet-by-system">
            <h4>Fleet Distribution by System:</h4>
            {allPlanets.map((planet) => {
              const planetFleet = planet.resources?.fleet?.reduce((sum: number, ship: any) => sum + ship.count, 0) || 0;
              if (planetFleet === 0 && !Array.isArray(planet.resources?.fleet)) return null;
              return (
                <div key={planet.id} className="system-fleet-card">
                  <strong>{planet.name}</strong> - {formatNumber(planetFleet)} ships in {planet.system_id || planet.system_name || 'System'}
                </div>
              );
            })}
          </div>
        )}

        {/* Actions */}
        <div className="fleet-actions">
          <button onClick={showFleetOverview} disabled={true} className="btn btn-secondary">
            &#128196; Show Fleet Overview (Same View)
          </button>
          <button onClick={() => { setActivePlanet(null); loadFleet(); }} className="btn btn-primary">
            &#128663; Back to Docking Bay
          </button>
        </div>
      </div>
    </div>
  );

  // Render fleet at each planet view
  const renderPlanetsView = () => (
    <div className="screen docking-bay-screen">
      <button onClick={onBack} className="back-btn">&larr; Main Menu</button>

      <h2>Your Planets & Fleets</h2>

      <div className={`message-box ${isLoading ? 'loading' : ''}`}>
        <strong>Status:</strong> {message}
      </div>

      <div className="planets-list">
        {allPlanets.length === 0 && (
          <div className="no-fleet">No planets discovered yet.</div>
        )}

        {allPlanets.map((planet) => {
          const fleetAtPlanet = planet.resources?.fleet?.reduce((sum: number, ship: any) => sum + ship.count, 0) || 0;
          const isOwned = planet.owner_name === 'Player';
          return (
            <div key={planet.id} className="planet-dock-card" onClick={() => { setActivePlanet(planet.id); loadFleet(); }} style={{cursor: 'pointer'}}>
              <h3>{planet.name}</h3>
              <span className="system-tag">{planet.system_name || planet.system_id}</span>
              <span className={`owner-badge ${isOwned ? 'owned' : 'neutral'}`}>{isOwned ? 'OWNED' : 'NEUTRAL'}</span>
              <div className="fleet-status">
                &#9851; Fleet: {fleetAtPlanet > 0 ? formatNumber(fleetAtPlanet) : 'None'} ships
              </div>
              <button onClick={() => { setActivePlanet(planet.id); loadFleet(); }}>
                View Dock
              </button>
            </div>
          );
        })}

        {/* Actions */}
        <div className="fleet-actions">
          <button onClick={showFleetOverview} className="btn btn-primary">
            &#128640; Show Fleet Overview
          </button>
          <button onClick={() => { setActivePlanet(null); loadFleet(); }} className="btn btn-primary">
            &#128213; View Docking Bay
          </button>
        </div>
      </div>
    </div>
  );

  // Render fleet view (default) or all planets view based on state
  return activePlanet ? renderFleetView() :
         allPlanets.length > 0 ? renderAllPlanetsView() :
         allPlanets.length === 0 && fleet.length === 0 ? renderFleetOverviewView() :
         renderPlanetsView();
};

export default FleetManagement;
