from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

extensions = [
    Extension("routercy", ["routercy.pyx"],
              include_dirs = ['/home/volttron/git/volttron-2/env/lib/python2.7/site-packages/zmq/utils',
                              '/home/volttron/git/volttron-2/env/lib/python2.7/site-packages/zmq/backend/cython'
                              ],
              language ="c++"
              ),
    Extension("routermaincy", ["routermaincy.pyx"],
              include_dirs=['/home/volttron/git/volttron-2/env/lib/python2.7/site-packages/zmq/utils',
                            '/home/volttron/git/volttron-2/env/lib/python2.7/site-packages/zmq/backend/cython'
                            ],
              language="c++"
              )
  ]
setup(
    name = 'router',
    ext_modules = cythonize(extensions)
)

# setup(
#     name = 'temp',
#     ext_modules = cythonize('temp.pyx',
#                             language="c++",
#                             include_path = ['/home/volttron/git/volttron-2/env/lib/python2.7/site-packages/zmq/utils'])
# )