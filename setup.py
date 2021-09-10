from setuptools import setup, find_packages

setup(name='structprop',
      version='0.0.11',
      description='Parser for structured property config file format',
      author='Edgeware AB',
      author_email='info@edgeware.tv',
      license='MIT',
      packages=find_packages(),
      install_requires=['six'],
      classifiers=[
          'Intended Audience :: Developers',
          'Topic :: Software Development'
      ])
