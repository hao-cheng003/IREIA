const BASE = (
  process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

async function handle(r: Response, url: string): Promise<unknown> {
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText} — ${url}`;
    try {
      const text = await r.text();
      if (text) msg = `${msg} — ${text.slice(0, 400)}`;
    } catch {}
    throw new Error(msg);
  }
  return r.json();
}

function withTimeout(ms = 12000) {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), ms);
  return { signal: ctl.signal, done: () => clearTimeout(t) };
}


export async function apiPredict(
  payload: Record<string, unknown>,
): Promise<{
  predictedPrice: number;
  finalPrice: number;
  assessPrice?: number;
  residual?: number;
  snappedLat?: number;
  snappedLng?: number;
  modelVersion?: string;
  meta?: Record<string, unknown>;
  trend?: unknown;
}> {
  const url = `${BASE}/api/predict`;
  const t = withTimeout(60000);

  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: t.signal,
    });

    const raw = await handle(r, url);

    const j = (raw ?? {}) as Record<string, unknown>;

    const finalPrice = Number(
      (j["final_price"] ??
        j["finalPrice"] ??
        j["predictedPrice"] ??
        j["estimatedPrice"] ??
        j["price"] ??
        0) as unknown,
    );

    const assessPrice =
      (j["assess_price"] ?? j["assessPrice"]) as number | undefined;

    const residual = j["residual"] as number | undefined;

    const snappedLat =
      (j["snappedLat"] ??
        j["snapped_lat"] ??
        j["lat"] ??
        payload["latitude"]) as number | undefined;

    const snappedLng =
      (j["snappedLng"] ??
        j["snapped_lng"] ??
        j["lng"] ??
        payload["longitude"]) as number | undefined;

    const modelVersion =
      (j["modelVersion"] ??
        j["modelName"] ??
        j["model"]) as string | undefined;

    const meta = j["meta"] as Record<string, unknown> | undefined;
    const trend = j["trend"];

    return {
      predictedPrice: finalPrice,
      finalPrice,
      assessPrice,
      residual,
      snappedLat,
      snappedLng,
      modelVersion: modelVersion ?? "IREA_V3",
      meta,
      trend,
    };
  } finally {
    t.done();
  }
}

export async function apiHealth(): Promise<unknown> {
  const url = `${BASE}/health`;
  const t = withTimeout(6000);
  try {
    return await handle(await fetch(url, { signal: t.signal }), url);
  } finally {
    t.done();
  }
}
