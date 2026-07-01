"""Paths and persistence for ML artifacts and accumulated training data."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

ML_ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ML_ROOT / "artifacts"
OUT_DIR = ML_ROOT / "notebooks" / "outputs"
DATA_PROCESSED_DIR = ML_ROOT / "data" / "processed"
DATA_RAW_DIR = ML_ROOT / "data" / "raw"

FINAL_MODEL_PATH = ARTIFACTS_DIR / "final_model.joblib"
TRAINING_STORE_PATH = ARTIFACTS_DIR / "training_store.parquet"
TRAINING_META_PATH = ARTIFACTS_DIR / "training_meta.json"
FEATURES_FILE = ML_ROOT / "placement_feature_columns.txt"


def ensure_dirs() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_bundle() -> dict[str, Any] | None:
    if not FINAL_MODEL_PATH.exists():
        return None
    return joblib.load(FINAL_MODEL_PATH)


def save_bundle(bundle: dict[str, Any]) -> Path:
    ensure_dirs()
    joblib.dump(bundle, FINAL_MODEL_PATH)
    return FINAL_MODEL_PATH


def load_training_store() -> pd.DataFrame | None:
    if not TRAINING_STORE_PATH.exists():
        return None
    return pd.read_parquet(TRAINING_STORE_PATH)


def save_training_store(df: pd.DataFrame) -> Path:
    ensure_dirs()
    df.to_parquet(TRAINING_STORE_PATH, index=False)
    return TRAINING_STORE_PATH


def load_training_meta() -> dict[str, Any]:
    if not TRAINING_META_PATH.exists():
        return {"runs": [], "best_xgb_params": None, "total_samples": 0}
    with open(TRAINING_META_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_training_meta(meta: dict[str, Any]) -> Path:
    ensure_dirs()
    with open(TRAINING_META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    return TRAINING_META_PATH


def merge_training_data(
    existing: pd.DataFrame | None,
    new: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Merge by PRN; newer rows replace older labels/features for the same student."""
    new_df = new.copy()
    if "prn" not in new_df.columns:
        raise ValueError("Training data must include a 'prn' column")

    new_df["prn"] = new_df["prn"].astype(str).str.strip()

    if existing is None or existing.empty:
        stats = {
            "previous_total": 0,
            "new_records": len(new_df),
            "updated_prns": 0,
            "added_prns": len(new_df),
            "total": len(new_df),
        }
        return new_df, stats

    old_df = existing.copy()
    old_df["prn"] = old_df["prn"].astype(str).str.strip()

    previous_total = len(old_df)
    overlap = set(old_df["prn"]) & set(new_df["prn"])
    old_df = old_df[~old_df["prn"].isin(new_df["prn"])]

    merged = pd.concat([old_df, new_df], ignore_index=True)
    stats = {
        "previous_total": previous_total,
        "new_records": len(new_df),
        "updated_prns": len(overlap),
        "added_prns": len(new_df) - len(overlap),
        "total": len(merged),
    }
    return merged, stats


def append_training_run(
    meta: dict[str, Any],
    *,
    merge_stats: dict[str, int],
    incremental: bool,
    source_batch: str | None,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    run = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "incremental" if incremental else "fresh",
        "source_batch": source_batch,
        "merge_stats": merge_stats,
        "metrics_summary": metrics,
    }
    runs = meta.get("runs", [])
    runs.append(run)
    meta["runs"] = runs[-50:]
    meta["total_samples"] = merge_stats.get("total", 0)
    meta["last_run"] = run
    return meta
