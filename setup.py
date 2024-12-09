#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Pydra: Dataflow Engine

"""
import sys
from setuptools import setup

import re

def _get_version():

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
    return verstr

if __name__ == "__main__":
    setup(
        version=_get_version()
    )
