import os
from setuptools import setup
from setuptools import find_packages


__status__      = "Package"
__copyright__   = "Copyright 2022"
__license__     = "MIT License"
__version__     = "0.1.0"

# 01101100 00110000 00110000 01110000
__author__      = "Felix Geilert"


this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'readme.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='functown',
    version=__version__,
    description='Various Helper Tools to make working with azure functions easier',
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='azure functions',
    url='https://github.com/felixnext/python-functown',
    download_url='https://github.com/felixnext/python-functown/releases/tag/v0.1.0-alpha',
    author='Felix Geilert',
    license='MIT License',
    packages=find_packages(include=['functown', 'functown.*']),
    install_requires=['azure-functions', 'python-jose'],
    setup_requires=['pytest-runner', 'flake8'],
    tests_require=['pytest'],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
