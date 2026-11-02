from pathlib import Path
from shutil import copyfile


ROOT = Path.cwd()
OUT = ROOT / "reports" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

files = {
    "02_churn_distribution.png": ROOT / "outputs" / "plots" / "01_churn_distribution.png",
    "03_playtime_churn_rate.png": ROOT / "outputs" / "plots" / "02_contract_churn_rate.png",
    "04_product_churn_rate.png": ROOT / "outputs" / "plots" / "03_region_churn_rate.png",
    "05_engagement_scatter.png": ROOT / "outputs" / "plots" / "04_fee_vs_activity.png",
    "06_nlp_sentiment_distribution.png": ROOT / "outputs" / "deep_mining" / "nlp_sentiment_distribution.png",
    "07_cluster_analysis.png": ROOT / "outputs" / "deep_mining" / "cluster_analysis.png",
    "08_confusion_matrix.png": ROOT / "outputs" / "deep_mining" / "confusion_matrix.png",
    "09_learning_curve.png": ROOT / "outputs" / "deep_mining" / "learning_curve.png",
    "10_feature_importance_or_shap.png": ROOT / "outputs" / "shap_summary.png",
    "11_standard_flow_group_churn_rate.png": ROOT / "outputs" / "standard_flow" / "group_churn_rate.png",
    "12_standard_flow_time_series.png": ROOT / "outputs" / "standard_flow" / "time_series_churn_trend.png",
}

for name, src in files.items():
    if src.exists():
        dst = OUT / name
        copyfile(src, dst)
        print(dst)
    else:
        print(f"missing: {src}")
