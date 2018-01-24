import sys

from setuptools import setup, find_packages

install_requires = []

if sys.version_info < (2, 7):
    install_requires.append('ordereddict')

setup(name='structprop',
      version='0.0.10',
      description='Parser for structured property config file format',
      author='Edgeware AB',
      author_email='info@edgeware.tv',
      license='MIT',
      use_2to3=True,
      packages=find_packages(),
      test_suite='structprop.test',
      install_requires=install_requires,
      classifiers=[
          'Intended Audience :: Developers',
          'Topic :: Software Development'
      ])
