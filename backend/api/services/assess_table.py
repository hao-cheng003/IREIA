from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd


@dataclass
class AssessTable:
    df: pd.DataFrame
    lat: np.ndarray
    lng: np.ndarray
    cols: List[str]

    @classmethod
    def load(cls, csv_path: str, usecols: List[str]) -> "AssessTable":
        p = Path(csv_path)
        if not p.exists():
            raise FileNotFoundError(f"Assess table not found: {p}")

        df = pd.read_csv(p, usecols=usecols, low_memory=False)

        df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
        df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")

        df = df.dropna(subset=["LATITUDE", "LONGITUDE"]).reset_index(drop=True)

        lat = df["LATITUDE"].to_numpy(dtype=np.float32)
        lng = df["LONGITUDE"].to_numpy(dtype=np.float32)
        df0 = pd.read_csv(p, nrows=0)
        available = set(df0.columns)
        usecols = [c for c in usecols if c in available]
        df = pd.read_csv(p, usecols=usecols, low_memory=False)

        return cls(df=df, lat=lat, lng=lng, cols=usecols)

    def nearest_row_dict(self, lat: float, lng: float) -> Dict[str, Any]:

        lat0 = np.float32(lat)
        lng0 = np.float32(lng)
        d2 = (self.lat - lat0) ** 2 + (self.lng - lng0) ** 2
        idx = int(np.argmin(d2))
        row = self.df.iloc[idx]
        out = {}
        for k in row.index:
            v = row[k]
            if pd.isna(v):
                out[k] = None
            elif isinstance(v, (np.generic,)):
                out[k] = v.item()
            else:
                out[k] = v
        out["_nearest_idx"] = idx
        out["_nearest_d2"] = float(d2[idx])
        return out
