from pathlib import Path
import textwrap

import cv2
from PIL import Image, ImageDraw, ImageFont


ROOT = Path.cwd()
SCREEN = ROOT / "reports" / "screenshots"
OUT_DIR = ROOT / "reports" / "demo_recording"
OUT_DIR.mkdir(parents=True, exist_ok=True)
VIDEO = OUT_DIR / "第五组-企业客户流失预警与挽留分析系统-演示录屏.mp4"
SCRIPT = OUT_DIR / "第五组-企业客户流失预警与挽留分析系统-演讲稿.md"

W, H = 1280, 720
FPS = 24
FONT_PATHS = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]
FONT_PATH = next((p for p in FONT_PATHS if Path(p).exists()), None)


def font(size):
    return ImageFont.truetype(FONT_PATH, size) if FONT_PATH else ImageFont.load_default()


TITLE_FONT = font(42)
SUBTITLE_FONT = font(26)
BODY_FONT = font(24)
SMALL_FONT = font(19)
CODE_FONT = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 22) if Path(r"C:\Windows\Fonts\consola.ttf").exists() else SMALL_FONT


def wrap_text(draw, text, fnt, width):
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for char in paragraph:
            test = current + char
            if draw.textbbox((0, 0), test, font=fnt)[2] <= width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = char
        if current:
            lines.append(current)
    return lines


def draw_text_block(draw, text, xy, fnt, fill="#1f2937", width=1100, line_gap=8):
    x, y = xy
    for line in wrap_text(draw, text, fnt, width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def base_slide(title, subtitle=None):
    img = Image.new("RGB", (W, H), "#f7fafc")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 80), fill="#1f4e79")
    draw.text((44, 22), "企业客户流失预警与挽留分析系统", font=SUBTITLE_FONT, fill="white")
    draw.text((60, 118), title, font=TITLE_FONT, fill="#0f172a")
    if subtitle:
        draw_text_block(draw, subtitle, (64, 176), BODY_FONT, "#334155", width=1080)
    return img


def paste_image_slide(title, image_path, note=None):
    img = base_slide(title)
    draw = ImageDraw.Draw(img)
    if image_path.exists():
        src = Image.open(image_path).convert("RGB")
        src.thumbnail((1120, 455), Image.LANCZOS)
        x = (W - src.width) // 2
        y = 170
        draw.rectangle((x - 8, y - 8, x + src.width + 8, y + src.height + 8), fill="white", outline="#cbd5e1", width=2)
        img.paste(src, (x, y))
        bottom = y + src.height + 26
    else:
        bottom = 180
        draw.text((80, bottom), f"缺少图片：{image_path.name}", font=BODY_FONT, fill="#b91c1c")
        bottom += 40
    if note:
        draw_text_block(draw, note, (70, max(bottom, 610)), SMALL_FONT, "#334155", width=1120, line_gap=5)
    return img


def bullets_slide(title, bullets, footer=None):
    img = base_slide(title)
    draw = ImageDraw.Draw(img)
    y = 185
    for bullet in bullets:
        draw.ellipse((70, y + 9, 82, y + 21), fill="#1f4e79")
        y = draw_text_block(draw, bullet, (100, y), BODY_FONT, "#1f2937", width=1060, line_gap=8) + 16
    if footer:
        draw.rectangle((60, 620, 1220, 675), fill="#eaf2f8", outline="#bfdbfe")
        draw_text_block(draw, footer, (82, 636), SMALL_FONT, "#1e3a8a", width=1100, line_gap=5)
    return img


def code_slide(title, code, note=None):
    img = base_slide(title)
    draw = ImageDraw.Draw(img)
    draw.rectangle((70, 170, 1210, 470), fill="#0f172a", outline="#334155")
    y = 195
    for line in code.strip().splitlines():
        draw.text((98, y), line, font=CODE_FONT, fill="#e5e7eb")
        y += 34
    if note:
        draw_text_block(draw, note, (76, 510), BODY_FONT, "#334155", width=1100)
    return img


slides = [
    (
        15,
        bullets_slide(
            "演示目标",
            [
                "本项目是课程级客户流失预警原型系统。",
                "演示从项目目录、运行入口、数据结果、模型评价到单客预测的完整流程。",
                "训练过程不现场长时间等待，直接展示已生成的 outputs 结果。",
            ],
            "建议录屏讲解总时长控制在 8-9 分钟，满足 10 分钟以内要求。",
        ),
    ),
    (
        28,
        bullets_slide(
            "项目目录说明",
            [
                "data：原始数据和清洗后的客户行为数据。",
                "src：核心源码，包括采集、预处理、NLP、可视化、建模和流程编排。",
                "outputs：运行后生成的模型、指标、图表和分析结果。",
                "reports：项目报告和截图材料。",
                "run_project.py：一键运行完整分析流程。",
                "streamlit_app.py：启动交互式演示看板。",
            ],
        ),
    ),
    (
        25,
        code_slide(
            "运行入口",
            """
cd E:\\Pycharm\\数分项目设计\\customer-churn-analysis\\customer-churn-analysis
python run_project.py
streamlit run streamlit_app.py
            """,
            "python run_project.py 会完成采集、清洗、NLP、聚类、模型训练和图表输出。正式录屏不建议等待完整重训，可直接展示已经生成的 outputs。",
        ),
    ),
    (
        35,
        paste_image_slide(
            "Streamlit 业务概览",
            SCREEN / "01_streamlit_business_overview.png",
            "这里重点讲样本量 2000、流失率约 49.3%、产品筛选和分析管线状态。这个页面证明项目已经可以作为交互式看板展示。",
        ),
    ),
    (
        32,
        paste_image_slide(
            "客户流失总体分布",
            SCREEN / "02_churn_distribution.png",
            "流失率接近一半，说明数据中流失与留存样本较均衡，适合做二分类预警演示。",
        ),
    ),
    (
        35,
        paste_image_slide(
            "使用时长与流失风险",
            SCREEN / "03_playtime_churn_rate.png",
            "从业务上看，使用时长越短、参与度越低的客户越容易流失，运营上应优先关注低活跃用户。",
        ),
    ),
    (
        32,
        paste_image_slide(
            "不同产品流失率",
            SCREEN / "04_product_churn_rate.png",
            "不同产品的流失率存在差异，可用于定位产品体验、内容或用户群体上的问题。",
        ),
    ),
    (
        32,
        paste_image_slide(
            "参与度与流失关系",
            SCREEN / "05_engagement_scatter.png",
            "散点图用于观察使用时长、参与度和流失状态之间的关系，帮助识别低活跃高风险客户。",
        ),
    ),
    (
        35,
        paste_image_slide(
            "NLP 文本情感分析",
            SCREEN / "06_nlp_sentiment_distribution.png",
            "NLP 把评论文本转成情感标签。负面评论比例较高时，说明需要重点关注用户体验和客服响应。",
        ),
    ),
    (
        35,
        paste_image_slide(
            "K-Means 客户聚类",
            SCREEN / "07_cluster_analysis.png",
            "聚类把客户分成不同群体，用于区分高活跃客户、低活跃客户和潜在流失客户，支持差异化挽留策略。",
        ),
    ),
    (
        40,
        bullets_slide(
            "模型评估口径",
            [
                "当前去除标签泄露后，DecisionTree 的测试集 F1=0.6254，Recall=0.8618，AUC=0.5334。",
                "流失预警不能只看 Accuracy，更要看 F1、Recall 和 AUC。",
                "Recall 高表示更容易识别潜在流失客户，适合预警场景。",
                "AUC 不高说明公开评论数据预测信号有限，后续需要真实 CRM 数据。",
            ],
            "主动说明标签泄露修复：宁可指标下降，也要让结果更真实。",
        ),
    ),
    (
        30,
        paste_image_slide(
            "混淆矩阵",
            SCREEN / "08_confusion_matrix.png",
            "混淆矩阵展示模型对流失客户和留存客户的识别情况，适合说明模型预测结果是否符合预警目标。",
        ),
    ),
    (
        30,
        paste_image_slide(
            "学习曲线",
            SCREEN / "09_learning_curve.png",
            "学习曲线用于说明模型稳定性。当前模型有基础预警能力，但仍受数据质量和特征质量限制。",
        ),
    ),
    (
        30,
        paste_image_slide(
            "模型解释性分析",
            SCREEN / "10_feature_importance_or_shap.png",
            "SHAP 或特征重要性图用于解释模型判断依据，避免模型完全变成黑盒。",
        ),
    ),
    (
        35,
        bullets_slide(
            "单客预测演示说法",
            [
                "输入低使用时长、负面评论、低参与度客户，系统会输出较高流失风险和挽留建议。",
                "再输入高使用时长、正面反馈客户，风险会下降。",
                "这个模块模拟运营人员对单个客户做快速风险判断。",
            ],
            "如果录屏时不现场输入，也可以口头说明这个页面的业务作用。",
        ),
    ),
    (
        28,
        bullets_slide(
            "结尾总结",
            [
                "系统完成了数据采集、预处理、NLP、可视化、聚类、建模、解释和看板展示。",
                "当前是课程演示原型，适合验证完整分析流程。",
                "未来可接入登录频率、消费记录、客服工单和真实流失时间，提升业务落地能力。",
            ],
        ),
    ),
]


def write_video():
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(VIDEO), fourcc, FPS, (W, H))
    for seconds, slide in slides:
        frame = cv2.cvtColor(__import__("numpy").array(slide), cv2.COLOR_RGB2BGR)
        for _ in range(int(seconds * FPS)):
            writer.write(frame)
    writer.release()


script_text = """# 企业客户流失预警与挽留分析系统演示稿

总时长建议控制在 8 到 9 分钟。

## 1. 开场
大家好，我们第五组的项目是《企业客户流失预警与挽留分析系统》。这个项目的目标不是单纯训练一个模型，而是完整展示从数据采集、数据预处理、分析挖掘、模型评价到交互式展示的客户流失预警流程。

## 2. 项目目录
首先看项目目录。data 目录存放原始数据和清洗后的数据；src 是核心源码目录，包含数据采集、预处理、NLP、可视化、模型训练和流程编排；outputs 是运行后生成的模型、指标和图表结果；reports 放项目报告和截图；run_project.py 是一键运行入口；streamlit_app.py 是交互式看板入口。

## 3. 运行方式
项目运行时先在根目录执行 python run_project.py，它会自动完成数据采集、清洗、NLP 情感分析、聚类分群、多模型训练和图表输出。因为完整训练需要一定时间，正式演示时不等待全部重训，而是展示已经生成好的 outputs 结果。然后执行 streamlit run streamlit_app.py 打开网页看板。

## 4. 业务概览
Streamlit 首页展示当前样本量、流失率、产品数量和分析管线状态。当前清洗后样本量是 2000 条，整体流失率约 49.3%。这个页面主要模拟企业运营人员的看板入口，可以通过筛选产品和使用时长观察不同客户群体的风险变化。

## 5. 可视化分析
流失分布图展示留存客户和流失客户的总体比例。使用时长流失率图说明低使用时长客户更容易流失。不同产品流失率图可以帮助定位哪些产品用户流失问题更明显。参与度散点图则从使用时长和互动程度两个角度观察客户状态。

## 6. NLP 情感分析
NLP 模块把评论文本转换成正面、中性和负面情感标签。当前中性评论占比最高，负面评论也占一定比例。业务上，负面评论客户往往需要优先客服跟进，因为他们可能代表产品体验、服务体验或社区环境方面的问题。

## 7. 客户聚类
聚类模块使用 K-Means 对客户进行分群。分类模型回答“客户会不会流失”，聚类回答“客户属于哪一类”。通过聚类结果，可以把客户分成不同画像，例如高活跃客户、低活跃客户和潜在流失客户，从而制定差异化挽留策略。

## 8. 模型评估
模型评估部分比较多个模型的 Accuracy、Precision、Recall、F1 和 AUC。我们重点看 F1、Recall 和 AUC，而不是只看准确率。去除标签泄露后，DecisionTree 的 F1 为 0.6254，Recall 为 0.8618。Recall 较高说明它更容易识别潜在流失客户，适合预警场景。AUC 不高也说明公开评论数据的预测信号有限，后续需要接入真实企业数据。

## 9. 稳定性和解释性
混淆矩阵用于观察预测对错情况，学习曲线用于判断模型稳定性，SHAP 或特征重要性图用于解释模型判断依据。我们还修复了标签泄露问题，排除了 churn_signal 及其直接来源字段，避免模型只是学习标签公式。这样指标虽然下降，但结果更加真实。

## 10. 单客预测和结尾
单客预测页面可以输入某个客户的使用时长、评论倾向和互动情况，输出流失概率和挽留建议。比如低时长、负面评价、低参与度客户会被判断为较高风险；高时长、正面反馈客户风险会下降。

总结来说，本项目完成了客户流失预警的完整数据分析闭环，适合作为课程演示原型。未来如果接入真实企业的登录频率、消费记录、客服工单和真实流失时间，模型预测和业务落地效果会更好。
"""


if __name__ == "__main__":
    write_video()
    SCRIPT.write_text(script_text, encoding="utf-8")
    print(VIDEO)
    print(SCRIPT)
