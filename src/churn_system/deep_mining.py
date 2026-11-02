from __future__ import annotations

import logging
import importlib.util
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
    confusion_matrix,
    classification_report,
)
from sklearn.model_selection import (
    cross_val_score,
    StratifiedKFold,
    learning_curve,
    validation_curve,
)
from sklearn.preprocessing import StandardScaler

from .config import CLUSTER_PATH, DEEP_MINING_DIR, SHAP_PATH

logger = logging.getLogger(__name__)

sns.set_theme(style="whitegrid")


def perform_clustering(
    features: pd.DataFrame,
    n_clusters_range: tuple[int, int] = (3, 8),
    random_state: int = 42,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    logger.info("开始客户聚类分群分析...")

    numeric_features = features.select_dtypes(include=[np.number])
    scaler = StandardScaler()
    scaled = scaler.fit_transform(numeric_features)

    cluster_metrics: list[dict[str, Any]] = []
    for k in range(n_clusters_range[0], n_clusters_range[1] + 1):
        kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = kmeans.fit_predict(scaled)
        cluster_metrics.append(
            {
                "n_clusters": k,
                "inertia": kmeans.inertia_,
                "silhouette": silhouette_score(scaled, labels),
                "davies_bouldin": davies_bouldin_score(scaled, labels),
                "calinski_harabasz": calinski_harabasz_score(scaled, labels),
            }
        )

    metrics_df = pd.DataFrame(cluster_metrics)
    best_k = metrics_df.sort_values("silhouette", ascending=False).iloc[0]["n_clusters"]
    best_k = int(best_k)

    best_kmeans = KMeans(n_clusters=best_k, random_state=random_state, n_init=10)
    cluster_labels = best_kmeans.fit_predict(scaled)

    features_with_clusters = features.copy()
    features_with_clusters["cluster"] = cluster_labels

    _plot_cluster_analysis(scaled, cluster_labels, best_k, metrics_df)

    cluster_profiles = _build_cluster_profiles(features_with_clusters, best_k)
    features_with_clusters.to_csv(CLUSTER_PATH, index=False, encoding="utf-8-sig")

    result = {
        "best_k": best_k,
        "metrics": metrics_df,
        "profiles": cluster_profiles,
        "cluster_labels": cluster_labels,
    }
    logger.info("聚类分析完成，最优簇数: %d，轮廓系数: %.4f", best_k, metrics_df.iloc[best_k - n_clusters_range[0]]["silhouette"])
    return features_with_clusters, result


def _plot_cluster_analysis(
    scaled_data: np.ndarray,
    labels: np.ndarray,
    n_clusters: int,
    metrics_df: pd.DataFrame,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    pca = PCA(n_components=2, random_state=42)
    pca_result = pca.fit_transform(scaled_data)
    scatter_df = pd.DataFrame({"PC1": pca_result[:, 0], "PC2": pca_result[:, 1], "cluster": labels.astype(str)})
    sns.scatterplot(
        data=scatter_df,
        x="PC1",
        y="PC2",
        hue="cluster",
        palette="Set2",
        alpha=0.7,
        ax=axes[0, 0],
    )
    axes[0, 0].set_title(f"PCA 降维可视化 (K={n_clusters})")
    axes[0, 0].legend(title="分群", loc="best")

    axes[0, 1].plot(metrics_df["n_clusters"], metrics_df["inertia"], "o-", color="#2c7fb8", linewidth=2)
    axes[0, 1].set_title("肘部法则 - 惯性值")
    axes[0, 1].set_xlabel("簇数 K")
    axes[0, 1].set_ylabel("惯性值 (Inertia)")

    axes[1, 0].plot(metrics_df["n_clusters"], metrics_df["silhouette"], "s-", color="#e6550d", linewidth=2)
    axes[1, 0].set_title("轮廓系数")
    axes[1, 0].set_xlabel("簇数 K")
    axes[1, 0].set_ylabel("轮廓系数 (Silhouette)")

    cluster_sizes = pd.Series(labels).value_counts().sort_index()
    axes[1, 1].bar(cluster_sizes.index.astype(str), cluster_sizes.values, color=sns.color_palette("Set2", n_clusters))
    axes[1, 1].set_title("各分群样本量")
    axes[1, 1].set_xlabel("分群编号")
    axes[1, 1].set_ylabel("样本数")

    plt.tight_layout()
    plt.savefig(DEEP_MINING_DIR / "cluster_analysis.png", dpi=220, bbox_inches="tight")
    plt.close()


def _build_cluster_profiles(df: pd.DataFrame, n_clusters: int) -> pd.DataFrame:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if "cluster" in numeric_cols:
        numeric_cols.remove("cluster")

    profiles = df.groupby("cluster")[numeric_cols].mean()
    profiles["size"] = df.groupby("cluster").size()
    profiles["pct"] = (profiles["size"] / len(df) * 100).round(1)
    return profiles


def compute_shap_analysis(
    model,
    x_train: pd.DataFrame,
    x_test: pd.DataFrame,
    feature_names: list[str],
    max_display: int = 20,
) -> dict[str, Any]:
    logger.info("开始 SHAP 模型可解释性分析...")
    if importlib.util.find_spec("shap") is None:
        logger.info("未安装 shap，使用模型系数/特征重要性生成解释性替代图。")
        importance = _build_model_explainability_fallback(model, feature_names, max_display)
        return {"shap_values": None, "importance": importance}

    try:
        import shap

        if hasattr(model, "named_steps"):
            preprocessor = model.named_steps.get("scaler")
            estimator = model.named_steps.get("model", model)
            if preprocessor is not None:
                x_test_transformed = pd.DataFrame(
                    preprocessor.transform(x_test),
                    columns=feature_names,
                    index=x_test.index,
                )
            else:
                x_test_transformed = x_test
        else:
            estimator = model
            x_test_transformed = x_test

        sample_size = min(200, len(x_test_transformed))
        background = shap.sample(x_train, min(100, len(x_train)), random_state=42)

        if hasattr(estimator, "predict_proba"):
            explainer = shap.KernelExplainer(
                estimator.predict_proba,
                background,
                feature_names=feature_names,
            )
            shap_values = explainer.shap_values(x_test_transformed.iloc[:sample_size])
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
        else:
            explainer = shap.KernelExplainer(
                estimator.predict,
                background,
                feature_names=feature_names,
            )
            shap_values = explainer.shap_values(x_test_transformed.iloc[:sample_size])

        plt.figure(figsize=(12, 8))
        shap.summary_plot(
            shap_values,
            x_test_transformed.iloc[:sample_size],
            feature_names=feature_names,
            max_display=max_display,
            show=False,
        )
        plt.tight_layout()
        plt.savefig(SHAP_PATH, dpi=220, bbox_inches="tight")
        plt.close()

        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        if mean_abs_shap.ndim > 1:
            mean_abs_shap = mean_abs_shap.mean(axis=1)
        shap_importance = pd.DataFrame(
            {"feature": feature_names[: len(mean_abs_shap)], "shap_importance": mean_abs_shap}
        ).sort_values("shap_importance", ascending=False)

        logger.info("SHAP 分析完成，已保存至 %s", SHAP_PATH)
        return {"shap_values": shap_values, "importance": shap_importance}

    except Exception as exc:
        logger.warning("SHAP 分析失败: %s，使用模型系数/特征重要性生成替代图", exc)
        importance = _build_model_explainability_fallback(model, feature_names, max_display)
        return {"shap_values": None, "importance": importance}


def _build_model_explainability_fallback(model, feature_names: list[str], max_display: int = 20) -> pd.DataFrame:
    if hasattr(model, "named_steps"):
        estimator = model.named_steps.get("model", model)
    else:
        estimator = model

    if hasattr(estimator, "coef_"):
        values = np.abs(estimator.coef_[0])
        title = "模型解释性分析（逻辑回归系数绝对值）"
    elif hasattr(estimator, "feature_importances_"):
        values = estimator.feature_importances_
        title = "模型解释性分析（树模型特征重要性）"
    else:
        values = np.ones(len(feature_names))
        title = "模型解释性分析（特征权重占位）"

    importance = (
        pd.DataFrame({"feature": feature_names[: len(values)], "shap_importance": values})
        .sort_values("shap_importance", ascending=False)
        .head(max_display)
    )

    fig, ax = plt.subplots(figsize=(11, 7))
    plot_df = importance.sort_values("shap_importance", ascending=True)
    ax.barh(plot_df["feature"], plot_df["shap_importance"], color="#2c7fb8", alpha=0.85)
    ax.set_title(title)
    ax.set_xlabel("贡献强度")
    ax.set_ylabel("特征")
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    plt.savefig(SHAP_PATH, dpi=220, bbox_inches="tight")
    plt.close()
    logger.info("解释性替代图已保存至 %s", SHAP_PATH)

    return importance


def perform_cross_validation(
    model,
    x: pd.DataFrame,
    y: pd.Series,
    cv_folds: int = 5,
) -> dict[str, Any]:
    logger.info("开始 %d 折交叉验证...", cv_folds)
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)

    cv_scores = cross_val_score(model, x, y, cv=cv, scoring="f1")
    cv_auc = cross_val_score(model, x, y, cv=cv, scoring="roc_auc")

    result = {
        "f1_mean": cv_scores.mean(),
        "f1_std": cv_scores.std(),
        "f1_scores": cv_scores.tolist(),
        "auc_mean": cv_auc.mean(),
        "auc_std": cv_auc.std(),
        "auc_scores": cv_auc.tolist(),
    }

    logger.info(
        "交叉验证完成: F1=%.4f(±%.4f), AUC=%.4f(±%.4f)",
        result["f1_mean"],
        result["f1_std"],
        result["auc_mean"],
        result["auc_std"],
    )
    return result


def plot_learning_curve(
    model,
    x: pd.DataFrame,
    y: pd.Series,
    cv_folds: int = 5,
) -> None:
    logger.info("绘制学习曲线...")
    train_sizes, train_scores, test_scores = learning_curve(
        model,
        x,
        y,
        cv=StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42),
        train_sizes=np.linspace(0.1, 1.0, 10),
        scoring="f1",
        n_jobs=1,
        random_state=42,
    )

    train_mean = train_scores.mean(axis=1)
    train_std = train_scores.std(axis=1)
    test_mean = test_scores.mean(axis=1)
    test_std = test_scores.std(axis=1)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.15, color="#2c7fb8")
    ax.fill_between(train_sizes, test_mean - test_std, test_mean + test_std, alpha=0.15, color="#e6550d")
    ax.plot(train_sizes, train_mean, "o-", color="#2c7fb8", label="训练集 F1")
    ax.plot(train_sizes, test_mean, "s-", color="#e6550d", label="验证集 F1")
    ax.set_xlabel("训练样本数")
    ax.set_ylabel("F1 分数")
    ax.set_title("学习曲线")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(DEEP_MINING_DIR / "learning_curve.png", dpi=220, bbox_inches="tight")
    plt.close()
    logger.info("学习曲线已保存")


def plot_confusion_matrix_deep(
    y_true: pd.Series | np.ndarray,
    y_pred: np.ndarray,
    class_names: list[str] | None = None,
) -> None:
    if class_names is None:
        class_names = ["留存", "流失"]

    cm = confusion_matrix(y_true, y_pred)
    cm_normalized = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        ax=axes[0],
    )
    axes[0].set_title("混淆矩阵 (计数)")
    axes[0].set_xlabel("预测标签")
    axes[0].set_ylabel("真实标签")

    sns.heatmap(
        cm_normalized,
        annot=True,
        fmt=".2%",
        cmap="Oranges",
        xticklabels=class_names,
        yticklabels=class_names,
        ax=axes[1],
    )
    axes[1].set_title("混淆矩阵 (行归一化)")
    axes[1].set_xlabel("预测标签")
    axes[1].set_ylabel("真实标签")

    plt.tight_layout()
    plt.savefig(DEEP_MINING_DIR / "confusion_matrix.png", dpi=220, bbox_inches="tight")
    plt.close()
    logger.info("混淆矩阵已保存")


def generate_deep_insights(
    shap_result: dict[str, Any],
    cluster_result: dict[str, Any],
    cv_result: dict[str, Any],
    feature_importance: pd.DataFrame,
) -> dict[str, Any]:
    insights: dict[str, Any] = {
        "top_risk_factors": [],
        "customer_segments": [],
        "model_stability": {},
        "actionable_recommendations": [],
    }

    if not feature_importance.empty:
        top_features = feature_importance.head(5)
        insights["top_risk_factors"] = [
            {"feature": row["feature"], "importance": round(row["importance"], 4)}
            for _, row in top_features.iterrows()
        ]

    if "profiles" in cluster_result:
        profiles = cluster_result["profiles"]
        for cluster_id, profile in profiles.iterrows():
            insights["customer_segments"].append(
                {
                    "cluster": int(cluster_id),
                    "size": int(profile.get("size", 0)),
                    "pct": float(profile.get("pct", 0)),
                }
            )

    if cv_result:
        insights["model_stability"] = {
            "cv_f1_mean": round(cv_result.get("f1_mean", 0), 4),
            "cv_f1_std": round(cv_result.get("f1_std", 0), 4),
            "cv_auc_mean": round(cv_result.get("auc_mean", 0), 4),
            "cv_auc_std": round(cv_result.get("auc_std", 0), 4),
        }

    insights["actionable_recommendations"] = [
        "高风险客户：建议在 24 小时内通过专属客服触达，提供限时优惠或服务升级方案",
        "中风险客户：纳入重点观察名单，定期推送个性化内容和优惠活动",
        "低风险客户：维持常规运营，通过社区互动和内容推送增强粘性",
        "基于聚类分群结果，对不同客群制定差异化的留存策略",
        "持续监控关键特征变化趋势，建立流失预警自动化流程",
    ]

    return insights
