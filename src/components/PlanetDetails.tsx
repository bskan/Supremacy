import React, { useState, useEffect } from 'react';
// Mirror CLI Screen 3: Planet Details View - Full resource breakdown and infrastructure

interface PlanetDetailsProps {
  planetId: number;
  onBack: () => void;
  onBattle?: (a: number, b: number) => void;
  systemList?: () => void;
}

// Helper to format large numbers with commas
const formatNumber = (num: any): string => {
  if (num === null || num === undefined) return '0';
  const n = typeof num === 'string' ? parseFloat(num) : num;
  return Math.abs(n) >= 1000000 ? (n / 1000000).toFixed(2) + 'M'
    : Math.abs(n) >= 1000 ? (n / 1000).toFixed(1) + 'K'
    : n.toLocaleString();
};

const PlanetDetails: React.FC<PlanetDetailsProps> = ({ planetId, onBack, onBattle, systemList }) => {
  // State matching CLI get_planet_state / calculate_resource_flow
  const [planet, setPlanet] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [productionData, setProductionData] = useState<any>(null);
  const [consumptionData, setConsumptionData] = useState<any>(null);
  const [message, setMessage] = useState("Loading planet data...");

  // Calculate production/consumption per turn (mirror CLI display_planet_details logic)
  useEffect(() => {
    const calculateStats = async () => {
      try {
        // Get detailed planet state from API
        const res = await fetch(`/api/planet/${planetId}`);
        if (!res.ok) throw new Error(`Failed to get planet ${planetId} details`);
        const data = await res.json();

        setPlanet(data);

        // Calculate production/consumption per turn (from CLI logic)
        const infra = {
          farming_stations: data.infrastructure.farming_stations || 0,
          mining_stations: data.infrastructure.mining_stations || 0,
          solar_satellites: data.infrastructure.solar_satellites || 0,
        };

        const ships = Array.isArray(data.resources?.fleet) ? data.resources.fleet.length : 1;

        // Production per turn (from CLI simulate_turn logic)
        const food_produced = infra.farming_stations * 15.0;
        const minerals_produced = infra.mining_stations * 8.0;
        const energy_produced = infra.solar_satellites * 12.0;
        const fuel_from_minerals = minerals_produced * 0.5;
        const fuel_from_food = food_produced * 0.2;
        const total_fuel_produced = fuel_from_minerals + fuel_from_food;

        // Consumption per turn (from CLI simulate_turn logic)
        const pop = data.population || 100;
        const food_consumed = pop * 0.5;
        const energy_consumed = pop * 0.3 + ships * 2.0;
        const minerals_consumed = ships * 1.0;
        const fuel_consumed = ships * 0.8;

        setProductionData({ food_produced, minerals_produced, energy_produced, total_fuel_produced });
        setConsumptionData({ food_consumed, energy_consumed, minerals_consumed, fuel_consumed });

        setMessage(
          `Population: ${pop.toLocaleString()} | ` +
          `Food: ${food_produced.toFixed(1)}/${food_consumed.toFixed(1)} | ` +
          `Energy: ${energy_produced.toFixed(1)}/${energy_consumed.toFixed(1)} | ` +
          `Minerals: ${minerals_produced.toFixed(1)}/${minerals_consumed.toFixed(1)} | ` +
          `Fuel: ${total_fuel_produced.toFixed(1)}/${fuel_consumed.toFixed(1)}`
        );

      } catch (error: any) {
        console.error('Error loading planet:', error);
        setMessage(`Error: ${error.message || 'Unknown error'}`);
      } finally {
        setIsLoading(false);
      }
    };

    calculateStats();
  }, [planetId]);

  if (!planet) return <div>Loading...</div>;

  const resourceKeys = ['food', 'energy', 'mineral', 'fuel', 'taxable_income'];
  const isOwned = planet.owner_name === 'Player';

  return (
    <div className="screen planets-screen">
      {/* Back Button */}
      <button onClick={onBack} className="back-btn">&larr; Main Menu</button>

      {/* Header with Credits Display */}
      <div className="planet-header">
        <h2>{planet.name}</h2>
        <div className="planet-meta-row">
          <span className="status-badge">{isOwned ? 'OWNED' : 'NEUTRAL/ENEMY'}</span>
          <span className="system-name">System ID: {planet.system_id}</span>
          <span className="credits-badge">&#8363; {formatNumber(planet.resources?.taxable_income || 0)}/turn</span>
        </div>
      </div>

      {/* Status Message */}
      <div className={`message-box ${isLoading ? 'loading' : ''}`}>
        <strong>Status:</strong> {message}
      </div>

      {/* Planet Info Grid - Mirror CLI display_planet_details output */}
      <div className="info-grid">
        <div className="info-section">
          <h3>&#128515; Ownership &amp; Economy</h3>
          <div className="info-row"><span>Owner:</span><strong>{planet.owner_name}</strong></div>
          <div className="info-row"><span>Population:</span><strong>{planet.population.toLocaleString()}</strong></div>
          <div className="info-row"><span>Morale:</span><strong>{planet.morale || 5}/10</strong></div>
          <div className="info-row"><span>Tax Rate:</span><strong>{(planet.tax_rate * 100).toFixed(1)}%</strong></div>
        </div>

        {/* Resources Section - Mirror CLI resource levels */}
        <div className="info-section">
          <h3>&#128176; Resource Levels</h3>
          {resourceKeys.map((key) => (
            <div key={key} className="info-row">
              <span>{key.charAt(0).toUpperCase() + key.slice(1)} Level:</span>
              <strong>{Math.floor(planet.resources[key] || 0).toLocaleString()}</strong>
            </div>
          ))}
        </div>

        {/* Infrastructure - Mirror CLI infrastructure display */}
        <div className="info-section">
          <h3>&#128736; Infrastructure</h3>
          <div className="infrastructure-grid">
            <div className="infra-card">
              <span className="infra-icon">&#127950;</span>
              <span className="infra-label">Farming Stations</span>
              <strong>{planet.infrastructure.farming_stations || 0}</strong>
            </div>
            <div className="infra-card">
              <span className="infra-icon">&#128722;</span>
              <span className="infra-label">Mining Stations</span>
              <strong>{planet.infrastructure.mining_stations || 0}</strong>
            </div>
            <div className="infra-card">
              <span className="infra-icon">&#9650;</span>
              <span className="infra-label">Solar Satellites</span>
              <strong>{planet.infrastructure.solar_satellites || 0}</strong>
            </div>
          </div>
        </div>

        {/* Fleet Section - Mirror CLI docking bay fleet view */}
        {Array.isArray(planet.resources?.fleet) && (
          <div className="info-section">
            <h3>&#128663; Fleet Inventory</h3>
            <div className="fleet-grid">
              {planet.resources.fleet.map((ship: any, idx: number) => (
                <div key={idx} className="fleet-card">
                  <span className="fleet-icon">&#9851;</span>
                  <strong>{ship.ship_type || 'Ship'}</strong>
                  <span className="fleet-count">&times;{ship.count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Production/Consumption Breakdown - Mirror CLI detailed stats */}
        <div className="info-section">
          <h3>&#128640; Production &amp; Consumption (Per Turn)</h3>

          {productionData && consumptionData && (
            <>
              <div className="stat-row">
                <span className="stat-label">Food:</span>
                <span className={`stat-value ${productionData.food_produced >= productionData.food_consumed ? 'positive' : 'negative'}`}>
                  +{productionData.food_produced.toFixed(1)} / -{productionData.food_consumed.toFixed(1)}
                </span>
              </div>

              <div className="stat-row">
                <span className="stat-label">Energy:</span>
                <span className={`stat-value ${productionData.energy_produced >= productionData.energy_consumed ? 'positive' : 'negative'}`}>
                  +{productionData.energy_produced.toFixed(1)} / -{productionData.energy_consumed.toFixed(1)}
                </span>
              </div>

              <div className="stat-row">
                <span className="stat-label">Minerals:</span>
                <span className={`stat-value ${productionData.minerals_produced >= productionData.minerals_consumed ? 'positive' : 'negative'}`}>
                  +{productionData.minerals_produced.toFixed(1)} / -{productionData.minerals_consumed.toFixed(1)}
                </span>
              </div>

              <div className="stat-row">
                <span className="stat-label">Fuel:</span>
                <span className={`stat-value ${productionData.total_fuel_produced >= productionData.fuel_consumed ? 'positive' : 'negative'}`}>
                  +{productionData.total_fuel_produced.toFixed(1)} / -{productionData.fuel_consumed.toFixed(1)}
                </span>
              </div>

              {/* Net Flow Summary */}
              <div className="net-flow">
                <span className="net-label">Net Change:</span>
                <span className={`net-value ${productionData.food_produced + productionData.minerals_produced >= 0 ? 'positive' : 'negative'}`}>
                  {Math.sign(productionData.food_produced + productionData.minerals_produced) > 0
                    ? '+'
                    : ''}{(productionData.food_produced + productionData.minerals_produced).toFixed(1)} units
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Action Buttons - Mirror CLI action options */}
      <div className="action-buttons">
        {isOwned && (
          <>
            <button onClick={onBattle} className="btn btn-secondary">
              &#127881; Initiate Battle with Another Planet
            </button>
            <button onClick={systemList} className="btn btn-secondary">
              &#128083; View All Systems
            </button>
          </>
        )}

        <button onClick={() => { /* TODO: Simulate turn for this planet */ }} className="btn btn-secondary">
          &#9754; Simulate Turn (Resource Update)
        </button>
      </div>

    </div>
  );
};

export default PlanetDetails;
