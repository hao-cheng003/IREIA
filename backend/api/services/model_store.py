# backend/api/services/model_store.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd

BASELINE_CATEGORICALS = [
    "CITY",
    "ZIP_CODE",
    "INT_COND",
    "EXT_COND",
    "OVERALL_COND",
    "AC_TYPE",
    "HEAT_CLASS",
]

RESIDUAL_CATEGORICALS = [
    "CITY",
    "ZIP_CODE",
    "INT_COND",
    "EXT_COND",
    "OVERALL_COND",
    "AC_TYPE",
    "HEAT_CLASS",
]

ASSESS_VALUE_CANDIDATES = [
    "TOTAL_VALUE_2025",
    "TOTAL_VALUE",
    "AV_TOTAL",
    "TOTAL_VAL",
]


def _safe_float(x: Any) -> Optional[float]:
    try:
        v = float(x)
        if np.isfinite(v):
            return v
        return None
    except Exception:
        return None


def _nearest_row_by_latlng(
    df: pd.DataFrame, lat: float, lng: float
) -> Tuple[int, float]:
    lat_arr = pd.to_numeric(df["LATITUDE"], errors="coerce").to_numpy(dtype=float)
    lng_arr = pd.to_numeric(df["LONGITUDE"], errors="coerce").to_numpy(dtype=float)

    bad = ~np.isfinite(lat_arr) | ~np.isfinite(lng_arr)
    lat_arr[bad] = 1e9
    lng_arr[bad] = 1e9

    d2 = (lat_arr - lat) ** 2 + (lng_arr - lng) ** 2
    idx = int(np.argmin(d2))
    return idx, float(d2[idx])


def _to_one_row_frame(row: pd.Series, feature_names: List[str]) -> pd.DataFrame:
    data = {}
    for c in feature_names:
        data[c] = row[c] if c in row.index else np.nan
    return pd.DataFrame([data], columns=feature_names)


def _sanitize_for_lgbm(X: pd.DataFrame, categoricals: List[str]) -> pd.DataFrame:
    X = X.copy()

    # categorical -> category
    for c in categoricals:
        if c in X.columns:
            X[c] = X[c].astype("category")

    # others -> numeric
    for c in X.columns:
        if c in categoricals:
            continue
        if X[c].dtype == "object" or str(X[c].dtype).startswith("string"):
            X[c] = pd.to_numeric(X[c], errors="coerce")
        if not (
            pd.api.types.is_integer_dtype(X[c])
            or pd.api.types.is_float_dtype(X[c])
            or pd.api.types.is_bool_dtype(X[c])
        ):
            X[c] = pd.to_numeric(X[c], errors="coerce")

    return X


def _pick_assess_from_row(row: pd.Series) -> Optional[float]:
    for col in ASSESS_VALUE_CANDIDATES:
        if col in row.index:
            v = _safe_float(row.get(col))
            if v is not None and v > 0:
                return v
    return None


def _baseline_to_usd(baseline_pred: float, row_assess: Optional[float]) -> float:

    if row_assess is not None and row_assess > 0:
        cand_log = float(np.exp(baseline_pred))
        cand_raw = float(baseline_pred)

        if abs(cand_log - row_assess) < abs(cand_raw - row_assess):
            return cand_log
        return cand_raw

    if baseline_pred < 1000:
        return float(np.exp(baseline_pred))

    return float(baseline_pred)


class ModelStore:
    def __init__(self, baseline_path: str, residual_path: str):
        self.baseline = lgb.Booster(model_file=baseline_path)
        self.residual = lgb.Booster(model_file=residual_path)

        self.baseline_features = self.baseline.feature_name()
        self.residual_features = self.residual.feature_name()

        self.baseline_categoricals = [
            c for c in BASELINE_CATEGORICALS if c in self.baseline_features
        ]
        self.residual_categoricals = [
            c for c in RESIDUAL_CATEGORICALS if c in self.residual_features
        ]

    def predict(self, payload: Dict[str, Any], assess_table: Any) -> Dict[str, Any]:
        df = getattr(assess_table, "df", None)
        if df is None or not hasattr(df, "__len__"):
            raise RuntimeError("AssessTable.df not found")

        lat = _safe_float(payload.get("latitude"))
        lng = _safe_float(payload.get("longitude"))
        if lat is None or lng is None:
            raise RuntimeError("latitude/longitude missing")

        row_i, d2 = _nearest_row_by_latlng(df, lat, lng)
        row = df.iloc[row_i]

        snapped_lat = _safe_float(row.get("LATITUDE")) or lat
        snapped_lng = _safe_float(row.get("LONGITUDE")) or lng

        row_assess = _pick_assess_from_row(row)

        Xb = _to_one_row_frame(row, self.baseline_features)
        Xb = _sanitize_for_lgbm(Xb, self.baseline_categoricals)
        baseline_pred = float(self.baseline.predict(Xb)[0])

        if row_assess is not None and row_assess > 0:
            assess_price = float(row_assess)
            assess_source = "table"
        else:
            assess_price = _baseline_to_usd(baseline_pred, None)
            assess_source = "baseline"

        Xr = _to_one_row_frame(row, self.residual_features)
        Xr = _sanitize_for_lgbm(Xr, self.residual_categoricals)
        residual_pred = float(self.residual.predict(Xr)[0])  # log residual

        final_price = float(assess_price * np.exp(residual_pred))

        trend = {}
        for k in [
            "assess_year",
            "long_term_log_trend",
            "trend_5yr_norm",
            "long_term_norm",
        ]:
            if k in row.index:
                v = row.get(k)
                fv = _safe_float(v)
                trend[k] = fv if fv is not None else v
        if not trend:
            trend = None

        return {
            "predictedPrice": final_price,
            "finalPrice": final_price,
            "assessPrice": float(assess_price),
            "residual": float(residual_pred),
            "snappedLat": float(snapped_lat),
            "snappedLng": float(snapped_lng),
            "modelVersion": "baseline+residual(lgbm)",
            "trend": trend,
            "meta": {
                "assess_source": assess_source,
                "baseline_raw_pred": baseline_pred,
                "row_assess": row_assess,
                "nearest_row_index": int(row_i),
                "nearest_d2": float(d2),
                "pid": row.get("PID", None) if "PID" in row.index else None,
            },
        }
