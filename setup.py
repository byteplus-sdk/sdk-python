#!/usr/bin/env python
# Learn more: https://github.com/kennethreitz/setup.py
import os

from codecs import open

import pkg_resources
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open('requirements.txt') as f:
    install_requires = [str(req) for req in pkg_resources.parse_requirements(f)]

print(install_requires)

about = {}
with open(os.path.join(here, 'byteplus', '__version__.py'), 'r', 'utf-8') as f:
    exec(f.read(), about)

with open('README.md', 'r', 'utf-8') as f:
    readme = f.read()

print(find_packages())

print(here)

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3",
    install_requires=install_requires,
    license=about['__license__'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    project_urls={
        'Documentation': 'https://docs.byteplus.com',
        'Source': 'https://github.com/byteplus-sdk/sdk-python',
    },
)
