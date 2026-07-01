"""
Re-save final_model.joblib with the current sklearn version (refits preprocessor only).
Run from the ml_service directory:
    python resave_model.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import joblib
import numpy as np
import pandas as pd
import sklearn
from model_store import DATA_RAW_DIR, FINAL_MODEL_PATH, load_bundle, save_bundle

print(f"Running with sklearn {sklearn.__version__}")

bundle = load_bundle()
if bundle is None:
    print(f"ERROR: No model at {FINAL_MODEL_PATH}")
    sys.exit(1)

model = bundle["model"]
preprocessor = bundle["preprocessor"]
selected_raw_columns = bundle["selected_raw_columns"]
feature_names = bundle.get("feature_names", [])
label_map = bundle.get("label_map", {})
best_xgb_params = bundle.get("best_xgb_params")

print(f"Loaded. selected_raw_columns count: {len(selected_raw_columns)}")

csv_options = [
    DATA_RAW_DIR / "placement_Feb25_corrected_updated.csv",
    Path(__file__).resolve().parent.parent / "backend" / "ml_inputs" / "prediction_input_Feb-25_all.csv",
]

df_raw = None
for path in csv_options:
    if path.exists():
        print(f"Using data from: {path}")
        df_raw = pd.read_csv(path)
        break

if df_raw is None:
    print("ERROR: No training CSV found. Tried:")
    for path in csv_options:
        print(f"  {path}")
    sys.exit(1)

features_dict = {}
for col in selected_raw_columns:
    if col in df_raw.columns:
        features_dict[col] = pd.to_numeric(df_raw[col], errors="coerce")
    else:
        features_dict[col] = pd.Series(np.nan, index=df_raw.index)

X = pd.DataFrame(features_dict, index=df_raw.index)

print("Re-fitting preprocessor with current sklearn...")
preprocessor.fit(X)
print("Preprocessor re-fitted successfully.")

new_bundle = {
    "model": model,
    "preprocessor": preprocessor,
    "selected_raw_columns": selected_raw_columns,
    "feature_names": feature_names,
    "label_map": label_map,
    "best_xgb_params": best_xgb_params,
}

print(f"Saving updated bundle to {FINAL_MODEL_PATH} ...")
save_bundle(new_bundle)
print("Done! Model re-saved with sklearn", sklearn.__version__)
