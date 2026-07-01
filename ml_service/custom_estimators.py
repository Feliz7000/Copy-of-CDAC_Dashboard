import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.class_weight import compute_sample_weight

class BalancedXGBClassifier(ClassifierMixin, BaseEstimator):
    def __init__(self, objective="multi:softprob", num_class=3, n_estimators=250, max_depth=4, 
                 learning_rate=0.08, subsample=0.9, colsample_bytree=0.9, random_state=42, 
                 n_jobs=1, eval_metric="logloss"):
        self.objective = objective
        self.num_class = num_class
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state
        self.n_jobs = n_jobs
        self.eval_metric = eval_metric
        self.model_ = None
        self.classes_ = None

    def fit(self, X, y, xgb_model=None):
        self.classes_ = np.unique(y)
        from xgboost import XGBClassifier
        from sklearn.preprocessing import LabelEncoder

        self.le_ = LabelEncoder()
        y_encoded = self.le_.fit_transform(y)
        n_classes = len(self.classes_)

        obj = self.objective
        nc = self.num_class
        if n_classes == 2:
            obj = "binary:logistic"
            nc = None
        else:
            obj = "multi:softprob"
            nc = n_classes

        kwargs = {
            "objective": obj,
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "learning_rate": self.learning_rate,
            "subsample": self.subsample,
            "colsample_bytree": self.colsample_bytree,
            "random_state": self.random_state,
            "n_jobs": self.n_jobs,
            "eval_metric": "logloss",
        }
        if nc is not None:
            kwargs["num_class"] = nc

        self.model_ = XGBClassifier(**kwargs)
        weights = compute_sample_weight("balanced", y_encoded)
        fit_kwargs = {"sample_weight": weights}
        if xgb_model is not None:
            fit_kwargs["xgb_model"] = xgb_model
        self.model_.fit(X, y_encoded, **fit_kwargs)
        return self

    def predict(self, X):
        preds = self.model_.predict(X)
        return self.le_.inverse_transform(preds)

    def predict_proba(self, X):
        return self.model_.predict_proba(X)
