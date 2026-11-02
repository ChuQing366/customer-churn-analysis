from copy import deepcopy
from pathlib import Path

from docx import Document


TEMPLATE = Path(r"C:\Users\Liu Jiawang\Desktop\第二学期-作业\数分\《大数据分析与应用》综合项目模板.docx")
REPORT = Path.cwd() / "reports" / "第五组-企业客户流失与预警分析系统-保留模板结构版.docx"
OUT = Path.cwd() / "reports" / "第五组-企业客户流失与预警分析系统-模板首页原样版.docx"


def first_body_paragraph_index(doc: Document) -> int:
    for idx, paragraph in enumerate(doc.paragraphs):
        if paragraph.text.strip() == "《大数据分析与应用》课程":
            return idx
    raise ValueError("Cannot find second-page start paragraph")


def replace_cover():
    template = Document(TEMPLATE)
    report = Document(REPORT)

    template_start = first_body_paragraph_index(template)
    report_start = first_body_paragraph_index(report)

    template_body = template._body._element
    report_body = report._body._element

    template_cover_elements = [deepcopy(p._p) for p in template.paragraphs[:template_start]]
    report_cover_elements = [p._p for p in report.paragraphs[:report_start]]

    insert_before = report.paragraphs[report_start]._p
    for old in report_cover_elements:
        report_body.remove(old)
    for element in template_cover_elements:
        report_body.insert(report_body.index(insert_before), element)

    report.save(OUT)
    print(OUT)


if __name__ == "__main__":
    replace_cover()
