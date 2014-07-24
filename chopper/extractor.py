# -*- coding:utf-8 -*-
from six import string_types

from .css.extractor import CSSExtractor
from .html.extractor import HTMLExtractor


class Extractor(object):
    """
    Extracts HTML contents given a list of xpaths
    by preserving ancestors
    """
    html_extractor = HTMLExtractor
    css_extractor = CSSExtractor

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
        :rtype: Extractor
        """
        self.__add(self._xpaths_to_keep, xpath)
        return self

    def discard(self, xpath):
        """
        Adds a discard Xpath expression

        :param e: The Xpath expression to discard
        :type e: str

        :retuns: self
        :rtype: Extractor
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
        # Whether rel_to_abs process is necessary or not
        do_rel_to_abs = rel_to_abs and base_url is not None

        # Clean HTML
        html_extractor = self.html_extractor(
            html_contents, self._xpaths_to_keep, self._xpaths_to_discard)
        has_matches = html_extractor.parse()

        if has_matches:

            # Relative to absolute URLs
            if do_rel_to_abs:
                html_extractor.rel_to_abs(base_url)

            # Convert ElementTree to string
            cleaned_html = html_extractor.to_string()

        else:
            cleaned_html = None

        # Clean CSS
        if css_contents is not None:

            css_extractor = self.css_extractor(css_contents, html_extractor.tree)
            css_extractor.parse()

            # Relative to absolute URLs
            if do_rel_to_abs:
                css_extractor.rel_to_abs(base_url)

            cleaned_css = css_extractor.to_string()

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
