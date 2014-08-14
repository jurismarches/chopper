# -*- coding: utf-8 -*-
from unittest import TestCase

from .extractor import Extractor


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


class ExtractorTestCase(TestCase):

    def __init__(self, *args, **kwargs):
        super(ExtractorTestCase, self).__init__(*args, **kwargs)

        if not hasattr(self, 'assertIsNone'):
            self.assertIsNone = lambda v: self.assertEqual(v, None)

    def format_output(self, output):
        return ''.join(l.strip() for l in output.splitlines())

    def test_no_rules(self):
        """
        Tests an extractor without any rules
        """
        extractor = Extractor()
        html = extractor.extract(TEST_HTML)

        self.assertIsNone(html)

    def test_rule_is_root(self):
        """
        Tests a single rule is the root element
        """
        sample_html = "<html><body><p>TEST</p></body></html>"

        extractor = Extractor().keep('//html')
        html = extractor.extract(sample_html)

        self.assertEqual(self.format_output(html), sample_html)

    def test_no_matches(self):
        """
        Tests no keep rules matched
        """
        extractor = Extractor().keep('//section')
        html = extractor.extract(TEST_HTML)

        self.assertIsNone(html)

    def test_single_keep_html(self):
        """
        Tests an extractor with a single keep rule
        """
        extractor = Extractor().keep('//a[@href="test"]')
        html = extractor.extract(TEST_HTML)

        expected_html = """<html><body><div class="cls1"><a href="test">Test Link</a></div><div id="main"><a href="test">Test <em>Link</em></a></div></body></html>"""

        self.assertEqual(self.format_output(html), expected_html)

    def test_single_keep_and_discard_html(self):
        """
        Tests an extractor with a single keep rule and a discard rule
        """
        extractor = Extractor().keep('//a[@href="test"]').discard('//em')
        html = extractor.extract(TEST_HTML)

        expected_html = """<html><body><div class="cls1"><a href="test">Test Link</a></div><div id="main"><a href="test">Test </a></div></body></html>"""

        self.assertEqual(self.format_output(html), expected_html)

    def test_single_keep_html_css(self):
        """
        Tests a single keep rule with CSS
        """
        extractor = Extractor().keep('//strong')
        html, css = extractor.extract(TEST_HTML, TEST_CSS)

        expected_html = """<html><body><div class="cls1"><p>Hello <strong>world</strong> !</p></div></body></html>"""
        expected_css = """p{margin:10px;}strong{text-decoration:underline;}div{border:1px solid red;}div.cls1{border-bottom:1px solid green;}"""

        self.assertEqual(self.format_output(html), expected_html)
        self.assertEqual(self.format_output(css), expected_css)

    def test_single_keep_and_discard_html_css(self):
        """
        Tests an extractor with a single keep rule and a discard rule with CSS
        """
        extractor = Extractor().keep('//footer').discard('//span')
        html, css = extractor.extract(TEST_HTML, TEST_CSS)

        expected_html = """<html><body><footer>I am the </footer></body></html>"""
        expected_css = """footer{color:blue;}"""

        self.assertEqual(self.format_output(html), expected_html)
        self.assertEqual(self.format_output(css), expected_css)

    def test_multiple_keep(self):
        """
        Tests an extractor with multiple keep rules
        """
        extractor = Extractor().keep('//footer').keep('//div[@id="main"]')
        html = extractor.extract(TEST_HTML)

        expected_html = """<html><body><div id="main"><a href="test">Test <em>Link</em></a></div><footer>I am the <span>footer</span></footer></body></html>"""

        self.assertEqual(self.format_output(html), expected_html)

    def test_global_discard_with_specific_keep(self):
        """
        Tests an extractor with a global element discard but with a specific keep
        """
        extractor = Extractor().keep('//div[@id="main"]/a').discard('//a')
        html = extractor.extract(TEST_HTML)

        expected_html = """<html><body><div id="main"><a href="test">Test <em>Link</em></a></div></body></html>"""

        self.assertEqual(self.format_output(html), expected_html)

    def test_rel_to_abs(self):
        """
        Tests the rel_to_abs feature
        """
        input_css = """a { background: url('picture.jpg');}"""

        extractor = Extractor().keep('//div[@id="main"]/a').discard('//a')
        html, css = extractor.extract(
            TEST_HTML, input_css, base_url='http://test.com')

        expected_html = """<html><body><div id="main"><a href="http://test.com/test">Test <em>Link</em></a></div></body></html>"""
        expected_css = """a{background:url('http://test.com/picture.jpg');}"""

        self.assertEqual(self.format_output(html), expected_html)
        self.assertEqual(self.format_output(css), expected_css)

        # More tests with different CSS formatting

        input_css = """a { background: url("picture.jpg");}"""
        html, css = extractor.extract(
            TEST_HTML, input_css, base_url='http://test.com')

        self.assertEqual(self.format_output(css), expected_css)

        input_css = """a { background: url(picture.jpg);}"""
        html, css = extractor.extract(
            TEST_HTML, input_css, base_url='http://test.com')

        self.assertEqual(self.format_output(css), expected_css)

    def test_css_at_rules(self):
        """
        Tests CSS parsing with multiple @ rules
        """
        input_css = """
        @import 'test.css';
        @import url(http://website.com/css/style.css);
        @media screen {p{color: blue;}}
        @font-face {font-family: 'test';
          font-style: normal;
          font-weight: 300;
          src: local('test');
        }
        @page {
            margin: 1in;
            size: portrait;
            marks: none;
        }
        @page h1  :first {
            font-size: 20pt;
        }
        @page :left {
          margin-left: 4cm;
        }
        a {
            color: blue;
            background-image: url(data:image/png;base64,BASE64DATA)
        }
        """
        extractor = Extractor().keep('//div[@id="main"]/a').discard('//a')
        _, css = extractor.extract(
            TEST_HTML, input_css, base_url='http://test.com/dir/')

        expected_css = """@import url('http://test.com/dir/test.css') all;@import url('http://website.com/css/style.css') all;@media screen{p{color:blue;}}@font-face{font-family:'test';font-style:normal;font-weight:300;src:local('test');}@page{margin:1in;size:portrait;marks:none;}@page h1 :first{font-size:20pt;}@page :left{margin-left:4cm;}a{color:blue;background-image:url(data:image/png;base64,BASE64DATA);}"""
        self.assertEqual(self.format_output(css), expected_css)

    def test_css_selector_formatting(self):
        """
        Tests CSS selectors with newlines, multiple spaces, etc
        """
        input_css = """body,
        a,     div .test #id,

        article
        { color: blue; }"""

        extractor = Extractor().keep('//body')
        _, css = extractor.extract(TEST_HTML, input_css)

        expected_css = """body,a{color:blue;}"""
        self.assertEqual(css, expected_css)

    def test_css_multiple_selectors_clean(self):
        """
        Tests CSS with multiple selectors cleaning
        """
        input_css = """
        a, div, footer, body, span { color: red; font-size: 10px; }
        a, span, header { border: 1px solid red; }
        """

        extractor = Extractor().keep('//div[@id="main"]/a')
        html, css = extractor.extract(TEST_HTML, input_css)

        expected_css = """a,div,body{color:red;font-size:10px;}a{border:1px solid red;}"""
        self.assertEqual(self.format_output(css), expected_css)

    def test_pseudo_css(self):
        """
        Tests pseudo CSS conversion
        """
        input_css = """
        a:hover { background-color: red; }
        a.red:visited { color: blue; }
        """

        extractor = Extractor().keep('//div[@id="main"]/a')
        _, css = extractor.extract(TEST_HTML, input_css)

        expected_css = """a:hover{background-color:red;}"""
        self.assertEqual(self.format_output(css), expected_css)

    def test_unknown_css_matches(self):
        """
        Tests that unknown pseudo CSS rules always matches
        """
        input_css = """
        a::-moz-page-sequence {color:blue;}
        """

        extractor = Extractor().keep('//div[@id="main"]/a')
        _, css = extractor.extract(TEST_HTML, input_css)

        expected_css = """a::-moz-page-sequence{color:blue;}"""
        self.assertEqual(self.format_output(css), expected_css)

    def test_html_onclick_rel_to_abs(self):
        """
        Tests HTML with onlick attributes
        """
        input_html = """
        <html>
            <head>
            </head>
            <body>
                <a onclick="open('page.html')">Hello world :)</a>
            </body>
        </html>
        """

        extractor = Extractor().keep('//*')
        html = extractor.extract(
            input_html, base_url='http://test.com/folder/hello.html')

        expected_html = """<html><head></head><body><a onclick="open('http://test.com/folder/page.html')">Hello world :)</a></body></html>"""
        self.assertEqual(self.format_output(html), expected_html)

    def test_elements_with_tail(self):
        """
        Tests removing elements but preserving their tail
        """
        input_html = """
        <html>
            <head>
            </head>
            <body>
                <p>Hello world :)</p>
                NOPE
            </body>
        </html>
        """

        extractor = Extractor().keep('//body').discard('//p')
        html = extractor.extract(input_html)

        expected_html = """<html><body>NOPE</body></html>"""
        self.assertEqual(self.format_output(html), expected_html)

    def test_classmethods(self):
        """
        Tests creation with classmethods
        """
        extractor = Extractor.keep('//a').keep('//p').discard('//div')

        self.assertEqual(len(extractor._xpaths_to_keep), 2)
        self.assertEqual(len(extractor._xpaths_to_discard), 1)

    def test_unknown_css_at_rule_are_removed(self):
        """
        Tests that unknown CSS @ rules are removed
        """
        input_css = """
        @foo url('lol.py');
        body { color: red; }
        """

        extractor = Extractor.keep('//body')
        _, css = extractor.extract(TEST_HTML, input_css)

        expected_css = """body{color:red;}"""
        self.assertEqual(self.format_output(css), expected_css)

    def test_bad_css_rules_always_match(self):
        """
        Tests that bad CSS rules always match 'as is'
        """
        input_css = """
        @bar();
        body < a { color: red; }
        help << p { color: blue; }
        """

        extractor = Extractor.keep('//body')
        _, css = extractor.extract(TEST_HTML, input_css)

        expected_css = """body < a{color:red;}help << p{color:blue;}"""
        self.assertEqual(self.format_output(css), expected_css)

    def test_css_rel_to_abs_non_regression(self):
        """
        Tests css rel to abs quote fix
        """
        input_css = """
        @font-face {
          font-family: 'Roboto';
          font-style: normal;
          font-weight: 700;
          src: local('Font'), local('Font'), url(font.woff) format('woff');
        }
        @font-face {
          font-family: 'Roboto';
          font-style: normal;
          font-weight: 700;
          src: local('Font'), local('Font'), url('font.woff') format('woff');
        }
        @font-face {
          font-family: 'Roboto';
          font-style: normal;
          font-weight: 700;
          src: local('Font'), local('Font'), url("font.woff") format('woff');
        }"""

        _, css = Extractor.keep('//*').extract(
            TEST_HTML, input_css, base_url='http://website.com/dir/page.html')

        expected_css = (
            """@font-face{font-family:'Roboto';font-style:normal;font-weight:700;src:local('Font'), local('Font'), url('http://website.com/dir/font.woff') format('woff');}"""
            """@font-face{font-family:'Roboto';font-style:normal;font-weight:700;src:local('Font'), local('Font'), url('http://website.com/dir/font.woff') format('woff');}"""
            """@font-face{font-family:'Roboto';font-style:normal;font-weight:700;src:local('Font'), local('Font'), url('http://website.com/dir/font.woff') format('woff');}"""
        )

        self.assertEqual(self.format_output(css), expected_css)

    def test_css_parsing_when_html_has_no_matches_non_regression(self):
        """
        Tests CSS parsing when HTML didn't match
        """
        html, css = Extractor.keep('//div[@id="doesnotexists"]').extract(
            TEST_HTML, TEST_CSS)

        self.assertIsNone(html)
        self.assertIsNone(css)

    def test_img_src_rel_to_abs(self):
        """
        Tests images SRC attribute rel to abs
        """
        input_html = """
        <html>
            <body>
                <img alt="Test" src="../img/cool-picture.png">
            </body>
        </html>"""

        html = Extractor.keep('//img').extract(
            input_html, base_url='https://website.com/section/category/index.html')

        expected_html = """<html><body><img alt="Test" src="https://website.com/section/img/cool-picture.png"></body></html>"""
        self.assertEqual(self.format_output(html), expected_html)

    def test_css_multiline_non_regression(self):
        """
        Tests multiline CSS parsing
        """
        input_html = """
        <html>
            <body>
                <span class="need"></span>
            </body>
        </html>
        """

        input_css = """
        .hello world this .is a .test,
        .ineed more .tests,
        .more tests,
        body span.need,
        .do not .want,
        body {
            color: blue;
        }
        """

        _, css = Extractor.keep("//span[@class='need']").extract(input_html, input_css)
        expected_css = "body span.need,body{color:blue;}"

        self.assertEqual(self.format_output(css), expected_css)
