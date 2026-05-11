// game_types.ts - Shared TypeScript types for Supremacy Game frontend

export interface ResourceUpdate {
  food: number;
  energy: number;
  mineral: number;
  fuel: number;
  taxable_income: number;
}

export interface PlanetResourceData {
  id: number;
  name: string;
  system_name: string;
  ownerName: string;
  population: number;
  resources: ResourceUpdate;
  morale: number;
}

export interface Infrastructure {
  farming_stations: number;
  mining_stations: number;
  solar_satellites: number;
}

export interface PlanetInfo {
  planet_id: number;
  name: string;
  system_id: number;
  owner_name: string;
  population: number;
  morale: number;
  tax_rate: number;
  resources: Record<string, number>;
  infrastructure: Infrastructure;
}

export interface FleetItem {
  ship_type: string;
  count: number;
}

export interface SystemInfo {
  system_id: number;
  name: string;
  planets: Array<{
    planet_id: number;
    name: string;
    owner: string;
  }>;
}

export interface AssetCatalogItem {
  name: string;
  category: 'Ship' | 'Infrastructure' | 'Equipment';
  base_cost: number;
  description?: string;
}

export interface PurchaseRequest {
  planet_id: number;
  asset_name: string;
}

export interface CombatRequest {
  attacker_planet_id: number;
  defender_planet_id: number;
}

export interface ShipMoveRequest {
  ship_id: number;
  destination_planet_id: number;
}

// Debug types matching CLI debug menu
export interface DebugPlanetLevel {
  planet_id: number;
  name: string;
  population: number;
  food_level: number;
  energy_level: number;
  fuel_level: number;
}

export interface LevelChangeRequest {
  planet_id: number;
  resource_type: 'population' | 'food_level' | 'energy_level' | 'fuel_level';
  new_value: number;
}
