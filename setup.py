#!/usr/bin/env python

import setuptools
from distutils.core import setup


kwds = {'long_description': open('README.rst').read()}

setup(name='bitstring',
      version='4.0.0.b1',
      description='Simple construction, analysis and modification of binary data.',
      author='Scott Griffiths',
      author_email='dr.scottgriffiths@gmail.com',
      url='https://github.com/scott-griffiths/bitstring',
      download_url='https://pypi.python.org/pypi/bitstring/',
      license='The MIT License: https://www.opensource.org/licenses/mit-license.php',
      py_modules=['bitstring'],
      platforms='all',
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      **kwds
      )
