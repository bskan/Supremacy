import React, { useState, useEffect } from 'react';
// Mirror CLI Screen 9: Planet Battle - Combat simulation between two planets

interface BattlesProps {
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

const Battles: React.FC<BattlesProps> = ({ onBack }) => {
  const [planetA, setPlanetA] = useState<any>(null);
  const [planetB, setPlanetB] = useState<any>(null);
  const [battleData, setBattleData] = useState<any>(null);
  const [isAttacking, setIsAttacking] = useState(false);
  const [attackMessage, setAttackMessage] = useState("");
  const [result, setResult] = useState<null | 'win' | 'lose'>();

  // Helper to format large numbers with commas
  const formatNumberHelper = (num: any): string => {
    if (num === null || num === undefined) return '0';
    const n = typeof num === 'string' ? parseFloat(num) : num;
    return Math.abs(n) >= 1000000 ? (n / 1000000).toFixed(2) + 'M'
      : Math.abs(n) >= 1000 ? (n / 1000).toFixed(1) + 'K'
      : n.toLocaleString();
  };

  // Simulate turn for battle calculation (mirror CLI simulate_turn logic)
  const calculateBattle = async () => {
    if (!planetA || !planetB) return;

    try {
      setIsAttacking(true);
      setAttackMessage("Calculating battle outcome...");
      setResult(null);

      // Get detailed planet state from API
      const resA = await fetch(`/api/planet/${planetA.planet_id}`);
      if (!resA.ok) throw new Error(`Failed to get planet ${planetA.planet_id} details`);
      const dataA = await resA.json();

      const resB = await fetch(`/api/planet/${planetB.planet_id}`);
      if (!resB.ok) throw new Error(`Failed to get planet ${planetB.planet_id} details`);
      const dataB = await resB.json();

      setPlanetA(dataA);
      setPlanetB(dataB);

      // Calculate battle outcome (simplified version of CLI logic)
      // Production per turn for both planets
      const infraA = {
        farming_stations: dataA.infrastructure.farming_stations || 0,
        mining_stations: dataA.infrastructure.mining_stations || 0,
        solar_satellites: dataA.infrastructure.solar_satellites || 0,
      };

      const infraB = {
        farming_stations: dataB.infrastructure.farming_stations || 0,
        mining_stations: dataB.infrastructure.mining_stations || 0,
        solar_satellites: dataB.infrastructure.solar_satellites || 0,
      };

      // Calculate combat power based on resources and fleet strength
      const shipsA = Array.isArray(dataA.resources?.fleet) ? dataA.resources.fleet.reduce((sum: number, ship: any) => sum + ship.count, 0) : 0;
      const shipsB = Array.isArray(dataB.resources?.fleet) ? dataB.resources.fleet.reduce((sum: number, ship: any) => sum + ship.count, 0) : 0;

      // Combat power based on fleet sizes and production capabilities
      const combatPowerA = shipsA * 10 + (infraA.mining_stations * 20) + (dataA.population || 100);
      const combatPowerB = shipsB * 10 + (infraB.mining_stations * 20) + (dataB.population || 100);

      // Battle outcome based on combat power ratio
      if (combatPowerA > combatPowerB * 1.5) {
        setResult('win');
        setAttackMessage(`Victory! Your forces overwhelm ${dataB.name} with ease.`);
      } else if (combatPowerA < combatPowerB * 0.6) {
        setResult('lose');
        setAttackMessage(`${dataA.name} is overwhelmed by the defenses of ${dataB.name}.`);
      } else {
        // Roughly equal - outcome depends on resource reserves
        const totalResourcesA = (dataA.resources?.food_level || 0) + (dataA.resources?.energy_level || 0) + (dataA.resources?.fuel_level || 0);
        const totalResourcesB = (dataB.resources?.food_level || 0) + (dataB.resources?.energy_level || 0) + (dataB.resources?.fuel_level || 0);

        if (totalResourcesA > totalResourcesB * 1.2) {
          setResult('win');
          setAttackMessage(`${dataA.name} prevails through superior resource reserves.`);
        } else if (totalResourcesA < totalResourcesB * 0.8) {
          setResult('lose');
          setAttackMessage(`${dataA.name}'s resources deplete against ${dataB.name}'s defenses.`);
        } else {
          // Settle with minimal damage
          setResult(null);
          setAttackMessage(`The battle ends in a stalemate - neither side gains the upper hand.`);
        }
      }

      setBattleData({
        planetA,
        planetB,
        combatPowerA,
        combatPowerB,
        attackMessage,
        result,
      });

    } catch (error: any) {
      console.error('Error calculating battle:', error);
      setAttackMessage(`Error calculating battle: ${error.message}`);
    } finally {
      setIsAttacking(false);
    }
  };

  // Simulate turn (resource update for this planet)
  const simulateTurn = async () => {
    if (!planetA) return;

    try {
      const res = await fetch('/api/turn/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ planet_id: planetA.planet_id }),
      });

      if (res.ok) {
        const data = await res.json();
        setAttackMessage(data.message || "Turn simulated successfully.");
        // Reload planet to show updated resources
        const planetRes = await fetch(`/api/planet/${planetA.planet_id}`);
        if (planetRes.ok) {
          setPlanetA(await planetRes.json());
        }
      } else {
        const data = await res.json();
        setAttackMessage(data.detail || "Failed to simulate turn.");
      }
    } catch (error: any) {
      console.error('Error simulating turn:', error);
      setAttackMessage(`Error: ${error.message}`);
    }
  };

  // Handle attacking another planet
  const handleAttack = async (targetPlanetId: number, targetName: string) => {
    try {
      setIsAttacking(true);
      const res = await fetch('/api/planet/battle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_planet_id: targetPlanetId }),
      });

      if (res.ok) {
        const data = await res.json();
        setAttackMessage(data.message || `Battle with ${targetName} completed.`);
        setResult(data.result as any);
      } else {
        const data = await res.json();
        setAttackMessage(data.detail || `Failed to attack ${targetName}.`);
      }
    } catch (error: any) {
      console.error('Error attacking:', error);
      setAttackMessage(`Error: ${error.message}`);
    } finally {
      setIsAttacking(false);
    }
  };

  if (!planetA || !planetB) return <div>Loading...</div>;

  return (
    <div className="screen battles-screen">
      {/* Back Button */}
      <button onClick={onBack} className="back-btn">&larr; Main Menu</button>

      {/* Header with Credits Display */}
      <div className="battle-header">
        <h2>&#10008; Planet Battle - Combat Simulation</h2>
      </div>

      {/* Status Message */}
      <div className={`message-box ${isAttacking ? 'loading' : ''}`}>
        <strong>Status:</strong> {attackMessage || "Ready to calculate battle"}
      </div>

      {/* Player's Planet (Left Panel) */}
      <div className="battle-panel player-panel">
        <h3>&#9790; Your Planet</h3>

        <div className="planet-info">
          <div className="info-row"><span>Name:</span><strong>{planetA.name}</strong></div>
          <div className="info-row"><span>System ID:</span><strong>{planetA.system_id}</strong></div>
          <div className="info-row"><span>Population:</span><strong>{formatNumberHelper(planetA.population)}</strong></div>
          <div className="info-row"><span>Morale:</span><strong>{planetA.morale || 5}/10</strong></div>
        </div>

        {/* Resources Section */}
        <div className="resource-section">
          <h4>&#9851; Fleet Composition</h4>
          {Array.isArray(planetA.resources?.fleet) && planetA.resources.fleet.length > 0 ? (
            <div className="fleet-list">
              {planetA.resources.fleet.map((ship: any, idx: number) => (
                <div key={idx} className="fleet-item">
                  <span>{ship.ship_type || 'Ship'}:</span>
                  <strong>&times;{ship.count}</strong>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-fleet">No fleet present</div>
          )}

          {/* Resource Levels */}
          <div className="resource-row">
            <span>&#127881; Food Level:</span>
            <strong>{Math.floor(planetA.resources?.food_level || planetA.food_level).toLocaleString()}</strong>
          </div>
          <div className="resource-row">
            <span>&#9889; Energy Level:</span>
            <strong>{Math.floor(planetA.resources?.energy_level || 0).toLocaleString()}</strong>
          </div>
          <div className="resource-row">
            <span>&#128657; Fuel Level:</span>
            <strong>{Math.floor(planetA.resources?.fuel_level || 0).toLocaleString()}</strong>
          </div>
          <div className="resource-row">
            <span>&#9730; Mineral Level:</span>
            <strong>{Math.floor(planetA.resources?.mineral || 0)}</strong>
          </div>
        </div>

        {/* Infrastructure Section */}
        <div className="infrastructure-section">
          <h4>&#128736; Infrastructure</h4>
          <div className="infrastructure-grid">
            <div className="infra-item">
              <span>Farming Stations:</span>
              <strong>{planetA.infrastructure?.farming_stations || 0}</strong>
            </div>
            <div className="infra-item">
              <span>Mining Stations:</span>
              <strong>{planetA.infrastructure?.mining_stations || 0}</strong>
            </div>
            <div className="infra-item">
              <span>Solar Satellites:</span>
              <strong>{planetA.infrastructure?.solar_satellites || 0}</strong>
            </div>
          </div>
        </div>

        {/* Combat Power */}
        {battleData && (
          <div className="combat-power">
            <h4>&#128151; Combat Power</h4>
            <span>{formatNumberHelper(battleData.combatPowerA)}</span>
          </div>
        )}
      </div>

      {/* VS Badge */}
      <div className="vs-badge">&larr;</div>

      {/* Enemy/Target Planet (Right Panel) */}
      <div className="battle-panel enemy-panel">
        <h3>&#129480; Enemy Planet</h3>

        <div className="planet-info">
          <div className="info-row"><span>Name:</span><strong>{planetB.name}</strong></div>
          <div className="info-row"><span>System ID:</span><strong>{planetB.system_id}</strong></div>
          <div className="info-row"><span>Owner:</span><strong>
            {planetB.owner_name === 'Player' ? '&#127891; Owned' :
             planetB.owner_name || 'Neutral'}
          </strong></div>
          <div className="info-row"><span>Population:</span><strong>{formatNumberHelper(planetB.population)}</strong></div>
          <div className="info-row"><span>Morale:</span><strong>{planetB.morale || 5}/10</strong></div>
        </div>

        {/* Resources Section */}
        <div className="resource-section">
          <h4>&#9851; Fleet Composition</h4>
          {Array.isArray(planetB.resources?.fleet) && planetB.resources.fleet.length > 0 ? (
            <div className="fleet-list">
              {planetB.resources.fleet.map((ship: any, idx: number) => (
                <div key={idx} className="fleet-item">
                  <span>{ship.ship_type || 'Ship'}:</span>
                  <strong>&times;{ship.count}</strong>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-fleet">No fleet present</div>
          )}

          {/* Resource Levels */}
          <div className="resource-row">
            <span>&#127881; Food Level:</span>
            <strong>{Math.floor(planetB.resources?.food_level || planetB.food_level).toLocaleString()}</strong>
          </div>
          <div className="resource-row">
            <span>&#9889; Energy Level:</span>
            <strong>{Math.floor(planetB.resources?.energy_level || 0).toLocaleString()}</strong>
          </div>
          <div className="resource-row">
            <span>&#128657; Fuel Level:</span>
            <strong>{Math.floor(planetB.resources?.fuel_level || 0).toLocaleString()}</strong>
          </div>
          <div className="resource-row">
            <span>&#9730; Mineral Level:</span>
            <strong>{Math.floor(planetB.resources?.mineral || 0)}</strong>
          </div>
        </div>

        {/* Infrastructure Section */}
        <div className="infrastructure-section">
          <h4>&#128736; Infrastructure</h4>
          <div className="infrastructure-grid">
            <div className="infra-item">
              <span>Farming Stations:</span>
              <strong>{planetB.infrastructure?.farming_stations || 0}</strong>
            </div>
            <div className="infra-item">
              <span>Mining Stations:</span>
              <strong>{planetB.infrastructure?.mining_stations || 0}</strong>
            </div>
            <div className="infra-item">
              <span>Solar Satellites:</span>
              <strong>{planetB.infrastructure?.solar_satellites || 0}</strong>
            </div>
          </div>
        </div>

        {/* Combat Power */}
        {battleData && (
          <div className="combat-power">
            <h4>&#128151; Combat Power</h4>
            <span>{formatNumberHelper(battleData.combatPowerB)}</span>
          </div>
        )}

        {/* Battle Result Display */}
        {result && (
          <div className={`battle-result ${result}`}>
            <h4>&#127901; Battle Result</h4>
            <p>{battleData.attackMessage}</p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="action-buttons">
        {result !== null && (
          <button onClick={calculateBattle} disabled={isAttacking} className="btn btn-secondary">
            &#8635; Reset Battle Simulation
          </button>
        )}

        <button onClick={() => handleAttack(planetB.planet_id, planetB.name)} disabled={isAttacking} className="btn btn-primary">
          &#9870; Attack Enemy Planet
        </button>

        <button onClick={onBack} className="btn btn-secondary">
          &#9654; Return to Main Menu
        </button>
      </div>

      {/* Instructions - Mirrors CLI */}
      <div className="battle-instructions">
        <h4>Battle Actions:</h4>
        <ul>
          <li>&#8635; Reset battle simulation to recalculate outcome</li>
          <li>&#9870; Initiate attack on enemy planet (if available)</li>
          <li>&#9654; Return to main menu anytime</li>
        </ul>
      </div>
    </div>
  );
};

export default Battles;
