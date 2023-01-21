import os
from setuptools import setup
from setuptools import find_packages
from functown import __version__
import pathlib


__status__ = "Package"
__copyright__ = "Copyright 2023"
__license__ = "MIT License"
__author__ = "Felix Geilert"


this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


def versions_in_requirements(file):
    lines = file.read().splitlines()
    versions = [line for line in lines if not line.isspace() and "--" not in line]
    return list(versions)


HERE = pathlib.Path(__file__).parent
with open(HERE / "requirements.txt") as f:
    required_list = versions_in_requirements(f)

setup(
    name="functown",
    version=__version__,
    description="Various Helper Tools to make working with azure functions easier",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="azure functions",
    url="https://github.com/felixnext/python-functown",
    download_url="https://github.com/felixnext/python-functown/releases/tag/v0.1.0-alpha",
    author="Felix Geilert",
    license="MIT License",
    packages=find_packages(include=["functown", "functown.*"]),
    install_requires=required_list,
    setup_requires=["pytest-runner", "flake8"],
    tests_require=["pytest"],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
