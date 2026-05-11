import React, { useState, useEffect } from 'react';

interface MarketplaceHeroProps {
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

interface HeroItem {
  name: string;
  category: string;
  base_cost: number;
  description: string;
  image_url?: string;
}

const MarketplaceHero: React.FC<MarketplaceHeroProps> = ({ onBack }) => {
  const [assets, setAssets] = useState<{ ships: HeroItem[]; infrastructure: HeroItem[]; equipment: HeroItem[] }>({
    ships: [],
    infrastructure: [],
    equipment: [],
  });
  const [credits, setCredits] = useState(0);
  const [activeCategory, setActiveCategory] = useState<'ships' | 'infrastructure' | 'equipment'>('ships');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<string>('Loading marketplace...');
  const scrollRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadMarketplace();
  }, []);

  const scrollToItem = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollLeft = scrollRef.current.scrollWidth / 2;
    }
  };

  const handleHoverEnter = () => {
    if (scrollRef.current) {
      scrollRef.current.classList.add('hover');
    }
  };

  const handleHoverLeave = () => {
    if (scrollRef.current) {
      scrollRef.current.classList.remove('hover');
    }
  };

  const loadMarketplace = async () => {
    try {
      setIsLoading(true);
      // Load asset catalog from API
      const res = await fetch('/api/marketplace');
      if (res.ok) {
        const rawData: any = await res.json();

        let ships: HeroItem[] = [];
        let infrastructure: HeroItem[] = [];
        let equipment: HeroItem[] = [];

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

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'ship': return '&#9851;';
      case 'infrastructure': return '&#128736;';
      default: return '&#128663;';
    }
  };

  const getCategoryTitle = (category: string) => {
    switch (category.toLowerCase()) {
      case 'ship': return '&#9851; Ships';
      case 'infrastructure': return '&#128736; Infrastructure';
      default: return '&#128663; Equipment';
    }
  };

  const renderHeroItem = (item: HeroItem) => {
    const affordable = credits >= item.base_cost;

    return (
      <div
        key={item.name}
        className="hero-item-card"
        onClick={() => affordable && purchaseAsset(item.name, item.base_cost)}
      >
        {/* Large hero header */}
        <div className="hero-header">
          <img
            src={`/images/${item.image_url || ''}`}
            alt={item.name}
            className="hero-image"
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
          />
          <div className="hero-category-badge">
            <span className="category-icon">{getCategoryIcon(item.category)}</span>
            <span className="category-title">{getCategoryTitle(item.category)}</span>
          </div>
        </div>

        {/* Content section */}
        <div className="hero-content">
          <h3 className="hero-item-name">{item.name}</h3>

          {item.description && (
            <p className="hero-item-desc">{item.description}</p>
          )}

          {!item.description && (
            <p className="hero-item-desc">Advanced {item.name.toLowerCase()}</p>
          )}

          <div className="hero-stats">
            <span className="stat price" title={`${Math.floor(item.base_cost).toLocaleString()} credits`}>
              Price: ₫{Math.floor(item.base_cost).toLocaleString()}
            </span>
            {!affordable && (
              <span className="stat unavailable">&#9888; Out of Credits</span>
            )}
          </div>

          {affordable && (
            <button className="btn btn-primary hero-purchase-btn" onClick={(e) => { e.stopPropagation(); purchaseAsset(item.name, item.base_cost); }}>
              Purchase Now
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="screen marketplace-hero-screen">
      {/* Back button */}
      <button onClick={onBack} className="back-btn">&larr; Main Menu</button>

      {/* Header section */}
      <header className="marketplace-header">
        <h2>Purchase Assets & Infrastructure</h2>

        {/* Credits Display */}
        <div className="credits-display">
          &#8363; {formatNumber(credits)} Credits Available
        </div>

        {/* Category Tabs */}
        <nav className="category-tabs">
          <button
            className={activeCategory === 'ships' ? 'active' : ''}
            onClick={() => { setActiveCategory('ships'); loadMarketplace(); }}
          >
            &#9851; Ships ({assets.ships.length})
          </button>
          <button
            className={activeCategory === 'infrastructure' ? 'active' : ''}
            onClick={() => { setActiveCategory('infrastructure'); loadMarketplace(); }}
          >
            &#128736; Infrastructure ({assets.infrastructure.length})
          </button>
          <button
            className={activeCategory === 'equipment' ? 'active' : ''}
            onClick={() => { setActiveCategory('equipment'); loadMarketplace(); }}
          >
            &#128663; Equipment ({assets.equipment.length})
          </button>
        </nav>
      </header>

      {/* Status/Message */}
      <div className={`message-box ${isLoading ? 'loading' : ''}`}>
        <strong>Status:</strong> {message}
      </div>

      {/* Horizontal Scroll Container */}
      <div className="hero-scroll-container">
        <div
          ref={scrollRef}
          className="hero-scroll-track"
          onMouseEnter={handleHoverEnter}
          onMouseLeave={handleHoverLeave}
        >
          {/* Scroll Controls */}
          <button
            className="scroll-btn left"
            onClick={(e) => { e.stopPropagation(); scrollToItem(); }}
            disabled={isLoading}
          >
            &#9664; Previous
          </button>

          {/* Items */}
          {(assets[activeCategory] || []).map(renderHeroItem)}

          {/* Scroll indicator */}
          <span className="scroll-indicator">Scroll &rarr;</span>

          <button
            className="scroll-btn right"
            onClick={(e) => { e.stopPropagation(); scrollToItem(); }}
            disabled={isLoading}
          >
            Next &rarr;
          </button>
        </div>
      </div>

      {/* Footer actions */}
      <div className="marketplace-footer">
        <button onClick={loadMarketplace} disabled={isLoading} className="btn btn-secondary">
          &#128704; Refresh Catalog
        </button>
        <button onClick={onBack} className="btn btn-secondary">
          &rarr; Return to Main Menu
        </button>

        {/* Instructions */}
        <div className="marketplace-instructions">
          <h4>Purchase Guide:</h4>
          <ul>
            <li>&#128640; Click any item banner above with sufficient credits</li>
            <li>&#9888; Items show as unavailable when you're out of credits</li>
            <li>&#127935; Use scroll buttons to browse more items</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default MarketplaceHero;
