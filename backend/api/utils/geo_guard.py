from fastapi import HTTPException

BOSTON_BBOX = {
    "lat_min": 42.2279,
    "lat_max": 42.3995,
    "lng_min": -71.1912,
    "lng_max": -70.9860,
}


def ensure_in_boston(lat: float, lng: float) -> None:
    try:
        lat = float(lat)
        lng = float(lng)
    except Exception:
        raise HTTPException(status_code=400, detail="目前只支持Boston地区")

    ok = (
        BOSTON_BBOX["lat_min"] <= lat <= BOSTON_BBOX["lat_max"]
        and BOSTON_BBOX["lng_min"] <= lng <= BOSTON_BBOX["lng_max"]
    )
    if not ok:
        raise HTTPException(status_code=400, detail="目前只支持Boston地区")
