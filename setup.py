try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='beancount-ethereum',
    version='1.2.0',
    description='Ethereum transaction importer for Beancount',
    packages=['beancount_ethereum'],
    license='GPLv3',
)
