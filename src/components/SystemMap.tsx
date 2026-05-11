import React, { useState, useEffect } from 'react';
// Mirror CLI Screen 10: System List - Browse all systems and planets

interface SystemMapProps {
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

const SystemMap: React.FC<SystemMapProps> = ({ onBack }) => {
  const [systems, setSystems] = useState<any[]>([]);
  const [allPlanets, setAllPlanets] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState("Loading system list...");
  const [playerCredits, setPlayerCredits] = useState<number | null>(null);

  useEffect(() => {
    loadSystems();
  }, []);

  // Load player credits for display
  useEffect(() => {
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

    loadPlayerCredits();
  }, []);

  const loadSystems = async () => {
    try {
      setIsLoading(true);
      const res = await fetch('/api/systems');
      if (res.ok) {
        const data = await res.json();
        setSystems(data);
      }

      // Also load all owned planets
      const planetsRes = await fetch('/api/planets');
      if (planetsRes.ok) {
        setAllPlanets(await planetsRes.json());
      }

      setMessage(
        `Found ${systems.length} system${systems.length !== 1 ? 's' : ''}. ` +
        `${allPlanets.length} owned planet${allPlanets.length !== 1 ? 's' : ''}.`
      );
    } catch (error: any) {
      console.error('Error loading systems:', error);
      setMessage(`Error loading systems: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Render system list view
  const renderSystemListView = () => (
    <div className="screen system-map-screen">
      <button onClick={onBack} className="back-btn">&larr; Main Menu</button>

      <h2>&#127938; System List - Browse All Systems and Planets</h2>

      {/* Credits Display */}
      <div className="credits-display">
        &#8363; {formatNumber(playerCredits || 0)} Credits Available
      </div>

      <div className={`message-box ${isLoading ? 'loading' : ''}`}>
        <strong>Status:</strong> {message}
      </div>

      {/* System Grid */}
      <div className="systems-grid">
        {isLoading && (
          <div className="loading">Loading systems...</div>
        )}

        {!isLoading && systems.length === 0 && (
          <div className="empty-list">No systems discovered yet. Explore planets first.</div>
        )}

        {systems.map((system) => (
          <div key={system.system_id} className="system-card" onClick={() => showSystemDetails(system)} style={{cursor: 'pointer'}}>
            <h3>{system.name}</h3>
            <span className="planet-count">
              &#127942; {formatNumber(system.planets?.length || 0)} planet{system.planets?.length !== 1 ? 's' : ''}
            </span>

            {/* Show first planet preview with ownership status and production stats */}
            {system.planets?.[0] && (
              <div className="preview-planet">
                <strong>{formatNumber(system.planets[0].name)}</strong><br/>
                <span className={`owner-badge ${system.planets[0].owner_name === 'Player' ? 'owned' : 'neutral'}`} title={`${system.planets[0].owner_name || system.planets[0].owner || 'Neutral'} owned`}>
                  {system.planets[0].owner_name || 'Neutral'}
                </span>

                {/* Production/Consumption Stats */}
                {system.planets[0].resources?.fleet && (
                  <div className="preview-stats">
                    &#9851; Fleet: {formatNumber(system.planets[0].resources.fleet.reduce((sum: number, ship: any) => sum + ship.count, 0))} ships |
                    Pop: {formatNumber(system.planets[0].population || 0)}
                  </div>
                )}

                {/* Infrastructure Stats */}
                {system.planets[0].infrastructure && (
                  <div className="infra-preview">
                    Farm: {system.planets[0].infrastructure.farming_stations || 0} |
                    Mine: {system.planets[0].infrastructure.mining_stations || 0} |
                    Solar: {system.planets[0].infrastructure.solar_satellites || 0}
                  </div>
                )}
              </div>
            )}

            <button onClick={(e) => { e.stopPropagation(); showSystemDetails(system); }}>
              View Details
            </button>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="system-actions">
        <button onClick={loadSystems} disabled={isLoading} className="btn btn-secondary">
          &#128704; Refresh System List
        </button>
        <button onClick={onBack} className="btn btn-secondary">
          &#9654; Return to Main Menu
        </button>
      </div>

      {/* Instructions - Mirrors CLI */}
      <div className="system-instructions">
        <h4>System List Actions:</h4>
        <ul>
          <li>&#127938; Browse all discovered systems and planets</li>
          <li>&#9730; Click on a system to view its planets</li>
          <li>&#128704; Refresh system list to see new discoveries</li>
        </ul>
      </div>
    </div>
  );

  // Render single system details view (expanded)
  const renderSystemDetailsView = () => (
    <div className="screen system-map-screen">
      <button onClick={onBack} className="back-btn">&larr; System List</button>

      <h2>&#127946; Details: {selectedSystem?.name}</h2>

      <div className={`message-box ${isLoading ? 'loading' : ''}`}>
        <strong>Status:</strong> Loading system details...
      </div>

      {/* Credits Display */}
      <div className="credits-display">
        &#8363; {formatNumber(playerCredits || 0)} Credits Available
      </div>

      {/* Planets in System */}
      <div className="planets-grid">
        {selectedSystem?.planets?.map((planet: any, idx: number) => (
          <div key={idx} className="system-planet-card" onClick={() => goToPlanetDetails(planet)} style={{cursor: 'pointer'}}>
            <h3>{planet.name}</h3>
            <span className={`owner-badge ${planet.owner_name === 'Player' ? 'owned' : 'neutral'}`} title={`${planet.owner_name || planet.owner || 'Neutral'} owned`}>
              {planet.owner_name || planet.owner || 'Neutral'}
            </span>

            {/* Fleet and Infrastructure Preview */}
            {planet.resources?.fleet && (
              <div className="planet-stats">
                &#9851; Fleet: {formatNumber(planet.resources.fleet.reduce((sum: number, ship: any) => sum + ship.count, 0))} ships |
                Pop: {formatNumber(planet.population || 0)}
              </div>
            )}

            {/* Infrastructure Stats */}
            {planet.infrastructure && (
              <div className="infra-stats">
                Farm: {planet.infrastructure.farming_stations || 0} |
                Mine: {planet.infrastructure.mining_stations || 0} |
                Solar: {planet.infrastructure.solar_satellites || 0}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="system-actions">
        <button onClick={loadSystems} disabled={isLoading} className="btn btn-secondary">
          &#128704; Back to System List
        </button>
        <button onClick={onBack} className="btn btn-secondary">
          &#9654; Return to Main Menu
        </button>
      </div>

      {/* Instructions */}
      <div className="system-instructions">
        <h4>System Actions:</h4>
        <ul>
          <li>&#128704; Back to system list</li>
          <li>&#9654; Return to main menu</li>
        </ul>
      </div>
    </div>
  );

  const [selectedSystem, setSelectedSystem] = useState<any>(null);
  const showSystemDetails = async (system: any) => {
    try {
      // Load detailed system info
      const res = await fetch(`/api/planets/system/${system.system_id}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedSystem(data);
        setMessage(`Viewing ${data.name} with ${data.planets.length} planet${data.planets.length !== 1 ? 's' : ''}`);
      }
    } catch (error: any) {
      console.error('Error:', error);
      setMessage(`Error: ${error.message}`);
    }
  };

  const goToPlanetDetails = async (planet: any) => {
    try {
      await fetch(`/api/planet/${planet.planet_id}`);
      onBack(); // Return to main menu
      // Would navigate to planet details in full app
      setMessage(`Planet ${planet.name} opened (navigation pending)`);
    } catch (error: any) {
      console.error('Error:', error);
    }
  };

  return selectedSystem ? renderSystemDetailsView() : renderSystemListView();
};

export default SystemMap;
