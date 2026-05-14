import React, { useState, useEffect } from 'react';

interface MyAssetsProps {
  onBack: () => void;
}

interface AssetRow {
  asset_name: string;
  asset_type: string;
  quantity: number;
  base_cost: number;
  planet_id: number;
  planet_name: string;
}

const MyAssets: React.FC<MyAssetsProps> = ({ onBack }) => {
  const [assets, setAssets] = useState<AssetRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState("Loading your assets...");

  useEffect(() => {
    loadAssets();
  }, []);

  const loadAssets = async () => {
    try {
      setIsLoading(true);
      const res = await fetch('/api/player/assets');
      if (res.ok) {
        const data = await res.json();
        setAssets(data);
        setMessage(`You own ${data.reduce((s: number, a: any) => s + (a.quantity || 1), 0)} assets across your planets.`);
      } else {
        setMessage('Failed to load assets.');
      }
    } catch (error: any) {
      console.error('Error loading assets:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const grouped = assets.reduce<Record<string, AssetRow[]>>((acc, asset) => {
    const type = asset.asset_type || 'Unknown';
    if (!acc[type]) acc[type] = [];
    acc[type].push(asset);
    return acc;
  }, {});

  const typeIcons: Record<string, string> = {
    'Ship': '🚀',
    'Infrastructure': '🏗️',
    'Equipment': '⚔️',
  };

  return (
    <div className="screen">
      <button onClick={onBack} className="back-btn">&larr; Main Menu</button>

      <h2>&#128722; My Purchased Assets</h2>

      <div className={`message-box ${isLoading ? 'loading' : ''}`}>
        <strong>Status:</strong> {message}
      </div>

      {isLoading ? (
        <p className="loading">Loading assets...</p>
      ) : assets.length === 0 ? (
        <p className="empty-catalog">No assets purchased yet. Visit the Marketplace to buy ships, infrastructure, or equipment.</p>
      ) : (
        Object.entries(grouped).map(([type, items]) => {
          const totalQty = items.reduce((s: number, a: any) => s + (a.quantity || 1), 0);
          return (
          <div key={type} className="info-section" style={{marginTop: '1.5rem'}}>
            <h3>{typeIcons[type] || '📦'} {type} ({items.length} unique, {totalQty} total)</h3>
            <div className="purchased-list">
              {items.map((asset, idx) => (
                <div key={idx} className="purchased-card">
                  <span className="purchased-icon">{typeIcons[asset.asset_type] || '📦'}</span>
                  <div>
                    <div className="purchased-type">{asset.asset_type}</div>
                    <strong>{asset.asset_name} x{asset.quantity}</strong>
                  </div>
                  <span className="purchased-cost">{Math.floor(asset.base_cost).toLocaleString()} credits each</span>
                  <span className="purchased-type" style={{fontSize: '0.7rem'}}>Planet {asset.planet_id} ({asset.planet_name})</span>
                </div>
              ))}
            </div>
          </div>
          );
        })
      )}

      <div className="debug-actions" style={{marginTop: '1.5rem'}}>
        <button onClick={loadAssets} disabled={isLoading} className="btn btn-secondary">
          &#128260; Refresh
        </button>
        <button onClick={onBack} className="btn btn-secondary">
          &#9654; Return to Main Menu
        </button>
      </div>
    </div>
  );
};

export default MyAssets;
