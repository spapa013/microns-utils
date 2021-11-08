#!/usr/bin/env python
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='microns-utils',
    version='0.0.1',
    description='utilities for MICrONS',
    author='Stelios Papadopoulos, Christos Papadopoulos',
    author_email='spapadop@bcm.edu, cpapadop@bcm.edu',
    packages=find_packages(exclude=[]),
    install_requires=['numpy']
)