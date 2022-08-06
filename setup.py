from pathlib import Path
from setuptools import setup

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='beancount-ethereum',
    version='1.4.3',
    description='Ethereum transaction importer for Beancount',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['beancount_ethereum'],
    license='GPLv3',
    author='xuhcc',
    url='https://github.com/xuhcc/beancount-ethereum-importer',
    download_url='https://github.com/xuhcc/beancount-ethereum-importer',
    install_requires=requirements,
    entry_points={'console_scripts': 'beancount-ethereum=beancount_ethereum.__main__:main'},
    python_requires='>=3.6',  # This is the version beancount requires
    keyword='Beancount Ethereum'
)
