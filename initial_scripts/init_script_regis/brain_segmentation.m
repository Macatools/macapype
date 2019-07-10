% Perform segmentation with the appropriate method depending on the species

if ~exist(paths.segmentation,'dir');mkdir(paths.segmentation);end % create segmentation folder if non-existant

if strcmp(paths.species,'human')
    if isfield(paths,'T2_file')
        spm_segment(paths.anat_file,paths.T2_file,'TPM',paths)
    else
        spm_segment(paths.anat_file,[],'TPM',paths)
    end
elseif strcmp(paths.species,'macaque') || strcmp(paths.species,'marmoset')
    %% first check if brain has been extracted from the anat (necessary for flirt)
    if ~isfield(paths,'anat_file_BET')
        error('Cannot continue segmentation without a brain extraction of the anatomic file. \nRun ''brain_extraction'' beforehand and run the parameters again.%s','')
    end
    
    fprintf('Registering template to anat:\n')
    %% flirt template-brain to anat-brain
    fprintf('Linear registration...\n')
%     flirt_out_file = fullfile(paths.segmentation,'template_brain_flirt.nii');
%     temp2anat_xfm = fullfile(paths.segmentation,'template_to_anat.xfm');
%     if exist(flirt_out_file,'file') == 2; delete(flirt_out_file);end
%     system(sprintf('%sflirt -in %s -ref %s -out %s -cost normcorr -omat %s',paths.FSL_prefix,paths.template_brain,paths.anat_file_BET,flirt_out_file,temp2anat_xfm));
%     system(sprintf('gunzip %s',flirt_out_file));
%     fprintf(' done.\n')
    
    temp2anat_iterations = 4;
    flirt_in_file = paths.template_brain;
    flirt_ref_file = paths.anat_file_BET;
    flirt_out_file = fullfile(paths.segmentation,[paths.template_name '_brain_flirt.nii']);
    temp2anat_xfm = fullfile(paths.segmentation,[paths.template_name '_to_anat.xfm']);
    for i = 1:temp2anat_iterations
        fprintf('FLIRT & mask iteration %i/%i...',i,temp2anat_iterations)
        
        if exist(flirt_out_file,'file') == 2; delete(flirt_out_file);end
        system(sprintf('%sflirt -in %s -ref %s -omat %s -out %s -cost normcorr',paths.FSL_prefix,flirt_in_file,flirt_ref_file,temp2anat_xfm,flirt_out_file));
        system(sprintf('gunzip %s',flirt_out_file));
        
        if i < temp2anat_iterations
        	if exist(paths.anat_file_brain_mask,'file') == 2; delete(paths.anat_file_brain_mask);end
        	system(sprintf('%sflirt -in %s -ref %s -out %s -interp nearestneighbour -applyxfm -init %s',paths.FSL_prefix,paths.template_brain_mask,flirt_ref_file,paths.anat_file_brain_mask,temp2anat_xfm));
        	system(sprintf('gunzip %s',paths.anat_file_brain_mask));

        	if exist(paths.anat_file_brain,'file') == 2; delete(paths.anat_file_brain);end
        	system(sprintf('%sfslmaths %s -mul %s %s',paths.FSL_prefix,paths.anat_file,paths.anat_file_brain_mask,paths.anat_file_brain));
        	system(sprintf('gunzip %s',paths.anat_file_brain));
        end
        
        fprintf(' done.\n')
        
        if i == temp2anat_iterations-1
        	reg_prob_maps = cell(3,1);
    		for i = 1:3
        		in_file = paths.template_tissue{i};
        		out_file = fullfile(paths.segmentation,sprintf('%s_prob_%i_flirt.nii',paths.template_name,i));
        		if exist(out_file,'file') == 2; delete(out_file);end
        		system(sprintf('%sflirt -in %s -ref %s -out %s -interp nearestneighbour -applyxfm -init %s',paths.FSL_prefix,in_file,paths.anat_file_brain,out_file,temp2anat_xfm));
        		system(sprintf('gunzip %s',out_file));
        		reg_prob_maps{i} = out_file;
    		end
    		spm_old_segment(paths.anat_file,reg_prob_maps{1},reg_prob_maps{2},reg_prob_maps{3},paths)
        end
        flirt_ref_file = paths.anat_file_brain;
    end
    
    
    
    %% Save figure of anat overlaid with template
    view_slice_overlay(paths.anat_file,flirt_out_file,0)
    figurewrite(fullfile(paths.segmentation,[paths.template_name '_to_anat_flirt'])) % Using GLMdenoise function
    
    %% fnirt template to anat while providing the affine transform obtained from flirt
    fprintf('Non-linear registration... (this may take several minutes...)')
    fnirt_out_file = fullfile(paths.segmentation,[paths.template_name '_head_fnirt.nii']);
    cout_file = fullfile(paths.segmentation,[paths.template_name '_to_anat_fnirt.nii']);
    system(sprintf('%sfnirt --ref=%s --in=%s --iout=%s --aff=%s --cout=%s',paths.FSL_prefix,paths.anat_file,paths.template_head,fnirt_out_file,temp2anat_xfm,cout_file));
    
    %% Apply warp to the brain template
    fnirt_out_file = fullfile(paths.segmentation,[paths.template_name '_brain_fnirt.nii']);
    if exist(fnirt_out_file,'file') == 2; delete(fnirt_out_file);end
    system(sprintf('%sapplywarp --ref=%s --in=%s --out=%s --warp=%s',paths.FSL_prefix,paths.anat_file,paths.template_brain,fnirt_out_file,cout_file));
    system(sprintf('gunzip %s',fnirt_out_file));
    
    %% Save figure of anat overlaid with template
    view_slice_overlay(paths.anat_file,fnirt_out_file,0)
    figurewrite(fullfile(paths.segmentation,[paths.template_name '_to_anat_fnirt'])) % Using GLMdenoise function
    fprintf(' done.\n')
    
    %% Prompt user choose between linear and non linear registration
    hmsg = msgbox('Choose between linear (flirt) or non-linear (fnirt) registration by inspecting the results in FSLView. Close FSLView when finished.');
    hmsgb = findobj(hmsg,'Style','pushbutton');
    hmsgb.Units = 'normalized';
    hmsgb.Position(3) = 0.3;
    hmsgb.Position(1) = 0.5 - (0.15);
    hmsgb.String = 'Open FSLView';
    uiwait(hmsg);
    
    %% Open FSLView & ask user to decide
    reop_btn = 'Re-open FSLView';
    which_reg = reop_btn;
    while strcmp(which_reg,reop_btn)
        fslview_command = 'fslview';
        [s,~] = system(sprintf('%s %s -l Greyscale %s -l Copper -t 0.5 %s -l Blue-Lightblue -t 0.5',fslview_command,paths.anat_file,flirt_out_file,fnirt_out_file));
        if s == 127
            error('Could not find %s! \nChange the ''fslview_command'' variable (3 lines above this error), \nto match with the way fslview is called on your system.',fslview_command)
        end
        %% Time for the user to choose
        which_reg = questdlg('Which registration was the best?','Time to decide','FLIRT','FNIRT',reop_btn,reop_btn);
    end
    spm_jsonwrite(paths.which_reg_file,which_reg)
    
    %% Register prob maps to anat
    fprintf('Registering prob maps...')
    reg_prob_maps = cell(3,1);
    for i = 1:3
        in_file = paths.template_tissue{i};
        out_file = fullfile(paths.segmentation,sprintf('%s_prob_%i_%s.nii',paths.template_name,i,lower(which_reg)));
        if exist(out_file,'file') == 2; delete(out_file);end
        if strcmp(which_reg,'FLIRT')
            system(sprintf('%sflirt -in %s -ref %s -out %s -interp nearestneighbour -applyxfm -init %s',paths.FSL_prefix,in_file,paths.anat_file_brain,out_file,temp2anat_xfm));
        elseif strcmp(which_reg,'FNIRT')
            system(sprintf('%sapplywarp --ref=%s --in=%s --out=%s --warp=%s --interp=nn',paths.FSL_prefix,paths.anat_file,in_file,out_file,cout_file));
        end
        system(sprintf('gunzip %s',out_file));
        reg_prob_maps{i} = out_file;
    end
    
    % also register stg-sts mask
    if isfield(paths,'STS_STG_mask')
        if exist(paths.STS_STG_reg_mask,'file') == 2; delete(paths.STS_STG_reg_mask);end
        if strcmp(which_reg,'FLIRT')
            system(sprintf('%sflirt -in %s -ref %s -out %s -interp nearestneighbour -applyxfm -init %s',paths.FSL_prefix,paths.STS_STG_mask,paths.anat_file_brain,paths.STS_STG_reg_mask,temp2anat_xfm));
        elseif strcmp(which_reg,'FNIRT')
            system(sprintf('%sapplywarp --ref=%s --in=%s --out=%s --warp=%s --interp=nn --datatype=short',paths.FSL_prefix,paths.anat_file,paths.STS_STG_mask,paths.STS_STG_reg_mask,cout_file));
        end
        system(sprintf('gunzip %s',paths.STS_STG_reg_mask));
    end
    fprintf(' done.\n')
      
    %% Perform SPM segmentation
    spm_old_segment(paths.anat_file,reg_prob_maps{1},reg_prob_maps{2},reg_prob_maps{3},paths)
     
else
    error('No brain segmentation yet possible for this species...')
end

%% Perform FSL segmentation using the brain extracted by the SPM segmentation
fsl_fast(paths.anat_file_brain,paths)
[~,anat_file] = fileparts(paths.anat_file);
movefile(fullfile(paths.segmentation,'FSL',[anat_file '_brain_pveseg.nii.gz']),paths.anat_file_brain_segmentation.fsl.segmentation);

%% Save figures of anat overlaid with the segmentation
[~,name,ext] = fileparts(paths.anat_file);
cm = lines(7);
cm = cm([1 1 3 7],:);
view_slice_overlay(paths.anat_file,paths.anat_file_brain_segmentation.spm.segmentation,0,[],0.3,[],cm)
figurewrite(fullfile(paths.segmentation,[name '_brain_segmented_spm'])) % Using GLMdenoise function

view_slice_overlay(paths.anat_file,paths.anat_file_brain_segmentation.fsl.segmentation,0,[],0.3,[],cm)
figurewrite(fullfile(paths.segmentation,[name '_brain_segmented_fsl'])) % Using GLMdenoise function

view_slice_overlay(paths.anat_file,paths.anat_file_brain,0)
figurewrite(fullfile(paths.segmentation,[name '_brain'])) % Using GLMdenoise function

view_slice_overlay(paths.anat_file,paths.anat_file_brain_mask,0,[],0.3,[],cm)
figurewrite(fullfile(paths.segmentation,[name '_brain_mask'])) % Using GLMdenoise function

view_slice_overlay(paths.anat_file,paths.anat_file_brain_mask_dil,0,[],0.3,[],cm)
figurewrite(fullfile(paths.segmentation,[name '_brain_mask_dil'])) % Using GLMdenoise function

%% Choose which segmentation will be used
choose_which_seg

%% Create 01 & 99 percents masks for each tissue
tissues = fieldnames(paths.anat_file_brain_segmentation.(paths.which_seg).tissues);
probs = paths.tissues_probs;
for i = 1:numel(tissues)
    for p = 1:numel(probs)
        % Create a mask of voxels with prob >= probs-percent
        maths_out_file = paths.(sprintf('anat_file_tissues_%sp',probs{p})).(tissues{i});
        if exist(maths_out_file,'file') == 2; delete(maths_out_file);end
        system(sprintf('%sfslmaths %s -thr 0.%s %s',paths.FSL_prefix,paths.anat_file_brain_segmentation.(paths.which_seg).tissues.(tissues{i}),probs{p},maths_out_file));
        system(sprintf('%sfslmaths %s -bin %s -odt short',paths.FSL_prefix,maths_out_file,maths_out_file));
        system(sprintf('gunzip %s',maths_out_file));
        
        % Keep the largest cluster
        P = spm_vol(maths_out_file);
        mask = spm_read_vols(P);
        [labels,num] = bwlabeln(mask,18);
        cluster_size = nan(num,1);
        for n = 1:num
            idx = labels == n;
            cluster_size(n) = sum(idx(:));
        end
        [~,largest_cluster] = max(cluster_size);
        mask = labels == largest_cluster;
        spm_write_vol(P,mask);
    end
end

%% Create white + csf mask
out_file = paths.anat_file_tissues_white_csf_mask;
if exist(out_file,'file') == 2; delete(out_file);end
system(sprintf('%sfslmaths %s -add %s %s',paths.FSL_prefix,paths.anat_file_tissues_99p.white,paths.anat_file_tissues_99p.csf,out_file)); % combine white and csf masks
system(sprintf('%sfslmaths %s -sub %s %s',paths.FSL_prefix,out_file,paths.anat_file_tissues_01p.grey,out_file)); % remove voxels that might be in the grey matter
system(sprintf('%sfslmaths %s -bin %s',paths.FSL_prefix,out_file,out_file)); % binarize
system(sprintf('%sfslmaths %s -kernel boxv 3 -ero %s',paths.FSL_prefix,out_file,out_file)); % erode mask (to be sure no voxels of interest will be selected)
system(sprintf('gunzip %s',out_file));


%% TRASH


%     %% Register standard neurological
%     fprintf('Registering to standard neurological template...')
%     %% flirt standard neurological to anat-brain
%     in_file = fullfile(paths.std_atlas,'standard_neurological.nii.gz');
%     out_file = fullfile(paths.segmentation,'standard_neurological_flirt.nii');
%     xfm_file_std = fullfile(paths.segmentation,'std-to_anat.xfm');
%     if exist(out_file,'file') == 2; delete(out_file);end
%     system(sprintf('%sflirt -in %s -ref %s -out %s -cost normcorr -omat %s',paths.FSL_prefix,in_file,paths.anat_file_BET,out_file,xfm_file_std));
%     system(sprintf('gunzip %s',out_file));
%
%     %% Save figure of anat overlaid with standard neurological
%     view_slice_overlay(paths.anat_file,out_file,0)
%     figurewrite(fullfile(paths.segmentation,'std-to_anat_flirt')) % Using GLMdenoise function
%
%     % No fnirt here because standard neurological does not come with an
%     % unbetted version of the atlas
%
%     %% Register prob maps to anat
%     for i = 1:17
%         in_file = fullfile(paths.std_atlas,sprintf('ProbMapAC%i.nii.gz',i));
%         out_file = fullfile(paths.segmentation,sprintf('ProbMapAC%i_flirt.nii',i));
%         if exist(out_file,'file') == 2; delete(out_file);end
%         system(sprintf('%sflirt -in %s -ref %s -out %s -interp nearestneighbour -applyxfm -init %s',paths.FSL_prefix,in_file,paths.anat_file_BET,out_file,xfm_file_std));
% %         system(sprintf('gunzip %s',out_file));
%     end
%
%     mask_files = {'Mask_ROIs.nii.gz';'Mask_dil_ROIs.nii.gz';'Merged_ROIs.nii.gz'};
%     for i = 1:numel(mask_files)
%         in_file = fullfile(paths.std_atlas,mask_files{i});
%         out_file = fullfile(paths.segmentation,[fileparts2(mask_files{i}) '_flirt.nii']);
%         if exist(out_file,'file') == 2; delete(out_file);end
%         system(sprintf('%sflirt -in %s -ref %s -out %s -interp nearestneighbour -applyxfm -init %s',paths.FSL_prefix,in_file,paths.anat_file_BET,out_file,xfm_file_std));
%         % Save figure of anat overlaid with merged ROIs
%         view_slice_overlay(paths.anat_file,[out_file '.gz'],0,[],0.5,[],lines(18))
%         figurewrite(fullfile(paths.segmentation,[fileparts2(mask_files{i}) '_flirt'])) % Using GLMdenoise function
%     end
%
%     fprintf(' done.\n')

