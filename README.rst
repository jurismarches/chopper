Chopper
=======

.. image:: https://travis-ci.org/jurismarches/chopper.svg?branch=master
    :target: https://travis-ci.org/jurismarches/chopper
.. image:: https://coveralls.io/repos/jurismarches/chopper/badge.png
    :target: https://coveralls.io/r/jurismarches/chopper

Extracts html contents by preserving ancestors and clean CSS

Compatible with Python >= 2.6, <= 3.4

Installation
------------

``pip install tree-extractor``

Usage
-----

.. code-block:: python

  from chopper import TreeExtractor

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

  extractor = TreeExtractor().keep('//div[@class="iwantthis"]').discard('//a')
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
