# ML Service

Placement prediction API (`/ml/predict-placement/`) and incremental training (`/ml/train/`).

## Artifacts (single canonical location)

All runtime files live under `ml_service/artifacts/`:

| File | Purpose |
|------|---------|
| `final_model.joblib` | Production bundle: model + preprocessor + feature list |
| `training_store.parquet` | Accumulated labeled training rows (merged by PRN) |
| `training_meta.json` | Run history and saved XGBoost hyperparameters |

Notebook outputs: `ml_service/notebooks/outputs/`

## Training

**Incremental (default)** — each run:

1. Merges new rows into `training_store.parquet` (same PRN → newer row wins)
2. Trains on the **full accumulated dataset**
3. **Continues XGBoost** from the prior booster when `final_model.joblib` exists
4. Refits Random Forest and Logistic Regression on the full data
5. Reuses saved hyperparameters (skips slow tuning unless `--force-retrain`)

```bash
# CLI — add a new CSV batch incrementally
python ml_service/run_all_models.py --input ml_service/data/raw/your_batch.csv

# Train from scratch (ignore store + prior model)
python ml_service/run_all_models.py --input ... --fresh

# Re-tune hyperparameters on incremental run
python ml_service/run_all_models.py --input ... --force-retrain
```

**API** (`POST /ml/train/`): upload labels CSV + `batch_name` for features.  
Form fields: `fresh=false` (default), `force_retrain=false`.

## Serving

```bash
cd ml_service
uvicorn main:app --host 0.0.0.0 --port 8001
```

Docker Compose mounts `./ml_service` → `/app`; artifacts path is `/app/artifacts/final_model.joblib`.
