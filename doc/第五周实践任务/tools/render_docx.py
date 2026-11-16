# -*- coding: utf-8 -*-
"""把 content.BLOCKS 渲染为 docx（A4，按老师模板的样式口径）。"""
import os
import re
import sys

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content import BLOCKS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "数据模型设计说明书.docx")

CN_FONT = "宋体"
EN_FONT = "Times New Roman"


def set_run(run, size=10.5, bold=False, color=None, cn=CN_FONT, en=EN_FONT):
    run.font.name = en
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), cn)
    rfonts.set(qn("w:ascii"), en)
    rfonts.set(qn("w:hAnsi"), en)


def add_para(doc, text="", size=10.5, bold=False, color=None, align=None,
             indent=True, before=0, after=0, line=1.5, keep_next=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    if align is not None:
        p.alignment = align
    if indent:
        pf.first_line_indent = Cm(0.74)
    if keep_next:
        pf.keep_with_next = True
    if text:
        r = p.add_run(text)
        set_run(r, size=size, bold=bold, color=color)
    return p


def shade_cell(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_cell_margins(table, top=25, bottom=25, left=70, right=70):
    tblPr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for tag, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{tag}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)


def set_fixed_layout(table):
    tblPr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)


def add_table(doc, caption, headers, rows, widths, font_size=8.5):
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(8)
    cap.paragraph_format.space_after = Pt(3)
    cap.paragraph_format.keep_with_next = True
    r = cap.add_run(caption)
    set_run(r, size=9, bold=True)

    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_fixed_layout(table)
    set_cell_margins(table)
    for i, w in enumerate(widths):
        table.columns[i].width = Cm(w)

    hdr = table.rows[0]
    trPr = hdr._tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    tblHeader.set(qn("w:val"), "true")
    trPr.append(tblHeader)
    cant = OxmlElement("w:cantSplit")
    trPr.append(cant)
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.width = Cm(widths[i])
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.0
        run = p.add_run(h)
        set_run(run, size=font_size, bold=True)
        shade_cell(cell, "DCE6F1")

    keep_together = len(rows) <= 10
    if keep_together:
        for cell in hdr.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True

    for row_idx, row in enumerate(rows):
        tr = table.add_row()
        trPr = tr._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
        for i, val in enumerate(row):
            cell = tr.cells[i]
            cell.width = Cm(widths[i])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.0
            lines = str(val).replace("_", "_\u200b").split("\n")
            run = p.add_run(lines[0])
            set_run(run, size=font_size)
            for extra in lines[1:]:
                run.add_break()
                run = p.add_run(extra)
                set_run(run, size=font_size)
            if keep_together and row_idx < len(rows) - 1:
                p.paragraph_format.keep_with_next = True

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(0)
    spacer.paragraph_format.line_spacing = 0.8


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = paragraph.add_run("第 ")
    set_run(r1, size=9, color=(0x66, 0x66, 0x66))
    run = paragraph.add_run()
    set_run(run, size=9, color=(0x66, 0x66, 0x66))
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)
    r2 = paragraph.add_run(" 页")
    set_run(r2, size=9, color=(0x66, 0x66, 0x66))


def setup_portrait(section):
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)
    section.header_distance = Cm(1.5)
    section.footer_distance = Cm(1.6)


def setup_landscape(section):
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width = Cm(29.7)
    section.page_height = Cm(21)
    section.top_margin = Cm(1.2)
    section.bottom_margin = Cm(1.2)
    section.left_margin = Cm(1.2)
    section.right_margin = Cm(1.2)
    section.header_distance = Cm(1.0)
    section.footer_distance = Cm(1.0)


def add_figure(doc, path, caption, height_cm, note=""):
    abs_path = os.path.join(ROOT, path)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run()
    run.add_picture(abs_path, height=Cm(height_cm))

    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(2)
    cap.paragraph_format.space_after = Pt(2)
    r = cap.add_run(caption)
    set_run(r, size=9, bold=True)

    if note:
        n = doc.add_paragraph()
        n.alignment = WD_ALIGN_PARAGRAPH.LEFT
        n.paragraph_format.space_before = Pt(0)
        n.paragraph_format.space_after = Pt(0)
        n.paragraph_format.line_spacing = 1.15
        r = n.add_run(note)
        set_run(r, size=8, color=(0x55, 0x55, 0x55))


def main():
    doc = Document()
    sec0 = doc.sections[0]
    setup_portrait(sec0)
    add_page_number(sec0.footer.paragraphs[0])

    # 默认正文样式
    normal = doc.styles["Normal"]
    normal.font.name = EN_FONT
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), CN_FONT)

    for block in BLOCKS:
        kind = block[0]
        if kind == "title":
            p = add_para(doc, block[1], size=18, bold=True,
                         align=WD_ALIGN_PARAGRAPH.CENTER, indent=False,
                         before=6, after=6, line=1.2)
        elif kind == "center":
            add_para(doc, block[1], size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER,
                     indent=False, before=0, after=0, line=1.3)
        elif kind == "h1":
            add_para(doc, block[1], size=12, bold=True, indent=False,
                     before=12, after=6, line=1.2, keep_next=True)
        elif kind == "h2":
            add_para(doc, block[1], size=11, bold=True, indent=False,
                     before=9, after=4, line=1.2, keep_next=True)
        elif kind == "p":
            add_para(doc, block[1], size=10.5, indent=True, line=1.5)
        elif kind == "note":
            add_para(doc, "注：" + block[1], size=9, color=(0x55, 0x55, 0x55),
                     indent=False, before=2, after=4, line=1.2)
        elif kind == "bullet":
            p = add_para(doc, "", size=10.5, indent=False, line=1.3)
            p.paragraph_format.left_indent = Cm(0.74)
            p.paragraph_format.first_line_indent = Cm(-0.37)
            r = p.add_run("• " + block[1])
            set_run(r, size=10.5)
        elif kind == "table":
            add_table(doc, block[1], block[2], block[3], block[4], block[5] if len(block) > 5 else 8.5)
        elif kind == "figure":
            add_figure(doc, block[1], block[2], block[3],
                       block[4] if len(block) > 4 else "")
        elif kind == "pagebreak":
            doc.add_page_break()
        elif kind == "section":
            orient = block[1]
            sec = doc.add_section(WD_SECTION.NEW_PAGE)
            if orient == "landscape":
                setup_landscape(sec)
            else:
                setup_portrait(sec)
            if not sec.footer.is_linked_to_previous:
                add_page_number(sec.footer.paragraphs[0])

    doc.core_properties.title = "「知识分享」博客系统的数据模型设计"
    doc.core_properties.subject = "第五周实践任务：数据模型设计说明书"
    doc.core_properties.author = "第 13 组"
    doc.core_properties.comments = "依据 main@81f2d69 的 models.py 编写"
    doc.save(OUT)
    print("DOCX:", OUT)


if __name__ == "__main__":
    main()
