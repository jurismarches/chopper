# -*- coding:utf-8 -*-
import tinycss
import cssselect
from lxml import html
from itertools import chain

from .translator import XpathTranslator


class TreeExtractor(object):
    """
    Extracts HTML contents given a list of xpaths
    by preserving ancestors
    """
    css_parser = tinycss.CSSPage3Parser()
    xpath_translator = XpathTranslator()

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

    def extract(self, html_contents, css_contents=None):
        """
        Extracts the cleaned html tree as a string and only
        css rules matching the cleaned html tree
        """
        # Clean HTML
        cleaned_html = self._extract_html(html_contents)

        # Clean CSS
        if css_contents is not None:
            cleaned_css = self._extract_css(css_contents)
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

        return html.tostring(self.tree).decode()

    def _get_elements_to_keep(self):
        """
        Returns a list of lxml Elements to keep
        """
        return list(*chain(self.tree.xpath(x) for x in self.xpaths_to_keep))

    def _get_elements_to_discard(self):
        """
        Returns a list of lxml Elements to discard
        """
        return list(*chain(self.tree.xpath(x) for x in self.xpaths_to_discard))

    def _parse_element(self, elt, is_keep=False):
        """
        Parses an Element
        """
        for e in elt.iterchildren():

            # Element is an explicit one to discard, flag it and continue
            if self._is_discard(e):
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
            css_contents += '%s{%s}\n' % (
                rule.selector.as_css(),
                ''.join('%s:%s;' % (d.name, d.value.as_css()) for d in rule.declarations))

        return css_contents
