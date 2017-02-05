# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""

import re
from setuptools import setup

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('backupy/backup.py').read(),
    re.M
).group(1)

with open("README.md", "rb") as f:
    long_descr = f.read().decode("utf-8")

setup(
    name="backupy",
    packages=["backupy"],
    entry_points={
        "console_scripts": ['backupy = backupy.backup:main']
    },
    version=version,
    description="Create rolling backups of a file or folder",
    long_description=long_descr,
    author="Christiaan B van Zyl",
    author_email="christiaanvanzyl@gmail.com",
    url="https://github.com/mozey/backupy",
    install_requires=[
        "sh>=1.11"
    ]
)
