import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
import nipype.interfaces.ants as ants

from ..utils.misc import get_elem
from ..utils.utils_nodes import NodeParams, parse_key

from ..nodes.register import (interative_flirt, NMTSubjectAlign,
                              NMTSubjectAlign2, NwarpApplyPriors,
                              IterREGBET)


def create_iterative_register_pipe(
        template_file, template_brain_file, template_mask_file, gm_prob_file,
        wm_prob_file, csf_prob_file, n_iter, name="register_pipe"):
    """
    Registration of template (NMT or other) according to Regis:

    - The iterative FLIRT is between NMT_SS and subject's anat after a quick
    skull-stripping but the anat is more and more refined to corresponds to the
    brain

    - there is also a FNIRT done once, for comparison of the quality of the
    template on the subject's brain

    Not used anymore: corresponds to the IterREGBET provided by Regis in bash
    and wrapped node IterREGBET in nodes/register.py

    #TODO: test if gives the same results as IterREGBET
    """
    register_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['anat_file_BET', 'anat_file']),
        name='inputnode')

    # register node
    register = pe.Node(
        niu.Function(input_names=["anat_file", "anat_file_BET",
                                  "template_brain_file",
                                  "template_mask_file", 'n_iter'],
                     output_names=["anat_file_brain", "template_to_anat_file"],
                     function=interative_flirt),
        name="register")

    register.inputs.template_brain_file = template_brain_file
    register.inputs.template_mask_file = template_mask_file
    register.inputs.n_iter = n_iter

    register_pipe.connect(inputnode, 'anat_file', register, 'anat_file')
    register_pipe.connect(inputnode, 'anat_file_BET',
                          register, "anat_file_BET")

    # apply transfo over the 3 tissues:
    # gm
    register_gm = pe.Node(fsl.ApplyXFM(), name="register_gm")

    register_gm.inputs.in_file = gm_prob_file
    register_gm.inputs.apply_xfm = True
    register_gm.inputs.interp = "nearestneighbour"
    register_gm.inputs.output_type = "NIFTI"  # for SPM segment

    register_pipe.connect(register, 'anat_file_brain',
                          register_gm, 'reference')
    register_pipe.connect(register, 'template_to_anat_file',
                          register_gm, "in_matrix_file")

    # wm
    register_wm = pe.Node(fsl.ApplyXFM(), name="register_wm")

    register_wm.inputs.in_file = wm_prob_file
    register_wm.inputs.apply_xfm = True
    register_wm.inputs.interp = "nearestneighbour"
    register_wm.inputs.output_type = "NIFTI"  # for SPM segment

    register_pipe.connect(register, 'anat_file_brain',
                          register_wm, 'reference')
    register_pipe.connect(register, 'template_to_anat_file',
                          register_wm, "in_matrix_file")

    # csf
    register_csf = pe.Node(fsl.ApplyXFM(), name="register_csf")

    register_csf.inputs.in_file = csf_prob_file
    register_csf.inputs.apply_xfm = True
    register_csf.inputs.interp = "nearestneighbour"
    register_csf.inputs.output_type = "NIFTI"  # for SPM segment

    register_pipe.connect(register, 'anat_file_brain',
                          register_csf, 'reference')
    register_pipe.connect(register, 'template_to_anat_file',
                          register_csf, "in_matrix_file")

    def return_list(file1, file2, file3):
        return [file1, file2, file3]

    # merge 3 outputs to a list (...)
    merge_3_files = pe.Node(
        niu.Function(input_names=["file1", "file2", "file3"],
                     output_names=["list3files"],
                     function=return_list),
        name="merge_3_files")

    register_pipe.connect(register_gm, 'out_file', merge_3_files, "file1")
    register_pipe.connect(register_wm, 'out_file', merge_3_files, "file2")
    register_pipe.connect(register_csf, 'out_file', merge_3_files, "file3")

    # same with non linear
    # non linear register between anat and head
    # (FNIRT work directly on head?
    # I thought FLIRT was only skull-stripped brain, is it different? )

    nl_register = pe.Node(fsl.FNIRT(), name="nl_register")
    nl_register.inputs.in_file = template_file

    register_pipe.connect(inputnode, 'anat_file', nl_register, 'ref_file')
    register_pipe.connect(register, 'template_to_anat_file',
                          nl_register, 'affine_file')

    # apply non linear warp to NMT_SS
    nl_apply = pe.Node(fsl.ApplyWarp(), name="nl_apply")
    nl_apply.inputs.in_file = template_brain_file
    register_pipe.connect(inputnode, 'anat_file', nl_apply, 'ref_file')
    register_pipe.connect(nl_register, 'fieldcoeff_file',
                          nl_apply, 'field_file')  # iout from fnirt

    return register_pipe


def create_native_iter_reg_pipe(params_template, params={},
                                name="native_iter_reg_pipe"):
    """
    Description: Register template to anat with the IterREGBET and \
    apply the transfo to gm, wm and csf priors

    Processing steps:

    - IterREGBET (reg) compute transformation between T1 and template T1, \
    using skull-stripped versions of T1 and template as well
    - apply inv transfo (template -> native) using ApplyXFM \
    (register_csf_to_nat, register_gm_to_nat, register_wm_to_nat)

    Params:

        - reg (see :class:`IterREGBET <macapype.nodes.register.IterREGBET>`) \
    - also available as :ref:`indiv_params <indiv_params>`

    Inputs:

        inputnode:

            t1_debiased_file:
                debiased T1 file name

            t1_debiased_file:
                debiased skull stripped T1 file name


        arguments:

            params_template:
                dictionary of info about template

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "native_iter_reg_pipe")

    Outputs:

        register_csf_to_nat.out_file:
            csf template tissue in subject space

        register_gm_to_nat.out_file:
            grey matter template tissue in subject space

        register_wm_to_nat.out_file:
            white matter template tissue in subject space
    """

    native_iter_reg_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['t1_debiased_file',
                                      't1_debiased_brain_file',
                                      'indiv_params']),
        name='inputnode')

    # Iterative registration to the INIA19 template
    reg = NodeParams(IterREGBET(),
                     params=parse_key(params, "reg"),
                     name='reg')

    reg.inputs.refb_file = params_template["template_brain"]

    native_iter_reg_pipe.connect(inputnode, 't1_debiased_file',
                                 reg, 'inw_file')
    native_iter_reg_pipe.connect(inputnode, 't1_debiased_brain_file',
                                 reg, 'inb_file')

    native_iter_reg_pipe.connect(
        inputnode, ('indiv_params', parse_key, "reg"),
        reg, 'indiv_params')

    # apply inv_transfo over the 3 tissues:
    # gm
    register_gm_to_nat = pe.Node(fsl.ApplyXFM(), name="register_gm_to_nat")
    register_gm_to_nat.inputs.in_file = params_template["template_gm"]
    register_gm_to_nat.inputs.output_type = "NIFTI"  # for SPM segment

    native_iter_reg_pipe.connect(inputnode, 't1_debiased_file',
                                 register_gm_to_nat, 'reference')
    native_iter_reg_pipe.connect(reg, 'inv_transfo_file',
                                 register_gm_to_nat, "in_matrix_file")

    # wm
    register_wm_to_nat = pe.Node(fsl.ApplyXFM(), name="register_wm_to_nat")
    register_wm_to_nat.inputs.in_file = params_template["template_wm"]
    register_wm_to_nat.inputs.output_type = "NIFTI"  # for SPM segment

    native_iter_reg_pipe.connect(inputnode, 't1_debiased_file',
                                 register_wm_to_nat, 'reference')
    native_iter_reg_pipe.connect(reg, 'inv_transfo_file',
                                 register_wm_to_nat, "in_matrix_file")

    # csf
    register_csf_to_nat = pe.Node(fsl.ApplyXFM(), name="register_csf_to_nat")
    register_csf_to_nat.inputs.in_file = params_template["template_csf"]
    register_csf_to_nat.inputs.output_type = "NIFTI"  # for SPM segment

    native_iter_reg_pipe.connect(inputnode, 't1_debiased_file',
                                 register_csf_to_nat, 'reference')
    native_iter_reg_pipe.connect(reg, 'inv_transfo_file',
                                 register_csf_to_nat, "in_matrix_file")

    return native_iter_reg_pipe


###############################################################################
def create_register_NMT_pipe(params_template, params={},
                             name="register_NMT_pipe", NMT_version="v1.3"):
    """Description: Register template to anat with the script NMT_subject_align

    Processing steps:

    - Bias correction (norm_intensity)
    - Deoblique (Refit with deoblique option)
    - NMT_subject_align (see :class:`NMTSubjectAlign \
    <macapype.nodes.register.NMTSubjectAlign>` and :class:`NMTSubjectAlign2 \
    <macapype.nodes.register.NMTSubjectAlign2>` for explanations)
    - apply it to tissues list_priors (NwarpApplyPriors and Allineate)

    Params:
        - norm_intensity (see `N4BiasFieldCorrection <https://\
        nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.interfaces\
        .ants.segmentation.html#n4biasfieldcorrection>`_ for arguments)) - \
        also available as :ref:`indiv_params <indiv_params>`
        - NMT_version (default = 1.2; 1.3 is also accepted)

    Inputs:

        inputnode:

            T1:
                T1 file name

            indiv_params:
                dict with individuals parameters for some nodes

        arguments:

            params_template:
                dictionary of info about template

            params:
                dictionary of node sub-parameters (from a json file)

            name:
                pipeline name (default = "register_NMT_pipe")

            NMT_version:
                NMT version (default = 1.2); can be overwritten in params json

    Outputs:

        norm_intensity.output_image:
            filled mask after erode

        align_seg_csf.out_file:
            csf template tissue in subject space

        align_seg_gm.out_file:
            grey matter template tissue in subject space

        align_seg_wm.out_file:
            white matter template tissue in subject space
    """

    register_NMT_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['T1', 'indiv_params']),
        name='inputnode')

    # N4 intensity normalization over brain
    norm_intensity = NodeParams(ants.N4BiasFieldCorrection(),
                                params=parse_key(params, "norm_intensity"),
                                name='norm_intensity')

    register_NMT_pipe.connect(inputnode, 'T1',
                              norm_intensity, "input_image")

    register_NMT_pipe.connect(
        inputnode, ('indiv_params', parse_key, "norm_intensity"),
        norm_intensity, "indiv_params")

    deoblique = pe.Node(afni.Refit(deoblique=True), name="deoblique")
    register_NMT_pipe.connect(norm_intensity, 'output_image',
                              deoblique, "in_file")

    print("*** Found NMT_version {}".format(NMT_version))

    if NMT_version == "v1.2":
        # align subj to nmt
        NMT_subject_align = pe.Node(NMTSubjectAlign(),
                                    name='NMT_subject_align')
    elif NMT_version == "v1.3" or NMT_version == "v2.0":
        # align subj to nmt
        NMT_subject_align = pe.Node(NMTSubjectAlign2(),
                                    name='NMT_subject_align')
    else:
        print("NMT_version {} is not implemented".format(NMT_version))
        exit()

    NMT_subject_align.inputs.NMT_SS_file = params_template["template_brain"]

    register_NMT_pipe.connect(deoblique, 'out_file',
                              NMT_subject_align, "T1_file")

    if NMT_version.split(".")[0] == "v1":

        # align_masks
        # "overwrap" of NwarpApply, with specifying the outputs as wished
        list_priors = [params_template["template_head"],
                       params_template["template_csf"],
                       params_template["template_gm"],
                       params_template["template_wm"]]

    elif NMT_version.split(".")[0] == "v2":

        # align_masks
        # "overwrap" of NwarpApply, with specifying the outputs as wished
        list_priors = [params_template["template_head"],
                       params_template["template_seg"]]

    align_masks = pe.Node(NwarpApplyPriors(), name='align_masks2')
    align_masks.inputs.in_file = list_priors
    align_masks.inputs.out_file = list_priors
    align_masks.inputs.interp = "NN"
    align_masks.inputs.args = "-overwrite"

    register_NMT_pipe.connect(NMT_subject_align, 'aff_file',
                              align_masks, 'master')
    register_NMT_pipe.connect(NMT_subject_align, 'warpinv_file',
                              align_masks, "warp")

    # align_NMT
    align_NMT = pe.Node(
        afni.Allineate(), name="align_NMT", iterfield=['in_file'])
    align_NMT.inputs.final_interpolation = "nearestneighbour"
    align_NMT.inputs.overwrite = True
    align_NMT.inputs.outputtype = "NIFTI_GZ"

    register_NMT_pipe.connect(align_masks, ('out_file', get_elem, 0),
                              align_NMT, "in_file")  # -source
    register_NMT_pipe.connect(norm_intensity, 'output_image',
                              align_NMT, "reference")  # -base
    register_NMT_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                              align_NMT, "in_matrix")  # -1Dmatrix_apply

    if NMT_version.split(".")[0] == "v1":

        # seg_csf
        align_seg_csf = pe.Node(
            afni.Allineate(), name="align_seg_csf", iterfield=['in_file'])
        align_seg_csf.inputs.final_interpolation = "nearestneighbour"
        align_seg_csf.inputs.overwrite = True
        align_seg_csf.inputs.outputtype = "NIFTI_GZ"

        register_NMT_pipe.connect(align_masks, ('out_file', get_elem, 1),
                                  align_seg_csf, "in_file")  # -source
        register_NMT_pipe.connect(norm_intensity, 'output_image',
                                  align_seg_csf, "reference")  # -base
        register_NMT_pipe.connect(
            NMT_subject_align, 'inv_transfo_file', align_seg_csf,
            "in_matrix")  # -1Dmatrix_apply

        # seg_gm
        align_seg_gm = pe.Node(
            afni.Allineate(), name="align_seg_gm", iterfield=['in_file'])
        align_seg_gm.inputs.final_interpolation = "nearestneighbour"
        align_seg_gm.inputs.overwrite = True
        align_seg_gm.inputs.outputtype = "NIFTI_GZ"

        register_NMT_pipe.connect(align_masks, ('out_file', get_elem, 2),
                                  align_seg_gm, "in_file")  # -source
        register_NMT_pipe.connect(norm_intensity, 'output_image',
                                  align_seg_gm, "reference")  # -base
        register_NMT_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                                  align_seg_gm, "in_matrix")  # -1Dmatrix_apply

        # seg_wm
        align_seg_wm = pe.Node(afni.Allineate(), name="align_seg_wm",
                               iterfield=['in_file'])
        align_seg_wm.inputs.final_interpolation = "nearestneighbour"
        align_seg_wm.inputs.overwrite = True
        align_seg_wm.inputs.outputtype = "NIFTI_GZ"

        register_NMT_pipe.connect(align_masks, ('out_file', get_elem, 3),
                                  align_seg_wm, "in_file")  # -source
        register_NMT_pipe.connect(norm_intensity, 'output_image',
                                  align_seg_wm, "reference")  # -base
        register_NMT_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                                  align_seg_wm, "in_matrix")  # -1Dmatrix_apply

    elif NMT_version.split(".")[0] == "v2":

        # seg
        align_seg = pe.Node(
            afni.Allineate(), name="align_seg", iterfield=['in_file'])
        align_seg.inputs.final_interpolation = "nearestneighbour"
        align_seg.inputs.overwrite = True
        align_seg.inputs.outputtype = "NIFTI_GZ"

        register_NMT_pipe.connect(align_masks, ('out_file', get_elem, 1),
                                  align_seg, "in_file")  # -source
        register_NMT_pipe.connect(norm_intensity, 'output_image',
                                  align_seg, "reference")  # -base
        register_NMT_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                                  align_seg, "in_matrix")  # -1Dmatrix_apply

    return register_NMT_pipe
