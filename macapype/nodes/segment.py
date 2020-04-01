import os
from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    TraitedSpec)
from nipype.interfaces.base import traits, File


class AtroposN4InputSpec(CommandLineInputSpec):

    dimension = traits.Int(
        3, default=True, usedefault=True,
        exists=True,
        desc='Dimension',
        mandatory=True, position=0, argstr="-d %d")

    brain_file = File(
        exists=True,
        desc='brain_file',
        mandatory=True, position=1, argstr="-a %s")

    brainmask_file = File(
        exists=True,
        desc='brain_file',
        mandatory=True, position=2, argstr="-x %s")

    numberOfClasses = traits.Int(
        3, usedefault=True,
        exists=True,
        desc='numberOfClasses',
        mandatory=True, position=3, argstr="-c %d")

    priors = traits.List(
        File(exists=True),
        desc='priors',
        mandatory=True)

    template_file = traits.String(
        "tmp_%02d_allineate.nii.gz", usedefault=True,
        exists=True,
        desc='template_file',
        mandatory=True, position=4, argstr="-p %s")

    out_pref = traits.String(
        "segment_", usedefault=True, desc="output prefix", mandatory=False,
        position=5,  argstr="-o %s")


class AtroposN4OutputSpec(TraitedSpec):
    segmented_file = File(
        exists=True, desc="segmented file with all tissues")

    segmented_files = traits.List(
        File(exists=True), desc="segmented indivual files")


class AtroposN4(CommandLine):
    """
    Description:
        Wrap of antsAtroposN4.sh
        Requires PATH to ANTS Scripts added


    Inputs:

    Outputs:

        brain_file:
            type = File, exists=True, desc="extracted brain from AtroposN4.sh"

    """
    input_spec = AtroposN4InputSpec
    output_spec = AtroposN4OutputSpec

    package_directory = os.path.dirname(os.path.abspath(__file__))
    _cmd = 'bash antsAtroposN4.sh'.format(package_directory)

    def _format_arg(self, name, spec, value):
        import os
        import shutil

        cur_path = os.path.abspath("")

        # all the files have to be in local and
        if name == 'brain_file' or name == 'brainmask_file':
            # requires local copy
            shutil.copy(value, cur_path)
            value = os.path.split(value)[1]

        elif name == 'priors':
            new_value = []

            for prior_file in value:
                shutil.copy(prior_file, cur_path)
                new_value.append(os.path.split(prior_file)[1])

            value = new_value
        return super(AtroposN4, self)._format_arg(name, spec, value)

    def _list_outputs(self):

        import os
        import glob

        outputs = self._outputs().get()

        outputs['segmented_file'] = os.path.abspath(
            self.inputs.out_pref + "Segmentation.nii.gz")

        seg_files = glob.glob(
            self.inputs.out_pref + "SegmentationPosteriors*.nii.gz")

        assert len(seg_files) == len(self.inputs.priors), \
            "Error, there should {} SegmentationPosteriors".format(
                len(self.inputs.priors))

        outputs['segmented_files'] = [os.path.abspath(
            seg_file) for seg_file in seg_files]

        return outputs


if __name__ == '__main__':
    # path_to = "/hpc/crise/meunier.d"
    path_to = "/hpc/crise/meunier.d/Data/Primavoice/test_pipeline_kepkee_crop"

    seg_path = os.path.join(path_to, "segment_pnh_subpipes",
                            "segment_devel_NMT_sub_align")

    brain_file = os.path.join(
        seg_path, "segment_atropos_pipe", "_session_01_subject_Apache",
        "deoblique",
        "sub-Apache_ses-01_T1w_cropped_noise_corrected_maths_masked_\
            corrected.nii.gz")

    brainmask_file = os.path.join(
        seg_path, "segment_atropos_pipe", "_session_01_subject_Apache",
        "bin_norm_intensity",
        "sub-Apache_ses-01_T1w_cropped_noise_corrected_maths_masked_\
            corrected_bin.nii.gz")

    priors = [os.path.join(
        seg_path, "register_NMT_pipe", "_session_01_subject_Apache",
        "align_seg_csf", "NMT_segmentation_CSF_allineate.nii.gz"),
              os.path.join(
                  seg_path, "register_NMT_pipe", "_session_01_subject_Apache",
                  "align_seg_gm", "NMT_segmentation_GM_allineate.nii.gz"),
              os.path.join(
                  seg_path, "register_NMT_pipe", "_session_01_subject_Apache",
                  "align_seg_wm", "NMT_segmentation_WM_allineate.nii.gz")]

    seg_at = AtroposN4()

    seg_at.inputs.brain_file = brain_file
    seg_at.inputs.brainmask_file = brainmask_file

    seg_at.inputs.priors = priors

    val = seg_at.run().outputs

    print(val)
