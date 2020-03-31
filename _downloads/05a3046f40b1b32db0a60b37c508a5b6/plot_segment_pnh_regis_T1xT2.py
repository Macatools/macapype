"""
.. _plot_segment_pnh_regis_T1xT2:

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
# Load test data and run
#========================

from macapype.utils.utils_tests import load_test_data

from macapype.pipelines.full_segment import create_full_segment_pnh_T1xT2
from macapype.utils.utils_spm import format_spm_priors

# data file

#my_path = "/hpc/crise/meunier.d/"
#data_path = load_test_data("data_test_macapype", path_to = my_path)

#T1_file = op.join(data_path, "sub-Apache_ses-01_T1w.nii")
#T2_file = op.join(data_path, "sub-Apache_ses-01_T2w.nii")


#inia_dir = load_test_data("inia19", path_to = my_path)

## template
#template = op.join(inia_dir, "inia19-t1-brain.nii")

## priors

#priors = [op.join(inia_dir, "inia19-prob_1.nii"),
          #op.join(inia_dir, "inia19-prob_2.nii"),
          #op.join(inia_dir, "inia19-prob_0.nii")]


## running workflow
#segment_pnh = create_full_segment_pnh_T1xT2(template, format_spm_priors(priors))
#segment_pnh.base_dir = my_path

#segment_pnh.inputs.inputnode.T1 = T1_file
#segment_pnh.inputs.inputnode.T2 = T2_file

#segment_pnh.write_graph(graph2use="colored")
#segment_pnh.run()

###############################################################################
# Testing plot in local
#======================

my_path = "/home/INT/meunier.d/Data/Primavoice/"

# displaying results
wf_path = os.path.join(my_path, "T1xT2_segmentation_pipeline")
bet_path = os.path.join(wf_path, "bet")

T1_file = op.join(bet_path, "sub-Apache_ses-01_T1w_cropped.nii.gz")
assert os.path.exists(T1_file)

outfile_T1 = os.path.join(wf_path, "outfile_T1.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(outfile_T1, T1_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(outfile_T1)
plt.figure(figsize=(16, 16))
plt.imshow(img)
plt.axis('off')
plt.show()


###############################################################################
# Correct bias results
#==========================

debiased_T1_file = op.join(wf_path, "debias",
                           "sub-Apache_ses-01_T1w_cropped_debiased.nii.gz")


debiased_T1 = os.path.join(wf_path,"debiased_T1.png")

cmd = "fsleyes render --outfile {} --size 1800 600 {}".format(debiased_T1, debiased_T1_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(outfile_T1)

fig, axs = plt.subplots(2, 1, figsize=(24, 16))
axs[0].imshow(plt.imread(outfile_T1))
axs[0].axis('off')

axs[1].imshow(plt.imread(debiased_T1))
axs[1].axis('off')
plt.show()

###############################################################################
# brain extraction results
#==========================

mask_file = op.join(bet_path, "sub-Apache_ses-01_T1w_BET_mask_cropped.nii.gz")

# Bet results
output_img_overlay = os.path.join(wf_path,"outfile_overlay.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -a 50".format(output_img_overlay, T1_file, mask_file)
os.system(cmd)


import matplotlib.pyplot as plt  # noqa
img = plt.imread(output_img_overlay)
plt.figure(figsize=(16, 16))
plt.imshow(img)
plt.axis('off')
plt.show()

###############################################################################
#registration results
#=====================

reg_T1_file = op.join(wf_path,"reg", "sub-Apache_ses-01_T1w_cropped_debiased_brain_FLIRT-to_inia19-t1-brain.nii")

# showing mask
segment_path = os.path.join(wf_path, "old_segment_extraction_pipe")

filled_mask_file = os.path.join(segment_path, "fill_holes", "c1sub-Apache_ses-01_T1w_cropped_debiased_brain_FLIRT-to_inia19-t1-brain_thresh_maths_maths_dil_ero_filled.nii.gz")

#filled_mask_file = os.path.join(segment_path, "fill_holes_dil", "c1sub-Apache_ses-01_T1w_cropped_debiased_brain_FLIRT-to_inia19-t1-brain_thresh_maths_maths_dil_filled.nii.gz")

outfile_seg_mask = os.path.join(wf_path,"outfile_seg_mask.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -a 50".format(outfile_seg_mask, reg_T1_file, filled_mask_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(outfile_seg_mask)
plt.figure(figsize=(16, 16))
plt.imshow(img)
plt.axis('off')
plt.show()

###############################################################################
#segmentation results
#=====================

gm_file = os.path.join(segment_path, "threshold_gm", "c1sub-Apache_ses-01_T1w_cropped_debiased_brain_FLIRT-to_inia19-t1-brain_thresh.nii.gz")
wm_file = os.path.join(segment_path, "threshold_wm", "c2sub-Apache_ses-01_T1w_cropped_debiased_brain_FLIRT-to_inia19-t1-brain_thresh.nii.gz")
csf_file = os.path.join(segment_path, "threshold_csf", "c3sub-Apache_ses-01_T1w_cropped_debiased_brain_FLIRT-to_inia19-t1-brain_thresh.nii.gz")

outfile_seg_col = os.path.join(wf_path,"outfile_seg_col.png")
cmd = "fsleyes render --outfile {} --size 1800 600 {} {} {} {}".format(outfile_seg_col, reg_T1_file, gm_file, wm_file, csf_file)
cmd = "fsleyes render --outfile {} --size 1800 600 {} {} -cm red {} -cm blue {} -cm green".format(outfile_seg_col, reg_T1_file, gm_file, wm_file, csf_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(outfile_seg_col)
plt.figure(figsize=(16, 16))
plt.imshow(img)
plt.axis('off')
plt.show()
