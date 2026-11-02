from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "customer_churn_dataset.csv"
SCRAPED_DATA_PATH = DATA_DIR / "raw" / "scraped_reviews.csv"
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "customer_churn_cleaned.csv"
OUTPUTS_DIR = BASE_DIR / "outputs"
PLOTS_DIR = OUTPUTS_DIR / "plots"
DEEP_MINING_DIR = OUTPUTS_DIR / "deep_mining"
STANDARD_FLOW_DIR = OUTPUTS_DIR / "standard_flow"
METRICS_PATH = OUTPUTS_DIR / "model_metrics.csv"
IMPORTANCE_PATH = OUTPUTS_DIR / "feature_importance.csv"
SHAP_PATH = OUTPUTS_DIR / "shap_summary.png"
CLUSTER_PATH = OUTPUTS_DIR / "cluster_analysis.csv"
NLP_RESULT_PATH = OUTPUTS_DIR / "nlp_sentiment.csv"
MODEL_PATH = OUTPUTS_DIR / "best_model.joblib"
STACKING_MODEL_PATH = OUTPUTS_DIR / "stacking_model.joblib"


for directory in [DATA_DIR / "raw", DATA_DIR / "processed", OUTPUTS_DIR, PLOTS_DIR, DEEP_MINING_DIR, STANDARD_FLOW_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
