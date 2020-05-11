#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

import re

verstr = "unknown"
try:
    verstrline = open('macapype/_version.py', "rt").read()
except EnvironmentError:
    pass # Okay, there is no version file.
else:
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(VSRE, verstrline, re.M)
    if mo:
        verstr = mo.group(1)
    else:
        raise RuntimeError("unable to find version in yourpackage/_version.py")



setup(
    name="macapype",
    version=verstr,
    packages=find_packages(),
    author="David Meunier, Bastien Cagna",
    description="Pipeline for anatomic processing for macaque",
    license='BSD 3',
    install_requires=["nipype", "networkx>=2.0", "pybids"]
)
