:orphan:

.. _derivatives:


************
Introduction
************

Depending on the options provided by command line and params.json, different files will ouput

Derivatives will be output if option ``-deriv`` is provided to the command line (See `Commands <commands>`):

All files are by default in stereo space; if option ``-pad`` is provided to the command line (See `Commands <commands>`), files in native  will also be output.

****************
Data Preparation
****************

Native
------

Original files (possibly after reorientation and avereging):

sub-Stevie_ses-01_space-native_T1w.nii.gz
sub-Stevie_ses-01_space-native_T2w.nii.gz

If -pad is defined in command line (See `Commands <commands>`):

sub-Stevie_ses-01_space-native_desc-denoised_T1w.nii.gz
sub-Stevie_ses-01_space-native_desc-denoised_T2w.nii.gz
sub-Stevie_ses-01_space-native_desc-debiased_T1w.nii.gz
sub-Stevie_ses-01_space-native_desc-debiased_T2w.nii.gz

**NB:** Both denoise and debias are optional

Stereo
------

Original files in template space:

sub-Stevie_ses-01_space-stereo_T1w.nii.gz
sub-Stevie_ses-01_space-stereo_T2w.nii.gz

After some preprocessing :

sub-Stevie_ses-01_space-stereo_desc-denoised_T1w.nii.gz
sub-Stevie_ses-01_space-stereo_desc-denoised_T2w.nii.gz
sub-Stevie_ses-01_space-stereo_desc-debiased_T1w.nii.gz
sub-Stevie_ses-01_space-stereo_desc-debiased_T2w.nii.gz

**NB:** Both denoise and debias are optional

Transformations
---------------

sub-Stevie_ses-01_space-native_target-stereo_affine.txt
sub-Stevie_ses-01_space-stereo_target-native_affine.txt

****************
Brain extraction
****************

Brain mask:

sub-Stevie_ses-01_space-stereo_desc-brain_mask.nii.gz
sub-Stevie_ses-01_space-native_desc-brain_mask.nii.gz


******************
Brain segmentation
******************

Brainmasked files after T1*T2 Bias correction:

sub-Stevie_ses-01_space-stereo_desc-debiased_desc-brain_T1w.nii.gz
sub-Stevie_ses-01_space-stereo_desc-debiased_desc-brain_T2w.nii.gz

sub-Stevie_ses-01_space-native_desc-debiased_desc-brain_T2w.nii.gz
sub-Stevie_ses-01_space-native_desc-debiased_desc-brain_T1w.nii.gz

Segmentated files as probability tisses:

sub-Stevie_ses-01_space-stereo_label-WM_probseg.nii.gz
sub-Stevie_ses-01_space-stereo_label-GM_probseg.nii.gz
sub-Stevie_ses-01_space-stereo_label-CSF_probseg.nii.gz

sub-Stevie_ses-01_space-native_label-WM_probseg.nii.gz
sub-Stevie_ses-01_space-native_label-GM_probseg.nii.gz
sub-Stevie_ses-01_space-native_label-CSF_probseg.nii.gz

Segmentated files as indexed tisses:

sub-Stevie_ses-01_space-stereo_desc-brain_dseg.nii.gz
sub-Stevie_ses-01_space-native_desc-brain_dseg.nii.gz

Segmented files in mrtrix format:

sub-Stevie_ses-01_space-stereo_desc-5tt_dseg.nii.gz
sub-Stevie_ses-01_space-native_desc-5tt_dseg.nii.gz


White matter + Gray matter binary mask and corresponding mesh:

sub-Stevie_ses-01_space-stereo_desc-wmgm_mask.nii.gz
sub-Stevie_ses-01_space-native_desc-wmgm_mask.nii.gz

sub-Stevie_ses-01_desc-wmgm_mask.stl

