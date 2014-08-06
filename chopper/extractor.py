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

        # Expose public methods
        self.keep = self._keep
        self.discard = self._discard

        # Keep Xpaths expressions
        self._xpaths_to_keep = []

        # Discard Xpaths expressions
        self._xpaths_to_discard = []

    ##########
    # Public #
    ##########

    @classmethod
    def keep(cls, xpath):
        """
        Creates an instance of Extractor and adds a keep Xpath expression

        :param xpath: The Xpath expression to keep
        :type xpath: str

        :retuns: A new instance of Extractor
        :rtype: Extractor
        """
        return cls().keep(xpath)

    @classmethod
    def discard(cls, xpath):
        """
        Creates an instance of Extractor and adds a discard Xpath expression

        :param xpath: The Xpath expression to discard
        :type xpath: str

        :retuns: A new instance of Extractor
        :rtype: Extractor
        """
        return cls().discard(xpath)

    def extract(self, html_contents, css_contents=None, base_url=None):
        """
        Extracts the cleaned html tree as a string and only
        css rules matching the cleaned html tree

        :param html_contents: The HTML contents to parse
        :type html_contents: str
        :param css_contents: The CSS contents to parse
        :type css_contents: str
        :param base_url: The base page URL to use for relative to absolute links
        :type base_url: str

        :returns: cleaned HTML contents, cleaned CSS contents
        :rtype: str or tuple
        """
        # Clean HTML
        html_extractor = self.html_extractor(
            html_contents, self._xpaths_to_keep, self._xpaths_to_discard)
        has_matches = html_extractor.parse()

        if has_matches:

            # Relative to absolute URLs
            if base_url is not None:
                html_extractor.rel_to_abs(base_url)

            # Convert ElementTree to string
            cleaned_html = html_extractor.to_string()

        else:
            cleaned_html = None

        # Clean CSS
        if css_contents is not None:

            if cleaned_html is not None:

                css_extractor = self.css_extractor(css_contents, cleaned_html)
                css_extractor.parse()

                # Relative to absolute URLs
                if base_url is not None:
                    css_extractor.rel_to_abs(base_url)

                cleaned_css = css_extractor.to_string()

            else:
                cleaned_css = None

        else:
            return cleaned_html

        return (cleaned_html, cleaned_css)

    ##################
    # Rules handling #
    ##################

    def _keep(self, xpath):
        """
        Adds a keep Xpath expression

        :param xpath: The Xpath expression to keep
        :type xpath: str

        :retuns: self
        :rtype: Extractor
        """
        self.__add(self._xpaths_to_keep, xpath)
        return self

    def _discard(self, xpath):
        """
        Adds a discard Xpath expression

        :param xpath: The Xpath expression to discard
        :type xpath: str

        :retuns: self
        :rtype: Extractor
        """
        self.__add(self._xpaths_to_discard, xpath)
        return self

    def __add(self, dest, xpath):
        """
        Adds a Xpath expression to the dest list

        :param dest: The destination list to add the Xpath
        :type dest: list
        :param xpath: The Xpath expression to add
        :type xpath: str
        """
        assert isinstance(xpath, string_types)
        dest.append(xpath)
