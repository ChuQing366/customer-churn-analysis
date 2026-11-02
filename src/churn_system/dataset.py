import pandas as pd
from sklearn.datasets import fetch_openml

from .config import RAW_DATA_PATH


def ensure_dataset_exists(rows: int = 800) -> pd.DataFrame:
    if RAW_DATA_PATH.exists():
        existing = pd.read_csv(RAW_DATA_PATH)
        if "Churn" in existing.columns:
            return existing

    dataset = download_telco_customer_churn()
    dataset.to_csv(RAW_DATA_PATH, index=False)
    return dataset


def download_telco_customer_churn() -> pd.DataFrame:
    data = fetch_openml(name="Telco-Customer-Churn", version=1, as_frame=True)
    df = data.frame.copy()
    for column in df.select_dtypes(include="object").columns:
        df[column] = df[column].astype(str).str.replace("'", "", regex=False).str.strip()
    return df
