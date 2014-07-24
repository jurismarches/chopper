# -*- coding:utf-8 -*-
import re
import cssselect
from itertools import chain
from lxml import html
from lxml.etree import strip_attributes
from six import string_types
from six.moves.urllib.parse import urljoin
from tinycss.css21 import RuleSet, ImportRule, MediaRule, PageRule

from .parser import CSSParser
from .rules import FontFaceRule
from .translator import XpathTranslator


class TreeExtractor(object):
    """
    Extracts HTML contents given a list of xpaths
    by preserving ancestors
    """
    # HTML specifics
    rel_to_abs_html_excluded_prefixes = ('#', 'javascript:', 'mailto:')
    javascript_open_re = re.compile(
        r'(?P<opening>open\([\"\'])(?P<url>.*)(?P<ending>[\"\']\))',
        re.IGNORECASE | re.MULTILINE | re.DOTALL)

    # CSS specifics
    css_parser = CSSParser()
    xpath_translator = XpathTranslator()
    rel_to_abs_css_re = re.compile(
        r'url\(["\']?(?!data:)(?P<path>.*)["\']?\)',
        re.IGNORECASE | re.MULTILINE)

    def __init__(self):
        # Keep Xpaths expressions
        self._xpaths_to_keep = []

        # Discard Xpaths expressions
        self._xpaths_to_discard = []

    ##########
    # Public #
    ##########

    def keep(self, xpath):
        """
        Adds a keep Xpath expression

        :param e: The Xpath expression to keep
        :type e: str

        :retuns: self
        :rtype: TreeExtractor
        """
        self.__add(self._xpaths_to_keep, xpath)
        return self

    def discard(self, xpath):
        """
        Adds a discard Xpath expression

        :param e: The Xpath expression to discard
        :type e: str

        :retuns: self
        :rtype: TreeExtractor
        """
        self.__add(self._xpaths_to_discard, xpath)
        return self

    def extract(self, html_contents, css_contents=None, base_url=None, rel_to_abs=False):
        """
        Extracts the cleaned html tree as a string and only
        css rules matching the cleaned html tree

        :param html_contents: The HTML contents to parse
        :type html_contents: str
        :param css_contents: The CSS contents to parse
        :type css_contents: str
        :param base_url: The base page URL to use for relative to absolute links
        :type base_url: str
        :param rel_to_abs: Convert relative links to absolute ones
        :type rel_to_abs: bool

        :returns: cleaned HTML contents, cleaned CSS contents
        :rtype: str or tuple
        """
        # Clean HTML
        if self._extract_html(html_contents):

            # Relative to absolute URLs
            if rel_to_abs and base_url is not None:
                self._rel_to_abs_html(base_url)

            # Convert ElementTree to string
            cleaned_html = html.tostring(self.tree).decode()

        else:
            cleaned_html = None

        # Clean CSS
        if css_contents is not None:

            cleaned_css = self._extract_css(css_contents)

            # Relative to absolute URLs
            if rel_to_abs and base_url is not None:
                cleaned_css = self._rel_to_abs_css(base_url, cleaned_css)

        else:
            return cleaned_html

        return (cleaned_html, cleaned_css)

    ##################
    # Rules handling #
    ##################

    def __add(self, dest, e):
        """
        Adds a Xpath expression or HtmlElement to the dest list

        :param dest: The destination list to add the element/Xpath
        :type dest: list
        :param e: The HtmlElement or Xpath expression to add
        :type e: lxml.html.HtmlElement or str
        """
        assert isinstance(e, string_types)
        dest.append(e)

    ################
    # HTML parsing #
    ################

    def _extract_html(self, html_contents):
        """
        Returns a cleaned lxml ElementTree

        :param html_contents: The HTML contents to parse
        :type html_contents: str

        :returns: The cleaned lxml tree
        :rtype: lxml.html.HtmlElement
        """
        # Create the ElementTree
        self.tree = html.fromstring(html_contents)

        # Get explicits elements to keep and discard
        self.elts_to_keep = self._get_elements_to_keep()
        self.elts_to_discard = self._get_elements_to_discard()

        # Init an empty list of Elements to remove
        self.elts_to_remove = []

        # Check if the root is a match or if there is any matches
        is_root = self._is_keep(self.tree)
        has_descendant = self._has_keep_elt_in_descendants(self.tree)

        if not(is_root or has_descendant):
            return False

        # Parse and clean the ElementTree
        self._parse_element(self.tree, parent_is_keep=is_root)
        self._remove_elements()

        return True

    def _get_elements(self, source):
        """
        Returns the list of HtmlElements for the source

        :param source: The source list to parse
        :type source: list
        :returns: A list of HtmlElements
        :rtype: list
        """
        return list(chain(*[self.tree.xpath(xpath) for xpath in source]))

    def _get_elements_to_keep(self):
        """
        Returns a list of lxml Elements to keep

        :returns: List of elements to keep
        :rtype: list of lxml.html.HtmlElement
        """
        return self._get_elements(self._xpaths_to_keep)

    def _get_elements_to_discard(self):
        """
        Returns a list of lxml Elements to discard

        :returns: List of elements to discard
        :rtype: list of lxml.html.HtmlElement
        """
        return self._get_elements(self._xpaths_to_discard)

    def _parse_element(self, elt, parent_is_keep=False):
        """
        Parses an Element recursively

        :param elt: HtmlElement to parse
        :type elt: lxml.html.HtmlElement
        :param parent_is_keep: Whether the element is inside a keep element or not
        :type parent_is_keep: bool
        """
        for e in elt.iterchildren():

            is_discard_element = self._is_discard(e)
            is_keep_element = self._is_keep(e)

            # Element is an explicit one to discard, flag it and continue
            if is_discard_element and not is_keep_element:
                self.elts_to_remove.append(e)
                continue

            if not parent_is_keep:
                # Parent element is not an explicit keep, normal process
                # Element is an explicit one to keep, inspect it
                if is_keep_element:
                    self._parse_element(e, parent_is_keep=True)
                    continue

                # Has a descendant to keep, inspect it
                if self._has_keep_elt_in_descendants(e):
                    self._parse_element(e)
                    continue

                # Element did not match anything, remove it
                self.elts_to_remove.append(e)

            else:
                # Element is a child of a keep element, only check explicit discards
                self._parse_element(e, parent_is_keep=True)

    def _is_keep(self, elt):
        """
        Returns whether an Element is an explicit one to keep or not

        :param elt: The HtmlElement to check
        :type elt: str
        :returns: True if the element is an explicit one to keep
        :rtype: bool
        """
        return elt in self.elts_to_keep

    def _is_discard(self, elt):
        """
        Returns whether an Element is an explicit one to discard or not

        :param elt: The HtmlElement to check
        :type elt: str
        :returns: True if the element is an explicit one to discard
        :rtype: bool
        """
        return elt in self.elts_to_discard

    def _has_keep_elt_in_descendants(self, elt):
        """
        Returns whether the element has a descendant to keep or not

        :param elt: The HtmlElement to check
        :type elt: lxml.html.HtmlElement
        :returns: True if the element has a keep element in its descendants
        :rtype: bool
        """
        # iterdescendants is a generator, don't cast it as a list to avoid
        # parsing the whole descendants tree if not necessary
        for d in elt.iterdescendants():
            if d in self.elts_to_keep:
                return True

        return False

    def _remove_elements(self):
        """
        Removes flagged elements from the ElementTree
        """
        for e in self.elts_to_remove:

            # Get the element parent
            parent = e.getparent()

            # lxml also remove the element tail, preserve it
            if e.tail and e.tail.strip():
                parent_text = parent.text or ''
                parent.text = parent_text + e.tail

            # Remove the element
            e.getparent().remove(e)

    def _rel_to_abs_html(self, base_url):
        """
        Converts relative links from html contents to absolute links

        :param base_url: The base page url to use for building absolute links
        :type base_url: str
        """
        # Delete target attributes
        strip_attributes(self.tree, 'target')

        # Absolute links
        self.tree.rewrite_links(
            lambda link: urljoin(base_url, link)
            if not link.startswith(self.rel_to_abs_html_excluded_prefixes) else link)

        # Extra attributes
        onclick_elements = self.tree.xpath('//*[@onclick]')

        for element in onclick_elements:
            # Replace attribute with absolute URL
            element.set('onclick', self.javascript_open_re.sub(
                lambda match: '%s%s%s' % (match.group('opening'),
                        urljoin(base_url, match.group('url')),
                        match.group('ending')),
                element.get('onclick')))

    ###############
    # CSS Parsing #
    ###############

    def _extract_css(self, css_contents):
        """
        Returns the cleaned css only matching the ElementTree

        :param css_contents: The CSS contents to parse
        :type css_contents: str
        :returns: The cleaned CSS contents
        :rtype: str
        """
        # Parse the CSS contents
        stylesheet = self.css_parser.parse_stylesheet(
            css_contents)

        # Get the cleaned CSS contents
        return self._clean_css(stylesheet)

    def _clean_css(self, stylesheet):
        """
        Returns the cleaned CSS

        :param stylesheet: The Stylesheet object to parse
        :type stylesheet: tinycss.css21.Stylesheet
        :returns: The cleaned CSS contents
        :rtype: str
        """
        # Init the cleaned CSS rules and contents string
        css_rules = []

        # For every rule in the CSS
        for rule in stylesheet.rules:
            try:
                # Check if any of the rule declaration matches the tree
                if self._rule_matches_tree(rule):
                    # Append it to the css rules matches list
                    css_rules.append(rule)
            except:
                # On error, assume the rule matched the tree
                css_rules.append(rule)

        return self._build_css(css_rules)

    def _rule_matches_tree(self, rule):
        """
        Returns whether the rule matches the HTML tree

        :param rule: CSS Rule to check
        :type rule: A tinycss Rule object
        :returns: True if the rule has matches in self.tree
        :rtype: bool
        """
        # Always return True for @ rules
        if rule.at_keyword:
            return True

        return any(self.tree.xpath(self.xpath_translator.selector_to_xpath(selector))
                   for selector in cssselect.parse(rule.selector.as_css()))

    def _build_css(self, rules):
        """
        Returns a CSS string for the given rules

        :param rules: List of tinycss Rule
        :type rules: list of tinycss Rule objects
        :returns: CSS contents for the rules
        :rtype: string
        """
        # Build and return the cleaned CSS contents
        return '\n'.join(self._rule_as_string(rule) for rule in rules)

    def _rule_as_string(self, rule):
        """
        Converts a tinycss rule to a formatted CSS string

        :param rule: The rule to format
        :type rule: tinycss Rule object
        :returns: The Rule as a CSS string
        :rtype: str
        """
        if isinstance(rule, RuleSet):
            # Simple CSS rule : a { color: red; }
            return '%s{%s}' % (
                rule.selector.as_css(),
                self._declarations_as_string(rule.declarations))

        elif isinstance(rule, ImportRule):
            # @import rule
            return "@import url('%s') %s;" % (
                rule.uri, ','.join(rule.media))

        elif isinstance(rule, FontFaceRule):
            # @font-face rule
            return "@font-face{%s}" % self._declarations_as_string(rule.declarations)

        elif isinstance(rule, MediaRule):
            # @media rule
            return "@media %s{%s}" % (
                ','.join(rule.media),
                ''.join(self._rule_as_string(r) for r in rule.rules))

        elif isinstance(rule, PageRule):
            # @page rule
            selector, pseudo = rule.selector

            return "@page%s%s{%s}" % (
                ' %s' % selector if selector else '',
                ' :%s' % pseudo if pseudo else '',
                self._declarations_as_string(rule.declarations))

        return ''

    def _declarations_as_string(self, declarations):
        """
        Returns a list of declarations as a formatted CSS string

        :param declarations: The list of tinycss Declarations to format
        :type declarations: list of tinycss.css21.Declaration
        :returns: The CSS string for the declarations list
        :rtype: str
        """
        return ''.join('%s:%s;' % (d.name, d.value.as_css()) for d in declarations)

    def _rel_to_abs_css(self, base_url, css_contents):
        """
        Converts relative links from css contents to absolute links

        :param base_url: The base page url to use for building absolute links
        :type base_url: str
        :param css_contents: The CSS contents to parse
        :type css_contents: str
        :returns: The CSS contents with relative links converted to absolutes ones
        :rtype: str
        """
        return self.rel_to_abs_css_re.sub(
            lambda match: "url('%s')" % urljoin(base_url, match.group('path').strip('\'"')),
            css_contents)
