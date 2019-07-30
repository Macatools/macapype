import nipype

import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe
import nipype.interfaces.ants as ants

import nipype.interfaces.fsl as fsl
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

import os

#from macapype.pipelines.preproc import create_average_align_pipe
#from macapype.pipelines.denoise import (
#    create_denoised_cropped_pipe, create_cropped_denoised_pipe)

from macapype.pipelines.correct_bias import create_debias_N4_pipe

from macapype.nodes.correct_bias import interative_N4_debias
from macapype.nodes.denoise import nonlocal_denoise

from macapype.pipelines.register import create_register_pipe


#from macapype.pipelines.extract_brain import create_brain_extraction_pipe
#from macapype.pipelines.segment import (create_brain_segment_pipe,
#    create_full_segment_pipe)

nmt_dir="/hpc/meca/users/loh.k/macaque_preprocessing/NMT_v1.2/"

nmt_file = os.path.join(nmt_dir,"NMT.nii.gz")
nmt_mask_file = os.path.join(nmt_dir, 'masks','anatomical_masks','NMT_brainmask.nii.gz')

from macapype.utils.misc import show_files

#data_path = "/home/INT/meunier.d/ownCloud/Documents/Hackaton/Data-Hackaton/Primavoice"
data_path = "/hpc/crise/cagna.b/Primavoice"

gm_prob_file = os.path.join(data_path, 'FSL','NMT_SS_pve_1.nii.gz')
wm_prob_file = os.path.join(data_path, 'FSL','NMT_SS_pve_2.nii.gz')
csf_prob_file = os.path.join(data_path, 'FSL','NMT_SS_pve_3.nii.gz')

main_path = os.path.join(os.path.split(__file__)[0],"../tests/")


subject_ids = ['Elouk']

def create_infosource():
    infosource = pe.Node(interface=niu.IdentityInterface(fields=['subject_id']),name="infosource")
    infosource.iterables = [('subject_id', subject_ids)]

    return infosource

def create_datasource():
   datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],outfields=['T1']),name = 'datasource')
   datasource.inputs.base_directory = data_path
   datasource.inputs.template = '%s/sub-%s_ses-01_%s.nii'
   datasource.inputs.template_args = dict(
       T1=[['subject_id','subject_id',"T1w"]],
       )
   datasource.inputs.sort_filelist = True

   return datasource

###############################################################################
def create_segment_pnh_onlyT1(name= "segment_pnh_subpipes"):

    # creating pipeline
    seg_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1']),
        name='inputnode')

    ############ preprocessing (avg and align)
    #debias_pipe = create_debias_N4_pipe()

    #seg_pipe.connect(inputnode,'T1',debias_pipe,'inputnode.cropped_T1')

    # N4 correction
    debias_N4 = pe.Node(ants.N4BiasFieldCorrection(),
                             name='debias_N4')

    seg_pipe.connect(inputnode,'T1',debias_N4,'input_image')


    ## N4 correction
    #iterative_debias_N4 = pe.Node(
        #niu.Function(
            #input_names=['input_image','stop_param'],
            #output_names=['debiased_image'],
            #function=interative_N4_debias),
        #name='iterative_debias_N4')

    #seg_pipe.connect(inputnode,'T1',iterative_debias_N4,'input_image')
    #iterative_debias_N4.inputs.stop_param = 0.01

    denoise_T1 = pe.Node(
        niu.Function(input_names=["img_file"],
                     output_names=["denoised_img_file"],
                     function=nonlocal_denoise),
        name = "denoise_T1")

    seg_pipe.connect(debias_N4, 'output_image', denoise_T1, 'img_file')

    #######  !!!! Attention , brain extraction should come in between !!!!!!!

    bet = pe.Node(fsl.BET(), name = 'bet')
    seg_pipe.connect(denoise_T1, 'denoised_img_file',
                                  bet, 'in_file')
    bet.inputs.frac = 0.7

    register_pipe = create_register_pipe(template_file = nmt_file,
                                         template_mask_file=nmt_mask_file,
                                         gm_prob_file=gm_prob_file,
                                         wm_prob_file=wm_prob_file,
                                         csf_prob_file=csf_prob_file, n_iter = 2)
    seg_pipe.connect(bet, 'out_file', register_pipe, "inputnode.anat_file_BET")
    seg_pipe.connect(denoise_T1, 'denoised_img_file', register_pipe, 'inputnode.anat_file')

    return seg_pipe


    return seg_pipe

###############################################################################

def create_main_workflow():

    #main_workflow = pe.Workflow(name= "test_pipeline_kepkee_by_david")
    main_workflow = pe.Workflow(name= "test_pipeline_with_bastien_and_kepkee")
    main_workflow.base_dir = main_path

    ## Infosource
    infosource = create_infosource()

    ## Data source
    datasource = create_datasource()

    ## connect
    main_workflow.connect(infosource, 'subject_id', datasource, 'subject_id')

    ############################################## Preprocessing ################################
    ##### segment_pnh

    print('segment_pnh')

    #segment_pnh = create_segment_pnh_subpipes()
    segment_pnh = create_segment_pnh_onlyT1()

    main_workflow.connect(datasource,'T1',segment_pnh,'inputnode.T1')

    return main_workflow


if __name__ =='__main__':

    ### main_workflow
    wf = create_main_workflow()
    wf.write_graph(graph2use = "colored")
    wf.config['execution'] = {'remove_unnecessary_outputs':'false'}

    wf.run()
    #wf.run(plugin='MultiProc', plugin_args={'n_procs' : 2})
