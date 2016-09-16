from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

#LD_LIBRARY_PATH need to be set
setup(
    ext_modules = cythonize([
        Extension("queue", ["queue.pyx"],
                  include_dirs = ['/usr/local/include'],
                  libraries=["calg"],
                  library_dirs=['/usr/local/lib'])
        ])
)