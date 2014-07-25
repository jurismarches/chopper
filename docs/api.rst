API
===

`Extractor` public API
----------------------

.. py:class:: Extractor

  .. py:method:: keep(xpath)

    Adds an Xpath expression to keep

    :param str xpath: The Xpath expression to add
    :returns: The self instance
    :rtype: `Extractor`

  .. py:method:: discard(xpath)

    Adds an Xpath expression to discard

    :param str xpath: The Xpath expression to add
    :returns: The self instance
    :rtype: `Extractor`


  .. py:method:: extract(html_contents, css_contents=None, base_url=None)

    Extracts the cleaned html tree as a string and only
    css rules matching the cleaned html tree

    :param html_contents: The HTML contents to parse
    :type html_contents: str
    :param css_contents: The CSS contents to parse
    :type css_contents: str
    :param base_url: The base page URL to use for relative to absolute links
    :type base_url: str

    :returns: cleaned HTML contents or (cleaned HTML contents, cleaned CSS contents)
    :rtype: str or tuple
