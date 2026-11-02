from __future__ import annotations

import logging
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    RandomForestClassifier,
    StackingClassifier,
    GradientBoostingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from .config import IMPORTANCE_PATH, METRICS_PATH, MODEL_PATH, STACKING_MODEL_PATH

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=UserWarning)


def _build_base_models() -> dict[str, object]:
    return {
        "LogisticRegression": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(max_iter=2000, random_state=42, class_weight="balanced")),
            ]
        ),
        "DecisionTree": DecisionTreeClassifier(
            max_depth=6,
            min_samples_split=20,
            min_samples_leaf=10,
            class_weight="balanced",
            random_state=42,
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=150,
            max_depth=8,
            min_samples_split=15,
            min_samples_leaf=8,
            class_weight="balanced",
            random_state=42,
            n_jobs=1,
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            min_samples_split=20,
            min_samples_leaf=10,
            subsample=0.8,
            random_state=42,
        ),
        "XGBoost": XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=1,
            random_state=42,
            use_label_encoder=False,
            eval_metric="logloss",
            verbosity=0,
            n_jobs=1,
        ),
        "LightGBM": LGBMClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_samples=20,
            class_weight="balanced",
            random_state=42,
            n_jobs=1,
            verbose=-1,
        ),
    }


def _build_param_grids() -> dict[str, dict]:
    return {
        "LogisticRegression": {
            "model__C": [0.01, 0.1, 1.0, 10.0],
            "model__solver": ["liblinear"],
        },
        "DecisionTree": {
            "max_depth": [3, 5, 8],
            "min_samples_split": [10, 30],
            "min_samples_leaf": [5, 15],
        },
        "RandomForest": {
            "n_estimators": [100, 200],
            "max_depth": [6, 10],
            "min_samples_split": [10, 20],
        },
        "GradientBoosting": {
            "n_estimators": [80, 150],
            "max_depth": [3, 5],
            "learning_rate": [0.05, 0.1],
        },
        "XGBoost": {
            "n_estimators": [80, 150],
            "max_depth": [3, 5],
            "learning_rate": [0.05, 0.1],
        },
        "LightGBM": {
            "n_estimators": [80, 150],
            "max_depth": [3, 5],
            "learning_rate": [0.05, 0.1],
        },
    }


def train_and_evaluate_models(
    x_train: pd.DataFrame,
    x_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    enable_grid_search: bool = True,
) -> tuple[pd.DataFrame, str, dict[str, object]]:
    logger.info("开始多模型训练与评估（深度挖掘模式）...")
    logger.info("训练集: %d 样本, 测试集: %d 样本", len(x_train), len(x_test))
    logger.info("训练集流失率: %.2f%%", y_train.mean() * 100)

    base_models = _build_base_models()
    param_grids = _build_param_grids()
    cv = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)

    metrics: list[dict] = []
    trained_models: dict[str, object] = {}
    best_scores: dict[str, float] = {}

    for name, model in base_models.items():
        logger.info("训练 %s ...", name)

        if enable_grid_search and name in param_grids:
            try:
                grid = GridSearchCV(
                    model,
                    param_grids[name],
                    cv=cv,
                    scoring="f1",
                    n_jobs=1,
                    verbose=0,
                )
                grid.fit(x_train, y_train)
                best_model = grid.best_estimator_
                logger.info("%s 最优参数: %s", name, grid.best_params_)
            except Exception as exc:
                logger.warning("%s GridSearch 失败: %s，使用默认参数", name, exc)
                model.fit(x_train, y_train)
                best_model = model
        else:
            model.fit(x_train, y_train)
            best_model = model

        predictions = best_model.predict(x_test)
        try:
            probabilities = best_model.predict_proba(x_test)[:, 1]
        except Exception:
            probabilities = predictions.astype(float)

        metric = {
            "model": name,
            "accuracy": round(accuracy_score(y_test, predictions), 4),
            "precision": round(precision_score(y_test, predictions, zero_division=0), 4),
            "recall": round(recall_score(y_test, predictions, zero_division=0), 4),
            "f1_score": round(f1_score(y_test, predictions, zero_division=0), 4),
            "roc_auc": round(roc_auc_score(y_test, probabilities), 4),
        }
        metrics.append(metric)
        trained_models[name] = best_model
        best_scores[name] = metric["f1_score"]
        logger.info("%s 完成: F1=%.4f, AUC=%.4f", name, metric["f1_score"], metric["roc_auc"])

    metrics_df = pd.DataFrame(metrics).sort_values(["f1_score", "roc_auc"], ascending=False).reset_index(drop=True)
    best_model_name = str(metrics_df.iloc[0]["model"])

    logger.info("构建 Stacking 集成模型...")
    top_models = metrics_df.head(4)["model"].tolist()
    stacking_estimators = [
        (name.lower().replace(" ", "_"), trained_models[name])
        for name in top_models
        if name in trained_models
    ]

    if len(stacking_estimators) >= 2:
        stacking = StackingClassifier(
            estimators=stacking_estimators,
            final_estimator=LogisticRegression(max_iter=1000, random_state=42),
            cv=2,
            n_jobs=1,
        )
        stacking.fit(x_train, y_train)
        stack_pred = stacking.predict(x_test)
        try:
            stack_prob = stacking.predict_proba(x_test)[:, 1]
        except Exception:
            stack_prob = stack_pred.astype(float)

        stack_metric = {
            "model": "StackingEnsemble",
            "accuracy": round(accuracy_score(y_test, stack_pred), 4),
            "precision": round(precision_score(y_test, stack_pred, zero_division=0), 4),
            "recall": round(recall_score(y_test, stack_pred, zero_division=0), 4),
            "f1_score": round(f1_score(y_test, stack_pred, zero_division=0), 4),
            "roc_auc": round(roc_auc_score(y_test, stack_prob), 4),
        }

        if stack_metric["f1_score"] > best_scores.get(best_model_name, 0):
            best_model_name = "StackingEnsemble"
            trained_models["StackingEnsemble"] = stacking
            logger.info("Stacking 集成优于最佳单模型，采用集成模型")

        metrics_df = pd.concat([metrics_df, pd.DataFrame([stack_metric])], ignore_index=True)
        metrics_df = metrics_df.sort_values(["f1_score", "roc_auc"], ascending=False).reset_index(drop=True)

    best_model = trained_models[best_model_name]

    metrics_df.to_csv(METRICS_PATH, index=False)
    _save_feature_importance(best_model_name, best_model, x_train.columns)
    joblib.dump({"model": best_model, "feature_columns": list(x_train.columns)}, MODEL_PATH)

    if "StackingEnsemble" in trained_models:
        joblib.dump(
            {"model": trained_models["StackingEnsemble"], "feature_columns": list(x_train.columns)},
            STACKING_MODEL_PATH,
        )

    logger.info("最佳模型: %s", best_model_name)
    return metrics_df, best_model_name, trained_models


def _save_feature_importance(model_name: str, model, feature_columns: pd.Index) -> None:
    try:
        if model_name == "LogisticRegression":
            if hasattr(model, "named_steps"):
                importance = np.abs(model.named_steps["model"].coef_[0])
            else:
                importance = np.abs(model.coef_[0])
        elif model_name == "StackingEnsemble":
            importance = np.ones(len(feature_columns))
            logger.info("Stacking 集成模型使用均匀权重作为特征重要性占位")
        elif hasattr(model, "feature_importances_"):
            importance = model.feature_importances_
        elif hasattr(model, "named_steps") and hasattr(model.named_steps.get("model", None), "feature_importances_"):
            importance = model.named_steps["model"].feature_importances_
        else:
            importance = np.ones(len(feature_columns))

        importance_df = pd.DataFrame(
            {"feature": list(feature_columns), "importance": importance}
        ).sort_values("importance", ascending=False)
        importance_df.to_csv(IMPORTANCE_PATH, index=False)
        logger.info("特征重要性已保存，Top 5: %s", importance_df.head(5)["feature"].tolist())
    except Exception as exc:
        logger.warning("特征重要性提取失败: %s", exc)
