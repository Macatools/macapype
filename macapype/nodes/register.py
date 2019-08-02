import os

def interative_flirt(anat_file, anat_file_BET, template_brain_file,
                     template_mask_file, n_iter):
    """
    This funcion, from Regis script, aims at interatively building a better
    skull stripped version of the subject's. There is a need for an already
    computed skullstripped version to initiallized the procedure (anat_file_BET)

    The algo works this way:
    1) flirt skullstripped template to skullstripped subject's brain
    2) apply transfo on template's mask to have the mask in subject's space
    3) mask orig anat with compute mask to obtained a new skullstripped
    subject's brain. Use this new skullstripped subject's for the next
    iteration.
    """

    import os
    import nipype.interfaces.fsl as fsl

    from nipype.utils.filemanip import split_filename as split_f

    path_t, fname_t, ext_t = split_f(template_brain_file)
    out_file = os.path.abspath(fname_t + "_brain_flirt.nii")
    template_to_anat_file = os.path.abspath(fname_t + "_to_anat.xfm")

    path_a, fname_a, ext_a = split_f(anat_file)

    anat_file_brain_mask = os.path.abspath(fname_a + "_brain_mask.nii.gz")
    anat_file_brain = os.path.abspath(fname_a + "_brain.nii")

    flirt_ref_file = anat_file_BET

    for i in range(n_iter):

        print('Iter flirt {}'.format(i))

        # first step = FLIRT: template brain to anat bet
        # -> transfo matrix (linear) between the two
        flirt = fsl.FLIRT()
        flirt.inputs.in_file = template_brain_file
        flirt.inputs.reference = flirt_ref_file

        flirt.inputs.out_matrix_file = template_to_anat_file
        #flirt.inputs.out_file = out_file
        flirt.inputs.cost = "normcorr"

        flirt.run()

        # second step = apply transfo to template's mask
        # -> brain_mask in subject's space
        print('Iter apply_flirt {}'.format(i))
        apply_flirt = fsl.ApplyXFM()
        apply_flirt.inputs.in_file = template_mask_file
        apply_flirt.inputs.reference = anat_file_BET
        apply_flirt.inputs.in_matrix_file = template_to_anat_file
        apply_flirt.inputs.apply_xfm = True
        apply_flirt.inputs.interp = "nearestneighbour"
        apply_flirt.inputs.out_file = anat_file_brain_mask
        apply_flirt.run()


        # third step = use the mask in subject's space to mask the build
        # a skull-stripped version of the subject's brain
        # -> better skullstripped version
        print('Iter apply_mask {}'.format(i))
        #apply_mask = fsl.ApplyMask() ### a voir si plus pertinent...
        apply_mask = fsl.BinaryMaths()
        apply_mask.inputs.in_file = anat_file
        apply_mask.inputs.operation = 'mul'
        apply_mask.inputs.operand_file = anat_file_brain_mask
        apply_mask.inputs.out_file = anat_file_brain
        apply_mask.inputs.output_type = "NIFTI"
        apply_mask.run()

        flirt_ref_file = anat_file_brain

    return anat_file_brain, template_to_anat_file


########### NMT_subject_align



from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    TraitedSpec)
from nipype.interfaces.base import traits, File

# NMTSubjectAlign

class NMTSubjectAlignInputSpec(CommandLineInputSpec):

    script_file = File(
        exists=True,
        desc='NMT_subject_align script',
        mandatory=True, position=0, argstr="%s")

    T1_file = File(
        exists=True,
        desc='Target file',
        mandatory=True, position=1, argstr="%s")

    NMT_SS_file = File(
        exists=True,
        desc='Align to T1',
        mandatory=True, position=2, argstr="%s")


class NMTSubjectAlignOutputSpec(TraitedSpec):

    shft_aff_file = File(
        exists=True,
        desc="shft_aff")

    warpinv_file = File(
        exists=True,
        desc="shft_WARPINV")

    transfo_file = File(
        exists=True,
        desc="composite_linear_to_NMT")

    inv_transfo_file = File(
        exists=True,
        desc="_composite_linear_to_NMT_inv")



class NMTSubjectAlign(CommandLine):
    """
    Description:
        Align NMT subject to template


    Inputs:


        script_file = File(
            exists=True,
            desc='NMT_subject_align script',
            mandatory=True, position=0, argstr="%s")

        T1_file = File(
            exists=True,
            desc='Target file',
            mandatory=True, position=1, argstr="%s")

        NMT_SS_file = File(
            exists=True,
            desc='Align to T1',
            mandatory=True, position=2, argstr="%s")


    Outputs:

        shft_aff_file = File(
            exists=True,
            desc="shft_aff")

        warpinv_file = File(
            exists=True,
            desc="shft_WARPINV")

        transfo_file = File(
            exists=True,
            desc="composite_linear_to_NMT")

        inv_transfo_file = File(
            exists=True,
            desc="_composite_linear_to_NMT_inv")


    """
    input_spec = NMTSubjectAlignInputSpec
    output_spec = NMTSubjectAlignOutputSpec

    _cmd = 'tcsh -x'

    def _list_outputs(self):

        outputs = self._outputs().get()

        fname, ext = os.path.split(self.inputs.T1_file,".")

        outputs["shft_aff_file"] = os.path.abspath(fname + "_shft_aff" + ext )
        outputs["warpinv_file"] = os.path.abspath(fname + "_shft_WARPINV" + ext )

        outputs["transfo_file"] = os.path.abspath(fname + "_composite_linear_to_NMT.1D")
        outputs["inv_transfo_file"] = os.path.abspath(fname + "_composite_linear_to_NMT_inv.1D")

        return outputs


# newer, less dirty version
def wrap_NMT_subject_align(script_file, T1_file, NMT_SS_file):

    import os
    import shutil

    from nipype.utils.filemanip import split_filename as split_f
    #shutil.copy(T1_file,cur_dir)

    ## just to be sure...
    #os.chdir(nmt_dir)

    os.system("tcsh -x {} {} {}".format(script_file, T1_file, NMT_SS_file))

    shft_aff_file = os.path.abspath(fname + "_shft_aff" + ext )
    warpinv_file = os.path.abspath(fname + "_shft_WARPINV" + ext )

    transfo_file = os.path.abspath(fname + "_composite_linear_to_NMT.1D")
    inv_transfo_file = os.path.abspath(fname + "_composite_linear_to_NMT_inv.1D")

    return shft_aff_file, warpinv_file, transfo_file, inv_transfo_file

# previous dirty version
#def wrap_NMT_subject_align(T1_file):

    #import os
    #import shutil

    #from nipype.utils.filemanip import split_filename as split_f

    #nmt_dir="/hpc/meca/users/loh.k/macaque_preprocessing/NMT_v1.2/"
    #NMT_SS_file = os.path.join(nmt_dir,"NMT_SS.nii.gz")
    ##shutil.copy(NMT_SS_file,cur_dir)

    #script_file = os.path.join(nmt_dir,"NMT_subject_align.csh")

    #path, fname, ext = split_f(T1_file)
    ##shutil.copy(T1_file,cur_dir)

    ### just to be sure...
    ##os.chdir(nmt_dir)

    #os.system("tcsh -x {} {} {}".format(script_file, T1_file, nmt_ss_file))

    #shft_aff_file = os.path.abspath(fname + "_shft_aff" + ext )
    #warpinv_file = os.path.abspath(fname + "_shft_WARPINV" + ext )

    #transfo_file = os.path.abspath(fname + "_composite_linear_to_NMT.1D")
    #inv_transfo_file = os.path.abspath(fname + "_composite_linear_to_NMT_inv.1D")


    #return shft_aff_file, warpinv_file, transfo_file, inv_transfo_file

########### add Nwarp
def add_Nwarp(list_prior_files):

    import os
    from nipype.utils.filemanip import split_filename as split_f

    out_files = []
    for prior_file in list_prior_files[:3]:

        path, fname, ext = split_f(prior_file)
        #out_files.append(os.path.join(path,fname + "_Nwarp" + ext))
        out_files.append(os.path.abspath(fname + "_Nwarp" + ext))

    for i in range(1,4):
        out_files.append(os.path.abspath("tmp_%02d.nii.gz"%i))

    return out_files

# NwarpApplyPriors

from nipype.interfaces.afni import NwarpApply

from nipype.utils.filemanip import split_filename as split_f

class NwarpApplyPriors(NwarpApply):
    """
    Over Wrap of NwarpApply (afni node) in order to generate files in the right
    node directory (instead of in the original data directory, or the script directory
    as is now)

    Modifications are made over inputs and outputs
    """

    def _format_arg(self, name, spec, value):

        import os
        import shutil

        cur_dir = os.getcwd()

        new_value = []
        if name == 'in_file':
            for in_file in value:
                print(in_file)

                ### copy en local
                shutil.copy(in_file,cur_dir)

                new_value.append(os.path.join(cur_dir, in_file))

            value = new_value

        if name == 'out_file':
            for out_file in value[:3]:
                print(out_file)

                path, fname, ext = split_f(out_file)
                #out_files.append(os.path.join(path,fname + "_Nwarp" + ext))
                new_value.append(os.path.join(cur_dir, fname + "_Nwarp" + ext))

            for i in range(1,4):
                new_value.append(os.path.join(cur_dir, "tmp_%02d.nii.gz"%i))
            value = new_value

        return super(NwarpApplyPriors, self)._format_arg(name, spec, value)




# Testing: at one point, should be turned into unittest
if __name__ =='__main__':

    # test of wrap_NMT_subject_align/NMTSubjectAlign
    #T1_file = "/hpc/crise/meunier.d/Packages/pipeline-anat-macaque/tests/test_pipeline_kepkee/segment_pnh_subpipes/full_segment_pipe/register_NMT_pipe/_subject_id_032311/norm_intensity/avg_sub-032311_ses-001_run-1_T1w_roi_aonlm_denoised_maths_masked_corrected.nii.gz"

    #nmt_dir = "/hpc/meca/users/loh.k/macaque_preprocessing/NMT_v1.2/"
    #NMT_SS_file = os.path.join(nmt_dir,"NMT_SS.nii.gz")
    #script_file = os.path.join(nmt_dir,"NMT_subject_align.csh")

    ### function
    ##wrap_NMT_subject_align(script_file, T1_file, NMT_SS_file)

    #### node version
    #NMT_subject_align = NMTSubjectAlign()
    #NMT_subject_align.inputs.script_file = script_file
    #NMT_subject_align.inputs.NMT_SS_file = NMT_SS_file

    #NMT_subject_align.inputs.T1_file = T1_file
    #NMT_subject_align.run()

    ## test of NwarpApplyPriors

    import nipype.pipeline.engine as pe

    ref_dir = "/hpc/meca/users/loh.k/macaque_preprocessing/"
    nmt_dir = os.path.join(ref_dir,"NMT_v1.2/")
    p_dir = os.path.join(nmt_dir, "masks", "probabilisitic_segmentation_masks")


    NMT_file = os.path.join(nmt_dir, "NMT.nii.gz")
    NMT_SS_file = os.path.join(nmt_dir, "NMT_SS.nii.gz")
    NMT_brainmask = os.path.join(nmt_dir, "masks", "anatomical_masks",
                                    "NMT_brainmask.nii.gz")

    NMT_brainmask_prob = os.path.join(p_dir, "NMT_brainmask_prob.nii.gz")
    NMT_brainmask_CSF = os.path.join(p_dir, "NMT_segmentation_CSF.nii.gz")
    NMT_brainmask_GM = os.path.join(p_dir, "NMT_segmentation_GM.nii.gz")
    NMT_brainmask_WM = os.path.join(p_dir, "NMT_segmentation_WM.nii.gz")
    list_priors = [NMT_file, NMT_brainmask_prob, NMT_brainmask,
                   NMT_brainmask_CSF, NMT_brainmask_GM, NMT_brainmask_WM]

    cur_dir = "/hpc/crise/meunier.d/Packages/pipeline-anat-macaque/tests/test_pipeline_kepkee/segment_pnh_subpipes/full_segment_pipe/register_NMT_pipe/_subject_id_032311/NMT_subject_align"

    shft_aff_file = os.path.join(cur_dir, "avg_sub-032311_ses-001_run-1_T1w_roi_aonlm_denoised_maths_masked_corrected_shft_aff.nii.gz")
    warp_file = os.path.join(cur_dir, "avg_sub-032311_ses-001_run-1_T1w_roi_aonlm_denoised_maths_masked_corrected_shft_WARPINV.nii.gz")

    align_masks = pe.Node(NwarpApplyPriors(), name='align_masks')
    align_masks.inputs.in_file = list_priors
    align_masks.inputs.out_file = list_priors

    align_masks.inputs.warp = warp_file
    align_masks.inputs.master = shft_aff_file
    align_masks.run()

