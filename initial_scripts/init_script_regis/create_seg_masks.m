function create_seg_masks(T1_file,paths)
% Create brain masks from segmentation files
fprintf('Creating masks...')

%% fileparts T1
[pathstr,name,ext] = fileparts(T1_file);
if exist('paths','var')
    if ~isempty(paths)
        pathstr = paths.segmentation;
    end
end

%% Load segmentation prob maps
tissues = fieldnames(paths.anat_file_brain_segmentation.spm.tissues);
for i = 1:numel(tissues)
    P.(tissues{i}) = spm_vol(paths.anat_file_brain_segmentation.spm.tissues.(tissues{i}));
    Y.(tissues{i}) = spm_read_vols(P.(tissues{i}));
end

%% Create masks
prob = 0.05;
brain_mask = Y.grey > prob | Y.white > prob | Y.csf > prob; % Union of all tissues

%% Dilate & smooth mask
dilated_brain_mask = erode_or_dilate(brain_mask,'dilate',18);
smoothed_brain_mask = erode_or_dilate(dilated_brain_mask,'erode',18);

%% Fill holes
for i = 1:size(brain_mask,1)
    dilated_brain_mask(i,:,:) = imfill(dilated_brain_mask(i,:,:),'holes');
    smoothed_brain_mask(i,:,:) = imfill(smoothed_brain_mask(i,:,:),'holes');
end
for j = 1:size(brain_mask,2)
    dilated_brain_mask(:,j,:) = imfill(dilated_brain_mask(:,j,:),'holes');
    smoothed_brain_mask(:,j,:) = imfill(smoothed_brain_mask(:,j,:),'holes');
end
for k = 1:size(brain_mask,3)
    dilated_brain_mask(:,:,k) = imfill(dilated_brain_mask(:,:,k),'holes');
    smoothed_brain_mask(:,:,k) = imfill(smoothed_brain_mask(:,:,k),'holes');
end

%% Load T1 & extract brain using the newly created mask
PT1 = spm_vol(T1_file);
YT1 = spm_read_vols(PT1);
YT1(~smoothed_brain_mask) = 0;

%% Map of the 3 tissues
Yall = zeros(size(Y.grey,1),size(Y.grey,2),size(Y.grey,3),numel(tissues));
for i = 1:numel(tissues)
    Yall(:,:,:,i) = Y.(tissues{i});
end

Ymerged = zeros(size(Y.grey));
for i = 1:size(Y.grey,1)
    for j = 1:size(Y.grey,2)
        for k = 1:size(Y.grey,3)
            if sum(Yall(i,j,k,:))
                [maxtissue,itissue] = max(Yall(i,j,k,:));
                if maxtissue > prob
                    Ymerged(i,j,k) = itissue;
                end
            end
        end
    end
end

%% save files
P = PT1;

P.fname = fullfile(pathstr,[name '_brain' ext]);
spm_write_vol(P,YT1);

P.fname = fullfile(pathstr,[name '_brain_mask' ext]);
spm_write_vol(P,smoothed_brain_mask);

P.fname = fullfile(pathstr,[name '_brain_mask_dil' ext]);
spm_write_vol(P,dilated_brain_mask);

P.fname = fullfile(pathstr,[name '_brain_segmented_SPM' ext]);
spm_write_vol(P,Ymerged);

fprintf(' done.\n')





% for i = 1:size(Y,3)
%     imagesc(squeeze(Y(:,:,i)))
%     drawnow
% end
