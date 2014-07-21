# -*- coding: utf-8 -*-
from setuptools import setup

VERSION = '0.1.2'


setup(
    name='tree_extractor',
    version=VERSION,
    description="Lib to extract html elements by preserving ancestors and cleaning CSS",
    author=u'Jurismarchés',
    author_email='contact@jurismarches.com',
    url='https://github.com/jurismarches/tree_extractor',
    packages=[
        'tree_extractor'
    ],
    install_requires=[
        'cssselect==0.9.1',
        'tinycss==0.3',
        'lxml==3.3.5'
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tree_extractor.tests'
)
