from distutils.core import setup
from Cython.Build import cythonize

setup(
    name = 'cython router',
    ext_modules = cythonize(["temp.pyx"], language="c++")
)
