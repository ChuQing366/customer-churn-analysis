from __future__ import annotations

import re
import shutil
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"E:\Pycharm\数分项目设计\customer-churn-analysis\customer-churn-analysis")
FINAL_DOCX = Path(r"C:\Users\Liu Jiawang\Desktop\第二学期-作业\数分\第五组\交付\第五组-企业客户流失与预警分析系统-最终打印版.docx")
OUT_DOCX = FINAL_DOCX.with_name("第五组-企业客户流失与预警分析系统-最终打印版-修订.docx")
ARCH_PATH = ROOT / "reports" / "system_architecture_7modules.png"


def set_run_font(run, size: float | None = None, bold: bool | None = None) -> None:
    run.font.name = "宋体"
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def replace_paragraph_text(paragraph, text: str) -> None:
    style = paragraph.style
    alignment = paragraph.alignment
    paragraph.clear()
    paragraph.style = style
    paragraph.alignment = alignment
    run = paragraph.add_run(text)
    set_run_font(run, 12)


def paragraph_text(paragraph) -> str:
    return paragraph.text.strip()


def find_paragraph(doc: Document, text: str, start: int = 0) -> int:
    for i, p in enumerate(doc.paragraphs[start:], start):
        if paragraph_text(p) == text:
            return i
    raise ValueError(f"paragraph not found: {text}")


def find_contains(doc: Document, needle: str, start: int = 0) -> int:
    for i, p in enumerate(doc.paragraphs[start:], start):
        if needle in p.text:
            return i
    raise ValueError(f"paragraph containing not found: {needle}")


def insert_paragraph_after(paragraph, text: str = "", style=None):
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    p = paragraph._parent.add_paragraph()
    p._p = new_p
    p._element = new_p
    if style is not None:
        p.style = style
    if text:
        r = p.add_run(text)
        set_run_font(r, 12)
    return p


def make_caption(paragraph, text: str) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(6)
    replace_paragraph_text(paragraph, text)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_image_after(paragraph, image_path: Path, caption: str, note: str, width_inches: float = 5.8):
    note_p = insert_paragraph_after(paragraph, note)
    img_p = insert_paragraph_after(note_p)
    img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img_run = img_p.add_run()
    img_run.add_picture(str(image_path), width=Inches(width_inches))
    cap_p = insert_paragraph_after(img_p)
    make_caption(cap_p, caption)
    return cap_p


def generate_architecture_diagram(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    W, H = 1900, 920
    img = Image.new("RGB", (W, H), "#fbfcfd")
    draw = ImageDraw.Draw(img)
    font_title = ImageFont.truetype(r"C:\Windows\Fonts\simhei.ttf", 48)
    font_box = ImageFont.truetype(r"C:\Windows\Fonts\simhei.ttf", 32)
    font_small = ImageFont.truetype(r"C:\Windows\Fonts\simsun.ttc", 24)
    font_num = ImageFont.truetype(r"C:\Windows\Fonts\simhei.ttf", 26)

    draw.text((W // 2, 58), "企业客户流失预警与挽留分析系统架构图", fill="#1f2937", font=font_title, anchor="mm")
    draw.line((190, 110, W - 190, 110), fill="#2563eb", width=5)

    boxes = [
        ("1", "数据采集模块", "Steam API / 备用数据\n评论、时长、评分、互动"),
        ("2", "数据预处理模块", "缺失值、异常值、编码\n特征衍生与标签构造"),
        ("3", "NLP文本挖掘模块", "分词、情感评分\n关键词与词云输出"),
        ("4", "数据可视化模块", "流失分布、产品差异\n参与度与情感图表"),
        ("5", "客户聚类模块", "K-Means 分群\nPCA 降维展示画像"),
        ("6", "模型训练与评价模块", "分类预测、多模型对比\n混淆矩阵与学习曲线"),
        ("7", "交互展示与预警模块", "Streamlit 看板\n结果解释与单客预测"),
    ]
    positions = [
        (95, 175, 480, 355),
        (560, 175, 945, 355),
        (1025, 175, 1410, 355),
        (1485, 175, 1870, 355),
        (1025, 545, 1410, 725),
        (560, 545, 945, 725),
        (95, 545, 480, 725),
    ]
    colors = ["#dbeafe", "#dcfce7", "#fef3c7", "#ede9fe", "#cffafe", "#fee2e2", "#e5e7eb"]
    outlines = ["#2563eb", "#16a34a", "#d97706", "#7c3aed", "#0891b2", "#dc2626", "#4b5563"]

    for (num, title, desc), rect, fill, outline in zip(boxes, positions, colors, outlines):
        draw.rounded_rectangle(rect, radius=28, fill=fill, outline=outline, width=4)
        x1, y1, x2, y2 = rect
        draw.ellipse((x1 + 22, y1 + 20, x1 + 70, y1 + 68), fill=outline)
        draw.text((x1 + 46, y1 + 44), num, fill="white", font=font_num, anchor="mm")
        draw.text(((x1 + x2) // 2 + 25, y1 + 52), title, fill="#111827", font=font_box, anchor="mm")
        for j, line in enumerate(desc.split("\n")):
            draw.text(((x1 + x2) // 2, y1 + 108 + j * 34), line, fill="#374151", font=font_small, anchor="mm")

    def arrow(p1, p2):
        draw.line((p1, p2), fill="#6b7280", width=5)
        x1, y1 = p1
        x2, y2 = p2
        if abs(x2 - x1) >= abs(y2 - y1):
            sign = 1 if x2 > x1 else -1
            pts = [(x2, y2), (x2 - sign * 20, y2 - 12), (x2 - sign * 20, y2 + 12)]
        else:
            sign = 1 if y2 > y1 else -1
            pts = [(x2, y2), (x2 - 12, y2 - sign * 20), (x2 + 12, y2 - sign * 20)]
        draw.polygon(pts, fill="#6b7280")

    arrow((480, 265), (560, 265))
    arrow((945, 265), (1025, 265))
    arrow((1410, 265), (1485, 265))
    arrow((1680, 355), (1220, 545))
    arrow((1025, 635), (945, 635))
    arrow((560, 635), (480, 635))

    draw.rounded_rectangle((360, 790, 1540, 865), radius=22, fill="#ffffff", outline="#cbd5e1", width=3)
    draw.text(
        (W // 2, 828),
        "输出结果：清洗数据表、情感分析图、客户分群图、模型评价图、风险预测与业务预警建议",
        fill="#1f2937",
        font=font_small,
        anchor="mm",
    )
    img.save(path)


def replace_first_three_fixed_parts(doc: Document) -> None:
    p1 = find_paragraph(doc, "（1）通过 pandas、numpy 对 Steam 公开评论数据进行读取、清洗、缺失值处理、字段类型转换和特征衍生，形成可用于挖掘建模的结构化客户行为数据。数据处理过程中保留用户评论、游戏时长、评分倾向、互动反馈、评论时间等核心字段，并进一步生成评论长度、评论词数、使用时长分层、参与度评分和流失标签等分析变量，为后续可视化分析、客户分群和分类预测提供统一的数据基础；")
    fixed = [
        "（1）通过Numpy、Pandas 等第三方模块对数据集进行读取和数据清洗；",
        "（2）通过 matplotlib/seaborn 对清洗后的数据进行可视化分析，探索隐藏在大量数据背后的业务规律；",
        "（3）根据业务需求识别项目模型类型（分类、聚类、回归），找出模型所需的特征属性。通过 sklearn进行模型建立、模型训练、模型预测、模型评价。",
        "2、项目要求",
        "（1）项目中需要包含数据读取、数据预处理、数据可视化、业务建模等功能；",
        "（2）使用工具：pycharm 或美林数据 TempoAI",
        "使用技术：numpy、pandas、matplotlib、seaborn、sklearn",
        "3、提交作品",
        "项目设计报告、项目源程序（项目工程目录及相关资源文件）、项目演示录屏。",
        "4、项目组各成员工作分工",
    ]
    for offset, text in enumerate(fixed):
        replace_paragraph_text(doc.paragraphs[p1 + offset], text)


def update_design_text(doc: Document) -> None:
    idx = find_contains(doc, "从需求角度看，本系统需要完成三个层面的任务")
    replace_paragraph_text(
        doc.paragraphs[idx],
        "从需求角度看，本系统不是简单地罗列图表，而是要围绕“哪些客户可能流失、为什么会流失、应当如何预警”开展分析。首先，系统将公开评论、使用时长、互动反馈等原始信息清洗为可计算的客户行为特征，用流失标签刻画客户是否存在离开风险；其次，通过可视化和 NLP 情感分析观察低使用时长、低参与度、负面评论等业务现象是否与流失相关；再次，使用 K-Means 聚类是为了在没有人工分群标签的情况下识别高活跃、低活跃和潜在流失等客户画像，便于制定分层运营策略；使用分类模型则是为了在已有流失标签基础上学习“行为特征→流失风险”的映射关系，对单个客户给出预警判断。聚类解决“客户可以分成哪些类型”的问题，分类解决“某个客户是否可能流失”的问题，两者结合后，系统既能解释群体规律，也能服务单客预测和挽留决策。",
    )

    idx = find_contains(doc, "系统采用“数据采集层—数据处理层—分析挖掘层—模型预测层—交互展示层”")
    replace_paragraph_text(
        doc.paragraphs[idx],
        "系统按照七个业务模块组织整体方案：数据采集模块负责获取 Steam 公开评论与行为数据；数据预处理模块负责完成清洗、编码、异常处理和特征衍生；NLP 文本挖掘模块把评论内容转换为情感分数、关键词和词云结果；数据可视化模块输出流失分布、产品差异、参与度关系和情感分布等分析图；客户聚类模块使用 K-Means 和 PCA 形成客户分群画像；模型训练与评价模块完成分类预测、指标对比、混淆矩阵、学习曲线和特征重要性解释；交互展示与预警模块通过 Streamlit 汇总结果并提供单客风险判断。总体流程为：Steam 数据输入 → 数据清洗与特征工程 → NLP 情感分析 → 可视化分析 → 客户聚类 → 分类模型训练与评价 → 看板展示和预警输出。",
    )

    idx = find_contains(doc, "系统框架图体现了本项目从数据到应用的处理链路")
    replace_paragraph_text(
        doc.paragraphs[idx],
        "图1按照七个模块展示了系统从数据输入到预警输出的完整链路。数据采集和预处理保证输入数据可用；NLP 文本挖掘补充评论情绪和关键词信息；数据可视化负责发现业务现象；客户聚类用于形成客户画像和分层运营思路；模型训练与评价负责完成流失分类预测并验证模型效果；交互展示模块将清洗数据、分析图、预测图和模型解释结果集中到页面中，便于演示、复查和业务解释。",
    )

    idx = find_contains(doc, "系统主要包含七个模块")
    replace_paragraph_text(
        doc.paragraphs[idx],
        "系统主要包含七个模块，并且每个模块都有明确输入、处理动作和输出结果。数据采集模块输入 Steam 公开评论接口或备用数据文件，输出原始评论数据；数据预处理模块输入原始数据，完成字段规范化、缺失值处理、异常值裁剪、评论长度和参与度等特征衍生，输出清洗后的客户行为表；NLP 文本挖掘模块输入评论文本，完成 jieba 分词、情感词典评分、关键词统计和词云生成，输出情感分布图、情感与流失交叉图和高频关键词图；数据可视化模块输入清洗数据和 NLP 结果，输出流失分布、使用时长分组、产品流失率、参与度散点等业务分析图；客户聚类模块输入标准化行为特征，使用 K-Means 形成客户分群，并通过 PCA 展示高活跃、低活跃和潜在流失群体；模型训练与评价模块输入建模特征和 churn_label，训练多种分类模型，输出 Accuracy、Precision、Recall、F1、ROC-AUC、混淆矩阵、学习曲线和特征重要性结果；交互展示模块读取所有 CSV、图片和模型文件，在 Streamlit 页面中展示业务概览、图表结果、模型评估和单客预测。",
    )


def replace_architecture_image(doc: Document) -> None:
    cap_idx = find_contains(doc, "图1  系统框架结构图")
    img_p = doc.paragraphs[cap_idx - 1]
    img_p.clear()
    img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img_p.add_run().add_picture(str(ARCH_PATH), width=Inches(6.35))


def add_extra_result_figures(doc: Document) -> None:
    fig7_idx = find_contains(doc, "情感分析结果表明")
    p = doc.paragraphs[fig7_idx]
    additions = [
        (
            ROOT / "outputs" / "deep_mining" / "nlp_sentiment_by_churn.png",
            "图X  评论情感与流失状态对比图",
            "进一步将情感倾向与流失标签交叉观察，可以看到负面评论与流失风险之间存在更直接的业务联系。该图用于验证 NLP 文本挖掘模块不仅能输出情感分布，还能把情感结果用于解释客户流失差异。",
            5.6,
        ),
        (
            ROOT / "outputs" / "deep_mining" / "nlp_top_keywords.png",
            "图X  NLP 高频关键词分析图",
            "高频关键词结果用于查看客户评论中反复出现的体验问题和产品关注点，为后续解释流失原因提供文本证据，也弥补了单纯数值特征难以表达主观反馈的问题。",
            5.8,
        ),
        (
            ROOT / "outputs" / "deep_mining" / "wordcloud_churn.png",
            "图X  流失客户评论词云图",
            "流失客户词云用于直观呈现高风险客户评论中的主要词语，帮助从文本层面识别可能影响留存的产品体验、情绪表达和用户关注主题。",
            5.8,
        ),
    ]
    for img_path, cap, note, width in additions:
        p = add_image_after(p, img_path, cap, note, width)

    tail_idx = find_contains(doc, "模型解释性结果用于说明影响流失预测的关键因素")
    p = doc.paragraphs[tail_idx]
    additions = [
        (
            ROOT / "outputs" / "standard_flow" / "group_churn_rate.png",
            "图X  分组客户流失率分析图",
            "分组流失率结果用于验证系统能够按照业务分组输出可解释的分析结论，帮助判断不同客户群体的流失风险差异，并与聚类画像和分类预测结果相互印证。",
            5.8,
        ),
        (
            ROOT / "outputs" / "standard_flow" / "time_series_churn_trend.png",
            "图X  客户流失时间趋势分析图",
            "时间趋势图用于观察不同时间窗口下客户流失风险的变化情况，体现系统不仅输出静态模型评价，也能够生成面向运营监测的趋势型分析结果。",
            5.8,
        ),
    ]
    for img_path, cap, note, width in additions:
        p = add_image_after(p, img_path, cap, note, width)


def renumber_figures(doc: Document) -> None:
    n = 1
    for p in doc.paragraphs:
        text = p.text.strip()
        if re.match(r"^图(?:\d+|X)\s+", text):
            new_text = re.sub(r"^图(?:\d+|X)", f"图{n}", text)
            make_caption(p, new_text)
            n += 1


def main() -> None:
    generate_architecture_diagram(ARCH_PATH)
    shutil.copy2(FINAL_DOCX, OUT_DOCX)
    doc = Document(str(OUT_DOCX))
    replace_first_three_fixed_parts(doc)
    update_design_text(doc)
    replace_architecture_image(doc)
    add_extra_result_figures(doc)
    renumber_figures(doc)
    doc.save(str(OUT_DOCX))
    print(OUT_DOCX)


if __name__ == "__main__":
    main()
