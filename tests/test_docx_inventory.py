"""Meaningful OOXML fixtures; no Office application or third-party library."""

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "docx_inventory.py"
SPEC = importlib.util.spec_from_file_location("docx_inventory", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'


def make_docx(path, body, extra=None):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", f'<w:document {NS}><w:body>{body}</w:body></w:document>')
        for name, xml in (extra or {}).items():
            archive.writestr(name, xml)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_complex_content_order_locations_and_original(self):
        source = self.root / "标准.docx"
        make_docx(source, '''
          <w:p><w:r><w:t>温度为 20 ℃。</w:t></w:r></w:p>
          <w:tbl><w:tblGrid><w:gridCol/><w:gridCol/></w:tblGrid><w:tr>
            <w:tc><w:p><w:r><w:t>上层</w:t></w:r></w:p>
              <w:tbl><w:tr><w:tc><w:p><w:r><w:t>嵌套</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
            </w:tc><w:tc><w:tcPr><w:vMerge/></w:tcPr><w:p/></w:tc>
          </w:tr></w:tbl>
          <w:sdt><w:sdtPr><w:tag w:val="limit"/></w:sdtPr><w:sdtContent><w:p><w:r><w:t>控件 5</w:t></w:r></w:p></w:sdtContent></w:sdt>
          <w:p><w:r><w:drawing><a:blip r:embed="rId1"/></w:drawing></w:r></w:p>
          <w:p><w:r><w:t>框外</w:t><w:pict><w:txbxContent><w:p><w:r><w:t>框内</w:t></w:r></w:p></w:txbxContent></w:pict></w:r></w:p>
          <w:p><m:oMath><m:r><m:t>x=2</m:t></m:r></m:oMath></w:p>
          <w:p><w:del><w:r><w:delText>旧 10</w:delText></w:r></w:del><w:ins><w:r><w:t>新 12</w:t></w:r></w:ins></w:p>
        ''', {
            "word/header1.xml": f'<w:hdr {NS}><w:p><w:r><w:t>页眉</w:t></w:r></w:p></w:hdr>',
            "word/footer1.xml": f'<w:ftr {NS}><w:p><w:r><w:instrText>PAGE</w:instrText><w:t>1</w:t></w:r></w:p></w:ftr>',
            "word/footnotes.xml": f'<w:footnotes {NS}><w:footnote w:id="1"><w:p><w:r><w:t>脚注</w:t></w:r></w:p></w:footnote></w:footnotes>',
            "word/endnotes.xml": f'<w:endnotes {NS}><w:endnote w:id="2"><w:p><w:r><w:t>尾注</w:t></w:r></w:p></w:endnote></w:endnotes>',
            "word/comments.xml": f'<w:comments {NS}><w:comment w:id="3"><w:p><w:r><w:t>批注</w:t></w:r></w:p></w:comment></w:comments>',
            "word/media/image1.png": b"fixture-image",
        })
        before = source.read_bytes()
        result = MODULE.inventory(source)
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(result["source"]["sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(result["source"]["filename"], "标准.docx")
        self.assertNotIn(str(self.root), json.dumps(result, ensure_ascii=False))
        items = result["items"]
        self.assertEqual(len({x["id"] for x in items}), len(items))
        self.assertTrue(all(x["status"] == "未审查" for x in items))
        self.assertEqual(items[0]["numeric_tokens"], ["20"])
        self.assertLess(next(i for i, x in enumerate(items) if x.get("text") == "上层"), next(i for i, x in enumerate(items) if x.get("text") == "嵌套"))
        tables = [x for x in items if x["kind"] == "table"]
        self.assertEqual([x["row_cell_counts"] for x in tables], [[2], [1]])
        empty = [x for x in items if x["kind"] == "cell" and x["text_empty"]]
        self.assertEqual(len(empty), 1)
        self.assertEqual(empty[0]["vMerge"], "continue")
        texts = [x["text"] for x in items if x["kind"] == "paragraph"]
        for text in ["控件 5", "框外", "框内", "脚注", "尾注", "页眉", "批注", "旧 10新 12"]:
            self.assertIn(text, texts)
        self.assertNotIn("框外框内", texts)
        self.assertEqual(result["counts"]["formula"], 1)
        self.assertEqual(result["counts"]["revision_markers"], 2)
        self.assertIn("TRACKED_CHANGES", [x["code"] for x in result["warnings"]])
        footnote = next(x for x in items if x.get("text") == "脚注")
        self.assertEqual(footnote["annotation"], {"type": "footnote", "id": "1"})

    def test_image_only_does_not_claim_text_coverage(self):
        source = self.root / "scan.docx"
        make_docx(source, '<w:p><w:r><w:drawing><a:blip r:embed="rId1"/></w:drawing></w:r></w:p>')
        result = MODULE.inventory(source)
        self.assertFalse(result["extraction"]["body_text_present"])
        self.assertEqual(result["extraction"]["body_graphics"], 1)
        self.assertIn("NO_BODY_TEXT", [x["code"] for x in result["warnings"]])

    def test_compatibility_branches_symbols_and_cell_revision_are_visible(self):
        source = self.root / "compatibility.docx"
        make_docx(source, '''
          <mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">
            <mc:Choice Requires="w"><w:p><w:r><w:t>分支</w:t></w:r></w:p></mc:Choice>
            <mc:Fallback><w:p><w:r><w:t>备用</w:t></w:r></w:p></mc:Fallback>
          </mc:AlternateContent>
          <w:p><w:r><w:sym w:font="Symbol" w:char="F0B1"/></w:r></w:p>
          <w:tbl><w:tr><w:tc><w:tcPr><w:cellDel/></w:tcPr><w:p/></w:tc></w:tr></w:tbl>
        ''')
        result = MODULE.inventory(source)
        warning_codes = [x["code"] for x in result["warnings"]]
        self.assertIn("ALTERNATE_CONTENT", warning_codes)
        self.assertIn("FONT_SYMBOLS", warning_codes)
        self.assertIn("TRACKED_CHANGES", warning_codes)
        symbol = next(x for x in result["items"] if x["kind"] == "symbol")
        self.assertEqual(symbol["character_code"], "F0B1")

    def test_cli_success_and_no_overwrite(self):
        source, output = self.root / "input.docx", self.root / "inventory.json"
        make_docx(source, '<w:p><w:r><w:t>正文</w:t></w:r></w:p>')
        before = source.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(MODULE.main([str(source), "--output", str(output)]), 0)
            self.assertEqual(MODULE.main([str(source), "--output", str(output)]), 2)
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(json.loads(output.read_text())["review_status"], "未审查")
        self.assertIn("already exists", errors.getvalue())

    def test_input_path_and_hardlink_are_rejected(self):
        source = self.root / "input.docx"
        make_docx(source, "<w:p/>")
        before = source.read_bytes()
        linked = self.root / "linked.json"
        linked.hardlink_to(source)
        for output in (source, linked):
            with contextlib.redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(MODULE.main([str(source), "--output", str(output)]), 2)
            self.assertIn("Output must differ", errors.getvalue())
        self.assertEqual(source.read_bytes(), before)

    def test_bad_zip_and_malformed_xml_fail_clearly(self):
        source = self.root / "bad.docx"
        source.write_text("not a zip")
        with contextlib.redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(MODULE.main([str(source), "--output", str(self.root / "out.json")]), 2)
        self.assertIn("DOCX/ZIP", errors.getvalue())
        self.assertFalse((self.root / "out.json").exists())
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("word/document.xml", "<broken>")
        with self.assertRaisesRegex(MODULE.InventoryError, "Cannot parse XML part"):
            MODULE.inventory(source)


if __name__ == "__main__":
    unittest.main()
