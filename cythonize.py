#!/usr/bin/env python
from distutils.core import setup
from distutils.extension import Extension

from Cython.Distutils import build_ext
from Cython.Build import cythonize

macros = [('PYREX_WITHOUT_ASSERTIONS', None)]
cmdclass = {}
print("Compiling with Cython")
ext_modules = [Extension('_cbitstring', ["_cbitstring.pyx"], define_macros=macros)]
cythonize(ext_modules)
cmdclass.update({'build_ext': build_ext})

setup(name='bitstring',
      ext_modules = ext_modules,
      )

