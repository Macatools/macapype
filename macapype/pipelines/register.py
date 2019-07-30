
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.spm as spm
import nipype.interfaces.afni as afni

from ..nodes.register import interative_flirt



def create_register_pipe(template_file, template_mask_file, gm_prob_file,
                         wm_prob_file, csf_prob_file, n_iter,
                         name = "register_pipe"):

    register_pipe = pe.Workflow(name = name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['anat_file_BET','anat_file']),
        name='inputnode')

    # register node
    register = pe.Node(
        niu.Function(input_names=["anat_file","anat_file_BET","template_file",
                                  "template_mask_file",'n_iter'],
                     output_names=["realigned_file"],
                     function=interative_flirt),
        name = "register")

    register.inputs.template_file = template_file
    register.inputs.template_mask_file = template_mask_file
    register.inputs.n_iter = n_iter

    register_pipe.connect(inputnode, 'anat_file', register, 'anat_file')
    register_pipe.connect(inputnode, 'anat_file_BET', register, "anat_file_BET")

    # old segment

    #old_segment = pe.Node(spm.Segment())
    #old_segment.inputs.tissue_prob_maps = [gm_prob_file, wm_prob_file, csf_prob_file]

    #register_pipe.connect(register, 'realigned_file', old_segment, "data")


    return register_pipe

