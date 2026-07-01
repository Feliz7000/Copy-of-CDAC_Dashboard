"""Build, fit, save, and validate a ColumnTransformer preprocessor for placement data.

Usage:
    python preprocessor.py --input data/raw/placement_Aug24.parquet
"""
from pathlib import Path
import argparse
from typing import Iterable, List, Optional
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
import joblib

from model_store import ARTIFACTS_DIR, ensure_dirs


def load_feature_list(features_file: Optional[str]) -> List[str]:
    if not features_file:
        return []
    path = Path(features_file)
    if not path.exists():
        raise FileNotFoundError(f"Features file not found: {path}")
    features = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]
    return features


from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np
import warnings

class CategoryMeanTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, prefixes=None):
        if prefixes is None:
            prefixes = ["cc_", "ia_", "ap_", "sx_", "ps_", "gr_", "ta_", "na_", "in_", "as_", "pq_", "gac_", "prj_"]
        self.prefixes = prefixes
        self.feature_names_out_ = None
        
    def fit(self, X, y=None):
        return self
        
    def transform(self, X):
        X_out = X.copy()
        if not isinstance(X_out, pd.DataFrame):
            return X_out
            
        new_cols = {}
        for prefix in self.prefixes:
            cols = [c for c in X_out.columns if c.startswith(prefix)]
            if cols:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    new_cols[f"{prefix}mean"] = np.nanmean(X_out[cols].values, axis=1)
                    
        if new_cols:
            new_df = pd.DataFrame(new_cols, index=X_out.index)
            X_out = pd.concat([X_out, new_df], axis=1)
        self.feature_names_out_ = X_out.columns.tolist()
        return X_out

def build_preprocessor(df: pd.DataFrame, feature_cols: Optional[Iterable[str]] = None):
    feature_set = set(feature_cols) if feature_cols else None
    if feature_set is not None:
        df = df.loc[:, [c for c in df.columns if c in feature_set or c in {"placement_status", "pass_fail", "prn", "student_full_name", "batch_name"}]].copy()

    # numeric columns
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    prefixes = ["cc_", "ia_", "ap_", "sx_", "ps_", "gr_", "ta_", "na_", "in_", "as_", "pq_", "gac_", "prj_"]
    for prefix in prefixes:
        cols = [c for c in df.columns if c.startswith(prefix)]
        if cols:
            numeric_cols.append(f"{prefix}mean")

    # categorical columns: string/categorical excluding identifiers and target cols
    exclude = {"prn", "student_full_name", "batch_name", "placement_status", "pass_fail"}
    cat_cols = [c for c in df.select_dtypes(include=["object", "category"]).columns.tolist() if c not in exclude]

    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    # handle sklearn API differences for OneHotEncoder (sparse vs sparse_output)
    try:
        ohe = OneHotEncoder(handle_unknown="ignore", sparse=False)
    except TypeError:
        ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="__MISSING__")),
        ("ohe", ohe),
    ])

    col_transformer = ColumnTransformer([
        ("num", num_pipeline, numeric_cols),
        ("cat", cat_pipeline, cat_cols),
    ], remainder="drop")

    preprocessor = Pipeline([
        ("category_mean", CategoryMeanTransformer(prefixes)),
        ("column_transformer", col_transformer)
    ])

    return preprocessor, numeric_cols, cat_cols


def fit_and_save(input_path: str, out_path: str, features_file: Optional[str] = None):
    p = Path(input_path)
    if not p.exists():
        raise FileNotFoundError(f"Input parquet not found: {p}")
    df = pd.read_parquet(p)
    feature_cols = load_feature_list(features_file)

    preprocessor, numeric_cols, cat_cols = build_preprocessor(df, feature_cols or None)
    # fit
    preprocessor.fit(df)

    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"preprocessor": preprocessor, "numeric_cols": numeric_cols, "cat_cols": cat_cols}, outp)
    print("Saved preprocessor to:", outp)

    # quick validation: transform first 10 rows and assert no NaNs
    sample = df.head(10)
    import numpy as np
    transformed = np.asarray(preprocessor.transform(sample))
    if np.isnan(transformed).any():
        print("Warning: transformed output contains NaNs")
    else:
        print("Validation: transformed output contains no NaNs. Shape:", transformed.shape)

    return outp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/placement_Feb25_corrected_updated.csv")
    parser.add_argument("--out", default=str(ARTIFACTS_DIR / "preprocessor_only.joblib"))
    parser.add_argument("--features-file", default=None, help="Optional newline-delimited list of input feature columns")
    args = parser.parse_args()
    fit_and_save(args.input, args.out, args.features_file)
