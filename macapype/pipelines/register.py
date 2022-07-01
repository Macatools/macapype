import shutil

import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
import nipype.interfaces.ants as ants

from ..utils.misc import get_elem
from ..utils.utils_nodes import NodeParams, parse_key

from ..nodes.register import (interative_flirt, NMTSubjectAlign,
                              NMTSubjectAlign2, NwarpApplyPriors,
                              animal_warper)


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


###############################################################################
def create_register_NMT_pipe(params_template, params={},
                             name="register_NMT_pipe"):
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

    if "norm_intensity" in params.keys():

        # N4 intensity normalization over brain
        norm_intensity = NodeParams(ants.N4BiasFieldCorrection(),
                                    params=parse_key(params, "norm_intensity"),
                                    name='norm_intensity')

        register_NMT_pipe.connect(inputnode, 'T1',
                                  norm_intensity, "input_image")

        register_NMT_pipe.connect(
            inputnode, ('indiv_params', parse_key, "norm_intensity"),
            norm_intensity, "indiv_params")

    # deoblique (seems mandatory from NMTSubjectAlign)
    deoblique = pe.Node(afni.Refit(deoblique=True), name="deoblique")

    if "norm_intensity" in params.keys():

        register_NMT_pipe.connect(norm_intensity, 'output_image',
                                  deoblique, "in_file")

    else:

        register_NMT_pipe.connect(inputnode, 'T1',
                                  deoblique, "in_file")

    print("which @animal_warper: ", shutil.which("@animal_warper"))

    if "NMT_subject_align" in params.keys():

        if "NMT_version" in params["NMT_subject_align"].keys():
            NMT_version = params["NMT_subject_align"]['NMT_version']
        else:
            print("Warning, for NMT_subject_align, NMT_version is required")
            NMT_version = "v1.3"

        print("*** NMT_version: {}".format(NMT_version))

        print("running NMT_subject_align with version {}".format(NMT_version))

        if NMT_version == "v1.2":
            # align subj to nmt
            NMT_subject_align = NodeParams(
                NMTSubjectAlign(),
                params=parse_key(params, "NMT_subject_align"),
                name='NMT_subject_align')

        elif NMT_version == "v1.3" or NMT_version == "v2.0":
            # align subj to nmt
            NMT_subject_align = NodeParams(
                NMTSubjectAlign2(),
                params=parse_key(params, "NMT_subject_align"),
                name='NMT_subject_align')

        else:
            print("NMT_version {} is not implemented, breaking".format(
                NMT_version))

            exit()

    elif shutil.which("@animal_warper") is not None:
        # TODO AnimalWarper()

        print("running @animal_warper with version {}".format(
            shutil.which("@animal_warper")))

        NMT_subject_align = pe.Node(
            niu.Function(input_names=["T1_file", "NMT_SS_file"],
                         output_names=["aff_file", "warp_file",
                                       "warpinv_file", "transfo_file",
                                       "inv_transfo_file"],
                         function=animal_warper),
            name='NMT_subject_align')
    else:
        print("running default NMT_subject_align version (NMTSubjectAlign2)")

        NMT_subject_align = NodeParams(
            NMTSubjectAlign2(),
            params=parse_key(params, "NMT_subject_align"),
            name='NMT_subject_align')

    NMT_subject_align.inputs.NMT_SS_file = params_template["template_brain"]

    register_NMT_pipe.connect(deoblique, 'out_file',
                              NMT_subject_align, "T1_file")

    # defining list priors
    list_priors = [params_template["template_head"]]

    if "template_seg" in params_template.keys():
        # align_masks
        list_priors.append(params_template["template_seg"])

    else:
        if "template_csf" in params_template.keys():
            list_priors.append(params_template["template_csf"])

        if "template_gm" in params_template.keys():
            list_priors.append(params_template["template_gm"])

        if "template_wm" in params_template.keys():
            list_priors.append(params_template["template_wm"])

    # align_masks
    # "overwrap" of NwarpApply, with specifying the outputs as wished
    align_masks = pe.Node(NwarpApplyPriors(), name='align_masks')
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

    register_NMT_pipe.connect(deoblique, 'out_file',
                              align_NMT, "reference")  # -base

    register_NMT_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                              align_NMT, "in_matrix")  # -1Dmatrix_apply

    if "template_seg" in params_template.keys():

        # seg
        align_seg = pe.Node(
            afni.Allineate(), name="align_seg", iterfield=['in_file'])
        align_seg.inputs.final_interpolation = "nearestneighbour"
        align_seg.inputs.overwrite = True
        align_seg.inputs.outputtype = "NIFTI_GZ"

        register_NMT_pipe.connect(align_masks, ('out_file', get_elem, 1),
                                  align_seg, "in_file")  # -source
        register_NMT_pipe.connect(deoblique, 'out_file',
                                  align_seg, "reference")  # -base
        register_NMT_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                                  align_seg, "in_matrix")  # -1Dmatrix_apply

    else:
        if "template_csf" in params_template.keys():
            # seg_csf
            align_seg_csf = pe.Node(
                afni.Allineate(), name="align_seg_csf", iterfield=['in_file'])
            align_seg_csf.inputs.final_interpolation = "nearestneighbour"
            align_seg_csf.inputs.overwrite = True
            align_seg_csf.inputs.outputtype = "NIFTI_GZ"

            register_NMT_pipe.connect(align_masks, ('out_file', get_elem, 1),
                                      align_seg_csf, "in_file")  # -source

            register_NMT_pipe.connect(deoblique, 'out_file',
                                      align_seg_csf, "reference")  # -base

            register_NMT_pipe.connect(
                NMT_subject_align, 'inv_transfo_file', align_seg_csf,
                "in_matrix")  # -1Dmatrix_apply

        if "template_gm" in params_template.keys():
            # seg_gm
            align_seg_gm = pe.Node(
                afni.Allineate(), name="align_seg_gm", iterfield=['in_file'])
            align_seg_gm.inputs.final_interpolation = "nearestneighbour"
            align_seg_gm.inputs.overwrite = True
            align_seg_gm.inputs.outputtype = "NIFTI_GZ"

            register_NMT_pipe.connect(align_masks, ('out_file', get_elem, 2),
                                      align_seg_gm, "in_file")  # -source
            register_NMT_pipe.connect(deoblique, 'out_file',
                                      align_seg_gm, "reference")  # -base
            register_NMT_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                                      align_seg_gm, "in_matrix")
        if "template_wm" in params_template.keys():

            # seg_wm
            align_seg_wm = pe.Node(afni.Allineate(), name="align_seg_wm",
                                   iterfield=['in_file'])
            align_seg_wm.inputs.final_interpolation = "nearestneighbour"
            align_seg_wm.inputs.overwrite = True
            align_seg_wm.inputs.outputtype = "NIFTI_GZ"

            register_NMT_pipe.connect(align_masks, ('out_file', get_elem, 3),
                                      align_seg_wm, "in_file")  # -source
            register_NMT_pipe.connect(deoblique, 'out_file',
                                      align_seg_wm, "reference")  # -base
            register_NMT_pipe.connect(NMT_subject_align, 'inv_transfo_file',
                                      align_seg_wm, "in_matrix")

    return register_NMT_pipe


def create_reg_seg_pipe(name="reg_seg_pipe"):

    reg_pipe = pe.Workflow(name=name)

    # creating inputnode
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['native_seg',
                                      'native_threshold_gm',
                                      'native_threshold_wm',
                                      'native_threshold_csf',
                                      'native_prob_gm',
                                      'native_prob_wm',
                                      'native_prob_csf',
                                      'transfo_file',
                                      'ref_image']),
        name='inputnode')

    # align_seg
    align_seg = pe.Node(
        afni.Allineate(), name="align_seg", iterfield=['in_file'])
    align_seg.inputs.final_interpolation = "nearestneighbour"
    align_seg.inputs.overwrite = True
    align_seg.inputs.outputtype = "NIFTI_GZ"

    reg_pipe.connect(inputnode, 'native_seg',
                     align_seg, "in_file")
    reg_pipe.connect(inputnode, 'ref_image', align_seg, "reference")
    reg_pipe.connect(inputnode, 'transfo_file', align_seg, "in_matrix")

    # align_threshold_gm
    align_threshold_gm = pe.Node(
        afni.Allineate(), name="align_threshold_gm", iterfield=['in_file'])
    align_threshold_gm.inputs.final_interpolation = "nearestneighbour"
    align_threshold_gm.inputs.overwrite = True
    align_threshold_gm.inputs.outputtype = "NIFTI_GZ"

    reg_pipe.connect(inputnode, 'native_threshold_gm',
                     align_threshold_gm, "in_file")
    reg_pipe.connect(inputnode, 'ref_image', align_threshold_gm, "reference")
    reg_pipe.connect(inputnode, 'transfo_file',
                     align_threshold_gm, "in_matrix")

    # align_threshold_wm
    align_threshold_wm = pe.Node(
        afni.Allineate(), name="align_threshold_wm", iterfield=['in_file'])
    align_threshold_wm.inputs.final_interpolation = "nearestneighbour"
    align_threshold_wm.inputs.overwrite = True
    align_threshold_wm.inputs.outputtype = "NIFTI_GZ"

    reg_pipe.connect(inputnode, 'native_threshold_wm',
                     align_threshold_wm, "in_file")
    reg_pipe.connect(inputnode, 'ref_image', align_threshold_wm, "reference")
    reg_pipe.connect(inputnode, 'transfo_file',
                     align_threshold_wm, "in_matrix")

    # align_threshold_csf
    align_threshold_csf = pe.Node(
        afni.Allineate(), name="align_threshold_csf", iterfield=['in_file'])
    align_threshold_csf.inputs.final_interpolation = "nearestneighbour"
    align_threshold_csf.inputs.overwrite = True
    align_threshold_csf.inputs.outputtype = "NIFTI_GZ"

    reg_pipe.connect(inputnode, 'native_threshold_csf',
                     align_threshold_csf, "in_file")
    reg_pipe.connect(inputnode, 'ref_image', align_threshold_csf, "reference")
    reg_pipe.connect(inputnode, 'transfo_file',
                     align_threshold_csf, "in_matrix")

    # align_prob_gm
    align_prob_gm = pe.Node(
        afni.Allineate(), name="align_prob_gm", iterfield=['in_file'])
    align_prob_gm.inputs.final_interpolation = "nearestneighbour"
    align_prob_gm.inputs.overwrite = True
    align_prob_gm.inputs.outputtype = "NIFTI_GZ"

    reg_pipe.connect(inputnode, 'native_prob_gm',
                     align_prob_gm, "in_file")
    reg_pipe.connect(inputnode, 'ref_image', align_prob_gm, "reference")
    reg_pipe.connect(inputnode, 'transfo_file', align_prob_gm, "in_matrix")

    # align_prob_wm
    align_prob_wm = pe.Node(
        afni.Allineate(), name="align_prob_wm", iterfield=['in_file'])
    align_prob_wm.inputs.final_interpolation = "nearestneighbour"
    align_prob_wm.inputs.overwrite = True
    align_prob_wm.inputs.outputtype = "NIFTI_GZ"

    reg_pipe.connect(inputnode, 'native_prob_wm',
                     align_prob_wm, "in_file")
    reg_pipe.connect(inputnode, 'ref_image', align_prob_wm, "reference")
    reg_pipe.connect(inputnode, 'transfo_file', align_prob_wm, "in_matrix")

    # align_prob_csf
    align_prob_csf = pe.Node(
        afni.Allineate(), name="align_prob_csf", iterfield=['in_file'])
    align_prob_csf.inputs.final_interpolation = "nearestneighbour"
    align_prob_csf.inputs.overwrite = True
    align_prob_csf.inputs.outputtype = "NIFTI_GZ"

    reg_pipe.connect(inputnode, 'native_prob_csf',
                     align_prob_csf, "in_file")
    reg_pipe.connect(inputnode, 'ref_image', align_prob_csf, "reference")
    reg_pipe.connect(inputnode, 'transfo_file', align_prob_csf, "in_matrix")

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['norm_seg', 'norm_threshold_gm',
                                      'norm_threshold_wm',
                                      'norm_threshold_csf',
                                      'norm_prob_gm', 'norm_prob_wm',
                                      'norm_prob_csf']),
        name='outputnode')

    reg_pipe.connect(align_seg, 'out_file', outputnode, "norm_seg")

    reg_pipe.connect(align_threshold_gm, 'out_file',
                     outputnode, "norm_threshold_gm")
    reg_pipe.connect(align_threshold_wm, 'out_file',
                     outputnode, "norm_threshold_wm")
    reg_pipe.connect(align_threshold_csf, 'out_file',
                     outputnode, "norm_threshold_csf")

    reg_pipe.connect(align_prob_gm, 'out_file', outputnode, "norm_prob_gm")
    reg_pipe.connect(align_prob_wm, 'out_file', outputnode, "norm_prob_wm")
    reg_pipe.connect(align_prob_csf, 'out_file', outputnode, "norm_prob_csf")

    return reg_pipe
