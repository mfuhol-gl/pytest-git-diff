from pathlib import Path

from setuptools import setup

from pytest_gitdiff import __version__

HERE = Path(__file__).parent

REQUIREMENTS = (HERE / "requirements.txt").read_text().splitlines()
PACKAGE_NAME = "pytest-git-diff"

setup(
    name=PACKAGE_NAME,
    description="A tool for comparing pytest runs on different git revisions",
    install_requires=REQUIREMENTS,
    version=__version__,
    license="MIT",
    license_file="LICENSE",
    py_modules=["pytest_git_diff"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    entry_points={
        "console_scripts": ["pytest-git-diff=pytest_gitdiff.cli.main"],
    },
)
