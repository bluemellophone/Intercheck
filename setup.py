#!/usr/bin/env python
from __future__ import absolute_import, division, print_function
from setuptools import setup
from intercheck import __version__, tagline

setup(
    name='Intercheck',
    version=__version__,
    author='Jason Parham',
    author_email='bluemellophone@gmail.com',
    license='Apache v. 2.0',
    description=(tagline),
    long_description=open('README.rst').read(),
    packages=['intercheck'],
    install_requires=[
        'Flask >= 0.10.1',
        'requests >=2.9.1',
        'simplejson >= 3.8.1',
        'speedtest-cli >= 0.3.4',
        'tornado >= 4.3',
        'Sphinx >= 1.3.6',
        'sphinxcontrib-napoleon >= 0.5.0',
    ],
    entry_points={
        'console_scripts' : [
            'intercheck = intercheck:start',
        ],
    },
    keywords='Internet SpeedTest disconnect web log graph accountability',
    url='http://packages.python.org/intercheck',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache v. 2.0 License',
    ],
)
