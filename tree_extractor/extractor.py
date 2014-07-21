# -*- coding:utf-8 -*-
import re
import tinycss
import cssselect
from six.moves.urllib.parse import urljoin
from lxml import html
from lxml.etree import strip_attributes
from itertools import chain

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
    css_parser = tinycss.CSSPage3Parser()
    xpath_translator = XpathTranslator()
    rel_to_abs_css_re = re.compile(
        r'url\(["\']?(?P<path>.*)["\']?\)',
        re.IGNORECASE | re.MULTILINE | re.DOTALL)

    def __init__(self):

        # xpaths expressions to keep
        self.xpaths_to_keep = []

        # xpaths expressions to discard
        self.xpaths_to_discard = []

    ##########
    # Public #
    ##########

    def keep(self, xpath):
        """
        Adds a keep xpath expression
        """
        self.xpaths_to_keep.append(xpath)
        return self

    def discard(self, xpath):
        """
        Adds a discard xpath expression
        """
        self.xpaths_to_discard.append(xpath)
        return self

    def extract(self, html_contents, css_contents=None, base_url=None, rel_to_abs=False):
        """
        Extracts the cleaned html tree as a string and only
        css rules matching the cleaned html tree
        """
        # Clean HTML
        cleaned_tree = self._extract_html(html_contents)

        if cleaned_tree is not None:

            # Relative to absolute URLs
            if rel_to_abs and base_url is not None:
                cleaned_tree = self._rel_to_abs_html(cleaned_tree, base_url)

            # Convert ElementTree to string
            cleaned_html = html.tostring(cleaned_tree).decode()

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

    ################
    # HTML parsing #
    ################

    def _extract_html(self, html_contents):
        """
        Returns a cleaned lxml ElementTree
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
            return None

        # Parse and clean the ElementTree
        self._parse_element(self.tree, is_keep=is_root)
        self._remove_elements()

        return self.tree

    def _get_elements_to_keep(self):
        """
        Returns a list of lxml Elements to keep
        """
        return list(chain(*[self.tree.xpath(x) for x in self.xpaths_to_keep]))

    def _get_elements_to_discard(self):
        """
        Returns a list of lxml Elements to discard
        """
        return list(chain(*[self.tree.xpath(x) for x in self.xpaths_to_discard]))

    def _parse_element(self, elt, is_keep=False):
        """
        Parses an Element
        """
        for e in elt.iterchildren():

            # Element is an explicit one to discard, flag it and continue
            if self._is_discard(e) and not self._is_keep(e):
                self.elts_to_remove.append(e)
                continue

            if not is_keep:
                # Parent element is not an explicit keep, normal process
                # Element is an explicit one to keep, inspect it
                if self._is_keep(e):
                    self._parse_element(e, is_keep=True)
                    continue

                # Has a descendant to keep, inspect it
                if self._has_keep_elt_in_descendants(e):
                    self._parse_element(e)
                    continue

                # Element did not match anything, remove it
                self.elts_to_remove.append(e)

            else:
                # Element is a child of a keep element, only check explicit discards
                self._parse_element(e, is_keep=True)

    def _is_keep(self, elt):
        """
        Returns whether an Element is an explicit one to keep or not
        """
        return elt in self.elts_to_keep

    def _is_discard(self, elt):
        """
        Returns whether an Element is an explicit one to discard or not
        """
        return elt in self.elts_to_discard

    def _has_keep_elt_in_descendants(self, elt):
        """
        Returns whether the element has a descendant to keep or not
        """
        # Get Element descendants
        descendants = list(elt.iterdescendants())

        return any(k in descendants for k in self.elts_to_keep)

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

    def _rel_to_abs_html(self, tree, base_url):
        """
        Converts relative links from html contents to absolute links
        """
        # Delete target attributes
        strip_attributes(tree, 'target')

        # Absolute links
        tree.rewrite_links(
            lambda link: urljoin(base_url, link)
            if not link.startswith(self.rel_to_abs_html_excluded_prefixes) else link)

        # Extra attributes
        onclick_elements = tree.xpath('//*[@onclick]')

        for element in onclick_elements:
            # Replace attribute with absolute URL
            element.set('onclick', self.javascript_open_re.sub(
                lambda match: '%s%s%s' % (match.group('opening'),
                        urljoin(base_url, match.group('url')),
                        match.group('ending')),
                element.get('onclick')))

        return tree

    ###############
    # CSS Parsing #
    ###############

    def _extract_css(self, css_contents):
        """
        Returns the cleaned css only matching the ElementTree
        """
        # Parse the CSS contents
        stylesheet = self.css_parser.parse_stylesheet(
            css_contents)

        # Get the cleaned CSS contents
        return self._clean_css(stylesheet)

    def _clean_css(self, stylesheet):
        """
        Returns the cleaned CSS
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
        """
        return any(self.tree.xpath(self.xpath_translator.selector_to_xpath(selector))
                   for selector in cssselect.parse(rule.selector.as_css()))

    def _build_css(self, rules):
        """
        Returns a CSS string for the given rules
        """
        css_contents = ''

        # Build the cleaned CSS contents
        for rule in rules:
            if rule.at_keyword is None:
                css_contents += '%s{%s}\n' % (
                    rule.selector.as_css(),
                    ''.join('%s:%s;' % (d.name, d.value.as_css()) for d in rule.declarations))

        return css_contents

    def _rel_to_abs_css(self, base_url, css_contents):
        """
        Converts relative links from css contents to absolute links
        """
        return self.rel_to_abs_css_re.sub(
            lambda match: "url('%s')" % urljoin(base_url, match.group('path').strip('\'"')),
            css_contents)
