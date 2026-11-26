#!/usr/bin/env python3
"""Read-only OOXML inventory for a human/agent-led standard review.

Python standard library only. This enumerates document content; it neither
decides compliance nor accepts/rejects tracked changes. Every item starts
unreviewed. Locations refer to the source package, not the revised document.
"""

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile


W = {
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "http://purl.oclc.org/ooxml/wordprocessingml/main",
}
M = {
    "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "http://purl.oclc.org/ooxml/officeDocument/math",
}
STORIES = re.compile(r"word/(document|header\d+|footer\d+|footnotes|endnotes|comments)\.xml$")
REVISION_TAGS = {
    "ins", "del", "moveFrom", "moveTo", "moveFromRangeStart", "moveToRangeStart",
    "pPrChange", "rPrChange", "tblPrChange", "tblGridChange", "trPrChange", "tcPrChange",
    "sectPrChange", "numberingChange", "cellIns", "cellDel", "cellMerge",
    "customXmlInsRangeStart", "customXmlDelRangeStart", "customXmlMoveFromRangeStart", "customXmlMoveToRangeStart",
}
KINDS = {
    "p": "paragraph", "tbl": "table", "tc": "cell",
    "drawing": "graphic", "pict": "graphic", "object": "embedded_object",
    "sdt": "content_control", "txbxContent": "text_box", "altChunk": "external_content", "sym": "symbol",
}


class InventoryError(Exception):
    """A concise, user-actionable inventory error."""


def split_tag(tag):
    if tag.startswith("{"):
        namespace, local = tag[1:].split("}", 1)
        return namespace, local
    return "", tag


def word_tag(node, local=None):
    namespace, name = split_tag(node.tag)
    return namespace in W and (local is None or name == local)


def attr(node, local):
    for key, value in node.attrib.items():
        if split_tag(key)[1] == local:
            return value
    return None


def path_tag(tag):
    namespace, local = split_tag(tag)
    if namespace in W:
        return "w:" + local
    if namespace in M:
        return "m:" + local
    return "{" + namespace + "}" + local if namespace else local


def element_paths(root):
    paths = {root: "/" + path_tag(root.tag) + "[1]"}
    parents = {}
    for node in root.iter():
        counts = Counter()
        for child in node:
            counts[child.tag] += 1
            paths[child] = paths[node] + "/" + path_tag(child.tag) + f"[{counts[child.tag]}]"
            parents[child] = node
    return paths, parents


def text_of(node, skip_nested_paragraphs=False):
    pieces = []

    def walk(current):
        if current is not node and skip_nested_paragraphs and word_tag(current, "p"):
            return
        namespace, name = split_tag(current.tag)
        if (namespace in W and name in {"t", "delText"}) or (namespace in M and name == "t"):
            pieces.append(current.text or "")
        elif namespace in W and name == "tab":
            pieces.append("\t")
        elif namespace in W and name in {"br", "cr"}:
            pieces.append("\n")
        for child in current:
            walk(child)

    walk(node)
    return "".join(pieces)


def nearest(node, parents, local):
    node = parents.get(node)
    while node is not None:
        if word_tag(node, local):
            return node
        node = parents.get(node)
    return None


def revisions_for(node, parents):
    kinds = {split_tag(x.tag)[1] for x in node.iter() if word_tag(x) and split_tag(x.tag)[1] in REVISION_TAGS}
    ancestor = parents.get(node)
    while ancestor is not None:
        if word_tag(ancestor) and split_tag(ancestor.tag)[1] in REVISION_TAGS:
            kinds.add(split_tag(ancestor.tag)[1])
        ancestor = parents.get(ancestor)
    return sorted(kinds)


def numeric_tokens(text):
    # Preserve tokens for comparison; do not infer thresholds or units.
    return re.findall(r"[+−-]?\d+(?:[.,．]\d+)*(?:[%％])?", text)


def inventory(path):
    path = Path(path)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise InventoryError(f"Cannot read input: {exc.strerror}.") from exc
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise InventoryError("Input is not a readable DOCX/ZIP package.") from exc

    items, parts, warnings = [], [], []
    totals = Counter()
    body_text_present = False
    body_graphics = 0
    with archive:
        names = archive.namelist()
        if "word/document.xml" not in names:
            raise InventoryError("Package has no word/document.xml; convert the document to DOCX first.")
        if len(names) != len(set(names)):
            raise InventoryError("Package contains duplicate part names; repair a copy before inventorying it.")
        story_names = sorted((n for n in names if STORIES.fullmatch(n)), key=lambda n: (n != "word/document.xml", n))
        for part in story_names:
            try:
                root = ET.fromstring(archive.read(part))
            except (ET.ParseError, zipfile.BadZipFile, RuntimeError) as exc:
                raise InventoryError(f"Cannot parse XML part: {part}.") from exc
            if split_tag(root.tag)[0] not in W:
                raise InventoryError(f"Unsupported Word XML namespace in {part}.")
            paths, parents = element_paths(root)
            part_counts = Counter()
            for node in root.iter():
                namespace, local = split_tag(node.tag)
                if namespace == "http://schemas.openxmlformats.org/markup-compatibility/2006" and local == "AlternateContent":
                    totals["alternate_content_blocks"] += 1
                if namespace in W and local in REVISION_TAGS:
                    totals["revision_markers"] += 1
                kind = KINDS.get(local) if namespace in W else None
                if namespace in M and local == "oMath":
                    kind = "formula"
                if kind is None:
                    continue
                item = {"id": part + "#" + paths[node], "part": part, "kind": kind, "status": "未审查"}
                if kind in {"paragraph", "formula"}:
                    text = text_of(node, skip_nested_paragraphs=(kind == "paragraph"))
                    item.update(text=text, numeric_tokens=numeric_tokens(text))
                    if kind == "paragraph":
                        item["field_instructions"] = [x.text or "" for x in node.iter() if word_tag(x, "instrText")]
                        if part == "word/document.xml" and text.strip():
                            body_text_present = True
                if kind == "table":
                    rows = [x for x in node.iter() if word_tag(x, "tr") and nearest(x, parents, "tbl") is node]
                    item["row_cell_counts"] = [sum(1 for x in row.iter() if word_tag(x, "tc") and nearest(x, parents, "tr") is row) for row in rows]
                    item["row_count"] = len(rows)
                    item["grid_columns"] = sum(1 for x in node.iter() if word_tag(x, "gridCol") and nearest(x, parents, "tbl") is node)
                if kind == "cell":
                    cell_text = text_of(node)
                    item["text_empty"] = not bool(cell_text.strip())
                    item["contains_nested_table"] = any(word_tag(x, "tbl") for x in node.iter())
                    properties = next((x for x in node if word_tag(x, "tcPr")), None)
                    if properties is not None:
                        for prop in properties:
                            name = split_tag(prop.tag)[1]
                            if word_tag(prop) and name in {"gridSpan", "vMerge", "hMerge"}:
                                item[name] = attr(prop, "val") or "continue"
                if kind == "graphic":
                    item["xml_type"] = local
                    item["relationship_ids"] = sorted({value for x in node.iter() for key, value in x.attrib.items() if split_tag(key)[1] in {"embed", "link"} or (split_tag(x.tag)[1] == "imagedata" and split_tag(key)[1] == "id")})
                    item["descriptions"] = [value for x in node.iter() for key, value in x.attrib.items() if split_tag(key)[1] in {"descr", "title"} and value]
                    if part == "word/document.xml":
                        body_graphics += 1
                if kind == "content_control":
                    properties = next((x for x in node if word_tag(x, "sdtPr")), None)
                    if properties is not None:
                        item["labels"] = {split_tag(x.tag)[1]: attr(x, "val") for x in properties if word_tag(x) and split_tag(x.tag)[1] in {"alias", "tag"}}
                if kind == "symbol":
                    item.update(font=attr(node, "font"), character_code=attr(node, "char"))
                changes = revisions_for(node, parents)
                if changes:
                    item["revision_types"] = changes
                for container_kind in ("footnote", "endnote", "comment"):
                    container = nearest(node, parents, container_kind)
                    if container is not None:
                        item["annotation"] = {"type": container_kind, "id": attr(container, "id")}
                        break
                items.append(item)
                part_counts[kind] += 1
                totals[kind] += 1
            parts.append({"name": part, "item_counts": dict(sorted(part_counts.items()))})

        if totals["revision_markers"]:
            warnings.append({"code": "TRACKED_CHANGES", "message": "存在修订标记；清点保留插入和删除文本。审查时确认工作版本，不自动接受或拒绝原有修订。"})
        if not body_text_present:
            warnings.append({"code": "NO_BODY_TEXT", "message": "未提取到正文可读文本。图片稿需 OCR 并逐页核对，当前不能据此开展完整文字审查。"})
        if totals["graphic"] or totals["formula"] or totals["text_box"]:
            warnings.append({"code": "VISUAL_CONTENT", "message": "含图形、公式或文本框；请渲染核对布局、图中文字及对象内容。XML 清点不能证明视觉内容完整。"})
        if totals["symbol"]:
            warnings.append({"code": "FONT_SYMBOLS", "message": "存在按字体编码的符号；已记录字体及编码，请结合渲染识别其含义。"})
        if totals["alternate_content_blocks"]:
            warnings.append({"code": "ALTERNATE_CONTENT", "message": "XML 含兼容性分支；清点包含各分支，渲染时可能只显示其中一个。请按实际显示内容核对，勿把计数等同于页面对象数量。"})
        if totals["embedded_object"] or totals["external_content"]:
            warnings.append({"code": "NON_TEXT_CONTENT", "message": "含嵌入对象或外部内容块；请另行读取对象内容并补充覆盖记录。"})
        chart_parts = sorted(n for n in names if n.startswith("word/charts/") and n.endswith(".xml"))
        if chart_parts:
            warnings.append({"code": "CHART_CONTENT", "message": "图表内部的数据与标签需单独读取并与渲染结果核对。"})
        other_word_xml = sorted(n for n in names if n.startswith("word/") and n.endswith(".xml") and n not in story_names)
        media_parts = sorted(n for n in names if n.startswith("word/media/") and not n.endswith("/"))

    return {
        "schema_version": "1.0",
        "source": {"filename": path.name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)},
        "review_status": "未审查",
        "scope": "按各 XML 部件内部文档顺序清点。计数含容器和内容，不等于独立条款数量；所有项目仍需语义审查。",
        "extraction": {"body_text_present": body_text_present, "body_graphics": body_graphics, "requires_visual_review": True, "tracked_changes_preserved": True},
        "counts": dict(sorted(totals.items())),
        "parts": parts,
        "media_parts": media_parts,
        "other_word_xml_parts": other_word_xml,
        "warnings": warnings,
        "items": items,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Source DOCX (read only)")
    parser.add_argument("--output", required=True, type=Path, help="New JSON path; existing files are never overwritten")
    args = parser.parse_args(argv)
    try:
        same_path = args.input.resolve() == args.output.resolve()
        if args.input.exists() and args.output.exists():
            same_path = same_path or args.input.samefile(args.output)
        if same_path:
            raise InventoryError("Output must differ from input; source documents are read only.")
        if args.output.exists():
            raise InventoryError("Output already exists; choose a new JSON filename.")
        result = inventory(args.input)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except InventoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc.strerror}.", file=sys.stderr)
        return 2
    print(f"Inventoried {len(result['items'])} unreviewed items; wrote {args.output.name}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
