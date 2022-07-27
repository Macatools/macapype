#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from setuptools import find_packages, setup


required_packages=[
    "nipype", "nilearn", "networkx", "pybids", "scikit-image", "nibabel==3.2.2", "numpy",
    "brain-slam"]

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

print("Will not build conda module")

setup(
    name="macapype",
    version=verstr,
    packages=find_packages(),
    author="macatools team",
    description="Pipeline for anatomic processing for macaque",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='BSD 3',
    entry_points = {
        'console_scripts': ['segment_pnh = workflows.segment_pnh:main']},
    install_requires= required_packages,
    include_package_data=True)
