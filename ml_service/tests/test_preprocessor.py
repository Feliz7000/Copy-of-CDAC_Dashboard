import numpy as np
import pandas as pd

from preprocessor import build_preprocessor, load_feature_list
from model_store import FEATURES_FILE


def test_build_preprocessor_shape():
    feature_cols = load_feature_list(str(FEATURES_FILE))
    assert feature_cols, "placement_feature_columns.txt must list features"

    rng = np.random.default_rng(42)
    n = 20
    data = {col: rng.random(n) for col in feature_cols[:10]}
    df = pd.DataFrame(data)

    selected = [c for c in feature_cols if c in df.columns]
    preprocessor, numeric_cols, _cat_cols = build_preprocessor(df, selected)
    preprocessor.fit(df[selected])

    transformed = preprocessor.transform(df[selected])
    assert transformed.shape[0] == n
    assert not np.isnan(transformed).any()
