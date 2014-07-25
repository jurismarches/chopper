import re
from lxml import html
from itertools import chain
from lxml.etree import strip_attributes
from six.moves.urllib.parse import urljoin

from ..mixins import TreeBuilderMixin


class HTMLExtractor(TreeBuilderMixin):
    """
    Extracts HTML contents given a list
    of xpaths to keep and to discard
    """
    rel_to_abs_excluded_prefixes = ('#', 'javascript:', 'mailto:')

    javascript_open_re = re.compile(
        r'(?P<opening>open\([\"\'])(?P<url>.*)(?P<ending>[\"\']\))',
        re.IGNORECASE | re.MULTILINE | re.DOTALL)

    def __init__(self, html_contents, xpaths_to_keep, xpaths_to_discard):
        """
        Inits the extractor

        :param html_contents: The HTML contents to parse
        :type html_contents: str
        :param to_keep: A list of xpaths to keep
        :type to_keep: list
        :param to_discard: A list of xpaths to discard
        :type to_discard: list
        """
        self.html_contents = html_contents
        self.xpaths_to_keep = xpaths_to_keep
        self.xpaths_to_discard = xpaths_to_discard

    ##########
    # Public #
    ##########

    def parse(self):
        """
        Returns a cleaned lxml ElementTree

        :returns: Whether the cleaned HTML has matches or not
        :rtype: bool
        """
        # Create the element tree
        self.tree = self._build_tree(self.html_contents)

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
        self._remove_elements(self.elts_to_remove)

        return True

    def rel_to_abs(self, base_url):
        """
        Converts relative links from html contents to absolute links
        """
        # Delete target attributes
        strip_attributes(self.tree, 'target')

        # Absolute links
        self.tree.rewrite_links(
            lambda link: urljoin(base_url, link)
            if not link.startswith(self.rel_to_abs_excluded_prefixes) else link)

        # Extra attributes
        onclick_elements = self.tree.xpath('//*[@onclick]')

        for element in onclick_elements:
            # Replace attribute with absolute URL
            element.set('onclick', self.javascript_open_re.sub(
                lambda match: '%s%s%s' % (match.group('opening'),
                        urljoin(base_url, match.group('url')),
                        match.group('ending')),
                element.get('onclick')))

    def to_string(self):
        """
        Returns the cleaned html tree as a string

        :returns: The cleaned HTML contents
        :rtype: str
        """
        return html.tostring(self.tree).decode()

    ###########
    # Private #
    ###########

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
        return self._get_elements(self.xpaths_to_keep)

    def _get_elements_to_discard(self):
        """
        Returns a list of lxml Elements to discard

        :returns: List of elements to discard
        :rtype: list of lxml.html.HtmlElement
        """
        return self._get_elements(self.xpaths_to_discard)

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
                # Parent element is not an explicit keep, normal process
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
        :type elt: lxml.html.HtmlElement
        :returns: True if the element is an explicit one to keep
        :rtype: bool
        """
        return elt in self.elts_to_keep

    def _is_discard(self, elt):
        """
        Returns whether an Element is an explicit one to discard or not

        :param elt: The HtmlElement to check
        :type elt: lxml.html.HtmlElement
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

    def _remove_elements(self, elts_to_remove):
        """
        Removes flagged elements from the ElementTree
        """
        for e in elts_to_remove:

            # Get the element parent
            parent = e.getparent()

            # lxml also remove the element tail, preserve it
            if e.tail and e.tail.strip():
                parent_text = parent.text or ''
                parent.text = parent_text + e.tail

            # Remove the element
            e.getparent().remove(e)
