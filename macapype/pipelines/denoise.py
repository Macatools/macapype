
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from nipype.interfaces.ants.segmentation import DenoiseImage


# Preprocessing: Avg multiples images, align T2 to T1,
# and crop/denoise in both order
def create_denoised_pipe(params = {}, name="denoised_pipe"):

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
