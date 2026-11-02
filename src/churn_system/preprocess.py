from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


NUMERIC_COLUMNS = [
    "author_playtime_forever",
    "author_playtime_at_review",
    "author_num_games_owned",
    "author_num_reviews",
    "votes_up",
    "votes_funny",
    "weighted_vote_score",
    "comment_count",
    "review_length",
    "review_word_count",
    "playtime_hours",
    "playtime_at_review_hours",
    "engagement_score",
    "churn_signal",
]

CATEGORICAL_COLUMNS = [
    "app_id",
    "is_negative",
    "is_free_copy",
    "is_early_access",
    "playtime_tier",
    "review_month",
    "review_hour",
]

TARGET_COLUMN = "churn_label"

LABEL_LEAKAGE_COLUMNS = [
    "churn_signal",
    "author_playtime_forever",
    "playtime_hours",
    "review_length",
    "author_num_reviews",
    "votes_up",
    "comment_count",
    "engagement_score",
    "is_negative",
    "voted_up",
    "is_free_copy",
    "received_for_free",
    "is_early_access",
    "written_during_early_access",
]


def _numeric_series(df: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in df.columns:
        return pd.Series(default, index=df.index, dtype="float64")
    return pd.to_numeric(df[column], errors="coerce").fillna(default).astype(float)


def _stable_noise(df: pd.DataFrame) -> pd.Series:
    if "recommendation_id" in df.columns:
        key = df["recommendation_id"].fillna("").astype(str)
    else:
        key = pd.Series(df.index.astype(str), index=df.index)

    hashed = pd.util.hash_pandas_object(key, index=False).astype("uint64")
    return (hashed % 10000).astype(float) / 10000.0


def _sigmoid(value: pd.Series) -> pd.Series:
    return 1 / (1 + np.exp(-value.clip(-20, 20)))


def _rebuild_churn_signal_and_label(cleaned: pd.DataFrame) -> pd.DataFrame:
    playtime_hours = _numeric_series(cleaned, "playtime_hours")
    review_length = _numeric_series(cleaned, "review_length")
    votes_up = _numeric_series(cleaned, "votes_up")
    comment_count = _numeric_series(cleaned, "comment_count")
    num_reviews = _numeric_series(cleaned, "author_num_reviews")
    is_negative = _numeric_series(cleaned, "is_negative")
    is_free_copy = _numeric_series(cleaned, "is_free_copy")
    is_early_access = _numeric_series(cleaned, "is_early_access")

    playtime_scale = np.log1p(playtime_hours) / max(float(np.log1p(playtime_hours.max())), 1.0)
    social_feedback = np.log1p(votes_up + comment_count) / max(float(np.log1p((votes_up + comment_count).max())), 1.0)

    risk_logit = (
        -0.55
        + is_negative * 1.15
        + (playtime_hours < 2).astype(float) * 0.75
        + (playtime_hours.between(2, 10, inclusive="left")).astype(float) * 0.35
        + (review_length < 40).astype(float) * 0.35
        + (num_reviews <= 1).astype(float) * 0.2
        + is_free_copy * 0.2
        + is_early_access * 0.15
        - playtime_scale * 0.45
        - social_feedback * 0.25
    )

    cleaned["churn_signal"] = _sigmoid(risk_logit).round(4)
    cleaned[TARGET_COLUMN] = (cleaned["churn_signal"] > _stable_noise(cleaned)).astype(int)
    return cleaned


def sanitize_feature_columns(features: pd.DataFrame) -> pd.DataFrame:
    """Make model feature names compatible with XGBoost/LightGBM."""
    sanitized_columns: list[str] = []
    seen: dict[str, int] = {}

    for column in features.columns:
        safe_name = str(column)
        for old, new in {
            "[": "_",
            "]": "_",
            "<": "lt",
            ">": "gt",
            "(": "_",
            ")": "_",
            ",": "_",
            ":": "_",
            " ": "_",
        }.items():
            safe_name = safe_name.replace(old, new)

        while "__" in safe_name:
            safe_name = safe_name.replace("__", "_")
        safe_name = safe_name.strip("_") or "feature"

        if safe_name in seen:
            seen[safe_name] += 1
            safe_name = f"{safe_name}_{seen[safe_name]}"
        else:
            seen[safe_name] = 0

        sanitized_columns.append(safe_name)

    result = features.copy()
    result.columns = sanitized_columns
    return result


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()

    for col in NUMERIC_COLUMNS:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")
            cleaned[col] = cleaned[col].fillna(0)
            cleaned[col] = cleaned[col].clip(lower=0)

    if "review_text" in cleaned.columns:
        cleaned["review_length"] = cleaned["review_text"].fillna("").apply(len)
        cleaned["review_word_count"] = cleaned["review_text"].fillna("").apply(lambda t: len(t.split()))

    if "author_playtime_forever" in cleaned.columns:
        cleaned["playtime_hours"] = cleaned["author_playtime_forever"] / 60.0

    if "author_playtime_at_review" in cleaned.columns:
        cleaned["playtime_at_review_hours"] = cleaned["author_playtime_at_review"] / 60.0

    if "voted_up" in cleaned.columns:
        cleaned["is_negative"] = (~cleaned["voted_up"].astype(bool)).astype(int)

    if "received_for_free" in cleaned.columns:
        cleaned["is_free_copy"] = _numeric_series(cleaned, "received_for_free").astype(int)

    if "written_during_early_access" in cleaned.columns:
        cleaned["is_early_access"] = _numeric_series(cleaned, "written_during_early_access").astype(int)

    if "engagement_score" not in cleaned.columns:
        cleaned["engagement_score"] = (
            _numeric_series(cleaned, "votes_up") * 0.4
            + _numeric_series(cleaned, "comment_count") * 0.3
            + _numeric_series(cleaned, "weighted_vote_score") * 0.2
            + (_numeric_series(cleaned, "review_length") / 500).clip(0, 1) * 0.1
        )

    cleaned = _rebuild_churn_signal_and_label(cleaned)

    for col in CATEGORICAL_COLUMNS:
        if col in cleaned.columns:
            if isinstance(cleaned[col].dtype, pd.CategoricalDtype):
                cleaned[col] = cleaned[col].cat.add_categories("unknown")
            cleaned[col] = cleaned[col].fillna("unknown").astype(str)

    available_numeric = [c for c in NUMERIC_COLUMNS if c in cleaned.columns]
    if available_numeric:
        cleaned[available_numeric] = cleaned[available_numeric].clip(lower=0)

    return cleaned


def build_model_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    exclude_cols = [
        TARGET_COLUMN,
        *LABEL_LEAKAGE_COLUMNS,
        "review_text",
        "recommendation_id",
        "author_steamid",
        "review_date",
        "timestamp_created",
        "timestamp_updated",
        "language",
        "app_name",
        "hidden_in_steam_china",
        "steam_purchase",
    ]

    feature_frame = df.drop(columns=[c for c in exclude_cols if c in df.columns], errors="ignore")

    available_categorical = [c for c in CATEGORICAL_COLUMNS if c in feature_frame.columns]
    if available_categorical:
        feature_frame = pd.get_dummies(feature_frame, columns=available_categorical, drop_first=False)

    feature_frame = sanitize_feature_columns(feature_frame)
    target = df[TARGET_COLUMN]
    return feature_frame, target


def split_dataset(features: pd.DataFrame, target: pd.Series):
    return train_test_split(features, target, test_size=0.25, random_state=42, stratify=target)
