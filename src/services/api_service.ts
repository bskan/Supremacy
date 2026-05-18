// api_service.ts - Client-side wrapper for all Supremacy API calls

export async function getDashboardState() {
    const response = await fetch('/api/systems/all');
    if (!response.ok) throw new Error('Failed to load dashboard state');
    return response.json();
}

export async function advanceTurn() {
    const response = await fetch('/api/turn/advance', { method: 'POST' });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Failed to advance turn.');
    }
    return true;
}

export async function moveShip(shipId: number, destinationPlanetId: number) {
    const response = await fetch('/api/action/move_ship', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ship_id: shipId, destination_planet_id: destinationPlanetId }),
    });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Failed to move ship.');
    }
    return true;
}

export async function resolveCombat(attackerPlanetId: number, defenderPlanetId: number) {
    const response = await fetch('/api/action/battle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ attacker_planet_id: attackerPlanetId, defender_planet_id: defenderPlanetId }),
    });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Failed to resolve combat.');
    }
    return true;
}

export async function getPlayerCredits() {
    const response = await fetch('/api/player/credits');
    if (!response.ok) throw new Error('Failed to load credits');
    return response.json();
}

export async function purchaseAsset(planetId: number, assetName: string) {
    const response = await fetch('/api/marketplace/purchase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ planet_id: planetId, asset_name: assetName }),
    });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Failed to purchase asset.');
    }
    return response.json();
}

export async function getMarketplaceCatalog() {
    const response = await fetch('/api/marketplace');
    if (!response.ok) throw new Error('Failed to load marketplace');
    return response.json();
}

export async function getSystems() {
    const response = await fetch('/api/systems');
    if (!response.ok) throw new Error('Failed to load systems');
    return response.json();
}

export async function getSystemPlanets(systemId: number) {
    const response = await fetch(`/api/planets/system/${systemId}`);
    if (!response.ok) throw new Error('Failed to load system planets');
    return response.json();
}

export async function getPlanetDetails(planetId: number) {
    const response = await fetch(`/api/planet/${planetId}`);
    if (!response.ok) throw new Error('Failed to load planet details');
    return response.json();
}

export function getImageUrl(imageName: string | null): string {
    if (!imageName) return '';
    const name = imageName.endsWith('.png') ? imageName : imageName + '.png';
    return `/images/${name}`;
}
