from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


TEMPLATE = Path(r"C:\Users\Liu Jiawang\Desktop\第二学期-作业\数分\《大数据分析与应用》综合项目模板.docx")
OUT = Path.cwd() / "reports" / "第五组-企业客户流失与预警分析系统-保留模板结构版.docx"
SCREEN = Path.cwd() / "reports" / "screenshots"
FRAMEWORK = Path.cwd() / "outputs" / "standard_flow" / "system_framework_diagram.png"

SONGTI = "\u5b8b\u4f53"
TIMES = "Times New Roman"


def rfont(run, name=SONGTI, size=12, bold=None):
    run.font.name = name
    if run._element.rPr is None:
        run._element.get_or_add_rPr()
    if run._element.rPr.rFonts is None:
        run._element.rPr.get_or_add_rFonts()
    for attr in ["w:eastAsia", "w:ascii", "w:hAnsi", "w:cs"]:
        run._element.rPr.rFonts.set(qn(attr), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def set_paragraph_text(paragraph, text, font=SONGTI, size=12, bold=None):
    paragraph.text = ""
    run = paragraph.add_run(text)
    rfont(run, font, size, bold)
    paragraph.paragraph_format.line_spacing = 1.5
    return paragraph


def add_after(paragraph, text="", font=SONGTI, size=12):
    new_p = paragraph._parent.add_paragraph()
    paragraph._p.addnext(new_p._p)
    set_paragraph_text(new_p, text, font, size)
    return new_p


def clear_paragraph(paragraph):
    paragraph.text = ""
    return paragraph


def add_image_after(paragraph, image_path: Path, caption: str, width=5.6):
    if not image_path.exists():
        return paragraph
    p = add_after(paragraph, "")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(image_path), width=Inches(width))
    cap = add_after(p, caption, size=10.5)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return cap


def fill_cell(cell, text, font=SONGTI, size=10.5, bold=None):
    cell.text = ""
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    p = cell.paragraphs[0]
    p.paragraph_format.line_spacing = 1.5
    run = p.add_run(text)
    rfont(run, font, size, bold)


def fill_code_cell(cell, code):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.line_spacing = 1.5
    lines = code.strip().splitlines()
    for i, line in enumerate(lines):
        if i:
            p.add_run("\n")
        run = p.add_run(line)
        rfont(run, TIMES, 12)


def replace_exact(paragraphs, old, new):
    for p in paragraphs:
        if p.text.strip() == old:
            set_paragraph_text(p, new)
            return p
    raise ValueError(old)


def find_exact(paragraphs, text):
    for p in paragraphs:
        if p.text.strip() == text:
            return p
    raise ValueError(text)


def build():
    doc = Document(TEMPLATE)
    ps = doc.paragraphs

    # Cover page: replace text only, preserve original template positions.
    replacements = {
        "项目名称：            XXXX大数据分析和挖掘系统": "项目名称：         企业客户流失预警与挽留分析系统",
        "专业班级：                 计科（升本）2501": "专业班级：             计科（专升本）2502",
        "学生姓名：           张三（学号）、李四（学号）": "学生姓名：   刘佳旺（20252S1037）、辛天乐（20252S1132）、孟航天（20252S1082）",
        "—XXX大数据分析和挖掘系统": "—企业客户流失预警与挽留分析系统",
    }
    for old, new in replacements.items():
        replace_exact(ps, old, new)

    # Part 1.
    replace_exact(ps, "（1）通过Numpy、Pandas等第三方模块对数据集进行读取和数据清洗；", "（1）通过 pandas、numpy 对 Steam 公开评论数据进行读取、清洗、缺失值处理、字段类型转换和特征衍生，形成可用于挖掘建模的结构化客户行为数据；")
    replace_exact(ps, "（2）通过matplotlib/seaborn对清洗后的数据进行可视化分析，探索隐藏在大量数据背后的业务规律；", "（2）通过 matplotlib、seaborn 对客户流失分布、使用时长、产品差异、参与度、评论情感等指标进行可视化分析，探索客户流失背后的业务规律；")
    replace_exact(ps, "（3）根据业务需求识别项目模型类型（分类、聚类、回归），找出模型所需的特征属性。通过skleran进行模型建立、模型训练、模型预测、模型评价。", "（3）围绕客户流失预警目标，构建二分类预测模型，并结合 K-Means 聚类完成客户分群；通过 scikit-learn、XGBoost、LightGBM 完成模型训练、预测、评价和可解释性分析。")
    replace_exact(ps, "（1）项目中需要包含数据读取、数据预处理、数据可视化、业务建模等功能；", "（1）项目中包含实时数据采集、数据读取、数据预处理、NLP 文本挖掘、数据可视化、客户聚类、多模型训练、模型评价和单客流失预测等功能；")
    replace_exact(ps, "（2）使用工具：pycharm或美林数据TempoAI", "（2）使用工具：PyCharm、Python 脚本调试环境、Streamlit 交互式展示页面。")
    replace_exact(ps, "使用技术：numpy、pandas、matplotlib、seaborn、skleran", "使用技术：numpy、pandas、matplotlib、seaborn、scikit-learn、XGBoost、LightGBM、jieba、wordcloud、SHAP、Streamlit。")

    # Team table.
    team_rows = [
        ["企业客户流失预警与挽留分析系统", "刘佳旺", "负责项目总体规划、技术路线设计和进度协调。"],
        ["企业客户流失预警与挽留分析系统", "刘佳旺", "完成数据预处理、特征工程、模型训练与评估等核心算法模块。"],
        ["企业客户流失预警与挽留分析系统", "刘佳旺", "负责 Streamlit 看板整合、项目调试和报告统稿。"],
        ["企业客户流失预警与挽留分析系统", "辛天乐", "负责数据采集模块和原始数据整理，协助完成字段梳理、数据质量检查、基础统计分析和部分可视化图表制作。"],
        ["企业客户流失预警与挽留分析系统", "孟航天", "负责 NLP 情感分析和客户分群结果整理，协助完成词云、关键词分析、聚类业务解释和测试截图整理。"],
    ]
    for row, values in zip(doc.tables[0].rows[1:], team_rows):
        for cell, value in zip(row.cells, values):
            fill_cell(cell, value)

    # Part 2.
    p = replace_exact(ps, "要求：介绍本系统的应用场景，使用本系统的客户群体，系统实现将达到的目标。", "本系统面向互联网产品运营、游戏社区运营和企业客户关系管理场景，重点解决“用户可能流失但企业难以及时发现”的问题。系统以 Steam 公开评论数据作为模拟业务数据源，采集用户评论、游戏时长、评分倾向、获赞数、评论时间等行为信息，通过数据挖掘方法提前识别高风险客户，并输出影响因素和挽留建议。系统使用对象包括运营人员、客户经理、数据分析人员和课程项目评审人员，目标是形成从数据采集、清洗、分析、建模到可视化展示的完整闭环。")
    p = replace_exact(ps, "要求：介绍本系统的框架结构（以系统框架结构图的方式展示），系统总体设计思路。", "系统采用“数据采集层—数据处理层—分析挖掘层—模型预测层—交互展示层”的分层设计思路。总体流程为：Steam 公开评论 API → 数据采集与缓存 → 数据清洗与特征工程 → NLP 情感分析和数据可视化 → K-Means 客户分群 → 多模型训练与评价 → SHAP/特征重要性解释 → Streamlit 交互看板与单客预测。")
    add_image_after(p, FRAMEWORK, "图1  系统框架结构图", width=6.0)
    replace_exact(ps, "要求：主要介绍本系统各模块的功能。", "系统主要包含七个模块：数据采集模块负责调用 Steam 公开评论 API 并提供缓存、重试和备用数据机制；数据预处理模块负责缺失值处理、异常值裁剪、字段类型转换和特征衍生；NLP 文本挖掘模块负责评论分词、情感评分、词云和关键词分析；数据可视化模块负责输出流失分布、使用时长、产品差异、参与度和情感趋势图；客户聚类模块负责基于 K-Means 和 PCA 完成客户分群；模型训练模块负责多模型训练、评价和解释；交互展示模块通过 Streamlit 提供业务概览、模型评估、输出图表和单客预测功能。")

    # Part 3.
    p_env = find_exact(ps, "1、系统开发环境")
    add_after(p_env, "操作系统：Windows；")
    add_after(p_env, "开发工具：PyCharm；")
    add_after(p_env, "编程语言：Python 3；")
    add_after(p_env, "核心依赖：pandas、numpy、scikit-learn、matplotlib、seaborn、xgboost、lightgbm、jieba、wordcloud、shap、streamlit、joblib；")
    add_after(p_env, "运行方式：命令行执行 python run_project.py 生成分析结果，执行 streamlit run streamlit_app.py 启动交互式看板。")

    replace_exact(ps, "要求：主要包括各模块的实现流程和实现代码（可包含处理流程图、部分重要的源代码等）。", "本系统按照“数据读取与探索—数据预处理—数据可视化—数据挖掘建模”的流程实现。以下各模块选取项目中的核心代码片段进行说明。")
    replace_exact(ps, "注意：以下各部分不能只粘贴代码，要对代码实现的具体功能有简单的描述。", "各模块代码均来自当前项目源码，报告中保留关键实现逻辑，并结合文字说明其功能作用。")
    replace_exact(ps, "功能要求：对数据集中包含的属性进行简要介绍；查看各属性的数据类型、描述信息、特征、统计。", "功能说明：数据探索阶段主要查看原始数据和清洗后数据的样本数量、字段类型、描述统计、缺失情况和目标变量分布。本项目清洗后数据包含 2000 条样本、35 个字段，整体流失率约为 49.30%。")
    clear_paragraph(find_exact(ps, "格式要求：请将代码粘贴在以下表格框中，小四号字，1.5倍行距，字体为Times New Roman，以下要求相同。"))
    fill_code_cell(doc.tables[1].cell(0, 0), """
import pandas as pd
from src.churn_system.config import SCRAPED_DATA_PATH, PROCESSED_DATA_PATH

raw_df = pd.read_csv(SCRAPED_DATA_PATH)
cleaned_df = pd.read_csv(PROCESSED_DATA_PATH)
print(raw_df.shape, cleaned_df.shape)
print(raw_df.dtypes)
print(cleaned_df.describe())
print(cleaned_df["churn_label"].value_counts(normalize=True))
""")

    replace_exact(ps, "功能要求：通过数据预处理的方法对数据进行清洗、处理缺失值、数据类型转换等。", "功能说明：数据预处理模块对数值字段进行类型转换、缺失值填充和异常值裁剪；从评论文本中生成评论长度和词数；根据游戏时长、互动反馈等信息构造分析字段，并在模型特征构建阶段排除标签泄露字段。")
    clear_paragraph(find_exact(ps, "格式要求：请将代码粘贴在以下表格框中，小四号字，1.5倍行距，字体为Times New Roman，以下要求相同。"))
    fill_code_cell(doc.tables[2].cell(0, 0), """
def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    for col in NUMERIC_COLUMNS:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")
            cleaned[col] = cleaned[col].fillna(0).clip(lower=0)
    cleaned["review_length"] = cleaned["review_text"].fillna("").apply(len)
    cleaned["playtime_hours"] = cleaned["author_playtime_forever"] / 60.0
    cleaned["is_negative"] = (~cleaned["voted_up"].astype(bool)).astype(int)
    cleaned = _rebuild_churn_signal_and_label(cleaned)
    return cleaned
""")

    replace_exact(ps, "功能要求：可通过散点图查看不同属性之间的关联关系；可通过柱状图查看不同分类类型的数量比较；可通过饼图查看不同分类类型的占比；可通过折线图查看变化的趋势等。", "功能说明：可视化模块生成客户流失总体分布饼图、不同使用时长层级流失率柱状图、不同产品流失率柱状图、使用时长与参与度散点图、评论情感分布图等，帮助从业务角度识别高风险客户群体。")
    clear_paragraph(find_exact(ps, "格式要求：请将代码粘贴在以下表格框中，小四号字，1.5倍行距，字体为Times New Roman，以下要求相同。"))
    fill_code_cell(doc.tables[3].cell(0, 0), """
def create_visualizations(df: pd.DataFrame, output_dir: Path) -> None:
    _plot_churn_distribution(df, output_dir)
    _plot_playtime_churn_rate(df, output_dir)
    _plot_app_churn_rate(df, output_dir)
    _plot_engagement_vs_churn(df, output_dir)
    _plot_sentiment_timeline(df, output_dir)
""")

    replace_exact(ps, "功能要求：根据业务目标选择合适的模型；识别模型所需的特征属性，对特征属性进行类型转换、标准化处理、PCA降维等。模型训练、模型预测、模型评估。", "功能说明：数据挖掘模块围绕客户流失预警进行二分类建模，同时使用 K-Means 完成客户分群。系统训练多个分类模型，通过 Accuracy、Precision、Recall、F1、ROC-AUC 等指标进行评价，并输出模型解释结果。")
    clear_paragraph(find_exact(ps, "格式要求：请将代码粘贴在以下表格框中，小四号字，1.5倍行距，字体为Times New Roman，以下要求相同。"))
    fill_code_cell(doc.tables[4].cell(0, 0), """
def train_and_evaluate_models(x_train, x_test, y_train, y_test, enable_grid_search=True):
    base_models = _build_base_models()
    param_grids = _build_param_grids()
    metrics, trained_models = [], {}
    for name, model in base_models.items():
        grid = GridSearchCV(model, param_grids[name], cv=2, scoring="f1")
        grid.fit(x_train, y_train)
        best_model = grid.best_estimator_
        pred = best_model.predict(x_test)
        prob = best_model.predict_proba(x_test)[:, 1]
        metrics.append({
            "model": name,
            "f1_score": f1_score(y_test, pred),
            "roc_auc": roc_auc_score(y_test, prob)
        })
        trained_models[name] = best_model
    return pd.DataFrame(metrics).sort_values(["f1_score", "roc_auc"], ascending=False)
""")

    # Part 4.
    p = replace_exact(ps, "总体要求：主要对各模块功能代码实现结果进行测试，并验证功能运行结果与期望结果是否一致。结果截图，依次粘贴，图要截的能看清，大小合适，不要过大过小，居中显示。", "本部分对各模块功能代码实现结果进行测试，并验证功能运行结果与预期是否一致。测试截图依次展示预处理结果、可视化结果、模型评价结果和交互式看板结果。")
    p = replace_exact(ps, "要求：主要测试预处理前后数据差异对比，以此来验证数据预处理功能是否正确。", "测试说明：通过对比原始数据和清洗后数据，验证数据预处理功能是否正确。系统能够稳定输出 2000 条清洗后样本，字段数量为 35，核心衍生字段包括 review_length、playtime_hours、engagement_score、churn_signal 和 churn_label。")
    p = add_image_after(p, SCREEN / "01_streamlit_business_overview.png", "图2  Streamlit 看板启动与数据概览截图", width=5.8)
    add_after(p, "测试结论：预处理模块能够完成字段规范化、缺失值处理、异常值裁剪和特征衍生，处理后的数据能够继续用于 NLP 分析、可视化分析、客户聚类和模型训练。")

    p = replace_exact(ps, "要求：输出数据分析和可视化结果（截图），并从业务的角度对可视化的结果进行结论性的描述。", "测试说明：输出数据分析和可视化结果，并从业务角度对结果进行结论性描述。")
    for img, cap, desc in [
        ("02_churn_distribution.png", "图3  客户流失总体分布图", "该图展示流失客户与留存客户占比。当前样本整体流失率约为 49.30%，说明数据中流失与留存样本较为接近，适合进行二分类建模。"),
        ("03_playtime_churn_rate.png", "图4  不同使用时长层级的客户流失率", "该图展示使用时长与流失之间的关系。使用时长较短、参与度较低的客户更容易出现流失风险。"),
        ("04_product_churn_rate.png", "图5  不同产品的客户流失率", "该图比较不同产品下客户流失率差异，可帮助运营人员定位流失率较高的产品。"),
        ("05_engagement_scatter.png", "图6  使用时长与参与度关系散点图", "该图展示用户使用时长、参与度和流失状态之间的关系，可用于识别低活跃高风险客户。"),
        ("06_nlp_sentiment_distribution.png", "图7  NLP 评论情感分布图", "该图展示评论情感倾向。当前中性评论占 44.60%，负面评论占 31.15%，正面评论占 24.25%。"),
    ]:
        p = add_image_after(p, SCREEN / img, cap, width=5.4)
        p = add_after(p, desc)

    p = replace_exact(ps, "要求：数据挖掘建立的模型是否合理，通过不同模型的评价指标进行评价和总结。可通过数据可视化的方式对模型的效果进行展示，并从业务的角度对可视化的结果进行结论性的描述。", "测试说明：通过不同模型的评价指标、聚类结果、混淆矩阵、学习曲线和模型解释图，对数据挖掘模型的合理性进行评价和总结。")
    metric_text = "模型评价结果：去除标签泄露后，DecisionTree 在测试集上 F1=0.6254，Recall=0.8618，ROC-AUC=0.5334；5 折交叉验证 F1=0.5045±0.0716，AUC=0.5260±0.0376。该结果说明模型具备基础预警能力，但公开评论数据的预测信号有限。"
    p = add_after(p, metric_text)
    for img, cap, desc in [
        ("07_cluster_analysis.png", "图8  K-Means 客户聚类结果", "聚类结果将客户分为不同群体，可用于识别高活跃客户、低活跃客户和潜在流失客户。"),
        ("08_confusion_matrix.png", "图9  混淆矩阵", "混淆矩阵用于观察模型对流失客户和留存客户的识别情况，流失预警场景中 Recall 具有重要意义。"),
        ("09_learning_curve.png", "图10  学习曲线", "学习曲线用于判断模型是否存在明显过拟合或欠拟合。"),
        ("10_feature_importance_or_shap.png", "图11  模型解释性分析图", "模型解释性结果用于说明影响流失预测的关键因素。项目已排除 churn_signal 及其直接来源字段，避免标签泄露。"),
    ]:
        p = add_image_after(p, SCREEN / img, cap, width=5.4)
        p = add_after(p, desc)

    # Part 5.
    replace_exact(ps, "通过该项目的设计和实现，掌握了哪些理论知识和实践技能。。。。。。", "通过本项目的设计与实现，我们系统掌握了大数据分析项目从数据采集、数据清洗、探索性分析、可视化展示、文本情感分析、客户聚类、分类建模、模型评价到交互式展示的完整流程。理论方面，进一步理解了数据预处理、特征工程、聚类分析、监督学习、交叉验证、模型评价指标和模型可解释性的基本思想；实践方面，熟悉了 pandas、numpy、matplotlib、seaborn、scikit-learn、XGBoost、LightGBM、jieba、wordcloud、SHAP 和 Streamlit 等工具的综合使用。")
    replace_exact(ps, "不足之处，什么原因？下一步如何改进。。。。", "本项目的不足主要包括：第一，公开评论数据缺少企业真实 CRM 中的登录频率、消费金额、续费记录和客服工单，因此流失标签只能根据公开行为和评论信息构造，模型效果与真实企业业务仍有差距；第二，NLP 情感分析主要采用词典规则，对讽刺、反语和复杂语义识别能力有限；第三，去除标签泄露后模型指标下降，说明当前公开数据特征对真实流失预测的支撑有限。下一步可接入真实企业业务数据，引入更强的语义模型，建立定时更新的数据看板和模型监控机制，并结合运营反馈不断调整预警阈值和挽留策略。")
    replace_exact(ps, "至少半页！", "总体来看，本项目较完整地完成了模板要求中的数据读取、数据预处理、数据可视化和业务建模任务，也形成了从数据到业务建议的课程演示原型系统。项目不仅训练了客户流失预测模型，还结合 NLP 情感分析、客户聚类、模型解释和 Streamlit 看板展示，使分析结果能够服务于运营决策。通过本次项目实践，团队进一步提升了数据处理、代码调试、结果解释、报告撰写和项目演示能力。")
    clear_paragraph(find_exact(ps, "说明：写完报告以后，请将红色的“要求”全部删掉。"))
    clear_paragraph(find_exact(ps, "。"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
