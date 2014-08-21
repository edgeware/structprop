from setuptools import setup, find_packages

setup(name='structprop',
      version='0.0.9',
      description='Parser for structured property config file format',
      author='Edgeware AB',
      author_email='info@edgeware.tv',
      license='MIT',
      packages=find_packages(),
      test_suite='structprop.test',
      classifiers=[
          'Intended Audience :: Developers',
          'Topic :: Software Development'
      ])
