from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

from .config import STANDARD_FLOW_DIR


sns.set_theme(style="whitegrid")
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def generate_standard_flow_outputs(
    cleaned_df: pd.DataFrame,
    nlp_df: pd.DataFrame | None = None,
    metrics_df: pd.DataFrame | None = None,
    cluster_result: dict[str, Any] | None = None,
    data_info: dict[str, Any] | None = None,
    output_dir: Path = STANDARD_FLOW_DIR,
) -> dict[str, Path]:
    """Generate artifacts aligned with the textbook data-analysis flow."""
    output_dir.mkdir(parents=True, exist_ok=True)
    analysis_df = _merge_nlp_columns(cleaned_df, nlp_df)

    paths = {
        "compliance": output_dir / "flow_compliance_check.csv",
        "data_quality": output_dir / "data_quality_report.csv",
        "comparison": output_dir / "comparison_analysis.csv",
        "group": output_dir / "group_analysis.csv",
        "cross": output_dir / "cross_analysis.csv",
        "regression": output_dir / "regression_analysis.csv",
        "time_series": output_dir / "time_series_analysis.csv",
        "association": output_dir / "association_rules.csv",
        "model_eval": output_dir / "model_evaluation_summary.csv",
        "report": Path("reports") / "standard_flow_compliance.md",
    }

    _build_data_quality_report(analysis_df).to_csv(paths["data_quality"], index=False, encoding="utf-8-sig")
    _build_comparison_analysis(analysis_df).to_csv(paths["comparison"], index=False, encoding="utf-8-sig")
    _build_group_analysis(analysis_df).to_csv(paths["group"], index=False, encoding="utf-8-sig")
    _build_cross_analysis(analysis_df).to_csv(paths["cross"], index=False, encoding="utf-8-sig")
    _build_regression_analysis(analysis_df).to_csv(paths["regression"], index=False, encoding="utf-8-sig")
    _build_time_series_analysis(analysis_df).to_csv(paths["time_series"], index=False, encoding="utf-8-sig")
    _build_association_rules(analysis_df).to_csv(paths["association"], index=False, encoding="utf-8-sig")
    _build_model_evaluation_summary(metrics_df, cluster_result).to_csv(paths["model_eval"], index=False, encoding="utf-8-sig")

    _plot_time_series(paths["time_series"], output_dir / "time_series_churn_trend.png")
    _plot_group_churn(paths["group"], output_dir / "group_churn_rate.png")
    _plot_regression_coefficients(paths["regression"], output_dir / "regression_coefficients.png")

    compliance_df = _build_compliance_check(paths, data_info)
    compliance_df.to_csv(paths["compliance"], index=False, encoding="utf-8-sig")
    _write_markdown_report(paths["report"], compliance_df, paths, data_info)

    return paths


def _merge_nlp_columns(cleaned_df: pd.DataFrame, nlp_df: pd.DataFrame | None) -> pd.DataFrame:
    result = cleaned_df.copy().reset_index(drop=True)
    if nlp_df is None:
        return result

    for column in ["sentiment_score", "sentiment_label", "positive_words", "negative_words"]:
        if column in nlp_df.columns and column not in result.columns:
            result[column] = nlp_df[column].reset_index(drop=True)
    return result


def _build_data_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in df.columns:
        rows.append(
            {
                "column": column,
                "dtype": str(df[column].dtype),
                "missing_count": int(df[column].isna().sum()),
                "missing_rate": round(float(df[column].isna().mean()), 4),
                "unique_count": int(df[column].nunique(dropna=True)),
            }
        )
    return pd.DataFrame(rows)


def _numeric_columns(df: pd.DataFrame) -> list[str]:
    excluded = {"churn_label", "recommendation_id", "author_steamid", "timestamp_created", "timestamp_updated"}
    columns = df.select_dtypes(include=[np.number]).columns.tolist()
    return [column for column in columns if column not in excluded]


def _build_comparison_analysis(df: pd.DataFrame) -> pd.DataFrame:
    if "churn_label" not in df.columns:
        return pd.DataFrame()

    rows = []
    for column in _numeric_columns(df):
        grouped = df.groupby("churn_label", observed=False)[column].mean()
        rows.append(
            {
                "feature": column,
                "retained_mean": round(float(grouped.get(0, 0)), 4),
                "churned_mean": round(float(grouped.get(1, 0)), 4),
                "difference_churn_minus_retained": round(float(grouped.get(1, 0) - grouped.get(0, 0)), 4),
            }
        )
    return pd.DataFrame(rows).sort_values("difference_churn_minus_retained", key=lambda s: s.abs(), ascending=False)


def _build_group_analysis(df: pd.DataFrame) -> pd.DataFrame:
    if "churn_label" not in df.columns:
        return pd.DataFrame()

    group_columns = [column for column in ["playtime_tier", "app_name", "sentiment_label", "is_negative"] if column in df.columns]
    rows = []
    for column in group_columns:
        grouped = df.groupby(column, observed=False)["churn_label"].agg(["count", "mean"]).reset_index()
        for _, row in grouped.iterrows():
            rows.append(
                {
                    "group_field": column,
                    "group_value": row[column],
                    "sample_count": int(row["count"]),
                    "churn_rate": round(float(row["mean"]), 4),
                }
            )
    return pd.DataFrame(rows).sort_values(["group_field", "churn_rate"], ascending=[True, False])


def _build_cross_analysis(df: pd.DataFrame) -> pd.DataFrame:
    if "churn_label" not in df.columns:
        return pd.DataFrame()

    rows = []
    cross_columns = [column for column in ["playtime_tier", "app_name", "sentiment_label"] if column in df.columns]
    for column in cross_columns:
        table = pd.crosstab(df[column], df["churn_label"], normalize="index")
        for group_value, values in table.iterrows():
            rows.append(
                {
                    "cross_field": column,
                    "group_value": group_value,
                    "retained_rate": round(float(values.get(0, 0)), 4),
                    "churn_rate": round(float(values.get(1, 0)), 4),
                }
            )
    return pd.DataFrame(rows).sort_values("churn_rate", ascending=False)


def _build_regression_analysis(df: pd.DataFrame) -> pd.DataFrame:
    target_column = "churn_signal" if "churn_signal" in df.columns else "churn_label"
    if target_column not in df.columns:
        return pd.DataFrame()

    features = df[_numeric_columns(df)].drop(columns=[target_column], errors="ignore").replace([np.inf, -np.inf], np.nan)
    features = features.fillna(features.median(numeric_only=True)).fillna(0)
    if features.empty:
        return pd.DataFrame()

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(features)
    y = pd.to_numeric(df[target_column], errors="coerce").fillna(0)
    model = LinearRegression()
    model.fit(x_scaled, y)
    predictions = model.predict(x_scaled)
    r2 = r2_score(y, predictions)

    result = pd.DataFrame(
        {
            "feature": features.columns,
            "coefficient": model.coef_,
            "abs_coefficient": np.abs(model.coef_),
            "model_r2": r2,
            "target": target_column,
        }
    )
    return result.sort_values("abs_coefficient", ascending=False)


def _build_time_series_analysis(df: pd.DataFrame) -> pd.DataFrame:
    if "review_month" not in df.columns or "churn_label" not in df.columns:
        return pd.DataFrame()

    agg_map: dict[str, tuple[str, str]] = {
        "sample_count": ("churn_label", "count"),
        "churn_rate": ("churn_label", "mean"),
    }
    if "sentiment_score" in df.columns:
        agg_map["avg_sentiment_score"] = ("sentiment_score", "mean")
    if "engagement_score" in df.columns:
        agg_map["avg_engagement_score"] = ("engagement_score", "mean")

    result = df.groupby("review_month", observed=False).agg(**agg_map).reset_index()
    for column in result.select_dtypes(include=[np.number]).columns:
        result[column] = result[column].round(4)
    return result.sort_values("review_month")


def _build_association_rules(df: pd.DataFrame, min_support: float = 0.03) -> pd.DataFrame:
    if "churn_label" not in df.columns or len(df) == 0:
        return pd.DataFrame()

    candidate_columns = [column for column in ["playtime_tier", "app_name", "sentiment_label", "is_negative", "is_free_copy"] if column in df.columns]
    churn_rate = float(df["churn_label"].mean())
    rows = []

    for column in candidate_columns:
        for value, subset in df.groupby(column, observed=False):
            support = len(subset) / len(df)
            if support < min_support:
                continue
            confidence = float(subset["churn_label"].mean())
            lift = confidence / churn_rate if churn_rate else 0
            rows.append(
                {
                    "antecedent": f"{column}={value}",
                    "consequent": "churn_label=1",
                    "support": round(support, 4),
                    "confidence": round(confidence, 4),
                    "lift": round(lift, 4),
                    "sample_count": int(len(subset)),
                }
            )

    return pd.DataFrame(rows).sort_values(["lift", "confidence"], ascending=False)


def _build_model_evaluation_summary(metrics_df: pd.DataFrame | None, cluster_result: dict[str, Any] | None) -> pd.DataFrame:
    rows = []
    if metrics_df is not None and not metrics_df.empty:
        for _, row in metrics_df.iterrows():
            rows.append(
                {
                    "model_type": "classification",
                    "model": row.get("model"),
                    "primary_metric": "f1_score",
                    "primary_value": row.get("f1_score"),
                    "secondary_metric": "roc_auc",
                    "secondary_value": row.get("roc_auc"),
                }
            )

    if cluster_result and "metrics" in cluster_result:
        metrics = cluster_result["metrics"]
        if isinstance(metrics, pd.DataFrame):
            for _, row in metrics.iterrows():
                rows.append(
                    {
                        "model_type": "clustering",
                        "model": f"KMeans_k_{int(row['n_clusters'])}",
                        "primary_metric": "silhouette",
                        "primary_value": row.get("silhouette"),
                        "secondary_metric": "davies_bouldin",
                        "secondary_value": row.get("davies_bouldin"),
                    }
                )
    return pd.DataFrame(rows)


def _build_compliance_check(paths: dict[str, Path], data_info: dict[str, Any] | None) -> pd.DataFrame:
    rows = [
        ("需求分析", "已补齐", "reports/standard_flow_compliance.md", "把业务/客服/运营/产品等部门需求映射为流失预警、原因解释和挽留策略。"),
        ("数据获取", "已完成", "data/raw/scraped_reviews.csv", f"数据来源：{(data_info or {}).get('source', 'Steam reviews / local dataset')}。"),
        ("数据预处理-数据合并", "已完成", "src/churn_system/scraper.py", "爬取数据、本地缓存数据和备用数据统一进入同一张原始表。"),
        ("数据预处理-缺失清洗", "已完成", str(paths["data_quality"]), "输出字段缺失率，并在 clean_dataset 中完成缺失填充和异常值裁剪。"),
        ("数据预处理-数据标准化", "已完成", "src/churn_system/deep_mining.py", "聚类和回归分析使用 StandardScaler，分类模型中的逻辑回归也使用标准化管道。"),
        ("数据预处理-数据变换", "已完成", "src/churn_system/preprocess.py", "生成 playtime_hours、engagement_score、churn_signal、churn_label 等衍生变量。"),
        ("分析与挖掘-对比分析", "已补齐", str(paths["comparison"]), "比较流失与留存客户在数值特征上的均值差异。"),
        ("分析与挖掘-分组分析", "已补齐", str(paths["group"]), "按时长层级、产品、情感类型等维度统计流失率。"),
        ("分析与挖掘-交叉分析", "已补齐", str(paths["cross"]), "生成分类维度与流失标签的交叉占比。"),
        ("分析与挖掘-回归分析", "已补齐", str(paths["regression"]), "用线性回归解释 churn_signal 的主要影响方向。"),
        ("分析与挖掘-时间序列", "已补齐", str(paths["time_series"]), "按 review_month 统计样本量、流失率、情感分和活跃度趋势。"),
        ("分析与挖掘-关联规则", "已补齐", str(paths["association"]), "计算特征取值到流失结果的 support、confidence 和 lift。"),
        ("模型评价与优化-聚类模型评价", "已完成", "outputs/deep_mining/cluster_analysis.png", "K-Means 使用轮廓系数、DBI、CH 指数和肘部法则评估。"),
        ("模型评价与优化-分类模型评价", "已完成", "outputs/model_metrics.csv", "比较 Accuracy、Precision、Recall、F1、AUC，并做 GridSearchCV 和 Stacking。"),
        ("模型评价与优化-回归模型评价", "已补齐", str(paths["regression"]), "输出回归 R2 和标准化系数，作为影响因素解释补充。"),
        ("部署", "已完成", "streamlit_app.py", "使用 Streamlit 展示业务看板、模型结果、客户预测和挽留建议。"),
    ]
    return pd.DataFrame(rows, columns=["flow_step", "status", "evidence", "description"])


def _plot_time_series(csv_path: Path, output_path: Path) -> None:
    df = pd.read_csv(csv_path)
    if df.empty or "review_month" not in df.columns:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["review_month"].astype(str), df["churn_rate"], marker="o", linewidth=2.2, color="#d62728")
    ax.set_title("按月份统计的客户流失率趋势")
    ax.set_xlabel("评论月份")
    ax.set_ylabel("流失率")
    ax.tick_params(axis="x", rotation=30)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y * 100:.1f}%"))
    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()


def _plot_group_churn(csv_path: Path, output_path: Path) -> None:
    df = pd.read_csv(csv_path)
    if df.empty:
        return
    plot_df = df.sort_values("churn_rate", ascending=False).head(12).copy()
    plot_df["label"] = plot_df["group_field"].astype(str) + "=" + plot_df["group_value"].astype(str)
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.barplot(data=plot_df, x="churn_rate", y="label", hue="label", legend=False, palette="Reds_r", ax=ax)
    ax.set_title("高流失率分组 Top 12")
    ax.set_xlabel("流失率")
    ax.set_ylabel("分组")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x * 100:.1f}%"))
    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()


def _plot_regression_coefficients(csv_path: Path, output_path: Path) -> None:
    df = pd.read_csv(csv_path)
    if df.empty:
        return
    plot_df = df.head(12).sort_values("coefficient")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#d62728" if value > 0 else "#2ca02c" for value in plot_df["coefficient"]]
    ax.barh(plot_df["feature"], plot_df["coefficient"], color=colors, alpha=0.85)
    ax.set_title("回归分析：影响流失信号的主要特征")
    ax.set_xlabel("标准化回归系数")
    ax.set_ylabel("特征")
    ax.axvline(0, color="#333333", linewidth=1)
    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()


def _write_markdown_report(
    report_path: Path,
    compliance_df: pd.DataFrame,
    paths: dict[str, Path],
    data_info: dict[str, Any] | None,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 标准数据分析流程对照报告",
        "",
        "## 结论",
        "",
        "当前项目原本已经完成数据获取、预处理、可视化、聚类、分类建模、模型评价、解释性分析和 Streamlit 展示。对照课堂图示后，已补齐独立产物较弱的对比分析、分组分析、交叉分析、回归分析、时间序列分析、关联规则分析和流程对照说明。",
        "",
        "## 数据来源",
        "",
        f"- 数据来源：{(data_info or {}).get('source', 'Steam reviews / local dataset')}",
        f"- 样本数量：{(data_info or {}).get('total_records', '以当前运行数据为准')}",
        f"- 时间范围：{(data_info or {}).get('date_range', '以当前运行数据为准')}",
        "",
        "## 流程对照",
        "",
        "| 流程环节 | 状态 | 证据文件 | 说明 |",
        "|---|---|---|---|",
    ]
    for _, row in compliance_df.iterrows():
        lines.append(f"| {row['flow_step']} | {row['status']} | `{row['evidence']}` | {row['description']} |")

    lines.extend(
        [
            "",
            "## 新增补充产物",
            "",
            f"- 数据质量报告：`{paths['data_quality']}`",
            f"- 对比分析：`{paths['comparison']}`",
            f"- 分组分析：`{paths['group']}`",
            f"- 交叉分析：`{paths['cross']}`",
            f"- 回归分析：`{paths['regression']}`",
            f"- 时间序列分析：`{paths['time_series']}`",
            f"- 关联规则分析：`{paths['association']}`",
            f"- 模型评价汇总：`{paths['model_eval']}`",
            "",
            "## 说明",
            "",
            "图中示例包含业务系统、财务系统、生产系统。本项目是客户流失预警方向，因此部署环节对应为 Streamlit 业务分析系统，面向运营、客服、产品和管理人员使用；财务/生产系统不作为本项目的真实业务边界。",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
