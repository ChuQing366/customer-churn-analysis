from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


sns.set_theme(style="whitegrid")
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _annotate_rate_bars(ax: plt.Axes) -> None:
    for patch in ax.patches:
        height = patch.get_height()
        if np.isnan(height):
            continue
        ax.text(
            patch.get_x() + patch.get_width() / 2,
            height + 0.01,
            _format_percent(height),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="#333333",
        )


def create_visualizations(df: pd.DataFrame, output_dir: Path) -> None:
    _plot_churn_distribution(df, output_dir)
    _plot_playtime_churn_rate(df, output_dir)
    _plot_app_churn_rate(df, output_dir)
    _plot_engagement_vs_churn(df, output_dir)
    _plot_sentiment_timeline(df, output_dir)


def _save_current_plot(output_dir: Path, filename: str) -> None:
    plt.tight_layout()
    plt.savefig(output_dir / filename, dpi=220, bbox_inches="tight")
    plt.close()


def _plot_churn_distribution(df: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    churn_col = "churn_label" if "churn_label" in df.columns else "Churn"
    if churn_col not in df.columns:
        return

    if churn_col == "Churn":
        label_map = {0: "Retained", 1: "Churned"}
    else:
        label_map = {0: "留存客户", 1: "流失客户"}

    counts = df[churn_col].map(label_map).value_counts()
    colors = ["#2ca02c", "#d62728"]
    labels = [f"{name}\n{count}人" for name, count in counts.items()]
    wedges, _, _ = ax.pie(
        counts.values,
        labels=labels,
        autopct="%.1f%%",
        startangle=90,
        colors=colors,
        textprops={"fontsize": 11},
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    ax.set_title("客户流失总体分布\n颜色区分客户状态，数字表示样本占比", fontsize=15, fontweight="bold")
    ax.legend(wedges, counts.index, title="客户状态", loc="center left", bbox_to_anchor=(1.0, 0.5))
    _save_current_plot(output_dir, "01_churn_distribution.png")


def _plot_playtime_churn_rate(df: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 6))
    churn_col = "churn_label" if "churn_label" in df.columns else "Churn"

    if "playtime_tier" in df.columns:
        chart = df.groupby("playtime_tier", observed=False)[churn_col].mean().sort_values(ascending=False)
        sns.barplot(x=chart.index, y=chart.values, hue=chart.index, legend=False, palette="Reds_d", ax=ax)
        ax.set_title("不同游戏时长层级的客户流失率\n柱形越高表示该时长层级的流失风险越高", fontsize=15, fontweight="bold")
        ax.set_xlabel("游戏时长层级", fontsize=12)
        ax.set_ylabel("流失率", fontsize=12)
        ax.set_ylim(0, min(1.0, max(chart.values) + 0.15))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: _format_percent(y)))
        ax.tick_params(axis="x", rotation=20)
        _annotate_rate_bars(ax)
    elif "tenure" in df.columns:
        chart = df.groupby("Contract", as_index=False)[churn_col].mean()
        sns.barplot(data=chart, x="Contract", y=churn_col, hue="Contract", legend=False, palette="Blues_d", ax=ax)
        ax.set_title("不同合约类型的流失率", fontsize=15, fontweight="bold")
        ax.set_xlabel("合约类型")
        ax.set_ylabel("流失率")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: _format_percent(y)))
        _annotate_rate_bars(ax)

    _save_current_plot(output_dir, "02_contract_churn_rate.png")


def _plot_app_churn_rate(df: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    churn_col = "churn_label" if "churn_label" in df.columns else "Churn"

    if "app_name" in df.columns:
        chart = df.groupby("app_name")[churn_col].mean().sort_values(ascending=False)
        sns.barplot(x=chart.index, y=chart.values, hue=chart.index, legend=False, palette="Oranges_d", ax=ax)
        ax.set_title("不同产品的客户流失率\n用于比较各产品用户留存风险差异", fontsize=15, fontweight="bold")
        ax.set_xlabel("产品名称", fontsize=12)
        ax.set_ylabel("流失率", fontsize=12)
        ax.set_ylim(0, min(1.0, max(chart.values) + 0.15))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: _format_percent(y)))
        ax.tick_params(axis="x", rotation=30)
        _annotate_rate_bars(ax)
    elif "PaymentMethod" in df.columns:
        chart = df.groupby("PaymentMethod", as_index=False)[churn_col].mean().sort_values(churn_col, ascending=False)
        sns.barplot(data=chart, x="PaymentMethod", y=churn_col, hue="PaymentMethod", legend=False, palette="Oranges_d", ax=ax)
        ax.set_title("不同支付方式的流失率", fontsize=15, fontweight="bold")
        ax.set_xlabel("支付方式")
        ax.set_ylabel("流失率")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: _format_percent(y)))
        ax.tick_params(axis="x", rotation=20)
        _annotate_rate_bars(ax)

    _save_current_plot(output_dir, "03_region_churn_rate.png")


def _plot_engagement_vs_churn(df: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    churn_col = "churn_label" if "churn_label" in df.columns else "Churn"

    if "playtime_hours" in df.columns and "engagement_score" in df.columns:
        label_map = {0: "留存客户", 1: "流失客户"}
        sns.scatterplot(
            data=df,
            x="playtime_hours",
            y="engagement_score",
            hue=df[churn_col].map(label_map),
            alpha=0.6,
            s=48,
            palette={"留存客户": "#2ca02c", "流失客户": "#d62728"},
            ax=ax,
        )
        ax.set_title("游戏时长与参与度关系\n每个点代表一位客户，颜色表示客户状态", fontsize=15, fontweight="bold")
        ax.set_xlabel("游戏时长（小时）", fontsize=12)
        ax.set_ylabel("参与度分数", fontsize=12)
        ax.legend(title="客户状态", loc="best")
        ax.text(
            0.02,
            0.98,
            "观察重点：红色点若集中在低时长/低参与度区域，说明活跃不足与流失风险相关",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=10,
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
        )
    elif "MonthlyCharges" in df.columns and "tenure" in df.columns:
        label_map = {0: "Retained", 1: "Churned"}
        sns.scatterplot(
            data=df,
            x="MonthlyCharges",
            y="tenure",
            hue=df[churn_col].map(label_map),
            alpha=0.65,
            ax=ax,
        )
        ax.set_title("月消费金额与在网月数关系", fontsize=15, fontweight="bold")
        ax.set_xlabel("月消费金额")
        ax.set_ylabel("在网月数")
        ax.legend(title="客户状态", loc="best")

    _save_current_plot(output_dir, "04_fee_vs_activity.png")


def _plot_sentiment_timeline(df: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    churn_col = "churn_label" if "churn_label" in df.columns else "Churn"

    if "review_month" in df.columns and "sentiment_score" in df.columns:
        chart = df.groupby(["review_month", churn_col], observed=False)["sentiment_score"].mean().reset_index()
        label_map = {0: "留存客户", 1: "流失客户"}
        chart["group"] = chart[churn_col].map(label_map)
        sns.lineplot(data=chart, x="review_month", y="sentiment_score", hue="group", marker="o", linewidth=2.2, ax=ax)
        ax.axhline(0, color="#666666", linestyle="--", linewidth=1, label="中性情感线")
        ax.set_title("不同客户群体的情感分数变化趋势\n高于0偏正面，低于0偏负面", fontsize=15, fontweight="bold")
        ax.set_xlabel("评论月份", fontsize=12)
        ax.set_ylabel("平均情感分数", fontsize=12)
        ax.tick_params(axis="x", rotation=30)
        ax.legend(title="客户状态/参考线", loc="best")
    elif "tenure" in df.columns:
        bins = pd.cut(df["tenure"], bins=[0, 12, 24, 36, 48, 60, 72], include_lowest=True)
        chart = (
            df.assign(tenure_group=bins)
            .groupby(["tenure_group", churn_col], observed=False)["MonthlyCharges"]
            .mean()
            .reset_index()
        )
        label_map = {0: "Retained", 1: "Churned"}
        chart["group"] = chart[churn_col].map(label_map)
        chart["tenure_group"] = chart["tenure_group"].astype(str)
        sns.lineplot(data=chart, x="tenure_group", y="MonthlyCharges", hue="group", marker="o", ax=ax)
        ax.set_title("不同生命周期客户的平均消费变化", fontsize=15, fontweight="bold")
        ax.set_xlabel("在网时长范围")
        ax.set_ylabel("平均月消费")
        ax.tick_params(axis="x", rotation=20)

    _save_current_plot(output_dir, "05_login_trend_by_churn.png")
