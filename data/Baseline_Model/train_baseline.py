import os
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import lightgbm as lgb


# =========================
# 配置
# =========================
DATA_FILE = "final_table_12.csv"   # 你的输入文件（含 label）
TARGET = "TOTAL_VALUE_2025"               # 目标列
DROP_COLS = ["PID"]                       # 如果存在 PID，就丢掉

CATEGORICAL_COLS = [
    "CITY",
    "ZIP_CODE",
    "INT_COND",
    "EXT_COND",
    "OVERALL_COND",
    "AC_TYPE",
    "HEAT_CLASS",
]

# label 处理
USE_LOG1P_Y = True

# label 截尾（处理长尾极端值污染 RMSE）
USE_LABEL_CAP = True
LABEL_CAP_Q = 0.999   # 可改：0.995 / 0.999 / 0.9995

# 输出
OUT_MODEL = "lgbm_model.txt"
OUT_IMPORTANCE = "feature_importance.csv"

RANDOM_SEED = 42


# =========================
# 工具函数
# =========================
def rmse(y_true, y_pred) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def clean_numeric_with_commas(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """
    把可能含千分位逗号的数值列从 object/string 转为 float。
    例如 "5,000" -> 5000
    """
    for c in cols:
        if c in df.columns:
            if df[c].dtype == "object":
                s = df[c].astype(str).str.strip()
                s = s.str.replace(",", "", regex=False)
                s = s.replace({"": np.nan, "nan": np.nan, "None": np.nan})
                df[c] = pd.to_numeric(s, errors="coerce")
            else:
                df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def assert_no_bad_object_columns(X: pd.DataFrame, cat_cols: list[str]) -> None:
    bad = [col for col, dt in X.dtypes.items() if dt == "object" and col not in cat_cols]
    if bad:
        raise ValueError(
            f"Found non-categorical object columns: {bad}\n"
            f"Fix: convert these columns to numeric (remove commas) or to category."
        )


# =========================
# 主流程
# =========================
def main():
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"Cannot find {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    # 1) 删除 ID 列（如果存在）
    for c in DROP_COLS:
        if c in df.columns:
            df = df.drop(columns=[c])

    # 2) 确认 label 存在
    if TARGET not in df.columns:
        raise ValueError(
            f"TARGET column '{TARGET}' not found in data. Columns: {list(df.columns)[:50]} ..."
        )

    # 3) 清理带逗号的数值列（修复 LAND_SF object / label 逗号等）
    df = clean_numeric_with_commas(df, ["LAND_SF", "GROSS_AREA", "LIVING_AREA", TARGET])

    # 4) 删除无效 label（保险：>0）
    before = len(df)
    df = df.dropna(subset=[TARGET]).copy()
    df = df[df[TARGET] > 0].copy()
    after = len(df)
    print(f"[data] rows: {before} -> {after} (after dropping invalid labels)")

    # 5) label 截尾 cap（处理长尾）
    if USE_LABEL_CAP:
        cap = float(df[TARGET].quantile(LABEL_CAP_Q))
        df[TARGET] = df[TARGET].clip(upper=cap)
        print(f"[cap] enabled: q={LABEL_CAP_Q}  upper_cap={cap:,.0f}")

    # 6) 类别列转 category
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            df[col] = df[col].astype("category")

    # 7) 特征/标签
    y = df[TARGET].astype(float)
    X = df.drop(columns=[TARGET])

    # 8) 检查是否还存在“坏的 object 列”
    cat_feats = [c for c in CATEGORICAL_COLS if c in X.columns]
    assert_no_bad_object_columns(X, cat_feats)

    # 9) train/val split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED
    )

    # 10) y transform
    if USE_LOG1P_Y:
        y_train_fit = np.log1p(y_train)
        y_val_fit = np.log1p(y_val)
    else:
        y_train_fit = y_train
        y_val_fit = y_val

    # 11) Dataset
    dtrain = lgb.Dataset(
        X_train, label=y_train_fit, categorical_feature=cat_feats, free_raw_data=False
    )
    dval = lgb.Dataset(
        X_val, label=y_val_fit, categorical_feature=cat_feats, reference=dtrain, free_raw_data=False
    )

    # 12) 参数（更强正则，减少你之前那种 train/val gap）
    params = {
        "objective": "regression",
        "metric": "rmse",
        "learning_rate": 0.03,
        "num_leaves": 31,
        "min_data_in_leaf": 200,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "lambda_l2": 5.0,
        "lambda_l1": 1.0,
        "verbosity": -1,
        "seed": RANDOM_SEED,
    }

    # 13) 训练
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

    # 14) 预测（log空间）
    pred_val_fit = model.predict(X_val, num_iteration=model.best_iteration)

    # 15) 反变换（回到原尺度）
    if USE_LOG1P_Y:
        pred_val = np.expm1(pred_val_fit)
    else:
        pred_val = pred_val_fit

    # 16) 评估（原尺度）
    mae = float(mean_absolute_error(y_val, pred_val))
    rmse_v = rmse(y_val, pred_val)
    r2 = float(r2_score(y_val, pred_val))

    print("\n===== Evaluation (VAL, original scale) =====")
    print(f"MAE : {mae:,.2f}")
    print(f"RMSE: {rmse_v:,.2f}")
    print(f"R^2 : {r2:.4f}")
    print("Best iteration:", model.best_iteration)

    # 17) 评估（log1p 空间，与你训练 metric 一致）
    if USE_LOG1P_Y:
        rmse_log = float(np.sqrt(mean_squared_error(np.log1p(y_val), np.log1p(pred_val))))
        mae_log = float(mean_absolute_error(np.log1p(y_val), np.log1p(pred_val)))
        print("\n===== Evaluation (VAL, log1p scale) =====")
        print(f"MAE (log1p) : {mae_log:.6f}")
        print(f"RMSE(log1p) : {rmse_log:.6f}")

    # 18) 保存模型
    model.save_model(OUT_MODEL)
    print(f"\n✅ Saved model: {OUT_MODEL}")

    # 19) 特征重要性
    imp = pd.DataFrame({
        "feature": model.feature_name(),
        "importance_gain": model.feature_importance(importance_type="gain"),
        "importance_split": model.feature_importance(importance_type="split"),
    }).sort_values("importance_gain", ascending=False)

    imp.to_csv(OUT_IMPORTANCE, index=False)
    print(f"✅ Saved feature importance: {OUT_IMPORTANCE}")

    print("\nTop 20 features by gain:")
    print(imp.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
