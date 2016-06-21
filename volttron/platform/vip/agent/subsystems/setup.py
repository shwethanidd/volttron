from distutils.core import setup
from Cython.Build import cythonize

setup(
    name = 'Cy Pub Sub',
    ext_modules = cythonize("pubsubcyht.pyx")
)
