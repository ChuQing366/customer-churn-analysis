from __future__ import annotations

import math
import joblib
import pandas as pd
import streamlit as st

from src.churn_system.config import (
    CLUSTER_PATH,
    DEEP_MINING_DIR,
    IMPORTANCE_PATH,
    METRICS_PATH,
    MODEL_PATH,
    NLP_RESULT_PATH,
    PLOTS_DIR,
    PROCESSED_DATA_PATH,
    SCRAPED_DATA_PATH,
    SHAP_PATH,
    STACKING_MODEL_PATH,
)
from src.churn_system.preprocess import (
    CATEGORICAL_COLUMNS,
    NUMERIC_COLUMNS,
    TARGET_COLUMN,
    clean_dataset,
    sanitize_feature_columns,
)
from src.churn_system.scraper import STEAM_APP_IDS, ensure_scraped_data, get_data_source_info, scrape_steam_reviews

PAGE_TITLE = "基于 Steam 用户行为特征与评论情感的客户流失预警与挽留分析系统"
CHURN_LABELS = {0: "留存客户", 1: "流失客户"}
MODEL_LABELS = {
    "LogisticRegression": "逻辑回归",
    "DecisionTree": "决策树",
    "RandomForest": "随机森林",
    "GradientBoosting": "梯度提升树",
    "XGBoost": "XGBoost",
    "LightGBM": "LightGBM",
    "StackingEnsemble": "Stacking 集成模型",
}
RISK_LEVELS = [
    (0.7, "高风险", "建议 24 小时内安排客户经理触达，优先提供专属优惠或服务补救方案。"),
    (0.45, "中风险", "建议纳入重点观察名单，结合用户行为数据制定个性化挽留策略。"),
    (0.0, "低风险", "当前风险较低，可维持常规运营关怀并持续监控行为变化。"),
]
SENTIMENT_LABELS = {"positive": "正面", "neutral": "中性", "negative": "负面"}
FEATURE_LABELS = {
    "author_playtime_forever": "累计使用时长",
    "author_playtime_at_review": "评论时使用时长",
    "author_num_games_owned": "拥有游戏数",
    "author_num_reviews": "历史评论数",
    "votes_up": "评论获赞数",
    "votes_funny": "趣味投票数",
    "weighted_vote_score": "加权投票分数",
    "comment_count": "评论回复数",
    "review_length": "评论长度",
    "review_word_count": "评论词数",
    "playtime_hours": "使用时长",
    "playtime_at_review_hours": "评论时使用时长",
    "engagement_score": "参与度分数",
    "received_for_free": "是否免费获取",
    "written_during_early_access": "是否抢先体验",
}
PLAYTIME_TIER_LABELS = {
    "极短_lt2h": "极短(<2h)",
    "短_2-10h": "短(2-10h)",
    "中_10-50h": "中(10-50h)",
    "长_50-200h": "长(50-200h)",
    "很长_200-1000h": "很长(200-1000h)",
    "超长_gt1000h": "超长(>1000h)",
}
PLOT_LABELS = {
    "01_churn_distribution": "客户流失总体分布",
    "02_contract_churn_rate": "不同使用时长的流失率",
    "03_region_churn_rate": "不同产品的流失率",
    "04_fee_vs_activity": "使用时长与参与度关系",
    "05_login_trend_by_churn": "情感分数变化趋势",
}
PLOT_EXPLANATIONS = {
    "01_churn_distribution": "用于说明样本中流失和留存客户的整体比例，是后续建模和运营判断的基础。",
    "02_contract_churn_rate": "用于比较不同使用时长层级的流失差异，帮助定位需要重点挽留的生命周期阶段。",
    "03_region_churn_rate": "用于比较不同产品的流失差异，帮助确定优先复盘的产品或游戏社区。",
    "04_fee_vs_activity": "用于观察使用时长和参与度之间的关系，识别高活跃、低活跃等典型用户行为模式。",
    "05_login_trend_by_churn": "用于观察情感或时间趋势变化，辅助判断流失风险是否随时间波动。",
}
APP_LABELS = {
    730: "CS2",
    570: "Dota 2",
    440: "Team Fortress 2",
    578080: "PUBG",
    271590: "GTA V",
    1172470: "Apex Legends",
    1938090: "The Finals",
    252490: "Rust",
    292030: "The Witcher 3",
    359550: "Rainbow Six Siege",
}

st.set_page_config(page_title=PAGE_TITLE, layout="wide")


@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_df = ensure_scraped_data()
    processed_is_fresh = (
        PROCESSED_DATA_PATH.exists()
        and SCRAPED_DATA_PATH.exists()
        and PROCESSED_DATA_PATH.stat().st_mtime >= SCRAPED_DATA_PATH.stat().st_mtime
    )
    if processed_is_fresh:
        cleaned_df = pd.read_csv(PROCESSED_DATA_PATH)
    else:
        cleaned_df = clean_dataset(raw_df)
        cleaned_df.to_csv(PROCESSED_DATA_PATH, index=False, encoding="utf-8-sig")
    return raw_df, cleaned_df


@st.cache_data(show_spinner=False)
def load_metrics() -> pd.DataFrame:
    if not METRICS_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(METRICS_PATH)


@st.cache_data(show_spinner=False)
def load_importance() -> pd.DataFrame:
    if not IMPORTANCE_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(IMPORTANCE_PATH)


@st.cache_data(show_spinner=False)
def load_nlp_results() -> pd.DataFrame:
    if not NLP_RESULT_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(NLP_RESULT_PATH)


@st.cache_data(show_spinner=False)
def load_cluster_results() -> pd.DataFrame:
    if not CLUSTER_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(CLUSTER_PATH)


@st.cache_resource(show_spinner=False)
def load_model():
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --app-bg: #f6f8fb;
                --panel-bg: #ffffff;
                --panel-border: #dfe6ef;
                --text-main: #1f2937;
                --text-muted: #64748b;
                --accent: #2563eb;
                --accent-soft: #eff6ff;
                --success-soft: #eaf8f0;
            }
            .stApp { background: var(--app-bg); }
            .block-container {
                max-width: 1520px;
                padding-top: 1.15rem;
                padding-bottom: 3rem;
            }
            h1, h2, h3 { color: var(--text-main); letter-spacing: 0; }
            h1 { font-size: 2.45rem; line-height: 1.15; margin-bottom: 0.45rem; }
            h2, h3 { margin-top: 1.05rem; }
            [data-testid="stSidebar"] {
                background: #eef2f7;
                border-right: 1px solid #d8e0ea;
            }
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3 {
                color: #263244;
            }
            [data-testid="stMetric"] {
                background: var(--panel-bg);
                border: 1px solid var(--panel-border);
                border-radius: 8px;
                padding: 16px 18px;
                box-shadow: 0 4px 16px rgba(15, 23, 42, 0.055);
                min-height: 118px;
            }
            [data-testid="stMetricLabel"] {
                color: #55708c;
                font-weight: 650;
            }
            [data-testid="stMetricValue"] {
                color: #202938;
                font-weight: 720;
                line-height: 1.05;
                overflow-wrap: anywhere;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
                border-bottom: 1px solid #dce4ee;
                padding-bottom: 6px;
            }
            .stTabs [data-baseweb="tab"] {
                height: 44px;
                padding: 0 16px;
                background: #ffffff;
                border: 1px solid #dde5ef;
                border-radius: 8px 8px 0 0;
                color: #475569;
                font-weight: 650;
            }
            .stTabs [aria-selected="true"] {
                background: var(--accent-soft);
                color: #1d4ed8;
                border-color: #b8cff8;
            }
            .section-note {
                color: var(--text-muted);
                font-size: 0.95rem;
                margin-top: -0.25rem;
                margin-bottom: 0.9rem;
            }
            .chart-title {
                color: #243044;
                font-weight: 750;
                font-size: 1.05rem;
                margin: 1.1rem 0 0.45rem;
            }
            .app-hero {
                background:
                    linear-gradient(135deg, rgba(37, 99, 235, 0.10), rgba(20, 184, 166, 0.08)),
                    #ffffff;
                border: 1px solid #d9e4f2;
                border-radius: 8px;
                padding: 26px 30px 24px;
                margin-bottom: 1.1rem;
                box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
            }
            .app-hero-grid {
                display: grid;
                grid-template-columns: minmax(0, 1.55fr) minmax(360px, 0.9fr);
                gap: 22px;
                align-items: stretch;
            }
            .app-eyebrow {
                color: #2563eb;
                font-size: 0.92rem;
                font-weight: 760;
                letter-spacing: 0.02em;
                margin-bottom: 8px;
            }
            .app-title {
                color: #172033;
                font-size: 2.18rem;
                line-height: 1.18;
                font-weight: 820;
                margin: 0 0 12px;
            }
            .app-subtitle {
                color: #526579;
                font-size: 1.02rem;
                line-height: 1.65;
                max-width: 900px;
                margin-bottom: 16px;
            }
            .hero-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            .hero-tag {
                display: inline-flex;
                align-items: center;
                border: 1px solid #cbd9ec;
                background: rgba(255, 255, 255, 0.76);
                color: #334155;
                border-radius: 999px;
                padding: 6px 11px;
                font-size: 0.88rem;
                font-weight: 650;
            }
            .hero-summary {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }
            .hero-summary-card {
                background: rgba(255, 255, 255, 0.88);
                border: 1px solid #dce6f3;
                border-radius: 8px;
                padding: 13px 14px;
                min-height: 88px;
            }
            .hero-summary-label {
                color: #64748b;
                font-size: 0.82rem;
                font-weight: 700;
                margin-bottom: 6px;
            }
            .hero-summary-value {
                color: #172033;
                font-size: 1.42rem;
                line-height: 1.1;
                font-weight: 780;
                overflow-wrap: anywhere;
            }
            .hero-summary-note {
                color: #64748b;
                font-size: 0.78rem;
                margin-top: 5px;
            }
            .status-band {
                background: #ffffff;
                border: 1px solid #dfe6ef;
                border-radius: 8px;
                padding: 14px 16px;
                margin: 1rem 0 0.9rem;
                box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
            }
            @media (max-width: 980px) {
                .app-hero-grid { grid-template-columns: 1fr; }
                .hero-summary { grid-template-columns: 1fr 1fr; }
                .app-title { font-size: 1.72rem; }
            }
            div[data-testid="stImage"] {
                background: var(--panel-bg);
                border: 1px solid var(--panel-border);
                border-radius: 8px;
                padding: 14px;
                box-shadow: 0 4px 14px rgba(15, 23, 42, 0.045);
                margin-bottom: 1rem;
            }
            div[data-testid="stImage"] img {
                border-radius: 5px;
            }
            div[data-testid="stImage"] figcaption {
                color: #51657d;
                font-size: 0.92rem;
                padding-top: 0.35rem;
            }
            .risk-panel {
                border: 1px solid var(--panel-border);
                border-radius: 8px;
                padding: 18px;
                background: var(--panel-bg);
                box-shadow: 0 4px 14px rgba(15, 23, 42, 0.045);
            }
            .risk-panel strong { color: #102a43; }
            .insight-card {
                background: #f0f7ff;
                border-left: 4px solid #2c7fb8;
                border-radius: 6px;
                padding: 14px 18px;
                margin: 8px 0;
            }
            div[data-testid="stAlert"] {
                border-radius: 8px;
            }
            div[data-testid="stDataFrame"] {
                border-radius: 8px;
                overflow: hidden;
                border: 1px solid var(--panel-border);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_pipeline_status() -> None:
    steps = [
        ("实时数据采集", SCRAPED_DATA_PATH, None),
        ("数据预处理与特征工程", PROCESSED_DATA_PATH, SCRAPED_DATA_PATH),
        ("NLP 文本情感分析", NLP_RESULT_PATH, PROCESSED_DATA_PATH),
        ("数据可视化图表生成", PLOTS_DIR / "01_churn_distribution.png", PROCESSED_DATA_PATH),
        ("客户聚类分群分析", CLUSTER_PATH, PROCESSED_DATA_PATH),
        ("多模型训练与超参优化", METRICS_PATH, PROCESSED_DATA_PATH),
        ("模型评估与可解释性", SHAP_PATH, METRICS_PATH),
    ]

    def step_state(path, dependency) -> str:
        if not path.exists():
            return "missing"
        if dependency is not None and dependency.exists() and path.stat().st_mtime < dependency.stat().st_mtime:
            return "stale"
        return "done"

    states = [step_state(path, dependency) for _, path, dependency in steps]
    completed_count = sum(1 for state in states if state == "done")
    stale_count = sum(1 for state in states if state == "stale")
    all_completed = completed_count == len(steps)

    st.subheader("分析管线状态")
    if all_completed:
        st.success("全部 7 个阶段已完成")
    elif stale_count:
        st.warning(f"有 {stale_count} 个阶段基于旧数据生成，建议运行 `python run_project.py` 刷新完整结果。")
    elif completed_count == 0:
        st.warning("尚未运行分析流程，请先执行 `python run_project.py` 或在“实时数据采集”页启动采集。")
    else:
        st.info(f"已完成 {completed_count}/7 个阶段")

    progress_cols = st.columns(len(steps))
    for column, (label, path, dependency) in zip(progress_cols, steps):
        state = step_state(path, dependency)
        with column:
            if state == "done":
                st.success(label)
                st.caption("已完成")
            elif state == "stale":
                st.warning(label)
                st.caption("需更新")
            else:
                st.info(label)
                st.caption("待运行")

    current_progress = (completed_count + stale_count) / len(steps)
    st.progress(current_progress, text=f"当前进度：{completed_count} 个完成，{stale_count} 个需更新")

    if SCRAPED_DATA_PATH.exists():
        data_info = get_data_source_info(pd.read_csv(SCRAPED_DATA_PATH, encoding="utf-8-sig"))
        source_cols = st.columns(6)
        source_cols[0].metric("数据来源", "Steam API / 缓存")
        source_cols[1].metric("样本量", f"{data_info.get('total_records', 0):,}")
        source_cols[2].metric("产品数", f"{data_info.get('apps_count', 0)}")
        source_cols[3].metric("流失率", f"{data_info.get('churn_rate', 0):.1%}")
        source_cols[4].metric("正面评论", f"{data_info.get('positive_rate', 0):.1%}")
        source_cols[5].metric("最后更新", data_info.get("last_updated", "N/A"))
        st.caption(f"数据时间范围：{data_info.get('date_range', 'N/A')}")


def format_rate(value: float) -> str:
    return f"{value:.1%}"


def sentiment_label(value: str) -> str:
    return SENTIMENT_LABELS.get(value, value)


def feature_label(feature: str) -> str:
    if feature in FEATURE_LABELS:
        return FEATURE_LABELS[feature]
    if feature.startswith("is_negative_"):
        return f"是否差评：{'是' if feature.endswith('_1') else '否'}"
    if feature.startswith("is_free_copy_"):
        return f"是否免费获取：{'是' if feature.endswith('_1') else '否'}"
    if feature.startswith("is_early_access_"):
        return f"是否抢先体验：{'是' if feature.endswith('_1') else '否'}"
    if feature.startswith("app_id_"):
        return f"产品 ID：{feature.removeprefix('app_id_')}"
    if feature.startswith("review_month_"):
        return f"评论月份：{feature.removeprefix('review_month_')}"
    if feature.startswith("review_hour_"):
        return f"评论时段：{feature.removeprefix('review_hour_')} 点"
    if feature.startswith("playtime_tier_"):
        raw_value = feature.removeprefix("playtime_tier_")
        return f"使用时长层级：{PLAYTIME_TIER_LABELS.get(raw_value, raw_value)}"
    return feature


def render_horizontal_bar(
    values: pd.Series,
    *,
    category_title: str,
    value_title: str,
    height: int = 280,
    value_format: str = ".0%",
    color: str = "#0f73c8",
) -> None:
    chart_df = values.reset_index()
    chart_df.columns = ["category", "value"]
    chart_df["value"] = pd.to_numeric(chart_df["value"], errors="coerce")
    chart_df = chart_df.dropna(subset=["value"])

    st.vega_lite_chart(
        chart_df,
        {
            "height": height,
            "mark": {"type": "bar", "color": color},
            "encoding": {
                "x": {
                    "field": "value",
                    "type": "quantitative",
                    "axis": {"format": value_format, "title": value_title, "grid": True},
                },
                "y": {
                    "field": "category",
                    "type": "nominal",
                    "sort": "-x",
                    "axis": {"title": None, "labelLimit": 260, "labelPadding": 8},
                },
                "tooltip": [
                    {"field": "category", "type": "nominal", "title": category_title},
                    {"field": "value", "type": "quantitative", "title": value_title, "format": value_format},
                ],
            },
        },
        use_container_width=True,
    )


def render_line_chart(
    values: pd.Series,
    *,
    category_title: str,
    value_title: str,
    height: int = 260,
) -> None:
    chart_df = values.reset_index()
    chart_df.columns = ["category", "value"]
    chart_df["value"] = pd.to_numeric(chart_df["value"], errors="coerce")
    chart_df = chart_df.dropna(subset=["value"])

    st.vega_lite_chart(
        chart_df,
        {
            "height": height,
            "mark": {"type": "line", "point": True, "color": "#0f73c8", "strokeWidth": 3},
            "encoding": {
                "x": {
                    "field": "category",
                    "type": "nominal",
                    "axis": {"title": None, "labelAngle": 0, "labelLimit": 120},
                },
                "y": {
                    "field": "value",
                    "type": "quantitative",
                    "axis": {"format": ".0%", "title": value_title, "grid": True},
                },
                "tooltip": [
                    {"field": "category", "type": "nominal", "title": category_title},
                    {"field": "value", "type": "quantitative", "title": value_title, "format": ".1%"},
                ],
            },
        },
        use_container_width=True,
    )


def render_insight_panel(title: str, lines: list[str]) -> None:
    valid_lines = [line for line in lines if line]
    if not valid_lines:
        return

    content = "\n\n".join(f"{index}. {line}" for index, line in enumerate(valid_lines, start=1))
    st.info(f"{title}\n\n{content}")


def _top_churn_group(df: pd.DataFrame, column: str) -> tuple[str, float] | None:
    if column not in df.columns or TARGET_COLUMN not in df.columns or df.empty:
        return None

    chart = df.groupby(column, observed=False)[TARGET_COLUMN].agg(["mean", "count"])
    chart = chart[chart["count"] >= max(5, len(df) * 0.02)]
    if chart.empty:
        return None

    row = chart.sort_values("mean", ascending=False).iloc[0]
    return str(row.name), float(row["mean"])


def _bottom_churn_group(df: pd.DataFrame, column: str) -> tuple[str, float] | None:
    if column not in df.columns or TARGET_COLUMN not in df.columns or df.empty:
        return None

    chart = df.groupby(column, observed=False)[TARGET_COLUMN].agg(["mean", "count"])
    chart = chart[chart["count"] >= max(5, len(df) * 0.02)]
    if chart.empty:
        return None

    row = chart.sort_values("mean", ascending=True).iloc[0]
    return str(row.name), float(row["mean"])


def _top_feature_text(importance_df: pd.DataFrame, limit: int = 5) -> str:
    if importance_df.empty or "feature" not in importance_df.columns:
        return "当前还没有可用的特征重要性结果。"

    labels = [feature_label(feature) for feature in importance_df.head(limit)["feature"].tolist()]
    return "、".join(labels)


def _best_model_summary(metrics_df: pd.DataFrame) -> str:
    if metrics_df.empty:
        return "当前还没有模型评估结果，请先运行完整分析流程。"

    best = metrics_df.sort_values(["f1_score", "roc_auc"], ascending=False).iloc[0]
    model_name = MODEL_LABELS.get(str(best["model"]), str(best["model"]))
    return (
        f"当前综合表现最好的模型是 {model_name}，"
        f"准确率 {best['accuracy']:.3f}，F1 分数 {best['f1_score']:.3f}，AUC {best['roc_auc']:.3f}。"
    )


def build_business_analysis(df: pd.DataFrame, mode: str = "总体分析") -> list[str]:
    metrics_df = load_metrics()
    importance_df = load_importance()
    nlp_df = load_nlp_results()

    if df.empty:
        return ["当前筛选条件下没有样本，建议先放宽筛选范围。"]

    churn_rate = float(df[TARGET_COLUMN].mean()) if TARGET_COLUMN in df.columns else 0.0
    avg_playtime = float(df["playtime_hours"].mean()) if "playtime_hours" in df.columns else 0.0
    avg_engagement = float(df["engagement_score"].mean()) if "engagement_score" in df.columns else 0.0
    negative_rate = float(df["is_negative"].astype(float).mean()) if "is_negative" in df.columns else 0.0

    product_risk = _top_churn_group(df, "app_name")
    playtime_risk = _top_churn_group(df, "playtime_tier")
    sentiment_risk = _top_churn_group(df, "sentiment_label")

    lines: list[str] = []

    if mode == "总体分析":
        risk_level = "偏高" if churn_rate >= 0.5 else ("中等" if churn_rate >= 0.35 else "较低")
        lines.append(f"当前筛选样本共 {len(df):,} 条，流失率为 {churn_rate:.1%}，整体风险水平{risk_level}。")
        lines.append(f"用户平均使用时长为 {avg_playtime:.1f} 小时，平均参与度分数为 {avg_engagement:.2f}，差评占比约 {negative_rate:.1%}。")
        if product_risk:
            lines.append(f"从产品维度看，{product_risk[0]} 的流失率最高，达到 {product_risk[1]:.1%}，建议优先关注该产品下的用户反馈。")
        if playtime_risk:
            lines.append(f"从使用时长看，{playtime_risk[0]} 用户流失率最高，达到 {playtime_risk[1]:.1%}，说明生命周期早期或特定活跃层级需要重点运营。")
        lines.append(_best_model_summary(metrics_df))
        lines.append(f"模型当前最关注的因素包括：{_top_feature_text(importance_df)}。")
        return lines

    if mode == "一句话结论":
        risk_level = "偏高" if churn_rate >= 0.5 else ("中等" if churn_rate >= 0.35 else "较低")
        if product_risk:
            lines.append(
                f"当前样本流失率为 {churn_rate:.1%}，风险水平{risk_level}；"
                f"{product_risk[0]} 是最需要优先关注的产品群体，建议结合差评和低活跃用户做定向挽留。"
            )
        else:
            lines.append(
                f"当前样本流失率为 {churn_rate:.1%}，风险水平{risk_level}；"
                "建议优先关注差评、低使用时长和低参与度用户。"
            )
        return lines

    if mode == "风险解释":
        lines.append("系统判断流失风险时，主要结合用户评价倾向、使用时长、互动反馈和历史活跃程度。")
        lines.append(f"当前样本差评占比为 {negative_rate:.1%}，这是最直接的风险信号之一。")
        if sentiment_risk:
            lines.append(f"情感倾向中，{sentiment_label(sentiment_risk[0])} 用户的流失率最高，达到 {sentiment_risk[1]:.1%}。")
        if not nlp_df.empty and "sentiment_label" in nlp_df.columns:
            dist = nlp_df["sentiment_label"].value_counts(normalize=True)
            lines.append(
                f"NLP 结果显示，正面评论占 {dist.get('positive', 0):.1%}，"
                f"中性评论占 {dist.get('neutral', 0):.1%}，负面评论占 {dist.get('negative', 0):.1%}。"
            )
        lines.append(f"模型解释层显示，关键影响因素集中在：{_top_feature_text(importance_df)}。")
        return lines

    if mode == "挽留建议":
        if churn_rate >= 0.5:
            lines.append("当前流失率较高，建议将运营重点放在高风险用户召回和负面反馈修复上。")
        else:
            lines.append("当前流失率处于可控区间，可以采用分层运营方式提升留存。")
        lines.append("对高风险用户：优先处理差评、低时长、低互动用户，提供限时活动、补偿礼包或客服触达。")
        lines.append("对中风险用户：推送个性化内容、版本更新说明和社区活动，提高继续使用的理由。")
        lines.append("对低风险用户：保持常规运营触达，重点提升社区参与度和口碑传播。")
        if product_risk:
            lines.append(f"建议把 {product_risk[0]} 作为优先复盘对象，重点检查该产品的评论关键词、差评原因和活跃下降情况。")
        return lines

    lines.append("请选择一个分析模式。")
    return lines


def render_business_assistant_panel(df: pd.DataFrame, compact: bool = False) -> None:
    title = "业务分析助手"
    if compact:
        st.sidebar.divider()
        st.sidebar.subheader(title)
        mode = st.sidebar.selectbox("分析类型", ["一句话结论", "总体分析", "风险解释", "挽留建议"], key="sidebar_ai_mode")
        if st.sidebar.button("生成业务分析", use_container_width=True):
            st.session_state["sidebar_ai_report"] = build_business_analysis(df, mode)
        report = st.session_state.get("sidebar_ai_report", build_business_analysis(df, mode)[:2])
        for line in report:
            st.sidebar.info(line)
        return

    st.subheader(title)
    st.caption("根据当前筛选后的数据、模型结果、特征重要性和情感分析结果，自动生成业务解读和运营建议。")
    mode = st.radio("选择分析任务", ["一句话结论", "总体分析", "风险解释", "挽留建议"], horizontal=True)
    report = build_business_analysis(df, mode)

    for index, line in enumerate(report, start=1):
        st.info(f"{index}. {line}")

    st.download_button(
        "下载本次分析文本",
        data="\n".join(f"{i}. {line}" for i, line in enumerate(report, start=1)).encode("utf-8-sig"),
        file_name="business_ai_analysis.txt",
        mime="text/plain",
        type="secondary",
    )


def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.header("数据筛选")
        st.caption("调整筛选条件，观察不同用户群体的流失特征变化。")

        if "app_name" in df.columns:
            apps = sorted(df["app_name"].dropna().unique().tolist())
            selected_apps = st.multiselect("产品", apps, default=apps)
        else:
            selected_apps = None

        if "playtime_tier" in df.columns:
            tiers = sorted(df["playtime_tier"].dropna().unique().tolist())
            selected_tiers = st.multiselect("使用时长层级", tiers, default=tiers)
        else:
            selected_tiers = None

        if "sentiment_label" in df.columns:
            sentiments = sorted(df["sentiment_label"].dropna().unique().tolist())
            selected_sentiments = st.multiselect("情感倾向", sentiments, default=sentiments, format_func=sentiment_label)
        else:
            selected_sentiments = None

        if "playtime_hours" in df.columns:
            min_h, max_h = float(df["playtime_hours"].min()), float(df["playtime_hours"].max())
            hours_range = st.slider("使用时长 (小时)", min_h, max_h, (min_h, max_h), step=10.0)
        else:
            hours_range = None

        if "engagement_score" in df.columns:
            min_e, max_e = float(df["engagement_score"].min()), float(df["engagement_score"].max())
            eng_range = st.slider("参与度分数", min_e, max_e, (min_e, max_e), step=0.5)
        else:
            eng_range = None

    result = df.copy()
    if selected_apps and "app_name" in result.columns:
        result = result[result["app_name"].isin(selected_apps)]
    if selected_tiers and "playtime_tier" in result.columns:
        result = result[result["playtime_tier"].isin(selected_tiers)]
    if selected_sentiments and "sentiment_label" in result.columns:
        result = result[result["sentiment_label"].isin(selected_sentiments)]
    if hours_range and "playtime_hours" in result.columns:
        result = result[result["playtime_hours"].between(*hours_range)]
    if eng_range and "engagement_score" in result.columns:
        result = result[result["engagement_score"].between(*eng_range)]

    return result


def render_header(df: pd.DataFrame) -> None:
    churn_col = TARGET_COLUMN if TARGET_COLUMN in df.columns else "Churn"
    churn_rate = df[churn_col].mean() if churn_col in df.columns else 0
    positive_rate = 0.0
    if "is_negative" in df.columns and not df.empty:
        positive_rate = 1 - float(df["is_negative"].astype(float).mean())
    product_count = df["app_name"].nunique() if "app_name" in df.columns else 0

    st.markdown(
        f"""
        <div class="app-hero">
            <div class="app-hero-grid">
                <div>
                    <div class="app-eyebrow">Steam 用户流失风险分析看板</div>
                    <div class="app-title">{PAGE_TITLE}</div>
                    <div class="app-subtitle">
                        结合用户游戏时长、互动反馈、产品信息与评论情感倾向，识别潜在流失风险，
                        并通过客户分群、模型解释和挽留建议辅助运营决策。
                    </div>
                    <div class="hero-tags">
                        <span class="hero-tag">用户行为特征</span>
                        <span class="hero-tag">评论情感分析</span>
                        <span class="hero-tag">流失风险预测</span>
                        <span class="hero-tag">客户分群</span>
                        <span class="hero-tag">挽留策略</span>
                    </div>
                </div>
                <div class="hero-summary">
                    <div class="hero-summary-card">
                        <div class="hero-summary-label">当前样本</div>
                        <div class="hero-summary-value">{len(df):,}</div>
                        <div class="hero-summary-note">已按侧边栏筛选</div>
                    </div>
                    <div class="hero-summary-card">
                        <div class="hero-summary-label">流失率</div>
                        <div class="hero-summary-value">{format_rate(churn_rate)}</div>
                        <div class="hero-summary-note">当前客户群体风险</div>
                    </div>
                    <div class="hero-summary-card">
                        <div class="hero-summary-label">正面评论</div>
                        <div class="hero-summary-value">{format_rate(positive_rate)}</div>
                        <div class="hero-summary-note">基于好评/差评信号</div>
                    </div>
                    <div class="hero-summary-card">
                        <div class="hero-summary-label">产品数</div>
                        <div class="hero-summary-value">{product_count}</div>
                        <div class="hero-summary-note">覆盖 Steam 产品</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_pipeline_status()

    with st.expander("系统说明", expanded=False):
        st.markdown(
            """
            **数据来源**：实时爬取 Steam 公开评论 API，获取用户行为、互动反馈与评论情感数据。

            **分析流程**：
            1. **实时爬取** -> 从公开 API 获取用户评论、游戏时长、评分等真实数据
            2. **NLP 情感分析** -> 基于词典的情感评分 + jieba 分词 + 词云可视化
            3. **客户分群** -> K-Means 客户分群，识别不同活跃度和风险群体
            4. **多模型对比** -> 多个分类模型 + GridSearchCV 超参优化 + Stacking 集成
            5. **标准流程分析** -> 对比、分组、交叉、回归、时间序列和关联规则分析
            6. **模型解释性分析** -> SHAP 或特征重要性图解释关键风险因素
            7. **挽留建议** -> 基于分析结果输出分层差异化挽留策略
            """
        )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("样本数", f"{len(df):,}")
    col2.metric("流失率", format_rate(churn_rate))

    if "playtime_hours" in df.columns:
        col3.metric("平均使用时长", f"{df['playtime_hours'].mean():.1f}h")
    if "engagement_score" in df.columns:
        col4.metric("平均参与度", f"{df['engagement_score'].mean():.2f}")

    st.progress(float(min(max(churn_rate, 0), 1)), text=f"当前筛选样本流失水平：{format_rate(churn_rate)}")

def render_overview(df: pd.DataFrame) -> None:
    st.subheader("业务概览 - 流失特征分析")
    st.caption("从使用时长、产品、参与度等维度分析哪些用户更容易流失。")
    churn_col = TARGET_COLUMN if TARGET_COLUMN in df.columns else "Churn"
    overview_insights: list[str] = []

    left, right = st.columns(2)
    with left:
        if "playtime_tier" in df.columns:
            chart = df.groupby("playtime_tier", observed=False)[churn_col].mean().sort_values(ascending=False)
            st.write("按使用时长的流失率")
            chart.index = [PLAYTIME_TIER_LABELS.get(str(value), str(value)) for value in chart.index]
            render_horizontal_bar(chart, category_title="使用时长", value_title="流失率", height=280)
            overview_insights.append(
                f"使用时长维度中，“{chart.index[0]}”流失率最高，为 {chart.iloc[0]:.1%}，说明低时长或特定使用阶段用户需要优先运营触达。"
            )
        elif "Contract" in df.columns:
            chart = df.groupby("Contract")[churn_col].mean().sort_values(ascending=False)
            st.write("按合约类型的流失率")
            render_horizontal_bar(chart, category_title="合约类型", value_title="流失率", height=280)
            overview_insights.append(f"合约类型中，“{chart.index[0]}”流失率最高，为 {chart.iloc[0]:.1%}。")

    with right:
        if "app_name" in df.columns:
            chart = df.groupby("app_name")[churn_col].mean().sort_values(ascending=False)
            st.write("按产品的流失率")
            render_horizontal_bar(chart, category_title="产品", value_title="流失率", height=280)
            overview_insights.append(
                f"产品维度中，“{chart.index[0]}”流失率最高，为 {chart.iloc[0]:.1%}；“{chart.index[-1]}”相对最低，为 {chart.iloc[-1]:.1%}。"
            )
        elif "PaymentMethod" in df.columns:
            chart = df.groupby("PaymentMethod")[churn_col].mean().sort_values(ascending=False)
            st.write("按支付方式的流失率")
            render_horizontal_bar(chart, category_title="支付方式", value_title="流失率", height=280)
            overview_insights.append(f"支付方式中，“{chart.index[0]}”流失率最高，为 {chart.iloc[0]:.1%}。")

    render_insight_panel("业务概览关键结论", overview_insights)

    left, right = st.columns(2)
    with left:
        if "sentiment_label" in df.columns:
            crosstab = pd.crosstab(df["sentiment_label"], df[churn_col], normalize="index")
            crosstab.index = [sentiment_label(value) for value in crosstab.index]
            st.write("情感倾向 vs 流失率")
            chart = crosstab[1] if 1 in crosstab.columns else crosstab.iloc[:, 0]
            render_horizontal_bar(chart, category_title="情感倾向", value_title="流失率", height=260)
            st.info(
                f"情感维度显示，“{chart.sort_values(ascending=False).index[0]}”用户流失率最高，"
                f"为 {chart.max():.1%}。这说明评论情绪可以作为风险识别的直接信号。"
            )

    with right:
        if "playtime_hours" in df.columns:
            bins = [0, 2, 10, 50, 200, 500, float("inf")]
            labels = ["<2h", "2-10h", "10-50h", "50-200h", "200-500h", ">500h"]
            df_temp = df.copy()
            df_temp["hours_bin"] = pd.cut(df_temp["playtime_hours"], bins=bins, labels=labels)
            chart = df_temp.groupby("hours_bin", observed=False)[churn_col].mean()
            st.write("使用时长与流失率趋势")
            render_line_chart(chart, category_title="使用时长区间", value_title="流失率", height=260)
            st.info(
                "趋势图用于观察使用时长和流失率是否呈现单调变化。若短时长区间明显更高，说明新用户冷启动和早期体验是挽留重点。"
            )


def render_realtime_collection() -> None:
    st.subheader("实时数据采集")
    st.caption("选择数据源后点击按钮，系统会从 Steam 公开评论接口采集最新评论；网络不可用时会自动保留本地缓存或使用备用数据。")

    with st.form("realtime_collection_form"):
        col1, col2, col3 = st.columns([1.1, 1.2, 0.8])
        keyword = col1.text_input("搜索关键词", value="游戏用户评论")
        selected_apps = col2.multiselect(
            "数据源（可多选）",
            options=STEAM_APP_IDS,
            default=[730, 570, 440],
            format_func=lambda app_id: f"{APP_LABELS.get(app_id, str(app_id))}（{app_id}）",
        )
        pages_per_app = col3.number_input("每个产品采集页数", min_value=1, max_value=5, value=1, step=1)

        submitted = st.form_submit_button("开始实时采集", type="primary", use_container_width=True)

    if submitted:
        if not selected_apps:
            st.warning("请至少选择一个数据源。")
            return

        progress = st.progress(0, text="正在连接公开评论接口...")
        status = st.empty()
        status.info(f"采集关键词：{keyword}；目标产品：{len(selected_apps)} 个；每个产品 {pages_per_app} 页。")

        try:
            with st.spinner("正在实时采集公开评论数据，请稍候..."):
                collected_df = scrape_steam_reviews(app_ids=selected_apps, pages_per_app=int(pages_per_app))
        except Exception as exc:
            progress.empty()
            st.error(f"实时采集失败：{exc}")
            st.info("可以稍后重试，或先使用本地缓存数据继续演示。")
            return

        progress.progress(1.0, text="实时采集完成")
        cleaned_collection = clean_dataset(collected_df)
        cleaned_collection.to_csv(PROCESSED_DATA_PATH, index=False, encoding="utf-8-sig")
        load_data.clear()
        load_nlp_results.clear()
        load_cluster_results.clear()
        load_metrics.clear()
        load_importance.clear()

        st.success(f"采集完成，共获得 {len(collected_df):,} 条评论数据，并已同步生成清洗数据。")
        if not collected_df.empty:
            info = get_data_source_info(cleaned_collection)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("样本量", f"{info.get('total_records', 0):,}")
            c2.metric("产品数", f"{info.get('apps_count', 0)}")
            c3.metric("正面评论", f"{info.get('positive_rate', 0):.1%}")
            c4.metric("估计流失率", f"{info.get('churn_rate', 0):.1%}")
            preview_columns = [
                column
                for column in ["app_id", "app_name", "review_text", "voted_up", "playtime_hours"]
                if column in collected_df.columns
            ]
            st.dataframe(
                collected_df[preview_columns].head(20),
                use_container_width=True,
                hide_index=True,
            )
            st.info("清洗数据已同步更新；如需刷新模型、聚类、NLP 和图表，请运行 `python run_project.py`。")
        return

    if SCRAPED_DATA_PATH.exists():
        cached_df = pd.read_csv(SCRAPED_DATA_PATH, encoding="utf-8-sig")
        info = get_data_source_info(cached_df)
        st.write("当前本地采集数据")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("样本量", f"{info.get('total_records', 0):,}")
        c2.metric("产品数", f"{info.get('apps_count', 0)}")
        c3.metric("正面评论", f"{info.get('positive_rate', 0):.1%}")
        c4.metric("估计流失率", f"{info.get('churn_rate', 0):.1%}")
        c5.metric("最后更新", info.get("last_updated", "N/A"))
        preview_columns = [c for c in ["app_id", "app_name", "review_text", "voted_up", "playtime_hours"] if c in cached_df.columns]
        st.dataframe(cached_df[preview_columns].head(20), use_container_width=True, hide_index=True)
    else:
        st.info("当前还没有本地采集数据，请选择数据源后点击“开始实时采集”。")


def render_nlp_section(df: pd.DataFrame) -> None:
    st.subheader("NLP 文本挖掘 - 情感分析")
    st.caption("基于词典的情感分析 + jieba 中文分词，挖掘用户评论中的情感倾向与流失信号。")

    nlp_df = load_nlp_results()
    if nlp_df.empty:
        st.info("尚未找到 NLP 分析结果，请先运行 `python run_project.py`。")
        return

    metric_cols = st.columns(4)
    if "sentiment_label" in nlp_df.columns:
        dist = nlp_df["sentiment_label"].value_counts(normalize=True)
        metric_cols[0].metric("正面评论占比", format_rate(dist.get("positive", 0)))
        metric_cols[1].metric("中性评论占比", format_rate(dist.get("neutral", 0)))
        metric_cols[2].metric("负面评论占比", format_rate(dist.get("negative", 0)))
    if "sentiment_score" in nlp_df.columns:
        metric_cols[3].metric("平均情感分数", f"{nlp_df['sentiment_score'].mean():.3f}")

    nlp_insights: list[str] = []
    if "sentiment_label" in nlp_df.columns:
        dist = nlp_df["sentiment_label"].value_counts(normalize=True)
        dominant_label = sentiment_label(str(dist.idxmax()))
        nlp_insights.append(f"当前评论中占比最高的情感类型是“{dominant_label}”，占比 {dist.max():.1%}。")
    if TARGET_COLUMN in df.columns and "sentiment_label" in df.columns:
        sentiment_churn_rate = df.groupby("sentiment_label", observed=False)[TARGET_COLUMN].mean().sort_values(ascending=False)
        if not sentiment_churn_rate.empty:
            nlp_insights.append(
                f"从流失风险看，“{sentiment_label(str(sentiment_churn_rate.index[0]))}”评论用户的流失率最高，"
                f"为 {sentiment_churn_rate.iloc[0]:.1%}。"
            )
    render_insight_panel("情感分析结论", nlp_insights)

    st.markdown('<div class="chart-title">情感分布总览</div>', unsafe_allow_html=True)
    sentiment_dist = DEEP_MINING_DIR / "nlp_sentiment_distribution.png"
    if sentiment_dist.exists():
        st.image(str(sentiment_dist), caption="情感类型占比与情感分数分布", use_container_width=True)
        st.caption("该图用于说明评论整体情绪结构：负面评论越集中，越需要结合产品体验和客服反馈做原因定位。")
    else:
        st.info("尚未生成情感分布图。")

    st.markdown('<div class="chart-title">流失客户与留存客户情感对比</div>', unsafe_allow_html=True)
    sentiment_churn = DEEP_MINING_DIR / "nlp_sentiment_by_churn.png"
    if sentiment_churn.exists():
        st.image(str(sentiment_churn), caption="不同客户状态下的平均情感分与情感倾向结构", use_container_width=True)
        st.caption("该图用于对比流失客户和留存客户的情绪差异，重点看流失客户是否负面情绪更集中。")
    else:
        st.info("尚未生成流失与留存情感对比图。")

    st.markdown('<div class="chart-title">评论词云</div>', unsafe_allow_html=True)
    wordcloud_items = [
        ("all", "全量评论词云"),
        ("churn", "流失客户词云"),
        ("retain", "留存客户词云"),
    ]
    first_row = st.columns([1, 1])
    for column, (tag, caption) in zip(first_row, wordcloud_items[:2]):
        wc_path = DEEP_MINING_DIR / f"wordcloud_{tag}.png"
        if wc_path.exists():
            column.image(str(wc_path), caption=caption, use_container_width=True)

    retain_path = DEEP_MINING_DIR / "wordcloud_retain.png"
    if retain_path.exists():
        st.image(str(retain_path), caption="留存客户词云", use_container_width=True)
        st.caption("词云适合作为定性补充，用来解释用户评论中反复出现的体验主题，但不能单独作为统计结论。")

    keywords_path = DEEP_MINING_DIR / "nlp_top_keywords.png"
    if keywords_path.exists():
        st.markdown('<div class="chart-title">高频关键词对比</div>', unsafe_allow_html=True)
        st.image(str(keywords_path), caption="全量、流失客户与留存客户高频关键词对比", use_container_width=True)

def render_cluster_section() -> None:
    st.subheader("深度挖掘 - 客户聚类分群")
    st.caption("使用 K-Means 聚类将客户分为不同群体，识别高价值客群与高风险客群。")

    cluster_img = DEEP_MINING_DIR / "cluster_analysis.png"
    if cluster_img.exists():
        st.image(str(cluster_img), caption="聚类分析可视化", use_container_width=True)
        st.caption("聚类图展示用户在行为特征空间中的分布，相近的点代表行为画像相似。该图主要用于找不同运营分层，而不是直接判断单个用户是否流失。")

    cluster_df = load_cluster_results()
    if not cluster_df.empty and "cluster" in cluster_df.columns:
        st.write("各分群统计特征")
        n_clusters = cluster_df["cluster"].nunique()
        cols = st.columns(n_clusters)
        for i in range(n_clusters):
            cluster_data = cluster_df[cluster_df["cluster"] == i]
            with cols[i]:
                st.metric(f"分群 {i}", f"{len(cluster_data)} 人")
                if TARGET_COLUMN in cluster_data.columns:
                    st.caption(f"流失率: {cluster_data[TARGET_COLUMN].mean():.1%}")
        if TARGET_COLUMN in cluster_df.columns:
            cluster_summary = cluster_df.groupby("cluster")[TARGET_COLUMN].agg(["mean", "count"]).sort_values("mean", ascending=False)
            high_cluster = cluster_summary.iloc[0]
            low_cluster = cluster_summary.iloc[-1]
            render_insight_panel(
                "聚类分群结论",
                [
                    f"分群 {cluster_summary.index[0]} 的流失率最高，为 {high_cluster['mean']:.1%}，样本数 {int(high_cluster['count'])}。",
                    f"分群 {cluster_summary.index[-1]} 的流失率最低，为 {low_cluster['mean']:.1%}，可作为相对稳定客群进行画像对比。",
                    "运营上建议把高风险分群作为优先触达对象，再结合评论情绪和使用时长制定差异化策略。",
                ],
            )


def render_model_section() -> None:
    st.subheader("深度挖掘 - 模型评估与对比")
    st.caption("6 个模型 + GridSearchCV 超参优化 + Stacking 集成，全面评估预测能力。")

    metrics_df = load_metrics()
    importance_df = load_importance()

    if metrics_df.empty:
        st.info("尚未找到模型评估结果，请先运行 `python run_project.py`。")
        return

    best = metrics_df.sort_values(["f1_score", "roc_auc"], ascending=False).iloc[0]
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("最佳模型", MODEL_LABELS.get(str(best["model"]), str(best["model"])))
    col2.metric("准确率", f"{best['accuracy']:.3f}")
    col3.metric("查准率", f"{best['precision']:.3f}")
    col4.metric("召回率", f"{best['recall']:.3f}")
    col5.metric("F1 分数", f"{best['f1_score']:.3f}")

    auc_value = float(best.get("roc_auc", 0))
    model_note = (
        "当前模型 AUC 接近 0.5，说明公开评论与行为特征对流失标签的区分度有限；"
        "页面结果更适合作为课程项目中的风险排序和运营辅助演示，不宜表述为高精度自动决策模型。"
        if auc_value < 0.6
        else "当前模型 AUC 高于 0.6，具备一定排序能力，但仍建议结合业务规则和人工复核使用。"
    )
    render_insight_panel(
        "模型评估结论",
        [
            f"综合 F1 和 AUC 排序，当前最佳模型是“{MODEL_LABELS.get(str(best['model']), str(best['model']))}”。",
            f"该模型准确率 {best['accuracy']:.3f}，召回率 {best['recall']:.3f}，F1 分数 {best['f1_score']:.3f}，AUC {best['roc_auc']:.3f}。",
            model_note,
        ],
    )

    display_metrics = metrics_df.copy()
    display_metrics["model"] = display_metrics["model"].map(lambda v: MODEL_LABELS.get(v, v))
    display_metrics = display_metrics.rename(
        columns={
            "model": "模型", "accuracy": "准确率", "precision": "查准率",
            "recall": "召回率", "f1_score": "F1分数", "roc_auc": "AUC",
        }
    )
    st.dataframe(display_metrics, use_container_width=True, hide_index=True)

    if not importance_df.empty:
        st.write("前 15 个关键影响因素")
        feature_display = importance_df.copy()
        feature_display["feature"] = feature_display["feature"].map(feature_label)
        top_features = feature_display.head(15).set_index("feature")["importance"]
        render_horizontal_bar(
            top_features,
            category_title="影响因素",
            value_title="重要性",
            height=420,
            value_format=".3f",
        )

    shap_img = SHAP_PATH
    if shap_img.exists() or not importance_df.empty:
        st.subheader("模型解释性分析")
        st.caption("解释模型主要依据哪些变量判断流失风险。主图展示全局重要性排序，数值越大代表模型越依赖该因素。")
        if not importance_df.empty:
            explanation_features = importance_df.copy()
            explanation_features["feature"] = explanation_features["feature"].map(feature_label)
            explanation_features = explanation_features.head(10).set_index("feature")["importance"]
            render_horizontal_bar(
                explanation_features,
                category_title="影响因素",
                value_title="重要性",
                height=340,
                value_format=".3f",
                color="#2563eb",
            )
            top_name = str(explanation_features.index[0])
            st.info(
                f"当前模型最依赖的因素是“{top_name}”。这里的“重要性”表示该变量对模型区分流失/留存的贡献大小，"
                "不是业务上的正负因果关系；要判断它是推高还是降低单个用户的流失概率，需要看 SHAP 归因方向或单客预测结果。"
            )

        if shap_img.exists():
            with st.expander("查看原始 SHAP 散点归因图（技术细节）", expanded=True):
                st.caption(
                    "SHAP 图中每个点代表一条样本在某个特征上的归因：越靠右越推高流失预测，越靠左越降低流失预测。"
                    "原图标签较长且包含 one-hot 编码后的产品 ID、月份、小时等特征，所以直接展示时会显得拥挤。"
                )
                st.image(str(shap_img), caption="原始 SHAP 特征归因图", use_container_width=True)


def render_deep_evaluation() -> None:
    st.subheader("深度挖掘 - 模型稳定性评估")
    st.caption("交叉验证 + 学习曲线 + 混淆矩阵，全面评估模型泛化能力。")

    col1, col2 = st.columns(2)
    with col1:
        lc_path = DEEP_MINING_DIR / "learning_curve.png"
        if lc_path.exists():
            st.image(str(lc_path), caption="学习曲线", use_container_width=True)
            st.caption("学习曲线用于观察训练样本增加后模型表现是否稳定；若训练分数和验证分数差距大，说明可能过拟合。")

    with col2:
        cm_path = DEEP_MINING_DIR / "confusion_matrix.png"
        if cm_path.exists():
            st.image(str(cm_path), caption="混淆矩阵", use_container_width=True)
            st.caption("混淆矩阵展示预测正确和错误的样本数量，重点关注流失客户被误判为留存的情况，因为这会导致错过挽留机会。")


def render_plots_gallery() -> None:
    st.subheader("项目输出图表")
    st.caption("分析流程自动生成的可视化图表，可作为课程报告素材。")
    plot_files = sorted(PLOTS_DIR.glob("*.png"))
    if not plot_files:
        st.info("尚未找到图表文件，请先运行 `python run_project.py`。")
        return

    cols = st.columns(2)
    for idx, pf in enumerate(plot_files):
        with cols[idx % 2]:
            st.image(str(pf), caption=PLOT_LABELS.get(pf.stem, pf.stem), use_container_width=True)
            explanation = PLOT_EXPLANATIONS.get(pf.stem)
            if explanation:
                st.caption(explanation)


def get_risk_message(probability: float) -> tuple[str, str]:
    for threshold, level, message in RISK_LEVELS:
        if probability >= threshold:
            return level, message
    return RISK_LEVELS[-1][1], RISK_LEVELS[-1][2]


def render_prediction_tool(raw_df: pd.DataFrame) -> None:
    st.subheader("单客户流失预测")
    st.caption("模拟企业实际使用场景，输入用户画像和行为数据，输出流失概率、风险等级和挽留建议。")

    bundle = load_model()
    if bundle is None:
        st.warning("尚未找到训练好的模型，请先运行 `python run_project.py`。")
        return

    model = bundle["model"]
    feature_columns = bundle["feature_columns"]

    with st.form("prediction_form"):
        st.write("用户行为特征")
        col1, col2, col3 = st.columns(3)

        playtime = col1.slider("游戏时长 (小时)", 0.0, 5000.0, 50.0, step=1.0)
        playtime_at_review = col2.slider("评论时游戏时长 (小时)", 0.0, 5000.0, 30.0, step=1.0)
        num_games = col3.slider("拥有游戏数", 1, 500, 20)

        num_reviews = col1.slider("历史评论数", 0, 100, 3)
        votes_up = col2.slider("获赞数", 0, 500, 5)
        votes_funny = col3.slider("趣味投票数", 0, 100, 1)

        comment_count = col1.slider("评论回复数", 0, 50, 2)
        review_length = col2.slider("评论长度 (字符)", 10, 5000, 200)
        review_word_count = col3.slider("评论词数", 5, 1000, 50)

        st.write("用户属性")
        col1, col2, col3 = st.columns(3)
        is_negative = col1.selectbox("是否差评", [0, 1], format_func=lambda v: "是" if v else "否")
        is_free = col2.selectbox("是否免费获取", [0, 1], format_func=lambda v: "是" if v else "否")
        is_ea = col3.selectbox("是否抢先体验", [0, 1], format_func=lambda v: "是" if v else "否")

        playtime_tier = col1.selectbox(
            "使用时长层级",
            ["极短(<2h)", "短(2-10h)", "中(10-50h)", "长(50-200h)", "很长(200-1000h)", "超长(>1000h)"],
        )
        app_id = col2.selectbox("产品 ID", [730, 570, 440, 578080, 271590, 1172470, 1938090, 252490, 292030, 359550])
        review_hour = col3.slider("评论时间 (小时)", 0, 23, 14)

        engagement_score = (
            votes_up * 0.4 + comment_count * 0.3 + 0.2 + (review_length / 500) * 0.1
        )
        playtime_scale = math.log1p(playtime) / math.log1p(5000)
        social_feedback = math.log1p(votes_up + comment_count) / math.log1p(550)
        risk_logit = (
            -0.55
            + is_negative * 1.15
            + (1 if playtime < 2 else 0) * 0.75
            + (1 if 2 <= playtime < 10 else 0) * 0.35
            + (1 if review_length < 40 else 0) * 0.35
            + (1 if num_reviews <= 1 else 0) * 0.2
            + is_free * 0.2
            + is_ea * 0.15
            - playtime_scale * 0.45
            - social_feedback * 0.25
        )
        churn_signal = 1 / (1 + math.exp(-risk_logit))

        submitted = st.form_submit_button("开始预测", type="primary", use_container_width=True)

    if not submitted:
        return

    sample_data = {
        "author_playtime_forever": playtime * 60,
        "author_playtime_at_review": playtime_at_review * 60,
        "author_num_games_owned": num_games,
        "author_num_reviews": num_reviews,
        "votes_up": votes_up,
        "votes_funny": votes_funny,
        "weighted_vote_score": 0.5,
        "comment_count": comment_count,
        "review_length": review_length,
        "review_word_count": review_word_count,
        "playtime_hours": playtime,
        "playtime_at_review_hours": playtime_at_review,
        "engagement_score": engagement_score,
        "churn_signal": churn_signal,
        "app_id": str(app_id),
        "is_negative": str(is_negative),
        "is_free_copy": str(is_free),
        "is_early_access": str(is_ea),
        "playtime_tier": playtime_tier,
        "review_month": "2024-06",
        "review_hour": str(review_hour),
    }

    sample_df = pd.DataFrame([sample_data])
    sample_df = pd.get_dummies(sample_df, columns=CATEGORICAL_COLUMNS, drop_first=False)
    sample_df = sanitize_feature_columns(sample_df)
    sample_df = sample_df.reindex(columns=feature_columns, fill_value=0)

    try:
        model_probability = float(model.predict_proba(sample_df)[0][1])
    except Exception:
        model_probability = 0.5

    probability = float(min(max(model_probability * 0.7 + churn_signal * 0.3, 0), 1))

    level, message = get_risk_message(probability)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("综合流失概率", f"{probability:.2%}")
        st.caption(f"模型概率 {model_probability:.1%}；规则风险信号 {churn_signal:.1%}")
    with col2:
        if level == "高风险":
            st.error(f"风险等级：{level}\n\n{message}")
        elif level == "中风险":
            st.warning(f"风险等级：{level}\n\n{message}")
        else:
            st.success(f"风险等级：{level}\n\n{message}")

    st.markdown("### 深度洞察与建议")
    insights_col1, insights_col2 = st.columns(2)
    with insights_col1:
        st.info(
            f"用户画像分析\n\n"
            f"游戏时长：{playtime:.0f} 小时（{playtime_tier}）\n\n"
            f"拥有游戏：{num_games} 款\n\n"
            f"历史评论：{num_reviews} 条\n\n"
            f"参与度评分：{engagement_score:.2f}"
        )
    with insights_col2:
        st.info(
            f"风险因素识别\n\n"
            f"差评信号：{'是' if is_negative else '否'}\n\n"
            f"低活跃度：{'是' if playtime < 2 else '否'}\n\n"
            f"免费获取：{'是' if is_free else '否'}\n\n"
            f"流失信号分：{churn_signal:.2f}"
        )
    render_insight_panel(
        "单客预测结论",
        [
            f"该用户当前预测流失概率为 {probability:.1%}，风险等级为“{level}”。",
            "综合概率由训练模型输出和页面实时规则风险信号共同构成，避免表单中的差评、低时长等业务字段在展示层失效。",
            "若用户同时存在差评、低使用时长或低互动反馈，应优先采取客服触达、问题修复说明和定向活动召回。",
            "单客预测结果应作为运营优先级参考，不建议脱离用户评论原文和近期行为直接做最终判断。",
        ],
    )


def main() -> None:
    inject_styles()
    raw_df, cleaned_df = load_data()
    filtered_df = filter_data(cleaned_df)

    if filtered_df.empty:
        st.warning("当前筛选条件下没有样本，请放宽筛选范围。")
        return

    render_business_assistant_panel(filtered_df, compact=True)
    render_header(filtered_df)

    tabs = st.tabs([
        "实时采集", "数据概览", "AI业务助手", "情感分析",
        "聚类分群", "模型评估", "单客预测", "输出图表",
    ])

    with tabs[0]:
        render_realtime_collection()
    with tabs[1]:
        render_overview(filtered_df)
    with tabs[2]:
        render_business_assistant_panel(filtered_df, compact=False)
    with tabs[3]:
        render_nlp_section(filtered_df)
    with tabs[4]:
        render_cluster_section()
    with tabs[5]:
        render_model_section()
        render_deep_evaluation()
    with tabs[6]:
        render_prediction_tool(raw_df)
    with tabs[7]:
        render_plots_gallery()


if __name__ == "__main__":
    main()
