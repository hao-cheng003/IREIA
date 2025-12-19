from __future__ import annotations

from typing import Any, Dict, List, Set

FORBIDDEN = {"TOTAL_VALUE_2025", "consideration", "y_residual"}


def enrich_payload_from_nearest(
    user_payload: Dict[str, Any],
    nearest_row: Dict[str, Any],
    allowed_keys: List[str],
) -> Dict[str, Any]:

    out = dict(user_payload)
    allowed: Set[str] = set(allowed_keys) - FORBIDDEN

    for k in allowed:
        if k in out and out[k] not in (None, "", "NaN"):
            continue

        v = nearest_row.get(k, None)
        if v is None:
            continue
        out[k] = v

    return out
