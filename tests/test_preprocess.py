import unittest

import pandas as pd

from src.churn_system.preprocess import (
    LABEL_LEAKAGE_COLUMNS,
    build_model_features,
    clean_dataset,
    split_dataset,
)


class PreprocessTests(unittest.TestCase):
    def _sample_reviews(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "app_id": [570, 730, 570, 578080, 292030, 570, 730, 578080],
                "app_name": ["Dota 2", "CS2", "Dota 2", "PUBG", "The Witcher 3", "Dota 2", "CS2", "PUBG"],
                "recommendation_id": [f"rec_{i}" for i in range(8)],
                "author_steamid": [f"user_{i}" for i in range(8)],
                "author_playtime_forever": [120, -5, 2400, 60, 480, 900, 30, 1500],
                "author_playtime_at_review": [60, 0, 1200, 30, 300, 400, 10, 700],
                "author_num_games_owned": [5, 10, None, 3, 8, 2, 7, 11],
                "author_num_reviews": [1, 2, 4, 1, 3, 1, 5, 2],
                "language": ["schinese"] * 8,
                "review_text": [
                    "优化很好，体验不错",
                    "卡顿严重，服务器差",
                    "玩了很久，整体推荐",
                    "匹配不平衡，想退坑",
                    "剧情优秀，值得购买",
                    "",
                    "外挂太多，不推荐",
                    "朋友一起玩很开心",
                ],
                "voted_up": [True, False, True, False, True, False, False, True],
                "votes_up": [10, None, 5, 0, 8, 1, 2, 6],
                "votes_funny": [0, 1, 0, 0, 2, 0, 3, 0],
                "weighted_vote_score": [0.5, 0.1, 0.3, 0.0, 0.8, 0.2, 0.4, 0.6],
                "comment_count": [2, 0, 1, 0, 3, 0, 1, 2],
                "received_for_free": [False, True, False, False, False, True, False, False],
                "written_during_early_access": [False, False, False, True, False, False, True, False],
                "review_month": ["2026-01", "2026-01", "2026-02", "2026-02", "2026-03", "2026-03", "2026-04", "2026-04"],
                "review_hour": [8, 12, 15, 20, 9, 11, 22, 14],
            }
        )

    def test_clean_dataset_normalizes_fields_and_builds_target(self):
        cleaned = clean_dataset(self._sample_reviews())

        self.assertEqual(len(cleaned), 8)
        self.assertIn("review_length", cleaned.columns)
        self.assertIn("playtime_hours", cleaned.columns)
        self.assertIn("is_negative", cleaned.columns)
        self.assertIn("churn_signal", cleaned.columns)
        self.assertIn("churn_label", cleaned.columns)
        self.assertGreaterEqual(cleaned["author_playtime_forever"].min(), 0)
        self.assertFalse(cleaned["votes_up"].isna().any())
        self.assertTrue(set(cleaned["churn_label"].unique()).issubset({0, 1}))

    def test_build_model_features_excludes_raw_identifiers_and_target(self):
        cleaned = clean_dataset(self._sample_reviews())
        features, target = build_model_features(cleaned)

        self.assertEqual(len(features), len(cleaned))
        self.assertEqual(len(target), len(cleaned))
        self.assertNotIn("churn_label", features.columns)
        self.assertNotIn("review_text", features.columns)
        self.assertNotIn("recommendation_id", features.columns)
        self.assertFalse(any("[" in col or "]" in col or " " in col for col in features.columns))
        self.assertTrue(all(pd.api.types.is_numeric_dtype(features[col]) for col in features.columns))

    def test_build_model_features_excludes_label_leakage_columns(self):
        cleaned = clean_dataset(self._sample_reviews())
        features, _ = build_model_features(cleaned)

        for leakage_column in LABEL_LEAKAGE_COLUMNS:
            self.assertNotIn(leakage_column, features.columns)
            self.assertFalse(
                any(column.startswith(f"{leakage_column}_") for column in features.columns),
                msg=f"{leakage_column} leaked through encoded features",
            )

    def test_split_dataset_preserves_sample_count(self):
        cleaned = clean_dataset(self._sample_reviews())
        features, target = build_model_features(cleaned)
        target = pd.Series([0, 1, 0, 1, 0, 1, 0, 1], name=target.name)

        x_train, x_test, y_train, y_test = split_dataset(features, target)

        self.assertEqual(len(x_train) + len(x_test), len(features))
        self.assertEqual(len(y_train) + len(y_test), len(target))
        self.assertEqual(list(x_train.columns), list(x_test.columns))


if __name__ == "__main__":
    unittest.main()
