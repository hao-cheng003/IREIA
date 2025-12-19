from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.health import router as health_router
from api.routes.predict import router as predict_router
from api.services.assess_table import AssessTable
from api.services.model_store import ModelStore

app = FastAPI(title="IREA V3 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(predict_router, prefix="/api")


@app.on_event("startup")
def _startup():
    root = Path(__file__).resolve().parent

    # 1) load models
    store = ModelStore(
        baseline_path=str(root / "models" / "baseline_lgb.txt"),
        residual_path=str(root / "models" / "residual_lgb.txt"),
    )
    app.state.model_store = store
    print("[INFO] ModelStore loaded")

    # 2) load assess master table (final_table_12.csv)
    need_cols = set(["PID", "LATITUDE", "LONGITUDE"])
    need_cols.update(store.baseline_features)
    need_cols.update(store.residual_features)

    need_cols.discard("sale_year")
    need_cols.discard("sale_month")

    csv_path = root / "models" / "final_table_12.csv"
    app.state.assess_table = AssessTable.load(str(csv_path), usecols=sorted(need_cols))
    print(
        f"[INFO] AssessTable loaded: {csv_path} | rows={len(app.state.assess_table.df)}"
    )
