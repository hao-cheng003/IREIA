from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

FORBIDDEN = {"TOTAL_VALUE_2025", "consideration", "y_residual"}


@dataclass
class BuiltFeatures:
    X_base: pd.DataFrame
    X_res: pd.DataFrame
    meta: Dict[str, Any]


def _to_num(v: Any) -> float:
    if v is None:
        return float("nan")
    if isinstance(v, (int, float, np.number)) and np.isfinite(v):
        return float(v)
    s = str(v).strip()
    if s == "" or s.lower() in {"nan", "none", "null"}:
        return float("nan")
    # remove thousand separators
    s = s.replace(",", "")
    try:
        return float(s)
    except Exception:
        return float("nan")


def _coerce_feature_types(df: pd.DataFrame, cat_cols: List[str]) -> pd.DataFrame:

    df = df.copy()

    # 1) categorical -> category, fill blanks
    for c in cat_cols:
        if c in df.columns:
            ser = df[c].astype("string")
            ser = ser.fillna("Unknown").replace({"": "Unknown"})
            df[c] = ser.astype("category")

    # 2) numeric: all non-cat columns -> to_numeric (commas removed)
    for c in df.columns:
        if c in cat_cols:
            continue
        if pd.api.types.is_bool_dtype(df[c]) or pd.api.types.is_numeric_dtype(df[c]):
            continue
        ser = df[c].astype("string").str.replace(",", "", regex=False)
        df[c] = pd.to_numeric(ser, errors="coerce")

    return df


def _apply_frontend_aliases(payload: Dict[str, Any]) -> Dict[str, Any]:

    p = dict(payload)

    # coords
    if "LATITUDE" not in p and "latitude" in p:
        p["LATITUDE"] = p.get("latitude")
    if "LONGITUDE" not in p and "longitude" in p:
        p["LONGITUDE"] = p.get("longitude")

    # areaSqft -> LIVING_AREA
    if "LIVING_AREA" not in p and "areaSqft" in p:
        p["LIVING_AREA"] = p.get("areaSqft")
    if "GROSS_AREA" not in p and "areaSqft" in p:
        p["GROSS_AREA"] = p.get("areaSqft")

    # lotSqft -> LAND_SF
    if "LAND_SF" not in p and "lotSqft" in p:
        p["LAND_SF"] = p.get("lotSqft")

    # bedrooms -> BED_RMS
    if "BED_RMS" not in p and "bedrooms" in p:
        p["BED_RMS"] = p.get("bedrooms")

    # bathrooms(float) -> FULL_BTH + HLF_BTH
    if ("FULL_BTH" not in p or "HLF_BTH" not in p) and "bathrooms" in p:
        b = _to_num(p.get("bathrooms"))
        if np.isfinite(b):
            full = int(np.floor(b + 1e-9))
            frac = b - full
            half = 1 if frac >= 0.49 else 0
            p.setdefault("FULL_BTH", full)
            p.setdefault("HLF_BTH", half)

    # builtYear -> YR_BUILT
    if "YR_BUILT" not in p and "builtYear" in p:
        p["YR_BUILT"] = p.get("builtYear")

    # parkingSpaces -> NUM_PARKING
    if "NUM_PARKING" not in p and "parkingSpaces" in p:
        p["NUM_PARKING"] = p.get("parkingSpaces")

    # renovated -> HAS_REMODEL (0/1)
    if "HAS_REMODEL" not in p and "renovated" in p:
        rv = p.get("renovated")
        if isinstance(rv, bool):
            p["HAS_REMODEL"] = 1 if rv else 0
        else:
            p["HAS_REMODEL"] = (
                1 if str(rv) in {"1", "true", "True", "yes", "YES"} else 0
            )

    return p


def build_features_for_models(
    payload: Dict[str, Any],
    baseline_features: List[str],
    residual_features: List[str],
    baseline_categoricals: List[str],
    residual_categoricals: List[str],
    default_sale_year: int = 2025,
    default_sale_month: Optional[int] = None,
) -> BuiltFeatures:

    p = _apply_frontend_aliases(payload)

    if default_sale_month is None:
        import datetime as _dt

        default_sale_month = _dt.datetime.now().month

    p.setdefault("sale_year", default_sale_year)
    p.setdefault("sale_month", default_sale_month)

    row: Dict[str, Any] = {}
    for k, v in p.items():
        if k in FORBIDDEN:
            continue
        row[k] = v

    base_cols = [c for c in baseline_features if c not in FORBIDDEN]
    res_cols = [c for c in residual_features if c not in FORBIDDEN]

    def _make_X(cols: List[str], cat_cols: List[str]) -> pd.DataFrame:
        d = {}
        for c in cols:
            if c in row:
                d[c] = row[c]
            else:
                d[c] = "Unknown" if c in cat_cols else np.nan
        X = pd.DataFrame([d], columns=cols)
        X = _coerce_feature_types(X, cat_cols)
        return X

    X_base = _make_X(base_cols, baseline_categoricals)
    X_res = _make_X(res_cols, residual_categoricals)

    meta = {
        "filled_sale_year": int(
            _to_num(p.get("sale_year"))
            if np.isfinite(_to_num(p.get("sale_year")))
            else default_sale_year
        ),
        "filled_sale_month": int(
            _to_num(p.get("sale_month"))
            if np.isfinite(_to_num(p.get("sale_month")))
            else default_sale_month
        ),
        "baseline_categoricals": baseline_categoricals,
        "residual_categoricals": residual_categoricals,
    }

    return BuiltFeatures(X_base=X_base, X_res=X_res, meta=meta)
