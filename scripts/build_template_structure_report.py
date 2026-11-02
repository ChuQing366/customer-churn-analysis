from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


ROOT = Path.cwd()
OUT = ROOT / "reports" / "第五组-企业客户流失与预警分析系统-模板结构重写版.docx"
SCREEN = ROOT / "reports" / "screenshots"
FRAMEWORK = ROOT / "outputs" / "standard_flow" / "system_framework_diagram.png"

SONGTI = "\u5b8b\u4f53"
HEITI = "\u9ed1\u4f53"
TIMES = "Times New Roman"


def set_run_font(run, name=SONGTI, size=12, bold=False):
    run.font.name = name
    if run._element.rPr is None:
        run._element.get_or_add_rPr()
    if run._element.rPr.rFonts is None:
        run._element.rPr.get_or_add_rFonts()
    for attr in ["w:eastAsia", "w:ascii", "w:hAnsi", "w:cs"]:
        run._element.rPr.rFonts.set(qn(attr), name)
    run.font.size = Pt(size)
    run.bold = bold


def set_para(paragraph, align=None, before=0, after=6, line_spacing=1.5):
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.line_spacing = line_spacing
    if align is not None:
        paragraph.alignment = align


def add_p(doc, text="", size=12, bold=False, align=None, font=SONGTI, before=0, after=6):
    p = doc.add_paragraph()
    set_para(p, align=align, before=before, after=after)
    if text:
        r = p.add_run(text)
        set_run_font(r, font, size, bold)
    return p


def add_heading(doc, text, level=1):
    if level == 1:
        p = add_p(doc, text, size=14, bold=True, font=HEITI, before=10, after=8)
    else:
        p = add_p(doc, text, size=12, bold=True, font=HEITI, before=8, after=6)
    return p


def shade_cell(cell, fill="F2F2F2"):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text, font=SONGTI, size=10.5, bold=False):
    cell.text = ""
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    p = cell.paragraphs[0]
    set_para(p, after=0)
    r = p.add_run(str(text))
    set_run_font(r, font, size, bold)


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], header, bold=True)
        shade_cell(table.rows[0].cells[i])
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value)
    if widths:
        for row in table.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Inches(width)
    add_p(doc, "", after=2)
    return table


def add_code_table(doc, code):
    table = doc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    cell.text = ""
    p = cell.paragraphs[0]
    set_para(p, after=0)
    for idx, line in enumerate(code.strip().splitlines()):
        if idx:
            p.add_run("\n")
        r = p.add_run(line)
        set_run_font(r, TIMES, 12)
    add_p(doc, "", after=2)
    return table


def add_image(doc, path, caption, width=5.7):
    if not path.exists():
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Inches(width))
    cap = add_p(doc, caption, size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER, after=6)
    return cap


def add_cover(doc):
    for _ in range(3):
        add_p(doc, "", after=0)
    add_p(doc, "项目设计报告", size=22, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font=HEITI, after=28)
    meta = [
        "课程名称：             《大数据分析与应用》",
        "项目名称：         企业客户流失预警与挽留分析系统",
        "专业班级：             计科（专升本）2502",
        "学生姓名：   刘佳旺（20252S1037）、辛天乐（20252S1132）、孟航天（20252S1082）",
        "开课时间：              2026.3-2026.7",
        "授课教师：              路陈红",
    ]
    for item in meta:
        add_p(doc, item, size=14, align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
    for _ in range(6):
        add_p(doc, "", after=0)
    add_p(doc, "智能科学与工程学院", size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font=HEITI)
    doc.add_page_break()
    add_p(doc, "《大数据分析与应用》课程", size=18, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font=HEITI, after=4)
    add_p(doc, "场景化综合实验", size=18, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font=HEITI, after=4)
    add_p(doc, "—企业客户流失预警与挽留分析系统", size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font=HEITI, after=16)


def build():
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.9)
    section.bottom_margin = Inches(0.9)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)

    for style_name in ["Normal", "List Paragraph", "List Bullet", "List Number"]:
        if style_name in doc.styles:
            style = doc.styles[style_name]
            style.font.name = SONGTI
            style._element.rPr.rFonts.set(qn("w:eastAsia"), SONGTI)
            style.font.size = Pt(12)
            style.paragraph_format.line_spacing = 1.5

    add_cover(doc)

    add_heading(doc, "一、功能与要求")
    add_heading(doc, "1、实现功能", level=2)
    for text in [
        "（1）通过 pandas、numpy 对 Steam 公开评论数据进行读取、字段整理、缺失值处理、异常值裁剪和类型转换，形成可用于后续分析建模的结构化客户行为数据。",
        "（2）通过 matplotlib、seaborn 对清洗后的数据进行可视化分析，展示客户流失总体分布、使用时长与流失关系、不同产品流失率、参与度与流失关系、评论情感分布等业务规律。",
        "（3）根据客户流失预警目标，构建二分类预测模型，并结合 K-Means 聚类完成客户分群；通过 scikit-learn、XGBoost、LightGBM 完成模型训练、预测、评价和解释，同时使用 Streamlit 实现交互式看板与单客流失预测。",
    ]:
        add_p(doc, text)

    add_heading(doc, "2、项目要求", level=2)
    add_p(doc, "（1）项目中包含数据读取、数据预处理、数据可视化、业务建模等功能，并补充 NLP 文本挖掘、客户聚类、模型解释、标准分析流程和交互式展示功能。")
    add_p(doc, "（2）使用工具：PyCharm、Python 脚本调试环境、Streamlit 交互式展示页面。")
    add_p(doc, "使用技术：numpy、pandas、matplotlib、seaborn、scikit-learn、XGBoost、LightGBM、jieba、wordcloud、SHAP、Streamlit。")

    add_heading(doc, "3、提交作品", level=2)
    add_p(doc, "项目设计报告、项目源程序（项目工程目录及相关资源文件）、项目演示录屏。")

    add_heading(doc, "4、项目组各成员工作分工", level=2)
    add_table(
        doc,
        ["项目名称", "成员", "实现功能"],
        [
            ["企业客户流失预警与挽留分析系统", "刘佳旺", "负责项目总体规划、技术路线设计和进度协调。"],
            ["企业客户流失预警与挽留分析系统", "刘佳旺", "完成数据预处理、特征工程、模型训练与评估等核心算法模块。"],
            ["企业客户流失预警与挽留分析系统", "刘佳旺", "负责 Streamlit 看板整合、项目调试和报告统稿。"],
            ["企业客户流失预警与挽留分析系统", "辛天乐", "负责数据采集模块和原始数据整理，协助完成 Steam 评论字段梳理、数据质量检查、基础统计分析和部分可视化图表制作。"],
            ["企业客户流失预警与挽留分析系统", "孟航天", "负责 NLP 情感分析和客户分群结果整理，协助完成词云、关键词分析、聚类业务解释和测试截图整理。"],
        ],
        widths=[2.2, 1.0, 4.0],
    )

    add_heading(doc, "二、系统方案设计")
    add_heading(doc, "1、系统背景", level=2)
    add_p(doc, "本系统面向互联网产品运营、游戏社区运营和企业客户关系管理场景，重点解决“用户可能流失但企业难以及时发现”的问题。客户流失会提高企业获客成本，降低产品留存和收入稳定性，因此需要借助数据分析方法提前识别高风险客户。")
    add_p(doc, "项目使用 Steam 公开评论数据作为模拟业务数据源，采集用户评论、游戏时长、评分倾向、获赞数、评论时间等信息，通过数据清洗、文本情感分析、可视化分析、客户聚类和分类建模，识别不同用户群体的流失风险，并输出影响因素和挽留建议。系统使用对象包括运营人员、客户经理、数据分析人员和课程项目评审人员。")

    add_heading(doc, "2、系统总体设计", level=2)
    add_p(doc, "系统采用“数据采集层—数据处理层—分析挖掘层—模型预测层—交互展示层”的分层设计思路。整体流程为：Steam 公开评论 API → 数据采集与缓存 → 数据清洗与特征工程 → NLP 情感分析和数据可视化 → K-Means 客户分群 → 多模型训练与评价 → SHAP/特征重要性解释 → Streamlit 交互看板与单客预测。")
    add_image(doc, FRAMEWORK, "图1  系统框架结构图", width=6.2)
    add_p(doc, "该框架既满足模板要求的数据读取、数据预处理、数据可视化和业务建模，也体现了完整数据分析项目从数据输入到业务输出的闭环。项目运行入口为 run_project.py，交互式展示入口为 streamlit_app.py，所有结果文件统一输出到 outputs 目录，便于测试、报告截图和演示录屏。")

    add_heading(doc, "3、系统模块设计", level=2)
    for text in [
        "（1）数据采集模块：调用 Steam 公开评论 API 获取评论数据，并提供本地缓存、请求重试、请求间隔和备用数据机制，保证项目在网络不稳定时仍可演示。",
        "（2）数据预处理模块：完成数值字段转换、缺失值填充、异常值裁剪、类别字段处理，并生成评论长度、游戏时长、参与度分数、流失信号和流失标签等字段。",
        "（3）数据可视化模块：输出流失比例、不同使用时长层级流失率、不同产品流失率、参与度散点图和情感趋势图，帮助从业务角度观察高风险群体特征。",
        "（4）NLP 文本挖掘模块：使用 jieba 分词和情感词典计算评论情感倾向，生成情感分布图、词云和关键词统计，为解释流失原因提供文本依据。",
        "（5）客户聚类模块：使用 K-Means 和 PCA 对客户进行分群，识别不同客户画像，为差异化运营和挽留策略提供依据。",
        "（6）模型训练模块：训练 LogisticRegression、DecisionTree、RandomForest、GradientBoosting、XGBoost、LightGBM 和 StackingEnsemble 等模型，通过 Accuracy、Precision、Recall、F1、ROC-AUC 进行评价。",
        "（7）交互展示模块：通过 Streamlit 展示业务概览、NLP 情感挖掘、聚类分群、模型评估、输出图表和单客预测，实现课程演示和业务应用表达。",
    ]:
        add_p(doc, text)

    add_heading(doc, "三、系统功能实现")
    add_heading(doc, "1、系统开发环境", level=2)
    for text in [
        "操作系统：Windows。",
        "开发工具：PyCharm。",
        "编程语言：Python 3。",
        "核心依赖：pandas、numpy、scikit-learn、matplotlib、seaborn、xgboost、lightgbm、jieba、wordcloud、shap、streamlit、joblib。",
        "运行方式：在项目根目录执行 python run_project.py 生成数据、模型和图表结果；执行 streamlit run streamlit_app.py 启动交互式看板。项目启动截图不作为单独模块展示，只在功能测试中作为系统能够运行的辅助证明。",
    ]:
        add_p(doc, text)

    add_heading(doc, "2、系统各模块功能实现", level=2)
    add_p(doc, "本系统按照“数据读取与探索—数据预处理—数据可视化—数据挖掘建模”的模板结构进行实现。以下各模块选取项目中的核心代码片段进行说明，代码均来自当前项目源码。")

    add_heading(doc, "（1）数据探索性分析", level=2)
    add_p(doc, "功能说明：数据探索阶段主要查看原始数据和清洗后数据的样本数量、字段类型、描述统计、缺失情况和目标变量分布。本项目清洗后数据包含 2000 条样本、35 个字段，整体流失率约为 49.30%，时间范围为 2023-12-31 至 2025-05-15。")
    add_code_table(
        doc,
        """
import pandas as pd
from src.churn_system.config import SCRAPED_DATA_PATH, PROCESSED_DATA_PATH

raw_df = pd.read_csv(SCRAPED_DATA_PATH)
cleaned_df = pd.read_csv(PROCESSED_DATA_PATH)
print(raw_df.shape, cleaned_df.shape)
print(raw_df.dtypes)
print(cleaned_df.describe())
print(cleaned_df["churn_label"].value_counts(normalize=True))
        """,
    )

    add_heading(doc, "（2）数据预处理模块", level=2)
    add_p(doc, "功能说明：数据预处理模块对数值字段进行类型转换、缺失值填充和异常值裁剪；根据评论文本生成评论长度和词数；根据游戏时长、评论倾向、互动反馈等信息构造分析字段。为保证模型评价可信，模型特征构建时会排除 churn_signal 及其直接来源字段，避免标签泄露。")
    add_code_table(
        doc,
        """
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
        """,
    )

    add_heading(doc, "（3）数据可视化模块", level=2)
    add_p(doc, "功能说明：可视化模块围绕客户流失业务问题生成多类图表，包括总体流失占比、不同游戏时长层级流失率、不同产品流失率、游戏时长与参与度散点图、情感趋势图等。通过图表可以直观看到流失客户与留存客户在行为和情感上的差异。")
    add_code_table(
        doc,
        """
def create_visualizations(df: pd.DataFrame, output_dir: Path) -> None:
    _plot_churn_distribution(df, output_dir)
    _plot_playtime_churn_rate(df, output_dir)
    _plot_app_churn_rate(df, output_dir)
    _plot_engagement_vs_churn(df, output_dir)
    _plot_sentiment_timeline(df, output_dir)
        """,
    )

    add_heading(doc, "（4）数据挖掘模块", level=2)
    add_p(doc, "功能说明：数据挖掘模块根据客户流失预警目标建立二分类模型，同时使用 K-Means 完成客户聚类。分类模型通过 F1、Recall、ROC-AUC 等指标评价，聚类结果通过轮廓系数和 PCA 可视化解释。当前去除标签泄露后，DecisionTree 在测试集上 F1=0.6254，Recall=0.8618，ROC-AUC=0.5334。")
    add_code_table(
        doc,
        """
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
        """,
    )

    add_heading(doc, "四、系统功能测试")
    add_p(doc, "本部分按照模板要求对各模块运行结果进行测试，并使用截图验证功能结果是否符合预期。截图主要展示预处理结果、可视化结果、模型评价结果和交互式看板结果。")

    add_heading(doc, "1、数据预处理功能测试", level=2)
    add_p(doc, "测试目标：对比原始数据 scraped_reviews.csv 与清洗后数据 customer_churn_cleaned.csv，验证数据预处理是否正确完成。测试结果显示，系统能够稳定输出 2000 条清洗后样本，字段数量为 35，核心衍生字段包括 review_length、playtime_hours、engagement_score、churn_signal 和 churn_label。")
    add_image(doc, SCREEN / "01_streamlit_business_overview.png", "图2  Streamlit 看板启动与数据概览截图", width=5.8)
    add_p(doc, "测试结论：预处理模块能够完成字段规范化、缺失值处理、异常值裁剪和特征衍生，处理后的数据能够继续用于 NLP 分析、可视化分析、客户聚类和模型训练。")

    add_heading(doc, "2、数据分析可视化功能测试", level=2)
    add_p(doc, "测试目标：验证系统能否输出客户流失相关图表，并从业务角度解释图表结果。")
    add_image(doc, SCREEN / "02_churn_distribution.png", "图3  客户流失总体分布图", width=4.8)
    add_p(doc, "该图展示当前客户样本中流失客户与留存客户的占比，可用于判断整体流失风险水平。当前样本整体流失率约为 49.30%，说明数据中流失与留存样本较为接近，适合进行二分类建模。")
    add_image(doc, SCREEN / "03_playtime_churn_rate.png", "图4  不同使用时长层级的客户流失率", width=5.5)
    add_p(doc, "该图用于分析使用时长与流失之间的关系。一般使用时长越短、参与度越低的客户越容易出现流失风险，因此该图可以帮助运营人员识别低活跃高风险群体。")
    add_image(doc, SCREEN / "04_product_churn_rate.png", "图5  不同产品的客户流失率", width=5.5)
    add_p(doc, "该图比较不同产品下客户流失率差异。若某些产品流失率明显偏高，说明该产品可能存在体验、内容、运营或用户群体差异，需要进一步分析原因。")
    add_image(doc, SCREEN / "05_engagement_scatter.png", "图6  使用时长与参与度关系散点图", width=5.5)
    add_p(doc, "该图展示用户使用时长、参与度和流失状态之间的关系。如果流失客户集中在低时长、低参与度区域，说明活跃不足是流失预警的重要业务信号。")
    add_image(doc, SCREEN / "06_nlp_sentiment_distribution.png", "图7  NLP 评论情感分布图", width=5.3)
    add_p(doc, "该图展示评论情感倾向，包括正面、中性和负面评论。当前 NLP 结果中中性评论占 44.60%，负面评论占 31.15%，正面评论占 24.25%。负面反馈比例较高时，应重点关注客服响应、产品体验和用户挽留策略。")
    add_p(doc, "测试结论：可视化模块能够从客户状态、产品差异、使用时长、参与度和评论情感等多个角度展示客户流失特征，符合模板对散点图、柱状图、饼图和趋势分析的要求。")

    add_heading(doc, "3、数据挖掘功能测试", level=2)
    add_p(doc, "测试目标：验证数据挖掘模型是否合理，并通过不同模型评价指标、聚类结果和模型解释图说明模型效果。")
    add_table(
        doc,
        ["模型", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"],
        [
            ["DecisionTree", "0.492", "0.4907", "0.8618", "0.6254", "0.5334"],
            ["LightGBM", "0.532", "0.5246", "0.5203", "0.5224", "0.5302"],
            ["LogisticRegression", "0.514", "0.5059", "0.5244", "0.5150", "0.5264"],
            ["GradientBoosting", "0.522", "0.5143", "0.5122", "0.5132", "0.5357"],
            ["XGBoost", "0.520", "0.5122", "0.5122", "0.5122", "0.5126"],
            ["RandomForest", "0.532", "0.5261", "0.4919", "0.5084", "0.5538"],
            ["StackingEnsemble", "0.524", "0.5196", "0.4309", "0.4711", "0.5339"],
        ],
        widths=[1.6, 1, 1, 1, 1, 1],
    )
    add_p(doc, "模型评价结果显示，去除标签泄露后 DecisionTree 的 F1 排名最高，为 0.6254，Recall 为 0.8618，说明模型更倾向于识别潜在流失客户，符合流失预警中“宁可多预警，也不要漏掉高风险客户”的业务需求。ROC-AUC 不高，说明公开评论数据对真实流失的预测信号有限，后续仍需接入更完整的企业业务数据。")
    add_image(doc, SCREEN / "07_cluster_analysis.png", "图8  K-Means 客户聚类结果", width=5.5)
    add_p(doc, "聚类结果将客户分为 4 类，可用于区分高活跃客户、低活跃客户、潜在流失客户等群体，从而制定差异化挽留策略。")
    add_image(doc, SCREEN / "08_confusion_matrix.png", "图9  混淆矩阵", width=4.8)
    add_p(doc, "混淆矩阵用于观察模型对流失客户和留存客户的识别情况。对于流失预警场景，Recall 具有重要意义，因为漏判高风险客户会导致企业错过挽留时机。")
    add_image(doc, SCREEN / "09_learning_curve.png", "图10  学习曲线", width=5.4)
    add_p(doc, "学习曲线用于判断模型是否存在明显过拟合或欠拟合。当前交叉验证 F1=0.5045±0.0716，AUC=0.5260±0.0376，说明模型具备基础预警能力，但受限于公开评论数据，仍有提升空间。")
    add_image(doc, SCREEN / "10_feature_importance_or_shap.png", "图11  模型解释性分析图", width=5.4)
    add_p(doc, "模型解释性结果用于说明影响流失预测的关键因素。项目已将 churn_signal 及其直接来源字段从模型训练特征中排除，避免模型直接学习标签公式，从而使模型评价结果更加可信。")
    add_p(doc, "测试结论：数据挖掘模块能够完成客户聚类、多模型训练、模型评价、模型解释和单客预测。虽然去除标签泄露后模型指标下降，但结果更符合真实建模要求，也说明后续改进重点应放在补充真实业务特征，而不是单纯增加模型数量。")

    add_heading(doc, "五、课程总结")
    add_p(doc, "通过本项目的设计与实现，我们系统掌握了大数据分析项目从数据采集、数据清洗、探索性分析、可视化展示、文本情感分析、客户聚类、分类建模、模型评价到交互式展示的完整流程。理论方面，进一步理解了数据预处理、特征工程、聚类分析、监督学习、交叉验证、模型评价指标和模型可解释性的基本思想；实践方面，熟悉了 pandas、numpy、matplotlib、seaborn、scikit-learn、XGBoost、LightGBM、jieba、wordcloud、SHAP 和 Streamlit 等工具的综合使用。")
    add_p(doc, "本项目的主要收获是将课程中的数据分析方法与具体业务问题结合起来。客户流失预警不是单纯追求模型分数，而是要从业务角度解释哪些客户风险高、为什么风险高、如何进行挽留。通过可视化图表可以观察低使用时长、低参与度、负面评论等高风险特征；通过聚类分析可以识别不同客户群体；通过分类模型可以输出单客流失风险；通过模型解释可以提高预测结果的透明度。")
    add_p(doc, "项目实现过程中也遇到了一些问题。第一，Steam 公开评论数据缺少企业真实 CRM 中的登录频率、消费金额、续费记录和客服工单，因此流失标签只能根据公开行为和评论信息构造，模型效果与真实企业业务仍存在差距。第二，NLP 情感分析主要采用词典规则，对讽刺、反语和复杂语义识别能力有限。第三，在模型测试过程中发现标签泄露风险，如果把 churn_signal 或其直接来源字段放入模型，模型指标会虚高，因此项目对特征构建进行了修正并重新训练模型。")
    add_p(doc, "下一步改进方向包括：接入更真实的企业业务数据，例如用户登录频率、消费记录、会员等级、客服投诉和实际流失时间；优化情感分析方法，引入更强的语义模型；建立定时更新的数据看板和模型监控机制；结合运营反馈调整预警阈值和挽留策略。总体来看，本项目较完整地完成了模板要求中的数据读取、数据预处理、数据可视化和业务建模任务，也形成了从数据到业务建议的课程演示原型系统。")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
