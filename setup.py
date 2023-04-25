# -*- coding: utf-8 -*-
from setuptools import setup

from chopper import __version__


with open("README.rst", "r") as f:
    long_description = f.read()

setup(
    name="chopper",
    version=__version__,
    description="Lib to extract html elements by preserving ancestors and cleaning CSS",
    long_description=long_description,
    author="Jurismarches",
    author_email="contact@octopusmind.info",
    url="https://github.com/jurismarches/chopper",
    packages=[
        "chopper",
        "chopper.css",
        "chopper.html",
    ],
    install_requires=[
        "cssselect>=1.2.0",
        "tinycss==0.4",
        "lxml>=4.9.1",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    test_suite="chopper.tests",
)
