from __future__ import annotations

import logging
import os
import sys

import pandas as pd

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

from .config import IMPORTANCE_PATH, PLOTS_DIR, PROCESSED_DATA_PATH
from .deep_mining import (
    compute_shap_analysis,
    generate_deep_insights,
    perform_clustering,
    perform_cross_validation,
    plot_confusion_matrix_deep,
    plot_learning_curve,
)
from .modeling import train_and_evaluate_models
from .nlp_analysis import analyze_sentiment, get_nlp_summary
from .preprocess import build_model_features, clean_dataset, split_dataset
from .scraper import ensure_scraped_data, get_data_source_info
from .standard_flow_analysis import generate_standard_flow_outputs
from .visualization import create_visualizations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def run_pipeline(force_scrape: bool = False, enable_grid_search: bool = True) -> dict:
    logger.info("=" * 60)
    logger.info("企业客户流失预警与挽留分析系统")
    logger.info("=" * 60)

    logger.info("[阶段 1/7] 实时数据爬取...")
    raw_df = ensure_scraped_data(force_refresh=force_scrape)
    data_info = get_data_source_info(raw_df)
    logger.info("数据来源: %s, 共 %d 条记录", data_info["source"], data_info["total_records"])

    logger.info("[阶段 2/7] 数据预处理与特征工程...")
    cleaned_df = clean_dataset(raw_df)
    cleaned_df.to_csv(PROCESSED_DATA_PATH, index=False)
    logger.info("清洗后数据: %d 条, 特征数: %d", len(cleaned_df), len(cleaned_df.columns))

    logger.info("[阶段 3/7] NLP 文本情感分析...")
    nlp_df = analyze_sentiment(cleaned_df)
    nlp_summary = get_nlp_summary(nlp_df)
    logger.info(
        "情感分析完成: 正面 %.1f%%, 中性 %.1f%%, 负面 %.1f%%",
        nlp_summary.get("sentiment_distribution", {}).get("positive", 0) * 100,
        nlp_summary.get("sentiment_distribution", {}).get("neutral", 0) * 100,
        nlp_summary.get("sentiment_distribution", {}).get("negative", 0) * 100,
    )

    logger.info("[阶段 4/7] 数据可视化...")
    create_visualizations(nlp_df, PLOTS_DIR)

    logger.info("[阶段 5/7] 深度挖掘 - 客户聚类分群...")
    features, target = build_model_features(cleaned_df)
    clustered_features, cluster_result = perform_clustering(features)
    logger.info("聚类完成: 最优簇数=%d", cluster_result["best_k"])

    logger.info("[阶段 6/7] 深度挖掘 - 多模型训练与超参优化...")
    x_train, x_test, y_train, y_test = split_dataset(features, target)
    metrics_df, best_model_name, trained_models = train_and_evaluate_models(
        x_train, x_test, y_train, y_test,
        enable_grid_search=enable_grid_search,
    )

    best_model = trained_models[best_model_name]

    logger.info("[阶段 7/7] 深度挖掘 - 模型评估与可解释性分析...")
    cv_result = perform_cross_validation(best_model, features, target, cv_folds=5)
    plot_learning_curve(best_model, features, target)
    y_pred = best_model.predict(x_test)
    plot_confusion_matrix_deep(y_test, y_pred)

    shap_result = compute_shap_analysis(best_model, x_train, x_test, list(features.columns))

    importance_df = pd.read_csv(IMPORTANCE_PATH)
    deep_insights = generate_deep_insights(shap_result, cluster_result, cv_result, importance_df)
    standard_flow_paths = generate_standard_flow_outputs(
        cleaned_df=cleaned_df,
        nlp_df=nlp_df,
        metrics_df=metrics_df,
        cluster_result=cluster_result,
        data_info=data_info,
    )

    _print_summary(cleaned_df, data_info, metrics_df, best_model_name, cv_result, nlp_summary, deep_insights)

    return {
        "data_info": data_info,
        "nlp_summary": nlp_summary,
        "cluster_result": cluster_result,
        "metrics_df": metrics_df,
        "best_model_name": best_model_name,
        "cv_result": cv_result,
        "shap_result": shap_result,
        "deep_insights": deep_insights,
        "standard_flow_paths": standard_flow_paths,
    }


def _print_summary(
    cleaned_df: pd.DataFrame,
    data_info: dict,
    metrics_df: pd.DataFrame,
    best_model_name: str,
    cv_result: dict,
    nlp_summary: dict,
    deep_insights: dict,
) -> None:
    print("\n" + "=" * 60)
    print("  企业客户流失预警与挽留分析系统 - 运行完成")
    print("=" * 60)
    print(f"  数据来源:       {data_info['source']}")
    print(f"  客户样本量:     {len(cleaned_df)}")
    print(f"  整体流失率:     {cleaned_df['churn_label'].mean():.2%}")
    print(f"  数据时间范围:   {data_info['date_range']}")
    print(f"  最佳模型:       {best_model_name}")
    print(f"  交叉验证 F1:    {cv_result['f1_mean']:.4f} (±{cv_result['f1_std']:.4f})")
    print(f"  交叉验证 AUC:   {cv_result['auc_mean']:.4f} (±{cv_result['auc_std']:.4f})")
    print(f"  情感分析:       正面 {nlp_summary.get('sentiment_distribution', {}).get('positive', 0):.1%}")
    print()
    print("  模型评估结果:")
    print("  " + metrics_df.to_string(index=False).replace("\n", "\n  "))
    print()
    print("  深度挖掘洞察:")
    for rec in deep_insights.get("actionable_recommendations", []):
        print(f"    - {rec}")
    print("=" * 60)
