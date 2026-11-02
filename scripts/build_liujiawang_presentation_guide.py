from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUT = Path.cwd() / "reports" / "刘佳旺_项目演讲与录屏准备手册.docx"

BLUE = RGBColor(31, 78, 121)
DARK = RGBColor(31, 31, 31)
MUTED = RGBColor(89, 89, 89)
FILL = "F2F4F7"
CALLOUT_BLUE = "EAF2F8"
CALLOUT_YELLOW = "FFF2CC"
CALLOUT_GREEN = "E2F0D9"


def set_east_asia_font(run, name="Microsoft YaHei"):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)


def shade_cell(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text, bold=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(str(text))
    set_east_asia_font(run)
    run.font.size = Pt(9.5)
    run.bold = bold
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    for i, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], header, bold=True)
        shade_cell(table.rows[0].cells[i], FILL)

    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value)

    if widths:
        for row in table.rows:
            for idx, width in enumerate(widths):
                row.cells[idx].width = Inches(width)

    doc.add_paragraph()
    return table


def add_bullets(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(4)
        p.add_run(item)


def add_numbers(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.space_after = Pt(4)
        p.add_run(item)


def add_callout(doc, title, body, fill):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    cell = table.cell(0, 0)
    shade_cell(cell, fill)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run(title)
    set_east_asia_font(run)
    run.bold = True
    run.font.size = Pt(10)
    p2 = cell.add_paragraph(body)
    p2.paragraph_format.space_after = Pt(0)
    for r in p2.runs:
        set_east_asia_font(r)
        r.font.size = Pt(9.5)
    doc.add_paragraph()


def add_code_line(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Consolas"
    r.font.size = Pt(10)


def build_doc():
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.85)
    section.bottom_margin = Inches(0.85)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)

    for style_name in ["Normal", "List Bullet", "List Number"]:
        style = doc.styles[style_name]
        style.font.name = "Microsoft YaHei"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        style.font.size = Pt(10.5)
        style.font.color.rgb = DARK
        style.paragraph_format.line_spacing = 1.15
        style.paragraph_format.space_after = Pt(6)

    heading_tokens = [
        ("Heading 1", 16, BLUE, 12, 6),
        ("Heading 2", 13, BLUE, 8, 4),
        ("Heading 3", 11.5, RGBColor(47, 84, 150), 6, 3),
    ]
    for name, size, color, before, after in heading_tokens:
        style = doc.styles[name]
        style.font.name = "Microsoft YaHei"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("刘佳旺项目演讲与演示录屏准备手册")
    set_east_asia_font(r)
    r.font.size = Pt(20)
    r.font.bold = True
    r.font.color.rgb = BLUE

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("企业客户流失预警与挽留分析系统 | 下周答辩使用")
    set_east_asia_font(r)
    r.font.size = Pt(10.5)
    r.font.color.rgb = MUTED

    doc.add_paragraph()
    add_callout(
        doc,
        "使用说明",
        "这份文档是新的答辩准备材料，不修改原项目报告。你可以按“项目一句话、业务逻辑、演示路线、老师问答”四个部分来准备。重点不是背代码，而是把业务问题、分析流程、测试问题和改进点讲清。",
        CALLOUT_BLUE,
    )

    doc.add_heading("一、先把项目讲成一句话", level=1)
    doc.add_paragraph(
        "这个项目不是单纯做一个分类模型，而是做一个从公开用户行为数据出发的客户流失预警闭环系统。它先采集 Steam 公开评论数据，再完成清洗、文本情感分析、可视化、客户分群、多模型预测、模型解释，最后用 Streamlit 看板把结果展示给运营人员，用于提前识别高风险客户并给出挽留建议。"
    )
    add_table(
        doc,
        ["答辩要点", "你可以这样说"],
        [
            ["业务问题", "企业或平台往往等用户已经离开才发现问题，本项目希望提前识别潜在流失客户。"],
            ["数据来源", "使用 Steam 公开评论数据，字段包括评论文本、游戏时长、是否好评、获赞数、评论时间等。"],
            ["分析方法", "清洗和特征工程负责把原始数据变成可分析数据；NLP 解释评论情感；聚类识别客户群体；分类模型做流失预测。"],
            ["最终价值", "不是只给一个准确率，而是告诉运营人员哪些客户风险高、为什么风险高、应该怎么挽留。"],
        ],
        [1.3, 5.7],
    )

    doc.add_heading("二、当前项目现状和最新结果", level=1)
    add_table(
        doc,
        ["项目项", "当前结果"],
        [
            ["样本量", "清洗后 2000 条客户评论数据，35 个字段。"],
            ["时间范围", "2023-12-31 17:43:00 到 2025-05-15 13:30:00。"],
            ["整体流失率", "约 49.30%。"],
            ["NLP 情感分布", "正面 24.25%，中性 44.60%，负面 31.15%，平均情感分约 -0.069。"],
            ["客户聚类", "K-Means 最优分为 4 类，四类样本量分别为 272、774、171、783。"],
            ["最佳模型", "去除标签泄露后，当前最佳模型为 DecisionTree。"],
            ["模型指标", "DecisionTree 测试集 F1=0.6254，AUC=0.5334；5 折交叉验证 F1=0.5045±0.0716，AUC=0.5260±0.0376。"],
            ["重要提醒", "近期已修复标签泄露问题，模型指标下降是正常现象，说明现在结果更真实。"],
        ],
        [1.4, 5.6],
    )
    add_callout(
        doc,
        "答辩时要主动说明的改进",
        "之前 churn_label 是由 churn_signal 派生的，而 churn_signal 又由部分入模特征计算得到。我们检查 build_model_features 后，进一步把 churn_signal 及标签公式直接来源字段从模型特征中排除，并重新训练模型。指标下降，但业务解释更可信。老师如果问“为什么指标不高”，这正好说明我们没有用泄露字段虚增效果。",
        CALLOUT_YELLOW,
    )

    doc.add_heading("三、系统流程怎么讲", level=1)
    add_numbers(
        doc,
        [
            "数据采集：调用 Steam 公开评论 API，带有本地缓存、重试、请求间隔和备用数据机制。",
            "数据预处理：处理缺失值、异常值、字段类型，把评论文本、游戏时长、互动数据转成结构化特征。",
            "NLP 情感分析：用 jieba 分词和情感词典分析评论情绪，生成情感分布、词云和关键词图。",
            "可视化分析：观察流失比例、游戏时长层级、产品差异、参与度与流失关系、情感趋势。",
            "标准分析流程补充：生成对比分析、分组分析、交叉分析、回归分析、时间序列分析、关联规则分析等文件。",
            "客户聚类：用 K-Means 把客户分群，再结合业务解释不同群体的风险和运营策略。",
            "多模型训练：比较逻辑回归、决策树、随机森林、GBDT、XGBoost、LightGBM 和 Stacking。",
            "模型解释与展示：输出特征重要性、学习曲线、混淆矩阵、SHAP 图，并在 Streamlit 看板中演示。",
        ],
    )
    add_table(
        doc,
        ["层级", "对应模块", "业务含义"],
        [
            ["数据采集层", "scraper.py", "把公开评论数据转成项目原始数据，并保证网络异常时仍可运行。"],
            ["数据处理层", "preprocess.py", "清洗数据、构造字段、排除泄露特征，保证模型输入稳定。"],
            ["分析挖掘层", "nlp_analysis.py、visualization.py、standard_flow_analysis.py、deep_mining.py", "从文本、图表、分组、时间趋势、关联规则和聚类角度解释流失。"],
            ["模型预测层", "modeling.py", "训练多个模型并比较 F1、AUC 等指标，选择适合当前数据的模型。"],
            ["交互展示层", "streamlit_app.py", "把分析结果变成老师和业务人员能看懂的交互式页面。"],
        ],
        [1.2, 2.4, 3.4],
    )

    doc.add_heading("四、你的分工应该怎么讲", level=1)
    doc.add_paragraph(
        "根据原 Word 报告中的分工，刘佳旺的职责不是一个单独小模块，而是偏项目主线和核心算法实现。答辩时要把自己的工作讲成“负责让项目跑通、可解释、能展示”。"
    )
    add_table(
        doc,
        ["你的分工", "答辩说法", "老师追问时补充"],
        [
            ["总体规划、技术路线、进度协调", "我负责确定项目从数据采集到模型展示的整体路线，保证每个模块能连成完整流程。", "可以强调采用“采集-清洗-NLP-可视化-聚类-建模-看板”的闭环，而不是零散图表。"],
            ["数据预处理与特征工程", "我负责把原始评论数据处理成模型能使用的结构化特征。", "包括缺失值填充、异常值裁剪、评论长度、游戏时长、参与度等衍生字段。"],
            ["模型训练与评估", "我负责多模型训练、指标比较和模型保存。", "指标不只看准确率，还看 F1、Recall、AUC，因为流失识别更关注能不能发现高风险客户。"],
            ["Streamlit 看板整合", "我负责把分析结果整合进交互式页面，方便演示业务概览、NLP、聚类、模型评估和单客预测。", "可以强调看板模拟真实企业运营人员使用场景。"],
            ["项目调试与报告统稿", "我负责最后联调流程、修复问题，并把各模块结果统一到报告口径。", "最近修复的标签泄露问题就是一次典型调试和质量控制。"],
        ],
        [1.5, 3.0, 2.5],
    )

    doc.add_heading("五、演讲时的推荐顺序", level=1)
    add_numbers(
        doc,
        [
            "开头 30 秒：说明业务背景。客户流失会带来获客成本上升，所以要提前预警。",
            "项目目标 30 秒：说明本项目做的是完整数据分析系统，不只是训练模型。",
            "数据和流程 1 分钟：介绍 Steam 评论数据、字段、清洗、NLP、可视化、聚类、建模和看板。",
            "核心功能 2 分钟：重点讲业务概览、NLP 情感分析、客户分群、模型评估、单客预测。",
            "你的工作 1 分钟：讲你负责总体规划、预处理、特征工程、模型训练、看板整合和调试。",
            "测试和问题 1 分钟：讲缓存、网络、中文字体、模型指标、标签泄露等问题如何解决。",
            "总结 30 秒：系统能帮助运营人员识别高风险客户，并为差异化挽留策略提供依据。",
        ],
    )
    add_callout(
        doc,
        "演讲口径",
        "不要把重点放在“我用了很多模型”。老师更可能关心为什么做这个项目、数据怎么来的、业务上怎么用、测试中遇到什么问题、模型结果为什么可信。",
        CALLOUT_BLUE,
    )

    doc.add_heading("六、完整演示录屏怎么录", level=1)
    doc.add_heading("录屏前准备", level=2)
    add_numbers(
        doc,
        [
            "先运行一次 python run_project.py，确认 outputs 目录下的模型、图表、NLP 和聚类结果都是最新的。正式录屏前建议再确认 model_metrics.csv 是否存在。",
            r"打开 PowerShell，进入项目目录：E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis。",
            "启动 Streamlit：streamlit run streamlit_app.py。如果命令不可用，可以用 python -m streamlit run streamlit_app.py。",
            "浏览器打开 Streamlit 自动给出的本地地址，通常是 http://localhost:8501。",
            "关闭无关窗口，桌面只保留 PowerShell、浏览器和项目目录，避免录屏杂乱。",
        ],
    )
    doc.add_heading("推荐录屏工具", level=2)
    add_table(
        doc,
        ["工具", "适合情况", "操作要点"],
        [
            ["Windows 自带 Xbox Game Bar", "最简单，适合快速录屏。", "按 Win+G，选择录制；如果不能录桌面，就先聚焦浏览器窗口再录。"],
            ["OBS Studio", "最稳，适合录完整演示。", "新建“显示器采集”或“窗口采集”，设置 1080p，开始录制。"],
            ["PowerPoint 录屏", "如果你边讲 PPT 边演示系统。", "插入-屏幕录制，选择浏览器区域，录完可导出视频。"],
        ],
        [1.5, 2.5, 3.0],
    )
    doc.add_heading("建议录屏脚本", level=2)
    add_numbers(
        doc,
        [
            "先展示项目目录：说明 data、src、outputs、reports、streamlit_app.py、run_project.py 分别是什么。时间控制在 20 秒。",
            "展示命令行运行入口：说明 python run_project.py 会完成采集、清洗、NLP、聚类、模型训练、图表输出。不要完整重跑，除非时间允许；可以展示已经生成的 outputs。",
            "打开 Streamlit 首页或业务概览：讲样本量、流失率、时间范围、产品筛选。",
            "切到 NLP 文本挖掘：讲正面、中性、负面评论比例，以及负面评论对流失预警的业务意义。",
            "切到聚类分群：讲 K-Means 把客户分成 4 类，不同客户群可以采取不同挽留策略。",
            "切到模型评估：讲多个模型对比，重点讲 F1、Recall、AUC，不要只讲 Accuracy。说明已修复标签泄露，所以指标更真实。",
            "切到模型稳定性或输出图表：展示学习曲线、混淆矩阵、SHAP/特征重要性图，说明模型不是黑盒。",
            "切到单客预测：输入一个低时长、负面评价、低参与度用户，展示流失概率和挽留建议。再输入一个高时长、正面评价用户，对比风险变化。",
            "结尾：总结系统可以服务运营决策，未来可以接入真实企业数据、登录频率、消费记录和客服工单。",
        ],
    )
    add_callout(
        doc,
        "录屏时不要做的事",
        "不要现场长时间等待完整训练；不要在录屏里翻太多代码；不要讲“准确率很高”这种不稳的说法；不要隐藏模型不足。更好的表达是：本系统完成了完整流程，当前公开评论数据能支撑基础预警，但真实企业场景还需要更多业务行为数据。",
        CALLOUT_YELLOW,
    )

    doc.add_heading("七、测试时遇到的问题与解决思路", level=1)
    add_table(
        doc,
        ["问题", "现象", "解决方式", "答辩表达"],
        [
            ["网络爬取不稳定", "Steam API 可能限流、超时或网络不可用。", "加入本地缓存、请求间隔、重试机制和备用数据。", "保证系统不是依赖一次网络请求，而是具备可复现实验能力。"],
            ["数据缺失和异常值", "部分字段为空、数值字段类型不统一，游戏时长可能出现异常。", "统一转数值、缺失填 0、负值裁剪、类别字段填 unknown。", "数据预处理是建模前最关键的质量控制。"],
            ["中文图表显示", "matplotlib 图表可能出现中文乱码。", "在可视化配置中设置中文字体或使用系统可用字体。", "测试图表时不仅看代码运行，还要看图片是否可读。"],
            ["模型指标虚高风险", "如果把 churn_signal 放进特征，模型等于学习标签公式。", "排除 churn_signal 及标签公式直接来源字段，补测试并重新训练。", "我们主动修复标签泄露，宁可指标下降，也保证分析结论可信。"],
            ["多个模型表现接近", "去泄露后模型 F1 差距不大，AUC 也不高。", "解释为公开评论数据特征有限，后续应补充真实业务行为特征。", "瓶颈不在继续堆模型，而在数据和特征质量。"],
            ["Streamlit 页面依赖输出文件", "如果没有先跑主流程，页面会提示缺少模型或图表。", "先运行 python run_project.py，再启动 streamlit run streamlit_app.py。", "这是离线分析结果和在线展示页面的依赖关系。"],
        ],
        [1.2, 1.6, 2.1, 2.1],
    )

    doc.add_heading("八、老师可能问你的问题", level=1)
    qa = [
        ("为什么选择客户流失预警这个题目？", "因为客户流失是企业运营里很典型的问题，直接影响收入和获客成本。通过数据分析提前识别高风险客户，可以让运营人员在用户真正离开前进行干预。这个题目也能覆盖课程要求的数据采集、预处理、可视化、建模和业务解释。"),
        ("为什么用 Steam 评论数据，它和企业客户有什么关系？", "Steam 评论数据虽然不是传统 CRM 数据，但它包含用户行为和反馈，例如游戏时长、是否好评、评论文本、互动数据和评论时间。我们把它作为互联网产品用户行为数据的公开替代，用来模拟客户流失预警场景。真实企业落地时，可以替换成登录、消费、客服、会员等数据。"),
        ("你们的流失标签是怎么来的，真实吗？", "公开数据没有真实的“是否流失”字段，所以项目根据评论倾向、使用时长、互动行为等构造了流失标签。这是课程项目里的模拟标签，不等同于企业真实流失。我们也意识到标签构造会影响模型可信度，所以修复了标签泄露，避免模型直接学习标签公式。"),
        ("为什么修复标签泄露后指标下降了？", "因为原来部分特征和标签生成逻辑关系太近，模型容易学到规则本身，指标会偏高。修复后，模型只能依赖剩余行为特征预测，难度更大，指标下降是正常的。这样虽然结果没那么漂亮，但更接近真实业务建模。"),
        ("为什么不用准确率作为主要指标？", "流失预警更关心能不能识别出高风险客户。如果只看准确率，在类别不均衡时可能误导判断。F1 综合 precision 和 recall，AUC 反映排序能力，所以我们用多指标综合评价。"),
        ("为什么最终 DecisionTree 最好，复杂模型反而不一定好？", "当前特征数量和样本规模有限，而且去除泄露字段后有效信号不强。复杂模型不一定能明显提升，反而可能受噪声影响。DecisionTree 在本次测试集上 F1 排第一，但从交叉验证看整体模型仍有提升空间。"),
        ("模型效果不高，这个项目还有意义吗？", "有意义。这个项目的重点是完整分析闭环和业务解释，不是追求一个很高但不真实的分数。模型效果不高反而说明公开评论数据对流失预测的信息有限，后续应补充真实业务特征，如登录频率、消费金额、客服投诉和会员等级。"),
        ("客户聚类有什么业务作用？", "分类模型回答“这个客户会不会流失”，聚类回答“客户属于哪一类”。聚类可以帮助运营人员制定差异化策略，比如高价值低风险客户维持互动，低活跃高风险客户重点挽留，负面评论客户优先客服跟进。"),
        ("NLP 情感分析为什么重要？", "用户评论文本包含很多结构化字段看不到的信息。情感分析可以把文本反馈转成正面、中性、负面等指标，帮助解释客户为什么可能流失，也能支持后续产品优化和客服处理。"),
        ("测试中你主要解决了什么问题？", "我主要解决了数据预处理稳定性、模型特征构建、标签泄露检查、模型重训和 Streamlit 看板整合问题。特别是标签泄露问题，修复后我们重新训练模型，并确认特征重要性中不再出现泄露字段。"),
        ("如果要真正上线，还缺什么？", "需要接入真实企业数据，包括用户登录、消费、续费、客服工单、投诉、会员等级和真实流失时间；还需要定时任务、模型监控、阈值策略、运营反馈闭环和权限管理。"),
        ("你的个人贡献是什么？", "我负责项目总体规划和技术路线，完成数据预处理、特征工程、模型训练评估等核心算法模块，同时整合 Streamlit 看板、联调项目流程并统稿报告。我的重点是保证项目能从数据到模型再到业务展示完整跑通。"),
    ]
    for question, answer in qa:
        doc.add_heading(question, level=2)
        doc.add_paragraph(answer)

    doc.add_heading("九、现场答辩速记", level=1)
    add_table(
        doc,
        ["老师问到", "你先回答这一句"],
        [
            ["业务价值", "提前识别高风险客户，降低流失带来的获客和运营成本。"],
            ["数据来源", "Steam 公开评论数据，用作互联网产品用户行为数据的公开替代。"],
            ["你的贡献", "总体规划、预处理、特征工程、模型训练评估、看板整合和调试统稿。"],
            ["模型指标不高", "去除标签泄露后结果更真实，说明后续重点应补充真实业务特征。"],
            ["测试问题", "网络缓存、缺失值处理、中文图表、输出文件依赖、标签泄露。"],
            ["未来优化", "接入真实 CRM 数据、消费/登录/客服记录，引入定时预警和运营反馈闭环。"],
        ],
        [1.6, 5.4],
    )

    doc.add_heading("十、演示命令备忘", level=1)
    for line in [
        r"cd E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis",
        "python run_project.py",
        "streamlit run streamlit_app.py",
        "python -m pytest -q",
    ]:
        add_code_line(doc, line)

    add_callout(
        doc,
        "最后提醒",
        "正式演讲前，把“旧报告里的模型指标”和“最新重训后的模型指标”区分清楚。现在建议以最新结果为准：DecisionTree F1=0.6254，交叉验证 F1=0.5045±0.0716，并说明这是去除标签泄露后的结果。",
        CALLOUT_GREEN,
    )

    for section in doc.sections:
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = footer.add_run("刘佳旺 | 企业客户流失预警与挽留分析系统答辩准备")
        set_east_asia_font(run)
        run.font.size = Pt(8)
        run.font.color.rgb = MUTED

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    return OUT


if __name__ == "__main__":
    print(build_doc())
