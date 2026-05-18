import React from 'react';
import PlanetDetails from './components/PlanetDetails';
import FleetManagement from './components/FleetManagement';
import Marketplace from './components/Marketplace';
import MarketplaceHero from './components/MarketplaceHero';
import SystemMap from './components/SystemMap';
import BattleSimulator from './components/BattleSimulator';
import DebugPanel from './components/DebugPanel';
import Dashboard from './components/Dashboard';
import MyAssets from './components/MyAssets';

type MarketPlaceView = 'compact' | 'hero';
type Screen = 'home' | 'dashboard' | 'planets' | 'fleet' | 'marketplace' | 'systems' | 'battle' | 'debug' | 'my-assets' | MarketPlaceView;

// Global styles import (already handled by CSS loader in vite config)

const App: React.FC = () => {
  const [currentScreen, setCurrentScreen] = React.useState<Screen>('home');
  const [activePlanetId, setActivePlanetId] = React.useState<number | null>(null);
  const [message, setMessage] = React.useState<string>("Welcome to Supremacy Game");
  const [credits, setCredits] = React.useState<number | null>(null);
  const [assetCount, setAssetCount] = React.useState<number | null>(null);
  const [marketplaceView, setMarketplaceView] = React.useState<MarketPlaceView>('compact');

  // Load player credits and asset count when switching screens
  React.useEffect(() => {
    loadPlayerCredits();
    loadAssetCount();
  }, []);

  const loadPlayerCredits = async () => {
    try {
      const res = await fetch('/api/player/credits');
      if (res.ok) {
        const data = await res.json();
        setCredits(data.credits || 0);
      }
    } catch (error) {
      console.error('Error loading credits:', error);
    }
  };

  const loadAssetCount = async () => {
    try {
      const res = await fetch('/api/player/assets');
      if (res.ok) {
        const data = await res.json();
        // Sum quantities since assets can be purchased multiple times
        const total = Array.isArray(data) ? data.reduce((s: number, a: any) => s + (a.quantity || 1), 0) : 0;
        setAssetCount(total);
      }
    } catch (error) {
      console.error('Error loading asset count:', error);
    }
  };

  const goHome = () => {
    setCurrentScreen('home');
    setActivePlanetId(null);
    setMessage("Main Menu");
  };

  const goToPlanets = (planetId?: number) => {
    setCurrentScreen(planetId ? 'planets' : 'home');
    if (planetId) setActivePlanetId(planetId);
    setMessage(planetId ? `Viewing Planet ${planetId}` : "Main Menu");
  };

  const goToFleet = () => {
    setCurrentScreen('fleet');
    setMessage("Fleet Management - Docking Bay");
  };

  const goToMarketplace = (view: MarketPlaceView) => {
    setCurrentScreen(view);
    setMarketplaceView(view);
    setMessage("Purchase Assets & Infrastructure");
  };

  const goToSystems = () => {
    setCurrentScreen('systems');
    setMessage("System List - Browse All Systems");
  };

  const goBattle = () => {
    setCurrentScreen('battle');
    setMessage("Battle Simulation - Select battles to simulate");
  };

  const goDebug = () => {
    setCurrentScreen('debug');
    setMessage("Debug Tools - Manual Level Setting");
  };

  const goToDashboard = () => {
    setCurrentScreen('dashboard');
    setActivePlanetId(null);
    setMessage("Dashboard - All Planets from Database");
  };

  const goMyAssets = () => {
    setCurrentScreen('my-assets');
    setMessage("My Purchased Assets");
  };

  return (
    <div className="supremacy-app">
      {/* Header / Navigation Bar */}
      <nav className="navigation-bar">
        <div className="nav-logo">
          <h1>SUPREMACY</h1>
          <span className="nav-status">{message}</span>
        </div>

        <div className="nav-screen-buttons">
          <button onClick={goToFleet} className="nav-btn active" id="btn-fleet">[1] Docking Bay</button>
          <button onClick={() => goToMarketplace('hero')} className="nav-btn" id="btn-marketplace-hero">[2a] Hero Banners</button>
          <button onClick={() => goToMarketplace('compact')} className="nav-btn" id="btn-marketplace-compact">[2b] Compact Grid</button>
          <button onClick={() => goToPlanets()} className="nav-btn" id="btn-planet-details">[3] Planet Details</button>
          <button onClick={goToDashboard} className="nav-btn" id="btn-dashboard">[4] Dashboard</button>
          <button onClick={goBattle} className="nav-btn" id="btn-battle-sim">[7] Battle Sim</button>
          <button onClick={goDebug} className="nav-btn debug" id="btn-debug">[8] Debug Tools</button>
          <button onClick={goToSystems} className="nav-btn" id="btn-systems">[10] System List</button>
          <button onClick={goMyAssets} className="nav-btn" id="btn-my-assets">[11] My Assets</button>
        </div>

        {credits !== null && (
        <button onClick={goHome} className="nav-home">Return to Main Menu</button>
        )}

        {assetCount !== null && (
        <div className="nav-asset-count">
          <span>&#128722;</span> {assetCount} Assets
        </div>
        )}
      </nav>

      {/* Screen Content */}
      <main className="screen-container">
        {(credits !== null || credits === undefined) && (
        <div className="player-credits-bar">
          <span>&#8363; {credits?.toLocaleString()} Credits</span>
        </div>
        )}

        {currentScreen === 'home' && (
          <div className="screen home-screen">
            <h2>Main Menu</h2>
            <div className="menu-grid">
              <div className="menu-card" onClick={goToFleet} style={{cursor: 'pointer', borderLeft: '4px solid #3498db'}}>
                <h3>[1] DOCKING BAY</h3>
                <p>Ship movement, fleet assignment, and docking operations</p>
              </div>
              <div className="menu-card" onClick={() => goToMarketplace('hero')} style={{cursor: 'pointer', borderLeft: '4px solid #3498db'}}>
                <h3>[2a] HERO BANNERS</h3>
                <p>Netflix-style horizontal banners with large item displays</p>
              </div>
              <div className="menu-card" onClick={() => goToMarketplace('compact')} style={{cursor: 'pointer'}}>
                <h3>[2b] COMPACT GRID</h3>
                <p>Traditional grid view with small thumbnails (original)</p>
              </div>
              <div className="menu-card" onClick={() => goToPlanets()} style={{cursor: 'pointer'}}>
                <h3>[3] PLANET DETAILS</h3>
                <p>View full planet information, resources, and infrastructure</p>
              </div>
              <div className="menu-card" onClick={goToDashboard} style={{cursor: 'pointer'}}>
                <h3>[4] DASHBOARD</h3>
                <p>View all planets from database with full stats and resources</p>
              </div>
              <div className="menu-card" onClick={goBattle} style={{cursor: 'pointer'}}>
                <h3>[7] BATTLE SIMULATION</h3>
                <p>Resolve combat between planets</p>
              </div>
              <div className="menu-card debug" onClick={goDebug} style={{cursor: 'pointer', borderColor: '#e74c3c'}}>
                <h3>[8] DEBUG TOOLS</h3>
                <p>Manual resource level adjustment (Development)</p>
              </div>
              <div className="menu-card" onClick={goToSystems} style={{cursor: 'pointer'}}>
                <h3>[10] SYSTEM LIST</h3>
                <p>Browse all discovered systems and planets</p>
              </div>
            </div>
          </div>
        )}

        {currentScreen === 'dashboard' && (
          <Dashboard />
        )}

        {currentScreen === 'planets' && (
          <PlanetDetails
            planetId={activePlanetId || 1}
            onBack={goHome}
            onBattle={goToSystems}
            systemList={() => goToSystems()}
          />
        )}

        {currentScreen === 'fleet' && (
          <FleetManagement
            onBack={goHome}
            setActivePlanetId={setActivePlanetId}
          />
        )}

        {currentScreen === 'compact' && (
          <Marketplace
            onBack={goHome}
          />
        )}

        {currentScreen === 'hero' && (
          <MarketplaceHero
            onBack={goHome}
          />
        )}

        {currentScreen === 'systems' && (
          <SystemMap
            onBack={goHome}
          />
        )}

        {currentScreen === 'battle' && (
          <BattleSimulator
            onBack={goHome}
          />
        )}

        {currentScreen === 'debug' && (
          <DebugPanel
            onBack={goHome}
          />
        )}

        {currentScreen === 'my-assets' && <MyAssets onBack={goHome} />}
      </main>

      {/* Status Bar */}
      <footer className="status-bar">
        <span>SUPREMACY Game v1.0</span>
        <span>Data: Live from Supremacy API (http://localhost:8000/api)</span>
      </footer>
    </div>
  );
};

export default App;
