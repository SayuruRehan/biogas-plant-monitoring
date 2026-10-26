"""Typeset the editable report Markdown as a standalone PDF.

Uses ReportLab for layout and Matplotlib's mathtext for the three equations.
No network connection, external files outside this package, or office software
is required. Run after run_analysis.py to regenerate the embedded figures.
"""
import re
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether, PageBreak
from report_contract import REPORT_TITLE_BLOCK, report_fingerprints, report_word_count


def register_fonts():
    """Use Matplotlib's bundled fonts, avoiding platform-specific font paths."""
    import matplotlib
    font_dir=Path(matplotlib.get_data_path())/'fonts'/'ttf'
    for name,file in [('Body','DejaVuSerif.ttf'),('BodyBold','DejaVuSerif-Bold.ttf'),('BodyItalic','DejaVuSerif-Italic.ttf'),('Sans','DejaVuSans.ttf'),('SansBold','DejaVuSans-Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(font_dir/file)))
    pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='BodyItalic',boldItalic='BodyBold')


def equation_image(latex, output_path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    # Mathtext supports \, \mid, \sum and common notation; \arg is replaced
    # by \mathrm to work across supported Matplotlib versions.
    latex=latex.replace(r'\arg\max',r'\mathrm{arg\,max}')
    fig=plt.figure(figsize=(8,0.75))
    fig.text(0.5,0.5,'$'+latex+'$',ha='center',va='center',fontsize=15)
    fig.savefig(output_path,dpi=250,bbox_inches='tight',pad_inches=0.08)
    plt.close(fig)


def main():
    root=Path(__file__).resolve().parent
    source=root/'report'/'COMP6009_Part_B_Report.md'
    output=root/'report'/'COMP6009_Part_B_Report.pdf'
    temporary=root/'report'/'_equations'
    temporary.mkdir(exist_ok=True)
    register_fonts()
    width=A4[0]-108
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportBody',fontName='Body',fontSize=10.4,leading=15,spaceAfter=8,alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='ReportTitle',fontName='SansBold',fontSize=21,leading=26,textColor=colors.HexColor('#173F42'),spaceAfter=10))
    styles.add(ParagraphStyle(name='ReportH1',fontName='SansBold',fontSize=13,leading=18,textColor=colors.HexColor('#173F42'),spaceBefore=13,spaceAfter=7,keepWithNext=True))
    styles.add(ParagraphStyle(name='ReportH2',fontName='SansBold',fontSize=11.3,leading=16,spaceBefore=10,spaceAfter=6,keepWithNext=True))
    styles.add(ParagraphStyle(name='Caption',fontName='BodyItalic',fontSize=8.5,leading=12,spaceAfter=10,textColor=colors.HexColor('#4B555B')))
    styles.add(ParagraphStyle(name='Cell',fontName='Sans',fontSize=8.4,leading=11))
    styles.add(ParagraphStyle(name='HeaderCell',fontName='SansBold',fontSize=8.4,leading=11,textColor=colors.white))
    styles.add(ParagraphStyle(name='Reference',fontName='Body',fontSize=9,leading=13,spaceAfter=8,wordWrap='CJK'))
    source_text=source.read_text(encoding='utf-8')
    if not source_text.startswith(REPORT_TITLE_BLOCK+'\n\n'):
        raise ValueError('Report title block is missing or differs from the submission details')
    blocks=source_text[len(REPORT_TITLE_BLOCK):].strip().split('\n\n')
    title_lines=REPORT_TITLE_BLOCK.splitlines()[1:-1]
    title_story=[]
    for line in title_lines:
        if line.startswith('# '):
            title_story.append(Paragraph(escape(line[2:]),styles['ReportTitle']))
        elif line:
            title_story.append(Paragraph(escape(line),styles['ReportBody']))
    story=[KeepTogether(title_story+[Spacer(1,10)])]
    equation_count=0
    references=False
    for block in blocks:
        if block.startswith('# '):
            story.append(Paragraph(escape(block[2:]),styles['ReportTitle']))
        elif block.startswith('## '):
            heading=block[3:]
            if heading.startswith('Appendix'):
                story.append(PageBreak())
            references=heading=='References'
            story.append(Paragraph(escape(heading),styles['ReportH1']))
        elif block.startswith('### '):
            story.append(Paragraph(escape(block[4:]),styles['ReportH2']))
        elif block.startswith('$$'):
            equation_count+=1
            path=temporary/f'equation_{equation_count}.png'
            equation_image(block.strip('$'),path)
            with PILImage.open(path) as im:
                image_width,image_height=im.size
            target_width=min(width,image_width/250*72)
            story.append(Image(str(path),width=target_width,height=target_width*image_height/image_width))
            story.append(Spacer(1,8))
        elif block.startswith('!['):
            filename=re.search(r'\]\((.*?)\)',block).group(1)
            path=(source.parent/filename).resolve()
            with PILImage.open(path) as im:
                image_width,image_height=im.size
            story.append(Image(str(path),width=width,height=width*image_height/image_width))
            story.append(Spacer(1,4))
        elif block.startswith('|'):
            rows=[[cell.strip() for cell in line.strip('|').split('|')] for line in block.splitlines() if not re.match(r'^\|\s*:?-',line)]
            ncols=len(rows[0])
            if ncols==6 and rows[0][0]=='State':
                col_widths=[width*x for x in [0.16,0.17,0.17,0.13,0.18,0.19]]
            elif ncols==6 and rows[0][0]=='Scenario / step':
                col_widths=[width*x for x in [0.15,0.18,0.17,0.17,0.17,0.16]]
            elif ncols==6:
                col_widths=[width*x for x in [0.12,0.31,0.13,0.13,0.14,0.17]]
            elif ncols==3 and 'Weight' in rows[0]:
                col_widths=[width*x for x in [0.17,0.66,0.17]]
            elif ncols==4 and 'perturbation' in rows[0][0]:
                col_widths=[width*x for x in [0.52,0.24,0.12,0.12]]
            elif ncols in [4,5]:
                col_widths=[width*0.34]+[width*0.66/(ncols-1)]*(ncols-1)
            else:
                col_widths=[width/ncols]*ncols
            cells=[[Paragraph(escape(c),styles['HeaderCell'] if i==0 else styles['Cell']) for c in row] for i,row in enumerate(rows)]
            table=Table(cells,colWidths=col_widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#264D50')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F3F6F6'),colors.white]),('LINEBELOW',(0,-1),(-1,-1),0.5,colors.HexColor('#CAD3D4'))]))
            story.append(KeepTogether([table,Spacer(1,4)]))
        elif block.startswith('*') and block.endswith('*'):
            story.append(Paragraph(escape(block[1:-1]),styles['Caption']))
        else:
            style=styles['Reference'] if references else styles['ReportBody']
            paragraph_text=escape(block.replace('\n',' '))
            paragraph_text=paragraph_text.replace('P(X_t | e_1:t)','P(X<sub>t</sub> | e<sub>1:t</sub>)')
            story.append(Paragraph(paragraph_text,style))
    # Keep each scenario's chart, caption and interpretation together. Keep
    # references together, then allow the compact model appendix on that page.
    packed=[]
    i=0
    while i<len(story):
        item=story[i]
        if isinstance(item,Paragraph) and item.style.name=='ReportH2' and item.getPlainText().startswith('Scenario'):
            group=[item]
            i+=1
            while i<len(story):
                following=story[i]
                if isinstance(following,Paragraph) and following.style.name=='ReportBody':
                    group.append(following)
                    i+=1
                    break
                group.append(following)
                i+=1
            packed.append(KeepTogether(group))
        elif isinstance(item,Paragraph) and item.getPlainText()=='5. Conclusion':
            group=[item]
            i+=1
            while i<len(story) and isinstance(story[i],Paragraph) and story[i].style.name=='ReportBody':
                group.append(story[i])
                i+=1
            packed.append(KeepTogether(group))
        elif isinstance(item,Paragraph) and item.getPlainText()=='References':
            group=[item]
            i+=1
            while i<len(story) and isinstance(story[i],Paragraph) and story[i].style.name=='Reference':
                group.append(story[i])
                i+=1
            packed.append(KeepTogether(group))
        else:
            packed.append(item)
            i+=1
    def footer(canvas,doc):
        canvas.setFont('Sans',8)
        canvas.setFillColor(colors.HexColor('#667078'))
        canvas.drawString(54,29,'COMP6009 | Biogas monitoring and decisions')
        canvas.drawRightString(A4[0]-54,29,str(doc.page))
    fingerprints=';'.join(f'{key}:{value}' for key,value in report_fingerprints(root).items())
    doc=SimpleDocTemplate(str(output),pagesize=A4,rightMargin=54,leftMargin=54,topMargin=45,bottomMargin=48,title='Biogas Plant Intelligent Monitoring and Decision System',author='Sayuru Bopitiya',subject='COMP6009 Assignment Part B',keywords=fingerprints)
    doc.build(packed,onFirstPage=footer,onLaterPages=footer)
    words=report_word_count(source.read_text(encoding='utf-8'))
    print(f'Created {output.name}; main-body word count including tables and headings: {words}')
    if not 1800 <= words <= 2200:
        raise ValueError('Report is outside the recommended 1800-2200 word range')


if __name__=='__main__':
    main()
