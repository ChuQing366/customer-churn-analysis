from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from wordcloud import WordCloud

from .config import DEEP_MINING_DIR, NLP_RESULT_PATH

logger = logging.getLogger(__name__)

sns.set_theme(style="whitegrid")
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
    "什么", "怎么", "如何", "为什么", "可以", "还是", "但是", "因为", "所以",
    "如果", "虽然", "而且", "然后", "已经", "这个", "那个", "哪个", "一下",
    "一点", "一种", "一样", "一直", "一般", "一边", "一起", "之后", "之前",
    "之后", "里面", "外面", "上面", "下面", "前面", "后面", "时候", "地方",
    "觉得", "知道", "应该", "可能", "需要", "现在", "以后", "真的", "比较",
    "非常", "特别", "太", "很", "最", "更", "越", "只", "才", "就", "又",
    "还", "再", "把", "被", "让", "给", "从", "对", "跟", "向", "往",
    "用", "拿", "做", "搞", "弄", "玩", "打", "跑", "走", "吃", "喝",
    "买", "卖", "送", "给", "带", "帮", "叫", "问", "听", "见", "想",
    "能", "会", "敢", "肯", "愿", "要", "该", "得", "必须", "一定",
    "游戏", "感觉", "不错", "还行", "有点", "真的", "还是", "已经",
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "having", "do", "does", "did",
    "doing", "will", "would", "shall", "should", "may", "might",
    "must", "can", "could", "i", "you", "he", "she", "it", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his",
    "its", "our", "their", "mine", "yours", "hers", "ours", "theirs",
    "this", "that", "these", "those", "and", "but", "or", "nor",
    "not", "so", "yet", "for", "in", "on", "at", "to", "from",
    "with", "by", "about", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "of", "game",
    "play", "playing", "played", "time", "hours", "hour", "good",
    "bad", "great", "nice", "fun", "love", "like", "really",
    "just", "much", "well", "still", "even", "also", "very",
    "too", "only", "quite", "always", "never", "ever", "get",
    "got", "make", "made", "one", "two", "all", "some", "any",
    "more", "most", "many", "few", "little", "lot", "bit",
}

SENTIMENT_LEXICON_POSITIVE = {
    "好", "棒", "赞", "优秀", "出色", "精彩", "完美", "满意", "喜欢",
    "推荐", "值得", "不错", "好玩", "有趣", "刺激", "爽", "过瘾",
    "经典", "神作", "良心", "良心作", "佳作", "精品", "顶级", "一流",
    "流畅", "稳定", "优化好", "画质好", "音效好", "手感好", "平衡",
    "公平", "良心", "用心", "诚意", "惊喜", "惊艳", "震撼", "感动",
    "开心", "快乐", "享受", "沉浸", "上瘾", "沉迷", "停不下来",
    "awesome", "amazing", "excellent", "fantastic", "great",
    "wonderful", "perfect", "love", "best", "recommend", "fun",
    "addictive", "beautiful", "impressive", "outstanding", "superb",
}

SENTIMENT_LEXICON_NEGATIVE = {
    "差", "烂", "垃圾", "坑", "骗", "失望", "后悔", "不值", "浪费",
    "无聊", "枯燥", "单调", "重复", "肝", "氪", "氪金", "骗氪",
    "卡", "卡顿", "掉帧", "闪退", "崩溃", "BUG", "bug", "Bug",
    "外挂", "挂逼", "作弊", "脚本", "机器人", "炸鱼", "演员",
    "服务器差", "延迟高", "丢包", "掉线", "断线", "连接失败",
    "不平衡", "不公平", "恶心", "难受", "痛苦", "折磨", "劝退",
    "差评", "不推荐", "别买", "别玩", "卸载", "退款", "退坑",
    "垃圾游戏", "垃圾优化", "垃圾服务器", "垃圾匹配",
    "terrible", "horrible", "awful", "worst", "boring", "broken",
    "unplayable", "trash", "garbage", "waste", "disappointing",
    "buggy", "laggy", "unbalanced", "pay2win", "p2w", "dead",
}

SENTIMENT_MODIFIERS_NEGATION = {"不", "没", "无", "非", "别", "未", "否", "not", "no", "never", "neither", "nor"}
SENTIMENT_MODIFIERS_INTENSIFIER = {"非常", "特别", "极其", "十分", "太", "很", "最", "超级", "真的", "确实", "very", "really", "extremely", "so", "too", "highly", "absolutely"}


def analyze_sentiment(df: pd.DataFrame, text_column: str = "review_text") -> pd.DataFrame:
    logger.info("开始 NLP 情感分析...")
    try:
        import jieba
        jieba.setLogLevel(logging.WARNING)

        result_df = df.copy()
        texts = result_df[text_column].fillna("").astype(str).tolist()

        sentiments: list[dict[str, Any]] = []
        all_words: list[str] = []
        churn_words: list[str] = []
        retain_words: list[str] = []

        for idx, text in enumerate(texts):
            cleaned = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9\s]", " ", str(text))
            words = [w.strip().lower() for w in jieba.cut(cleaned) if w.strip() and len(w.strip()) >= 2]

            filtered_words = [w for w in words if w not in STOP_WORDS]
            all_words.extend(filtered_words)

            pos_count = sum(1 for w in filtered_words if w in SENTIMENT_LEXICON_POSITIVE)
            neg_count = sum(1 for w in filtered_words if w in SENTIMENT_LEXICON_NEGATIVE)

            total_sentiment_words = pos_count + neg_count
            if total_sentiment_words > 0:
                sentiment_score = (pos_count - neg_count) / total_sentiment_words
            else:
                sentiment_score = 0.0

            if sentiment_score > 0.1:
                sentiment_label = "positive"
            elif sentiment_score < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"

            is_churn = result_df.iloc[idx].get("churn_label", 0) == 1
            if is_churn:
                churn_words.extend(filtered_words)
            else:
                retain_words.extend(filtered_words)

            sentiments.append(
                {
                    "index": idx,
                    "sentiment_score": round(sentiment_score, 4),
                    "sentiment_label": sentiment_label,
                    "positive_words": pos_count,
                    "negative_words": neg_count,
                    "word_count": len(filtered_words),
                }
            )

        sentiment_df = pd.DataFrame(sentiments)
        result_df = pd.concat([result_df.reset_index(drop=True), sentiment_df.reset_index(drop=True)], axis=1)
        result_df.to_csv(NLP_RESULT_PATH, index=False, encoding="utf-8-sig")

        _plot_sentiment_distribution(result_df)
        _plot_wordcloud(all_words, "all", "全量评论词云")
        _plot_wordcloud(churn_words, "churn", "流失客户评论词云")
        _plot_wordcloud(retain_words, "retain", "留存客户评论词云")
        _plot_sentiment_by_churn(result_df)
        _plot_top_keywords(all_words, churn_words, retain_words)

        logger.info("NLP 情感分析完成，共分析 %d 条文本", len(texts))
        return result_df

    except ImportError:
        logger.warning("jieba 未安装，跳过中文分词，使用简单规则分析")
        return _simple_sentiment_analysis(df, text_column)
    except Exception as exc:
        logger.error("NLP 分析异常: %s", exc)
        return df


def _simple_sentiment_analysis(df: pd.DataFrame, text_column: str = "review_text") -> pd.DataFrame:
    result_df = df.copy()
    texts = result_df[text_column].fillna("").astype(str).tolist()

    sentiments = []
    for text in texts:
        text_lower = text.lower()
        pos_count = sum(1 for w in SENTIMENT_LEXICON_POSITIVE if w in text_lower)
        neg_count = sum(1 for w in SENTIMENT_LEXICON_NEGATIVE if w in text_lower)
        total = pos_count + neg_count
        score = (pos_count - neg_count) / total if total > 0 else 0.0
        label = "positive" if score > 0.1 else ("negative" if score < -0.1 else "neutral")
        sentiments.append(
            {
                "sentiment_score": round(score, 4),
                "sentiment_label": label,
                "positive_words": pos_count,
                "negative_words": neg_count,
                "word_count": len(text.split()),
            }
        )

    sentiment_df = pd.DataFrame(sentiments)
    result_df = pd.concat([result_df.reset_index(drop=True), sentiment_df.reset_index(drop=True)], axis=1)
    result_df.to_csv(NLP_RESULT_PATH, index=False, encoding="utf-8-sig")
    return result_df


def _plot_sentiment_distribution(df: pd.DataFrame) -> None:
    if "sentiment_label" not in df.columns:
        return

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    label_counts = df["sentiment_label"].value_counts()
    label_map = {"positive": "正面评论", "neutral": "中性评论", "negative": "负面评论"}
    colors_map = {"positive": "#2ca02c", "negative": "#d62728", "neutral": "#7f7f7f"}
    colors = [colors_map.get(label, "#7f7f7f") for label in label_counts.index]
    labels = [f"{label_map.get(label, label)}\n{count}条" for label, count in label_counts.items()]
    wedges, _, _ = axes[0].pie(
        label_counts.values,
        labels=labels,
        autopct="%.1f%%",
        colors=colors,
        startangle=90,
        textprops={"fontsize": 11},
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    axes[0].set_title("评论情感类型占比\n颜色区分正面/中性/负面评论", fontsize=14, fontweight="bold")
    axes[0].legend(
        wedges,
        [label_map.get(label, label) for label in label_counts.index],
        title="情感类型",
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
    )

    axes[1].hist(df["sentiment_score"].dropna(), bins=40, color="#5b9bd5", edgecolor="white", alpha=0.85)
    axes[1].axvline(x=0, color="#d62728", linestyle="--", linewidth=1.5, label="中性线")
    axes[1].set_title("情感分数分布\n高于0偏正面，低于0偏负面", fontsize=14, fontweight="bold")
    axes[1].set_xlabel("情感分数（-1 到 1）")
    axes[1].set_ylabel("评论数量")
    axes[1].legend()
    axes[1].grid(axis="y", alpha=0.25)

    plt.tight_layout()
    plt.savefig(DEEP_MINING_DIR / "nlp_sentiment_distribution.png", dpi=220, bbox_inches="tight")
    plt.close()


def _plot_wordcloud(words: list[str], tag: str, title: str) -> None:
    if not words:
        return

    word_freq = Counter(words)
    if not word_freq:
        return

    try:
        font_path = None
        import os
        candidate_fonts = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/System/Library/Fonts/PingFang.ttc",
        ]
        for fp in candidate_fonts:
            if os.path.exists(fp):
                font_path = fp
                break

        wc = WordCloud(
            width=800,
            height=500,
            background_color="white",
            font_path=font_path,
            max_words=100,
            max_font_size=120,
            min_font_size=12,
            collocations=False,
            random_state=42,
        )
        wc.generate_from_frequencies(word_freq)

        plt.figure(figsize=(12, 7))
        plt.imshow(wc, interpolation="bilinear")
        plt.title(title, fontsize=16)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(DEEP_MINING_DIR / f"wordcloud_{tag}.png", dpi=220, bbox_inches="tight")
        plt.close()
    except Exception as exc:
        logger.warning("词云生成失败: %s", exc)


def _plot_sentiment_by_churn(df: pd.DataFrame) -> None:
    if "churn_label" not in df.columns or "sentiment_score" not in df.columns:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    churn_sentiment = df.groupby("churn_label")["sentiment_score"].mean()
    axes[0].bar(
        ["留存客户", "流失客户"],
        [churn_sentiment.get(0, 0), churn_sentiment.get(1, 0)],
        color=["#2ca02c", "#d62728"],
        edgecolor="white",
    )
    axes[0].set_title("不同客户群体的平均情感分数")
    axes[0].set_ylabel("平均情感分数")
    axes[0].axhline(y=0, color="gray", linestyle="--", linewidth=0.8)

    sentiment_crosstab = pd.crosstab(df["churn_label"], df["sentiment_label"], normalize="index")
    sentiment_crosstab.index = ["留存客户", "流失客户"]
    sentiment_crosstab.plot(kind="bar", stacked=True, ax=axes[1], color=["#2ca02c", "#d62728", "#7f7f7f"])
    axes[1].set_title("不同客户群体的情感倾向分布")
    axes[1].set_ylabel("占比")
    axes[1].legend(title="情感倾向")
    axes[1].tick_params(axis="x", rotation=0)

    plt.tight_layout()
    plt.savefig(DEEP_MINING_DIR / "nlp_sentiment_by_churn.png", dpi=220, bbox_inches="tight")
    plt.close()


def _plot_top_keywords(
    all_words: list[str],
    churn_words: list[str],
    retain_words: list[str],
    top_n: int = 15,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    for ax, words, title, color in [
        (axes[0], all_words, "全量高频词", "#5b9bd5"),
        (axes[1], churn_words, "流失客户高频词", "#d62728"),
        (axes[2], retain_words, "留存客户高频词", "#2ca02c"),
    ]:
        if not words:
            continue
        counter = Counter(words)
        top_items = counter.most_common(top_n)
        if not top_items:
            continue
        labels, values = zip(*top_items)
        ax.barh(range(len(labels)), values, color=color, edgecolor="white", alpha=0.85)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.set_title(title)
        ax.set_xlabel("词频")

    plt.tight_layout()
    plt.savefig(DEEP_MINING_DIR / "nlp_top_keywords.png", dpi=220, bbox_inches="tight")
    plt.close()


def get_nlp_summary(df: pd.DataFrame) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total_analyzed": len(df),
        "sentiment_distribution": {},
        "avg_sentiment_score": 0.0,
        "churn_sentiment_gap": 0.0,
    }

    if "sentiment_label" in df.columns:
        dist = df["sentiment_label"].value_counts(normalize=True)
        summary["sentiment_distribution"] = {
            "positive": round(dist.get("positive", 0), 4),
            "neutral": round(dist.get("neutral", 0), 4),
            "negative": round(dist.get("negative", 0), 4),
        }

    if "sentiment_score" in df.columns:
        summary["avg_sentiment_score"] = round(df["sentiment_score"].mean(), 4)

    if "churn_label" in df.columns and "sentiment_score" in df.columns:
        churn_avg = df[df["churn_label"] == 1]["sentiment_score"].mean()
        retain_avg = df[df["churn_label"] == 0]["sentiment_score"].mean()
        summary["churn_sentiment_gap"] = round(retain_avg - churn_avg, 4)

    return summary
