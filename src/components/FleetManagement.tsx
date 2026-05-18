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
  const [individualShips, setIndividualShips] = useState<any[]>([]);
  const [allPlanets, setAllPlanets] = useState<any[]>([]);
  const [activePlanet, setActivePlanet] = useState<number | null>(null);
  const [destPlanet, setDestPlanet] = useState<number | null>(null);
  const [selectedShipId, setSelectedShipId] = useState<number | null>(null);
  const [purchasedShips, setPurchasedShips] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState("Loading fleet data...");
  const [playerCredits, setPlayerCredits] = useState<number | null>(null);
  const allPlanetsRef = React.useRef<any[]>([]);

  // Transfer tab: 'move' or 'cargo'
  const [transferTab, setTransferTab] = useState<'move' | 'cargo'>('move');
  const [transferType, setTransferType] = useState<string>('');
  const [transferQuantity, setTransferQuantity] = useState<number>(1);

  // Cargo tab state
  const [cargoShipType, setCargoShipType] = useState<string>('CargoShip');
  const [cargoResource, setCargoResource] = useState<string>('food');
  const [cargoQuantity, setCargoQuantity] = useState<number>(100);
  const [cargoData, setCargoData] = useState<Record<string, Record<string, number>>>({});

  const transferPlanetsRef = React.useRef<any[]>([]);

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

  // Load all planets list on mount for destination selector
  useEffect(() => {
    loadAllPlanets();
  }, []);

  const loadAllPlanets = async () => {
    try {
      const res = await fetch('/api/planets');
      if (res.ok) {
        const data = await res.json();
        setAllPlanets(data);
      }
    } catch (error) {
      setAllPlanets([]);
    }
  };

  const loadFleet = async () => {
    try {
      setIsLoading(true);
      let planetId = activePlanet;

      // If no planet selected, show dock (no fleet) and list all planets
      if (!planetId) {
        setSelectedShipId(null);
        setIndividualShips([]);
        fetch('/api/planets')
          .then(res => res.ok ? res.json() : [])
          .then(setAllPlanets)
          .catch(() => setAllPlanets([]))
          .finally(() => setIsLoading(false));
        return;
      }
      setSelectedShipId(null);

      // Get fleet at active planet
      const res = await fetch('/api/planet/' + planetId);
      if (res.ok) {
        const data = await res.json();
        setFleet(data.fleet || data.resources?.fleet || []);
        setMessage(`At ${data.name}: Fleet loaded.`);

        // Load transfer data (destinations, cargo)
        loadTransferData();

        // Fetch individual ship records for movement selection
        const detailsRes = await fetch('/api/planet/' + planetId + '/fleet/details');
        if (detailsRes.ok) {
          const details = await detailsRes.json();
          setIndividualShips(details);
          setPurchasedShips(details);
        } else {
          setIndividualShips([]);
          setPurchasedShips([]);
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
        allPlanetsRef.current = data;

        // Build fleet summary with owner info
        const planetWithFleet: any[] = data.map((planet: any) => {
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
      const res = await fetch('/api/planets');
      if (res.ok) {
        const data = await res.json();
        const agg: Record<string, number> = {};
        for (const planet of data) {
          const fleet = planet.fleet || planet.resources?.fleet || [];
          for (const ship of fleet) {
            agg[ship.ship_type] = (agg[ship.ship_type] || 0) + ship.count;
          }
        }
        setFleet(Object.entries(agg).map(([ship_type, count]) => ({ ship_type, count })));
        setMessage(`Fleet overview across ${data.length} planets.`);
        allPlanetsRef.current = data;
      }
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
    if (!destPlanet) {
      setMessage("Please select a destination planet.");
      return;
    }
    if (destPlanet === activePlanet) {
      setMessage("Destination must be different from current planet.");
      return;
    }
    if (!selectedShipId) {
      setMessage("Please select a ship to move.");
      return;
    }

    try {
      setIsLoading(true);
      const res = await fetch('/api/action/move_ship', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ship_id: selectedShipId, destination_planet_id: destPlanet }),
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

  // Transfer ships between planets
  const transferShips = async () => {
    if (!activePlanet) {
      setMessage("Please select a planet first.");
      return;
    }
    if (!destPlanet) {
      setMessage("Please select a destination planet.");
      return;
    }
    if (destPlanet === activePlanet) {
      setMessage("Destination must be different from source.");
      return;
    }
    if (!transferType) {
      setMessage("Please select a ship type to transfer.");
      return;
    }
    if (transferQuantity < 1) {
      setMessage("Quantity must be at least 1.");
      return;
    }

    try {
      setIsLoading(true);
      const res = await fetch('/api/fleet/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from_planet_id: activePlanet,
          to_planet_id: destPlanet,
          ship_type: transferType,
          quantity: transferQuantity,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setMessage(data.message || "Transfer successful!");
        loadFleet();
        loadTransferData();
      } else {
        setMessage(`Transfer failed: ${data.message || data.detail}`);
      }
    } catch (error: any) {
      console.error('Error transferring ships:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Load cargo onto ships
  const loadCargo = async () => {
    if (!activePlanet) {
      setMessage("Please select a planet first.");
      return;
    }

    try {
      setIsLoading(true);
      const res = await fetch('/api/fleet/cargo/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          planet_id: activePlanet,
          ship_type: cargoShipType,
          resource_type: cargoResource,
          quantity: cargoQuantity,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setMessage(data.message || "Cargo loaded!");
        loadTransferData();
      } else {
        setMessage(`Load failed: ${data.message || data.detail}`);
      }
    } catch (error: any) {
      console.error('Error loading cargo:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Unload cargo from planet
  const unloadCargo = async () => {
    if (!activePlanet) {
      setMessage("Please select a planet first.");
      return;
    }

    try {
      setIsLoading(true);
      const res = await fetch('/api/fleet/cargo/unload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          planet_id: activePlanet,
          resource_type: cargoResource,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setMessage(data.message || "Cargo unloaded!");
        loadTransferData();
      } else {
        setMessage(`Unload failed: ${data.message || data.detail}`);
      }
    } catch (error: any) {
      console.error('Error unloading cargo:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Load transfer data (ships, cargo, destinations)
  const loadTransferData = async () => {
    if (!activePlanet) return;
    try {
      const res = await fetch(`/api/fleet/${activePlanet}/transfer`);
      if (res.ok) {
        const data = await res.json();
        setCargoData(data.cargo || {});
        // Update transferType options if first load
        if (transferPlanetsRef.current.length === 0) {
          transferPlanetsRef.current = data.destinations || [];
        }
      }
    } catch (error) {
      console.error('Error loading transfer data:', error);
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

        {/* Fleet List - aggregated */}
        {fleet.length > 0 && (
          <div className="fleet-list">
            <div className="section-header">
              <span className="section-title">&#9851; Fleet Summary</span>
            </div>
            {fleet.map((ship, idx) => (
              <div key={idx} className="fleet-item">
                <span className="fleet-icon">&#9851;</span>
                <strong>{ship.ship_type}</strong>
                <span className="fleet-count">&times;{ship.count}</span>
              </div>
            ))}
          </div>
        )}

        {/* Individual Ship Selection */}
        {individualShips.length > 0 && (
          <div className="fleet-list">
            <div className="section-header">
              <span className="section-title">&#9876; Select Ship to Move</span>
            </div>
            {individualShips.map((ship: any) => (
              <div
                key={ship.ship_id}
                className="fleet-item ship-selectable"
                onClick={() => setSelectedShipId(ship.ship_id)}
                style={{cursor: 'pointer', backgroundColor: selectedShipId === ship.ship_id ? '#e8f4f8' : 'transparent'}}
              >
                <span className="fleet-icon">&#9851;</span>
                <strong>{ship.ship_type}</strong>
                <span className="fleet-count">Slot {ship.docking_bay_slot}</span>
                {selectedShipId === ship.ship_id && <span style={{color: '#27ae60', marginLeft: '8px'}}>&#10003;</span>}
              </div>
            ))}
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

        {/* Transfer/Cargo Tabs */}
        <div className="fleet-actions">
          <div style={{ display: 'flex', gap: 4, marginBottom: 8 }}>
            <button
              onClick={() => setTransferTab('move')}
              style={{
                padding: '4px 12px',
                fontSize: 12,
                border: '1px solid #374151',
                borderRadius: 4,
                background: transferTab === 'move' ? '#3b82f6' : 'transparent',
                color: transferTab === 'move' ? '#fff' : '#9ca3af',
                cursor: 'pointer',
              }}
            >
              &#10147; Transfer Ships
            </button>
            <button
              onClick={() => setTransferTab('cargo')}
              style={{
                padding: '4px 12px',
                fontSize: 12,
                border: '1px solid #374151',
                borderRadius: 4,
                background: transferTab === 'cargo' ? '#3b82f6' : 'transparent',
                color: transferTab === 'cargo' ? '#fff' : '#9ca3af',
                cursor: 'pointer',
              }}
            >
              &#128305; Cargo Load/Unload
            </button>
          </div>

          {transferTab === 'move' && (
            <div style={{ marginBottom: 12 }}>
              {/* Ship type selector */}
              <div style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'center' }}>
                <label style={{ fontSize: 13 }}>Ship Type:</label>
                <select
                  value={transferType}
                  onChange={(e) => setTransferType(e.target.value)}
                  style={{ padding: '4px 8px', fontSize: 13 }}
                >
                  <option value="">Select ship type...</option>
                  {fleet.map((s, idx) => (
                    <option key={idx} value={s.ship_type}>
                      {s.ship_type} (available: {s.count})
                    </option>
                  ))}
                </select>
                <label style={{ fontSize: 13 }}>Qty:</label>
                <input
                  type="number"
                  min={1}
                  max={fleet.find(s => s.ship_type === transferType)?.count || 0}
                  value={transferQuantity}
                  onChange={(e) => setTransferQuantity(Number(e.target.value))}
                  style={{ width: 60, padding: '4px 8px', fontSize: 13 }}
                />
              </div>

              {/* Destination selector */}
              <div style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'center' }}>
                <label style={{ fontSize: 13 }}>Destination:</label>
                <select
                  value={destPlanet || ''}
                  onChange={(e) => setDestPlanet(e.target.value ? Number(e.target.value) : null)}
                  style={{ padding: '4px 8px', fontSize: 13 }}
                >
                  <option value="">Select destination...</option>
                  {allPlanets
                    .filter(p => p.id !== activePlanet)
                    .map(p => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                </select>
              </div>

              <button
                onClick={transferShips}
                disabled={!activePlanet || fleet.length === 0 || !destPlanet || !transferType || transferQuantity < 1}
                className="btn btn-primary"
                style={{ fontSize: 13 }}
              >
                &#10147; Transfer {transferQuantity} {transferType || 'Ship(s)'}
              </button>
            </div>
          )}

          {transferTab === 'cargo' && (
            <div style={{ marginBottom: 12 }}>
              {/* Cargo ship selector */}
              <div style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'center' }}>
                <label style={{ fontSize: 13 }}>Cargo Ship Type:</label>
                <select value={cargoShipType} onChange={(e) => setCargoShipType(e.target.value)} style={{ padding: '4px 8px', fontSize: 13 }}>
                  <option value="CargoShip">CargoShip (1000 cap)</option>
                </select>
              </div>

              {/* Resource selector */}
              <div style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'center' }}>
                <label style={{ fontSize: 13 }}>Resource:</label>
                <select value={cargoResource} onChange={(e) => setCargoResource(e.target.value)} style={{ padding: '4px 8px', fontSize: 13 }}>
                  <option value="food">&#127850; Food</option>
                  <option value="mineral">&#9874; Minerals</option>
                  <option value="energy">&#9889; Energy</option>
                  <option value="fuel">&#128172; Fuel</option>
                </select>
                <label style={{ fontSize: 13 }}>Amount:</label>
                <input
                  type="number"
                  min={1}
                  max={1000}
                  value={cargoQuantity}
                  onChange={(e) => setCargoQuantity(Number(e.target.value))}
                  style={{ width: 80, padding: '4px 8px', fontSize: 13 }}
                />
              </div>

              {/* Current cargo display */}
              {cargoData && Object.keys(cargoData).length > 0 && (
                <div style={{ marginBottom: 8, fontSize: 12, color: '#94a3b8' }}>
                  <strong>Current Cargo:</strong>{' '}
                  {Object.entries(cargoData).map(([shipType, res]) => (
                    <span key={shipType} style={{ marginRight: 12 }}>
                      {shipType}: {Object.entries(res as Record<string, number>).map(([res, amt]) => `${res}: ${amt}`).join(', ')}
                    </span>
                  ))}
                </div>
              )}

              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={loadCargo} className="btn btn-primary" style={{ fontSize: 13 }}>
                  &#9660; Load {cargoResource} ({cargoQuantity})
                </button>
                <button onClick={unloadCargo} className="btn btn-secondary" style={{ fontSize: 13 }}>
                  &#9650; Unload {cargoResource}
                </button>
              </div>
            </div>
          )}

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
        {(allPlanets.length > 0 || allPlanetsRef.current.length > 0) && (
          <div className="fleet-by-system">
            <h4>Fleet Distribution by System:</h4>
            {(allPlanetsRef.current.length > 0 ? allPlanetsRef.current : allPlanets).map((planet) => {
              const planetFleet = (planet.fleet || planet.resources?.fleet || []).reduce((sum: number, ship: any) => sum + ship.count, 0);
              if (planetFleet === 0 && !planet.fleet && !planet.resources?.fleet) return null;
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
