
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from nipype.interfaces.ants.segmentation import DenoiseImage


def create_denoised_pipe(params={}, name="denoised_pipe"):
    """
    Description: Using Ants denoise on T1 and T2

    Inputs:

        inputnode:
            preproc_T1: preprocessed T1 file name

            preproc_T2: preprocessed T2 file name

        arguments:
            params: dictionary of node sub-parameters (from a json file)\
                (Unused so far, could be used to specify DenoiseImage
                parameters)

            name: pipeline name (default = "denoised_pipe")

    Outputs:

        denoise_T1.out_file:
            T1 after denoising

        denoise_T2.out_file
            T2 after denoising

    """

    # creating pipeline
    denoised_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['preproc_T1', 'preproc_T2']),
        name='inputnode')

    # denoise with Ants package
    denoise_T1 = pe.Node(interface=DenoiseImage(), name="denoise_T1")
    denoised_pipe.connect(inputnode, 'preproc_T1', denoise_T1, 'input_image')

    denoise_T2 = pe.Node(interface=DenoiseImage(), name="denoise_T2")
    denoised_pipe.connect(inputnode, 'preproc_T2', denoise_T2, 'input_image')

    return denoised_pipe
