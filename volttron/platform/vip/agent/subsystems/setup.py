from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

# setup(
#     name = 'pubsub in cpp',
#     ext_modules = cythonize("pubsubcpp.pyx", language="c++")
# )

extensions = [
    Extension("pubsubcpp", ["pubsubcpp.pyx"],
              language ="c++"
              ),
  ]
setup(
    name = 'pubsubcpp',
    ext_modules = cythonize(extensions)
)
