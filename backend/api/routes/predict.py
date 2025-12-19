from typing import Any, Dict, Optional

import numpy as np
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from api.utils.geo_guard import ensure_in_boston

router = APIRouter()


def to01(v: Any) -> Optional[int]:
    if v is None:
        return None
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (int, float)):
        return 1 if float(v) != 0 else 0
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("1", "true", "yes", "y", "t"):
            return 1
        if s in ("0", "false", "no", "n", "f", ""):
            return 0
    return None


def json_safe(x: Any) -> Any:

    if x is None:
        return None
    if isinstance(x, (str, int, float, bool)):
        return x

    if isinstance(x, np.generic):
        return x.item()

    if isinstance(x, np.ndarray):
        return x.tolist()

    if isinstance(x, dict):
        return {str(k): json_safe(v) for k, v in x.items()}

    if isinstance(x, (list, tuple, set)):
        return [json_safe(v) for v in x]

    try:
        return str(x)
    except Exception:
        return None


class PredictRequest(BaseModel):
    latitude: float
    longitude: float

    areaSqft: Optional[float] = None
    lotSqft: Optional[float] = None
    bedrooms: Optional[float] = None
    bathrooms: Optional[float] = None
    builtYear: Optional[int] = None
    propertyType: Optional[Any] = None

    renovated: Optional[Any] = None
    parking: Optional[Any] = None
    parkingSpaces: Optional[int] = None

    sale_year: Optional[int] = None
    sale_month: Optional[int] = None

    class Config:
        extra = "allow"


@router.post("/predict")
def predict(req: PredictRequest, request: Request) -> Dict[str, Any]:
    ensure_in_boston(req.latitude, req.longitude)

    store = getattr(request.app.state, "model_store", None)
    table = getattr(request.app.state, "assess_table", None)
    if store is None or table is None:
        raise HTTPException(
            status_code=500, detail="Server not ready: model/table not loaded"
        )

    if not hasattr(store, "predict"):
        raise HTTPException(status_code=500, detail="ModelStore.predict() not found")

    payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()

    if "renovated" in payload:
        norm = to01(payload.get("renovated"))
        if norm is not None:
            payload["renovated"] = norm
        else:
            payload.pop("renovated", None)

    out = store.predict(payload, table)

    if isinstance(out, dict):
        slat = out.get("snappedLat", None)
        slng = out.get("snappedLng", None)
        if slat is not None and slng is not None:
            ensure_in_boston(float(slat), float(slng))

    return json_safe(out)
