from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


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
}


def feature_label(feature: str) -> str:
    if feature in FEATURE_LABELS:
        return FEATURE_LABELS[feature]
    if feature.startswith("app_id_"):
        return f"产品ID {feature.removeprefix('app_id_')}"
    if feature.startswith("review_month_"):
        return f"评论月份 {feature.removeprefix('review_month_')}"
    if feature.startswith("review_hour_"):
        return f"评论时段 {feature.removeprefix('review_hour_')}点"
    if feature.startswith("playtime_tier_"):
        return "使用时长层级 " + feature.removeprefix("playtime_tier_").replace("_", "")
    return feature


def main() -> None:
    importance_path = Path("outputs/feature_importance.csv")
    output_path = Path("outputs/plots/report_model_explainability.png")
    importance = pd.read_csv(importance_path).head(10).copy()
    importance["label"] = importance["feature"].map(feature_label)
    importance = importance.sort_values("importance", ascending=True)

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    bars = ax.barh(importance["label"], importance["importance"], color="#2f6fb0", alpha=0.88)
    ax.set_title("模型解释性分析：关键影响因素 Top 10", fontsize=17, fontweight="bold", pad=12)
    ax.set_xlabel("特征重要性（数值越大，模型越依赖该因素）", fontsize=11)
    ax.set_ylabel("")
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.003, bar.get_y() + bar.get_height() / 2, f"{width:.3f}", va="center", fontsize=9)
    ax.text(
        0.01,
        -0.18,
        "说明：该图展示全局重要性排序，用于解释模型主要依据哪些行为特征区分流失/留存；不直接代表因果关系。",
        transform=ax.transAxes,
        fontsize=9.5,
        color="#444444",
    )
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(output_path)


if __name__ == "__main__":
    main()
