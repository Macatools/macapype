clearvars('-except','recipient','HN','run_index','max_rank','this_params_file'); % clear all but 'recipient' and 'HN' which are used in RunScript & 'run_index' used for jackknife procedure

%% PARAMETERS
% All the parameters of the analysis are set here
% This script has to be run before starting any analysis

%% Paths
paths.dataset = '/hpc/banco/Primavoice_Data_and_Analysis'; % Directory where the data are (general BIDS folder containing all subjects)
paths.subject = 'Apache'; % the subject you want to analyze (eg. if the folder containing the subject data is called 'sub-moumou', omit the prefix 'sub-' and leave only 'moumou')
paths.task = 'sparse'; % the task you want to analyze (eg. if the datafiles include 'task-sparse', omit the prefix 'task-' and leave only 'sparse')
paths.realign_name = 'allok'; % general name of the analysis (to differentiate analyses that have different parameters)
paths.results_name = '7PCs_12mvt_4_10'; % to distinguish different analyses done of the same realigned data
% paths.results_sub_folder = 'Jackruns16'; % Usefull when computing resulst for a limited number of runs (e.g. jackknife runs). Leave blank ('') or comment otherwise.

% Main anatomic file(s)
paths.main_anat_suffix = 'mp2rageT1w'; % Suffix of the main structural scan (last part of the anat scan filename)
paths.main_anat_session = 1; % Session at which the main structural scan was acquired.
% paths.T2_anat_suffix = 'T2w'; % Suffix of the T2 structural scan (comment line if no T2 available)

% Secondary (daily) anatomic file(s).
paths.daily_anat_suffix = 'T1w'; % Suffix of the daily structural scan (last part of the anat scan filename). Set to '' if unavailable

% Segmentation template (for non-human primates). Comment for humans.
paths.template_name = 'NMT'; % Template that will be used during the segmentation process. Available templates: 'inia19' & 'NMT' for macaques. 'BSI-NI' for marmosets.

% FSL & ANTS paths
paths.FSL_prefix = 'fsl5.0-'; % prefix to call FSL tools by the system (eg. on frioul, to call 'flirt' you have to type 'fsl5.0-flirt', so the prefix is 'fsl5.0-'). Leave '' if no prefix is needed
paths.ANTS_path = '/hpc/soft/ANTS/antsbin/bin'; % path to ANTS programs (mostly used for bias field correction / comment if ANTS is not available [no bias correction will be performed])

%% Session and runs
% sessions = 'all'; % either a vector or 'all' if you want to analyze all sessions
sessions = 2:13; % either a vector or 'all' if you want to analyze all sessions
% sessions = [3 4]; % either a vector or 'all' if you want to analyze all sessions

runs = 'all'; % either a vector (if you want the same run numbers in each session) or 'all' if you want to analyze every run of each session
% runs = 1:2; % either a vector (if you want the same run numbers in each session) or 'all' if you want to analyze every run of each session

% runs = 1:2;

% runs = [{1};...
%         {2:4}];

% to select particular runs in each session, do something like this (one cell per session, a vector in each cell):
% runs = [{1:4};...
%         {[1 3]};...
%         {2:6}];


%%% if sort_runs_by_steady_blocks has already been launched on all runs, you can use:
% filename = sprintf('%s/Run_selection.mat',sprintf('%s/analysis_%s',paths.dataset,paths.jobname));
% load(filename)
% sessions = selected_sessions;
% runs = selected_runs;

%%% if jackknife_results has already been launched on all runs, you can use:
% filename = fullfile(fullfile(paths.dataset,['analysis_sub-' paths.subject]),paths.realign_name,'Jackknife_Run_selection.mat');
% % filename = fullfile(fullfile(paths.dataset,['analysis_sub-' paths.subject]),paths.realign_name,'Jackknife_Run_selection_2_folds_group2.mat');
% load(filename)
% sessions = selected_sessions;
% runs = selected_runs;


% %% Downsampling
% aims_resample_fact = [2 1 2]; % resample factor, dimensions ordered for AimsResample
% spm_resample_fact = [2 2 1]; % resample factor, dimensions ordered for SPM
aims_resample_fact = [1 1 1]; % resample factor, dimensions ordered for AimsResample
spm_resample_fact = [1 1 1]; % resample factor, dimensions ordered for SPM
use_resampled_scans = 0; % boolean, use resampled scans or the original ones

%% Parameters that are specific to realign_runs_FSL
realign_FSL.mcflirt_cost = 'mutualinfo'; % cost function for motion correction (mutualinfo, woods, corratio, normcorr, normmi, leastsquares)
realign_FSL.mcflirt_dof = 6; % degrees of freedom for for motion correction: 6 for rigid body (appropriate in most cases), 7 to compensate for global scale changes, 12 for all degrees of freedom
realign_FSL.N4iterations = 6; % Number of N4 iterations performed before estimating the transform matrices between each run reference volume.
                              % This will run only if 'paths.ANTS_path' is set
                              % Set to '1' for humans
                              % For epi images that show a strong field inhomogeneity (as is the case with Leuven coils), 
                              % a high number should be chosen, '5' for instance.
realign_FSL.flirt_cost = 'normcorr'; % cost function for reference volumes registration (mutualinfo,corratio,normcorr,normmi,leastsq)
realign_FSL.flirt_dof = 6; % degrees of freedom for for reference volumes registration: 6 for rigid body (appropriate in most cases), 7 to compensate for global scale changes, 12 for all degrees of freedom

%% Parameters that are specific to realign_runs_SPM
realign_flags.quality = 0.9; % Quality versus speed trade-off.  Highest quality (1)
realign_flags.sep = 2; % in voxels, the default separation to sample the images.
realign_flags.fwhm = 2; % in voxels, The FWHM applied to the images before estimating the realignment parameters.
realign_flags.interp = 2; % B-spline degree used for interpolation
realign_flags.wrap = [0 0 0]; % wrap around x, y or z. [0 0 0] for no wrap

%% Parameters used either by SPM's applyVDM or realign & unwarp
reslice_flags.unwarp = 1; % If set to false, no unwarping or fieldmap correction will be done (realign & reslice will be done when using realign_runs_SPM). If set to true, fieldmap corrections will be done when fielmaps are available (realign & unwarp will be done when using realign_runs_SPM)
reslice_flags.register_fmap = 0; % register the fieldmaps to the reference volume of each epi run (true/false)

% SPM reslicing options (used by applyVSM in realign_runs_FSL, used by realign & unwarp or realign & reslice in realign_runs_SPM)
reslice_flags.mask = 1; % mask output images (true/false)
reslice_flags.mean = 0; % write mean image (true/false)
reslice_flags.interp = 4; % the B-spline interpolation method
reslice_flags.which = 2; % 2-reslice all the images
reslice_flags.prefix = 'resliced_'; % prefix for resliced images

%% Parameters of the algorithm that will classify each volume as steady or moving 
% Maximum translations allowed
mvt_params.max_trans_vox_x = 0.7; % in voxels, maximum translation allowed between 2 consecutive volumes (in real voxel size)
mvt_params.max_trans_vox_y = 0.7; % in voxels
mvt_params.max_trans_vox_z = 0.7; % in voxels
mvt_params.trans_fact = 2; % in numbers of max_trans_vox, maximum translation allowed between each volume and the mean of the steadiest period

% Maximum rotations allowed
mvt_params.max_rot_pitch = 0.3; % in degrees (0.3 seems ok), maximum rotation allowed between 2 consecutive volumes
mvt_params.max_rot_roll = 0.3; % in degrees
mvt_params.max_rot_yaw = 0.3; % in degrees
mvt_params.rot_fact = 2; % in numbers of max_rot, maximum rotation allowed between each volume and the mean of the steadiest period

% Steady period definition
mvt_params.min_dur_steady = 6; % in seconds, minimal duration of a steady period (shorter steady periods will be considered as movement)
mvt_params.min_dur_mvt = 1; % in seconds, minimal duration of a movement period (shorter movement periods will be considered as steady)
mvt_params.after_mvt_lag = 1; % in seconds, minimal duration to consider as a movement period after a detected movement (can be short for event-related protocol in which the stimulation is movement dependent. Should be around 10 sec for block designs)

% Reference volume selection & Verificaton scan
mvt_params.sel_from_fmap = 1; % Method to select the reference volume of each run:
                              % '1' will select the volume, from the steadiest period, that has the minimum normmi cost when compared with the magnitude map (if available)
                              % '0' will select the volume that is the closest to the average of the steadiest period during the run
mvt_params.n_vols_verif = 3; % number of volumes per run to include in the verification scan

%% Smoothing parameters
smooth_params.fwhm = [2 2 2]; % in real voxels, Specify the FWHM of the Gaussian smoothing kernel in voxels. Three values should be entered, denoting the FWHM in the x, y and z directions
smooth_params.prefix = 'smoothed_'; %Specify the string to be prepended to the filenames of the smoothed image file(s). Default prefix is 's'.

%% Coregistration method
coreg_params.method = 'flirt'; % Method used to coregister the average functional volume to the anatomic volume:
% - 'bbr' will use FSL's epi_reg. No user action needed. This is the method that will give the best results, but it will only
%	 work with BOLD functional volumes (will most likely not work with MION volumes for instance) that are already very close
%	 to the anat (as is the case for human data). Always try this method first and check the results. Try the next methods if it failed.
% - 'bbr_manual' is the same method as 'bbr', except that the average functional volume will first be bias field corrected and denoised,
%	 and the brain extraction is manual (brain extraction is automatic in the 'bbr' method).
% - 'flirt' will use flirt with a 'corratio' cost function, after the manual steps done on the average functional volume described above.

coreg_params.flirt_cost = 'mutualinfo'; % cost function if 'flirt' method is chosen above {mutualinfo,corratio,normmi}

coreg_params.use_daily_anat = 1; % If daily anatomic scans are available (low resolution anats that are already close to the funcs), 
								 % you can use them to coregister the average functional volume to the main anatomic volume by setting
								 % this parameter to 1. Use this option if the coregistration from func to the main anat failed or is unsatisfactory.

coreg_params.daily_anat_method = 'flirt'; % Method used to coregister the daily (low-res) anatomic volume to the main (high-res) anatomic volume:
% - 'flirt' will use flirt with a 'corratio' cost function, after the manual steps done on the daily anatomic volume described above.
% - 'fnirt' will add a non-linear registration on the entire head to the flirt steps
% - 'fnirt_brains' will add a non-linear registration on the brains to the flirt steps

coreg_params.daily_anat_flirt_cost = 'mutualinfo'; % cost function if 'flirt' method is chosen above {mutualinfo,corratio,normmi,normcorr,leastsq}

%% GLM parameters
GLM_params.mask_type = 'brain';  % Mask used when finding the t-threshold
							% '': no mask
							% 'brain': brain mask (created after brain segmentation)
							% 'grey': grey matter only (from the segmentation)
							% 'auditory': only the auditory cortices, defined depending on the species
							
GLM_params.hrf = [4 10 20 7 0.0001]; % The parameters of the hrf are specified by a row vector whose elements are:
									% 1. PEAK1: time to the peak of the first gamma density;
									% 2. FWHM1: approximate FWHM of the first gamma density;
									% 3. PEAK2: time to the peak of the second gamma density;
									% 4. FWHM2: approximate FWHM of the second gamma density;
									% 5. DIP: coefficient of the second gamma density.
									% The final hrf is: gamma1/max(gamma1)-DIP*gamma2/max(gamma2) scaled so that its total integral is 1.
									% If PEAK1=0 then there is no smoothing of that event type with the hrf.
									% If PEAK1>0 but FWHM1=0 then the design is lagged by PEAK1.
									% The default, chosen by Glover (1999) for an auditory stimulus, is: [5.4 5.2 10.8 7.35 0.35]
									% You can plot the HRF by running 'plot_hrf' after having ran this parameters file
									
GLM_params.motion_reg_type = 2; % 0 = no motion regressors (MRs) ; 1 = 6 MRs (trans + rot) ; 2 = 12 MRs (6 + squared) ; 3 = 24 MRs (12 + derviate)
GLM_params.nPCs = 7; % Number of PCs from the PCA on white matter + CSF that will be passed as regressors
GLM_params.GLMdenoise = 0; % use GLM_denoise to derive noise regressors instead of motion parameters
GLM_params.GLMdenoise_nPCA_PCs = 1; % number of PCs from the white_csf PCA to use as extraregressors in GLMdenoise
GLM_params.AR = 1; % the order of the autoregressive model. Order 1 seems to be adequate for 1.5T data, but higher order models may be needed for 3T data (will take much longer). 
GLM_params.n_temporal_trends = 3; % number of cubic spline temporal trends to be removed per 6 
								  %  minutes of scanner time (so it is backwards compatible). Temporal  
								  %  trends are modeled by cubic splines, so for a 6 minute run, N_TEMPORAL
								  %  <=3 will model a polynomial trend of degree N_TEMPORAL in frame times, 
								  %  and N_TEMPORAL>3 will add (N_TEMPORAL-3) equally spaced knots.
								  %  N_TEMPORAL=0 will model just the constant level and no temporal trends.
								  %  N_TEMPORAL=-1 will not remove anything, in which case the design matrix 
								  %  is completely determined by X_CACHE.X. 
                                  
p_val_peak = [0.05 0.01 0.001 0.0001 0.00001 1e-51 1e-81];

%% CONTRASTS
% The contrasts 'sound_vs_silence' as well as each condition vs silence are
% computed automatically
% Fill in the other contrasts that you wish to do here

contrasts.L = 1; % At which sound category level the analysis will be performed

% contrast names: better to name them cond1_vs_cond2 (no space allowed)
contrast_names = {'voice_vs_nonvoice';...
				  'macaque_vs_nonvoice';...
                  'macaque_vs_human';...
                  'macaque_vs_all';...
                  'human_vs_all';...
                  'marmoset_vs_all'};
% contrast weights (the conditions order are displayed for each category level when running this file)
contrast_weights = [ 1  1  1 -3  0;
					 0  1  0 -1  0;...
                    -1  1  0  0  0;...
                    -1  3 -1 -1  0;...
                     3 -1 -1 -1  0;...
                    -1 -1  3 -1  0];



% % contrast names: better to name them cond1_vs_cond2 (no space allowed)
% contrast_names = {'male_vs_female'};
% % contrast weights (the conditions order are displayed for each category level when running this file)
% contrast_weights = [ 0 -1  1  0];


% % contrast names: better to name them cond1_vs_cond2 (no space allowed)
% contrast_names = {'artificial_vs_natural'};
% % contrast weights (the conditions order are displayed for each category level when running this file)
% contrast_weights = [0 1 0 0 -1 0 0 0 0 0 0 0 0];




%%% Restrict analysis to certain conditions
% contrasts.restrict(1).L = 1; % Level at which you want the restriction
% contrasts.restrict(1).c = [1 0 0 0 0]; % vector of zeros & ones, ones being the conditions at which the analysis will be restricted
% 
% contrasts.restrict(2).L = 3; % Add a new restriction by adding a new element (increase the number in brackets)
% contrasts.restrict(2).c = [0 0 0 0 0 0 1 1];












%% SCRIPT (do not modify)
addpath(genpath(fileparts(which('RunScript.m'))))
Pstack = dbstack;
set_parameters

