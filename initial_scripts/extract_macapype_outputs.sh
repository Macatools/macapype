#input baboon name
baboon_name=$1

#Input name of subject
name=_session_01_subject_${baboon_name}

#directory with nmt template and scripts
nmt_dir=/hpc/meca/users/loh.k/baboon_proc/haiko89_template/

#input subject directory -> your macapype output folder
subjdir=/hpc/meca/users/loh.k/baboon_noT1/preproc/baboon_noT1_segmentation_test_indiv_params/

#Make a separate directory for the subject's Brainvisa input files
mkdir /hpc/meca/users/loh.k/baboon_noT1/preproc/brainvisa_inputs/${name}
cd /hpc/meca/users/loh.k/baboon_noT1/preproc/brainvisa_inputs/${name}

#Copy T1 cropped + denoised file as t1_cropped -> serve as reference image for transformations later
cp ${subjdir}/full_segment_pnh_noT1_subpipes_baboon/short_preparation_noT1_pipe/${name}/denoise_T1/*_noise_corrected.nii.gz ${name}_t1_cropped.nii.gz

#get transformations from template to subject computed in macapype 

warp_nmt_to_subject=${subjdir}/full_segment_pnh_noT1_subpipes_baboon/brain_segment_from_mask_noT1_pipe/register_NMT_pipe/${name}/NMT_subject_align/*_WARPINV.nii.gz
linear_nmt_to_subject=${subjdir}/full_segment_pnh_noT1_subpipes_baboon/brain_segment_from_mask_noT1_pipe/register_NMT_pipe/${name}/NMT_subject_align/*_composite_linear_to_NMT_inv.1D
subject_shft_aff_ref=${subjdir}/full_segment_pnh_noT1_subpipes_baboon/brain_segment_from_mask_noT1_pipe/register_NMT_pipe/${name}/NMT_subject_align/*_shft_aff.nii.gz

# Warp L and R template brainmask to subject space

3dNwarpApply -prefix ${name}_HAIKO_L_brainmask.nii.gz -source ${nmt_dir}NMT_registration/Haiko89_Asymmetric.Template_n89_brainmask_L.nii.gz -master ${subject_shft_aff_ref} -nwarp ${warp_nmt_to_subject} -ainterp NN -overwrite
3dAllineate -base ${name}_t1_cropped.nii.gz -source ${name}_HAIKO_L_brainmask.nii.gz -1Dmatrix_apply ${linear_nmt_to_subject} -final NN -prefix ${name}_HAIKO_L_brainmask.nii.gz -overwrite

3dNwarpApply -prefix ${name}_HAIKO_R_brainmask.nii.gz -source ${nmt_dir}NMT_registration/Haiko89_Asymmetric.Template_n89_brainmask_R.nii.gz -master ${subject_shft_aff_ref} -nwarp ${warp_nmt_to_subject} -ainterp NN -overwrite
3dAllineate -base ${name}_t1_cropped.nii.gz -source ${name}_HAIKO_R_brainmask.nii.gz -1Dmatrix_apply ${linear_nmt_to_subject} -final NN -prefix ${name}_HAIKO_R_brainmask.nii.gz -overwrite

#binarize cerbellum mask from template and transform to subject space
fslmaths ${nmt_dir}NMT_registration/Haiko89_Asymmetric.Template_n89_brainmask_cerebellum.nii.gz -bin HAIKO_cerebellum_brainmask.nii.gz #binarize template cerebellum

3dNwarpApply -prefix ${name}_HAIKO_cerebellum_brainmask.nii.gz -source HAIKO_cerebellum_brainmask.nii.gz -master ${subject_shft_aff_ref} -nwarp ${warp_nmt_to_subject} -ainterp NN -overwrite
3dAllineate -base ${name}_t1_cropped.nii.gz -source ${name}_HAIKO_cerebellum_brainmask.nii.gz -1Dmatrix_apply ${linear_nmt_to_subject} -final NN -prefix ${name}_HAIKO_cerebellum_brainmask.nii.gz -overwrite

#Using LH and RH masks to obtain left and right hemisphere segmentation masks
segmentationfile=${subjdir}full_segment_pnh_noT1_subpipes_baboon/brain_segment_from_mask_noT1_pipe/segment_atropos_pipe/${name}/seg_at/segment_Segmentation.nii.gz

3dcalc -a ${segmentationfile} -b ${name}_HAIKO_L_brainmask.nii.gz -expr 'a*b/b' -prefix ${name}_segmentation_LH.nii.gz 
3dcalc -a ${segmentationfile} -b ${name}_HAIKO_R_brainmask.nii.gz -expr 'a*b/b' -prefix ${name}_segmentation_RH.nii.gz 

#remove cerebellum from left and right brain segmentations
3dcalc -a ${name}_segmentation_LH_corrected.nii.gz  -b ${name}_HAIKO_cerebellum_brainmask.nii.gz -expr '(a*(not(b)))' -prefix ${name}_LH_seg_nocb.nii.gz -overwrite
3dcalc -a ${name}_segmentation_RH_corrected.nii.gz -b ${name}_HAIKO_cerebellum_brainmask.nii.gz -expr '(a*(not(b)))' -prefix ${name}_RH_seg_nocb.nii.gz -overwrite


#create L/R GM and WM no-cerebellum binary masks from subject brain segmentation

3dcalc -a ${name}_LH_seg_nocb.nii.gz -expr 'iszero(a-2)' -prefix ${name}_L_GM_nocb_mask.nii.gz -overwrite
3dcalc -a ${name}_LH_seg_nocb.nii.gz -expr 'iszero(a-3)' -prefix ${name}_L_WM_nocb_mask.nii.gz -overwrite

3dcalc -a ${name}_RH_seg_nocb.nii.gz -expr 'iszero(a-2)' -prefix ${name}_R_GM_nocb_mask.nii.gz -overwrite
3dcalc -a ${name}_RH_seg_nocb.nii.gz -expr 'iszero(a-3)' -prefix ${name}_R_WM_nocb_mask.nii.gz -overwrite


#Extract Cerebellum using template mask transformed to subject space
dname=${name}_t1_cropped.nii.gz
mask=${name}_HAIKO_cerebellum_brainmask.nii.gz
3dcalc -a $dname -b $mask -expr 'a*b/b' -prefix ${name}_cerebellum.nii.gz -overwrite


#Extract L.GM using template mask transformed to subject space
dname=${name}_t1_cropped.nii.gz
mask=${name}_L_GM_nocb_mask.nii.gz
3dcalc -a $dname -b $mask -expr 'a*b/b' -prefix ${name}_LH_GM.nii.gz -overwrite

#Extract L.WM using template mask transformed to subject space
mask=${name}_L_WM_nocb_mask.nii.gz
3dcalc -a $dname -b $mask -expr 'a*b/b' -prefix ${name}_LH_WM.nii.gz -overwrite

#Extract R.GM using template mask transformed to subject space
dname=${name}_t1_cropped.nii.gz
mask=${name}_R_GM_nocb_mask.nii.gz
3dcalc -a $dname -b $mask -expr 'a*b/b' -prefix ${name}_RH_GM.nii.gz -overwrite

#Extract R.WM using template mask transformed to subject space
mask=${name}_R_WM_nocb_mask.nii.gz
3dcalc -a $dname -b $mask -expr 'a*b/b' -prefix ${name}_RH_WM.nii.gz -overwrite

