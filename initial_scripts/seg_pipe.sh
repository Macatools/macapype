## Commencer par Denoising du T1 et du T2 avec sanlm
## Il sait faire ça David.


## T1xT2BET. Le crop est large (20) car le crop final sera fait quand l'anat se retrouvera dans le template.
## Ce crop sert seulement a gagner du temps de calcul pour les étapes suivantes.
## l'option -f épend du singe, ici j'ai mis la valeur qui marche pour Maga
## C'est la seule option critique qu'il faut tester avec de l'essai erreur. La bonne nouvelle c'est que c'est sur une étape du début.
T1xT2BET.sh -t1 sub-Maga_ses-01_T1w0p6mmDenoised.nii -t2 sub-Maga_ses-01_T2w0p6mmDenoised.nii.gz -aT2 -n 3 -f 0.45 -c 20




## IterREGBET. Je le fais avec l'inia car je trouve qu'il fonctionne mieux pour le recalage non-linéaire qui aura lieu ensuite
template_brain=/hpc/banco/Primavoice_Data_and_Analysis/templates/inia19/inia19-t1-brain.nii.gz
IterREGBET.sh -inw sub-Maga_ses-01_T1w0p6mmDenoised_cropped.nii.gz -inb sub-Maga_ses-01_T1w0p6mmDenoised_BET_cropped.nii.gz -refb $template_brain




## T1xT2BiasFieldCorrection en donnant le cerveau extrait précédemment. Il faudrait voir avec Julien pour déterminer automatiquement une valeur de sigma (option -s) en fonction de la résolution de l'image.
T1xT2BiasFieldCorrection.sh -t1 sub-Maga_ses-01_T1w0p6mmDenoised_cropped.nii.gz -t2 sub-Maga_ses-01_T2w0p6mmDenoised-in-T1w_cropped.nii.gz -s 3 -b sub-Maga_ses-01_T1w0p6mmDenoised_cropped_IRbrain_mask.nii.gz




## Recalage rigide vers le template
T1_brain=sub-Maga_ses-01_T1w0p6mmDenoised_cropped_debiased_brain.nii.gz
T1_brain_in_temp=sub-Maga_ses-01_T1w0p6mmDenoised_cropped_debiased_brain-rigid-in-template.nii.gz
anat2temp_xfm=T1_rigid_to_template.xfm
flirt -in $T1_brain -ref $template_brain -dof 6 -cost normmi -out $T1_brain_in_temp -omat $anat2temp_xfm

T1=sub-Maga_ses-01_T1w0p6mmDenoised_cropped_debiased.nii.gz
T1_in_temp=sub-Maga_ses-01_T1w0p6mmDenoised_cropped_debiased-rigid-in-template.nii.gz
flirt -in $T1 -ref $template_brain -out $T1_in_temp -applyxfm -init $anat2temp_xfm




## Recalage non-linéaire avec ANTS
template_head=/hpc/banco/Primavoice_Data_and_Analysis/templates/inia19/inia19-t1.nii.gz
ANTs_out_base=SyN_template_to_anat
/hpc/soft/ANTS/ANTs/Scripts/antsRegistrationSyNQuick.sh -d 3 -f $T1_brain_in_temp -f $T1_in_temp -m $template_brain -m $template_head -o $ANTs_out_base -j 1




## Le reste je te le laisse en Matlab: en gros faut appliquer les transformations trouvées précédemment aux probas des tissus du template
to_move = {'paths.template_tissue{1}';'paths.template_tissue{2}';'paths.template_tissue{3}';'paths.template_brain_mask'};
reg_prob_maps = cell(length(to_move),1);
affine_xfm = [ANTs_out_base '0GenericAffine.mat'];
warp_file = [ANTs_out_base '1Warp.nii.gz'];
for i = 1:length(to_move)
    in_file = eval(to_move{i});
    [~,in_name,ext] = fileparts(in_file);
    if strcmp(ext,'.gz'); [~,in_name] = fileparts(in_name); end
    reg_prob_maps{i} = fullfile(paths.segmentation,[in_name '-in-anat.nii.gz']);
    system(sprintf('%s -i %s -r %s -o %s -t %s -t %s -n NearestNeighbor',fullfile('$ANTSPATH','antsApplyTransforms'),in_file,T1_in_temp,reg_prob_maps{i},warp_file,affine_xfm));
end



## Et puis hop: segmentation
[tissue_files,tissues] = spm_old_segment(T1_in_temp,reg_prob_maps{1},reg_prob_maps{2},reg_prob_maps{3});





## Je te laisse aussi du matlab qui crée des volumes binaires des différents tissus en fonction de probas
## Puis y a la concaténation des trois tissus pour faire le masque du cerveau
%% Create 01 & 99 percents masks for each tissue
probs = {'01';'50';'99'};
for i = 1:numel(tissues)
    for p = 1:numel(probs)
        % Create a mask of voxels with prob >= probs-percent
        maths_out_file = fullfile(paths.segmentation,sprintf('%s_%s_%sp.nii.gz',T1_base_name,tissues{i},probs{p}));
        system(sprintf('%sfslmaths %s -thr 0.%s %s',paths.FSL_prefix,tissue_files{i},probs{p},maths_out_file));
        system(sprintf('%sfslmaths %s -bin %s -odt short',paths.FSL_prefix,maths_out_file,maths_out_file));
        
        % Keep the largest cluster
        system(sprintf('%s 3 %s GetLargestComponent %s',fullfile('$ANTSPATH','ImageMath'),maths_out_file,maths_out_file));
        system(sprintf('%sfslmaths %s -add 0 %s -odt short',paths.FSL_prefix,maths_out_file,maths_out_file)); % convert to short (for brainvisa)
    end
end

%% Create brain mask from concatenation of 3 tissues at 1% prob
T1_brainmask_in_temp = fullfile(paths.segmentation,[T1_base_name '-brainmask-in-template.nii.gz']);
system(sprintf('%sfslmaths %s -add %s -add %s -bin %s -odt short',paths.FSL_prefix,fullfile(paths.segmentation,[T1_base_name '_white_01p.nii.gz']),fullfile(paths.segmentation,[T1_base_name '_grey_01p.nii.gz']),fullfile(paths.segmentation,[T1_base_name '_csf_01p.nii.gz']),T1_brainmask_in_temp));
system(sprintf('%s 3 %s FillHoles %s',fullfile('$ANTSPATH','ImageMath'),T1_brainmask_in_temp,T1_brainmask_in_temp));
system(sprintf('%sfslmaths %s -add 0 %s -odt short',paths.FSL_prefix,T1_brainmask_in_temp,T1_brainmask_in_temp)); % convert to short (for brainvisa)

% mask brain
system(sprintf('%sfslmaths %s -mas %s %s -odt short',paths.FSL_prefix,T1_in_temp,T1_brainmask_in_temp,T1_brain_in_temp));