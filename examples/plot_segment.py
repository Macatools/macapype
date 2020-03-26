"""
.. _plot_segment:

===================================
Plot the results of a segmentation
===================================
"""

# Authors: David Meunier <david_meunier_79@hotmail.fr>

# License: BSD (3-clause)
# sphinx_gallery_thumbnail_number = 2
import os
import os.path as op

import nipype.pipeline.engine as pe

from nipype.interfaces.utility import IdentityInterface
import nipype.interfaces.io as nio

###############################################################################
# Load test data
from macapype.utils.utils_tests import load_test_data

from ..worklfows.segment_pnh_regis_T1xT2 import create_segment_pnh_T1xT2

my_path = "/hpc/crise/meunier.d/"

data_path = load_test_data("data_test_macapype", path_to = my_path)

# data file
T1_file = op.join(data_path, "sub-Apache_ses-01_T1w.nii")
T2_file = op.join(data_path, "sub-Apache_ses-01_T2w.nii")


inia_dir = load_test_data("inia19", path_to = my_path)

template = op.join(inia_dir, "inia19-t1-brain.nii")
# priors

priors = [op.join(inia_dir, "inia19-prob_1.nii"),
          op.join(inia_dir, "inia19-prob_2.nii"),
          op.join(inia_dir, "inia19-prob_0.nii")]
# template


# running workflow
segment_pnh = create_segment_pnh_T1xT2(template, priors)
segment_pnh.base_dir = my_path

segment_pnh.inputs.T1 = T1_file
segment_pnh.inputs.T2 = T2_file

val = segment_pnh.run().outputs

print(val)
