# 企业客户流失预警与挽留分析系统

本项目面向课程《大数据分析与应用》，基于**实时爬取的公开真实用户数据**，通过**深度挖掘技术**完成客户流失预警、影响因素分析与挽留建议输出。

## 项目目标

1. 使用 `requests` + `BeautifulSoup` 实时爬取公开真实用户评论数据
2. 使用 `jieba` + 情感词典完成 NLP 文本情感分析与词云可视化
3. 使用 `scikit-learn` 完成 K-Means 客户聚类分群
4. 使用 `XGBoost` + `LightGBM` + `scikit-learn` 构建 6 个分类模型并 GridSearchCV 超参优化
5. 使用 `SHAP` 或模型特征重要性完成可解释性分析
6. 使用交叉验证 + 学习曲线评估模型稳定性
7. 输出可直接用于课程报告的结果文件、图表和结论草稿

## 项目结构

```text
customer-churn-analysis/
├── data/
│   ├── raw/                    # 原始爬取数据
│   └── processed/              # 清洗后数据
├── notebooks/
├── outputs/
│   ├── plots/                  # 基础可视化图表
│   ├── deep_mining/            # 深度挖掘图表（聚类/SHAP/NLP/学习曲线）
│   ├── best_model.joblib       # 最佳模型
│   ├── stacking_model.joblib   # Stacking 集成模型
│   ├── model_metrics.csv       # 模型评估指标
│   ├── feature_importance.csv  # 特征重要性
│   ├── cluster_analysis.csv    # 聚类结果
│   └── nlp_sentiment.csv       # NLP 情感分析结果
├── reports/
├── src/
│   └── churn_system/
│       ├── scraper.py          # 实时爬虫模块
│       ├── preprocess.py       # 数据预处理
│       ├── nlp_analysis.py     # NLP 文本挖掘
│       ├── visualization.py    # 数据可视化
│       ├── deep_mining.py      # 深度挖掘（聚类/SHAP/交叉验证）
│       ├── modeling.py         # 多模型训练与评估
│       ├── pipeline.py         # 完整流程编排
│       └── config.py           # 配置管理
├── run_project.py              # 一键运行入口
├── streamlit_app.py            # 交互式 Web 演示
└── requirements.txt
```

## 功能模块

| 阶段 | 模块 | 说明 |
|------|------|------|
| 1 | 实时数据爬取 | Steam 公开 API 爬取用户评论、时长、评分等真实数据 |
| 2 | 数据预处理 | 缺失值填充、特征衍生、One-Hot编码 |
| 3 | NLP文本挖掘 | 情感词典评分 + jieba分词 + 词云 + 关键词分析 |
| 4 | 数据可视化 | 流失分布、行为特征、情感趋势等 5 张图表 |
| 5 | 客户聚类分群 | K-Means + PCA + 肘部法则 + 轮廓系数 |
| 6 | 多模型训练 | 6模型 + GridSearchCV + Stacking集成 |
| 7 | 模型评估 | SHAP/特征重要性可解释性 + 5折交叉验证 + 学习曲线 + 混淆矩阵 |

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行完整分析流程（首次运行会自动爬取数据）
python run_project.py

# 启动交互式演示页面
streamlit run streamlit_app.py
```

## 运行结果

执行 `python run_project.py` 后会自动：

1. 从 Steam 公开 API 实时爬取用户评论数据 → `data/raw/scraped_reviews.csv`
2. 数据清洗与特征工程 → `data/processed/customer_churn_cleaned.csv`
3. NLP 情感分析 → `outputs/nlp_sentiment.csv` + 词云/情感图表
4. 基础可视化 → `outputs/plots/` 5 张图表
5. 客户聚类分群 → `outputs/cluster_analysis.csv` + 聚类可视化
6. 6 模型训练 + GridSearchCV + Stacking → `outputs/model_metrics.csv`
7. 模型解释性分析 → `outputs/shap_summary.png`（优先使用 SHAP，未安装时自动生成特征重要性替代图）
8. 交叉验证 + 学习曲线 + 混淆矩阵 → `outputs/deep_mining/`

## Streamlit 演示页面

7 个交互式 Tab 页：

1. **业务概览** - 流失特征多维度分析 + 侧边栏筛选
2. **NLP情感挖掘** - 情感分布 + 词云 + 关键词对比
3. **客户聚类分群** - PCA可视化 + 各分群画像
4. **模型评估对比** - 6模型指标对比 + 特征重要性 + 模型解释性分析
5. **模型稳定性** - 学习曲线 + 混淆矩阵
6. **输出图表** - 所有生成图表的画廊
7. **单客预测** - 输入用户画像 → 流失概率 + 风险等级 + 挽留建议

## 推荐答辩亮点

1. 实时爬取真实数据，而非使用静态数据集
2. 6 个模型对比 + GridSearchCV 超参优化 + Stacking 集成
3. NLP 文本情感分析挖掘用户真实反馈
4. K-Means 聚类实现客户分群与差异化策略
5. SHAP/特征重要性模型解释性分析，让"黑盒"模型透明化
6. 交叉验证 + 学习曲线全面评估模型泛化能力
7. Streamlit 交互式看板模拟企业实际应用场景

## 数据说明

本项目默认从 Steam 公开评论 API 实时爬取数据。爬虫具备：
- 随机 User-Agent 轮换
- 请求间隔限速（1.5~3秒）
- 自动重试机制（最多3次）
- 本地缓存（避免重复爬取）
- 备用数据生成（网络不可用时自动切换）

主要字段包括：
- `playtime_hours`：游戏时长
- `review_text`：评论内容
- `voted_up`：是否好评
- `votes_up`：获赞数
- `engagement_score`：参与度分数
- `churn_signal`：流失信号分
- `churn_label`：流失标签（目标变量）
