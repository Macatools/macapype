%% SCRIPT
% to be run after parameters_*

%% Run spm_BIDS
fprintf('Retrieving BIDS informations...')
BIDS = spm_BIDS(paths.dataset);
fprintf(' done.\n\n')

%% Get species
known_species = {'human';'macaque';'marmoset';'baboon'};

if isempty(BIDS.participants)
    error('There must be a ''participants.tsv'' file in the BIDS folder!!')
elseif ~isfield(BIDS.participants,'species')
    error('There must be a ''species'' column in the ''participants.tsv'' file!!')
else
    pn = find(strcmp(BIDS.participants.participant_id,['sub-' paths.subject]));
    if isempty(pn)
        error('Could not find participant in the ''participants.tsv'' file!!')
    elseif length(pn) > 1
        error('There are more than one participant with the ID ''%s'' in the ''participants.tsv'' file!!',['sub-' paths.subject])
    else
        paths.species = BIDS.participants.species{pn};
        if ~strcmp(paths.species,known_species)
            error('Species in the ''participants.tsv'' file must be exactly one of those:\n%s',sprintf('%s\n',known_species{:}))
        end
        paths.contrast_agent = BIDS.participants.contrast_agent{pn};
        
        fprintf('Subject: %s\n',BIDS.participants.name{pn})
        if ~strcmpi(paths.contrast_agent,'none')
            fprintf('Contrast agent: %s\n',BIDS.participants.contrast_agent{pn})
        end
    end
end

%% Unzip files if necessary
BIDS = gunzip_all_data(BIDS,paths,1);


%% Paths

paths.subject_analysis = fullfile(paths.dataset,['analysis_sub-' paths.subject]); % All analyses for this subject

paths.segmentation_root = fullfile(paths.subject_analysis,'segmentation'); % folder where the segmented brain files will be

paths.analysis = fullfile(paths.subject_analysis,paths.realign_name); % folder where one analysis corresponding to a certain realign name will be

paths.realign = sprintf('%s/realignment',paths.analysis); % realignment matrices

paths.tmp_nii = sprintf('%s/tmp_nii',paths.analysis); % tmp folder to store original bols with updated headers

paths.rp_files = sprintf('%s/rp_files',paths.realign); % folder for the rp_files

paths.resliced = sprintf('%s/resliced',paths.analysis); % folder where the resliced motion corrected images will be

paths.fieldmaps = sprintf('%s/fieldmaps',paths.analysis); % folder where the all the fieldmaps associated images will be

paths.PCA = fullfile(paths.analysis,'PCA'); % folder where the PCA results will be

paths.T1_normalized = fullfile(paths.analysis,'T1_normalized'); % folder where the PCA results will be

paths.results = fullfile(paths.analysis,['results_' paths.results_name]); % folder where the results will be

paths.results_indiv_runs = fullfile(paths.results,'individual_runs'); % folder where the results for individual runs will be

paths.GLMdenoise = fullfile(paths.results,sprintf('GLMdenoise_%iPCs',GLM_params.GLMdenoise_nPCA_PCs)); % folder where the PCA results will be

paths.AC_folder = fullfile(paths.results,'Activations');


%% create sessions / runs structure
SR = struct_sess_run(BIDS,sessions,runs,paths);

paths.in_jack = 0;
ST = dbstack;
for i = 1:numel(ST)
    if strcmp(ST(i).name,'launch_jackknife')
        paths.in_jack = 1;
        [sessions,runs,rem_session,rem_run] = get_sessions_runs_jackknife(SR,run_index);
        SR = struct_sess_run(BIDS,sessions,runs,paths);
        paths.results_jack_name = sprintf('%s_Jackknife_ses-%02.0f-run-%02.0f',paths.results_name,rem_session,rem_run);
        paths.results_multi = fullfile(paths.results,sprintf('Jackknife_%02.0f-%02.0f',rem_session,rem_run));
        break
    end
    if strcmp(ST(i).name,'select_jackrank')
        paths.in_jack = 1;
        jackknife_results
        [sessions,runs] = select_from_jack_ranks(sessions,runs,jack_ranks,max_rank);
        SR = struct_sess_run(BIDS,sessions,runs,paths);
        paths.results_jack_name = sprintf('%s_Jackknife_rank-%03.0f',paths.results_name,max_rank);
        paths.results_multi = fullfile(paths.results,sprintf('Jackknife_rank-%03.0f',max_rank));
        break
    end
end

if isempty(SR)
    fprintf('\n\n')
    warning('No functional data was found!!')
else
    n_total_runs = 0;
    for s = 1:numel(SR)
        n_total_runs = n_total_runs + length(SR(s).runs);
    end
end

%% End of Paths

if ~paths.in_jack
    if isfield(paths,'results_sub_folder') && ~isempty(paths.results_sub_folder)
        paths.results_multi = fullfile(paths.results,paths.results_sub_folder);
    else
        paths.results_multi = paths.results;
    end
end


%% Atlases
if strcmp(paths.species,'macaque')
    if strcmp(paths.template_name,'inia19')
        paths.template = fullfile(fileparts(which('RunScript.m')),'templates','inia19');
        paths.template_brain = fullfile(paths.template,'inia19-t1-brain.nii.gz');
        paths.template_brain_mask = fullfile(paths.template,'inia19-brainmask.nii.gz');
        paths.template_head = fullfile(paths.template,'inia19-t1.nii.gz');
        paths.template_tissue{1} = fullfile(paths.template,'inia19-prob_1.nii.gz');
        paths.template_tissue{2} = fullfile(paths.template,'inia19-prob_2.nii.gz');
        paths.template_tissue{3} = fullfile(paths.template,'inia19-prob_0.nii.gz');
        paths.STS_STG_mask = fullfile(paths.template,'inia19-STS_STG_dil.nii.gz');
    elseif strcmp(paths.template_name,'NMT')
%         paths.template = fullfile(fileparts(which('RunScript.m')),'templates','NMT_v1.2');
%         paths.template_brain = fullfile(paths.template,'NMT_SS.nii.gz');
%         paths.template_brain_mask = fullfile(paths.template,'masks','anatomical_masks','NMT_brainmask.nii.gz');
%         paths.template_head = fullfile(paths.template,'NMT.nii.gz');
%         paths.template_tissue{1} = fullfile(paths.template,'masks','probabilisitic_segmentation_masks','NMT_segmentation_GM.nii.gz');
%         paths.template_tissue{2} = fullfile(paths.template,'masks','probabilisitic_segmentation_masks','NMT_segmentation_WM.nii.gz');
%         paths.template_tissue{3} = fullfile(paths.template,'masks','probabilisitic_segmentation_masks','NMT_segmentation_CSF.nii.gz');
%         paths.STS_STG_mask = fullfile(paths.template,'NMT_STS_STG_dil.nii.gz');

        paths.template = fullfile(fileparts(which('RunScript.m')),'templates','NMT_v1.2');
        paths.template_brain = fullfile(paths.template,'NMT_SS.nii.gz');
        paths.template_brain_mask = fullfile(paths.template,'masks','anatomical_masks','NMT_brainmask.nii.gz');
        paths.template_head = fullfile(paths.template,'NMT.nii.gz');
        paths.template_tissue{1} = fullfile(paths.template,'FSL','NMT_SS_pve_1.nii.gz');
        paths.template_tissue{2} = fullfile(paths.template,'FSL','NMT_SS_pve_2.nii.gz');
        paths.template_tissue{3} = fullfile(paths.template,'FSL','NMT_SS_pve_3.nii.gz');
        paths.STS_STG_mask = fullfile(paths.template,'NMT_STS_STG_dil.nii.gz');
    else
        error('Template ''%s'' is not available.\nModify your parameters file.',paths.template_name)
    end
    
elseif strcmp(paths.species,'marmoset')
    if strcmp(paths.template_name,'BSI-NI')
        paths.template = fullfile(fileparts(which('RunScript.m')),'templates','The_Marmoset_MRI_Standard_Brain');
        paths.template_brain = fullfile(paths.template,'Template_T1_brain.nii.gz');
        paths.template_head = fullfile(paths.template,'Template_T1_head.nii.gz');
        paths.template_tissue{1} = fullfile(paths.template,'grey.nii.gz');
        paths.template_tissue{2} = fullfile(paths.template,'white.nii.gz');
        paths.template_tissue{3} = fullfile(paths.template,'csf.nii.gz');
    else
        error('Template ''%s'' is not available.\nModify your parameters file.',paths.template_name)
    end
end

%% Main anat file
anat_file = spm_BIDS(BIDS,'data','sub',paths.subject,'type',paths.main_anat_suffix,'ses',sprintf('%02.0f',paths.main_anat_session));
if isempty(anat_file); error('No anatomic scan of type''%s'' found in session %02.0f.\nModify your parameters file.',paths.main_anat_suffix,paths.main_anat_session); end

%% Cropped version of the main anat file
[anat_path,anat_name] = fileparts(anat_file{1});
anat_file_nocrop = fullfile(anat_path,[anat_name '.nocrop']);

if ~exist(anat_file_nocrop,'file')
    anat_file_cropped = spm_BIDS(BIDS,'data','sub',paths.subject,'type',[paths.main_anat_suffix 'Cropped'],'ses',sprintf('%02.0f',paths.main_anat_session),'modality','anat');
    if isempty(anat_file_cropped)
        uiwait(warndlg('No cropped version of the anatomic scan was found.'))
        answer = questdlg('Do you want to crop the anatomic scan now?','','Yes','No','No & don''t ask again','Yes');
        if strcmp(answer,'Yes')
            paths.anat_file = anat_file{1};
            force_type = ['_' paths.main_anat_suffix '.nii'];
            crop_volume
        elseif strcmp(answer,'No & don''t ask again')
            spm_jsonwrite(anat_file_nocrop,struct('nocrop_file',[anat_name ' will not be cropped. Delete this ''.nocrop'' file if you want to crop it anyway']))
        end
        warning('Please re-run your parameters file')
        return
    else
        paths.anat_file = anat_file_cropped{1};
        paths.main_anat_suffix = [paths.main_anat_suffix 'Cropped'];
    end
else
    paths.anat_file = anat_file{1};
end


%% N4 version of the main anat file
if isfield(paths,'ANTS_path')
    [anat_path,anat_name] = fileparts(paths.anat_file);
    anat_file_noN4 = fullfile(anat_path,[anat_name '.noN4']);
    paths.N4iterations_file = fullfile(anat_path,[anat_name '.N4iterations']);

    if ~exist(anat_file_noN4,'file')
        anat_file_N4 = spm_BIDS(BIDS,'data','sub',paths.subject,'type',[paths.main_anat_suffix 'N4'],'ses',sprintf('%02.0f',paths.main_anat_session),'modality','anat');
        if isempty(anat_file_N4)
            uiwait(warndlg('No bias field corrected (N4) version of the anatomic scan was found.'))
            answer = questdlg('Do you want to run N4 on the anatomic scan now?','','Yes','No','No & don''t ask again','Yes');
            
            if strcmp(answer,'Yes')
        		[paths.anat_file,N4ed,N4iterations] = ANTS_N4(paths.anat_file,paths.ANTS_path);
        		paths.main_anat_suffix = [paths.main_anat_suffix 'N4'];
                spm_jsonwrite( paths.N4iterations_file,N4iterations)
	        elseif strcmp(answer,'No')
    	        warning('Please re-run your parameters file')
    	        return
    	    end
    	    if strcmp(answer,'No & don''t ask again') || (exist('N4ed','var') && ~N4ed)
    	        spm_jsonwrite(anat_file_noN4,struct('noN4_file',[anat_name ' will not be bias field corrected. Delete this ''.noN4'' file if you want to unbias it it anyway']))
    	    end
        else
            paths.anat_file = anat_file_N4{1};
            paths.main_anat_suffix = [paths.main_anat_suffix 'N4'];
        end
    end
end


%% Denoised version of the main anat file
[anat_path,anat_name] = fileparts(paths.anat_file);
anat_file_noDenoise = fullfile(anat_path,[anat_name '.noDenoise']);

if ~exist(anat_file_noDenoise,'file')
    anat_file_Denoise = spm_BIDS(BIDS,'data','sub',paths.subject,'type',[paths.main_anat_suffix 'Denoised'],'ses',sprintf('%02.0f',paths.main_anat_session),'modality','anat');
    if isempty(anat_file_Denoise)
        uiwait(warndlg('No denoised version of the anatomic scan was found.'))
        answer = questdlg('Do you want to denoise the anatomic scan now?','','Yes','No','No & don''t ask again','Yes');
        if strcmp(answer,'Yes')
        	[paths.anat_file,denoised] = spm_sanlm(paths.anat_file);
        	paths.main_anat_suffix = [paths.main_anat_suffix 'Denoised'];
        elseif strcmp(answer,'No')
            warning('Please re-run your parameters file')
            return
        end
        if strcmp(answer,'No & don''t ask again') || (exist('denoised','var') && ~denoised)
            spm_jsonwrite(anat_file_noDenoise,struct('noDenoise_file',[anat_name ' will not be denoised. Delete this ''.noDenoise'' file if you want to denoise it it anyway']))
        end
    else
        paths.anat_file = anat_file_Denoise{1};
        paths.main_anat_suffix = [paths.main_anat_suffix 'Denoised'];
    end
end


% %% T2 files
% T2_reg_suffix = 'CroppedReg';
% if isfield(paths,'T2_anat_suffix')
%     T2_file = spm_BIDS(BIDS,'data','sub',paths.subject,'type',paths.T2_anat_suffix);
%     if ~isempty(T2_file) % if there is a T2 file
%         T2_file_reg = spm_BIDS(BIDS,'data','sub',paths.subject,'type',[paths.T2_anat_suffix T2_reg_suffix]);
%         if isempty(T2_file_reg) % if it has not been registered to the T1
%             fprintf('Registering T2 to T1...\n')
%             in_file = T2_file{1};
%             [pathstr,name,ext] = fileparts(T2_file{1});
%             out_file = fullfile(pathstr,[name T2_reg_suffix ext]);
%             if exist(out_file,'file') == 2; delete(out_file);end
%             system(sprintf('%sflirt -in %s -ref %s -out %s -dof 6',paths.FSL_prefix,in_file,paths.anat_file,out_file));
%             system(sprintf('gunzip %s',out_file));
%             % Warn user
%             hmsg = msgbox('The T2 scan has been registered to the T1 scan. Check registration on FSLView (by changing opacity of the T2) & close FSLView.');
%             hmsgb = findobj(hmsg,'Style','pushbutton');
%             hmsgb.Units = 'normalized';
%             hmsgb.Position(3) = 0.3;
%             hmsgb.Position(1) = 0.5 - (0.15);
%             hmsgb.String = 'Open FSLView';
%             uiwait(hmsg)
%     
%             % Open fslview
%             fslview_command = 'fslview';
%             [s,~] = system(sprintf('%s %s -l Greyscale %s -l Copper',fslview_command,paths.anat_file,out_file));
%             if s == 127
%                 error('Could not find %s! \nChange the ''fslview_command'' variable (3 lines above this error), \nto match with the way fslview is called on your system.',fslview_command)
%             end
%             % Update BIDS
%             BIDS = spm_BIDS(paths.dataset);
%             T2_file_reg = spm_BIDS(BIDS,'data','sub',paths.subject,'type',[paths.T2_anat_suffix T2_reg_suffix]);
%         end
%         paths.T2_file = T2_file_reg{1};
%     else
%         error('No T2 scan of type''%s'' found',paths.T2_anat_suffix)
%     end
% end

%% Segmentation
[~,anat_name,ext] = fileparts(paths.anat_file);

if strcmp(paths.species,'human')
    paths.segmentation = fullfile(paths.segmentation_root,anat_name); % folder where the segmented brain files will be
else
    paths.segmentation = fullfile(paths.segmentation_root,[paths.template_name '_' anat_name]); % folder where the segmented brain files will be
end

paths.which_reg_file = fullfile(paths.segmentation,'chosen_template_registration.json');
paths.which_seg_file = fullfile(paths.segmentation,'chosen_segmentation.json');

paths.anat_file_BET = fullfile(paths.segmentation_root,[anat_name '_BET.nii']);
if ~exist(paths.anat_file_BET,'file')
    uiwait(warndlg('No brain extraction from the anatomic scan was found.'))
    answer = questdlg('Do you want to run the brain extraction now?','','Yes','No','Yes');
    if strcmp(answer,'Yes')
        force_type = [anat_name ext];
        brain_extraction
        warning('Please re-run your parameters file')
    end
    return
else
	paths.anat_file_brain = fullfile(paths.segmentation,[anat_name '_brain.nii']);
    paths.anat_file_brain_mask = fullfile(paths.segmentation,[anat_name '_brain_mask.nii']);
    paths.anat_file_brain_mask_dil = fullfile(paths.segmentation,[anat_name '_brain_mask_dil.nii']);
    paths.anat_file_brain_segmentation.spm.segmentation = fullfile(paths.segmentation,[anat_name '_brain_segmented_SPM.nii']);
    paths.anat_file_brain_segmentation.spm.tissues.grey = fullfile(paths.segmentation,['c1' anat_name '.nii']);
    paths.anat_file_brain_segmentation.spm.tissues.white = fullfile(paths.segmentation,['c2' anat_name '.nii']);
    paths.anat_file_brain_segmentation.spm.tissues.csf = fullfile(paths.segmentation,['c3' anat_name '.nii']);
    paths.anat_file_brain_segmentation.fsl.segmentation = fullfile(paths.segmentation,'FSL',[anat_name '_brain_segmented_FSL.nii.gz']);
    paths.anat_file_brain_segmentation.fsl.tissues.grey = fullfile(paths.segmentation,'FSL',[anat_name '_brain_pve_1.nii.gz']);
    paths.anat_file_brain_segmentation.fsl.tissues.white = fullfile(paths.segmentation,'FSL',[anat_name '_brain_pve_2.nii.gz']);
    paths.anat_file_brain_segmentation.fsl.tissues.csf = fullfile(paths.segmentation,'FSL',[anat_name '_brain_pve_3.nii.gz']);
    
    tissues = fieldnames(paths.anat_file_brain_segmentation.spm.tissues);
    paths.tissues_probs = {'01';'50';'99'};
    probs = paths.tissues_probs;
    for i = 1:numel(tissues)
        paths.func_tissues.(tissues{i}) = fullfile(paths.resliced,sprintf('sub-%s_func_%s_prob.nii',paths.subject,tissues{i}));
        for p = 1:numel(probs)
            paths.(sprintf('anat_file_tissues_%sp',probs{p})).(tissues{i}) = fullfile(paths.segmentation,sprintf('%s_%s_%sp.nii',anat_name,tissues{i},probs{p}));
            paths.(sprintf('func_tissues_%sp',probs{p})).(tissues{i}) = fullfile(paths.resliced,sprintf('sub-%s_func_%s_%sp.nii',paths.subject,tissues{i},probs{p}));
        end
    end
    
    paths.anat_file_tissues_white_csf_mask = fullfile(paths.segmentation,sprintf('%s_white_csf_mask.nii',anat_name));
    
    paths.func_tissues_white_csf_mask = fullfile(paths.resliced,['sub-' paths.subject '_func_white_csf_mask.nii']);
    paths.func_brain_mask = fullfile(paths.resliced,['sub-' paths.subject '_func_brain_mask.nii']);
    
    paths.STS_STG_reg_mask = fullfile(paths.segmentation,[anat_name '_STS_STG_mask.nii']);
    paths.func_STS_STG_reg_mask = fullfile(paths.resliced,['sub-' paths.subject '_func_STS_STG_reg_mask.nii']);
    
    if ~exist(paths.anat_file_brain_segmentation.spm.segmentation,'file')
        uiwait(warndlg('No brain segmentation from the anatomic scan was found.'))
        answer = questdlg('Do you want to run the brain segmentation now?','','Yes','No','Yes');
        if strcmp(answer,'Yes')
            brain_segmentation
            warning('Please re-run your parameters file')
        end
        return
    end
end

% Chosen segmentation (SPM or FSL)
if ~exist(paths.which_seg_file,'file')
    choose_which_seg
else
    paths.which_seg = spm_jsonread(paths.which_seg_file);
end


%% Other files
paths.reference_scan = fullfile(paths.resliced,'Reference_scan.nii');
paths.reference_scan_infos = fullfile(paths.realign,'Reference_scan_infos.mat');
if paths.in_jack
    paths.log_file_params = sprintf('%s/Params_%s.log',paths.analysis,paths.results_jack_name);
else
    paths.log_file_params = sprintf('%s/Params_%s.log',paths.analysis,paths.results_name);
end
paths.log_file_realign = sprintf('%s/Realignment.log',paths.analysis);

paths.average = fullfile(paths.resliced,sprintf('Average_%s.nii',paths.realign_name));

if coreg_params.use_daily_anat
	reg_suffix = ['_' coreg_params.daily_anat_method];
else
	reg_suffix = '';
end

paths.average_to_anat = fullfile(paths.resliced,sprintf('Average_%s_to_anat_%s%s.nii',paths.realign_name,coreg_params.method,reg_suffix));
paths.average_to_anat_xfm = fullfile(paths.resliced,sprintf('Average_%s_to_anat_%s%s.xfm',paths.realign_name,coreg_params.method,reg_suffix));
paths.anat_to_average_xfm = fullfile(paths.resliced,sprintf('Anat_to_average_%s_%s%s.xfm',paths.realign_name,coreg_params.method,reg_suffix));
paths.average_to_anat_warp = fullfile(paths.resliced,sprintf('Average_%s_to_anat_warp_%s%s.nii',paths.realign_name,coreg_params.method,reg_suffix));
paths.anat_to_average_warp = fullfile(paths.resliced,sprintf('Anat_to_average_%s_warp_%s%s.nii',paths.realign_name,coreg_params.method,reg_suffix));
paths.no_mask = fullfile(paths.resliced,['sub-' paths.subject '_func_no_mask.nii']);

paths.betanames = sprintf('%s/BetaNames.txt',paths.results);
paths.sessnums = sprintf('%s/SessNums.txt',paths.results);
paths.combined_cons = sprintf('%s/Betas.nii',paths.results);
paths.thres_file = sprintf('%s/thresholds.mat',paths.results);

paths.realign_params = fullfile(paths.realign,'realign_params.mat');
paths.GLM_params = fullfile(paths.results_indiv_runs,'GLM_params.mat');

paths.GLM_noisereg_file = fullfile(paths.GLMdenoise,'GLM_noisereg.mat');
paths.GLM_denoise_params = fullfile(paths.GLMdenoise,'GLM_denoise_params.mat');


% Mask used to run the analysis
mask_types = {'';'brain';'grey';'auditory'};
if ~any(strcmp(GLM_params.mask_type,mask_types))
    error('Mask type ''%s'' unknown',GLM_params.mask_type)
end

switch GLM_params.mask_type
    case ''
        paths.func_mask = paths.no_mask;
    case 'brain'
        paths.func_mask = paths.func_brain_mask;
        paths.anat_mask = paths.anat_file_brain_mask;
    case 'grey'
        paths.func_mask = paths.func_tissues_01p.grey;
        if ~exist(paths.anat_file_tissues_01p.grey,'file')
            system(sprintf('%sfslmaths %s -thr 0.01 %s',paths.FSL_prefix,paths.anat_file_brain_segmentation.(paths.which_seg).tissues.grey,paths.anat_file_tissues_01p.grey));
            system(sprintf('%sfslmaths %s -bin %s -opt short',paths.FSL_prefix,paths.anat_file_tissues_01p.grey,paths.anat_file_tissues_01p.grey));
        end
        paths.anat_mask = paths.anat_file_tissues_01p.grey;
    case 'auditory'
        if isfield(paths,'STS_STG_mask')
            paths.func_mask = paths.func_STS_STG_reg_mask;
            paths.anat_mask = paths.STS_STG_reg_mask;
        else
            error('There is no ''auditory'' mask available for this species')
        end
end

%% Stop here if there is no functionnal data
if isempty(SR)
    return
end

%% Check some params
if ~ismember(GLM_params.motion_reg_type,[0 1 2 3])
    error('GLM_params.motion_reg_type value should be 0, 1, 2 or 3')
end

if (n_total_runs < 2) && GLM_params.GLMdenoise
    error('Cannot run GLMdenoise if the total number of runs is less than n=%i\nChange your parameters to correct this error (GLM_params.GLMdenoise_nPCA_PCs).',2)
end

%% scan info
if exist('scan_info','var')
    clear scan_info scan_log
end
run_id = 0;
for s = 1:numel(SR)
    session = SR(s).session;
    runs = SR(s).runs;
    for r = 1:length(runs)
        run = runs(r);
        run_id = run_id + 1;
        json_file = [fileparts2(SR(s).filename{r}) '.json'];
        try % fetch all json files and put them into scan_info
            ScanInfos = spm_jsonread(json_file);
            fn = fieldnames(ScanInfos);
            for f = 1:numel(fn)
                field = fn{f};
                scan_info(s,r).(field) = ScanInfos.(field);
            end
        catch ME
            error('.json file of session %02.0f, run %02.0f is different from the previous one(s)\nMatlab error:\n%s',SR(s).session,runs(r),getReport(ME,'extended'))
        end
        
        ScanLog_file = fullfile(paths.dataset,'sourcedata',['sub-' paths.subject],sprintf('ses-%02.0f',session),'func',[SR(s).namebase{r} '_ScanLog.mat']);
        
%         pathstr = fileparts(fileparts(SR(s).filename{r}));
%         ScanLog_file = fullfile(pathstr,'ScanLogs',[SR(s).namebase{r} '_ScanLog.mat']);
        
        if exist('ScanLog','var'); clear ScanLog; end
        load(ScanLog_file)
        try % fetch all ScanLogs & check if they are all similar
%             scan_log(s,r) = ScanLog; % this line doesn't work if the
%             order the fields in the structs is different. Solved with the
%             four following lines
            fn = fieldnames(ScanLog);
            for f = 1:numel(fn)
                field = fn{f};
                scan_log(s,r).(field) = ScanLog.(field);
            end
            
            if run_id == 1
                ScanLog_ref = ScanLog; % first run is the reference for validation
                nlevels = numel(fieldnames(ScanLog_ref.fMRISTAT));
            else
                if ~strcmp(ScanLog_ref.subject,scan_log(s,r).subject)
                    error('ScanLog of session %02.0f, run %02.0f is for a different subject than the previous one(s)',SR(s).session,runs(r))
                end
                if ~strcmp(ScanLog_ref.TaskName,scan_log(s,r).TaskName)
                    error('ScanLog of session %02.0f, run %02.0f is for a different task than the previous one(s)',SR(s).session,runs(r))
                end
                try
                    for L = 1:nlevels
                        if any(~cellfun(@strcmp,ScanLog_ref.fMRISTAT.(['L' num2str(L)]).names,scan_log(s,r).fMRISTAT.(['L' num2str(L)]).names))
                            error('Conditions of session %02.0f, run %02.0f, level %i are different from the previous one(s)',SR(s).session,runs(r),L)
                        end
                    end
                catch MEfor
                    error('Conditions do not match between runs\nMatlab error:\n%s',getReport(MEfor,'extended'))
                end
            end
        catch ME
            error('ScanLog of session %02.0f, run %02.0f is different from the previous one(s)\nMatlab error:\n%s',SR(s).session,runs(r),getReport(ME,'extended'))
        end
    end
end

%%%%%%% Until the dcm2nii converter at CERIMED gives us those info in the json files, read the header using FSL:
for s = 1:numel(SR)
    session = SR(s).session;
    runs = SR(s).runs;
    for r = 1:length(runs)
        run = runs(r);
        fname = spm_BIDS(BIDS,'data','sub',paths.subject,'ses',sprintf('%02.0f',session),'run',sprintf('%02.0f',run),'type','bold','task',paths.task);
        [~,comres] = system([paths.FSL_prefix 'fslval ' fname{1} ' dim4']);
        scan_info(s,r).NumberOfVolumesInFile = str2double(comres);
        [~,comres] = system([paths.FSL_prefix 'fslval ' fname{1} ' pixdim1']);
        scan_info(s,r).VoxelSizeX = str2double(comres);
        [~,comres] = system([paths.FSL_prefix 'fslval ' fname{1} ' pixdim2']);
        scan_info(s,r).VoxelSizeY = str2double(comres);
        [~,comres] = system([paths.FSL_prefix 'fslval ' fname{1} ' dim3']);
        scan_info(s,r).NumberOfSlices = str2double(comres);
    end
end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

if (length(unique([scan_info.RepetitionTime])) ~= 1)% || (length(unique([scan_info.nslices])) ~= 1)
    warning('Runs have different TRs')
end
if (length(unique([scan_info.VoxelSizeX])) ~= 1) || (length(unique([scan_info.VoxelSizeY])) ~= 1) || (length(unique([scan_info.SliceThickness])) ~= 1)
    warning('Runs have different voxel sizes')
end

PEDs = cell(n_total_runs,1);
sr = cell(n_total_runs,2);
i = 0;
for s = 1:numel(SR)
    session = SR(s).session;
    runs = SR(s).runs;
    for r = 1:length(runs)
        run = runs(r);
        i = i + 1;
        PEDs{i} = scan_info(s,r).PhaseEncodingDirection;
        sr{i,1} = session;
        sr{i,2} = run;
    end
end

if n_total_runs > 1
	if ~isequal(PEDs{:})
	    warning('Runs have different Phase Encoding Directions:')
	    eval('[{''ses'' ''run'' ''PED''};sr PEDs]')
	end
end

%% Display categories at each level
fprintf('\n')
for L = 1:nlevels
    if L == nlevels
        fprintf('### Categories in level %i:\n\tAll sounds (sound level)\n',L)
    else
        fprintf('### Categories in level %i:\n\t%s\n',L,strjoin(ScanLog_ref.fMRISTAT.(['L' num2str(L)]).names,', '))
    end
end
fprintf('\n')

%% Contrasts
contrasts.nconds = numel(ScanLog_ref.fMRISTAT.(['L' num2str(contrasts.L)]).names);
contrasts.names = cell(contrasts.nconds,1);
contrasts.names{1} = 'sound_vs_silence';
contrasts.weights = zeros(contrasts.nconds*2,contrasts.nconds);
contrasts.weights(1,:) = [ones(1,contrasts.nconds-1) -(contrasts.nconds-1)]; % silence always at the end
for c = 2:contrasts.nconds
    contrasts.names{c} = [ScanLog_ref.fMRISTAT.(['L' num2str(contrasts.L)]).names{c-1} '_vs_' ScanLog_ref.fMRISTAT.(['L' num2str(contrasts.L)]).names{end}];
    contrasts.weights(c,c-1) = 1;
    contrasts.weights(c,end) = -1;
end

c = 0;
for i = contrasts.nconds+1:contrasts.nconds+contrasts.nconds
    c = c + 1;
    contrasts.names{i} = ScanLog_ref.fMRISTAT.(['L' num2str(contrasts.L)]).names{c};
    contrasts.weights(i,c) = 1;
end

if exist('contrast_names','var')
    contrast_names = strrep(contrast_names,' ','_'); % deblank
    contrasts.names = [contrasts.names;contrast_names];
end
if exist('contrast_weights','var')
    contrasts.weights = [contrasts.weights;contrast_weights];
end

if isfield(contrasts,'restrict') || isfield(contrasts,'exclude')
    contrasts.weights(:,end+1) = 0; % add contrast column for exluded condition
end

%% Realign & Reslice wrap direction
PED = unique([scan_info.PhaseEncodingDirection]);
if strcmp(PED,'i')
    realign_flags.wrap = [1 0 0];
elseif strcmp(PED,'j')
    realign_flags.wrap = [0 1 0];
elseif strcmp(PED,'k')
    realign_flags.wrap = [0 0 1];
end
reslice_flags.wrap = realign_flags.wrap;

%% Use scan info for some parameters
mvt_params.TR = scan_info(1,1).RepetitionTime; % TR (in sec) of the first session first run (all TRs should be the same)
mvt_params.voxel_size(1) = unique([scan_info.VoxelSizeX]) * spm_resample_fact(1); % get voxel size of the protocol
mvt_params.voxel_size(2) = unique([scan_info.VoxelSizeY]) * spm_resample_fact(2);
mvt_params.voxel_size(3) = unique([scan_info.SliceThickness]) * spm_resample_fact(3);
realign_flags.sep = realign_flags.sep * min(mvt_params.voxel_size); %  % from voxels to mm, the default separation (mm) to sample the images.
realign_flags.fwhm = realign_flags.fwhm * min(mvt_params.voxel_size); % % from voxels to mm, The FWHM (mm) applied to the images before estimating the realignment parameters.
mvt_params.max_trans_x = mvt_params.voxel_size(1) * mvt_params.max_trans_vox_x; % from voxels to mm
mvt_params.max_trans_y = mvt_params.voxel_size(2) * mvt_params.max_trans_vox_y;
mvt_params.max_trans_z = mvt_params.voxel_size(3) * mvt_params.max_trans_vox_z;
mvt_params.after_mvt_lag = ceil(mvt_params.after_mvt_lag / (mvt_params.TR)); % from seconds to TRs, number of steady volumes to remove after a movement period

smooth_params.fwhm = smooth_params.fwhm .* mvt_params.voxel_size; % Specify the FWHM of the Gaussian smoothing kernel in mm. Three values should be entered, denoting the FWHM in the x, y and z directions

if ~isfield(paths,'smoothed_suffix')
    paths.smoothed = sprintf('%s/smoothed_%s',paths.analysis,sprintf('%g',round(smooth_params.fwhm))); % folder where the smoothed resliced motion corrected images will be
else
    paths.smoothed = sprintf('%s/smoothed_%s_%s',paths.analysis,sprintf('%g',round(smooth_params.fwhm)),paths.smoothed_suffix); % folder where the smoothed resliced motion corrected images will be
end


%% write log file parameters
if ~exist(paths.analysis,'dir');mkdir(paths.analysis);end % create folder if non-existant
fid = fopen(paths.log_file_params,'w');
fprintf(fid,'### Subject: %s\n',paths.subject);
fprintf(fid,'### Dataset path: %s\n',paths.dataset);
fprintf(fid,'### Realign name: %s\n',paths.realign_name);

fprintf(fid,'\n\n### Session(s):\n');
fprintf(fid,'%02.0f ',SR.session);

fprintf(fid,'\n### Run(s):\n');
for s = 1:length(SR)
    fprintf(fid,'%02.0f ',SR(s).runs);
    fprintf(fid,'\n');
end

fprintf(fid,'\n### Total number of runs: %i\n',n_total_runs);

fprintf(fid,'\n\n### Realign parameters:\n');
print_struct(realign_flags,fid)
fprintf(fid,'\n\n### Reslice parameters:\n');
print_struct(reslice_flags,fid)
fprintf(fid,'\n\n### Movement parameters:\n');
print_struct(mvt_params,fid)
fprintf(fid,'\n\n### Smoothing parameters:\n');
fprintf(fid,'fwhm in voxels:'); fprintf(fid,' %g',smooth_params.fwhm ./ mvt_params.voxel_size); fprintf(fid,'\n');
print_struct(smooth_params,fid)
fprintf(fid,'\n\n### GLM parameters:\n');
print_struct(GLM_params,fid)
fprintf(fid,'\n\n### Coregistration:\n');
print_struct(coreg_params,fid)
fprintf(fid,'\n\n### Contrasts:\n');
print_struct(contrasts,fid)
fprintf(fid,'\n\n\n### Scan infos of first scan:\n');
print_struct(scan_info(1,1),fid)

fclose(fid);







