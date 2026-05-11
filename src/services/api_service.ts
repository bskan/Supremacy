// api_service.ts - Client-side wrapper for all Supremacy API calls

/**
 * IMPORTANT: These functions assume a global Axios instance is configured
 * to point to the running backend server (e.g., 'http://localhost:8000/api').
 */


/**
 * Retrieves a snapshot of all active planets with their full database data.
 * @returns {Promise<Array<{planet_id: number, name: string, population: number, resources: any, infrastructure: any}>>}
 */
export async function getDashboardState() {
    const response = await fetch('/api/systems/all');
    if (!response.ok) throw new Error('Failed to load dashboard state');
    return response.json();
}

/**
 * Executes a full turn, calculating resource flow and triggering AI actions.
 */
export async function advanceTurn() {
    const response = await axios.post('/api/turn/advance');
    if (response.status === 200) return true;
    throw new Error(response.data.detail || 'Failed to advance turn.');
}

/**
 * Attempts to move a ship between two planets.
 */
export async function moveShip(shipId: number, destinationPlanetId: number) {
    const payload = {
        ship_id: shipId,
        destination_planet_id: destinationPlanetId
    };
    const response = await axios.post('/api/action/move_ship', payload);
    if (response.status === 200) return true;
    throw new Error(response.data.detail || 'Failed to move ship.');
}

/**
 * Executes combat between two planets.
 */
export async function resolveCombat(attackerPlanetId: number, defenderPlanetId: number) {
    const payload = {
        attacker_planet_id: attackerPlanetId,
        defender_planet_id: defenderPlanetId
    };
    const response = await axios.post('/api/action/battle', payload);
    if (response.status === 200) return true;
    throw new Error(response.data.detail || 'Failed to resolve combat.');
}

/**
 * Retrieves player's current credits balance.
 */
export async function getPlayerCredits() {
    const response = await axios.get('/api/player/credits');
    return response.data;
}

/**
 * Purchases an asset (ship, infrastructure, or equipment) from the marketplace.
 */
export async function purchaseAsset(planetId: number, assetName: string) {
    const payload = { planet_id: planetId, asset_name: assetName };
    const response = await axios.post('/api/marketplace/purchase', payload);
    return response.data;
}

/**
 * Retrieves available assets from the marketplace catalog.
 */
export async function getMarketplaceCatalog() {
    const response = await axios.get('/api/marketplace');
    return response.data;
}

/**
 * Retrieves a list of all systems in the game.
 */
export async function getSystems() {
    const response = await axios.get('/api/systems');
    return response.data;
}

/**
 * Retrieves planets grouped by system (system_id as key).
 */
export async function getSystemPlanets(systemId: number) {
    const response = await axios.get(`/api/planets/system/${systemId}`);
    return response.data;
}

/**
 * Retrieves a single planet's detailed state.
 */
export async function getPlanetDetails(planetId: number) {
    const response = await axios.get('/api/planet/' + planetId);
    return response.data;
}

/**
 * Formats image URL for static asset loading (from images/ folder).
 * @param imageName - Image filename from database (e.g., 'battle_cruiser.png')
 * @returns Full path to image in /images directory
 */
export function getImageUrl(imageName: string | null): string {
    if (!imageName) return '';
    // Add .png extension if missing and prefix with images/ path
    const name = imageName.endsWith('.png') ? imageName : imageName + '.png';
    return `/images/${name}`;
}