import os
from setuptools import setup
from setuptools import find_packages
from functown import __version__
import pathlib
from glob import glob


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


def load_req(extra: str = None, all: bool = False):
    if all is True:
        reqs_files = glob(str(HERE / "requirements*.txt"))
        reqs = []
        for file in reqs_files:
            with open(file) as f:
                reqs += versions_in_requirements(f)

        # make unique
        reqs = list(set(reqs))
        return reqs

    # load regular requirements
    file = "requirements.txt"
    if extra:
        file = f"requirements-{extra}.txt"
    with open(HERE / file) as f:
        required_list = versions_in_requirements(f)
    return required_list


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
    packages=find_packages(
        include=["functown", "functown.*"],
    ),
    install_requires=load_req(),
    setup_requires=["pytest-runner", "flake8"],
    tests_require=load_req(all=True),
    extras_require={
        "flatbuffer": load_req("flatbuffer"),
        "protobuf": load_req("protobuf"),
        "insights": load_req("insights"),
        "jwt": load_req("jwt"),
        "pandas": load_req("pandas"),
    },
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
        "Programming Language :: Python :: 3.11",
    ],
)
