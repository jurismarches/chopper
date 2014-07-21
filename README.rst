tree_extractor
==============

Extracts html contents by preserving ancestors and clean CSS

Usage
-----

.. code-block:: python

  from tree_extractor import TreeExtractor

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

.. code-block::

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
