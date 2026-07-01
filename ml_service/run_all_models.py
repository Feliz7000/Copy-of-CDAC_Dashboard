"""Single-entry script for EDA + baseline modeling on placement data.

What it does:
- loads a CSV export from placement reports, falling back to parquet if needed
- derives a 3-class target for placement status
- prints EDA summary (shape, label balance, missingness, variance)
- trains Logistic Regression, Decision Tree, Random Forest, and XGBoost
- reports stratified CV metrics: accuracy, precision_macro, recall_macro, F1_macro, ROC-AUC OVR
- computes permutation importance for the Random Forest
- saves processed features and metrics under data/processed and ml_service/notebooks/outputs

Run (from repo root or ml_service/ — paths are package-relative):
    python ml_service/run_all_models.py --input data/raw/placement_Aug24.parquet

Incremental training:
    Each run merges new rows into artifacts/training_store.parquet (by PRN).
    If final_model.joblib exists, XGBoost continues from the prior booster;
    RF and LR refit on the full accumulated dataset.
"""

from __future__ import annotations

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.model_selection import RandomizedSearchCV
import sys
from pathlib import Path

_ML_ROOT = Path(__file__).resolve().parent
if str(_ML_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(_ML_ROOT.parent))
if str(_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(_ML_ROOT))

from sklearn.ensemble import VotingClassifier
import numpy as np
try:
    from ml_service.custom_estimators import BalancedXGBClassifier
except ImportError:
    from custom_estimators import BalancedXGBClassifier

import argparse
import json
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    make_scorer,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.base import clone
import joblib

try:
    from ml_service.preprocessor import build_preprocessor, load_feature_list
    from ml_service.model_store import (
        OUT_DIR,
        DATA_PROCESSED_DIR,
        DATA_RAW_DIR,
        FEATURES_FILE as DEFAULT_FEATURES_FILE,
        append_training_run,
        ensure_dirs,
        load_bundle,
        load_training_meta,
        load_training_store,
        merge_training_data,
        save_bundle,
        save_training_meta,
        save_training_store,
    )
except ImportError:
    from preprocessor import build_preprocessor, load_feature_list
    from model_store import (
        OUT_DIR,
        DATA_PROCESSED_DIR,
        DATA_RAW_DIR,
        FEATURES_FILE as DEFAULT_FEATURES_FILE,
        append_training_run,
        ensure_dirs,
        load_bundle,
        load_training_meta,
        load_training_store,
        merge_training_data,
        save_bundle,
        save_training_meta,
        save_training_store,
    )

try:
    from xgboost import XGBClassifier
except Exception:  # pragma: no cover - only used if xgboost is missing
    XGBClassifier = None


OUT_DIR.mkdir(parents=True, exist_ok=True)

PLACEMENT_LABEL_TO_CODE = {
    "not placement ready": 0,
    "not eligible": 0,
    "can improve": 1,
    "hold": 1,
    "placement ready": 2,
    "eligible": 2,
}
PLACEMENT_CODE_TO_LABEL = {
    0: "not placement ready",
    1: "can improve",
    2: "placement ready",
}


def load_input_frame(input_path: str) -> pd.DataFrame:
    path = Path(input_path)
    if not path.is_absolute():
        for base in (Path.cwd(), DATA_RAW_DIR.parent.parent, DATA_RAW_DIR.parent, DATA_RAW_DIR):
            candidate = base / path
            if candidate.exists():
                path = candidate
                break

    candidates = [path]

    if path.suffix.lower() == ".csv":
        candidates.append(path.with_suffix(".parquet"))
    elif path.suffix.lower() == ".parquet":
        candidates.append(path.with_suffix(".csv"))
    else:
        candidates.extend([path.with_suffix(".csv"), path.with_suffix(".parquet")])

    seen = set()
    for candidate in candidates:
        candidate_str = str(candidate)
        if candidate_str in seen:
            continue
        seen.add(candidate_str)
        if not candidate.exists():
            continue
        if candidate.suffix.lower() == ".csv":
            return pd.read_csv(candidate)
        if candidate.suffix.lower() == ".parquet":
            return pd.read_parquet(candidate)

    tried = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Input data not found. Tried: {tried}")

def normalize_placement_status(value: object) -> str:
    raw = str(value).strip().lower()
    aliases = {
        "placement ready": "placement ready",
        "can improve": "can improve",
        "not placement ready": "not placement ready",
        "np": "placement ready",
        "eligible": "placement ready",
        "hold": "can improve",
        "not eligible": "not placement ready",
    }
    if raw in aliases:
        return aliases[raw]
    # Fail fast so we detect bad upstream values immediately
    raise ValueError(
        f"Unexpected placement_status value: {value!r}. "
        "Expected one of: 'Placement ready', 'Can Improve', 'Not Placement Ready', 'Eligible', 'Hold', 'Not Eligible'."
    )


def derive_label(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Return encoded 3-class label and normalized text label.

    Encoding:
    0 -> Not placement ready
    1 -> can improve
    2 -> Placement ready
    """
    if "placement_status" in df.columns:
        label_text = df["placement_status"].map(normalize_placement_status)
        y = label_text.map(PLACEMENT_LABEL_TO_CODE).astype(int)
        return y, label_text

    # if "pass_fail" in df.columns:
    #     raise ValueError(
    #         "Deprecated target column 'pass_fail' detected. "
    #         "Please regenerate input data with 'placement_status' before training."
    #     )

    raise ValueError("No suitable target column found (expected placement_status)")


def build_feature_names_from_preprocessor(preprocessor, numeric_cols, cat_cols):
    # try to use sklearn convenience API
    try:
        names = preprocessor.get_feature_names_out()
        return list(names)
    except Exception:
        # fallback: numeric cols + OHE categories
        names = []
        names.extend(numeric_cols)
        try:
            ohe = preprocessor.named_transformers_["cat"].named_steps["ohe"]
            for col, cats in zip(cat_cols, ohe.categories_):
                for v in cats:
                    names.append(f"{col}__{v}")
        except Exception:
            # best-effort: append cat col names
            names.extend(cat_cols)
        return names


def save_eda_outputs(df: pd.DataFrame, y: pd.Series, numeric_cols: List[str]) -> Dict[str, object]:
    summary = {
        "rows": int(len(df)),
        "cols": int(len(df.columns)),
        "placement_status_counts": df["placement_status"].value_counts(dropna=False).to_dict() if "placement_status" in df.columns else {},
        "label_counts": y.value_counts(dropna=False).to_dict(),
        "missing_total": int(df.isna().sum().sum()),
        "numeric_cols": int(len(numeric_cols)),
    }

    missing = df.isna().sum().sort_values(ascending=False)
    missing.to_csv(OUT_DIR / "missing_counts.csv")

    variances = df[numeric_cols].var().sort_values(ascending=False) if numeric_cols else pd.Series(dtype=float)
    variances.to_csv(OUT_DIR / "numeric_variances.csv")

    corr_with_label = df[numeric_cols].corrwith(y).abs().sort_values(ascending=False) if numeric_cols else pd.Series(dtype=float)
    corr_with_label.to_csv(OUT_DIR / "corr_with_label.csv")

    stats = df[numeric_cols].describe().transpose() if numeric_cols else pd.DataFrame()
    stats.to_csv(OUT_DIR / "numeric_stats.csv")

    if not missing.empty:
        plt.figure(figsize=(10, 6))
        sns.barplot(x=missing.head(30).values, y=missing.head(30).index)
        plt.title("Top 30 missing columns")
        plt.xlabel("Missing count")
        plt.tight_layout()
        plt.savefig(OUT_DIR / "missing_top30.png")
        plt.close()

    for col in variances.head(10).index.tolist():
        plt.figure(figsize=(6, 4))
        sns.histplot(df[col].dropna(), bins=50, kde=True)
        plt.title(f"Distribution: {col}")
        plt.tight_layout()
        plt.savefig(OUT_DIR / f"hist_{col}.png")
        plt.close()

    return summary | {
        "missing": missing,
        "variances": variances,
        "corr_with_label": corr_with_label,
    }


def run_models(X_scaled: pd.DataFrame, y: pd.Series) -> Dict[str, Dict[str, float]]:
    min_class = int(y.value_counts().min())
    n_splits = min(5, min_class) if min_class >= 2 else 2
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    models = {
        "logreg": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "rf": RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1, class_weight="balanced"),
    }

    if XGBClassifier is not None:
        models["xgboost"] = BalancedXGBClassifier(
            objective="multi:softprob",
            num_class=3,
            n_estimators=250,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            n_jobs=1,
            eval_metric="logloss",
        )

    results: Dict[str, Dict[str, float]] = {}
    scoring = {
        "accuracy": "accuracy",
        "precision_macro": make_scorer(precision_score, average="macro", zero_division=0),
        "recall_macro": make_scorer(recall_score, average="macro", zero_division=0),
        "f1_macro": make_scorer(f1_score, average="macro", zero_division=0),
        "roc_auc": "roc_auc_ovr" if y.nunique() > 2 else "roc_auc",
    }
    for name, model in models.items():
        scores = cross_validate(
            model,
            X_scaled,
            y,
            cv=cv,
            scoring=scoring,
            error_score="raise",
        )
        results[name] = {k: round(float(v.mean()), 4) for k, v in scores.items() if k.startswith("test_")}

    return results


def run_models_holdout(X_scaled: pd.DataFrame, y: pd.Series, test_size: float = 0.2) -> Dict[str, Dict[str, float]]:
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=test_size, random_state=42, stratify=y)
    models = {
        "logreg": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "rf": RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1, class_weight="balanced"),
    }
    if XGBClassifier is not None:
        models["xgboost"] = BalancedXGBClassifier(
            objective="multi:softprob",
            num_class=3,
            n_estimators=250,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            n_jobs=1,
            eval_metric="logloss",
        )

    results: Dict[str, Dict[str, float]] = {}
    for name, model in models.items():
        m = clone(model)
        m.fit(X_train, y_train)
        y_pred = m.predict(X_test)
        y_proba = m.predict_proba(X_test) if hasattr(m, "predict_proba") else None
        results[name] = compute_multiclass_metrics(y_test, y_pred, y_proba)

    return results


def make_final_model(xgb_params=None):
    if XGBClassifier is not None:
        if xgb_params is None:
            xgb_params = dict(n_estimators=250, max_depth=4, learning_rate=0.08, subsample=0.9, colsample_bytree=0.9)
            
        xgb = BalancedXGBClassifier(
            objective="multi:softprob",
            num_class=3,
            eval_metric="logloss",
            random_state=42,
            n_jobs=1,
            **xgb_params
        )
        rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1, class_weight="balanced")
        lr = LogisticRegression(max_iter=1000, class_weight="balanced")
        
        return VotingClassifier(
            estimators=[("xgb", xgb), ("rf", rf), ("lr", lr)],
            voting="soft"
        )
    return RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1, class_weight="balanced")


def extract_xgb_booster(model) -> object | None:
    """Return an XGBoost booster from a prior VotingClassifier, if present."""
    if model is None:
        return None
    estimators = getattr(model, "named_estimators_", None)
    if not estimators:
        return None
    xgb_est = estimators.get("xgb")
    if xgb_est is None:
        return None
    inner = getattr(xgb_est, "model_", None)
    if inner is None:
        return None
    try:
        return inner.get_booster()
    except Exception:
        return None


def fit_ensemble(
    X_scaled,
    y: pd.Series,
    xgb_params: dict | None = None,
    prior_model=None,
    incremental: bool = False,
):
    """Fit soft-voting ensemble; XGBoost can continue from a prior booster."""
    xgb_params = dict(xgb_params or {})
    booster = None
    if incremental and prior_model is not None:
        booster = extract_xgb_booster(prior_model)
        if booster is not None:
            xgb_params["n_estimators"] = max(
                50,
                int(xgb_params.get("n_estimators", 250) // 3),
            )
            xgb_params["learning_rate"] = max(
                0.01,
                float(xgb_params.get("learning_rate", 0.08)) * 0.5,
            )

    if XGBClassifier is not None:
        xgb = BalancedXGBClassifier(
            objective="multi:softprob",
            num_class=3,
            eval_metric="logloss",
            random_state=42,
            n_jobs=1,
            **xgb_params,
        )
        xgb.fit(X_scaled, y, xgb_model=booster)
        rf = RandomForestClassifier(
            n_estimators=200, random_state=42, n_jobs=-1, class_weight="balanced",
        )
        rf.fit(X_scaled, y)
        lr = LogisticRegression(max_iter=1000, class_weight="balanced")
        lr.fit(X_scaled, y)

        ensemble = VotingClassifier(
            estimators=[("xgb", xgb), ("rf", rf), ("lr", lr)],
            voting="soft",
        )
        ensemble.estimators_ = np.array([xgb, rf, lr])
        ensemble.named_estimators_ = {"xgb": xgb, "rf": rf, "lr": lr}
        ensemble.classes_ = np.unique(y)
        ensemble.le_ = LabelEncoder().fit(ensemble.classes_)
        return ensemble, booster is not None

    rf = RandomForestClassifier(
        n_estimators=200, random_state=42, n_jobs=-1, class_weight="balanced",
    )
    rf.fit(X_scaled, y)
    return rf, False


def compute_multiclass_metrics(y_true, y_pred, y_proba=None) -> Dict[str, float]:
    out = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_macro": round(float(precision_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
    }
    if y_proba is not None:
        try:
            out["roc_auc_ovr"] = round(float(roc_auc_score(y_true, y_proba, multi_class="ovr", average="macro")), 4)
        except Exception:
            pass
    return out


def run_overfitting_diagnostics(X_scaled, y: pd.Series, meta_df: pd.DataFrame, mode: str = "cv", xgb_params: dict = None) -> Dict[str, object]:
    min_class = int(y.value_counts().min())
    n_splits = min(5, min_class) if min_class >= 2 else 2
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    base_model = make_final_model(xgb_params)

    oof_metrics = None
    oof_out = None
    if mode == "cv":
        # Out-of-fold predictions: each row predicted by a fold model that did not train on that row.
        oof_pred = cross_val_predict(clone(base_model), X_scaled, y, cv=cv, method="predict")
        oof_proba = None
        try:
            oof_proba = cross_val_predict(clone(base_model), X_scaled, y, cv=cv, method="predict_proba")
        except Exception:
            oof_proba = None

        oof_metrics = compute_multiclass_metrics(y, oof_pred, oof_proba)
        oof_df = meta_df.copy()
        oof_df["placement_status_true"] = y.values
        oof_df["placement_status_true_label"] = pd.Series(y).map(PLACEMENT_CODE_TO_LABEL).values
        oof_df["oof_pred_label"] = oof_pred
        oof_df["oof_pred_label_text"] = pd.Series(oof_pred).map(PLACEMENT_CODE_TO_LABEL).values
        if oof_proba is not None:
            oof_df["oof_pred_confidence"] = oof_proba.max(axis=1)
        oof_out = OUT_DIR / "oof_predictions_Aug24.csv"
        oof_df.to_csv(oof_out, index=False)

    # Holdout split metrics for explicit train-vs-test gap.
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )
    hold_model = make_final_model(xgb_params)
    hold_model.fit(X_train, y_train)

    y_train_pred = hold_model.predict(X_train)
    y_test_pred = hold_model.predict(X_test)
    y_train_proba = hold_model.predict_proba(X_train) if hasattr(hold_model, "predict_proba") else None
    y_test_proba = hold_model.predict_proba(X_test) if hasattr(hold_model, "predict_proba") else None

    train_metrics = compute_multiclass_metrics(y_train, y_train_pred, y_train_proba)
    test_metrics = compute_multiclass_metrics(y_test, y_test_pred, y_test_proba)

    metric_gap = {}
    for k, v in train_metrics.items():
        if k in test_metrics:
            metric_gap[f"{k}_gap_train_minus_test"] = round(float(v - test_metrics[k]), 4)

    labels = sorted(PLACEMENT_CODE_TO_LABEL.keys())
    cm = confusion_matrix(y_test, y_test_pred, labels=labels)
    cm_df = pd.DataFrame(
        cm,
        index=[f"true_{PLACEMENT_CODE_TO_LABEL[l]}" for l in labels],
        columns=[f"pred_{PLACEMENT_CODE_TO_LABEL[l]}" for l in labels],
    )
    cm_df.to_csv(OUT_DIR / "confusion_matrix_test.csv")

    plt.figure(figsize=(8, 6))
    sns.heatmap(cm_df, annot=True, fmt="d", cmap="Blues")
    plt.title("Holdout Test Confusion Matrix")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "confusion_matrix_test.png")
    plt.close()

    report = {
        "cv_folds": n_splits,
        "oof_metrics": oof_metrics,
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
        "train_minus_test_gap": metric_gap,
        "oof_predictions_file": str(oof_out),
        "confusion_matrix_file": str(OUT_DIR / "confusion_matrix_test.csv"),
    }
    with open(OUT_DIR / "overfitting_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


def train_from_dataframe(
    df: pd.DataFrame,
    features_file: str | None = None,
    *,
    incremental: bool = True,
    source_batch: str | None = None,
    force_retrain: bool = False,
) -> dict:
    ensure_dirs()
    sns.set(style="whitegrid")

    prior_bundle = load_bundle() if incremental else None
    prior_meta = load_training_meta() if incremental else {"runs": [], "best_xgb_params": None}
    existing_store = load_training_store() if incremental else None

    if incremental:
        df, merge_stats = merge_training_data(existing_store, df)
        print(
            f"Incremental merge: {merge_stats['previous_total']} prior → "
            f"+{merge_stats['added_prns']} new, {merge_stats['updated_prns']} updated → "
            f"{merge_stats['total']} total"
        )
    else:
        merge_stats = {
            "previous_total": 0,
            "new_records": len(df),
            "updated_prns": 0,
            "added_prns": len(df),
            "total": len(df),
        }

    save_training_store(df)

    print("Rows:", len(df), "Cols:", len(df.columns))
    if features_file is None and DEFAULT_FEATURES_FILE.exists():
        features_file = str(DEFAULT_FEATURES_FILE)
    feature_cols = load_feature_list(features_file)
    if not feature_cols:
        raise ValueError(f"No feature list provided. Create or pass --features-file (default expected at {DEFAULT_FEATURES_FILE})")

    y, y_text = derive_label(df)
    drop_cols = [c for c in ["placement_status", "pass_fail", "prn", "student_full_name", "batch_name"] if c in df.columns]

    selected = [c for c in feature_cols if c in df.columns]
    missing_requested = [c for c in feature_cols if c not in df.columns]
    if missing_requested:
        print(f"Warning: {len(missing_requested)} requested columns were not found in input and will be skipped.")
    if not selected:
        raise ValueError("None of the requested features exist in input data")

    print(f"Using feature subset from {features_file}: {len(selected)} available columns")
    X = df[selected].copy()
    preprocessor, numeric_cols, cat_cols = build_preprocessor(X, selected)
    preprocessor.fit(X)
    X_scaled = preprocessor.transform(X)
    feature_names = build_feature_names_from_preprocessor(preprocessor, numeric_cols, cat_cols)

    ml_raw_df = X.copy()
    ml_raw_df["placement_status"] = y.values
    ml_raw_df["placement_status_label"] = y_text.values
    out_proc = DATA_PROCESSED_DIR
    out_proc.mkdir(parents=True, exist_ok=True)
    raw_out = out_proc / "placement_training_ml_raw.csv"
    try:
        ml_raw_df.to_csv(raw_out, index=False)
        print("Saved raw ML CSV to", raw_out)
    except PermissionError:
        print(f"Warning: Could not save {raw_out}, file is probably open in another program.")

    actual_numeric = [c for c in numeric_cols if c in ml_raw_df.columns]
    summary = save_eda_outputs(ml_raw_df.drop(columns=["placement_status_label"], errors="ignore"), y, actual_numeric)

    print("Label distribution:\n", y.value_counts(normalize=True).to_string())
    print("Top missing columns:\n", summary["missing"].head(20).to_string())
    print(f"Numeric columns: {len(numeric_cols)}")
    print("Top features correlated with label:\n", summary["corr_with_label"].head(20).to_string())

    # save processed features as CSV (construct DF if we have names)
    try:
        proc_df = pd.DataFrame(X_scaled, columns=feature_names)
    except Exception:
        proc_df = pd.DataFrame(X_scaled)
    proc_df["placement_status"] = y.values
    proc_df["placement_status_label"] = y_text.values
    try:
        proc_df.to_csv(out_proc / "placement_training_features.csv", index=False)
        print("Saved processed CSV to", out_proc / "placement_training_features.csv")
    except PermissionError:
        print(
            "Warning: Could not save placement_training_features.csv, "
            "file is probably open in another program."
        )

    if y.nunique() < 2:
        print("Skipping model training: target has a single class.")
        return {}

    # Evaluation mode: CV (default) or holdout (80/20 stratified)
    import os
    eval_method = os.environ.get("ML_EVAL_METHOD", "cv")
    metrics = {}
    if eval_method == "cv":
        metrics = run_models(X_scaled, y)
    else:
        metrics = run_models_holdout(X_scaled, y)
    for name, metric_values in metrics.items():
        print(f"{name} CV results:", metric_values)
    # imp_df = None
    # if len(feature_names) <= 60:
    #     imp_df = run_permutation_importance(X_scaled, y, feature_names)
    #     print("Top permutation features:\n", imp_df.head(15).to_string(index=False))
    # else:
    #     print(f"Skipping permutation importance for {len(feature_names)} features; enable it later on a smaller subset.")

    with open(OUT_DIR / "model_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    meta_df = df.loc[:, [c for c in ("prn", "student_full_name") if c in df.columns]].copy()

    print("Tuning XGBoost hyperparameters...")
    reuse_params = (
        incremental
        and not force_retrain
        and prior_meta.get("best_xgb_params")
        and prior_bundle is not None
    )

    if reuse_params:
        best_xgb_params = prior_meta["best_xgb_params"]
        print("Reusing saved XGBoost params (incremental run):", best_xgb_params)
    else:
        from sklearn.preprocessing import LabelEncoder
        le_tune = LabelEncoder()
        y_tune = le_tune.fit_transform(y)
        n_tune_classes = len(np.unique(y_tune))

        xgb_obj = "binary:logistic" if n_tune_classes == 2 else "multi:softprob"
        xgb_nc = None if n_tune_classes == 2 else n_tune_classes

        weights = compute_sample_weight("balanced", y_tune)
        xgb_kwargs = {"objective": xgb_obj, "eval_metric": "logloss", "random_state": 42, "n_jobs": 1}
        if xgb_nc is not None:
            xgb_kwargs["num_class"] = xgb_nc

        xgb_base = XGBClassifier(**xgb_kwargs)
        param_dist = {
            "n_estimators": [100, 200, 300],
            "max_depth": [3, 4, 5, 6],
            "learning_rate": [0.01, 0.05, 0.1],
            "subsample": [0.7, 0.8, 0.9, 1.0],
        }
        search = RandomizedSearchCV(
            xgb_base,
            param_distributions=param_dist,
            n_iter=5,
            cv=2,
            scoring="f1_macro",
            random_state=42,
            n_jobs=1,
        )
        search.fit(X_scaled, y_tune, sample_weight=weights)
        best_xgb_params = search.best_params_
        print("Best XGBoost params:", best_xgb_params)
    
    # produce diagnostics according to evaluation choice

    if eval_method == "cv":
        overfit_report = run_overfitting_diagnostics(X_scaled, y, meta_df, mode="cv", xgb_params=best_xgb_params)
        print("Overfitting diagnostics (train vs test):")
        print(json.dumps({
            "oof_metrics": overfit_report.get("oof_metrics"),
            "train_metrics": overfit_report.get("train_metrics"),
            "test_metrics": overfit_report.get("test_metrics"),
            "train_minus_test_gap": overfit_report.get("train_minus_test_gap"),
        }, indent=2))
    else:
        # run holdout diagnostics only (train/test gap)
        hold_report = run_overfitting_diagnostics(X_scaled, y, meta_df, mode="holdout", xgb_params=best_xgb_params)
        print("Holdout diagnostics:")
        print(json.dumps({
            "train_metrics": hold_report.get("train_metrics"),
            "test_metrics": hold_report.get("test_metrics"),
            "train_minus_test_gap": hold_report.get("train_minus_test_gap"),
        }, indent=2))

    # Train final ensemble on full accumulated data
    xgb_continued = False
    try:
        prior_model = prior_bundle.get("model") if prior_bundle else None
        final_model, xgb_continued = fit_ensemble(
            X_scaled,
            y,
            xgb_params=best_xgb_params,
            prior_model=prior_model,
            incremental=incremental and prior_bundle is not None,
        )

        prob_matrix = final_model.predict_proba(X_scaled)
        preds = final_model.predict(X_scaled)
        pred_conf = prob_matrix.max(axis=1)
        pred_df = df.loc[:, [c for c in ("prn", "student_full_name") if c in df.columns]].copy()
        pred_df["placement_status_true"] = y.values
        pred_df["placement_status_true_label"] = y_text.values
        pred_df["pred_proba"] = pred_conf
        pred_df["pred_label"] = preds
        pred_df["pred_placement_status_label"] = pd.Series(preds).map(PLACEMENT_CODE_TO_LABEL).values
        pred_out = OUT_DIR / "predictions_latest.csv"
        pred_df.to_csv(pred_out, index=False)
        print("Saved predictions to:", pred_out)
        print(pred_df.head(10).to_string())

        bundle = {
            "model": final_model,
            "preprocessor": preprocessor,
            "feature_names": feature_names,
            "selected_raw_columns": selected,
            "label_map": PLACEMENT_LABEL_TO_CODE,
            "best_xgb_params": best_xgb_params,
        }
        model_path = save_bundle(bundle)
        print("Saved trained model to:", model_path)
        if xgb_continued:
            print("XGBoost continued from prior booster (incremental refinement).")
    except Exception as e:
        print("Warning: could not produce final predictions:", e)
        raise

    print("EDA + modeling complete. Outputs in:", OUT_DIR)

    result = {
        "mode": "incremental" if incremental and prior_bundle else "fresh",
        "merge_stats": merge_stats,
        "xgb_continued": xgb_continued,
        "metrics": metrics,
        "overfitting_report": overfit_report if eval_method == "cv" else hold_report,
        "best_xgb_params": best_xgb_params,
    }

    meta = load_training_meta()
    meta["best_xgb_params"] = best_xgb_params
    meta = append_training_run(
        meta,
        merge_stats=merge_stats,
        incremental=incremental and prior_bundle is not None,
        source_batch=source_batch,
        metrics={"eval_method": eval_method, "xgb_continued": xgb_continued},
    )
    save_training_meta(meta)

    return result


def main(
    input_path: str,
    features_file: str | None = None,
    *,
    incremental: bool = True,
    force_retrain: bool = False,
) -> None:
    print("Loading:", input_path)
    df = load_input_frame(input_path)
    train_from_dataframe(
        df,
        features_file,
        incremental=incremental,
        force_retrain=force_retrain,
    )


if __name__ == "__main__":
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DATA_RAW_DIR / "placement_Feb25_corrected_updated.csv"))
    parser.add_argument(
        "--features-file",
        default=None,
        help="Optional newline-delimited list of raw input columns to train on",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore accumulated training store and prior model (train from scratch)",
    )
    parser.add_argument(
        "--force-retrain",
        action="store_true",
        help="Re-run hyperparameter search even when a prior model exists",
    )
    parser.add_argument(
        "--eval-method",
        choices=["cv", "holdout"],
        default="cv",
        help="Evaluation method: cv (default) or holdout",
    )
    args = parser.parse_args()
    os.environ["ML_EVAL_METHOD"] = args.eval_method
    main(
        args.input,
        args.features_file,
        incremental=not args.fresh,
        force_retrain=args.force_retrain,
    )