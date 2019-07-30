function spm_old_segment(T1_file,grey,white,csf,paths)
% script to use with macaque subjects
% Note that multi-spectral (when there are two or more
% registered images of different contrasts) processing is
% not yet implemented for this method. (SPM manual)

fprintf('Starting SPM segmentation...\n')

T1 = cellstr([T1_file ',1']);
TPM = {grey;white;csf};

%% matlabbatch
matlabbatch{1}.spm.tools.oldseg.data = T1;
matlabbatch{1}.spm.tools.oldseg.output.GM = [0 0 1];
matlabbatch{1}.spm.tools.oldseg.output.WM = [0 0 1];
matlabbatch{1}.spm.tools.oldseg.output.CSF = [0 0 1];
matlabbatch{1}.spm.tools.oldseg.output.biascor = 0;
matlabbatch{1}.spm.tools.oldseg.output.cleanup = 0;
matlabbatch{1}.spm.tools.oldseg.opts.tpm = TPM;
matlabbatch{1}.spm.tools.oldseg.opts.ngaus = [2
                                              2
                                              2
                                              4];
matlabbatch{1}.spm.tools.oldseg.opts.regtype = ''; % 'subj'
matlabbatch{1}.spm.tools.oldseg.opts.warpreg = 1;
matlabbatch{1}.spm.tools.oldseg.opts.warpco = 25;
matlabbatch{1}.spm.tools.oldseg.opts.biasreg = 0.0001;
matlabbatch{1}.spm.tools.oldseg.opts.biasfwhm = 60;
matlabbatch{1}.spm.tools.oldseg.opts.samp = 3;
matlabbatch{1}.spm.tools.oldseg.opts.msk = {''};

%% Initialization
spm('defaults', 'FMRI');
spm_jobman('initcfg'); % initialization
spm_get_defaults('cmdline',true)

%% Run jobs
spm_jobman('run', matlabbatch)

%% fileparts T1
[pathstr,name,ext] = fileparts(T1_file);

%% Move files if needed
if exist('paths','var')
    if ~isempty(paths)
        if ~exist(paths.segmentation,'dir');mkdir(paths.segmentation);end % create segmentation folder if non-existant
        movefile(fullfile(pathstr,['c*' name ext]),paths.segmentation);
        movefile(fullfile(pathstr,[name '_seg_*.mat']),paths.segmentation);
    end
end

%% Create brain masks from segmentation
create_seg_masks(T1_file,paths)



