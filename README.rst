|axe| Chopper
=============

|pypi| |github-actions| |readthedocs|

Chopper is a tool to extract elements from HTML by preserving ancestors and CSS rules.

Compatible with Python >= 3.8


Installation
------------

``pip install chopper``


Full documentation
------------------

http://chopper.readthedocs.org/en/latest/


Quick start
-----------

.. code-block:: python

  from chopper.extractor import Extractor

  HTML = """
  <html>
    <head>
      <title>Test</title>
    </head>
    <body>
      <div id="header"></div>
      <div id="main">
        <div class="iwantthis">
          HELLO WORLD
          <a href="/nope">Do not want</a>
        </div>
      </div>
      <div id="footer"></div>
    </body>
  </html>
  """

  CSS = """
  div { border: 1px solid black; }
  div#main { color: blue; }
  div.iwantthis { background-color: red; }
  a { color: green; }
  div#footer { border-top: 2px solid red; }
  """

  extractor = Extractor.keep('//div[@class="iwantthis"]').discard('//a')
  html, css = extractor.extract(HTML, CSS)

The result is :

.. code-block:: python

  >>> html
  """
  <html>
    <body>
      <div id="main">
        <div class="iwantthis">
          HELLO WORLD
        </div>
      </div>
    </body>
  </html>"""

  >>> css
  """
  div{border:1px solid black;}
  div#main{color:blue;}
  div.iwantthis{background-color:red;}
  """

.. |axe| image:: http://icons.iconarchive.com/icons/aha-soft/desktop-halloween/32/Hatchet-icon.png
.. |pypi| image:: http://img.shields.io/pypi/v/chopper.svg?style=flat
    :target: https://pypi.python.org/pypi/chopper
.. |github-actions| image:: https://github.com/jurismarches/chopper/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/jurismarches/chopper/actions/
.. |readthedocs| image:: https://readthedocs.org/projects/chopper/badge/?version=latest
    :target: http://chopper.readthedocs.org/en/latest/
