from lxml import html


class TreeBuilderMixin(object):
    """
    Adds a '_build_tree' method that returns an lxml HtmlElement
    from a HTML contents string
    """
    def _build_tree(self, html_contents):
        """
        Returns a HTML tree from the HTML contents

        :returns: The parsed lxml element
        :rtype: lxml.html.HtmlElement
        """
        return html.fromstring(html_contents)
