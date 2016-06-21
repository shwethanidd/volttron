from distutils.core import setup
from Cython.Build import cythonize

setup(
    name = 'Fast Integrate',
    ext_modules = cythonize("dicttest3.pyx", language="c++")
)
