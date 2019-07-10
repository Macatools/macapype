function [N4_out_file,N4ed,i] = ANTS_N4(N4_in_file,ANTS_path)

if ~exist('ANTS_path','var') || isempty(ANTS_path)
    ANTS_path = '/hpc/soft/ANTS/antsbin/bin';
end

ANTSbin = 'N4BiasFieldCorrection';
[N4_out_file_base,ext] = fileparts2(N4_in_file);
N4_tmp_file = sprintf('%sN4tmp%s',N4_out_file_base,ext);
N4_out_file = sprintf('%sN4%s',N4_out_file_base,ext);

stop = 0;
i = 0;
N4ed = 1;
while ~stop
    i = i + 1;
    fprintf('\nN4BiasFieldCorrection iteration %i...',i)
    copyfile(N4_in_file,N4_tmp_file);
    system(sprintf('%s -i %s -o %s',fullfile(ANTS_path,ANTSbin),N4_in_file,N4_out_file));
    fprintf(' done.\n')
    
    if i == 1
        uiwait(warndlg('FSLView will open the original and the bias corrected volumes. Inspect the result of N4 by playing with the opacity.'))
    end
    fslview_command = 'fslview';
    [s,~] = system(sprintf('%s %s -l Greyscale %s -l Greyscale -t 1',fslview_command,N4_tmp_file,N4_out_file));
    if s == 127
        error('Could not find %s! \nChange the ''fslview_command'' variable (3 lines above this error), \nto match with the way fslview is called on your system.',fslview_command)
    end
    % Time for the user to choose
    which_N4 = questdlg('What do you want to do?','Time to decide','New N4 pass','Stop here','Keep previous one','Stop here');
    
    if strcmp(which_N4,'New N4 pass')
        N4_in_file = N4_out_file;
    else
        stop = 1;
        if strcmp(which_N4,'Keep previous one')
            if i == 1
                delete(N4_out_file)
                N4_out_file = N4_in_file;
                N4ed = 0;
            else
                copyfile(N4_tmp_file,N4_out_file);
            end
        end
        delete(N4_tmp_file)
    end
end


