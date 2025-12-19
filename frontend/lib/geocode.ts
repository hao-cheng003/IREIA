type GeoOut = { lat: number; lng: number; display: string };

const GOOGLE_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

const BOSTON_BBOX = {
  latMin: 42.2279,
  latMax: 42.3995,
  lngMin: -71.1912,
  lngMax: -70.986,
};

function inBostonBBox(lat: number, lng: number) {
  return (
    lat >= BOSTON_BBOX.latMin &&
    lat <= BOSTON_BBOX.latMax &&
    lng >= BOSTON_BBOX.lngMin &&
    lng <= BOSTON_BBOX.lngMax
  );
}

export async function geocodeGreaterBoston(q: string): Promise<GeoOut> {
  if (!GOOGLE_KEY) throw new Error("Missing Google Maps API key");

  const query = q.trim();
  if (!query) throw new Error("Only support Boston area");

  const address = /boston/i.test(query) ? query : `${query}, Boston, MA`;

  const bounds = `${BOSTON_BBOX.latMin},${BOSTON_BBOX.lngMin}|${BOSTON_BBOX.latMax},${BOSTON_BBOX.lngMax}`;

  const url =
    `https://maps.googleapis.com/maps/api/geocode/json` +
    `?address=${encodeURIComponent(address)}` +
    `&bounds=${encodeURIComponent(bounds)}` +
    `&region=us` +
    `&key=${encodeURIComponent(GOOGLE_KEY)}`;

  const res = await fetch(url);
  const data = await res.json();

  const top = data?.results?.[0];
  const loc = top?.geometry?.location;
  if (!loc) throw new Error("Only support Boston area");

  const lat = Number(loc.lat);
  const lng = Number(loc.lng);

  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    throw new Error("Only support Boston area");
  }
  if (!inBostonBBox(lat, lng)) {
    throw new Error("Only support Boston area");
  }

  const display =
    top.formatted_address || `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
  return { lat, lng, display };
}
