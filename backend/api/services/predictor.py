from __future__ import annotations

import numpy as np

from api.services.enricher import enrich_payload_from_nearest
from api.services.feature_builder import build_features_for_models


def predict_prices(store, assess_table, payload: dict) -> dict:
    lat = payload.get("latitude") or payload.get("LATITUDE")
    lng = payload.get("longitude") or payload.get("LONGITUDE")
    if lat is None or lng is None:
        raise ValueError("latitude/longitude is required")

    nearest = assess_table.nearest_row_dict(float(lat), float(lng))
    allow_keys = list(set(store.baseline_features) | set(store.residual_features))
    enriched = enrich_payload_from_nearest(payload, nearest, allow_keys)

    built = build_features_for_models(
        payload=enriched,
        baseline_features=store.baseline_features,
        residual_features=store.residual_features,
        baseline_categoricals=store.baseline_categoricals,
        residual_categoricals=store.residual_categoricals,
        default_sale_year=2025,
    )

    log1p_assess = float(store.baseline.predict(built.X_base)[0])
    assess_price = float(np.expm1(log1p_assess))

    r = float(store.residual.predict(built.X_res)[0])
    final_price = float(assess_price * np.exp(r))

    trend = {
        "assess_year": 2025,
        "long_term_log_trend": float(nearest.get("long_term_log_trend") or 0.0),
        "trend_5yr_norm": float(nearest.get("trend_5yr_norm") or 0.0),
        "long_term_norm": float(nearest.get("long_term_norm") or 0.0),
    }

    return {
        "assess_price": assess_price,
        "residual": r,
        "final_price": final_price,
        "trend": trend,
        "meta": {
            **built.meta,
            "nearest_idx": nearest.get("_nearest_idx"),
            "nearest_d2": nearest.get("_nearest_d2"),
        },
    }
