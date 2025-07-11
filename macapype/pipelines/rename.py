
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu


def rename_all_brain_derivatives(params, main_workflow, segment_pnh_pipe,
                                 datasink, pref_deriv, parse_str,
                                 pad, ssoft, datatypes):
    # rename native_T1
    rename_native_T1 = pe.Node(
        niu.Rename(),
        name="rename_native_T1")
    rename_native_T1.inputs.format_string = \
        pref_deriv + "_space-native_T1w"
    rename_native_T1.inputs.parse_string = parse_str
    rename_native_T1.inputs.keep_ext = True

    main_workflow.connect(
        segment_pnh_pipe, 'outputnode.native_T1',
        rename_native_T1, 'in_file')

    main_workflow.connect(
        rename_native_T1, 'out_file',
        datasink, '@native_T1')

    # default: projection in stereo
    # rename stereo_T1
    rename_stereo_T1 = pe.Node(
        niu.Rename(),
        name="rename_stereo_T1")
    rename_stereo_T1.inputs.format_string = \
        pref_deriv + "_space-stereo_T1w"
    rename_stereo_T1.inputs.parse_string = parse_str
    rename_stereo_T1.inputs.keep_ext = True

    main_workflow.connect(
        segment_pnh_pipe, 'outputnode.stereo_T1',
        rename_stereo_T1, 'in_file')

    main_workflow.connect(
        rename_stereo_T1, 'out_file',
        datasink, '@stereo_T1')

    if 't2' in datatypes:

        # rename native_T2
        rename_native_T2 = pe.Node(
            niu.Rename(),
            name="rename_native_T2")
        rename_native_T2.inputs.format_string = \
            pref_deriv + "_space-native_T2w"
        rename_native_T2.inputs.parse_string = parse_str
        rename_native_T2.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.native_T2',
            rename_native_T2, 'in_file')

        main_workflow.connect(
            rename_native_T2, 'out_file',
            datasink, '@native_T2')

        # rename stereo_T2
        rename_stereo_T2 = pe.Node(
            niu.Rename(),
            name="rename_stereo_T2")
        rename_stereo_T2.inputs.format_string = \
            pref_deriv + "_space-stereo_T2w"
        rename_stereo_T2.inputs.parse_string = parse_str
        rename_stereo_T2.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.stereo_T2',
            rename_stereo_T2, 'in_file')

        main_workflow.connect(
            rename_stereo_T2, 'out_file',
            datasink, '@stereo_T2')

    # transfo to native to template and inverse

    # rename trans
    rename_trans = pe.Node(
        niu.Rename(),
        name="rename_trans")
    rename_trans.inputs.format_string = \
        pref_deriv + "_space-native_target-stereo_affine"
    rename_trans.inputs.parse_string = parse_str
    rename_trans.inputs.keep_ext = True

    main_workflow.connect(
        segment_pnh_pipe, 'outputnode.native_to_stereo_trans',
        rename_trans, 'in_file')

    main_workflow.connect(
        rename_trans, 'out_file',
        datasink, '@native_to_stereo_trans')

    # rename inv_trans
    rename_inv_trans = pe.Node(
        niu.Rename(),
        name="rename_inv_trans")
    rename_inv_trans.inputs.format_string = \
        pref_deriv + "_space-stereo_target-native_affine"
    rename_inv_trans.inputs.parse_string = parse_str
    rename_inv_trans.inputs.keep_ext = True

    main_workflow.connect(
        segment_pnh_pipe, 'outputnode.stereo_to_native_trans',
        rename_inv_trans, 'in_file')

    main_workflow.connect(
        rename_inv_trans, 'out_file',
        datasink, '@stereo_to_native_trans')

    if "denoise" in params["short_preparation_pipe"].keys():

        rename_stereo_denoised_T1 = pe.Node(
            niu.Rename(),
            name="rename_stereo_denoised_T1")
        rename_stereo_denoised_T1.inputs.format_string = \
            pref_deriv + "_space-stereo_desc-denoised_T1w"
        rename_stereo_denoised_T1.inputs.parse_string = parse_str
        rename_stereo_denoised_T1.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.stereo_denoised_T1',
            rename_stereo_denoised_T1, 'in_file')

        main_workflow.connect(
            rename_stereo_denoised_T1, 'out_file',
            datasink, '@stereo_denoised_T1')

        if 't2' in datatypes:

            # rename stereo_denoised_T2
            rename_stereo_denoised_T2 = pe.Node(
                niu.Rename(),
                name="rename_stereo_denoised_T2")
            rename_stereo_denoised_T2.inputs.format_string = \
                pref_deriv + "_space-stereo_desc-denoised_T2w"
            rename_stereo_denoised_T2.inputs.parse_string = parse_str
            rename_stereo_denoised_T2.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.stereo_denoised_T2',
                rename_stereo_denoised_T2, 'in_file')

            main_workflow.connect(
                rename_stereo_denoised_T2, 'out_file',
                datasink, '@stereo_denoised_T2')

    if "pad_template" in params["short_preparation_pipe"].keys():

        rename_stereo_padded_T1 = pe.Node(
            niu.Rename(),
            name="rename_stereo_padded_T1")
        rename_stereo_padded_T1.inputs.format_string = \
            pref_deriv + "_space-stereo_desc-pad_T1w"
        rename_stereo_padded_T1.inputs.parse_string = parse_str
        rename_stereo_padded_T1.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.stereo_padded_T1',
            rename_stereo_padded_T1, 'in_file')

        main_workflow.connect(
            rename_stereo_padded_T1, 'out_file',
            datasink, '@stereo_padded_T1')

        if 't2' in datatypes:

            # rename stereo_padded_T2
            rename_stereo_padded_T2 = pe.Node(
                niu.Rename(),
                name="rename_stereo_padded_T2")
            rename_stereo_padded_T2.inputs.format_string = \
                pref_deriv + "_space-stereo_desc-pad_T2w"
            rename_stereo_padded_T2.inputs.parse_string = parse_str
            rename_stereo_padded_T2.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.stereo_padded_T2',
                rename_stereo_padded_T2, 'in_file')

            main_workflow.connect(
                rename_stereo_padded_T2, 'out_file',
                datasink, '@stereo_padded_T2')

    if ("fast" in params["short_preparation_pipe"]
            or "N4debias" in params["short_preparation_pipe"]
            or "itk_debias" in params["short_preparation_pipe"]):

        # rename debiased_T1
        rename_stereo_debiased_T1 = pe.Node(
            niu.Rename(),
            name="rename_stereo_debiased_T1")
        rename_stereo_debiased_T1.inputs.format_string = \
            pref_deriv + "_space-stereo_desc-debiased_T1w"
        rename_stereo_debiased_T1.inputs.parse_string = parse_str
        rename_stereo_debiased_T1.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.stereo_debiased_T1',
            rename_stereo_debiased_T1, 'in_file')

        main_workflow.connect(
            rename_stereo_debiased_T1, 'out_file',
            datasink, '@stereo_debiased_T1')

        if 't2' in datatypes:

            # rename debiased_T2
            rename_stereo_debiased_T2 = pe.Node(
                niu.Rename(),
                name="rename_stereo_debiased_T2")
            rename_stereo_debiased_T2.inputs.format_string = \
                pref_deriv + "_space-stereo_desc-debiased_T2w"
            rename_stereo_debiased_T2.inputs.parse_string = parse_str
            rename_stereo_debiased_T2.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.stereo_debiased_T2',
                rename_stereo_debiased_T2, 'in_file')

            main_workflow.connect(
                rename_stereo_debiased_T2, 'out_file',
                datasink, '@stereo_debiased_T2')

    if "extract_pipe" in params.keys():

        # rename brain_mask
        rename_stereo_brain_mask = pe.Node(
            niu.Rename(), name="rename_stereo_brain_mask")
        rename_stereo_brain_mask.inputs.format_string = \
            pref_deriv + "_space-stereo_desc-brain_mask"
        rename_stereo_brain_mask.inputs.parse_string = parse_str
        rename_stereo_brain_mask.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.stereo_brain_mask',
            rename_stereo_brain_mask, 'in_file')

        main_workflow.connect(
            rename_stereo_brain_mask, 'out_file',
            datasink, '@stereo_brain_mask')

        if "pad_template" in params["short_preparation_pipe"].keys():

            rename_stereo_padded_brain_mask = pe.Node(
                niu.Rename(),
                name="rename_stereo_padded_brain_mask")
            rename_stereo_padded_brain_mask.inputs.format_string = \
                pref_deriv + "_space-stereo_desc-pad_desc-brain_mask"
            rename_stereo_padded_brain_mask.inputs.parse_string = parse_str
            rename_stereo_padded_brain_mask.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.stereo_padded_brain_mask',
                rename_stereo_padded_brain_mask, 'in_file')

            main_workflow.connect(
                rename_stereo_padded_brain_mask, 'out_file',
                datasink, '@stereo_padded_brain_mask')

    if "masked_correct_bias_pipe" in params.keys():

        # rename masked_debiased_T1
        rename_stereo_masked_debiased_T1 = pe.Node(
            niu.Rename(),
            name="rename_stereo_masked_debiased_T1")
        rename_stereo_masked_debiased_T1.inputs.format_string = \
            pref_deriv + "_space-stereo_desc-debiased_desc-brain_T1w"
        rename_stereo_masked_debiased_T1.inputs.parse_string = parse_str
        rename_stereo_masked_debiased_T1.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.stereo_masked_debiased_T1',
            rename_stereo_masked_debiased_T1, 'in_file')

        main_workflow.connect(
            rename_stereo_masked_debiased_T1, 'out_file',
            datasink, '@stereo_masked_debiased_T1')

        if 't2' in datatypes:

            # rename masked_debiased_T2
            rename_stereo_masked_debiased_T2 = pe.Node(
                niu.Rename(),
                name="rename_stereo_masked_debiased_T2")
            rename_stereo_masked_debiased_T2.inputs.format_string = \
                pref_deriv + "_space-stereo_desc-debiased_desc-brain_T2w"
            rename_stereo_masked_debiased_T2.inputs.parse_string = \
                parse_str
            rename_stereo_masked_debiased_T2.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.stereo_masked_debiased_T2',
                rename_stereo_masked_debiased_T2, 'in_file')

            main_workflow.connect(
                rename_stereo_masked_debiased_T2, 'out_file',
                datasink, '@stereo_masked_debiased_T2')

    if "debias" in params.keys():

        # rename masked_debiased_T1
        rename_stereo_masked_debiased_T1 = pe.Node(
            niu.Rename(),
            name="rename_stereo_masked_debiased_T1")
        rename_stereo_masked_debiased_T1.inputs.format_string = \
            pref_deriv + "_space-stereo_desc-debiased_desc-brain_T1w"
        rename_stereo_masked_debiased_T1.inputs.parse_string = parse_str
        rename_stereo_masked_debiased_T1.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.stereo_masked_debiased_T1',
            rename_stereo_masked_debiased_T1, 'in_file')

        main_workflow.connect(
            rename_stereo_masked_debiased_T1, 'out_file',
            datasink, '@stereo_masked_debiased_T1')

        if 't2' in datatypes:
            # rename masked_debiased_T2
            rename_stereo_masked_debiased_T2 = pe.Node(
                niu.Rename(),
                name="rename_stereo_masked_debiased_T2")
            rename_stereo_masked_debiased_T2.inputs.format_string = \
                pref_deriv + "_space-stereo_desc-debiased_desc-brain_T2w"
            rename_stereo_masked_debiased_T2.inputs.parse_string = \
                parse_str
            rename_stereo_masked_debiased_T2.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.stereo_masked_debiased_T2',
                rename_stereo_masked_debiased_T2, 'in_file')

            main_workflow.connect(
                rename_stereo_masked_debiased_T2, 'out_file',
                datasink, '@stereo_masked_debiased_T2')

        if 'extract_pipe' not in params.keys():

            # rename brain_mask
            rename_stereo_brain_mask = pe.Node(
                niu.Rename(), name="rename_stereo_brain_mask")
            rename_stereo_brain_mask.inputs.format_string = \
                pref_deriv + "_space-stereo_desc-brain_mask"
            rename_stereo_brain_mask.inputs.parse_string = parse_str
            rename_stereo_brain_mask.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.stereo_brain_mask',
                rename_stereo_brain_mask, 'in_file')

            main_workflow.connect(
                rename_stereo_brain_mask, 'out_file',
                datasink, '@stereo_brain_mask')

    if "brain_segment_pipe" in params or "brain_old_segment_pipe" in params:

        # rename prob_wm
        rename_stereo_prob_wm = pe.Node(niu.Rename(),
                                        name="rename_stereo_prob_wm")
        rename_stereo_prob_wm.inputs.format_string = \
            pref_deriv + "_space-stereo_label-WM_probseg"
        rename_stereo_prob_wm.inputs.parse_string = parse_str
        rename_stereo_prob_wm.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.stereo_prob_wm',
            rename_stereo_prob_wm, 'in_file')

        main_workflow.connect(
            rename_stereo_prob_wm, 'out_file',
            datasink, '@stereo_prob_wm')

        # rename prob_gm
        rename_stereo_prob_gm = pe.Node(niu.Rename(),
                                        name="rename_stereo_prob_gm")
        rename_stereo_prob_gm.inputs.format_string = \
            pref_deriv + "_space-stereo_label-GM_probseg"
        rename_stereo_prob_gm.inputs.parse_string = parse_str
        rename_stereo_prob_gm.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.stereo_prob_gm',
            rename_stereo_prob_gm, 'in_file')

        main_workflow.connect(
            rename_stereo_prob_gm, 'out_file',
            datasink, '@stereo_prob_gm')

        # rename prob_csf
        rename_stereo_prob_csf = pe.Node(niu.Rename(),
                                         name="rename_stereo_prob_csf")
        rename_stereo_prob_csf.inputs.format_string = \
            pref_deriv + "_space-stereo_label-CSF_probseg"
        rename_stereo_prob_csf.inputs.parse_string = parse_str
        rename_stereo_prob_csf.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.stereo_prob_csf',
            rename_stereo_prob_csf, 'in_file')

        main_workflow.connect(
            rename_stereo_prob_csf, 'out_file',
            datasink, '@stereo_prob_csf')

        # rename segmented_brain_mask
        rename_stereo_segmented_brain_mask = pe.Node(
            niu.Rename(),
            name="rename_stereo_segmented_brain_mask")
        rename_stereo_segmented_brain_mask.inputs.format_string = \
            pref_deriv + "_space-stereo_desc-brain_dseg"
        rename_stereo_segmented_brain_mask.inputs.parse_string = parse_str
        rename_stereo_segmented_brain_mask.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.stereo_segmented_brain_mask',
            rename_stereo_segmented_brain_mask, 'in_file')

        main_workflow.connect(
            rename_stereo_segmented_brain_mask, 'out_file',
            datasink, '@stereo_segmented_brain_mask')

        if "pad_template" in params["short_preparation_pipe"].keys():

            rename_stereo_padded_segmented_brain_mask = pe.Node(
                niu.Rename(),
                name="rename_stereo_padded_segmented_brain_mask")
            rename_stereo_padded_segmented_brain_mask.inputs.format_string = \
                pref_deriv + "_space-stereo_desc-pad_desc-brain_dseg"
            rename_stereo_padded_segmented_brain_mask.inputs.parse_string = \
                parse_str
            rename_stereo_padded_segmented_brain_mask.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe,
                'outputnode.stereo_padded_segmented_brain_mask',
                rename_stereo_padded_segmented_brain_mask, 'in_file')

            main_workflow.connect(
                rename_stereo_padded_segmented_brain_mask, 'out_file',
                datasink, '@stereo_padded_segmented_brain_mask')

        # rename 5tt
        if "export_5tt_pipe" in params.keys():
            rename_stereo_gen_5tt = pe.Node(
                niu.Rename(),
                name="rename_stereo_gen_5tt")
            rename_stereo_gen_5tt.inputs.format_string = \
                pref_deriv + "_space-stereo_desc-5tt_dseg"
            rename_stereo_gen_5tt.inputs.parse_string = parse_str
            rename_stereo_gen_5tt.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.stereo_gen_5tt',
                rename_stereo_gen_5tt, 'in_file')

            main_workflow.connect(
                rename_stereo_gen_5tt, 'out_file',
                datasink, '@stereo_gen_5tt')

        if "nii2mesh_brain_pipe" in params \
                or "IsoSurface_brain_pipe" in params:

            print("Renaming wmgm_stl file")

            rename_csfwmgm_stl = pe.Node(
                niu.Rename(), name="rename_csfwmgm_stl")
            rename_csfwmgm_stl.inputs.format_string = \
                pref_deriv + "_desc-wmgm_mask"
            rename_csfwmgm_stl.inputs.parse_string = parse_str
            rename_csfwmgm_stl.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.wmgm_stl',
                rename_csfwmgm_stl, 'in_file')

            main_workflow.connect(
                rename_csfwmgm_stl, 'out_file',
                datasink, '@csfwmgm_stl')

            print("Renaming wmgm_nii file")
            rename_stereo_wmgm_mask = pe.Node(
                niu.Rename(), name="rename_stereo_wmgm_mask")
            rename_stereo_wmgm_mask.inputs.format_string = \
                pref_deriv + "_space-stereo_desc-wmgm_mask"
            rename_stereo_wmgm_mask.inputs.parse_string = parse_str
            rename_stereo_wmgm_mask.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.stereo_wmgm_mask',
                rename_stereo_wmgm_mask, 'in_file')

            main_workflow.connect(
                rename_stereo_wmgm_mask, 'out_file',
                datasink, '@stereo_wmgm_mask')

        if "IsoSurface_tissues_pipe" in params:

            print("Renaming csf_stl file")

            rename_csf_stl = pe.Node(
                niu.Rename(), name="rename_csf_stl")
            rename_csf_stl.inputs.format_string = \
                pref_deriv + "_desc-csf_mask"
            rename_csf_stl.inputs.parse_string = parse_str
            rename_csf_stl.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.csf_stl',
                rename_csf_stl, 'in_file')

            main_workflow.connect(
                rename_csf_stl, 'out_file',
                datasink, '@csf_stl')

            print("Renaming wm_stl file")

            rename_wm_stl = pe.Node(
                niu.Rename(), name="rename_wm_stl")
            rename_wm_stl.inputs.format_string = \
                pref_deriv + "_desc-wm_mask"
            rename_wm_stl.inputs.parse_string = parse_str
            rename_wm_stl.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.wm_stl',
                rename_wm_stl, 'in_file')

            main_workflow.connect(
                rename_wm_stl, 'out_file',
                datasink, '@wm_stl')

            print("Renaming gm_stl file")

            rename_gm_stl = pe.Node(
                niu.Rename(), name="rename_gm_stl")
            rename_gm_stl.inputs.format_string = \
                pref_deriv + "_desc-gm_mask"
            rename_gm_stl.inputs.parse_string = parse_str
            rename_gm_stl.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.gm_stl',
                rename_gm_stl, 'in_file')

            main_workflow.connect(
                rename_gm_stl, 'out_file',
                datasink, '@gm_stl')

    # if pad back to native is defined
    if pad:

        if "denoise" in params["short_preparation_pipe"].keys():

            rename_native_denoised_T1 = pe.Node(
                niu.Rename(),
                name="rename_native_denoised_T1")
            rename_native_denoised_T1.inputs.format_string = \
                pref_deriv + "_space-native_desc-denoised_T1w"
            rename_native_denoised_T1.inputs.parse_string = parse_str
            rename_native_denoised_T1.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.native_denoised_T1',
                rename_native_denoised_T1, 'in_file')

            main_workflow.connect(
                rename_native_denoised_T1, 'out_file',
                datasink, '@native_denoised_T1')

            if 't2' in datatypes:

                # rename native_denoised_T2
                rename_native_denoised_T2 = pe.Node(
                    niu.Rename(),
                    name="rename_native_denoised_T2")
                rename_native_denoised_T2.inputs.format_string = \
                    pref_deriv + "_space-native_desc-denoised_T2w"
                rename_native_denoised_T2.inputs.parse_string = parse_str
                rename_native_denoised_T2.inputs.keep_ext = True

                main_workflow.connect(
                    segment_pnh_pipe, 'outputnode.native_denoised_T2',
                    rename_native_denoised_T2, 'in_file')

                main_workflow.connect(
                    rename_native_denoised_T2, 'out_file',
                    datasink, '@native_denoised_T2')

        # after some processing
        if ("fast" in params["short_preparation_pipe"]
                or "N4debias" in params["short_preparation_pipe"]
                or "itk_debias" in params["short_preparation_pipe"]):

            # rename debiased_T1
            rename_native_debiased_T1 = pe.Node(
                niu.Rename(),
                name="rename_native_debiased_T1")
            rename_native_debiased_T1.inputs.format_string = \
                pref_deriv + "_space-native_desc-debiased_T1w"
            rename_native_debiased_T1.inputs.parse_string = parse_str
            rename_native_debiased_T1.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.native_debiased_T1',
                rename_native_debiased_T1, 'in_file')

            main_workflow.connect(
                rename_native_debiased_T1, 'out_file',
                datasink, '@native_debiased_T1')

            if 't2' in datatypes:

                # rename debiased_T2
                rename_native_debiased_T2 = pe.Node(
                    niu.Rename(),
                    name="rename_native_debiased_T2")
                rename_native_debiased_T2.inputs.format_string = \
                    pref_deriv + "_space-native_desc-debiased_T2w"
                rename_native_debiased_T2.inputs.parse_string = parse_str
                rename_native_debiased_T2.inputs.keep_ext = True

                main_workflow.connect(
                    segment_pnh_pipe, 'outputnode.native_debiased_T2',
                    rename_native_debiased_T2, 'in_file')

                main_workflow.connect(
                    rename_native_debiased_T2, 'out_file',
                    datasink, '@native_debiased_T2')

        if "extract_pipe" in params.keys():

            # rename brain_mask
            rename_native_brain_mask = pe.Node(
                niu.Rename(), name="rename_native_brain_mask")
            rename_native_brain_mask.inputs.format_string = \
                pref_deriv + "_space-native_desc-brain_mask"
            rename_native_brain_mask.inputs.parse_string = parse_str
            rename_native_brain_mask.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.native_brain_mask',
                rename_native_brain_mask, 'in_file')

            main_workflow.connect(
                rename_native_brain_mask, 'out_file',
                datasink, '@native_brain_mask')

        if "masked_correct_bias_pipe" in params.keys():

            # rename masked_debiased_T1
            rename_native_masked_debiased_T1 = pe.Node(
                niu.Rename(),
                name="rename_native_masked_debiased_T1")
            rename_native_masked_debiased_T1.inputs.format_string = \
                pref_deriv + "_space-native_desc-debiased_desc-brain_T1w"
            rename_native_masked_debiased_T1.inputs.parse_string = parse_str
            rename_native_masked_debiased_T1.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.native_masked_debiased_T1',
                rename_native_masked_debiased_T1, 'in_file')

            main_workflow.connect(
                rename_native_masked_debiased_T1, 'out_file',
                datasink, '@native_masked_debiased_T1')

            if 't2' in datatypes:

                # rename masked_debiased_T2
                rename_native_masked_debiased_T2 = pe.Node(
                    niu.Rename(),
                    name="rename_native_masked_debiased_T2")
                rename_native_masked_debiased_T2.inputs.format_string = \
                    pref_deriv + "_space-native_desc-debiased_desc-brain_T2w"
                rename_native_masked_debiased_T2.inputs.parse_string = \
                    parse_str
                rename_native_masked_debiased_T2.inputs.keep_ext = True

                main_workflow.connect(
                    segment_pnh_pipe, 'outputnode.native_masked_debiased_T2',
                    rename_native_masked_debiased_T2, 'in_file')

                main_workflow.connect(
                    rename_native_masked_debiased_T2, 'out_file',
                    datasink, '@native_masked_debiased_T2')

        if "debias" in params.keys():

            # rename masked_debiased_T1
            rename_native_masked_debiased_T1 = pe.Node(
                niu.Rename(),
                name="rename_native_masked_debiased_T1")
            rename_native_masked_debiased_T1.inputs.format_string = \
                pref_deriv + "_space-native_desc-debiased_desc-brain_T1w"
            rename_native_masked_debiased_T1.inputs.parse_string = parse_str
            rename_native_masked_debiased_T1.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.native_masked_debiased_T1',
                rename_native_masked_debiased_T1, 'in_file')

            main_workflow.connect(
                rename_native_masked_debiased_T1, 'out_file',
                datasink, '@native_masked_debiased_T1')

            if 't2' in datatypes:
                # rename masked_debiased_T2
                rename_native_masked_debiased_T2 = pe.Node(
                    niu.Rename(),
                    name="rename_native_masked_debiased_T2")
                rename_native_masked_debiased_T2.inputs.format_string = \
                    pref_deriv + \
                    "_space-native_desc-debiased_desc-brain_T2w"

                rename_native_masked_debiased_T2.inputs.parse_string = \
                    parse_str
                rename_native_masked_debiased_T2.inputs.keep_ext = True

                main_workflow.connect(
                    segment_pnh_pipe, 'outputnode.native_masked_debiased_T2',
                    rename_native_masked_debiased_T2, 'in_file')

                main_workflow.connect(
                    rename_native_masked_debiased_T2, 'out_file',
                    datasink, '@native_masked_debiased_T2')

            if 'extract_pipe' not in params.keys():

                # rename brain_mask
                rename_native_brain_mask = pe.Node(
                    niu.Rename(), name="rename_native_brain_mask")
                rename_native_brain_mask.inputs.format_string = \
                    pref_deriv + "_space-native_desc-brain_mask"
                rename_native_brain_mask.inputs.parse_string = parse_str
                rename_native_brain_mask.inputs.keep_ext = True

                main_workflow.connect(
                    segment_pnh_pipe, 'outputnode.native_brain_mask',
                    rename_native_brain_mask, 'in_file')

                main_workflow.connect(
                    rename_native_brain_mask, 'out_file',
                    datasink, '@native_brain_mask')

        if "brain_segment_pipe" in params or \
                "brain_old_segment_pipe" in params:

            # rename prob_wm
            rename_native_prob_wm = pe.Node(
                niu.Rename(), name="rename_native_prob_wm")
            rename_native_prob_wm.inputs.format_string = \
                pref_deriv + "_space-native_label-WM_probseg"
            rename_native_prob_wm.inputs.parse_string = parse_str
            rename_native_prob_wm.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.native_prob_wm',
                rename_native_prob_wm, 'in_file')

            main_workflow.connect(
                rename_native_prob_wm, 'out_file',
                datasink, '@native_prob_wm')

            # rename prob_gm
            rename_native_prob_gm = pe.Node(
                niu.Rename(), name="rename_native_prob_gm")
            rename_native_prob_gm.inputs.format_string = \
                pref_deriv + "_space-native_label-GM_probseg"
            rename_native_prob_gm.inputs.parse_string = parse_str
            rename_native_prob_gm.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.native_prob_gm',
                rename_native_prob_gm, 'in_file')

            main_workflow.connect(
                rename_native_prob_gm, 'out_file',
                datasink, '@native_prob_gm')

            # rename prob_csf
            rename_native_prob_csf = pe.Node(
                niu.Rename(), name="rename_native_prob_csf")
            rename_native_prob_csf.inputs.format_string = \
                pref_deriv + "_space-native_label-CSF_probseg"
            rename_native_prob_csf.inputs.parse_string = parse_str
            rename_native_prob_csf.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.native_prob_csf',
                rename_native_prob_csf, 'in_file')

            main_workflow.connect(
                rename_native_prob_csf, 'out_file',
                datasink, '@native_prob_csf')

            # rename segmented_brain_mask
            rename_native_segmented_brain_mask = pe.Node(
                niu.Rename(),
                name="rename_native_segmented_brain_mask")
            rename_native_segmented_brain_mask.inputs.format_string = \
                pref_deriv + "_space-native_desc-brain_dseg"
            rename_native_segmented_brain_mask.inputs.parse_string = parse_str
            rename_native_segmented_brain_mask.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.native_segmented_brain_mask',
                rename_native_segmented_brain_mask, 'in_file')

            main_workflow.connect(
                rename_native_segmented_brain_mask, 'out_file',
                datasink, '@native_segmented_brain_mask')

            # rename 5tt
            if "export_5tt_pipe" in params.keys():
                rename_native_gen_5tt = pe.Node(
                    niu.Rename(), name="rename_native_gen_5tt")
                rename_native_gen_5tt.inputs.format_string = \
                    pref_deriv + "_space-native_desc-5tt_dseg"
                rename_native_gen_5tt.inputs.parse_string = parse_str
                rename_native_gen_5tt.inputs.keep_ext = True

                main_workflow.connect(
                    segment_pnh_pipe, 'outputnode.native_gen_5tt',
                    rename_native_gen_5tt, 'in_file')

                main_workflow.connect(
                    rename_native_gen_5tt, 'out_file',
                    datasink, '@native_gen_5tt')

            if "nii2mesh_brain_pipe" in params.keys() \
                    or "IsoSurface_brain_pipe" in params.keys():

                print("Renaming wmgm_stl file")

                rename_native_wmgm_stl = pe.Node(
                    niu.Rename(), name="rename_native_wmgm_stl")
                rename_native_wmgm_stl.inputs.format_string = \
                    pref_deriv + "_desc-wmgm_mask"
                rename_native_wmgm_stl.inputs.parse_string = parse_str
                rename_native_wmgm_stl.inputs.keep_ext = True

                main_workflow.connect(
                    segment_pnh_pipe, 'outputnode.wmgm_stl',
                    rename_native_wmgm_stl, 'in_file')

                main_workflow.connect(
                    rename_native_wmgm_stl, 'out_file',
                    datasink, '@native_wmgm_stl')

                print("Renaming wmgm_nii file")
                rename_native_wmgm_mask = pe.Node(
                    niu.Rename(), name="rename_native_wmgm_mask")
                rename_native_wmgm_mask.inputs.format_string = \
                    pref_deriv + "_space-native_desc-wmgm_mask"
                rename_native_wmgm_mask.inputs.parse_string = parse_str
                rename_native_wmgm_mask.inputs.keep_ext = True

                main_workflow.connect(
                    segment_pnh_pipe, 'outputnode.native_wmgm_mask',
                    rename_native_wmgm_mask, 'in_file')

                main_workflow.connect(
                    rename_native_wmgm_mask, 'out_file',
                    datasink, '@native_wmgm_mask')
