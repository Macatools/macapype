#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from setuptools import find_packages, setup

verstr = "unknown"
try:
    verstrline = open('macapype/_version.py', "rt").read()
except EnvironmentError:
    pass  # Okay, there is no version file.
else:
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(VSRE, verstrline, re.M)
    if mo:
        verstr = mo.group(1)
    else:
        raise RuntimeError("unable to find version in yourpackage/_version.py")

print("Will not build conda module")

test_deps = ['codecov', 'pytest', 'pytest-cov']
flake_deps = ['flake8']
doc_deps = ['sphinx', 'sphinx-gallery', 'sphinx_bootstrap_theme', 'numpydoc']

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="macapype",
    version=verstr,
    packages=find_packages(),
    author="macatools team",
    description="Pipeline for anatomic processing for macaque",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='BSD 3',
    entry_points={
        'console_scripts': ['segment_pnh = workflows.segment_pnh:main']},
    install_requires=requirements,
    extras_require={
        'test': test_deps + flake_deps,
        'doc': flake_deps + test_deps + doc_deps
    },
    include_package_data=True)
