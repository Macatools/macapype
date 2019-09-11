function fsl_fast(T1_brain_file,paths)

fprintf('Performing FSL segmentation...')

%% fileparts T1
[pathstr,name,ext] = fileparts(T1_brain_file);
if strcmp(ext,'.gz')
   [~,name] = fileparts(name);
end
if exist('paths','var')
    if ~isempty(paths)
        pathstr = paths.segmentation;
    end
end

% path
pathstr = fullfile(pathstr,'FSL');
if ~exist(pathstr,'dir');mkdir(pathstr);end % create FSL segmentation folder if non-existant

%% Clear folder
delete(fullfile(pathstr,'*'))

%% Find fsl fast command
FSL_prefix = 'fsl5.0-';
if exist('paths','var')
    if isfield(paths,'FSL_prefix')
        FSL_prefix = paths.FSL_prefix;
    end
end
[s,~] = system([FSL_prefix 'fast']);
if s == 127
    [s,~] = system('fast');
    if s == 127
        error('Cannot find FSL fast command \nIf the command needs a prefix (eg. fsl6.0-bet), put this prefix in a ''paths.FSL_prefix'' variable%s','')
    else
        FSL_prefix = '';
    end
end

%% Execute FAST
out_base = fullfile(pathstr,name);
system(sprintf('%sfast -t 1 -o %s %s',FSL_prefix,out_base,T1_brain_file));

%% Apply the same tissue number as SPM
seg_file = fullfile(pathstr,[name '_pveseg.nii.gz']);
system(sprintf('gunzip %s',seg_file));
seg_file = fullfile(pathstr,[name '_pveseg.nii']);
P = spm_vol(seg_file);
Y = spm_read_vols(P);

Y(Y==1) = 4;
Y(Y==2) = 1;
Y(Y==3) = 2;
Y(Y==4) = 3;

spm_write_vol(P,Y);
system(sprintf('gzip %s',seg_file));

movefile(fullfile(pathstr,[name '_pve_0.nii.gz']),fullfile(pathstr,[name '_pve_3.nii.gz']));

fprintf(' Done.\n')
