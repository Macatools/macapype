#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from setuptools import find_packages
from distutils.core import setup


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


try:
    import distutils.command.bdist_conda

    setup(
        name="macapype",
        version=verstr,
        packages=find_packages(),
        author="David Meunier, Bastien Cagna",
        description="Pipeline for anatomic processing for macaque",
        license='BSD 3',
        install_requires=[
            "nipype", "nilearn", "networkx>=2.0", "pybids", "scikit-image", "slam@git+https://github.com/gauzias/slam"],
        distclass=distutils.command.bdist_conda.CondaDistribution,
        conda_buildnum=1)

except ModuleNotFoundError as e:

    print("Will not build conda module")

    setup(
        name="macapype",
        version=verstr,
        packages=find_packages(),
        author="David Meunier, Bastien Cagna",
        description="Pipeline for anatomic processing for macaque",
        license='BSD 3',
        install_requires=[
            "nipype", "nilearn", "networkx>=2.0", "pybids", "scikit-image", "slam@git+https://github.com/gauzias/slam"])

