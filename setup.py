# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""

import re
from setuptools import setup

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('backup/backup.py').read(),
    re.M
).group(1)

with open("README.md", "rb") as f:
    long_descr = f.read().decode("utf-8")

setup(
    name="backup.py",
    packages=["backup"],
    entry_points={
        "console_scripts": ['bootstrap = backup.backup:main']
    },
    version=version,
    description="Create rolling backups of a file or folder",
    long_description=long_descr,
    author="Christiaan B van Zyl",
    author_email="christiaanvanzyl@gmail.com",
    url="https://github.com/mozey/backup.py",
    install_requires=[
        "sh==1.11"
    ]
)
