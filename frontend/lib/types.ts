export type LatLng = { lat: number; lng: number };

export type TrendPoint = { date: string; value: number };

export type PredictPayload = {
  latitude?: number;
  longitude?: number;
  areaSqft: number;
  lotSqft: number;
  bedrooms: number;
  bathrooms: number;
  builtYear: number;
  propertyType: string;
  renovated: boolean;
  parking: boolean;
  parkingSpaces: number;
};

export type PredictResponse = {
  estimatedPrice: number;
  // 你的接口如果还有这些就保留；没有就删
  trend?: TrendPoint[];
  neighborhood?: Record<string, unknown>;
  raw?: Record<string, unknown>;
};
