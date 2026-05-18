import React, { useState, useEffect } from 'react';
// Mirror CLI Screen 11: Debug Menu - Manual level setting and diagnostics

interface DebugPanelProps {
  onBack: () => void;
}

// Helper to format large numbers with commas
const formatNumber = (num: any): string => {
  if (num === null || num === undefined) return '0';
  const n = typeof num === 'string' ? parseFloat(num) : num;
  return Math.abs(n) >= 1000000 ? (n / 1000000).toFixed(2) + 'M'
    : Math.abs(n) >= 1000 ? (n / 1000).toFixed(1) + 'K'
    : n.toLocaleString();
};

const DebugPanel: React.FC<DebugPanelProps> = ({ onBack }) => {
  const [playerPlanets, setPlayerPlanets] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState("Loading owned planets...");
  const [playerCredits, setPlayerCredits] = useState<number | null>(null);
  const [productionData, setProductionData] = useState<Record<number, any>>({});
  const [consumptionData, setConsumptionData] = useState<Record<number, any>>({});
  const [selectedPlanet, setSelectedPlanet] = useState<any>(null);

  useEffect(() => {
    console.log('[DebugPanel] Component mounted, initial state:', { isLoading, playerPlanets: playerPlanets.length, message });
    loadDebugData();
  }, []);

  // Load player credits
  const loadCredits = async () => {
    try {
      const res = await fetch('/api/player/credits');
      if (res.ok) {
        const data = await res.json();
        console.log('[DebugPanel] setPlayerCredits:', data.credits);
        setPlayerCredits(data.credits || 0);
      }
    } catch (error) {
      console.error('Error loading credits:', error);
    }
  };

  useEffect(() => {
    loadCredits();
  }, []);

  // Load owned planets with full database content (mirrors CLI debug menu)
  const loadDebugData = async () => {
    console.log('Testing');
    try {
      setIsLoading(true);
      const res = await fetch('/api/debug/player-planets');
      if (res.ok) {
        const data = await res.json();
        console.log('[DebugPanel] setPlayerPlanets:', data, 'length:', data.length);
        setPlayerPlanets(data);

        // Calculate production/consumption stats per planet
        const newProductionData: Record<number, any> = {};
        const newConsumptionData: Record<number, any> = {};

        for (const planet of data) {
          const fleet = planet.fleet || planet.resources?.fleet || [];
          if (Array.isArray(fleet)) {
            const infra = {
              farming_stations: planet.infrastructure?.farming_stations || 0,
              mining_stations: planet.infrastructure?.mining_stations || 0,
              solar_satellites: planet.infrastructure?.solar_satellites || 0,
            };

            const pop = planet.population || 100;
            const ships = fleet.length;

            // Production per turn (from CLI logic)
            const food_produced = infra.farming_stations * 15.0;
            const minerals_produced = infra.mining_stations * 8.0;
            const energy_produced = infra.solar_satellites * 12.0;
            const fuel_from_minerals = minerals_produced * 0.5;
            const fuel_from_food = food_produced * 0.2;
            const total_fuel_produced = fuel_from_minerals + fuel_from_food;

            // Consumption per turn (from CLI logic)
            const food_consumed = pop * 0.5;
            const energy_consumed = pop * 0.3 + ships * 2.0;
            const minerals_consumed = ships * 1.0;
            const fuel_consumed = ships * 0.8;

            newProductionData[planet.planet_id] = { food_produced, minerals_produced, energy_produced, total_fuel_produced };
            newConsumptionData[planet.planet_id] = { food_consumed, energy_consumed, minerals_consumed, fuel_consumed };
          }
        }

        console.log('[DebugPanel] setProductionData keys:', Object.keys(newProductionData));
        console.log('[DebugPanel] setConsumptionData keys:', Object.keys(newConsumptionData));
        setProductionData(newProductionData);
        setConsumptionData(newConsumptionData);
        console.log('[DebugPanel] setMessage: Loaded', data.length, 'planets');
        setMessage(`Loaded ${data.length} owned planet${data.length !== 1 ? 's' : ''}.`);
      }
    } catch (error: any) {
      console.error('Error loading debug data:', error);
      console.log('[DebugPanel] setMessage: Error:', error.message);
      setMessage(`Error: ${error.message}`);
    } finally {
      console.log('[DebugPanel] setIsLoading(false), final state:', { playerPlanets: playerPlanets.length, isLoading: false });
      setIsLoading(false);
    }
  };

  // Adjust resource level for a planet (mirrors CLI adjustment functions)
  const adjustLevel = async (planetId: number, type: string, newValue: number) => {
    try {
      setIsLoading(true);

      const payload = {
        planet_id: planetId,
        resource_type: type,
        new_value: newValue,
      };

      const res = await fetch('/api/debug/adjust-level', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (res.ok) {
        console.log('[DebugPanel] setMessage:', data.message);
        setMessage(data.message);
        loadDebugData(); // Refresh planet list
      } else {
        console.log('[DebugPanel] setMessage: Failed to adjust', type, '-', data.detail);
        setMessage(data.detail || `Failed to adjust ${type}`);
      }
    } catch (error: any) {
      console.error('Error adjusting level:', error);
      console.log('[DebugPanel] setMessage: Adjust error:', error.message);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Increment resource level (used by quick buttons)
  const incrementLevel = async (planetId: number, type: string) => {
    try {
      const currentLevels = playerPlanets.find(p => p.planet_id === planetId)?.resources || {};

      // Get current value from database if available
      let currentValue = 0;
      for (const p of playerPlanets) {
        if (p.planet_id === planetId) {
          const levelName = type === 'population' ? 'population' : `${type.split('_')[1]}`;
          currentValue = p.resources?.[levelName] || p[type] || 0;
          break;
        }
      }

      const incrementValues: Record<string, number> = {
        'food_level': 1000,
        'energy_level': 1000,
        'fuel_level': 1000,
        'population': 100,
      };

      const newValue = currentValue + (incrementValues[type] || 1000);
      await adjustLevel(planetId, type, newValue);
    } catch (error: any) {
      console.error('Error incrementing:', error);
      console.log('[DebugPanel] setMessage: Increment error:', error.message);
      setMessage(`Error: ${error.message}`);
    }
  };

  // Increment level for all button types (population and resources)
  const incrementAllLevels = async (planetId: number, resourceType: string) => {
    try {
      if (!resourceType || resourceType === 'population') {
        await incrementLevel(planetId, resourceType);
        return;
      }

      // Map button type names to actual resource types
      const typeMap: Record<string, string> = {
        'food': 'food_level',
        'energy': 'energy_level',
        'fuel': 'fuel_level',
      };

      await incrementLevel(planetId, typeMap[resourceType] || resourceType);
    } catch (error: any) {
      console.error('Error incrementing all levels:', error);
      console.log('[DebugPanel] setMessage: IncrementAllLevels error:', error.message);
      setMessage(`Error: ${error.message}`);
    }
  };

  // Add credits (for testing)
  const addCredits = async (amount: number) => {
    try {
      setIsLoading(true);
      const res = await fetch('/api/credits/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credits_to_add: amount }),
      });

      if (res.ok) {
        console.log('[DebugPanel] setMessage: Added', amount, 'credits');
        setMessage(`Added $${amount.toLocaleString()} to Player credits.`);
        loadDebugData(); // Refresh planets to show updated credits context
      } else {
        console.log('[DebugPanel] setMessage: Failed to add credits');
        setMessage('Failed to add credits.');
      }
    } catch (error: any) {
      console.error('Error adding credits:', error);
      console.log('[DebugPanel] setMessage: Add credits error:', error.message);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // List all planets with current state
  const listAllPlanets = () => {
    setPlayerPlanets([...playerPlanets]); // Reload current state
    console.log('[DebugPanel] setMessage: listAllPlanets');
    setMessage("Showing all owned planets with current resource state.");
  };

  // Show detailed level adjustment or render main debug menu
  const renderPlanetLevelAdjustment = () => {
    if (!selectedPlanet) return null;

    return (
      <div className="screen debug-screen">
        <button onClick={() => setSelectedPlanet(null)} className="back-btn">&larr; Debug Menu</button>

        <h2>&#128640; Adjust: {selectedPlanet.name}</h2>

        {/* Status Message */}
        <div className={`message-box ${isLoading ? 'loading' : ''}`}>
          <strong>Status:</strong> Ready to adjust levels
        </div>

        {/* Planet Info */}
        <div className="planet-debug-info">
          <h3>Planet Information</h3>
          <div className="info-row"><span>ID:</span><strong>{selectedPlanet.planet_id}</strong></div>
          <div className="info-row"><span>Name:</span><strong>{selectedPlanet.name}</strong></div>

          {/* Resource Levels */}
          {['food_level', 'energy_level', 'fuel_level'].map((type) => (
            <div key={type} className={`info-row ${type}`}>
              <span>{type.split('_').map(c => c.charAt(0).toUpperCase() + c.slice(1))}</span>
              <strong>{Math.floor(selectedPlanet.resources[type] || 0).toLocaleString()}</strong>
            </div>
          ))}

          {/* Adjustment Controls */}
          <div className="adjustment-controls">
            {['food_level', 'energy_level', 'fuel_level'].map((type) => (
              <React.Fragment key={type}>
                <button onClick={() => adjustLevel(selectedPlanet.planet_id, type, -1000)} className="btn btn-secondary">
                  &#9664; &mdash;{1000} {type.split('_').join(' ')}
                </button>
                <button onClick={() => adjustLevel(selectedPlanet.planet_id, type, 1000)} className="btn btn-primary">
                  +{1000} {type.split('_').join(' ')} &#9654;
                </button>
              </React.Fragment>
            ))}
          </div>

          {/* Actions */}
          <div className="debug-actions">
            <button onClick={() => setSelectedPlanet(null)} disabled={isLoading} className="btn btn-secondary">
              &#128659; Cancel Adjustment
            </button>
            <button onClick={loadDebugData} disabled={isLoading} className="btn btn-secondary">
              &#128704; Back to Debug Menu
            </button>
          </div>

          {/* Instructions - Mirrors CLI */}
          <div className="adjustment-instructions">
            <h4>Adjustment Options:</h4>
            <ul>
              <li>&#9654; Increase food, energy, or fuel by +1000</li>
              <li>&#9664; Decrease by -1000</li>
              <li>&#128704; Cancel and return to debug menu</li>
            </ul>
          </div>
        </div>
      </div>
    );
  };

  // Show single planet detailed view (used by click handlers)
  const showPlanetDetails = async (planet: any) => {
    try {
      await fetch(`/api/planet/${planet.planet_id}`); // Load full planet data
      console.log('[DebugPanel] setSelectedPlanet:', planet.name);
      setSelectedPlanet(planet);
      console.log('[DebugPanel] setMessage: Selected', planet.name);
      setMessage(`Selected: ${planet.name}. Ready for adjustments.`);
    } catch (error: any) {
      console.error('Error:', error);
      console.log('[DebugPanel] setMessage: showPlanetDetails error:', error.message);
      setMessage(`Error loading planet: ${error.message}`);
    }
  };

  // Render main debug menu view (mirrors CLI handle_debug_menu output)
  console.log('[DebugPanel] Render - state:', { selectedPlanet: !!selectedPlanet, playerPlanets: playerPlanets.length, isLoading, message, productionKeys: Object.keys(productionData).length });
  const renderDebugMenu = () => (
    <div className="screen debug-screen">
      {/* Credits Display */}
      <div className="credits-display">
        &#8363; {formatNumber(playerCredits || 0)} Credits Available
      </div>

      <button onClick={onBack} className="back-btn">&larr; Main Menu</button>

      <h2>&#128269; Debug Menu - Manual Level Setting</h2>

      {/* Status Message */}
      <div className={`message-box ${isLoading ? 'loading' : ''}`}>
        <strong>Status:</strong> {message || (playerPlanets.length === 0 && !isLoading ? "Error: No owned planets loaded. Check API connection." : message)}
      </div>

      {/* Owned Planets List */}
      <div className="owned-planets-section">
        <h3>&#128206; Owned Planets</h3>

        {playerPlanets.length === 0 && !isLoading && (
          <div className="no-data">No owned planets found.</div>
        )}

        {playerPlanets.map((planet, idx) => (
          <div key={idx} className="planet-debug-card" onClick={() => showPlanetDetails(planet)} style={{cursor: 'pointer'}}>
            <h4>{planet.name}</h4>
            <span className="planet-tag">Planet ID: {planet.planet_id}</span>
            <span className={`owner-badge ${planet.owner_name === 'Player' ? 'owned' : 'neutral'}`}>
              {planet.owner_name || 'Neutral'}
            </span>

            {/* Resource Levels Display */}
            <div className="debug-resource-levels">
              <span className="level-item"><strong>Food:</strong>{Math.floor(planet.resources?.food_level || planet.food_level)}</span>
              <span className="level-item"><strong>Energy:</strong>{Math.floor(planet.resources?.energy_level || planet.energy_level)}</span>
              <span className="level-item"><strong>Fuel:</strong>{Math.floor(planet.resources?.fuel_level || planet.fuel_level)}</span>
              <span className="level-item"><strong>Minerals:</strong>{Math.floor(planet.resources?.mineral || 0)}</span>
              <span className="level-item"><strong>Population:</strong>{formatNumber(planet.population)}</span>
            </div>

            {/* Production/Consumption Stats */}
            {productionData[planet.planet_id] && consumptionData[planet.planet_id] && (
              <div className="production-breakdown">
                <span><strong>Food:</strong> +{formatNumber(productionData[planet.planet_id].food_produced)} / -{formatNumber(consumptionData[planet.planet_id].food_consumed)}</span>
                <span><strong>Energy:</strong> +{formatNumber(productionData[planet.planet_id].energy_produced)} / -{formatNumber(consumptionData[planet.planet_id].energy_consumed)}</span>
                <span><strong>Minerals:</strong> +{formatNumber(productionData[planet.planet_id].minerals_produced)} / -{formatNumber(consumptionData[planet.planet_id].minerals_consumed)}</span>
              </div>
            )}

            {/* Adjust Buttons */}
            <div className="debug-actions-mini">
              <button onClick={(e) => { e.stopPropagation(); incrementAllLevels(planet.planet_id, 'food'); }}>
                &#9650; Food +1000
              </button>
              <button onClick={(e) => { e.stopPropagation(); incrementAllLevels(planet.planet_id, 'energy'); }}>
                &#9650; Energy +1000
              </button>
              <button onClick={(e) => { e.stopPropagation(); incrementAllLevels(planet.planet_id, 'fuel'); }}>
                &#9650; Fuel +1000
              </button>
              <button onClick={(e) => { e.stopPropagation(); incrementLevel(planet.planet_id, 'population'); }}>
                &#9650; Pop +100
              </button>
            </div>
          </div>
        ))}

        {/* Actions */}
        <div className="debug-actions">
          <button onClick={listAllPlanets} disabled={isLoading} className="btn btn-secondary">
            &#128704; List All Planets with State
          </button>
          <button onClick={() => addCredits(10000)} disabled={isLoading} className="btn btn-secondary">
            &#128640; Add $10,000 Credits (Testing)
          </button>
          <button onClick={onBack} className="btn btn-secondary">
            &#9654; Return to Main Menu
          </button>
        </div>

        {/* Instructions - Mirrors CLI */}
        <div className="debug-instructions">
          <h4>Debug Actions:</h4>
          <ul>
            <li>&#128640; Manually adjust resource levels for any planet</li>
            <li>&#9650; Quick buttons to add +1000 to food/energy/fuel</li>
            <li>&#128704; Refresh to reload owned planets</li>
          </ul>
        </div>

        {/* Production Overview */}
        {Object.keys(productionData).length > 0 && (
          <div className="production-overview">
            <h4>Planet Production Overview:</h4>
            {playerPlanets.map((planet) => {
              const p = productionData[planet.planet_id];
              const c = consumptionData[planet.planet_id];
              if (!p || !c) return null;
              return (
                <div key={planet.planet_id} className="planet-prod-row">
                  <strong>{planet.name}</strong>:
                  Food +{formatNumber(p.food_produced)}/-{formatNumber(c.food_consumed)} |
                  Energy +{formatNumber(p.energy_produced)}/-{formatNumber(c.energy_consumed)} |
                  Minerals +{formatNumber(p.minerals_produced)}/-{formatNumber(c.minerals_consumed)}
                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );

  // Return the actual component JSX
  return selectedPlanet ? renderPlanetLevelAdjustment() : renderDebugMenu();
};

export default DebugPanel;
