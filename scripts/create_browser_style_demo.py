from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path.cwd()
SCREEN = ROOT / "reports" / "screenshots"
OUT = ROOT / "reports" / "demo_recording"
VIDEO = OUT / "browser_style_demo.mp4"
SCRIPT = OUT / "browser_style_speech_script.md"
W, H = 1440, 900
FPS = 24

OUT.mkdir(parents=True, exist_ok=True)


def pick_font(candidates, size):
    for item in candidates:
        path = Path(item)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


FONT_CJK = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]
FONT_MONO = [
    r"C:\Windows\Fonts\consola.ttf",
    r"C:\Windows\Fonts\CascadiaMono.ttf",
    r"C:\Windows\Fonts\msyh.ttc",
]

F_TITLE = pick_font(FONT_CJK, 32)
F_TAB = pick_font(FONT_CJK, 18)
F_BODY = pick_font(FONT_CJK, 21)
F_SMALL = pick_font(FONT_CJK, 16)
F_CODE = pick_font(FONT_MONO, 24)
F_BIG = pick_font(FONT_CJK, 42)


def text_width(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


def wrap_text(draw, text, fnt, max_width):
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for char in paragraph:
            test = current + char
            if text_width(draw, test, fnt) <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = char
        if current:
            lines.append(current)
    return lines


def draw_wrapped(draw, text, xy, fnt, fill="#1f2937", max_width=1180, line_gap=8):
    x, y = xy
    for line in wrap_text(draw, text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def browser_base(active="业务概览"):
    img = Image.new("RGB", (W, H), "#f3f6fb")
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, W, 46), fill="#e5e7eb")
    draw.ellipse((18, 15, 30, 27), fill="#ef4444")
    draw.ellipse((38, 15, 50, 27), fill="#f59e0b")
    draw.ellipse((58, 15, 70, 27), fill="#22c55e")
    draw.rounded_rectangle((110, 9, 1050, 36), radius=12, fill="white", outline="#cbd5e1")
    draw.text((130, 13), "http://localhost:8501  -  Streamlit", font=F_SMALL, fill="#475569")

    draw.rectangle((0, 46, W, 102), fill="#1f4e79")
    draw.text((44, 60), "企业客户流失预警与挽留分析系统", font=F_TITLE, fill="white")

    tabs = ["业务概览", "NLP 情感", "聚类分群", "模型评估", "稳定性", "单客预测", "输出图表"]
    x = 44
    for tab in tabs:
        width = text_width(draw, tab, F_TAB) + 30
        fill = "#dbeafe" if tab == active else "#ffffff"
        outline = "#60a5fa" if tab == active else "#cbd5e1"
        draw.rounded_rectangle((x, 114, x + width, 150), radius=15, fill=fill, outline=outline)
        draw.text((x + 15, 122), tab, font=F_TAB, fill="#0f172a")
        x += width + 12
    return img


def crop_to_content(src):
    chart = Image.open(src).convert("RGB")
    arr = np.array(chart)
    mask = np.any(arr < 245, axis=2)
    if not mask.any():
        return chart
    ys, xs = np.where(mask)
    pad = 34
    left = max(xs.min() - pad, 0)
    top = max(ys.min() - pad, 0)
    right = min(xs.max() + pad, chart.width)
    bottom = min(ys.max() + pad, chart.height)
    return chart.crop((left, top, right, bottom))


def add_caption(draw, text):
    draw.rounded_rectangle((70, 786, 1370, 858), radius=10, fill="#ffffff", outline="#cbd5e1")
    draw_wrapped(draw, text, (96, 808), F_BODY, max_width=1250, line_gap=6)


def chart_page(active, title, filename, caption):
    img = browser_base(active)
    draw = ImageDraw.Draw(img)
    draw.text((56, 172), title, font=F_TITLE, fill="#0f172a")

    src = SCREEN / filename
    if src.exists():
        chart = crop_to_content(src)
        chart.thumbnail((1240, 555), Image.LANCZOS)
        chart_x = (W - chart.width) // 2
        chart_y = 238 + max(0, (540 - chart.height) // 2)
        draw.rounded_rectangle(
            (chart_x - 12, chart_y - 12, chart_x + chart.width + 12, chart_y + chart.height + 12),
            radius=8,
            fill="white",
            outline="#cbd5e1",
            width=2,
        )
        img.paste(chart, (chart_x, chart_y))
    else:
        draw.rounded_rectangle((96, 245, 1344, 720), radius=8, fill="white", outline="#cbd5e1")
        draw.text((140, 430), f"未找到截图：{filename}", font=F_BODY, fill="#b91c1c")
    add_caption(draw, caption)
    return img


def directory_page():
    img = browser_base("业务概览")
    draw = ImageDraw.Draw(img)
    draw.text((56, 172), "项目目录说明", font=F_TITLE, fill="#0f172a")
    rows = [
        ("data", "原始数据和清洗后的数据，是整个分析的数据来源。"),
        ("src", "核心源代码，包括采集、预处理、NLP、聚类、建模、可视化和流程编排。"),
        ("outputs", "程序运行后生成的模型、指标、图表、NLP 和聚类分析结果。"),
        ("reports", "项目报告、演示截图、录屏材料和讲稿。"),
        ("run_project.py", "一键运行入口，用来串联完整分析流程。"),
        ("streamlit_app.py", "浏览器交互式看板入口，用来做课程演示。"),
    ]
    y = 232
    for name, desc in rows:
        draw.rounded_rectangle((70, y, 1320, y + 64), radius=8, fill="white", outline="#cbd5e1")
        draw.text((98, y + 17), name, font=F_TAB, fill="#1f4e79")
        draw.text((355, y + 17), desc, font=F_BODY, fill="#1f2937")
        y += 76
    add_caption(draw, "开头先说明项目结构，让老师知道这个系统不是单张图表，而是从数据、代码、输出到网页看板的完整项目。")
    return img


def command_page():
    img = browser_base("业务概览")
    draw = ImageDraw.Draw(img)
    draw.text((56, 172), "程序运行入口", font=F_TITLE, fill="#0f172a")
    draw.rounded_rectangle((70, 238, 1320, 468), radius=10, fill="#0f172a", outline="#334155")
    commands = [
        "cd <project_root>",
        "python run_project.py",
        "streamlit run streamlit_app.py",
    ]
    y = 275
    for line in commands:
        draw.text((106, y), line, font=F_CODE, fill="#e5e7eb")
        y += 52
    draw_wrapped(
        draw,
        "说明：完整训练会比较耗时，录屏时只展示命令入口和已经生成的 outputs 结果，不现场等待重训。这样演示节奏更稳，也不会影响 10 分钟时间控制。",
        (78, 520),
        F_BODY,
        max_width=1180,
    )
    return img


def overview_page():
    img = browser_base("业务概览")
    draw = ImageDraw.Draw(img)
    draw.text((56, 172), "Streamlit 业务概览页", font=F_TITLE, fill="#0f172a")
    src = SCREEN / "01_streamlit_business_overview.png"
    if src.exists():
        page = Image.open(src).convert("RGB")
        page.thumbnail((1280, 600), Image.LANCZOS)
        img.paste(page, ((W - page.width) // 2, 230))
    else:
        draw_wrapped(draw, "样本量 2000，整体流失率约 49.3%，产品数 10。", (90, 250), F_BIG)
    add_caption(draw, "首页主要讲业务对象：我们面对的是客户流失预警问题，系统先给运营人员提供样本量、流失率和产品维度的总体判断。")
    return img


def model_page():
    img = browser_base("模型评估")
    draw = ImageDraw.Draw(img)
    draw.text((56, 172), "模型评估对比", font=F_TITLE, fill="#0f172a")
    headers = ["模型", "Accuracy", "Precision", "Recall", "F1", "AUC"]
    rows = [
        ["DecisionTree", "0.492", "0.4907", "0.8618", "0.6254", "0.5334"],
        ["LightGBM", "0.532", "0.5246", "0.5203", "0.5224", "0.5302"],
        ["LogisticRegression", "0.514", "0.5059", "0.5244", "0.5150", "0.5264"],
        ["GradientBoosting", "0.522", "0.5143", "0.5122", "0.5132", "0.5357"],
        ["XGBoost", "0.520", "0.5122", "0.5122", "0.5122", "0.5126"],
        ["RandomForest", "0.532", "0.5261", "0.4919", "0.5084", "0.5538"],
        ["StackingEnsemble", "0.524", "0.5196", "0.4309", "0.4711", "0.5339"],
    ]
    x0, y0 = 96, 250
    colw = [270, 160, 175, 155, 140, 140]
    x = x0
    for header, width in zip(headers, colw):
        draw.rectangle((x, y0, x + width, y0 + 50), fill="#dbeafe", outline="#94a3b8")
        draw.text((x + 14, y0 + 14), header, font=F_TAB, fill="#0f172a")
        x += width
    y = y0 + 50
    for row in rows:
        x = x0
        for value, width in zip(row, colw):
            draw.rectangle((x, y, x + width, y + 48), fill="white", outline="#cbd5e1")
            draw.text((x + 14, y + 14), value, font=F_SMALL, fill="#1f2937")
            x += width
        y += 48
    add_caption(draw, "模型评估不要只讲 Accuracy。流失预警更关心 F1、Recall 和 AUC。修复 churn_signal 标签泄露后，指标更真实，说明瓶颈主要在特征质量。")
    return img


def single_customer_page():
    img = browser_base("单客预测")
    draw = ImageDraw.Draw(img)
    draw.text((56, 172), "单客流失预测", font=F_TITLE, fill="#0f172a")
    fields = [
        ("使用时长", "1.5 小时"),
        ("评论倾向", "负面评价"),
        ("参与度", "低"),
        ("互动反馈", "点赞少 / 评论少"),
    ]
    y = 250
    for label, value in fields:
        draw.rounded_rectangle((96, y, 610, y + 62), radius=8, fill="white", outline="#cbd5e1")
        draw.text((122, y + 18), label, font=F_TAB, fill="#475569")
        draw.text((330, y + 18), value, font=F_TAB, fill="#0f172a")
        y += 82
    draw.rounded_rectangle((760, 250, 1280, 520), radius=14, fill="#fee2e2", outline="#ef4444", width=3)
    draw.text((804, 296), "预测结果", font=F_TITLE, fill="#991b1b")
    draw.text((804, 370), "高风险客户", font=F_BIG, fill="#b91c1c")
    draw_wrapped(draw, "建议：客服优先跟进，提供补偿、专属活动或使用指导。", (804, 452), F_BODY, fill="#7f1d1d", max_width=420)
    add_caption(draw, "最后展示单个客户预测，体现系统可以把模型结果转成运营动作，而不是只停留在算法指标。")
    return img


PAGES = [
    (22, directory_page()),
    (24, command_page()),
    (32, overview_page()),
    (30, chart_page("业务概览", "客户流失总体分布", "02_churn_distribution.png", "整体流失率约 49.3%，流失与留存样本比较接近，适合做二分类预警演示。")),
    (30, chart_page("业务概览", "不同使用时长层级流失率", "03_playtime_churn_rate.png", "低使用时长客户更容易流失，运营上应优先关注低活跃客户。")),
    (28, chart_page("业务概览", "不同产品流失率", "04_product_churn_rate.png", "不同产品的流失率存在差异，可用于定位产品体验或客户群体差异。")),
    (28, chart_page("业务概览", "使用时长与参与度关系", "05_engagement_scatter.png", "低时长、低参与度区域更容易出现高风险客户。")),
    (32, chart_page("NLP 情感", "NLP 评论情感分布", "06_nlp_sentiment_distribution.png", "评论文本被转换为正面、中性、负面情感。负面反馈可以作为客服和产品优化线索。")),
    (32, chart_page("聚类分群", "K-Means 客户聚类", "07_cluster_analysis.png", "聚类用来识别不同客户画像，支持差异化挽留策略。")),
    (38, model_page()),
    (28, chart_page("稳定性", "混淆矩阵", "08_confusion_matrix.png", "混淆矩阵用于查看模型对流失客户和留存客户的识别情况。")),
    (28, chart_page("稳定性", "学习曲线", "09_learning_curve.png", "学习曲线用于判断模型稳定性，当前模型具备基础预警能力，但仍有提升空间。")),
    (28, chart_page("模型评估", "模型解释性分析", "10_feature_importance_or_shap.png", "SHAP 或特征重要性用于说明模型不是黑盒，能解释哪些因素影响流失判断。")),
    (32, single_customer_page()),
]


SCRIPT_TEXT = """# 浏览器式演示录屏讲稿

这版视频按浏览器里的 Streamlit 看板展示，不按 PPT 翻页展示。

1. 先展示项目目录：data 是数据目录，src 是核心代码，outputs 是模型、指标和图表输出，reports 是报告和演示材料，run_project.py 是完整流程入口，streamlit_app.py 是网页看板入口。
2. 程序运行入口：python run_project.py 会完成采集、清洗、NLP、聚类、模型训练和图表输出；streamlit run streamlit_app.py 用于启动浏览器看板。完整训练比较耗时，录屏里展示已经生成的 outputs 结果。
3. 进入业务概览：本项目围绕企业客户流失预警，样本量 2000，整体流失率约 49.3%，目标是帮助运营提前发现高风险客户。
4. 流失总体分布：流失与留存比例接近，说明这是一个适合做二分类预警的场景。
5. 使用时长流失率：低使用时长客户更容易流失，所以运营上要重点关注低活跃用户。
6. 产品流失率：不同产品的流失率不同，说明流失不仅是客户个人问题，也可能和产品体验有关。
7. 使用时长与参与度：低时长、低参与度区域更容易出现高风险客户，这类客户需要更早触达。
8. NLP 情感分析：把评论文本转换成正面、中性、负面情感，负面评论可作为客服和产品优化线索。
9. 聚类分群：K-Means 把客户分成不同画像，不同群体可以采用不同挽留策略，例如低活跃群体做使用引导，高价值风险群体做专属优惠。
10. 模型评估：重点看 F1、Recall、AUC，不只看 Accuracy。修复 churn_signal 标签泄露后，指标更真实。DecisionTree 的 Recall 较高，适合预警场景，但也说明特征质量仍有提升空间。
11. 混淆矩阵和学习曲线：混淆矩阵展示识别对错情况，学习曲线展示模型稳定性，说明模型能做基础预警，但不是完美模型。
12. 模型解释性：SHAP 或特征重要性说明模型不是黑盒，可以解释哪些因素影响流失判断。
13. 单客预测：输入低时长、负面评价、低参与度客户，系统输出高风险和挽留建议，体现模型结果能转成运营动作。
14. 结尾总结：本项目完成了从数据处理、文本挖掘、客户分群、模型训练到网页预警看板的完整闭环。未来可接入真实登录频率、消费记录、客服工单和真实流失时间，让预警更准确。
"""


def write_video():
    writer = cv2.VideoWriter(str(VIDEO), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    for seconds, page in PAGES:
        frame = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
        for _ in range(seconds * FPS):
            writer.write(frame)
    writer.release()
    SCRIPT.write_text(SCRIPT_TEXT, encoding="utf-8-sig")
    print(VIDEO)
    print(SCRIPT)


if __name__ == "__main__":
    write_video()
