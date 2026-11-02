# 标准数据分析流程对照报告

## 结论

当前项目原本已经完成数据获取、预处理、可视化、聚类、分类建模、模型评价、解释性分析和 Streamlit 展示。对照课堂图示后，已补齐独立产物较弱的对比分析、分组分析、交叉分析、回归分析、时间序列分析、关联规则分析和流程对照说明。

## 数据来源

- 数据来源：Steam 公开评论 API / 备用模拟数据
- 样本数量：2000
- 时间范围：2023-12-31 17:43:00 ~ 2025-05-15 13:30:00

## 流程对照

| 流程环节 | 状态 | 证据文件 | 说明 |
|---|---|---|---|
| 需求分析 | 已补齐 | `reports/standard_flow_compliance.md` | 把业务/客服/运营/产品等部门需求映射为流失预警、原因解释和挽留策略。 |
| 数据获取 | 已完成 | `data/raw/scraped_reviews.csv` | 数据来源：Steam 公开评论 API / 备用模拟数据。 |
| 数据预处理-数据合并 | 已完成 | `src/churn_system/scraper.py` | 爬取数据、本地缓存数据和备用数据统一进入同一张原始表。 |
| 数据预处理-缺失清洗 | 已完成 | `E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\data_quality_report.csv` | 输出字段缺失率，并在 clean_dataset 中完成缺失填充和异常值裁剪。 |
| 数据预处理-数据标准化 | 已完成 | `src/churn_system/deep_mining.py` | 聚类和回归分析使用 StandardScaler，分类模型中的逻辑回归也使用标准化管道。 |
| 数据预处理-数据变换 | 已完成 | `src/churn_system/preprocess.py` | 生成 playtime_hours、engagement_score、churn_signal、churn_label 等衍生变量。 |
| 分析与挖掘-对比分析 | 已补齐 | `E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\comparison_analysis.csv` | 比较流失与留存客户在数值特征上的均值差异。 |
| 分析与挖掘-分组分析 | 已补齐 | `E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\group_analysis.csv` | 按时长层级、产品、情感类型等维度统计流失率。 |
| 分析与挖掘-交叉分析 | 已补齐 | `E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\cross_analysis.csv` | 生成分类维度与流失标签的交叉占比。 |
| 分析与挖掘-回归分析 | 已补齐 | `E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\regression_analysis.csv` | 用线性回归解释 churn_signal 的主要影响方向。 |
| 分析与挖掘-时间序列 | 已补齐 | `E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\time_series_analysis.csv` | 按 review_month 统计样本量、流失率、情感分和活跃度趋势。 |
| 分析与挖掘-关联规则 | 已补齐 | `E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\association_rules.csv` | 计算特征取值到流失结果的 support、confidence 和 lift。 |
| 模型评价与优化-聚类模型评价 | 已完成 | `outputs/deep_mining/cluster_analysis.png` | K-Means 使用轮廓系数、DBI、CH 指数和肘部法则评估。 |
| 模型评价与优化-分类模型评价 | 已完成 | `outputs/model_metrics.csv` | 比较 Accuracy、Precision、Recall、F1、AUC，并做 GridSearchCV 和 Stacking。 |
| 模型评价与优化-回归模型评价 | 已补齐 | `E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\regression_analysis.csv` | 输出回归 R2 和标准化系数，作为影响因素解释补充。 |
| 部署 | 已完成 | `streamlit_app.py` | 使用 Streamlit 展示业务看板、模型结果、客户预测和挽留建议。 |

## 新增补充产物

- 数据质量报告：`E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\data_quality_report.csv`
- 对比分析：`E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\comparison_analysis.csv`
- 分组分析：`E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\group_analysis.csv`
- 交叉分析：`E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\cross_analysis.csv`
- 回归分析：`E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\regression_analysis.csv`
- 时间序列分析：`E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\time_series_analysis.csv`
- 关联规则分析：`E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\association_rules.csv`
- 模型评价汇总：`E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis\outputs\standard_flow\model_evaluation_summary.csv`

## 说明

图中示例包含业务系统、财务系统、生产系统。本项目是客户流失预警方向，因此部署环节对应为 Streamlit 业务分析系统，面向运营、客服、产品和管理人员使用；财务/生产系统不作为本项目的真实业务边界。