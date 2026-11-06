"""Typeset the report Markdown as an editable Word document.

Reads the same Markdown source and figures as build_report.py, so the Word and
PDF versions share identical content. Formatting is uniform: Times New Roman
throughout, black text, 12 pt body paragraphs, 10 pt tables and captions, A4
pages. The three display equations are rendered as images with Matplotlib's
STIX fonts, which are designed to match Times. Run after run_analysis.py (and
build_report.py, which refreshes the generated tables).
"""
import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image as PILImage

from report_contract import REPORT_TITLE_BLOCK

FONT = 'Times New Roman'
BLACK = RGBColor(0, 0, 0)
BODY_PT, HEADING1_PT, HEADING2_PT, TITLE_PT = 12, 14, 12, 16
TABLE_PT, CAPTION_PT, FOOTER_PT = 10, 10, 10
PAGE_WIDTH, PAGE_HEIGHT, MARGIN = Cm(21.0), Cm(29.7), Cm(2.54)
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN
EQUATION_DPI = 300
KEEP_TABLE_TOGETHER_ROWS = 16
FOOTER_TEXT = 'COMP6009 | Biogas monitoring and decisions'


def set_run_font(run, size=None, bold=None, italic=None):
    run.font.name = FONT
    run.font.color.rgb = BLACK
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    fonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    for attribute in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        fonts.set(qn(attribute), FONT)


def configure_styles(document):
    styles = document.styles
    for name, size, bold, italic, before, after in [
        ('Normal', BODY_PT, False, False, 0, 6),
        ('Title', TITLE_PT, True, False, 0, 12),
        ('Heading 1', HEADING1_PT, True, False, 12, 6),
        ('Heading 2', HEADING2_PT, True, False, 10, 4),
        ('Caption', CAPTION_PT, False, True, 2, 10),
    ]:
        style = styles[name]
        style.font.name = FONT
        style.font.size = Pt(size)
        style.font.bold = bold
        style.font.italic = italic
        style.font.color.rgb = BLACK
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.line_spacing = 1.15 if name == 'Normal' else 1.0
        if name.startswith('Heading') or name == 'Title':
            style.paragraph_format.keep_with_next = True
    # The default template's title has a coloured bottom border; remove it.
    title_ppr = styles['Title'].element.get_or_add_pPr()
    for border in title_ppr.findall(qn('w:pBdr')):
        title_ppr.remove(border)


def force_font_and_colour(element):
    """Replace theme fonts and theme colours with Times New Roman and black."""
    for node in element.iter():
        for attribute in list(node.attrib):
            if attribute.split('}')[-1].lower().startswith('theme') or attribute.split('}')[-1].lower().endswith('theme'):
                del node.attrib[attribute]
    for fonts in element.iter(qn('w:rFonts')):
        for attribute in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
            fonts.set(qn(attribute), FONT)
    for colour in element.iter(qn('w:color')):
        colour.set(qn('w:val'), '000000')


def remove_unused_table_styles(styles_element):
    """Drop the template's coloured table styles; tables here set their own formatting."""
    for style in list(styles_element.findall(qn('w:style'))):
        if style.get(qn('w:type')) == 'table' and style.get(qn('w:styleId')) not in ('TableNormal', 'TableGrid'):
            styles_element.remove(style)


TABLE_PROPERTY_ORDER = ['tblStyle', 'tblpPr', 'tblOverlap', 'bidiVisual', 'tblStyleRowBandSize',
                        'tblStyleColBandSize', 'tblW', 'jc', 'tblCellSpacing', 'tblInd', 'tblBorders',
                        'shd', 'tblLayout', 'tblCellMar', 'tblLook']


def order_table_properties(table):
    """Word's schema requires table properties in a fixed sequence."""
    properties = table._tbl.tblPr
    children = list(properties)
    rank = {qn(f'w:{name}'): i for i, name in enumerate(TABLE_PROPERTY_ORDER)}
    for child in children:
        properties.remove(child)
    for child in sorted(children, key=lambda c: rank.get(c.tag, len(rank))):
        properties.append(child)


def fix_settings(document):
    """The python-docx template's zoom element lacks the required percent attribute."""
    for zoom in document.settings.element.iter(qn('w:zoom')):
        zoom.set(qn('w:percent'), '100')


def add_text(paragraph, text, size=None, bold=None, italic=None):
    """Add text, rendering P(X_t | e_1:t) with true subscripts."""
    parts = re.split(r'(P\(X_t \| e_1:t\))', text)
    for part in parts:
        if part == 'P(X_t | e_1:t)':
            for piece, subscript in [('P(X', False), ('t', True), (' | e', False), ('1:t', True), (')', False)]:
                run = paragraph.add_run(piece)
                set_run_font(run, size, bold, italic)
                run.font.subscript = subscript
        elif part:
            set_run_font(paragraph.add_run(part), size, bold, italic)


def add_footer(section):
    paragraph = section.footer.paragraphs[0]
    tab_stops = paragraph.paragraph_format.tab_stops
    # The template's Footer style has US Letter tab stops; clear them so the
    # page number aligns with the A4 right margin.
    for inherited in paragraph.style.paragraph_format.tab_stops:
        tab_stops.add_tab_stop(inherited.position, WD_TAB_ALIGNMENT.CLEAR)
    tab_stops.add_tab_stop(CONTENT_WIDTH, WD_TAB_ALIGNMENT.RIGHT)
    set_run_font(paragraph.add_run(FOOTER_TEXT + '\t'), FOOTER_PT)
    run = paragraph.add_run()
    set_run_font(run, FOOTER_PT)
    for kind, text in [('begin', None), (None, 'PAGE'), ('separate', None), (None, '1'), ('end', None)]:
        if kind:
            field = OxmlElement('w:fldChar')
            field.set(qn('w:fldCharType'), kind)
            run._element.append(field)
        elif text == 'PAGE':
            instruction = OxmlElement('w:instrText')
            instruction.set(qn('xml:space'), 'preserve')
            instruction.text = ' PAGE '
            run._element.append(instruction)
        else:
            placeholder = OxmlElement('w:t')
            placeholder.text = text
            run._element.append(placeholder)


def equation_image(latex, output_path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    # Display-style fractions keep numerators and denominators at full size.
    latex = latex.replace(r'\arg\max', r'\mathrm{arg\,max}').replace(r'\frac', r'\dfrac')
    with plt.rc_context({'mathtext.fontset': 'stix', 'font.family': 'STIXGeneral'}):
        figure = plt.figure(figsize=(8, 0.55))
        figure.text(0.5, 0.5, '$' + latex + '$', ha='center', va='center', fontsize=BODY_PT + 2, color='black')
        figure.savefig(output_path, dpi=EQUATION_DPI, bbox_inches='tight', pad_inches=0.06)
        plt.close(figure)


def add_picture(document, path, width):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.add_run().add_picture(str(path), width=width)
    return paragraph


def set_cell_shading(cell, fill):
    properties = cell._tc.get_or_add_tcPr()
    shading = OxmlElement('w:shd')
    shading.set(qn('w:val'), 'clear')
    shading.set(qn('w:color'), 'auto')
    shading.set(qn('w:fill'), fill)
    properties.append(shading)


def set_table_borders(table):
    properties = table._tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        border = OxmlElement(f'w:{edge}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), '000000')
        borders.append(border)
    properties.append(borders)
    for existing in properties.findall(qn('w:tblW')):
        properties.remove(existing)
    width = OxmlElement('w:tblW')
    width.set(qn('w:w'), str(int(CONTENT_WIDTH // 635)))  # EMU to twips
    width.set(qn('w:type'), 'dxa')
    properties.append(width)


def column_widths(rows):
    """Give every column room for its longest word, then share the rest.

    Widths are estimated in characters at the table font size. Each column
    first receives enough width for its longest unbreakable word so numbers
    and labels never split mid-word; remaining width is shared in proportion
    to how much more each column needs to show its longest entry on one line.
    """
    char_width, padding = Cm(0.20), Cm(0.40)
    columns = range(len(rows[0]))
    minimum = [max(len(word) for row in rows for word in (row[c].split() or [''])) * char_width + padding for c in columns]
    desired = [max(len(row[c]) for row in rows) * char_width + padding for c in columns]
    spare = CONTENT_WIDTH - sum(minimum)
    if spare <= 0:
        return [int(CONTENT_WIDTH * m / sum(minimum)) for m in minimum]
    extra = [max(d - m, 0) for d, m in zip(desired, minimum)]
    if sum(extra) <= spare:
        # Everything fits on one line; spread the leftover evenly.
        leftover = (spare - sum(extra)) / len(minimum)
        return [int(d + leftover) for d in (m + e for m, e in zip(minimum, extra))]
    return [int(m + spare * e / sum(extra)) for m, e in zip(minimum, extra)]


def add_table(document, block):
    lines = block.splitlines()
    rows = [[cell.strip() for cell in line.strip().strip('|').split('|')] for line in lines if not re.match(r'^\|\s*:?-', line)]
    separator = next((line for line in lines if re.match(r'^\|\s*:?-', line)), '')
    right_aligned = [cell.strip().endswith(':') for cell in separator.strip().strip('|').split('|')]
    widths = column_widths(rows)
    table = document.add_table(rows=len(rows), cols=len(rows[0]))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    keep_together = len(rows) <= KEEP_TABLE_TOGETHER_ROWS
    for r, values in enumerate(rows):
        row = table.rows[r]
        row_properties = row._tr.get_or_add_trPr()
        no_split = OxmlElement('w:cantSplit')
        row_properties.append(no_split)
        if r == 0:
            header = OxmlElement('w:tblHeader')
            row_properties.append(header)
        for c, value in enumerate(values):
            cell = row.cells[c]
            cell.width = widths[c]
            if r == 0:
                set_cell_shading(cell, 'D9D9D9')
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.0
            # Keep short tables on one page and attached to their caption.
            paragraph.paragraph_format.keep_with_next = keep_together or r == len(rows) - 1
            if r > 0 and c < len(right_aligned) and right_aligned[c]:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            add_text(paragraph, value, TABLE_PT, bold=(r == 0))
    for c, width in enumerate(widths):
        table.columns[c].width = width
    order_table_properties(table)
    return table


def main():
    root = Path(__file__).resolve().parent
    source = root / 'report' / 'COMP6009_Part_B_Report.md'
    output = root / 'report' / 'COMP6009_Part_B_Report.docx'
    temporary = root / 'report' / '_equations'
    temporary.mkdir(exist_ok=True)
    source_text = source.read_text(encoding='utf-8')
    if not source_text.startswith(REPORT_TITLE_BLOCK + '\n\n'):
        raise ValueError('Report title block is missing or differs from the submission details')

    document = Document()
    configure_styles(document)
    section = document.sections[0]
    section.page_width, section.page_height = PAGE_WIDTH, PAGE_HEIGHT
    for side in ('left_margin', 'right_margin', 'top_margin', 'bottom_margin'):
        setattr(section, side, MARGIN)
    add_footer(section)
    properties = document.core_properties
    properties.title = 'Biogas Plant Intelligent Monitoring and Decision System'
    properties.author = properties.last_modified_by = 'Sayuru Rehan Bopitiya'
    properties.subject = 'COMP6009 Assignment Part B'
    properties.keywords = 'COMP6009; Assignment Part B; biogas monitoring'
    properties.comments = ''

    # Cover page: centred title, then the unit, name, ID and date further down.
    for line in REPORT_TITLE_BLOCK.splitlines()[1:-1]:
        if line.startswith('# '):
            paragraph = document.add_paragraph(style='Title')
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_after = Pt(120)
            add_text(paragraph, line[2:])
        elif line:
            paragraph = document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_after = Pt(2)
            add_text(paragraph, line)

    equation_count = 0
    references = False
    current_section = ''
    previous_was_table = False
    for block in source_text[len(REPORT_TITLE_BLOCK):].strip().split('\n\n'):
        block = block.strip()
        if re.fullmatch(r'<!-- generated:[a-z-]+:(?:start|end) -->', block):
            continue
        if block.startswith('## '):
            heading = block[3:]
            references = heading == 'References'
            current_section = heading
            paragraph = document.add_paragraph(style='Heading 1')
            # Section 1 starts after the cover page; each appendix starts a new page.
            paragraph.paragraph_format.page_break_before = heading.startswith(('Appendix', '1. '))
            add_text(paragraph, heading)
        elif block.startswith('### '):
            paragraph = document.add_paragraph(style='Heading 2')
            # Each complete scenario table in Appendix D gets its own page.
            paragraph.paragraph_format.page_break_before = (
                current_section.startswith('Appendix D') and block[4:] != 'Scenario A')
            add_text(paragraph, block[4:])
        elif block.startswith('$$'):
            equation_count += 1
            path = temporary / f'docx_equation_{equation_count}.png'
            equation_image(block.strip('$'), path)
            with PILImage.open(path) as image:
                natural_width = Cm(image.size[0] / EQUATION_DPI * 2.54)
            paragraph = add_picture(document, path, min(CONTENT_WIDTH, natural_width))
            paragraph.paragraph_format.keep_with_next = False
            paragraph.paragraph_format.space_before = Pt(4)
            paragraph.paragraph_format.space_after = Pt(8)
        elif block.startswith('!['):
            filename = re.search(r'\]\((.*?)\)', block).group(1)
            path = (source.parent / filename).resolve()
            scale = 0.86 if path.name == 'parameter_sweeps.png' else 1.0
            add_picture(document, path, int(CONTENT_WIDTH * scale))
        elif block.startswith('|'):
            if previous_was_table:
                # Separate consecutive tables, as in Appendix A.
                document.add_paragraph().paragraph_format.space_after = Pt(0)
            add_table(document, block)
        elif block.startswith('*') and block.endswith('*'):
            add_text(document.add_paragraph(style='Caption'), block[1:-1])
        else:
            paragraph = document.add_paragraph()
            if references:
                paragraph.paragraph_format.left_indent = Cm(0.9)
                paragraph.paragraph_format.first_line_indent = Cm(-0.9)
                paragraph.paragraph_format.line_spacing = 1.0
            add_text(paragraph, block.replace('\n', ' '))
        previous_was_table = block.startswith('|')

    remove_unused_table_styles(document.styles.element)
    for part in (document.styles.element, document.element.body, section.footer._element):
        force_font_and_colour(part)
    fix_settings(document)
    document.save(output)
    print(f'Created {output.name} with {equation_count} equations')


if __name__ == '__main__':
    main()
