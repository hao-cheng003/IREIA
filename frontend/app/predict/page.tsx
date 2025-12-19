"use client";

import { useMemo, useState } from "react";
import HouseForm from "@/components/HouseForm";
import MapView from "@/components/MapView";
import TrendChart from "@/components/TrendChart";
import { apiPredict } from "@/lib/api";
import { geocodeGreaterBoston } from "@/lib/geocode";

type LatLng = { lat: number; lng: number };


type HouseFormValues = Record<string, unknown>;

type PredictOut = {
  predictedPrice: number;
  finalPrice?: number;
  assessPrice?: number;
  residual?: number;

  snappedLat?: number;
  snappedLng?: number;
  modelVersion?: string;

  trend?: {
    assess_year?: number;
    long_term_log_trend?: number;
    trend_5yr_norm?: number;
    long_term_norm?: number;
  };

  meta?: Record<string, unknown>;
};

type TrendRow = { date: string; value: number };

type GoogleGeocodeResp = {
  results?: Array<{
    formatted_address?: string;
  }>;
};

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

function fmtUSD(n?: number | null) {
  if (n == null || !Number.isFinite(Number(n))) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(Number(n));
}

function fmtPctFromLogResidual(r?: number | null) {
  if (r == null || !Number.isFinite(Number(r))) return "—";
  const pct = (Math.exp(Number(r)) - 1) * 100;
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

function getErrorMessage(e: unknown): string {
  if (e instanceof Error) return e.message;
  if (typeof e === "string") return e;
  try {
    return JSON.stringify(e);
  } catch {
    return String(e);
  }
}

function buildAssessmentTrendSeries(
  anchorPrice: number,
  longTermLogTrend?: number,
  yearsBack = 5,
  yearsForward = 1,
): TrendRow[] {
  const now = new Date().getFullYear();
  const r = Number.isFinite(Number(longTermLogTrend))
    ? Number(longTermLogTrend)
    : 0.03;

  const floor = Math.max(50_000, anchorPrice * 0.2);
  const ceiling = Math.max(anchorPrice * 2.5, anchorPrice + 2_000_000);
  const clamp = (x: number) => Math.max(floor, Math.min(x, ceiling));

  const out: TrendRow[] = [];
  for (let y = now - yearsBack; y <= now + yearsForward; y++) {
    const val = anchorPrice * Math.exp(r * (y - now));
    out.push({ date: String(y), value: clamp(val) });
  }
  return out;
}

export default function PredictPage() {
  const [loading, setLoading] = useState(false);
  const [coords, setCoords] = useState<LatLng>({ lat: 42.3601, lng: -71.0589 });

  const [pred, setPred] = useState<PredictOut | null>(null);
  const [histTrend, setHistTrend] = useState<TrendRow[]>([]);

  const [addr, setAddr] = useState("");
  const [searching, setSearching] = useState(false);
  const [selectedAddress, setSelectedAddress] = useState<string | null>(null);

  const [geoError, setGeoError] = useState<string | null>(null);

  async function reverseGeocode(lat: number, lng: number) {
    try {
      if (!GOOGLE_KEY) return;
      const url = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${lat},${lng}&key=${GOOGLE_KEY}`;
      const res = await fetch(url);
      const data = (await res.json()) as GoogleGeocodeResp;

      const formatted =
        data?.results?.[0]?.formatted_address ??
        `${lat.toFixed(5)}, ${lng.toFixed(5)}`;

      setSelectedAddress(formatted);
    } catch (e) {
      console.error("reverseGeocode failed", e);
      setSelectedAddress(null);
    }
  }

  async function handleSearch() {
    if (!addr.trim()) return;
    setSearching(true);
    setGeoError(null);

    try {
      const r = await geocodeGreaterBoston(addr);
      if (!inBostonBBox(r.lat, r.lng)) {
        setGeoError("Only support Boston area");
        return;
      }

      setCoords({ lat: r.lat, lng: r.lng });
      setSelectedAddress(
        r.display || `${r.lat.toFixed(5)}, ${r.lng.toFixed(5)}`,
      );

      setPred(null);
      setHistTrend([]);
    } catch (e: unknown) {
      setGeoError(getErrorMessage(e) || "Only support Boston area");
    } finally {
      setSearching(false);
    }
  }

  async function handleSubmit(v: HouseFormValues) {
    try {
      if (!inBostonBBox(coords.lat, coords.lng)) {
        setGeoError("Only support Boston area");
        return;
      }
      setGeoError(null);
      setLoading(true);

      const payload = {
        ...(v as Record<string, unknown>),
        latitude: coords.lat,
        longitude: coords.lng,
      };

      const p = (await apiPredict(payload)) as PredictOut;
      setPred(p);

      const lat = Number.isFinite(Number(p.snappedLat))
        ? Number(p.snappedLat)
        : coords.lat;
      const lng = Number.isFinite(Number(p.snappedLng))
        ? Number(p.snappedLng)
        : coords.lng;

      if (!inBostonBBox(lat, lng)) {
        setGeoError("Only support Boston area");
        return;
      }

      setCoords({ lat, lng });
      reverseGeocode(lat, lng);

      const anchor = Number(p.finalPrice ?? p.predictedPrice);
      const r = p?.trend?.long_term_log_trend;

      if (Number.isFinite(anchor) && anchor > 0) {
        setHistTrend(buildAssessmentTrendSeries(anchor, r, 5, 1));
      } else {
        setHistTrend([]);
      }
    } catch (e: unknown) {
      console.error(e);
      setGeoError(getErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }

  const chartData: TrendRow[] = useMemo(() => {
    return [...histTrend].sort((a, b) => Number(a.date) - Number(b.date));
  }, [histTrend]);

  return (
    <main style={{ minHeight: "100vh", background: "#f8fafc" }}>
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 10,
          background: "#fff",
          borderBottom: "1px solid #e5e7eb",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          padding: "14px 16px",
        }}
      >
        <h1
          style={{ margin: 0, fontSize: 24, fontWeight: 800, letterSpacing: 1 }}
        >
          IREA
        </h1>
      </header>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "7fr 5fr",
          gap: 0,
          height: "75vh",
          minHeight: 420,
          background: "#fff",
          borderBottom: "1px solid #e5e7eb",
        }}
      >
        <div
          style={{
            borderRight: "1px solid #e5e7eb",
            display: "flex",
            flexDirection: "column",
            minHeight: 0,
          }}
        >
          <div style={{ flex: 1, minHeight: 0 }}>
            <MapView
              lat={coords.lat}
              lng={coords.lng}
              onPick={(lat: number, lng: number, address?: string, error?: string) => {
                if (error) {
                  setGeoError(error);
                  return;
                }
                if (!inBostonBBox(lat, lng)) {
                  setGeoError("Only support Boston area");
                  return;
                }
                setGeoError(null);
                setCoords({ lat, lng });
                if (address) setSelectedAddress(address);
                else reverseGeocode(lat, lng);
              }}
            />
          </div>
        </div>

        <aside style={{ display: "flex", flexDirection: "column", minHeight: 0 }}>
          <div
            style={{
              borderBottom: "1px solid #e5e7eb",
              padding: "10px 16px",
              fontSize: 12,
              color: "#4b5563",
            }}
          >
            <div>
              Coords: {coords.lat.toFixed(5)}, {coords.lng.toFixed(5)}
            </div>

            <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
              <input
                value={addr}
                onChange={(e) => setAddr(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSearch();
                }}
                placeholder="e.g. 12 Hull St"
                style={{
                  flex: 1,
                  background: "#fff",
                  color: "#111",
                  border: "1.5px solid #d1d5db",
                  borderRadius: 8,
                  padding: "8px 10px",
                  fontSize: 15,
                }}
              />
              <button
                onClick={handleSearch}
                disabled={searching || !addr.trim()}
                style={{
                  background: searching ? "#93c5fd" : "#2563eb",
                  color: "#fff",
                  fontSize: 14,
                  fontWeight: 600,
                  padding: "8px 14px",
                  border: "none",
                  borderRadius: 8,
                  cursor: searching ? "not-allowed" : "pointer",
                }}
              >
                {searching ? "Searching..." : "Search"}
              </button>
            </div>

            {geoError && (
              <div
                style={{
                  marginTop: 8,
                  fontSize: 13,
                  color: "#b91c1c",
                  fontWeight: 600,
                }}
              >
                {geoError}
              </div>
            )}

            {selectedAddress && (
              <div style={{ marginTop: 8, fontSize: 13, color: "#111827" }}>
                <div style={{ fontWeight: 600, marginBottom: 2 }}>
                  Selected Address
                </div>
                <div style={{ fontWeight: 400 }}>{selectedAddress}</div>
              </div>
            )}
          </div>

          <div
            style={{
              flex: 1,
              minHeight: 0,
              overflowY: "auto",
              padding: 16,
              background: "#f9fafb",
            }}
          >
            <div
              style={{
                border: "1px solid #e5e7eb",
                borderRadius: 12,
                padding: 16,
                background: "#fff",
              }}
            >
              <HouseForm
                onSubmit={handleSubmit}
                loading={loading}
                coords={coords}
                selectedAddress={selectedAddress ?? undefined}
              />
            </div>
          </div>
        </aside>
      </section>

      <section style={{ padding: "16px 16px 24px" }}>
        <h2
          style={{
            margin: "4px 0 12px",
            fontSize: 18,
            fontWeight: 600,
            color: "#111827",
          }}
        >
          Prediction Results
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div
            style={{
              border: "1px solid #e5e7eb",
              borderRadius: 12,
              padding: 16,
              background: "#fff",
              minHeight: 140,
            }}
          >
            <div style={{ fontSize: 20, marginBottom: 10 }}>
              Final Price:{" "}
              <b>{fmtUSD(pred?.finalPrice ?? pred?.predictedPrice)}</b>
            </div>

            <div style={{ fontSize: 18, color: "#374151", lineHeight: 2.2 }}>
              <div>
                Assessment: <b>{fmtUSD(pred?.assessPrice)}</b>
              </div>
              <div>
                Residual Adj.: <b>{fmtPctFromLogResidual(pred?.residual)}</b>
              </div>
            </div>

            <div style={{ fontSize: 16, color: "#6b7280", marginTop: 8 }}>
              Model: {pred?.modelVersion || "Baseline+Residual"}
            </div>

            <div style={{ fontSize: 16, color: "#6b7280", marginTop: 8 }}>
              Trend r:{" "}
              {pred?.trend?.long_term_log_trend != null
                ? Number(pred.trend.long_term_log_trend).toFixed(4)
                : "—"}
            </div>
          </div>

          <div
            style={{
              border: "1px solid #e5e7eb",
              borderRadius: 12,
              padding: 16,
              background: "#fff",
              minHeight: 140,
            }}
          >
            <TrendChart data={chartData} />
          </div>
        </div>
      </section>
    </main>
  );
}
