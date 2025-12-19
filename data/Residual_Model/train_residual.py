import os
import json
import numpy as np
import pandas as pd
from pathlib import Path

import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error

DATA_PATH = "train_residual.csv"

TARGET = "y_residual"
ID_COL = "PID"

DROP_COLS = [
    ID_COL,
    "consideration",
    "TOTAL_VALUE_2025",
]

USE_TRIM = True

TRIM_RANGE = (-1.5, 1.5)

USE_WINSOR = False
WINSOR_Q = (0.01, 0.99)

SEED = 42
TEST_SIZE = 0.2

OUT_DIR = "lgb_residual_output"
MODEL_PATH = os.path.join(OUT_DIR, "lgb_residual.txt")
FEAT_IMP_PATH = os.path.join(OUT_DIR, "feature_importance.csv")
METRICS_PATH = os.path.join(OUT_DIR, "metrics.json")

def rmse(y_true, y_pred):
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))

def safe_to_category(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype("category")
    return df

def build_X_y(df: pd.DataFrame):
    if TARGET not in df.columns:
        raise ValueError(f"Missing target column: {TARGET}")

    feature_cols = [c for c in df.columns if c not in ([TARGET] + DROP_COLS)]
    X = df[feature_cols].copy()
    y = df[TARGET].astype(float).copy()
    return X, y, feature_cols

def maybe_trim(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if USE_WINSOR:
        lo = out[TARGET].quantile(WINSOR_Q[0])
        hi = out[TARGET].quantile(WINSOR_Q[1])
        out[TARGET] = out[TARGET].clip(lower=lo, upper=hi)
        return out

    if USE_TRIM:
        lo, hi = TRIM_RANGE
        out = out[out[TARGET].between(lo, hi)].copy()
        return out

    return out


def main():
    Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH)

    if ID_COL not in df.columns:
        raise ValueError(f"Missing ID column: {ID_COL}")
    if TARGET not in df.columns:
        raise ValueError(f"Missing target column: {TARGET}")

    print("[Loaded]", df.shape)
    print(df[TARGET].describe())


    df2 = maybe_trim(df)
    print("[After trim/winsor]" , df2.shape)
    print(df2[TARGET].describe())

    cat_cols = []
    for c in ["CITY", "ZIP_CODE", "INT_COND", "EXT_COND", "OVERALL_COND", "AC_TYPE", "HEAT_CLASS"]:
        if c in df2.columns:
            cat_cols.append(c)
    df2 = safe_to_category(df2, cat_cols)

    X, y, feature_cols = build_X_y(df2)


    for c in feature_cols:
        if X[c].dtype.name not in ["category", "bool"]:
            X[c] = pd.to_numeric(X[c], errors="coerce")

    X_train, X_val, y_train, y_val = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=SEED
    )

    dtrain = lgb.Dataset(X_train, label=y_train, categorical_feature=cat_cols, free_raw_data=False)
    dval = lgb.Dataset(X_val, label=y_val, categorical_feature=cat_cols, reference=dtrain, free_raw_data=False)

    params = {
        "objective": "regression",
        "metric": "rmse",
        "boosting_type": "gbdt",

        "learning_rate": 0.03,
        "num_leaves": 63,
        "min_data_in_leaf": 20,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.9,
        "bagging_freq": 1,
        "lambda_l2": 1.0,

        "verbosity": -1,
        "seed": SEED,
    }

    print("[Training] cat_cols =", cat_cols)

    model = lgb.train(
        params,
        dtrain,
        num_boost_round=5000,
        valid_sets=[dtrain, dval],
        valid_names=["train", "val"],
        callbacks=[
            lgb.early_stopping(stopping_rounds=200),
            lgb.log_evaluation(period=100),
        ],
    )

    pred_val = model.predict(X_val, num_iteration=model.best_iteration)
    val_rmse = rmse(y_val, pred_val)
    val_mae = float(mean_absolute_error(y_val, pred_val))

    metrics = {
        "data_path": DATA_PATH,
        "n_rows_loaded": int(df.shape[0]),
        "n_rows_used": int(df2.shape[0]),
        "use_trim": USE_TRIM,
        "trim_range": TRIM_RANGE,
        "use_winsor": USE_WINSOR,
        "winsor_q": WINSOR_Q,
        "best_iteration": int(model.best_iteration),
        "val_rmse": val_rmse,
        "val_mae": val_mae,
        "cat_cols": cat_cols,
    }

    print("[Val] RMSE =", val_rmse)
    print("[Val] MAE  =", val_mae)

    model.save_model(MODEL_PATH)
    print("[Saved model]", MODEL_PATH)

    fi = pd.DataFrame({
        "feature": feature_cols,
        "importance_gain": model.feature_importance(importance_type="gain"),
        "importance_split": model.feature_importance(importance_type="split"),
    }).sort_values("importance_gain", ascending=False)

    fi.to_csv(FEAT_IMP_PATH, index=False)
    print("[Saved feat importance]", FEAT_IMP_PATH)

    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print("[Saved metrics]", METRICS_PATH)


if __name__ == "__main__":
    main()
