# -*- coding: utf-8 -*-
from unittest import TestCase

from .extractor import TreeExtractor


TEST_HTML = """
<html>
    <head>
        <title>TestCase</title>
    </head>

    <body>

        <div class="cls1">
            <a href="test">Test Link</a>
            <p>
                Hello <strong>world</strong> !
            </p>
            <p>
                This is <span>not</span> a test
            </p>
        </div>

        <div id="main">
            <a href="test">Test <em>Link</em></a>
        </div>

        <footer>I am the <span>footer</span></footer>

    </body>
</html>
"""

TEST_CSS = """
a { color: red; }
p { margin: 10px; }
div#main { border-bottom: 1px solid black; }
footer { color: blue; }
strong { text-decoration: underline; }
div { border: 1px solid red; }
div.cls1 { border-bottom: 1px solid green; }
span { color: red; }
"""


class TreeExtractorTestCase(TestCase):

    def __init__(self, *args, **kwargs):
        super(TreeExtractorTestCase, self).__init__(*args, **kwargs)

        if not hasattr(self, 'assertIsNone'):
            self.assertIsNone = lambda v: self.assertEqual(v, None)

    def format_output(self, output):
        return ''.join(l.strip() for l in output.splitlines())

    def test_no_rules(self):
        """
        Tests an extractor without any rules
        """
        extractor = TreeExtractor()
        html = extractor.extract(TEST_HTML)

        self.assertIsNone(html)

    def test_rule_is_root(self):
        """
        Tests a single rule is the root element
        """
        sample_html = "<html><body><p>TEST</p></body></html>"

        extractor = TreeExtractor().keep('//html')
        html = extractor.extract(sample_html)

        self.assertEqual(self.format_output(html), sample_html)

    def test_no_matches(self):
        """
        Tests no keep rules matched
        """
        extractor = TreeExtractor().keep('//section')
        html = extractor.extract(TEST_HTML)

        self.assertIsNone(html)

    def test_single_keep_html(self):
        """
        Tests an extractor with a single keep rule
        """
        extractor = TreeExtractor().keep('//a[@href="test"]')
        html = extractor.extract(TEST_HTML)

        expected_html = """<html><body><div class="cls1"><a href="test">Test Link</a></div><div id="main"><a href="test">Test <em>Link</em></a></div></body></html>"""

        self.assertEqual(self.format_output(html), expected_html)

    def test_single_keep_and_discard_html(self):
        """
        Tests an extractor with a single keep rule and a discard rule
        """
        extractor = TreeExtractor().keep('//a[@href="test"]').discard('//em')
        html = extractor.extract(TEST_HTML)

        expected_html = """<html><body><div class="cls1"><a href="test">Test Link</a></div><div id="main"><a href="test">Test </a></div></body></html>"""

        self.assertEqual(self.format_output(html), expected_html)

    def test_single_keep_html_css(self):
        """
        Tests a single keep rule with CSS
        """
        extractor = TreeExtractor().keep('//strong')
        html, css = extractor.extract(TEST_HTML, TEST_CSS)

        expected_html = """<html><body><div class="cls1"><p>Hello <strong>world</strong> !</p></div></body></html>"""
        expected_css = """p{margin:10px;}strong{text-decoration:underline;}div{border:1px solid red;}div.cls1{border-bottom:1px solid green;}"""

        self.assertEqual(self.format_output(html), expected_html)
        self.assertEqual(self.format_output(css), expected_css)

    def test_single_keep_and_discard_html_css(self):
        """
        Tests an extractor with a single keep rule and a discard rule with CSS
        """
        extractor = TreeExtractor().keep('//footer').discard('//span')
        html, css = extractor.extract(TEST_HTML, TEST_CSS)

        expected_html = """<html><body><footer>I am the </footer></body></html>"""
        expected_css = """footer{color:blue;}"""

        self.assertEqual(self.format_output(html), expected_html)
        self.assertEqual(self.format_output(css), expected_css)

    def test_multiple_keep(self):
        """
        Tests an extractor with multiple keep rules
        """
        extractor = TreeExtractor().keep('//footer').keep('//div[@id="main"]')
        html = extractor.extract(TEST_HTML)

        expected_html = """<html><body><div id="main"><a href="test">Test <em>Link</em></a></div><footer>I am the <span>footer</span></footer></body></html>"""

        self.assertEqual(self.format_output(html), expected_html)

    def test_global_discard_with_specific_keep(self):
        """
        Tests an extractor with a global element discard but with a specific keep
        """
        extractor = TreeExtractor().keep('//div[@id="main"]/a').discard('//a')
        html = extractor.extract(TEST_HTML)

        expected_html = """<html><body><div id="main"><a href="test">Test <em>Link</em></a></div></body></html>"""

        self.assertEqual(self.format_output(html), expected_html)

    def test_rel_to_abs(self):
        """
        Tests the rel_to_abs feature
        """
        input_css = """a { background: url('picture.jpg');}"""

        extractor = TreeExtractor().keep('//div[@id="main"]/a').discard('//a')
        html, css = extractor.extract(
            TEST_HTML, input_css, base_url='http://test.com', rel_to_abs=True)

        expected_html = """<html><body><div id="main"><a href="http://test.com/test">Test <em>Link</em></a></div></body></html>"""
        expected_css = """a{background:url('http://test.com/picture.jpg');}"""

        self.assertEqual(self.format_output(html), expected_html)
        self.assertEqual(self.format_output(css), expected_css)

        # More tests with different CSS formatting

        input_css = """a { background: url("picture.jpg");}"""
        html, css = extractor.extract(
            TEST_HTML, input_css, base_url='http://test.com', rel_to_abs=True)

        self.assertEqual(self.format_output(css), expected_css)

        input_css = """a { background: url(picture.jpg);}"""
        html, css = extractor.extract(
            TEST_HTML, input_css, base_url='http://test.com', rel_to_abs=True)

        self.assertEqual(self.format_output(css), expected_css)

    def test_css_at_rule(self):
        """
        Tests CSS contents with @ rules
        """
        input_css = """
        @import 'test.css';
        @media screen {p{color: blue;}}
        a { color: blue; }
        """
        extractor = TreeExtractor().keep('//div[@id="main"]/a').discard('//a')
        _, css = extractor.extract(TEST_HTML, input_css)

        expected_css = """a{color:blue;}"""
        self.assertEqual(self.format_output(css), expected_css)

