function [out_file,denoised] = spm_sanlm(in_file)

fprintf('\nStarting denoising...\n\n')

[in_path,in_name,ext] = fileparts(in_file);

if strcmp(ext,'.gz')
	in_file = fullfile(in_path,in_name);
	if exist(in_file,'file') == 2; delete(in_file);end
	system(sprintf('gunzip %s',in_file));
end

spm('defaults', 'FMRI');
spm_jobman('initcfg'); % initialization
spm_get_defaults('cmdline',true)

spm_prefix = 'sanlm_';
tmp_file = fullfile(in_path,[in_name 'Dtmp' ext]);
out_file = fullfile(in_path,[in_name 'Denoised' ext]);

matlabbatch{1}.spm.tools.cat.tools.sanlm.prefix = spm_prefix;
matlabbatch{1}.spm.tools.cat.tools.sanlm.NCstr = Inf;
matlabbatch{1}.spm.tools.cat.tools.sanlm.rician = 0;


stop = 0;
i = 0;
denoised = 1;
while ~stop
	i = i + 1;
    fprintf('\nDenoising iteration %i...',i)
    
    [in_path,in_name,ext] = fileparts(in_file);
    spm_out_file = fullfile(in_path,[spm_prefix in_name ext]);
    
    copyfile(in_file,tmp_file);
    matlabbatch{1}.spm.tools.cat.tools.sanlm.data = {in_file};
    spm_jobman('run', matlabbatch);
	movefile(spm_out_file,out_file);
    
    if i == 1
		uiwait(warndlg('FSLView will open the original and the denoised volumes. Inspect the result of denoising by playing with the opacity.'))
	end
	
    fslview_command = 'fslview';
    [s,~] = system(sprintf('%s %s -l Greyscale %s -l Greyscale -t 1',fslview_command,in_file,out_file));
    if s == 127
        error('Could not find %s! \nChange the ''fslview_command'' variable (3 lines above this error), \nto match with the way fslview is called on your system.',fslview_command)
    end
    
    % Time for the user to choose
    answer = questdlg('What do you want to do?','Time to decide','New denoising pass','Stop here','Keep previous one','Stop here');
    
    if strcmp(answer,'New denoising pass')
        in_file = out_file;
    else
        stop = 1;
        if strcmp(answer,'Keep previous one')
        	if i == 1
        		delete(out_file)
        		out_file = in_file;
        		denoised = 0;
        	else
            	copyfile(tmp_file,out_file);
            end
        end
        delete(tmp_file)
    end
end







