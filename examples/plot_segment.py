"""
.. _plot_segment:

===================================
Plot the results of a segmentation
===================================
"""

# Authors: David Meunier <david_meunier_79@hotmail.fr>

# License: BSD (3-clause)
# sphinx_gallery_thumbnail_number = 2
import os.path as op

import nipype.pipeline.engine as pe

from nipype.interfaces.utility import IdentityInterface
import nipype.interfaces.io as nio

###############################################################################
# Check if data are available
from macapype.utils.utils_tests import load_test_data

data_path = load_test_data("data_test_macapype", path_to = "/hpc/crise/meunier.d/")
