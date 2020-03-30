"""
.. _plot_segment_pnh_kepkee:

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

################################################################################
### Load test data

#from macapype.utils.utils_tests import load_test_data
#from macapype.pipelines.full_segment import create_full_segment_pnh_subpipes

#my_path = "/hpc/crise/meunier.d/"

#data_path = load_test_data("data_test_macapype", path_to = my_path)

### data file
#T1_file = op.join(data_path, "sub-Apache_ses-01_T1w.nii")
#T2_file = op.join(data_path, "sub-Apache_ses-01_T2w.nii")

#from macapype.utils.utils_tests import load_test_data

#my_path = "/hpc/crise/meunier.d"

#nmt_dir = load_test_data('NMT_v1.2', path_to = my_path)
#atlasbrex_dir = load_test_data('AtlasBREX', path_to = my_path)

### running workflow
#segment_pnh = create_full_segment_pnh_subpipes(nmt_dir, atlasbrex_dir)
#segment_pnh.base_dir = my_path

#segment_pnh.inputs.inputnode.T1 = T1_file
#segment_pnh.inputs.inputnode.T2 = T2_file

#segment_pnh.run()


##############################################################################
# Testing plot in local

my_path = "/home/INT/meunier.d/Data/Primavoice/"
wf_path = os.path.join(my_path, "segment_pnh_subpipes")

T1_file = op.join(wf_path, "preproc", "sub-Apache_ses-01_T1w_cropped.nii.gz")
assert os.path.exists(T1_file)

# displaying results
output_img = os.path.join(wf_path, "outfile.png")
cmd = "fsleyes render --outfile {} --size 800 600 {}".format(output_img, T1_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(output_img)
plt.figure(figsize=(16, 16))
plt.imshow(img)
plt.axis('off')
plt.show()

###############################################################################
# brain extraction results
#==========================

# At the end 1st part pipeline

mask_file = os.path.join(
    wf_path, "devel_atlas_brex", "smooth_mask",
    "sub-Apache_ses-01_T1w_cropped_maths_noise_corrected_brain_bin_bin.nii.gz")

output_img_overlay = os.path.join(wf_path,"outfile_overlay.png")
#cmd = "fsleyes render --outfile {} --size 800 600 {} -ot mask -o -a 50 {}".format(output_img_overlay, mask_file, T1_file)
cmd = "fsleyes render --outfile {} --size 800 600 {} {} -a 50".format(output_img_overlay, T1_file, mask_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(output_img_overlay)
plt.figure(figsize=(16, 16))
plt.imshow(img)
plt.axis('off')
plt.show()

##############################################################################
#Second part of the pipeline
##############################################################################

#register template to subject
#==============================



###############################################################################
# segmentation results
#==========================

seg_pipe = op.join(wf_path, "segment_devel_NMT_sub_align")

## showing mask
#reg_T1_file = os.path.join(
#    seg_pipe,"register_NMT_pipe", "norm_intensity/",
#    "sub-Apache_ses-01_T1w_cropped_noise_corrected_maths_masked_corrected.nii.gz")

reg_T1_file = os.path.join(
    seg_pipe,"segment_atropos_pipe", "deoblique/",
    "sub-Apache_ses-01_T1w_cropped_noise_corrected_maths_masked_corrected.nii.gz")

outfile_deoblique = os.path.join(wf_path,"outfile_deoblique.png")
cmd = "fsleyes render --outfile {} --size 800 600 {}".format(outfile_deoblique, reg_T1_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(outfile_deoblique)
plt.figure(figsize=(8, 8))
plt.imshow(img)
plt.axis('off')
plt.show()

# showing tissues
#gm_file = os.path.join(seg_pipe, "segment_atropos_pipe", "seg_at", "NMT_segmentation_GM_allineate.nii.gz")
#wm_file = os.path.join(seg_pipe, "segment_atropos_pipe", "seg_at", "NMT_segmentation_WM_allineate.nii.gz")
#csf_file = os.path.join(seg_pipe, "segment_atropos_pipe", "seg_at", "NMT_segmentation_CSF_allineate.nii.gz")

tissue_file = os.path.join(seg_pipe, "segment_atropos_pipe", "seg_at", "segment_Segmentation.nii.gz")
gm_file = os.path.join(seg_pipe, "segment_atropos_pipe", "seg_at", "segment_SegmentationPosteriors01.nii.gz")
wm_file = os.path.join(seg_pipe, "segment_atropos_pipe", "seg_at", "segment_SegmentationPosteriors02.nii.gz")
csf_file = os.path.join(seg_pipe, "segment_atropos_pipe", "seg_at", "segment_SegmentationPosteriors03.nii.gz")

###############################################################################
# gm as red
#outfile_seg_red = os.path.join(wf_path,"outfile_seg_red.png")
#cmd = "fsleyes render --outfile {} --size 800 600 {} {} -cm red -a 10".format(outfile_seg_red, reg_T1_file, gm_file)
#os.system(cmd)

#import matplotlib.pyplot as plt  # noqa
#img = plt.imread(outfile_seg_red)
#plt.figure(figsize=(8, 8))
#plt.imshow(img)
#plt.axis('off')
#plt.show()

outfile_deoblique = os.path.join(wf_path,"outfile_deoblique.png")
cmd = "fsleyes render --outfile {} --size 800 600 {} {} -dr 0 4 -cm random -a 30".format(outfile_deoblique, reg_T1_file, tissue_file)
os.system(cmd)

import matplotlib.pyplot as plt  # noqa
img = plt.imread(outfile_deoblique)
plt.figure(figsize=(8, 8))
plt.imshow(img)
plt.axis('off')
plt.show()


################################################################################
## all different colors



#outfile_deoblique = os.path.join(wf_path,"outfile_deoblique.png")
#cmd = "fsleyes render --outfile {} --size 800 600 {}".format(outfile_deoblique, reg_T1_file)
#os.system(cmd)

#import matplotlib.pyplot as plt  # noqa
#img = plt.imread(outfile_deoblique)
#plt.figure(figsize=(8, 8))
#plt.imshow(img)
#plt.axis('off')
#plt.show()

#outfile_seg_col = os.path.join(wf_path,"outfile_seg_col.png")
#cmd = "fsleyes render --outfile {} --size 800 600 {} -cm red -a 10 {} -cm blue -a 10 {} -cm green -a 10".format(outfile_seg_col, gm_file, wm_file, csf_file)
##cmd = "fsleyes render --outfile {} --size 800 600 {} {} -cm red".format(outfile_seg_col, reg_T1_file, gm_file)
#os.system(cmd)

#import matplotlib.pyplot as plt  # noqa
#img = plt.imread(outfile_seg_col)
#plt.figure(figsize=(8, 8))
#plt.imshow(img)
#plt.axis('off')
#plt.show()
