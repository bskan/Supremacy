import React, { useState, useEffect } from 'react';

interface MarketplaceProps {
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

const Marketplace: React.FC<MarketplaceProps> = ({ onBack }) => {
  const [assets, setAssets] = useState<{ ships: any[]; infrastructure: any[]; equipment: any[] }>({
    ships: [],
    infrastructure: [],
    equipment: [],
  });
  const [credits, setCredits] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<string>('Loading marketplace...');
  const tabRef = React.useRef<'ships' | 'infrastructure' | 'equipment'>('ships');

  useEffect(() => {
    loadMarketplace();
  }, []);

  const loadMarketplace = async () => {
    try {
      setIsLoading(true);
      // Load asset catalog from API
      const res = await fetch('/api/marketplace');
      if (res.ok) {
        const rawData: any = await res.json();

        // Handle object response format (from database query with category field)
        let ships: any[] = [];
        let infrastructure: any[] = [];
        let equipment: any[] = [];

        // Extract arrays from the API response
        if (rawData.ships && Array.isArray(rawData.ships)) {
          ships = rawData.ships;
        }
        if (rawData.infrastructure && Array.isArray(rawData.infrastructure)) {
          infrastructure = rawData.infrastructure;
        }
        if (rawData.equipment && Array.isArray(rawData.equipment)) {
          equipment = rawData.equipment;
        }

        // Handle flat array format with category field as fallback
        const hasArrayFormat = !ships.length && typeof rawData === 'object' && !Array.isArray(rawData);
        let allItems: any[] = [];
        if (hasArrayFormat) {
          Object.values(rawData).forEach((item: any) => {
            if (item && item.category && Array.isArray(item.category)) {
              return; // Skip category arrays
            }
            allItems.push(item);
          });
          ships = allItems.filter(i => i?.category === 'Ship' || i?.asset_category === 'ships');
          infrastructure = allItems.filter(i => i?.category === 'Infrastructure' || i?.asset_category === 'infrastructure');
          equipment = allItems.filter(i => i?.category === 'Equipment' || i?.asset_category === 'equipment');
        }

        // Handle flat array directly if available
        if (Array.isArray(rawData) && !ships.length) {
          const items = rawData;
          ships = items.filter(i => i?.category === 'Ship' || i?.asset_category === 'ships');
          infrastructure = items.filter(i => i?.category === 'Infrastructure' || i?.asset_category === 'infrastructure');
          equipment = items.filter(i => i?.category === 'Equipment' || i?.asset_category === 'equipment');
        }

        setAssets({ ships, infrastructure, equipment });

      } else {
        setMessage('Error: Failed to load marketplace catalog');
      }

      // Load player credits
      const creditsRes = await fetch('/api/player/credits');
      if (creditsRes.ok) {
        const credsData = await creditsRes.json();
        setCredits(credsData.credits || 0);
      }
    } catch (error: any) {
      console.error('Error loading marketplace:', error);
      setMessage(`Error: Failed to load data`);
    } finally {
      setIsLoading(false);
    }
  };

  const purchaseAsset = async (assetName: string, assetPrice: number) => {
    try {
      setIsLoading(true);
      const res = await fetch('/api/marketplace/purchase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ planet_id: 1, asset_name: assetName }),
      });

      if (!res.ok) {
        const data = await res.json();
        setMessage(data.detail || `Purchase failed: ${data.detail}`);
        setIsLoading(false);
        return;
      }

      const data = await res.json();
      setMessage(data.message || 'Purchase successful');

      // Update credits after purchase
      const response = await fetch('/api/player/credits');
      if (response.ok) {
        const creditData = await response.json();
        setCredits(creditData.credits || 0);
      }
      loadMarketplace(); // Refresh catalog
    } catch (error: any) {
      console.error('Error purchasing asset:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Render catalog view
  const renderCatalog = () => {
    return (
      <div className="screen marketplace-screen">
        <button onClick={onBack} className="back-btn">&larr; Main Menu</button>
        <h2>Purchase Assets & Infrastructure</h2>

        {/* Credits Display */}
        <div className="credits-display">
          &#8363; {formatNumber(credits)} Credits Available
        </div>

        <div className={`message-box ${isLoading ? 'loading' : ''}`}>
          <strong>Status:</strong> {message}
        </div>

        {/* Catalog Tabs */}
        <nav className="catalog-tabs">
          <button
            className={tabRef.current === 'ships' ? 'active' : ''}
            onClick={() => {
              tabRef.current = 'ships';
              loadMarketplace(); // Refresh to re-render with new tab active
            }}
          >
            &#9851; Ships ({assets.ships.length})
          </button>
          <button
            className={tabRef.current === 'infrastructure' ? 'active' : ''}
            onClick={() => {
              tabRef.current = 'infrastructure';
              loadMarketplace(); // Refresh to re-render with new tab active
            }}
          >
            &#128736; Infrastructure ({assets.infrastructure.length})
          </button>
          <button
            className={tabRef.current === 'equipment' ? 'active' : ''}
            onClick={() => {
              tabRef.current = 'equipment';
              loadMarketplace(); // Refresh to re-render with new tab active
            }}
          >
            &#128663; Equipment ({assets.equipment.length})
          </button>
        </nav>

        {/* Asset Catalog */}
        <div className="catalog-content">
          {isLoading && (
            <div className="loading">Loading catalog...</div>
          )}

          {!isLoading && (
            <>
              {/* Ships Tab */}
              {tabRef.current === 'ships' && assets.ships.length > 0 && (
                <div className="catalog-section ships">
                  <h3>&#9851; Available Ships</h3>
                  {assets.ships.map((ship: any, idx: number) => (
                    <div key={idx} className={`asset-card ${credits < ship.base_cost ? 'out-of-credits' : ''}`}>
                      <div className="asset-header">
                        <img
                          src={`/images/${ship.image_url}`}
                          alt={ship.name}
                          className="asset-image"
                          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                        />
                        <span className="asset-icon">&#9851;</span>
                        <strong>{ship.name}</strong>
                        <span className={`asset-category ${credits < ship.base_cost ? 'out-of-credits' : ''}`} title={`${Math.floor(ship.base_cost).toLocaleString()} credits`}>Ship</span>
                        {credits < ship.base_cost && (
                          <span className="out-of-credits-badge">&#9888; Out of Credits</span>
                        )}
                      </div>
                      <p className="asset-desc">{ship.description || `Advanced ${ship.name.toLowerCase()}`}</p>
                      <div className="asset-price">₫{Math.floor(ship.base_cost).toLocaleString()}</div>
                      <button
                        onClick={() => purchaseAsset(ship.name, ship.base_cost)}
                        disabled={credits < ship.base_cost}
                        className={`btn btn-primary ${credits < ship.base_cost ? 'disabled' : ''}`}
                      >
                        {credits >= ship.base_cost ? 'Purchase' : 'Out of Credits'}
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Infrastructure Tab */}
              {tabRef.current === 'infrastructure' && assets.infrastructure.length > 0 && (
                <div className="catalog-section infrastructure">
                  <h3>&#128736; Available Infrastructure</h3>
                  {assets.infrastructure.map((item: any, idx: number) => (
                    <div key={idx} className={`asset-card ${credits < item.base_cost ? 'out-of-credits' : ''}`}>
                      <div className="asset-header">
                        <img
                          src={`/images/${item.image_url}`}
                          alt={item.name}
                          className="asset-image"
                          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                        />
                        <span className="asset-icon">&#128736;</span>
                        <strong>{item.name}</strong>
                        <span className={`asset-category ${credits < item.base_cost ? 'out-of-credits' : ''}`} title={`${Math.floor(item.base_cost).toLocaleString()} credits`}>Infrastructure</span>
                        {credits < item.base_cost && (
                          <span className="out-of-credits-badge">&#9888; Out of Credits</span>
                        )}
                      </div>
                      <p className="asset-desc">{item.description || 'Planet development infrastructure'}</p>
                      <div className="asset-price">₫{Math.floor(item.base_cost).toLocaleString()}</div>
                      <button
                        onClick={() => purchaseAsset(item.name, item.base_cost)}
                        disabled={credits < item.base_cost}
                        className={`btn btn-primary ${credits < item.base_cost ? 'disabled' : ''}`}
                      >
                        {credits >= item.base_cost ? 'Purchase' : 'Out of Credits'}
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Equipment Tab */}
              {tabRef.current === 'equipment' && assets.equipment.length > 0 && (
                <div className="catalog-section equipment">
                  <h3>&#128663; Available Equipment</h3>
                  {assets.equipment.map((item: any, idx: number) => (
                    <div key={idx} className={`asset-card ${credits < item.base_cost ? 'out-of-credits' : ''}`}>
                      <div className="asset-header">
                        <img
                          src={`/images/${item.image_url}`}
                          alt={item.name}
                          className="asset-image"
                          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                        />
                        <span className="asset-icon">&#9851;</span>
                        <strong>{item.name}</strong>
                        <span className={`asset-category ${credits < item.base_cost ? 'out-of-credits' : ''}`} title={`${Math.floor(item.base_cost).toLocaleString()} credits`}>Equipment</span>
                        {credits < item.base_cost && (
                          <span className="out-of-credits-badge">&#9888; Out of Credits</span>
                        )}
                      </div>
                      <p className="asset-desc">{item.description || 'Ship and unit equipment'}</p>
                      <div className="asset-price">₫{Math.floor(item.base_cost).toLocaleString()}</div>
                      <button
                        onClick={() => purchaseAsset(item.name, item.base_cost)}
                        disabled={credits < item.base_cost}
                        className={`btn btn-primary ${credits < item.base_cost ? 'disabled' : ''}`}
                      >
                        {credits >= item.base_cost ? 'Purchase' : 'Out of Credits'}
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Show empty message if no items in current tab */}
              {!isLoading && assets[tabRef.current] && assets[tabRef.current].length === 0 && (
                <div className="empty-catalog">No items in this category.</div>
              )}
            </>
          )}
        </div>

        {/* Catalog Actions */}
        <div className="catalog-actions">
          <button onClick={loadMarketplace} disabled={isLoading} className="btn btn-secondary">
            &#128704; Refresh Catalog
          </button>
          <button onClick={onBack} className="btn btn-secondary">
            &#9654; Return to Main Menu
          </button>
        </div>

        {/* Purchase Instructions */}
        <div className="catalog-instructions">
          <h4>Purchase Options:</h4>
          <ul>
            <li>&#128640; Purchase assets from catalog (ships, infrastructure, equipment)</li>
            <li>&#9888; Assets show as unavailable when out of credits</li>
            <li>&#128704; Refresh catalog to see updated availability</li>
          </ul>
        </div>
      </div>
    );
  };

  return renderCatalog();
};

export default Marketplace;
