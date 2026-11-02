from __future__ import annotations

from pathlib import Path

from docx import Document


DOCX = Path(r"C:\Users\Liu Jiawang\Desktop\第二学期-作业\数分\第五组\交付\第五组-企业客户流失与预警分析系统-最终打印版-修订完善.docx")
TARGET = "本项目的测试通过条件包括：原始数据能够被程序读取，清洗后数据字段完整且可用于后续分析；可视化图片能够正常生成并反映对应指标；模型训练能够输出评价指标和模型文件；Streamlit 页面能够加载数据、图表和模型结果；单客预测功能能够根据输入特征返回风险判断。上述条件覆盖了数据、算法和展示三个层面的功能验证。"


def delete_paragraph(paragraph) -> None:
    element = paragraph._element
    element.getparent().remove(element)
    paragraph._p = paragraph._element = None


def main() -> None:
    doc = Document(str(DOCX))
    seen = False
    for paragraph in list(doc.paragraphs):
        if paragraph.text.strip() == TARGET:
            if seen:
                delete_paragraph(paragraph)
            seen = True
    doc.save(str(DOCX))
    print(DOCX)


if __name__ == "__main__":
    main()
