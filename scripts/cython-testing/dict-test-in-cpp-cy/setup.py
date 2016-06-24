from distutils.core import setup
from Cython.Build import cythonize

setup(
    name = 'Dict test with cpp implementation',
    ext_modules = cythonize("dicttest3.pyx", language="c++")
)
