#!/bin/tcsh
# affine alignment of individual dataset to D99/NMT/any template
#
# usage:
#    NMT_subject_align.csh dset template_dset [segmentation_dset]
#
# example:
#    tcsh -x NMT_subject_align.csh macaque1+orig \
#	../NMT.nii.gz 				\
#	${atlas_dir}/D99_atlas_1.2a_al2NMT.nii.gz
#
set atlas_dir = "../.."
if ("$#" <  "2") then
   echo "usage:"
   echo "   NMT_subject_align.csh dset template_dset segmentation_dset"
   echo
   echo "example:"
   echo " tcsh NMT_subject_align.csh macaque1+orig \"
   echo "   ../NMT.nii.gz			  \"
   echo "   ${atlas_dir}/D99_atlas_1.2a_al2NMT.nii.gz"
   echo
   echo "Note only the dset and template_dset are required. If no segmentation"
   echo "is given, then only the alignment steps are performed."
   echo
   echo
   echo "NMT_subject_align provides multiple outputs to assist in registering your anatomicals and associated MRI data to the NMT:"
   echo "- Subject scan registered to the NMT"
   echo "	+ **mydset_shft.nii.gz** - dataset center aligned to the NMT center"
   echo "	+ **mydset_shft_al2std.nii.gz** - dataset affine aligned to the NMT"
   echo "	+ **mydset_shft_aff.nii.gz** - dataset affine aligned to the NMT and on the NMT grid"
   echo "	+ **mydset_warp2std.nii.gz** - dataset nonlinearly warped to the NMT"
   echo "-Registration parameters for Alignment to NMT"
   echo "	+ **mydset_composite_linear_to_NMT.1D** - combined affine transformations to the NMT"
   echo "	+ **mydset_shft_WARP.nii.gz** - warp deformations to the NMT from nonlinear alignment only"
   echo "-Registration parameters for NMT Alignment to Subject"
   echo "	+ **mydset_composite_linear_to_NMT_inv.1D** - inverse of mydset_composite_linear_to_NMT.1D"
   echo "	+ **mydset_shft_WARPINV.nii.gz** - inverse of mydset_shft_WARP.nii.gz"
   echo "-D99 Atlas Aligned to Single Subject (Optional)"
   echo "	+ **mask_in_mydset.nii.gz** - D99 Atlas or other mask aligned to native scan"
   echo "***-NOTE: NMT_subject_align.csh requires the AFNI software package to run correctly***"
   echo
   echo " Here all occurrences of mydset in the output file names would be replaced"
   echo "    with the name of your dataset"
   exit
endif

setenv AFNI_COMPRESSOR GZIP

set dset = $1
set base = $2
if ("$#" < "3") then
   set segset = ""
else
   set segset = $3
endif

# optional resample to template resolution and use that
# set finalmaster = `@GetAfniPrefix $base`
set finalmaster = $dset

# get the non-NIFTI name out, dset+ , dset.nii, dset.nii.gz all -> 'dset'
set dsetprefix = `@GetAfniPrefix $dset`
set dsetprefix = `basename $dsetprefix .gz`
set dsetprefix = `basename $dsetprefix .nii`

# which afni view is used even if NIFTI dataset is used as base
# usually +tlrc
#set baseview = `3dinfo -av_space $base`

# this fails for AFNI format, but that's okay!
#3dcopy $dset $dsetprefix
# get just the first occurrence if both +orig, +tlrc
#set dset = ( $dsetprefix+*.HEAD )
#set dset = $dset[1]

# this fails for NIFTI format, but that's okay!
3dAFNItoNIFTI -prefix ${dsetprefix}.nii.gz ${dset}
set dset = ${dsetprefix}.nii.gz


set origdsetprefix = $dsetprefix

if ($segset != "") then
   #set segsetprefix = `@GetAfniPrefix $segset`
   set segsetdir = `dirname $segset`
   echo $segset |grep D99
   if ($status == 0) then
      set segname = D99
   else
      set segname = atlas
   endif
endif
# put the center of the dataset on top of the center of the template
@Align_Centers -base $base -dset $dset

# keep a copy of the inverse translation too
# (should just be negation of translation column)
cat_matvec ${dsetprefix}_shft.1D -I > ${dsetprefix}_shft_inv.1D

#set origview = `@GetAfniView $dset`
set dset = ${dsetprefix}_shft.nii.gz
set dsetprefix = ${dsetprefix}_shft

# figure out short name for template to insert into output files
echo $base |grep NMT
if ($status == 0) then
   set templatename = NMT
else
   set templatename = template
endif

# goto apply_warps

# do affine alignment with lpa cost
# using dset as dset2 input and the base as dset1
# (the base and source are treated differently
# by align_epi_anats resampling and by 3dAllineate)
align_epi_anat.py -dset2 $dset -dset1 $base -overwrite -dset2to1 -cost lpa -rigid_body \
    -giant_move -suffix _al2std -dset1_strip None -dset2_strip None
#
3dAFNItoNIFTI -prefix ${dsetprefix}_al2std.nii.gz ${dsetprefix}_al2std+orig
rm ${dsetprefix}_al2std+orig.*

## put affine aligned data on template grid
# similar to al2std dataset but with exactly same grid
3dAllineate -1Dmatrix_apply ${dsetprefix}_al2std_mat.aff12.1D \
    -prefix ${dsetprefix}_aff.nii.gz -base $base -master BASE         \
    -source $dset -overwrite

# affinely align to template
#  (could let auto_warp.py hande this, but AUTO_CENTER option might be needed)
# @auto_tlrc -base $base -input $dset -no_ss -init_xform AUTO_CENTER

# !!! Now skipping cheap skullstripping !!!
#   didn't work for macaques with very different size brains. V1 got cut off
#   probably could work with dilated mask
# "cheap" skullstripping with affine registered dataset
#  the macaque brains are similar enough that the affine seems to be sufficient here
#  for skullstripping
# 3dcalc -a ${dsetprefix}_aff+tlrc. -b $base -expr 'a*step(b)'   \
#    -prefix ${dsetprefix}_aff_ns -overwrite


# nonlinear alignment of affine skullstripped dataset to template
#  by default,the warp and the warped dataset are computed
#  by using "-qw_opts ", one could save the inverse warp and do extra padding
#  with -qw_opts '-iwarp -expad 30'
# change qw_opts to remove max_lev 2 for final   ********************
rm -rf awpy_${dsetprefix}
auto_warp.py -base $base -affine_input_xmat ID -qworkhard 0 2 \
   -input ${dsetprefix}_aff.nii.gz -overwrite \
   -output_dir awpy_${dsetprefix} -qw_opts -iwarp


apply_warps:
# the awpy has the result dataset, copy the warped data, the warp, inverse warp
# don't copy the warped dataset - combine the transformations instead below
# cp awpy_${dsetprefix}/${dsetprefix}_aff.aw.nii ./${dsetprefix}_warp2std.nii
cp awpy_${dsetprefix}/anat.un.qw_WARP.nii ${dsetprefix}_WARP.nii
cp awpy_${dsetprefix}/anat.un.qw_WARPINV.nii ${dsetprefix}_WARPINV.nii

# if the datasets are compressed, then copy those instead
# note - not using the autowarped dataset, just the WARP
#  see 3dNwarpApply just below
# cp awpy_${dsetprefix}/${dsetprefix}_aff.aw.nii.gz ./${dsetprefix}_warp2std.nii.gz
cp awpy_${dsetprefix}/anat.un.qw_WARP.nii.gz  ./${dsetprefix}_WARP.nii.gz
cp awpy_${dsetprefix}/anat.un.qw_WARPINV.nii.gz ${dsetprefix}_WARPINV.nii.gz
# compress these copies (if not already compressed)
# gzip -f ${dsetprefix}_warp2std.nii ${dsetprefix}_WARP.nii
gzip -f ${dsetprefix}_WARP.nii ${dsetprefix}_WARPINV.nii

# combine nonlinear and affine warps for dataset warped to standard template space
#   **** mod - DRG 07 Nov 2016
3dNwarpApply -prefix ${origdsetprefix}_warp2std.nii.gz                      \
   -nwarp "${dsetprefix}_WARP.nii.gz ${dsetprefix}_al2std_mat.aff12.1D" \
   -source $dset -master $base

rm -rf awpy_${dsetprefix}

# compute the inverse of the affine alignment transformation - all 12 numbers
#cat_matvec ${dsetprefix}_al2std_mat.aff12.1D >! ${dsetprefix}_al2std_mat.aff12.1D
cat_matvec -ONELINE ${dsetprefix}_al2std_mat.aff12.1D -I >! ${dsetprefix}_inv_al2std_mat.aff12.1D

# combine shft and affine 1D files for composite linear transformation to template space
cat_matvec -ONELINE ${dsetprefix}.1D ${dsetprefix}_al2std_mat.aff12.1D > ${origdsetprefix}_composite_linear_to_NMT.1D
#Now create the inverse composite warp from NMT to subject space
cat_matvec -ONELINE ${dsetprefix}_inv.1D ${dsetprefix}_inv_al2std_mat.aff12.1D > ${origdsetprefix}_composite_linear_to_NMT_inv.1D

 # warp segmentation from atlas back to the original macaque space
 #  of the input dataset (compose overall warp when applying)
 #  note - if transforming other datasets like the template
 #    back to the same native space, it will be faster to compose
 #    the warp separately with 3dNwarpCat or 3dNwarpCalc rather
 #    than composing it for each 3dNwarpApply
 if ($segset != "") then
    3dNwarpApply -ainterp NN -short -overwrite -nwarp \
       ${dsetprefix}_WARPINV.nii.gz  -overwrite \
       -source $segset -master ${dsetprefix}_aff.nii.gz -prefix ${segname}_in_${origdsetprefix}_nl.nii.gz
    3dAllineate -source ${segname}_in_${origdsetprefix}_nl.nii.gz -base ${origdsetprefix}.nii.gz \
    	-final NN -1Dmatrix_apply ${origdsetprefix}_composite_linear_to_NMT_inv.1D -prefix ${segname}_in_${origdsetprefix}.nii.gz
    rm ${segname}_in_${origdsetprefix}_nl.nii.gz

    # change the datum type to byte to save space
    # this step also gets rid of the shift transform in the header
    3dcalc -a ${segname}_in_${origdsetprefix}.nii.gz -expr a -datum byte -nscale \
       -overwrite -prefix ${segname}_in_${origdsetprefix}.nii.gz

    # copy segmentation information from atlas to this native-space
    #   segmentation dataset and mark to be shown with integer colormap
    3drefit -cmap INT_CMAP ${segname}_in_${origdsetprefix}.nii.gz
    3drefit -copytables $segset ${segname}_in_${origdsetprefix}.nii.gz
    #mv ${segsetdir}/${segname}_in_${origdsetprefix}.nii.gz ./${segname}_in_${origdsetprefix}.nii.gz
 endif

cp $base ./

# get rid of temporary warped datasets
rm __tmp*_${dsetprefix}*.HEAD __tmp*_${dsetprefix}*.BRIK* __tmp*_${dsetprefix}*.1D
rm ${dsetprefix}.1D
rm ${dsetprefix}_inv.1D
rm *_al2std_mat.aff12.1D

# notes

# warp the transformed macaque back to its original space
#  just as a quality control. The two datasets should be very similar
#3dNwarpApply -overwrite -short -nwarp \
#   "${dsetprefix}_inv.aff12.1D INV(${dsetprefix}_WARP.nii.gz)" \
#   -source ${dsetprefix}_warp2std.nii.gz -master ${finalmaster}+orig \
#   -prefix ${dsetprefix}_iwarpback -overwrite


# zeropad the warp if segmentation doesn't cover the brain and reapply the warp
# 3dZeropad -S 50 -prefix ${dsetprefix}_zp_WARP.nii.gz ${dsetprefix}_WARP.nii.gz
# 3dNwarpApply -interp NN \
#   -nwarp "${dsetprefix}_inv.aff12.1D INV(${dsetprefix}_zp_WARP.nii.gz)" \
#   -source $segset -master $dset -prefix ${dsetprefix}_seg_zp
# 3drefit -cmap INT_CMAP ${dsetprefix}_seg_zp+orig
# 3drefit -copytables $segset ${dsetprefix}_seg_zp+orig
