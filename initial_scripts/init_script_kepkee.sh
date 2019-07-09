#!/bin/sh

#Generic macaque processing script for cerimed monkeys (worked for Zebulon, Jaffar, Cleo, Cesar)
#Script is compatible with frioul

#############################
##Set up for preprocessing ##
#############################

##Log on to frioul and set up paths to afni and ANTs 

ssh -x loh.k@frioul.int.univ-amu.fr
frioul_interactive 

export PATH=$PATH:/hpc/soft/afni/afni/
export ANTSPATH=/hpc/soft/ANTS/antsbin/bin/
export PATH=$ANTSPATH:$PATH
export PATH=$PATH:/hpc/soft/ANTS/ANTs/Scripts/

##Specify subject names and file directories 

#Input name of subject
subj=zebulon
site=cerimed
name=${site}_${subj}

#nii directory - where the images are stored

rawdir=/hpc/meca/data/Macaques/Macaque_hiphop/${site}/sub-${subj}/

#nmt directory with template and scripts - where the NMT template and scripts are stored
nmt_dir=/hpc/meca/users/loh.k/macaque_preprocessing/NMT_v1.2/

#scripts directory - location of this script
script_dir=/hpc/meca/users/loh.k/macaque_preprocessing/preproc_cloud/processing_scripts/

#subject directories - output folders
subjdir=/hpc/meca/users/loh.k/macaque_preprocessing/preproc_cloud/${name}/
subj_preprocess_dir=${subjdir}preprocessing/

mkdir ${subjdir}
cd ${subjdir}


##COPY data, scripts and templates into subject directory

cp ${rawdir}*T*.nii.gz ${subjdir} #change here if neccessary to get all T1/T2 files from the nii directory
cp ${nmt_dir}NMT.nii.gz ${subjdir}
cp ${nmt_dir}NMT_SS.nii.gz ${subjdir}
cp ${script_dir}atlasBREX_fslfrioul.sh ${subjdir}

#Counting, renaming, averaging and renaming T1 and T2 files.

t1list=(`ls *T1w*.nii.gz`)

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

if [ "$(ls -l *T2w*.nii.gz | wc -l)" == "1" ]
then
  t2list=(`ls *T2w*.nii.gz`)
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

#view t1 and t2 images
#note: check for the following:
#1. are the files correctly oriented?
#2. are they properly registered to each other?
#3. Determine the cropping parameters

fslview ${name}_t1.nii.gz ${name}_t2.nii.gz

#Reorienting to canonical orientation if necessary using fslorient and fslswapdim: +x = Right; +y = Anterior; +z = Superior.

#cp ${name}_t1.nii.gz ${name}_t1_reorient.nii.gz
#fsl5.0-fslorient -deleteorient ${name}_t1_reorient.nii.gz
#fsl5.0-fslorient -setqformcode 1 ${name}_t1_reorient.nii.gz
#fsl5.0-fslorient -forceradiological ${name}_t1_reorient.nii.gz

#cp ${name}_t2.nii.gz ${name}_t2_reorient.nii.gz
#fsl5.0-fslorient -deleteorient ${name}_t2_reorient.nii.gz
#fsl5.0-fslorient -setqformcode 1 ${name}_t2_reorient.nii.gz
#fsl5.0-fslorient -forceradiological ${name}_t2_reorient.nii.gz

#cp ${name}_t1_reorient.nii.gz ${name}_t1.nii.gz
#cp ${name}_t2_reorient.nii.gz ${name}_t2.nii.gz

#rm ${name}_t1_reorient.nii.gz
#rm ${name}_t2_reorient.nii.gz

#fslview ${name}_t1.nii.gz ${name}_t2.nii.gz

#############################
##PART 1: Brain Extraction ##
#############################

# I mainly used atlasbrex.sh for brain-extraction, which depends on registration to a template for brain stripping, and which in turn requires the subject images to be bias-free and denoised. 
# Main steps:
# 1. Bias-correction using HCP method (T1mulT2)
# 2. Denoise using ANLM filter
# 3. Crop images using defined coordinates
# 4. Atlasbrex (script to strip brain, based on fsl-bet, flirt and fnirt) 


#Step 1: bias correction via t2

sigma=2 #I found that this seems to be a better value
sub=${name}
T1=${name}_t1.nii.gz
T2=${name}_t2.nii.gz

fsl5.0-fslmaths $T1 -mul $T2 -abs -sqrt "${sub}_T1mulT2.nii.gz" -odt float
meanbrainval=`fsl5.0-fslstats "${sub}_T1mulT2.nii.gz" -M`
fsl5.0-fslmaths "${sub}_T1mulT2.nii.gz" -div $meanbrainval "${sub}_T1mulT2_norm.nii.gz"
fsl5.0-fslmaths "${sub}_T1mulT2_norm.nii.gz" -bin -s $sigma "smooth_norm_s${sigma}.nii.gz"
fsl5.0-fslmaths "${sub}_T1mulT2_norm.nii.gz" -s $sigma -div "smooth_norm_s${sigma}.nii.gz" "${sub}_T1mulT2_norm_s${sigma}.nii.gz"
fsl5.0-fslmaths "${sub}_T1mulT2_norm.nii.gz" -div "${sub}_T1mulT2_norm_s${sigma}.nii.gz" "${sub}_T1mulT2_norm_modulate.nii.gz"
STD=`fsl5.0-fslstats "${sub}_T1mulT2_norm_modulate.nii.gz" -S`
echo $STD
MEAN=`fsl5.0-fslstats "${sub}_T1mulT2_norm_modulate.nii.gz" -M`
echo $MEAN
Lower=`echo "$MEAN - ($STD * 0.5)" | bc -l`
echo $Lower

fsl5.0-fslmaths "${sub}_T1mulT2_norm_modulate.nii.gz" -thr $Lower -bin -ero -mul 255 "${sub}_T1mulT2_norm_modulate_mask.nii.gz"
fsl5.0-fslmaths "${sub}_T1mulT2_norm.nii.gz" -mas "${sub}_T1mulT2_norm_modulate_mask.nii.gz" -dilall "${sub}_bias_raw.nii.gz" -odt float
fsl5.0-fslmaths "${sub}_bias_raw.nii.gz"  -s $sigma "${sub}_OutputBiasField.nii.gz"

fsl5.0-fslmaths $T1 -div "${sub}_OutputBiasField.nii.gz" "${sub}_t1_restored_s${sigma}.nii.gz" -odt float
fsl5.0-fslmaths $T2 -div "${sub}_OutputBiasField.nii.gz"   "${sub}_t2_restored_s${sigma}.nii.gz" -odt float

#remove non-used files

rm ${sub}_bias_raw.nii.gz
rm ${sub}_T1mulT2*.nii.gz
rm smooth_norm_s${sigma}.nii.gz

#Step 2: Denoising T1 and T2

gunzip ${name}_t1_restored_s${sigma}.nii.gz
matlab -nosplash -nojvm -nodisplay -nodesktop -r "addpath('/hpc/meca/users/loh.k/macaque_preprocessing/denoise/');meuhmagicfilter('${name}_t1_restored_s${sigma}.nii','denoised','aonlm',0,'gauss',1,1,3);exit;"
gzip ${name}_t1_restored_s${sigma}__denoised_aonlm_gauss_1.0_1_3.nii
gzip ${name}_t1_restored_s${sigma}.nii

gunzip ${name}_t2_restored_s${sigma}.nii.gz
matlab -nosplash -nojvm -nodisplay -nodesktop -r "addpath('/hpc/meca/users/loh.k/macaque_preprocessing/denoise/');meuhmagicfilter('${name}_t2_restored_s${sigma}.nii','denoised','aonlm',0,'gauss',1,1,3);exit;"
gzip ${name}_t2_restored_s${sigma}__denoised_aonlm_gauss_1.0_1_3.nii
gzip ${name}_t2_restored_s${sigma}.nii

#Crop image #MAKE SURE YOU DEFINE THESE VALUES)

fsl5.0-fslroi ${name}_t1_restored_s${sigma}__denoised_aonlm_gauss_1.0_1_3.nii.gz ${name}_t1_restored_s${sigma}_denoised_cropped.nii.gz 20 192 24 244 288 156
fsl5.0-fslroi ${name}_t2_restored_s${sigma}__denoised_aonlm_gauss_1.0_1_3.nii.gz ${name}_t2_restored_s${sigma}_denoised_cropped.nii.gz 20 192 24 244 288 156

fslview ${name}_t1_restored_s${sigma}_denoised_cropped.nii.gz #VIEW and CHECK cropped denoised image.

#Step 3: brain extraction
#The following parameters are optimal for the cerimed images I encountered so far.
#If you find that the brain extraction is not ideal, you can try other parameters using this procedure:
# 1. Run command: bash atlasBREX_fslfrioul.sh -b NMT_SS.nii.gz -nb NMT.nii.gz -h ${name}_t1_restored_s${sigma}_denoised_cropped.nii.gz -f n
# 2. This will generate 3 possible initial brain masks based on 3 bet values, enter the best value and the script will run and give u the brain extraction by the best linear transformation of the initial brain mask to the subject.
# 3. You can also then apply non-linear transformation (warping) to better fit the initial bet mask to the subject image by entering your optimal f value in the following command : bash atlasBREX_fslfrioul.sh -b NMT_SS.nii.gz -nb NMT.nii.gz -h ${name}_t1_restored_s${sigma}_denoised_cropped.nii.gz -f 0.4 -reg 1 -w 5,5,5

bash atlasBREX_fslfrioul.sh -b NMT_SS.nii.gz -nb NMT.nii.gz -h ${name}_t1_restored_s${sigma}_denoised_cropped.nii.gz -f 0.4 -reg 1 -w 5,5,5 


#Convert stripped brain into brainmask
fsl5.0-fslmaths ${name}_t1_restored_s${sigma}_denoised_cropped_brain.nii.gz -bin ${name}_t1_restored_s${sigma}_denoised_cropped_brainmask.nii.gz 

#Load mask wih respect to subject t1 for checking
fslview ${name}_t1_restored_s${sigma}_denoised_cropped.nii.gz ${name}_t1_restored_s${sigma}_denoised_cropped_brainmask.nii.gz 

#EDIT BRAINMASK and save as ${name}_t1_restored_s${sigma}_denoised_cropped_brainmask_nice.nii.gz

#Smooth corrected brain mask
fsl5.0-fslmaths ${name}_t1_restored_s${sigma}_denoised_cropped_brainmask_nice.nii.gz -bin -s 1 -thr 0.5 -bin ${name}_brainmask.nii.gz

#View mask to check
fslview ${name}_t1_restored_s${sigma}_denoised_cropped.nii.gz ${name}_brainmask.nii.gz


#make old_t2debias folder and move initial denoising and debias files into this folder, leaving just brainmask and t1, t2

mkdir old_t2debias
mv ${name}_t1_restored*.nii.gz old_t2debias
mv ${name}_t2_restored*.nii.gz old_t2debias
mv log.txt old_t2debias
mv ${name}_OutputBiasField*.nii.gz old_t2debias
mv NMT*.log old_t2debias
mv std2high*.nii.gz old_t2debias

#########################
##PART 2: Segmentation ##
#########################

# Main steps:
# 1. Recrop from initial T1 and T2 using same parameters 
# 2. Run denoise again on cropped T1 and T2
# 3. Run T2biascorrection, but this time with the brainmask from Part 1.
# 4. Run N4 (with special parameters from Jerome Sallet (Oxford) on the skull-stripped T1 brain image.
# 5. Run NMT_subject_align script (from NMT), that computes all transformation between subject T1 and NMT skullstripped brain template.
# 6. Transform NMT segmentation priors into subject space.
# 7  Run AntsAtroposN4 in subject space with NMT priors.


# 1. Recrop from initial T1 and T2 using same parameters 

fsl5.0-fslroi ${name}_t1.nii.gz ${name}_t1_cropped.nii.gz 20 192 24 244 288 156
fsl5.0-fslroi ${name}_t2.nii.gz ${name}_t2_cropped.nii.gz 20 192 24 244 288 156

# 2. Run denoise again on cropped T1 and T2

gunzip ${name}_t1_cropped.nii.gz
matlab -nosplash -nojvm -nodisplay -nodesktop -r "addpath('/hpc/meca/users/loh.k/macaque_preprocessing/denoise/');meuhmagicfilter('${name}_t1_cropped.nii','denoised','aonlm',0,'gauss',1,1,3);exit;"
gzip ${name}_t1_cropped__denoised_aonlm_gauss_1.0_1_3.nii
gzip ${name}_t1_cropped.nii

gunzip ${name}_t2_cropped.nii.gz
matlab -nosplash -nojvm -nodisplay -nodesktop -r "addpath('/hpc/meca/users/loh.k/macaque_preprocessing/denoise/');meuhmagicfilter('${name}_t2_cropped.nii','denoised','aonlm',0,'gauss',1,1,3);exit;"
gzip ${name}_t2_cropped__denoised_aonlm_gauss_1.0_1_3.nii
gzip ${name}_t2_cropped.nii

# 3. Run T2biascorrection, but this time with the brainmask from Part 1.

sigma=2
sub=${name}
T1=${name}_t1_cropped__denoised_aonlm_gauss_1.0_1_3.nii.gz
T2=${name}_t2_cropped__denoised_aonlm_gauss_1.0_1_3.nii.gz

fsl5.0-fslmaths $T1 -mul $T2 -abs -sqrt "${sub}_T1mulT2.nii.gz" -odt float

#mask with nice brain mask that i edited
fsl5.0-fslmaths "${sub}_T1mulT2.nii.gz" -mas "${name}_brainmask.nii.gz" "${sub}_T1mulT2_brain.nii.gz"

meanbrainval=`fsl5.0-fslstats "${sub}_T1mulT2.nii.gz" -M`
fsl5.0-fslmaths "${sub}_T1mulT2_brain.nii.gz" -div $meanbrainval "${sub}_T1mulT2_brain_norm.nii.gz"
fsl5.0-fslmaths "${sub}_T1mulT2_brain_norm.nii.gz" -bin -s $sigma "smooth_norm_s${sigma}.nii.gz"
fsl5.0-fslmaths "${sub}_T1mulT2_brain_norm.nii.gz" -s $sigma -div "smooth_norm_s${sigma}.nii.gz" "${sub}_T1mulT2_brain_norm_s${sigma}.nii.gz"
fsl5.0-fslmaths "${sub}_T1mulT2_brain_norm.nii.gz" -div "${sub}_T1mulT2_brain_norm_s${sigma}.nii.gz" "${sub}_T1mulT2_brain_norm_modulate.nii.gz"

STD=`fsl5.0-fslstats "${sub}_T1mulT2_brain_norm_modulate.nii.gz" -S`
echo $STD
MEAN=`fsl5.0-fslstats "${sub}_T1mulT2_brain_norm_modulate.nii.gz" -M`
echo $MEAN
Lower=`echo "$MEAN - ($STD * 0.5)" | bc -l`
echo $Lower

fsl5.0-fslmaths "${sub}_T1mulT2_brain_norm_modulate.nii.gz" -thr $Lower -bin -ero -mul 255 "${sub}_T1mulT2_brain_norm_modulate_mask.nii.gz"
fsl5.0-fslmaths "${sub}_T1mulT2_brain_norm.nii.gz" -mas "${sub}_T1mulT2_brain_norm_modulate_mask.nii.gz" -dilall "${sub}_bias_raw.nii.gz" -odt float
fsl5.0-fslmaths "${sub}_bias_raw.nii.gz"  -s $sigma "${sub}_OutputBiasField_new.nii.gz"

fsl5.0-fslmaths $T1 -div "${sub}_OutputBiasField_new.nii.gz" -mas "${name}_brainmask.nii.gz" "${sub}_t1_brain_restored_s${sigma}.nii.gz" -odt float
fsl5.0-fslmaths $T1 -div "${sub}_OutputBiasField_new.nii.gz" "${sub}_t1_restored_s${sigma}_new.nii.gz" -odt float
fsl5.0-fslmaths $T2 -div "${sub}_OutputBiasField_new.nii.gz" "${sub}_t2_restored_s${sigma}_new.nii.gz" -odt float
fsl5.0-fslmaths $T2 -div "${sub}_OutputBiasField_new.nii.gz" -mas "${name}_brainmask.nii.gz"  "${sub}_t2_brain_restored_s${sigma}.nii.gz" -odt float

#remove non-used files

rm ${sub}_bias_raw.nii.gz
rm ${sub}_T1mulT2*.nii.gz
rm smooth_norm_s${sigma}.nii.gz

# 4. Run N4 (with special parameters from Jerome Sallet (Oxford) on the skull-stripped T1 brain image.

N4BiasFieldCorrection -d 3 -b [200] -c [50x50x40x30,0.00000001] -i ${sub}_t1_brain_restored_s${sigma}.nii.gz -o ${sub}_t1_brain_restored_s${sigma}_N4.nii.gz -r 0 -s 2 --verbose 1

fslview ${name}_t1_cropped__denoised_aonlm_gauss_1.0_1_3.nii.gz ${sub}_t1_brain_restored_s${sigma}.nii.gz ${sub}_t1_brain_restored_s${sigma}_N4.nii.gz

# 5. Run NMT_subject_align script (from NMT), that computes all transformation between subject T1 and NMT skullstripped brain template.

dset=${sub}_t1_brain_restored_s${sigma}_N4.nii.gz
base=${nmt_dir}NMT_SS.nii.gz

tcsh -x ${nmt_dir}NMT_subject_align.csh $dset $base

# 6. Transform NMT segmentation priors into subject space.

croppedfileprefix=${sub}_t1_brain_restored_s${sigma}_N4
mkdir NMT_${name}_segmentation
cd ./NMT_${name}_segmentation

3dNwarpApply -prefix ${name}_NMT_prior.nii.gz ${name}_NMT_brainmask_prob_prior.nii.gz ${name}_NMT_brainmask_prior.nii.gz tmp_01.nii.gz tmp_02.nii.gz tmp_03.nii.gz \
	-source ${nmt_dir}/NMT_SS.nii.gz ${nmt_dir}/masks/probabilisitic_segmentation_masks/NMT_brainmask_prob.nii.gz ${nmt_dir}/masks/anatomical_masks/NMT_brainmask.nii.gz ${nmt_dir}/masks/probabilisitic_segmentation_masks/NMT_segmentation_CSF.nii.gz \
	${nmt_dir}/masks/probabilisitic_segmentation_masks/NMT_segmentation_GM.nii.gz ${nmt_dir}/masks/probabilisitic_segmentation_masks/NMT_segmentation_WM.nii.gz \
	-master ../${croppedfileprefix}_shft_aff.nii.gz -nwarp ../${croppedfileprefix}_shft_WARPINV.nii.gz -ainterp NN -overwrite

3dAllineate -base ../${sub}_t1_brain_restored_s${sigma}_N4.nii.gz -source ${name}_NMT_brainmask_prob_prior.nii.gz -1Dmatrix_apply ../${croppedfileprefix}_composite_linear_to_NMT_inv.1D  -final NN -prefix ${name}_NMT_brainmask_prob_prior.nii.gz -overwrite

3dAllineate -base ../${sub}_t1_brain_restored_s${sigma}_N4.nii.gz -source ${name}_NMT_brainmask_prior.nii.gz -1Dmatrix_apply ../${croppedfileprefix}_composite_linear_to_NMT_inv.1D  -final NN -prefix ${name}_NMT_brainmask_prior.nii.gz -overwrite

3dAllineate -base ../${sub}_t1_brain_restored_s${sigma}_N4.nii.gz -source ${name}_NMT_prior.nii.gz -1Dmatrix_apply ../${croppedfileprefix}_composite_linear_to_NMT_inv.1D  -final NN -prefix ${name}_NMT_prior.nii.gz -overwrite

3dAllineate -base ../${sub}_t1_brain_restored_s${sigma}_N4.nii.gz -source tmp_01.nii.gz -1Dmatrix_apply ../${croppedfileprefix}_composite_linear_to_NMT_inv.1D  -final NN -prefix tmp_01.nii.gz -overwrite 

3dAllineate -base ../${sub}_t1_brain_restored_s${sigma}_N4.nii.gz -source tmp_02.nii.gz -1Dmatrix_apply ../${croppedfileprefix}_composite_linear_to_NMT_inv.1D  -final NN -prefix tmp_02.nii.gz -overwrite

3dAllineate -base ../${sub}_t1_brain_restored_s${sigma}_N4.nii.gz -source tmp_03.nii.gz -1Dmatrix_apply ../${croppedfileprefix}_composite_linear_to_NMT_inv.1D  -final NN -prefix tmp_03.nii.gz -overwrite

#STEP 7: antsAtropos

# Additional checks to make sure nifti headers correspond between subject N4 images,brain mask and priors. ANTs is sensitive to header differences that could arise due to the mix-and-match processing via different softwares.

#command to compare headers, but does not check obliquity
#nifti_tool -diff_hdr -infiles tmp_01.nii.gz ../${sub}_t1_brain_restored_s${sigma}_N4.nii.gz 

#useful command to check obliquity
#3dinfo ../${sub}_t1_brain_restored_s${sigma}_N4.nii.gz 
#3dinfo tmp_01.nii.gz

#NOTE! FOR the cerimed subjects (Jaffar, Cleo, Cesar), there was a problem with obliquity. so I had to force dataset to be "deoblique" so as to match the tmp files. somehow during affine transform of the tmp files, the oblique information is lost. but the files are nicely aligned so i am manually changing the header input.

#3drefit -deoblique ${sub}_t1_brain_restored_s${sigma}_N4.nii.gz 

cp ../${sub}_t1_brain_restored_s${sigma}_N4.nii.gz ${sub}_t1_brain_restored_s${sigma}_N4.nii.gz #if no oblique

#make brainmask from brain image
fsl5.0-fslmaths ${sub}_t1_brain_restored_s${sigma}_N4.nii.gz -bin ${sub}_t1_brain_restored_s${sigma}_N4_mask

bash antsAtroposN4.sh -d 3 -a ${sub}_t1_brain_restored_s${sigma}_N4.nii.gz -x ${sub}_t1_brain_restored_s${sigma}_N4_mask.nii.gz -c 3 -p tmp_%02d.nii.gz -o ${name}_segmentation_

cp ${name}_segmentation_SegmentationPosteriors01.nii.gz ${name}_segmentation_CSF.nii.gz # change filenames
cp ${name}_segmentation_SegmentationPosteriors02.nii.gz ${name}_segmentation_GM.nii.gz # change filenames
cp ${name}_segmentation_SegmentationPosteriors03.nii.gz ${name}_segmentation_WM.nii.gz # change filenames
cp ${name}_segmentation_Segmentation.nii.gz ${name}_segmentation.nii.gz # change filenames

rm -r ${name}_segmentation_SegmentationPosteriors*.nii.gz # remove default ANTs outputs
rm -r ${name}_segmentation_ # remove default ANTs outputs
rm -r tmp_*.nii.gz # remove temporary NMT segmentation priors
rm -r ${name}_segmentation_Segmentation.nii.gz
rm -r ${name}_segmentation_Segmentation0N4.nii.gz

#VIEW segmentation
fslview ${sub}_t1_brain_restored_s${sigma}_N4.nii.gz ${name}_segmentation.nii.gz
