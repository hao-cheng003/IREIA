from pathlib import Path

import lightgbm as lgb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend/api/models/final_table_12.csv"
OUT = ROOT / "backend/api/models/assess_infer.parquet"


baseline = lgb.Booster(model_file=str(ROOT / "backend/api/models/baseline_lgb.txt"))
residual = lgb.Booster(model_file=str(ROOT / "backend/api/models/residual_lgb.txt"))

need_cols = set(["PID", "LATITUDE", "LONGITUDE"])
need_cols |= set(baseline.feature_name())
need_cols |= set(residual.feature_name())

print(f"Need {len(need_cols)} columns")

df = pd.read_csv(SRC, usecols=list(need_cols), low_memory=False)

df.to_parquet(OUT, index=False)
print(f"Saved inference table to {OUT}, shape={df.shape}")
