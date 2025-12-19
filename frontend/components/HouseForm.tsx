"use client";

import { useMemo, useState } from "react";

export type LatLng = { lat: number; lng: number };

export type HouseFormValues = {
  areaSqft: number;
  bedrooms: number;
  bathrooms: number;
  builtYear: number;
  parkingSpaces: number;
  lotSqft?: number;
  renovated: 0 | 1;
  sale_year?: number;
  sale_month?: number;
  latitude?: number;
  longitude?: number;
};

type Props = {
  onSubmit: (payload: HouseFormValues) => Promise<void> | void;
  loading?: boolean;
  coords?: LatLng;
  selectedAddress?: string; 
};

function clampInt(
  v: string | number,
  min: number,
  max: number,
  fallback: number,
): number {
  const n = typeof v === "number" ? v : Number(v);
  if (!Number.isFinite(n)) return fallback;
  return Math.max(min, Math.min(max, Math.round(n)));
}

function clampNum(
  v: string | number,
  min: number,
  max: number,
  fallback: number,
): number {
  const n = typeof v === "number" ? v : Number(v);
  if (!Number.isFinite(n)) return fallback;
  return Math.max(min, Math.min(max, n));
}

type FormState = {
  areaSqft: number;
  bedrooms: number;
  bathrooms: number;
  builtYear: number;
  parkingSpaces: number;

  lotSqft: string;
  renovated: boolean;
  sale_year: string;
  sale_month: string;
};

export default function HouseForm({
  onSubmit,
  loading,
  coords,
  selectedAddress,
}: Props) {
  const now = useMemo(() => new Date(), []);
  const defaultYear = 1950;

  const [showMore, setShowMore] = useState(false);

  const [form, setForm] = useState<FormState>({
    areaSqft: 1200,
    bedrooms: 3,
    bathrooms: 1.5,
    builtYear: defaultYear,
    parkingSpaces: 1,

    lotSqft: "",
    renovated: false,
    sale_year: "",
    sale_month: "",
  });

  const set = <K extends keyof FormState>(k: K, v: FormState[K]) =>
    setForm((p) => ({ ...p, [k]: v }));

  function buildPayload(): HouseFormValues {
    const payload: HouseFormValues = {
      areaSqft: clampInt(form.areaSqft, 100, 20000, 1200),
      bedrooms: clampInt(form.bedrooms, 0, 20, 3),
      bathrooms: clampNum(form.bathrooms, 0, 20, 1.5),
      builtYear: clampInt(form.builtYear, 1700, now.getFullYear(), defaultYear),
      parkingSpaces: clampInt(form.parkingSpaces, 0, 20, 1),
      renovated: form.renovated ? 1 : 0,
    };

    if (String(form.lotSqft).trim() !== "") {
      payload.lotSqft = clampInt(form.lotSqft, 0, 500000, 0);
    }

    if (String(form.sale_year).trim() !== "") {
      payload.sale_year = clampInt(
        form.sale_year,
        2000,
        now.getFullYear(),
        now.getFullYear(),
      );
    }

    if (String(form.sale_month).trim() !== "") {
      payload.sale_month = clampInt(form.sale_month, 1, 12, now.getMonth() + 1);
    }

    if (coords && Number.isFinite(coords.lat) && Number.isFinite(coords.lng)) {
      payload.latitude = coords.lat;
      payload.longitude = coords.lng;
    }

    return payload;
  }

  function resetBasic() {
    setForm({
      areaSqft: 1200,
      bedrooms: 3,
      bathrooms: 1.5,
      builtYear: defaultYear,
      parkingSpaces: 1,
      lotSqft: "",
      renovated: false,
      sale_year: "",
      sale_month: "",
    });
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(buildPayload());
      }}
      className="wrap"
    >
      <div className="card">
        <div className="title">Basic Inputs</div>

        {}
        {selectedAddress && (
          <div className="hint" style={{ marginBottom: 8 }}>
            Selected: {selectedAddress}
          </div>
        )}

        <div className="grid2">
          <div>
            <label className="label">Area (sqft)</label>
            <input
              className="input"
              type="number"
              value={form.areaSqft}
              onChange={(e) => set("areaSqft", Number(e.target.value))}
              min={0}
            />
          </div>

          <div>
            <label className="label">Built Year</label>
            <input
              className="input"
              type="number"
              value={form.builtYear}
              onChange={(e) => set("builtYear", Number(e.target.value))}
              min={1700}
              max={now.getFullYear()}
            />
          </div>
        </div>

        <div className="grid2">
          <div>
            <label className="label">Bedrooms</label>
            <input
              className="input"
              type="number"
              value={form.bedrooms}
              onChange={(e) => set("bedrooms", Number(e.target.value))}
              min={0}
            />
          </div>

          <div>
            <label className="label">Bathrooms</label>
            <input
              className="input"
              type="number"
              step="0.5"
              value={form.bathrooms}
              onChange={(e) => set("bathrooms", Number(e.target.value))}
              min={0}
            />
          </div>
        </div>

        <div className="grid2">
          <div>
            <label className="label">Parking Spaces</label>
            <input
              className="input"
              type="number"
              value={form.parkingSpaces}
              onChange={(e) => set("parkingSpaces", Number(e.target.value))}
              min={0}
            />
          </div>

          <div>
            <label className="label">Renovated (optional)</label>
            <select
              className="select"
              value={String(form.renovated)}
              onChange={(e) => set("renovated", e.target.value === "true")}
            >
              <option value="false">No / Unknown</option>
              <option value="true">Yes</option>
            </select>
          </div>
        </div>

        <div className="rowBtns">
          <button
            type="button"
            className="ghost"
            onClick={resetBasic}
            disabled={loading}
          >
            Reset
          </button>

          <button
            type="button"
            className="more"
            onClick={() => setShowMore((v) => !v)}
            disabled={loading}
          >
            {showMore ? "Hide More ▲" : "More (optional) ▼"}
          </button>
        </div>

        {showMore && (
          <div className="moreBox">
            <div className="grid2">
              <div>
                <label className="label">Lot (sqft)</label>
                <input
                  className="input"
                  type="number"
                  value={form.lotSqft}
                  onChange={(e) => set("lotSqft", e.target.value)}
                  placeholder="Leave blank if unknown"
                  min={0}
                />
              </div>

              <div>
                <label className="label">Market date (optional)</label>
                <div className="grid2_inner">
                  <input
                    className="input"
                    type="number"
                    value={form.sale_year}
                    onChange={(e) => set("sale_year", e.target.value)}
                    placeholder={`Year (default ${now.getFullYear()})`}
                    min={2000}
                    max={now.getFullYear()}
                  />
                  <input
                    className="input"
                    type="number"
                    value={form.sale_month}
                    onChange={(e) => set("sale_month", e.target.value)}
                    placeholder={`Month (default ${now.getMonth() + 1})`}
                    min={1}
                    max={12}
                  />
                </div>
              </div>
            </div>

            <div className="hint">
              If you leave market date blank, the residual model uses the default
              (year=2025, month=current).
            </div>
          </div>
        )}

        <button className="btn" disabled={loading}>
          {loading ? "Predicting..." : "Predict"}
        </button>
      </div>

      <style jsx>{`
        .wrap {
          font-size: 15px;
          line-height: 1.5;
          color: #111;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .card {
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          padding: 14px;
          background: #fff;
        }
        .title {
          font-size: 14px;
          font-weight: 800;
          color: #111827;
          margin-bottom: 6px;
        }
        .hint {
          font-size: 12px;
          color: #6b7280;
        }
        .grid2 {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
          margin-top: 10px;
        }
        .grid2_inner {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }
        .label {
          display: block;
          font-size: 13px;
          font-weight: 600;
          margin-bottom: 4px;
          color: #374151;
        }
        .input,
        .select {
          width: 100%;
          background: #fff;
          color: #111;
          border: 1.5px solid #d1d5db;
          border-radius: 10px;
          padding: 9px 10px;
          font-size: 15px;
          box-sizing: border-box;
        }
        .input:focus,
        .select:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 1px #3b82f6;
        }
        .rowBtns {
          display: flex;
          gap: 10px;
          margin-top: 12px;
        }
        .ghost,
        .more {
          flex: 1;
          background: #fff;
          color: #111827;
          border: 1px solid #e5e7eb;
          border-radius: 10px;
          padding: 9px 10px;
          font-size: 14px;
          font-weight: 700;
          cursor: pointer;
        }
        .ghost:hover:not(:disabled),
        .more:hover:not(:disabled) {
          background: #f3f4f6;
        }
        .ghost:disabled,
        .more:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        .moreBox {
          margin-top: 12px;
          border-top: 1px dashed #e5e7eb;
          padding-top: 12px;
        }
        .btn {
          width: 100%;
          margin-top: 14px;
          background: #2563eb;
          color: #fff;
          font-size: 16px;
          font-weight: 800;
          padding: 11px 14px;
          border: none;
          border-radius: 12px;
          cursor: pointer;
          transition: background 0.2s;
        }
        .btn:hover:not(:disabled) {
          background: #1d4ed8;
        }
        .btn:disabled {
          background: #93c5fd;
          cursor: not-allowed;
        }
      `}</style>
    </form>
  );
}
