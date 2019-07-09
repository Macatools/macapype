#!/bin/sh

#Latest version 280319 updated by Kep Kee

ssh -x loh.k@frioul.int.univ-amu.fr
frioul_interactive 

export PATH=$PATH:/hpc/soft/afni/afni/
export ANTSPATH=/hpc/soft/ANTS/antsbin/bin/
export PATH=$ANTSPATH:$PATH
export PATH=$PATH:/hpc/soft/ANTS/ANTs/Scripts/

#Input name of subject
subj=032311
site=sbri
name=${site}_${subj}

#nii directory

rawdir=/hpc/meca/data/Macaques/Macaque_hiphop/${site}/sub-${subj}/ses-001/anat/

#nmt directory with template and scripts
nmt_dir=/hpc/meca/users/loh.k/macaque_preprocessing/NMT_v1.2/

#scripts directory

script_dir=/hpc/meca/users/loh.k/macaque_preprocessing/preproc_cloud/processing_scripts/

#subject directories

subjdir=/hpc/meca/users/loh.k/macaque_preprocessing/preproc_cloud/${name}/
subj_preprocess_dir=${subjdir}preprocessing/

mkdir ${subjdir}
cd ${subjdir}

#COPY data, scripts and templates into subject directory

cp ${rawdir}*.nii.gz ${subjdir}
cp ${nmt_dir}NMT.nii.gz ${subjdir}
cp ${nmt_dir}NMT_SS.nii.gz ${subjdir}
cp ${script_dir}atlasBREX_fslfrioul.sh ${subjdir}

#Counting, renaming, averaging and renaming T1 and T2 files.

t1list=(`ls *T1*.nii.gz`)

x=1
for i in "${t1list[@]}" 
do 
  echo $i
  mv ${i} ${name}_t1_${x}.nii.gz 
  ((x++))
  echo ${x}
done

#flirt_average if multiple images

count=$((x - 1))

if (($count > 1))
then
  scanlist=(`ls *t1*.nii.gz`)
  echo "There are $count scans, so flirt_averaging ${scanlist[@]} with ref to ${scanlist[0]}"
  fsl5.0-flirt_average $count `echo ${scanlist[@]}` ${name}_t1.nii.gz -dof 6
else
  mv ${name}_t1_1.nii.gz ${name}_t1.nii.gz
fi

if [ "$(ls -l *T2*.nii.gz | wc -l)" == "1" ]
then
  t2list=(`ls *T2*.nii.gz`)
  y=1
  for i in "${t2list[@]}" 
  do 
    echo $i
    mv ${i} ${name}_t2_${y}.nii.gz 
    ((y++))
    echo ${y}
  done
  count2=$((y - 1))
  if (($count2 > 1))
  then
    scanlist=(`ls *t2*.nii.gz`)
    echo "There are $count2 scans, so flirting ${scanlist[@]} with ref to ${scanlist[0]} and then flirt to ${name}_t1.nii.gz"
    fsl5.0-flirt_average $count2 `echo ${scanlist[@]}` ${name}_t2.nii.gz -dof 6
    fsl5.0-flirt -dof 6 -in ${name}_t2.nii.gz -ref ${name}_t1.nii.gz -out ${name}_t2.nii.gz
  else
    mv ${name}_t2_1.nii.gz ${name}_t2.nii.gz
    echo "There is only one t2 scan, so flirting ${name}_t2.nii.gz to ${name}_t1.nii.gz"
    fsl5.0-flirt -dof 6 -in ${name}_t2.nii.gz -ref ${name}_t1.nii.gz -out ${name}_t2.nii.gz
  fi
else
    echo "There are no t2 scans"
fi

#denoising T1 and T2 with franck's matlab script

gunzip ${name}_t1.nii.gz
matlab -nosplash -nojvm -nodisplay -nodesktop -r "addpath('/hpc/meca/users/loh.k/macaque_preprocessing/denoise/');meuhmagicfilter('${name}_t1.nii','denoised','aonlm',0,'gauss',1,1,3);exit;"
gzip ${name}_t1__denoised_aonlm_gauss_1.0_1_3.nii
gzip ${name}_t1.nii

gunzip ${name}_t2.nii.gz
matlab -nosplash -nojvm -nodisplay -nodesktop -r "addpath('/hpc/meca/users/loh.k/macaque_preprocessing/denoise/');meuhmagicfilter('${name}_t2.nii','denoised','aonlm',0,'gauss',1,1,3);exit;"
gzip ${name}_t2__denoised_aonlm_gauss_1.0_1_3.nii
gzip ${name}_t2.nii

#Crop image (we have to determine the parameters of the brain cropping via fslview or fsleyes)

fsl5.0-fslroi ${name}_t1__denoised_aonlm_gauss_1.0_1_3.nii.gz ${name}_t1_denoised_cropped.nii.gz 88 144 14 180 27 103 #crop_bb_T1
fsl5.0-fslroi ${name}_t2__denoised_aonlm_gauss_1.0_1_3.nii.gz ${name}_t2_denoised_cropped.nii.gz 88 144 14 180 27 103 #crop_bb_T2

#bias correction via t2

sigma=4
sub=${name}
T1=${name}_t1_denoised_cropped.nii.gz
T2=${name}_t2_denoised_cropped.nii.gz

fsl5.0-fslmaths $T1 -mul $T2 -abs -sqrt "${sub}_T1mulT2.nii.gz" -odt float #mult_T1_T2 OK
meanbrainval=`fsl5.0-fslstats "${sub}_T1mulT2.nii.gz" -M` #meanbrainval
fsl5.0-fslmaths "${sub}_T1mulT2.nii.gz" -div $meanbrainval "${sub}_T1mulT2_norm.nii.gz" #norm_mult
fsl5.0-fslmaths "${sub}_T1mulT2_norm.nii.gz" -bin -s $sigma "smooth_norm_s${sigma}.nii.gz" #smooth
fsl5.0-fslmaths "${sub}_T1mulT2_norm.nii.gz" -s $sigma -div "smooth_norm_s${sigma}.nii.gz" "${sub}_T1mulT2_norm_s${sigma}.nii.gz" #norm_smooth
fsl5.0-fslmaths "${sub}_T1mulT2_norm.nii.gz" -div "${sub}_T1mulT2_norm_s${sigma}.nii.gz" "${sub}_T1mulT2_norm_modulate.nii.gz" #modulate
STD=`fsl5.0-fslstats "${sub}_T1mulT2_norm_modulate.nii.gz" -S`
echo $STD
MEAN=`fsl5.0-fslstats "${sub}_T1mulT2_norm_modulate.nii.gz" -M`
echo $MEAN
Lower=`echo "$MEAN - ($STD * 0.5)" | bc -l`
echo $Lower

######### Mask

fsl5.0-fslmaths "${sub}_T1mulT2_norm_modulate.nii.gz" -thr $Lower -bin -ero -mul 255 "${sub}_T1mulT2_norm_modulate_mask.nii.gz" #thresh_lower et mod_mask
fsl5.0-fslmaths "${sub}_T1mulT2_norm.nii.gz" -mas "${sub}_T1mulT2_norm_modulate_mask.nii.gz" -dilall "${sub}_bias_raw.nii.gz" -odt float #bias
fsl5.0-fslmaths "${sub}_bias_raw.nii.gz"  -s $sigma "${sub}_OutputBiasField.nii.gz" #smooth_bias

fsl5.0-fslmaths $T1 -div "${sub}_OutputBiasField.nii.gz" "${sub}_t1_restored_s${sigma}.nii.gz" -odt float #restore_T1
fsl5.0-fslmaths $T2 -div "${sub}_OutputBiasField.nii.gz"   "${sub}_t2_restored_s${sigma}.nii.gz" -odt float #restore_T2


#brain extraction (there are many options to tweak the brain extraction here)

bash atlasBREX_fslfrioul.sh -b NMT_SS.nii.gz -nb NMT.nii.gz -h ${name}_t1_restored_s4.nii.gz -f 0.5 -reg 1 -w 10,10,10 -msk a,0,0 # atlas_brex

#edit mask

fsl5.0-fslmaths ${name}_t1_restored_s4_brain.nii.gz -bin ${name}_t1_restored_s4_brainmask.nii.gz #maskbrex
fsl5.0-fslmaths ${name}_t1_restored_s4_brainmask_nice.nii.gz -bin -s 1 -thr 0.5 -bin ${name}_brainmask.nii.gz #smooth_mask

3dcalc -a ${name}_t1_restored_s4.nii.gz -b ${name}_brainmask.nii.gz -expr 'a*b' -prefix ${name}_t1_brain.nii.gz #mult_T1
3dcalc -a ${name}_t2_restored_s4.nii.gz -b ${name}_brainmask.nii.gz -expr 'a*b' -prefix ${name}_t2_brain.nii.gz #mult_T2

#run NMT_subject_aligh.csh to generate a whole range of linear and non-linear transformations between the subject image and NMT template

dset=${name}_t1_brain.nii.gz
base=${nmt_dir}NMT_SS.nii.gz

tcsh -x ${nmt_dir}NMT_subject_align.csh $dset $base # NMT_subject_align

#SEGMENTATION

croppedfileprefix=${name}_t1_brain
mkdir NMT_${name}_segmentation
cd ./NMT_${name}_segmentation

# STEP 1: Alignment of NMT's masks to subject for antsBrainExtraction.sh and Atropos (Not strictly necessary, but we've already calculated registration, so this reduces computations and is found to help results)

3dNwarpApply -prefix ${name}_NMT_prior.nii.gz ${name}_NMT_brainmask_prob_prior.nii.gz ${name}_NMT_brainmask_prior.nii.gz tmp_01.nii.gz tmp_02.nii.gz tmp_03.nii.gz \
	-source ${nmt_dir}/NMT.nii.gz ${nmt_dir}/masks/probabilisitic_segmentation_masks/NMT_brainmask_prob.nii.gz ${nmt_dir}/masks/anatomical_masks/NMT_brainmask.nii.gz ${nmt_dir}/masks/probabilisitic_segmentation_masks/NMT_segmentation_CSF.nii.gz \
	${nmt_dir}/masks/probabilisitic_segmentation_masks/NMT_segmentation_GM.nii.gz ${nmt_dir}/masks/probabilisitic_segmentation_masks/NMT_segmentation_WM.nii.gz \
	-master ../${croppedfileprefix}_shft_aff.nii.gz -nwarp ../${croppedfileprefix}_shft_WARPINV.nii.gz -ainterp NN -overwrite # align_masks

#STEP 2: N4 intensity normalization over brain
N4BiasFieldCorrection -d 3 -i ../${croppedfileprefix}_shft_aff.nii.gz -o ${croppedfileprefix}_shft_aff_N4.nii.gz # norm_intensity

#STEP 3: antsAtropos

#make brainmask from brain image
fsl5.0-fslmaths ${croppedfileprefix}_shft_aff_N4.nii.gz -thr 1 -bin ${croppedfileprefix}_shft_aff_brainmask.nii.gz # make_brainmask

bash antsAtroposN4.sh -d 3 -a ${croppedfileprefix}_shft_aff_N4.nii.gz -x ${croppedfileprefix}_shft_aff_brainmask.nii.gz -c 3 -p tmp_%02d.nii.gz -o ${name}_segmentation_ # seg_at

cp ${name}_segmentation_SegmentationPosteriors01.nii.gz ${name}_segmentation_CSF.nii.gz # change filenames
cp ${name}_segmentation_SegmentationPosteriors02.nii.gz ${name}_segmentation_GM.nii.gz # change filenames
cp ${name}_segmentation_SegmentationPosteriors03.nii.gz ${name}_segmentation_WM.nii.gz # change filenames
cp ${name}_segmentation_Segmentation.nii.gz ${name}_segmentation.nii.gz # change filenames

rm -r ${name}_segmentation_SegmentationPosteriors*.nii.gz # remove default ANTs outputs
rm -r ${name}_segmentation_ # remove default ANTs outputs
rm -r tmp_*.nii.gz # remove temporary NMT segmentation priors
rm -r ${name}_segmentation_Segmentation.nii.gz
rm -r ${name}_segmentation_Segmentation0N4.nii.gz

# Transformation of generated masks and volumes from NMT to subject
#echo "Warping results back to native space"

3dAllineate -base ../${name}_t1_brain.nii.gz -source ${name}_t1_brain_shft_aff_brainmask.nii.gz -1Dmatrix_apply ../${name}_t1_brain_composite_linear_to_NMT_inv.1D  -final NN -prefix ${name}_brainmask.nii.gz -overwrite # align_brainmask

3dAllineate -base ../${name}_t1_brain.nii.gz -source ${name}_segmentation.nii.gz -1Dmatrix_apply ../${name}_t1_brain_composite_linear_to_NMT_inv.1D -final NN -prefix ${name}_segmentation.nii.gz -overwrite # align_seg

3dAllineate -base ../${name}_t1_brain.nii.gz -source ${name}_segmentation_CSF.nii.gz -1Dmatrix_apply ../${name}_t1_brain_composite_linear_to_NMT_inv.1D -final NN -prefix ${name}_segmentation_CSF.nii.gz -overwrite # align_seg_post1

3dAllineate -base ../${name}_t1_brain.nii.gz -source ${name}_segmentation_GM.nii.gz -1Dmatrix_apply ../${name}_t1_brain_composite_linear_to_NMT_inv.1D -final NN -prefix ${name}_segmentation_GM.nii.gz -overwrite # align_seg_post2

3dAllineate -base ../${name}_t1_brain.nii.gz -source ${name}_segmentation_WM.nii.gz -1Dmatrix_apply ../${name}_t1_brain_composite_linear_to_NMT_inv.1D -final NN -prefix ${name}_segmentation_WM.nii.gz -overwrite # align_seg_post3



