import os

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

from src.churn_system.pipeline import run_pipeline


if __name__ == "__main__":
    run_pipeline(force_scrape=False, enable_grid_search=True)
