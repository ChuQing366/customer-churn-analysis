from __future__ import annotations

import shutil
import sys
from pathlib import Path

from docx import Document
from docx.shared import Inches


REPLACEMENTS = {
    "该图展示流失客户与留存客户占比。当前样本整体流失率约为 49.30%，说明数据中流失与留存样本较为接近，适合进行二分类建模。":
        "该图展示流失客户与留存客户占比。当前样本整体流失率约为 49.30%，流失与留存样本较为接近，适合进行二分类建模；同时也说明后续评价不能只看准确率，还需要结合 Recall、F1 和 AUC 判断模型是否真正具备预警价值。",
    "该图比较不同产品下客户流失率差异，可帮助运营人员定位流失率较高的产品。":
        "该图比较不同产品下客户流失率差异，可帮助运营人员定位流失率较高的产品。结合当前分组结果，Rainbow Six Siege、The Witcher 3、Apex Legends 等产品的流失率相对更高，后续可优先复盘这些产品的评论内容和用户体验问题。",
    "该图展示评论情感倾向。当前中性评论占 44.60%，负面评论占 31.15%，正面评论占 24.25%。":
        "该图展示评论情感倾向。当前中性评论占 44.60%，负面评论占 31.15%，正面评论占 24.25%。从流失率看，负面评论用户流失风险高于正面评论用户，说明情感倾向可以作为识别高风险客户的重要辅助信号。",
    "模型解释性结果用于说明影响流失预测的关键因素。项目已排除 churn_signal 及其直接来源字段，避免标签泄露。":
        "模型解释性结果用于说明影响流失预测的关键因素。项目已排除 churn_signal 及其直接来源字段，避免标签泄露。当前模型主要关注评论时使用时长、加权投票分数、拥有游戏数、趣味投票数等行为特征，这些因素可为后续用户分层和挽留策略提供依据。"
}


def replace_last_inline_shape(doc: Document, image_path: Path) -> None:
    if not doc.inline_shapes:
        raise RuntimeError("document has no inline images")
    shape = doc.inline_shapes[-1]
    rid = shape._inline.graphic.graphicData.pic.blipFill.blip.embed
    image_part = doc.part.related_parts[rid]
    image_part._blob = image_path.read_bytes()
    shape.width = Inches(5.4)
    shape.height = Inches(3.05)


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: update_report_content.py <input.docx> <new_image.png> <output.docx>")

    input_path = Path(sys.argv[1])
    image_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    shutil.copy2(input_path, output_path)
    doc = Document(output_path)
    for para in doc.paragraphs:
        text = para.text.strip()
        if text in REPLACEMENTS:
            para.text = REPLACEMENTS[text]

    replace_last_inline_shape(doc, image_path)
    doc.save(output_path)
    print(output_path)


if __name__ == "__main__":
    main()
