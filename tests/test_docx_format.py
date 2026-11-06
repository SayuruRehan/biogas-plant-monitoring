"""Check the committed Word report's formatting using only the standard library."""
import re
import unittest
import zipfile
from pathlib import Path

DOCX = Path(__file__).resolve().parents[1] / 'report' / 'COMP6009_Part_B_Report.docx'


def read_part(name):
    with zipfile.ZipFile(DOCX) as archive:
        return archive.read(name).decode('utf-8')


class DocxFormatTests(unittest.TestCase):
    def setUp(self):
        self.document = read_part('word/document.xml')
        self.styles = read_part('word/styles.xml')
        self.footer = read_part('word/footer1.xml')

    def test_every_font_is_times_new_roman(self):
        # The styles must set Times New Roman. Body text and the footer may
        # inherit it from the styles (Word drops run-level fonts on save),
        # but must never name a different font.
        self.assertEqual(set(re.findall(r'w:(?:ascii|hAnsi|cs)="([^"]+)"', self.styles)), {'Times New Roman'})
        for part in (self.document, self.styles, self.footer):
            fonts = set(re.findall(r'w:(?:ascii|hAnsi|cs)="([^"]+)"', part))
            self.assertLessEqual(fonts, {'Times New Roman'})
            self.assertIsNone(re.search(r'w:\w*[Tt]heme\w*="', part), 'theme font or colour attribute found')

    def test_every_text_colour_is_black(self):
        for part in (self.document, self.styles, self.footer):
            colours = set(re.findall(r'<w:color [^>]*w:val="([^"]+)"', part))
            self.assertLessEqual(colours, {'000000'})

    def test_body_paragraphs_share_one_size_and_page_is_a4(self):
        normal = re.search(r'<w:style [^>]*w:styleId="Normal".*?</w:style>', self.styles, re.S).group(0)
        self.assertIn('<w:sz w:val="24"/>', normal)
        # Only tables carry an explicit size (10 pt); body text inherits 12 pt.
        self.assertEqual(set(re.findall(r'<w:sz w:val="(\d+)"', self.document)), {'20'})
        self.assertIn('<w:pgSz w:w="11906" w:h="16838"/>', self.document)


if __name__ == '__main__':
    unittest.main()
