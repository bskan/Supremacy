import React, { useState, useEffect } from 'react';
// Mirror CLI Screen 7: Battle Simulation - Combat between planets

interface BattleSimulatorProps {
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

const BattleSimulator: React.FC<BattleSimulatorProps> = ({ onBack }) => {
  const [availableBattles, setAvailableBattles] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedBattle, setSelectedBattle] = useState<any | null>(null);
  const [battleResult, setBattleResult] = useState<string>("");
  const [battleData, setBattleData] = useState<any>(null);
  const [isResolving, setIsResolving] = useState(false);
  const [message, setMessage] = useState("Ready to simulate combat...");
  const [playerCredits, setPlayerCredits] = useState<number | null>(null);

  useEffect(() => {
    loadCredits();
  }, []);

  const loadCredits = async () => {
    try {
      const res = await fetch('/api/player/credits');
      if (res.ok) {
        const data = await res.json();
        setPlayerCredits(data.credits || 0);
      }
    } catch (error) {
      console.error('Error loading credits:', error);
    }
  };

  useEffect(() => {
    loadBattles();
  }, []);

  // Get potential battle pairs from owned planets (attacker vs neutral/enemy planets)
  const loadBattles = async () => {
    try {
      setIsLoading(true);
      const res = await fetch('/api/planets');
      if (!res.ok) throw new Error('Failed to get planets');

      const playersPlanets = await res.json();
      const allPlanets = await res.json(); // Full list with ownership info

      // Filter owned planets for potential attackers
      const ownedPlanets = allPlanets.filter((p: any) => p.owner_name === 'Player');

      if (ownedPlanets.length >= 1 && allPlanets.length > 1) {
        // Generate battles: each owned planet vs neutral/enemy planets
        const battles: any[] = [];
        const neutralPlanets = allPlanets.filter((p: any) => p.owner_name !== 'Player');

        if (neutralPlanets.length > 0) {
          // Create battle pairs for first few combos
          ownedPlanets.slice(0, 2).forEach((attacker: any) => {
            neutralPlanets.slice(0, 2).forEach((defender: any) => {
              battles.push({
                attacker_id: attacker.id,
                defender_id: defender.id,
                attacker_name: attacker.name || `Attacker ${attacker.id}`,
                defender_name: defender.name || `Defender ${defender.id}`,
              });
            });
          });
        }

        setAvailableBattles(battles);
      }

      setMessage(
        ownedPlanets.length > 0
          ? `You own ${ownedPlanets.length} planet${ownedPlanets.length !== 1 ? 's' : ''}. Select a battle to simulate.`
          : 'No planets owned yet. Purchase assets from the marketplace.'
      );
    } catch (error: any) {
      console.error('Error loading battles:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

 // Resolve single battle (calls API endpoint)
  const resolveBattle = async (attackerId: number, defenderId: number) => {
    try {
      setIsResolving(true);
      setBattleResult("Simulating combat...");
      setBattleData(null);

      const res = await fetch('/api/action/battle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          attacker_planet_id: attackerId,
          defender_planet_id: defenderId,
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setBattleResult(data.message || "Combat resolved successfully!");
        // Parse combat report into structured data
        const report = data.message || '';
        const lines = report.split('\n');
        const parsed: any = { attackerName: '', defenderName: '', attackerPower: 0, defenderPower: 0, attackerFleet: 0, defenderFleet: 0, outcome: '' };
        for (const line of lines) {
          if (line.startsWith('Attacker combat power:')) {
            const m = line.match(/combat power: (\d+)/);
            if (m) parsed.attackerPower = parseInt(m[1]);
          }
          if (line.startsWith('Defender combat power:')) {
            const m = line.match(/combat power: (\d+)/);
            if (m) parsed.defenderPower = parseInt(m[1]);
          }
          if (line.match(/fleet:\s*\d+/)) {
            const am = line.match(/fleet:\s*(\d+)/);
            if (am) { parsed.attackerFleet = parseInt(am[1]); parsed.defenderFleet = parsed.defenderFleet || 0; }
          }
          if (line.includes('Attacker wins') || line.includes('overwhelmed') || line.includes('stalemate') || line.includes('Superior')) {
            if (line.includes('stalemate')) parsed.outcome = 'Stalemate';
            else if (line.includes('overwhelmed')) parsed.outcome = 'Defender Victory';
            else if (line.includes('Superior')) parsed.outcome = 'Attacker Wins (Resources)';
            else parsed.outcome = 'Attacker Wins';
          }
        }
        setBattleData(parsed);
        setMessage(`Battle Result: ${parsed.outcome || 'Resolved'}`);
      } else {
        setBattleResult(data.detail || `Failed to resolve combat`);
        setMessage(`Battle Failed: ${data.detail}`);
      }
    } catch (error: any) {
      console.error('Error resolving battle:', error);
      setBattleResult(`Error: ${error.message}`);
      setMessage(error.message);
    } finally {
      setIsResolving(false);
    }
  };

  // Render main battles list view
  const renderBattlesList = () => (
    <div className="screen battle-screen">
      <button onClick={onBack} className="back-btn">&larr; Main Menu</button>

      <h2>&#127946; Battle Simulation</h2>

      {/* Status Message */}
      {/* Credits Display */}
      <div className="credits-display">
        &#8363; {formatNumber(playerCredits || 0)} Credits Available
      </div>

      <div className={`message-box ${isLoading ? 'loading' : ''}`}>
        <strong>Status:</strong> {message}
      </div>

      {/* Available Battles List - from owned planets */}
      <div className="battles-list">
        {availableBattles.length === 0 && !selectedBattle && (
          <div className="no-battles">No battles available. Own more planets to start battling.</div>
        )}

        {availableBattles.map((battle, idx) => (
          <div key={idx} className="battle-card" onClick={() => selectBattle(battle)} style={{cursor: 'pointer'}}>
            <h3>Battle #{battle.attacker_id || battle.defender_id ? idx + 1 : idx + 1}</h3>

            <div className="battle-vs">
              <PlanetPreview id={battle.attacker_id} name={battle.attacker_name || `Attacker ${battle.attacker_id}`} isAttacker />
              <span>&#8596;</span>
              <PlanetPreview id={battle.defender_id} name={battle.defender_name || `Defender ${battle.defender_id}`} isDefender />
            </div>

            <button onClick={(e) => { e.stopPropagation(); selectBattle(battle); }}>
              Simulate Battle
            </button>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="battle-actions">
        <button onClick={() => { setPlayerCredits((playerCredits || 0) + 1000); loadCredits(); }} className="btn btn-secondary">
          &#128640; Add $1,000 Credits (Debug)
        </button>
        <button onClick={onBack} className="btn btn-secondary">
          &#9654; Return to Main Menu
        </button>
      </div>

      {/* Instructions - Mirrors CLI */}
      <div className="battle-instructions">
        <h4>Battle Actions:</h4>
        <ul>
          <li>&#127946; Combat simulation between two planets</li>
          <li>&#9888; Select a battle pair to simulate combat</li>
          <li>&#128704; Refresh to see new battles</li>
        </ul>
      </div>
    </div>
  );

  // Render selected battle resolution view
  const renderBattleResolution = () => (
    <div className="screen battle-screen">
      <button onClick={onBack} className="back-btn">&larr; Battle List</button>

      {/* Credits Display */}
      <div className="credits-display">
        &#8363; {formatNumber(playerCredits || 0)} Credits Available
      </div>

      <h2>&#9889; Combat Resolution: Attacker vs Defender</h2>

      {/* Status Message */}
      <div className={`message-box ${isResolving ? 'loading' : ''}`}>
        <strong>Status:</strong> {battleResult || message}
      </div>

      {/* Battle Details - Mirror CLI resolve_combat output */}
      <div className="battle-details">
        <h3>Battle Information</h3>

        <div className="battle-stats">
          <div className="battle-side attacker">
            <span className="side-icon">&#128160;</span>
            <strong>Attacker</strong>
            <span>&#9730; Planet {selectedBattle?.attacker_id}</span>
          </div>

          <div className="battle-vs">&bull;</div>

          <div className="battle-side defender">
            <span className="side-icon">&#128161;</span>
            <strong>Defender</strong>
            <span>&#9730; Planet {selectedBattle?.defender_id}</span>
          </div>
        </div>

        {/* Combat Result */}
        {battleResult && (
          <div className="combat-result">
            <h4>&#128342; Combat Report:</h4>
            {battleData ? (
              <div>
                <div className="battle-side attacker" style={{padding: '8px', marginBottom: '4px', background: '#f0f0f0', borderRadius: '4px'}}>
                  <strong>{selectedBattle?.attacker_name}</strong> → Power: {battleData.attackerPower} (Fleet: {battleData.attackerFleet}, Mining: +, Pop: +)
                </div>
                <div className="battle-side defender" style={{padding: '8px', background: '#f0f0f0', borderRadius: '4px'}}>
                  <strong>{selectedBattle?.defender_name}</strong> → Power: {battleData.defenderPower} (Fleet: {battleData.defenderFleet}, Mining: +, Pop: +)
                </div>
                <div style={{marginTop: '8px', fontWeight: 'bold', color: battleData.outcome?.includes('Wins') || battleData.outcome?.includes('Victory') ? '#27ae60' : '#e74c3c'}}>
                  Result: {battleData.outcome || 'Resolved'}
                </div>
              </div>
            ) : (
              <pre>{battleResult}</pre>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="battle-actions">
          <button onClick={() => resolveBattle(selectedBattle.attacker_id, selectedBattle.defender_id)} disabled={isResolving} className="btn btn-primary">
            {isResolving ? 'Simulating...' : '&#9678; Simulate Battle'}
          </button>
          <button onClick={loadBattles} disabled={isLoading} className="btn btn-secondary">
            &#128704; Back to Battle List
          </button>
        </div>

        {/* Instructions */}
        <div className="battle-instructions">
          <h4>Combat Actions:</h4>
          <ul>
            <li>&#9678; Simulate battle between selected planets</li>
            <li>&#128704; Return to battle list for new battles</li>
          </ul>
        </div>
      </div>
    </div>
  );

  // Planet preview component for battle selection
  const PlanetPreview = ({ id, name, isAttacker }: any) => (
    <div className={`planet-preview ${isAttacker ? 'attacker' : 'defender'}`}>
      {isAttacker ? '&#128640;' : '&#128663;'}
      <span>{name}</span>
    </div>
  );

  const selectBattle = (battle: any) => {
    setSelectedBattle(battle);
    setBattleResult("");
  };

  return selectedBattle ? renderBattleResolution() : renderBattlesList();
};

export default BattleSimulator;
