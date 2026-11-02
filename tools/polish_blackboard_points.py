from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt


DOCX = Path(r"C:\Users\Liu Jiawang\Desktop\第二学期-作业\数分\第五组\交付\第五组-企业客户流失与预警分析系统-最终打印版-修订.docx")
OUT = DOCX.with_name("第五组-企业客户流失与预警分析系统-最终打印版-修订完善.docx")


def set_font(run, size=12):
    run.font.name = "宋体"
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(size)


def replace_text(paragraph, text: str) -> None:
    style = paragraph.style
    alignment = paragraph.alignment
    paragraph.clear()
    paragraph.style = style
    paragraph.alignment = alignment
    r = paragraph.add_run(text)
    set_font(r)


def find_contains(doc: Document, needle: str):
    for p in doc.paragraphs:
        if needle in p.text:
            return p
    raise ValueError(f"not found: {needle}")


def main() -> None:
    doc = Document(str(DOCX))
    p = find_contains(doc, "本系统面向互联网产品运营、游戏社区运营和企业客户关系管理场景")
    replace_text(
        p,
        "本系统面向互联网产品运营、游戏社区运营和企业客户关系管理场景，重点解决“用户可能流失但企业难以及时发现”的问题。数据源方面，本项目选取 Steam 公开评论数据作为企业客户行为数据的模拟来源，采集用户评论、游戏时长、评分倾向、获赞数、评论时间等字段；这些字段虽然来自公开游戏社区，但能够对应企业客户分析中的使用活跃度、满意度反馈、互动行为和时间变化等关键维度。通过数据挖掘方法，系统希望提前识别高风险客户，并输出影响因素和挽留建议。系统使用对象包括运营人员、客户经理、数据分析人员和课程项目评审人员，任务目标可以概括为：明确数据从哪里来、为什么要分析、分析要解决什么问题、每一步如何实现，以及最终得到什么结果和业务结论。与普通统计报表相比，本系统不仅展示已有数据，还尝试通过模型发现客户行为与流失风险之间的联系，使分析结果能够服务于后续运营决策。",
    )

    p = find_contains(doc, "系统按照七个业务模块组织整体方案")
    replace_text(
        p,
        "系统按照七个业务模块组织整体方案，并围绕“数据源—任务目标—处理过程—输出结果”的逻辑展开。数据采集模块负责获取 Steam 公开评论与行为数据，回答数据从哪里来的问题；数据预处理模块负责完成清洗、编码、异常处理和特征衍生，保证数据可以被后续分析使用；NLP 文本挖掘模块把评论内容转换为情感分数、关键词和词云结果，用于解释客户主观态度；数据可视化模块输出流失分布、产品差异、参与度关系和情感分布等分析图，用于发现业务规律；客户聚类模块使用 K-Means 和 PCA 形成客户分群画像，回答客户可以分成哪些类型；模型训练与评价模块完成分类预测、指标对比、混淆矩阵、学习曲线和特征重要性解释，回答单个客户是否存在流失风险；交互展示与预警模块通过 Streamlit 汇总结果并提供单客风险判断。总体流程为：Steam 数据输入 → 数据清洗与特征工程 → NLP 情感分析 → 可视化分析 → 客户聚类 → 分类模型训练与评价 → 看板展示和预警输出。",
    )

    p = find_contains(doc, "本部分对各模块功能代码实现结果进行测试")
    replace_text(
        p,
        "本部分对各模块功能代码实现结果进行测试，并验证功能运行结果与预期是否一致。测试截图依次展示预处理结果、可视化结果、NLP 文本挖掘结果、聚类结果、模型评价结果和交互式看板结果。测试重点不是单纯展示截图，而是围绕“每件事是否真正做成”进行核对：数据文件是否生成，清洗字段是否完整，图表是否正常展示，聚类结果是否能够解释客户群体差异，分类模型是否能够输出预测指标和风险判断，页面交互是否能够读取并展示最终结果。",
    )

    doc.save(str(OUT))
    print(OUT)


if __name__ == "__main__":
    main()
