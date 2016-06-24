from distutils.core import setup
from Cython.Build import cythonize

setup(
    name = 'Dict test in cy',
    ext_modules = cythonize("dicttest2.pyx")
)
