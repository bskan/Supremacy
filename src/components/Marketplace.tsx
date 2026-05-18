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
  const [ownedPlanets, setOwnedPlanets] = useState<any[]>([]);
  const [selectedPlanet, setSelectedPlanet] = useState<number | null>(null);
  const [barrenPlanets, setBarrenPlanets] = useState<any[]>([]);
  const [hasTerraformer, setHasTerraformer] = useState(false);
  const tabRef = React.useRef<'ships' | 'infrastructure' | 'equipment'>('ships');

  useEffect(() => {
    loadMarketplace();
    loadOwnedPlanets();
    loadBarrenPlanets();
    loadTerraformerStatus();
  }, []);

  const loadOwnedPlanets = async () => {
    try {
      const res = await fetch('/api/planets');
      if (res.ok) {
        const data = await res.json();
        setOwnedPlanets(data);
        // Auto-select first planet if none selected
        if (!selectedPlanet && data.length > 0) {
          setSelectedPlanet(data[0].id);
        }
      }
    } catch (error) {
      console.error('Error loading owned planets:', error);
    }
  };

  const loadBarrenPlanets = async () => {
    try {
      const res = await fetch('/api/systems');
      if (res.ok) {
        const systems: any[] = await res.json();
        const barren: any[] = [];
        for (const sys of systems) {
          if (sys.planets) {
            for (const p of sys.planets) {
              if (p.population === 0 || !p.population) {
                barren.push(p);
              }
            }
          }
        }
        setBarrenPlanets(barren);
      }
    } catch (error) {
      console.error('Error loading barren planets:', error);
    }
  };

  const loadTerraformerStatus = async () => {
    try {
      const res = await fetch('/api/player/assets');
      if (res.ok) {
        const data: any[] = await res.json();
        setHasTerraformer(data.some((a: any) => a.asset_name === 'Terraformer'));
      }
    } catch (error) {
      console.error('Error checking Terraformer:', error);
    }
  };

  const terraformPlanet = async (planetId: number, planetName: string) => {
    try {
      setIsLoading(true);
      setMessage(`Terraforming ${planetName}...`);
      const res = await fetch(`/api/terraform/${planetId}`, { method: 'POST' });
      if (!res.ok) {
        const data = await res.json();
        setMessage(data.detail || data.message || 'Terraforming failed');
        setIsLoading(false);
        return;
      }
      const data = await res.json();
      setMessage(data.message || 'Terraforming successful!');
      loadBarrenPlanets();
      loadTerraformerStatus();
      loadOwnedPlanets();
    } catch (error: any) {
      console.error('Error terraforming planet:', error);
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

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
        body: JSON.stringify({ planet_id: selectedPlanet, asset_name: assetName }),
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

        {/* Planet Selector */}
        {ownedPlanets.length > 0 && (
          <div className="dest-selector" style={{marginBottom: '8px'}}>
            <label>Target Planet: </label>
            <select value={selectedPlanet || ''} onChange={(e) => setSelectedPlanet(e.target.value ? Number(e.target.value) : null)}>
              {ownedPlanets.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Terraformer Section */}
        {!hasTerraformer && barrenPlanets.length > 0 && (
          <div className="info-section" style={{ marginBottom: 16 }}>
            <h3>&#127758; Terraformer - Available to Purchase</h3>
            <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 8 }}>
              The Terraformer allows you to terraform barren planets (set population to 100, adds 1 farm + 1 solar). Cost: 2,000 credits.
            </p>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => purchaseAsset('Terraformer', 2000)}
                disabled={credits < 2000}
                className="btn btn-primary"
                style={{ background: credits >= 2000 ? '#3b82f6' : '#374151' }}
              >
                {credits >= 2000 ? '&#127758; Purchase Terraformer ($2,000)' : '&#9888; Not Enough Credits'}
              </button>
            </div>
          </div>
        )}

        {hasTerraformer && barrenPlanets.length > 0 && (
          <div className="info-section" style={{ marginBottom: 16 }}>
            <h3>&#127758; Terraformer - Apply to a Barren Planet</h3>
            <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 8 }}>
              You own a Terraformer. Select a barren planet to terraform:
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {barrenPlanets.map((p: any) => (
                <div key={p.id} style={{ border: '1px solid #374151', borderRadius: 6, padding: 8, minWidth: 140 }}>
                  <div style={{ fontSize: 13, color: '#e5e7eb', marginBottom: 4 }}>{p.name}</div>
                  <button
                    onClick={() => terraformPlanet(p.id, p.name)}
                    disabled={isLoading}
                    className="btn btn-primary"
                    style={{ fontSize: 11, padding: '2px 8px' }}
                  >
                    {isLoading ? 'Working...' : '&#127758; Terraform'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {barrenPlanets.length === 0 && (
          <div className="info-section" style={{ marginBottom: 16 }}>
            <h3>&#127758; Terraformer</h3>
            <p style={{ color: '#94a3b8', fontSize: 13 }}>
              No barren planets available. All planets are already colonized.
            </p>
          </div>
        )}

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
                  {assets.infrastructure
                    .filter(item => !hasTerraformer || item.name !== 'Terraformer')
                    .map((item: any, idx: number) => (
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
                      <p className="asset-desc">{item.name === 'Terraformer'
                        ? 'Terraform a barren planet (set population=100, add 1 farm + 1 solar). Apply separately after purchase.'
                        : item.description || 'Planet development infrastructure'}</p>
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
