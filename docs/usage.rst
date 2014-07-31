Usage
=====

Create the |extractor| instance
-------------------------------

First, you need to import the |extractor| class :

.. code-block:: python

  from chopper.extractor import Extractor


Then you can create an |extractor| instance by explicitly instantiating one or by directly using |keep| and |discard| class methods :

.. code-block:: python

  from chopper.extractor import Extractor

  # Instantiate style
  extractor = Extractor().keep('//div').discard('//a')

  # Class method style
  extractor = Extractor.keep('//div').discard('//a')


Add Xpath expressions
---------------------

The |extractor| instance allows you to chain multiple |keep| and |discard|

.. code-block:: python

  from chopper.extractor import Extractor

  e = Extractor.keep('//div[p]').discard('//span').discard('//a').keep('strong')


Extract contents
----------------

Once your |extractor| instance is created you can call the |extract| method on it. The |extract| method takes at least one argument that is the HTML to parse.

If you want to also parse CSS, pass it as the second argument.

.. warning::

  Depending on the CSS content size, CSS parsing and cleaning can be really slow compared
  to HTML parsing and cleaning.

.. code-block:: python

  from chopper.extractor import Extractor

  HTML = """
  <html>
    <head>
      <title>Hello world !</title>
    </head>
    <body>
      <header>This is the header</header>
      <div>
        <p><span>Main </span>content</p>
        <a href="/">See more</a>
      </div>
      <footer>This is the footer</footer>
    </body>
  </html>
  """

  CSS = """
  a { color: blue; }
  p { color: red; }
  span { border: 1px solid red; }
  body { background-color: green; }
  """

  # Create the Extractor
  e = Extractor.keep('//div[p]').discard('//span').discard('//a')

  # Parse HTML only
  html = e.extract(HTML)

  >>> html
  """
  <html>
    <body>
      <div>
        <p>content</p>
      </div>
    </body>
  </html>
  """

  # Parse HTML & CSS
  html, css = e.extract(HTML, CSS)

  >>> html
  """
  <html>
    <body>
      <div>
        <p>content</p>
      </div>
    </body>
  </html>
  """

  >>> css
  """
  p{color:red;}
  body{background-color:green;}
  """


Convert relative links to absolute ones
---------------------------------------

Chopper can also convert relative links to absolute ones. To do so, simply use the `base_url` keyword arguments on the |extract| method.

.. code-block:: python

  from chopper.extractor import Extractor

  HTML = """
  <html>
    <head>
      <title>Hello world !</title>
    </head>
    <body>
      <div>
        <p>content</p>
        <a href="page.html">See more</a>
      </div>
    </body>
  </html>
  """

  html = Extractor.keep('//a').extract(HTML, base_url='http://test.com/path/index.html')

  >>> html
  """
  <html>
    <body>
      <div>
        <a href="http://test.com/path/page.html">See more</a>
      </div>
    </body>
  </html>
  """


.. |extractor| replace:: :py:class:`Extractor`
.. |keep| replace:: :py:meth:`Extractor.keep`
.. |discard| replace:: :py:meth:`Extractor.discard`
.. |extract| replace:: :py:meth:`Extractor.extract`
