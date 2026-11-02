from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


SOURCE_DOC = Path(
    r"C:\Users\Liu Jiawang\Desktop\第二学期-作业\数分\第五组\第五组-企业客户流失与预警分析系统.docx"
)
OUT_DOC = Path.cwd() / "reports" / "第五组-企业客户流失与预警分析系统-按模板完善版.docx"


def set_run_font(run, name="宋体", size=Pt(10.5), bold=False):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = size
    run.bold = bold


def insert_paragraph_after(paragraph, text="", style=None):
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    p = paragraph._parent.add_paragraph()
    p._p = new_p
    p._element = new_p
    if style:
        p.style = style
    if text:
        run = p.add_run(text)
        set_run_font(run)
    return p


def insert_picture_after(paragraph, image_path: Path, width=Inches(5.6), caption: str | None = None):
    anchor = paragraph
    if caption:
        cap = insert_paragraph_after(anchor, caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in cap.runs:
            set_run_font(run, size=Pt(9))
        anchor = cap
    p = insert_paragraph_after(anchor)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(image_path), width=width)
    return p


def add_paragraphs_after(paragraph, texts):
    anchor = paragraph
    for text in texts:
        anchor = insert_paragraph_after(anchor, text)
    return anchor


def replace_text(doc: Document, old: str, new: str):
    for paragraph in doc.paragraphs:
        if old in paragraph.text:
            for run in paragraph.runs:
                if old in run.text:
                    run.text = run.text.replace(old, new)
                    set_run_font(run)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    if old in paragraph.text:
                        for run in paragraph.runs:
                            if old in run.text:
                                run.text = run.text.replace(old, new)
                                set_run_font(run, name="Times New Roman", size=Pt(12))


def find_paragraph(doc: Document, text: str):
    for paragraph in doc.paragraphs:
        if paragraph.text.strip() == text:
            return paragraph
    raise ValueError(f"paragraph not found: {text}")


def add_framework_diagram():
    from PIL import Image, ImageDraw, ImageFont

    out = Path.cwd() / "outputs" / "standard_flow" / "system_framework_diagram.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    labels = [
        ("数据采集层", "Steam 公开评论 API\n本地缓存/重试/备用数据"),
        ("数据处理层", "缺失值处理\n类型转换/特征工程\n标签泄露防护"),
        ("分析挖掘层", "NLP 情感分析\n可视化/标准流程分析\nK-Means 聚类"),
        ("模型预测层", "多模型训练\nGridSearchCV\n模型评价/解释"),
        ("交互展示层", "Streamlit 看板\n单客预测\n挽留建议"),
    ]

    img = Image.new("RGB", (1800, 560), "white")
    draw = ImageDraw.Draw(img)
    font_paths = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
    font_path = next((p for p in font_paths if Path(p).exists()), None)
    title_font = ImageFont.truetype(font_path, 38) if font_path else ImageFont.load_default()
    body_font = ImageFont.truetype(font_path, 27) if font_path else ImageFont.load_default()
    caption_font = ImageFont.truetype(font_path, 30) if font_path else ImageFont.load_default()

    colors = ["#EAF2F8", "#E2F0D9", "#FFF2CC", "#FCE4D6", "#E4DFEC"]
    x_positions = [35, 385, 735, 1085, 1435]
    y = 120
    w = 280
    h = 310
    for idx, ((title, body), x) in enumerate(zip(labels, x_positions)):
        draw.rounded_rectangle((x, y, x + w, y + h), radius=24, fill=colors[idx], outline="#4F81BD", width=4)
        bbox = draw.textbbox((0, 0), title, font=title_font)
        draw.text((x + (w - (bbox[2] - bbox[0])) / 2, y + 42), title, fill="#1F4E79", font=title_font)
        lines = body.splitlines()
        start_y = y + 130
        for line_idx, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=body_font)
            draw.text(
                (x + (w - (bbox[2] - bbox[0])) / 2, start_y + line_idx * 48),
                line,
                fill="#1F1F1F",
                font=body_font,
            )
        if idx < len(labels) - 1:
            x1 = x + w + 25
            x2 = x_positions[idx + 1] - 25
            y_mid = y + h // 2
            draw.line((x1, y_mid, x2, y_mid), fill="#4F81BD", width=5)
            draw.polygon([(x2, y_mid), (x2 - 22, y_mid - 14), (x2 - 22, y_mid + 14)], fill="#4F81BD")

    caption = "图：企业客户流失预警与挽留分析系统总体框架"
    bbox = draw.textbbox((0, 0), caption, font=caption_font)
    draw.text(((1800 - (bbox[2] - bbox[0])) / 2, 485), caption, fill="#333333", font=caption_font)
    img.save(out)
    return out


def build_doc():
    framework_img = add_framework_diagram()
    doc = Document(SOURCE_DOC)

    replacements = {
        "当前最佳模型为 GradientBoosting，F1 分数为 0.6433，ROC-AUC 为 0.6678。": "修复标签泄露并重新训练后，当前测试集 F1 排名最高的模型为 DecisionTree，F1=0.6254，ROC-AUC=0.5334；5 折交叉验证 F1=0.5045±0.0716，AUC=0.5260±0.0376。该结果比修复前更保守，但更能反映模型在去除泄露特征后的真实表现。",
        "当前最佳模型为 GradientBoosting，F1=0.6433，ROC-AUC=0.6678，说明该模型在识别流失客户方面综合表现较好。": "修复标签泄露并重新训练后，DecisionTree 在测试集上 F1=0.6254，ROC-AUC=0.5334，Recall=0.8618。该模型召回率较高，说明它更倾向于识别出潜在流失客户，适合课程项目中“预警优先”的业务目标；但 AUC 不高，也说明公开评论数据的预测信号有限。",
        "特征重要性显示 is_negative_1, is_negative_0, weighted_vote_score, author_playtime_forever, review_length 等变量对流失预测贡献较大，说明模型结果与业务逻辑基本一致。": "特征重要性显示 playtime_at_review_hours、weighted_vote_score、author_num_games_owned、votes_funny、author_playtime_at_review 等变量贡献较大。由于已排除 churn_signal 及其直接来源字段，新的特征重要性不再依赖标签公式，模型解释更符合去泄露后的实验要求。",
        "排名靠前的变量包括 is_negative_1、is_negative_0、weighted_vote_score、author_playtime_forever、review_length，说明差评信号、互动反馈、游戏时长和评论长度等因素对流失判断贡献较大。": "排名靠前的变量包括 playtime_at_review_hours、weighted_vote_score、author_num_games_owned、votes_funny、author_playtime_at_review，说明评论时累计使用情况、互动反馈、玩家账号行为和评论互动热度仍然能为流失识别提供一定信息。需要说明的是，is_negative、playtime_hours、review_length 等直接参与标签生成的字段已从模型特征中排除，以避免标签泄露。",
        "GradientBoosting 的综合表现最好，F1=0.6433，AUC=0.6678。": "DecisionTree 在去泄露后的测试集上 F1 排名最高，F1=0.6254，AUC=0.5334；从交叉验证看，整体 F1=0.5045±0.0716，说明模型具备基础预警能力，但仍有提升空间。",
    }
    for old, new in replacements.items():
        replace_text(doc, old, new)

    p_design = find_paragraph(doc, "2、系统总体设计")
    insert_picture_after(p_design, framework_img, width=Inches(6.0), caption="系统框架结构图")
    add_paragraphs_after(
        p_design,
        [
            "按照模板要求，系统总体设计可以概括为五层结构：数据采集层负责获取 Steam 公开评论数据并做缓存；数据处理层负责缺失值、异常值和字段类型处理；分析挖掘层负责 NLP、可视化、标准流程分析和客户聚类；模型预测层负责多模型训练、评价和解释；交互展示层通过 Streamlit 展示业务看板和单客预测结果。",
            "该框架既覆盖课程要求的数据读取、数据预处理、数据可视化和业务建模，也补充了对比分析、分组分析、交叉分析、回归分析、时间序列和关联规则分析，使项目从“模型训练”扩展为完整的数据分析闭环。",
        ],
    )

    p_env = find_paragraph(doc, "1、系统开发环境")
    add_paragraphs_after(
        p_env,
        [
            "项目启动步骤如下：第一步，在项目根目录执行 python run_project.py，系统会依次完成数据采集、数据清洗、NLP 情感分析、可视化输出、客户聚类、多模型训练、交叉验证、混淆矩阵、学习曲线和模型解释图生成；第二步，执行 streamlit run streamlit_app.py 启动交互式看板；第三步，在浏览器中访问本地地址，展示业务概览、NLP 情感挖掘、聚类分群、模型评估、输出图表和单客预测。",
            "是否需要在报告中添加项目启动截图：建议添加 1 张即可，放在系统功能测试部分，截图内容应包含命令行运行完成信息或 Streamlit 本地访问地址。模板更强调“结果截图”，因此不建议放太多启动过程截图，避免挤占分析结果篇幅。",
        ],
    )

    p_test = find_paragraph(doc, "四、系统功能测试")
    add_paragraphs_after(
        p_test,
        [
            "按照模板要求，系统功能测试部分应重点展示运行结果截图，并验证结果是否符合预期。本项目建议保留并补充以下截图：预处理前后数据对比、流失总体分布图、不同游戏时长层级流失率图、产品流失率图、参与度散点图、NLP 情感分布图、模型评价指标表、特征重要性图、客户聚类图、混淆矩阵、学习曲线和 Streamlit 单客预测页面。",
            "启动过程截图可以作为辅助材料，但不应替代结果截图。更推荐在录屏中展示启动过程，在 Word 报告中展示“运行完成”和“结果页面”即可。",
        ],
    )

    p_mining = find_paragraph(doc, "3、数据挖掘功能测试")
    add_paragraphs_after(
        p_mining,
        [
            "标签泄露修复测试：在本次完善过程中，检查 build_model_features 后发现 churn_signal 已被排除，但 churn_label 的生成公式直接使用了 is_negative、playtime_hours、review_length、votes_up、comment_count 等字段。为避免模型学习标签公式，项目进一步新增 LABEL_LEAKAGE_COLUMNS，将 churn_signal 及其直接来源字段从训练特征中统一排除，并通过单元测试确认泄露字段不会直接或以 One-Hot 形式进入模型。重新训练后，feature_importance.csv 中泄露字段检查结果为空，说明修复生效。",
            "去泄露后模型结果虽然低于原结果，但更符合真实建模要求。该测试说明项目不仅能运行，还对模型评价的可信度进行了检查和修正，能够更好地回应课程答辩中关于模型合理性和业务真实性的问题。",
        ],
    )

    p_summary = find_paragraph(doc, "五、课程总结")
    add_paragraphs_after(
        p_summary,
        [
            "本次完善后，报告内容与模板要求的对应关系更加完整：功能与要求部分说明系统实现目标和成员分工；系统方案设计部分补充系统框架结构图和分层设计思路；系统功能实现部分覆盖数据探索、预处理、可视化和数据挖掘模块；系统功能测试部分结合截图和文字验证各模块运行结果；课程总结部分则对理论收获、实践技能、不足和改进方向进行归纳。",
        ],
    )

    # Replace the stale model metrics table with the latest metrics.
    latest_rows = [
        ["DecisionTree", "0.492", "0.4907", "0.8618", "0.6254", "0.5334"],
        ["LightGBM", "0.532", "0.5246", "0.5203", "0.5224", "0.5302"],
        ["LogisticRegression", "0.514", "0.5059", "0.5244", "0.5150", "0.5264"],
        ["GradientBoosting", "0.522", "0.5143", "0.5122", "0.5132", "0.5357"],
        ["XGBoost", "0.520", "0.5122", "0.5122", "0.5122", "0.5126"],
        ["RandomForest", "0.532", "0.5261", "0.4919", "0.5084", "0.5538"],
        ["StackingEnsemble", "0.524", "0.5196", "0.4309", "0.4711", "0.5339"],
    ]
    for table in doc.tables:
        if table.rows and table.rows[0].cells[0].text.strip() == "模型":
            headers = ["模型", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]
            for idx, value in enumerate(headers):
                table.rows[0].cells[idx].text = value
            # Remove all rows except header.
            while len(table.rows) > 1:
                table._tbl.remove(table.rows[-1]._tr)
            for row_data in latest_rows:
                row = table.add_row()
                for idx, value in enumerate(row_data):
                    row.cells[idx].text = value
            break

    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_DOC)
    print(OUT_DOC)


if __name__ == "__main__":
    build_doc()
