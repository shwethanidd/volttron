from distutils.core import setup
from Cython.Build import cythonize

setup(
    name = 'pubsub in cpp',
    ext_modules = cythonize("pubsubcpp.pyx", language="c++")
)
