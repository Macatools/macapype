
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu


def rename_all_derivatives(params, main_workflow, segment_pnh_pipe,
                           datasink, pref_deriv, parse_str, space, ssoft):

    if "brain_extraction_pipe" in params.keys():

        # rename brain_mask
        rename_brain_mask = pe.Node(niu.Rename(),
                                    name="rename_brain_mask")
        rename_brain_mask.inputs.format_string = \
            pref_deriv + "_space-native_desc-brain_mask"
        rename_brain_mask.inputs.parse_string = parse_str
        rename_brain_mask.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.brain_mask',
            rename_brain_mask, 'in_file')

        main_workflow.connect(
            rename_brain_mask, 'out_file',
            datasink, '@brain_mask')

    elif "debias" in params.keys():

        # rename brain_mask
        rename_brain_mask = pe.Node(
            niu.Rename(),
            name="rename_brain_mask")
        rename_brain_mask.inputs.format_string = \
            pref_deriv + "_space-native_desc-brain_mask"
        rename_brain_mask.inputs.parse_string = parse_str
        rename_brain_mask.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.brain_mask',
            rename_brain_mask, 'in_file')

        main_workflow.connect(
            rename_brain_mask, 'out_file',
            datasink, '@brain_mask')

        # rename debiased_T1
        rename_debiased_T1 = pe.Node(
            niu.Rename(),
            name="rename_debiased_T1")
        rename_debiased_T1.inputs.format_string = \
            pref_deriv + "_space-native_desc-debiased_T1w"
        rename_debiased_T1.inputs.parse_string = parse_str
        rename_debiased_T1.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.debiased_T1',
            rename_debiased_T1, 'in_file')

        main_workflow.connect(
            rename_debiased_T1, 'out_file',
            datasink, '@debiased_T1')

        # rename debiased_brain
        rename_debiased_brain = pe.Node(
            niu.Rename(),
            name="rename_debiased_brain")
        rename_debiased_brain.inputs.format_string = \
            pref_deriv + "_space-native_desc-debiased_desc-brain_T1w"
        rename_debiased_brain.inputs.parse_string = parse_str
        rename_debiased_brain.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.debiased_brain',
            rename_debiased_brain, 'in_file')

        main_workflow.connect(
            rename_debiased_brain, 'out_file',
            datasink, '@debiased_brain')

    if "brain_segment_pipe" in params.keys():
        # rename debiased_brain
        rename_debiased_brain = pe.Node(
            niu.Rename(),
            name="rename_debiased_brain")
        rename_debiased_brain.inputs.format_string = \
            pref_deriv + "_space-native_desc-debiased_desc-brain_T1w"
        rename_debiased_brain.inputs.parse_string = parse_str
        rename_debiased_brain.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.debiased_brain',
            rename_debiased_brain, 'in_file')

        main_workflow.connect(
            rename_debiased_brain, 'out_file',
            datasink, '@debiased_brain')

        # rename debiased_T1
        rename_debiased_T1 = pe.Node(niu.Rename(),
                                     name="rename_debiased_T1")
        rename_debiased_T1.inputs.format_string = \
            pref_deriv + "_space-native_desc-debiased_T1w"
        rename_debiased_T1.inputs.parse_string = parse_str
        rename_debiased_T1.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.debiased_T1',
            rename_debiased_T1, 'in_file')

        main_workflow.connect(
            rename_debiased_T1, 'out_file',
            datasink, '@debiased_T1')

        # rename segmented_brain_mask
        rename_segmented_brain_mask = pe.Node(
            niu.Rename(),
            name="rename_segmented_brain_mask")
        rename_segmented_brain_mask.inputs.format_string = \
            pref_deriv + "_space-{}_desc-brain_dseg".format(space)
        rename_segmented_brain_mask.inputs.parse_string = parse_str
        rename_segmented_brain_mask.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.segmented_brain_mask',
            rename_segmented_brain_mask, 'in_file')

        main_workflow.connect(
            rename_segmented_brain_mask, 'out_file',
            datasink, '@segmented_brain_mask')

        # rename prob_wm
        rename_prob_wm = pe.Node(niu.Rename(), name="rename_prob_wm")
        rename_prob_wm.inputs.format_string = \
            pref_deriv + "_space-{}_label-WM_probseg".format(space)
        rename_prob_wm.inputs.parse_string = parse_str
        rename_prob_wm.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.prob_wm',
            rename_prob_wm, 'in_file')

        main_workflow.connect(
            rename_prob_wm, 'out_file',
            datasink, '@prob_wm')

        # rename prob_gm
        rename_prob_gm = pe.Node(niu.Rename(), name="rename_prob_gm")
        rename_prob_gm.inputs.format_string = \
            pref_deriv + "_space-{}_label-GM_probseg".format(space)
        rename_prob_gm.inputs.parse_string = parse_str
        rename_prob_gm.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.prob_gm',
            rename_prob_gm, 'in_file')

        main_workflow.connect(
            rename_prob_gm, 'out_file',
            datasink, '@prob_gm')

        # rename prob_csf
        rename_prob_csf = pe.Node(niu.Rename(), name="rename_prob_csf")
        rename_prob_csf.inputs.format_string = \
            pref_deriv + "_space-{}_label-CSF_probseg".format(space)
        rename_prob_csf.inputs.parse_string = parse_str
        rename_prob_csf.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.prob_csf',
            rename_prob_csf, 'in_file')

        main_workflow.connect(
            rename_prob_csf, 'out_file',
            datasink, '@prob_csf')

        # rename 5tt
        if "export_5tt_pipe" in params["brain_segment_pipe"].keys():
            rename_gen_5tt = pe.Node(niu.Rename(), name="rename_gen_5tt")
            rename_gen_5tt.inputs.format_string = \
                pref_deriv + "_space-{}_desc-5tt_dseg".format(space)
            rename_gen_5tt.inputs.parse_string = parse_str
            rename_gen_5tt.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.gen_5tt',
                rename_gen_5tt, 'in_file')

            main_workflow.connect(
                rename_gen_5tt, 'out_file',
                datasink, '@gen_5tt')

        if "nii2mesh_brain_pipe" in params["brain_segment_pipe"].keys():

            if "native_to_stereo_pipe" in params.keys():

                print("Renaming stereo_wmgm_stl file")

                rename_stereo_wmgm_stl = pe.Node(niu.Rename(),
                                                 name="rename_stereo_wmgm_stl")
                rename_stereo_wmgm_stl.inputs.format_string = \
                    pref_deriv + "_space-stereo_desc-wmgm_mask"

                rename_stereo_wmgm_stl.inputs.parse_string = parse_str
                rename_stereo_wmgm_stl.inputs.keep_ext = True

                main_workflow.connect(
                    segment_pnh_pipe, 'outputnode.stereo_wmgm_stl',
                    rename_stereo_wmgm_stl, 'in_file')

                main_workflow.connect(
                    rename_stereo_wmgm_stl, 'out_file',
                    datasink, '@stereo_wmgm_stl')

                print("Renaming stereo_wmgm_mask file")
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

            else:

                print("Renaming wmgm_stl file")

                rename_wmgm_stl = pe.Node(niu.Rename(),
                                          name="rename_wmgm_stl")
                rename_wmgm_stl.inputs.format_string = \
                    pref_deriv + "_space-{}_desc-wmgm_mask".format(space)
                rename_wmgm_stl.inputs.parse_string = parse_str
                rename_wmgm_stl.inputs.keep_ext = True

                main_workflow.connect(
                    segment_pnh_pipe, 'outputnode.wmgm_stl',
                    rename_wmgm_stl, 'in_file')

                main_workflow.connect(
                    rename_wmgm_stl, 'out_file',
                    datasink, '@wmgm_stl')

                print("Renaming wmgm_nii file")
                rename_wmgm_mask = pe.Node(niu.Rename(),
                                           name="rename_wmgm_mask")
                rename_wmgm_mask.inputs.format_string = \
                    pref_deriv + "_space-{}_desc-wmgm_mask".format(space)
                rename_wmgm_mask.inputs.parse_string = parse_str
                rename_wmgm_mask.inputs.keep_ext = True

                main_workflow.connect(
                    segment_pnh_pipe, 'outputnode.wmgm_mask',
                    rename_wmgm_mask, 'in_file')

                main_workflow.connect(
                    rename_wmgm_mask, 'out_file',
                    datasink, '@wmgm_mask')

    elif "old_segment_pipe" in params.keys():

        # rename prob_wm
        print("Renaming prob_wm file")
        rename_prob_wm = pe.Node(niu.Rename(),
                                 name="rename_prob_wm")
        rename_prob_wm.inputs.format_string = \
            pref_deriv+"_space-{}_label-WM_probseg".format(space)
        rename_prob_wm.inputs.parse_string = parse_str
        rename_prob_wm.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.prob_wm',
            rename_prob_wm, 'in_file')

        main_workflow.connect(
            rename_prob_wm, 'out_file',
            datasink, '@prob_wm')

        # rename prob_gm
        print("Renaming prob_gm file")
        rename_prob_gm = pe.Node(niu.Rename(), name="rename_prob_gm")
        rename_prob_gm.inputs.format_string = \
            pref_deriv+"_space-{}_label-GM_probseg".format(space)
        rename_prob_gm.inputs.parse_string = parse_str
        rename_prob_gm.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.prob_gm',
            rename_prob_gm, 'in_file')

        main_workflow.connect(
            rename_prob_gm, 'out_file',
            datasink, '@prob_gm')

        # rename prob_csf
        print("Renaming prob_csf file")
        rename_prob_csf = pe.Node(niu.Rename(), name="rename_prob_csf")
        rename_prob_csf.inputs.format_string = \
            pref_deriv + "_space-{}_label-CSF_probseg".format(space)
        rename_prob_csf.inputs.parse_string = parse_str
        rename_prob_csf.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.prob_csf',
            rename_prob_csf, 'in_file')

        main_workflow.connect(
            rename_prob_csf, 'out_file',
            datasink, '@prob_csf')

    if "mask_from_seg_pipe" in params.keys():

        # rename segmented_brain_mask
        rename_segmented_brain_mask = pe.Node(
            niu.Rename(),
            name="rename_segmented_brain_mask")
        rename_segmented_brain_mask.inputs.format_string = \
            pref_deriv + "_space-{}_desc-brain_dseg".format(space)
        rename_segmented_brain_mask.inputs.parse_string = parse_str
        rename_segmented_brain_mask.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.segmented_brain_mask',
            rename_segmented_brain_mask, 'in_file')

        main_workflow.connect(
            rename_segmented_brain_mask, 'out_file',
            datasink, '@segmented_brain_mask')

        print("Renaming wmgm_stl file")

        rename_wmgm_stl = pe.Node(niu.Rename(),
                                  name="rename_wmgm_stl")
        rename_wmgm_stl.inputs.format_string = \
            pref_deriv + "_space-{}_desc-wmgm_mask".format(space)
        rename_wmgm_stl.inputs.parse_string = parse_str
        rename_wmgm_stl.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.wmgm_stl',
            rename_wmgm_stl, 'in_file')

        main_workflow.connect(
            rename_wmgm_stl, 'out_file',
            datasink, '@wmgm_stl')

    if "native_to_stereo_pipe" in params.keys():

        # rename stereo_native_T1
        rename_stereo_native_T1 = pe.Node(niu.Rename(),
                                          name="rename_stereo_native_T1")
        rename_stereo_native_T1.inputs.format_string = \
            pref_deriv + "_space-stereo_T1w"
        rename_stereo_native_T1.inputs.parse_string = parse_str
        rename_stereo_native_T1.inputs.keep_ext = True

        main_workflow.connect(
            segment_pnh_pipe, 'outputnode.stereo_native_T1',
            rename_stereo_native_T1, 'in_file')

        main_workflow.connect(
            rename_stereo_native_T1, 'out_file',
            datasink, '@stereo_native_T1')

        if "brain_extraction_pipe" in params.keys():
            # rename stereo_brain_mask
            rename_stereo_brain_mask = pe.Node(
                niu.Rename(),
                name="rename_stereo_brain_mask")
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

            # rename stereo_debiased_T1
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

        elif "debias" in params.keys():
            # rename stereo_brain_mask
            rename_stereo_brain_mask = pe.Node(
                niu.Rename(),
                name="rename_stereo_brain_mask")
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

            # rename stereo_debiased_T1
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

        if "brain_segment_pipe" in params.keys():

            # rename stereo_segmented_brain_mask
            rename_stereo_segmented_brain_mask = pe.Node(
                niu.Rename(),
                name="rename_stereo_segmented_brain_mask")

            rename_stereo_segmented_brain_mask.inputs.format_string =\
                pref_deriv + "_space-stereo_desc-brain_dseg"
            rename_stereo_segmented_brain_mask.inputs.parse_string = \
                parse_str
            rename_stereo_segmented_brain_mask.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.stereo_segmented_brain_mask',
                rename_stereo_segmented_brain_mask, 'in_file')

            main_workflow.connect(
                rename_stereo_segmented_brain_mask, 'out_file',
                datasink, '@stereo_segmented_brain_mask')

            # rename stereo_prob_gm
            print("Renaming stereo_prob_gm file")
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

            # rename stereo_prob_wm
            print("Renaming stereo_prob_wm file")
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

            # rename stereo_prob_csf
            print("Renaming stereo_prob_csf file")
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

        elif "mask_from_seg_pipe" in params:
            # rename stereo_segmented_brain_mask
            rename_stereo_segmented_brain_mask = pe.Node(
                niu.Rename(),
                name="rename_stereo_segmented_brain_mask")

            rename_stereo_segmented_brain_mask.inputs.format_string =\
                pref_deriv + "_space-stereo_desc-brain_dseg"
            rename_stereo_segmented_brain_mask.inputs.parse_string = \
                parse_str
            rename_stereo_segmented_brain_mask.inputs.keep_ext = True

            main_workflow.connect(
                segment_pnh_pipe, 'outputnode.stereo_segmented_brain_mask',
                rename_stereo_segmented_brain_mask, 'in_file')

            main_workflow.connect(
                rename_stereo_segmented_brain_mask, 'out_file',
                datasink, '@stereo_segmented_brain_mask')
