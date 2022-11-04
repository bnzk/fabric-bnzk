import os
from setuptools import setup, find_packages
import fabric_bnzk as app


def read(fname):
    # read the contents of a text file
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


install_requires = [
    'fab-classic',
]


setup(
    name="fabric-bnzk",
    version=app.__version__,
    description=read('DESCRIPTION'),
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    license='The MIT License',
    platforms=['OS Independent'],
    keywords='fabric',
    author='Ben Stähli',
    author_email='bnzk@bnzk.ch',
    url="https://github.com/bnzk/fabric-bnzk",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
)
