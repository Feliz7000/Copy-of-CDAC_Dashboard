"""Data extraction and preprocessing pipeline for placement ML.

Functions:
- extract_placement(batch_name, out_path): fetch placement rows via API or DB and save parquet
- build_preprocessing_pipeline(feature_cols): returns scikit-learn ColumnTransformer for numeric/categorical
- preprocess_dataframe(df, pipeline=None, fit=False): apply pipeline to dataframe
"""
from typing import List, Optional, Tuple
import os
import pandas as pd
import numpy as np
import joblib


def extract_placement_from_parquet(in_path: str) -> pd.DataFrame:
    return pd.read_parquet(in_path)


def save_parquet(df: pd.DataFrame, out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_parquet(out_path, index=False)


def numeric_columns_from_df(df: pd.DataFrame) -> List[str]:
    return df.select_dtypes(include=["number"]).columns.tolist()


def categorical_columns_from_df(df: pd.DataFrame) -> List[str]:
    return df.select_dtypes(include=["object", "category"]).columns.tolist()


from sklearn.base import BaseEstimator, TransformerMixin
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

def build_preprocessing_pipeline(numeric_cols: List[str], categorical_cols: List[str]):
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from sklearn.compose import ColumnTransformer

    prefixes = ["cc_", "ia_", "ap_", "sx_", "ps_", "gr_", "ta_", "na_", "in_", "as_", "pq_", "gac_", "prj_"]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse=False)),
        ]
    )

    col_transformer = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_cols),
            ("cat", categorical_transformer, categorical_cols),
        ],
        remainder="drop",
    )
    
    preprocessor = Pipeline([
        ("category_mean", CategoryMeanTransformer(prefixes)),
        ("column_transformer", col_transformer)
    ])
    return preprocessor


def preprocess_dataframe(df: pd.DataFrame, pipeline=None, fit=False) -> Tuple[pd.DataFrame, Optional[object]]:
    """Apply preprocessing pipeline. If fit=True and pipeline given, fit_transform and return fitted pipeline.
    If pipeline is None and fit=True, build a pipeline from df types.
    Returns transformed DataFrame and the pipeline object (if fit or provided).
    """
    if pipeline is None and fit:
        numeric_cols = numeric_columns_from_df(df)
        categorical_cols = [c for c in categorical_columns_from_df(df) if c not in ["placement_status", "prn"]]
        pipeline = build_preprocessing_pipeline(numeric_cols, categorical_cols)

    if pipeline is None:
        raise ValueError("pipeline must be provided or fit=True to infer one")

    arr = pipeline.fit_transform(df) if fit else pipeline.transform(df)

    # Construct column names for transformed output (approximate)
    num_cols = pipeline.transformers_[0][2]
    cat_cols = pipeline.transformers_[1][2]
    # OneHotEncoder categories
    ohe = pipeline.named_transformers_["cat"].named_steps["onehot"]
    cat_feature_names = []
    for i, cats in enumerate(ohe.categories_):
        orig = cat_cols[i]
        cat_feature_names.extend([f"{orig}__{v}" for v in cats])

    feature_names = list(num_cols) + cat_feature_names
    out_df = pd.DataFrame(arr, columns=feature_names)
    return out_df, pipeline
