import os
from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    TraitedSpec)
from nipype.interfaces.base import traits, File


# T1xT2BiasFieldCorrection
class T1xT2BiasFieldCorrectionInputSpec(CommandLineInputSpec):

    t1_file = File(
        exists=True,
        desc='Whole-head T1w image',
        mandatory=True, position=0, argstr="-t1 %s")

    t2_file = File(
        exists=True,
        desc='Whole-head T2w image (use -aT2 if T2w image is not in the T1w \
              space)',
        mandatory=True, position=1, argstr="-t2 %s")

    os = traits.String(
        "_debiased", usedefault=True,
        desc="Suffix for the bias field corrected images (default is \
              \"_debiased\")",
        argstr="-os %s", mandatory=False)

    aT2 = traits.Bool(
        False, usedefault=True,
        argstr="-aT2",
        desc="Will coregrister T2w to T1w using flirt. Output will have the\
            suffix provided. Will only work for spatially close images.",
        mandatory=False)

    # as -> opt_as, as is already a part of python keywords...
    opt_as = traits.String(
        "-in-T1w", usedefault=True, argstr="-as %s",
        desc="Suffix for T2w to T1w registration \
              (\"-in-T1w\" if not specified)",
        mandatory=False)

    s = traits.Int(
        4, usedefault=True,
        desc='size of gauss kernel in mm when performing mean filtering \
              (default=4)',
        argstr="-s %d", mandatory=False)

    # exists = True ???
    b = traits.File(
        argstr="-b %s",
        desc="Brain mask file. Will also output bias corrected brain files \
            with the format \"output_prefix_brain.nii.gz\"",
        mandatory=False)

    bet = traits.Int(
        0, usedefault=True,
        desc='Will try to "smart" BET the anat files to get a brain mask: n =\
            the number of iterations BET will be run to find center of gravity\
            (default=0, will not BET if option -b has been specified).',
        argstr="-bet %d", mandatory=False)

    bs = traits.String(
        "_BET", usedefault=True,
        desc="Suffix for the BET masked images (default is \"_BET\")",
        argstr="-bs %s", mandatory=False)

    f = traits.Float(
        0.5, usedefault=True,
        desc='-f options of BET: fractional intensity threshold (0->1); \
            default=0.5; smaller values give larger brain outline estimates',
        argstr="-f %f", mandatory=False)

    g = traits.Float(
        0.0, usedefault=True, desc='-g options of BET:\
                  vertical gradient in fractional intensity threshold (-1->1);\
                  default=0; positive values give larger brain outline at\
                  bottom, smaller at top',
        argstr="-g %f", mandatory=False)

    k = traits.Bool(
        False, usedefault=True, argstr="-k",
        desc="Will keep temporary files",
        mandatory=False)

    p = traits.String(
        desc="Prefix for running FSL functions\
              (can be a path or just a prefix)",
        argstr="-p %s", mandatory=False)


class T1xT2BiasFieldCorrectionOutputSpec(TraitedSpec):
    t1_debiased_file = File(
        exists=True,
        desc="debiased T1")

    t2_debiased_file = File(
        exists=True,
        desc="debiased T2")

    t2_coreg_file = File(
        desc="T2 on T1")

    t1_debiased_brain_file = File(
        desc="debiased bet T1")

    t2_debiased_brain_file = File(
        desc="debiased bet T2")

    debiased_mask_file = File(
        desc="debiased bet mask")


class T1xT2BiasFieldCorrection(CommandLine):
    """
    Description:  Bias field correction using T1w & T2w images.
        Provides an attempt of brain extration if wanted.

    Inputs:

        Mandatory:

            t1_file
                Whole-head T1w image
            t2_file
                Whole-head T2w image (use -aT2 if T2w image is not in the T1w
                space)

        Optional:

            os
                Suffix for the bias field corrected images (default is
                "_debiased")
            aT2
                Will coregrister T2w to T1w using flirt. Output will have the\
                    suffix provided. Will only work for spatially close images.
            opt_as
                Suffix for T2w to T1w registration ("-in-T1w" if not specified)
            s
                size of gauss kernel in mm when performing mean filtering \
                    (default=4)argstr="-s %d", mandatory=False)
            b
                Brain mask file. Will also output bias corrected brain files \
                    with the format "output_prefix_brain.nii.gz"
            bet
                Will try to "smart" BET the anat files to get a brain mask:
                n = the number of iterations BET will be run to find center of
                gravity (default=0, will not BET if option -b has been
                specified).
            bs
                Suffix for the BET masked images (default is "_BET")
            f
                -f options of BET: fractional intensity threshold (0->1); \
                    default=0.5; smaller values give larger brain outline
                    estimates
            g
                -g options of BET:\
                        vertical gradient in fractional intensity threshold
                        (-1->1); default=0; positive values give larger brain
                        outline at bottom, smaller at top
            k
                Will keep temporary files
            p
                Prefix for running FSL functions\
                    (can be a path or just a prefix)

    Outputs:

        t1_debiased_file
            debiased T1
        t2_debiased_file
            debiased T2
        t2_coreg_file
            T2 on T1
        t1_debiased_brain_file
            debiased bet T1
        t2_debiased_brain_file
            debiased bet T2
        debiased_mask_file
            debiased bet mask
    """
    input_spec = T1xT2BiasFieldCorrectionInputSpec
    output_spec = T1xT2BiasFieldCorrectionOutputSpec

    package_directory = os.path.dirname(os.path.abspath(__file__))
    _cmd = 'bash {}/../bash/T1xT2BiasFieldCorrection.sh'.format(
        package_directory)

    def _list_outputs(self):

        import os
        from nipype.utils.filemanip import split_filename as split_f

        outputs = self._outputs().get()

        t1_path, t1_fname, ext = split_f(self.inputs.t1_file)
        t2_path, t2_fname, ext = split_f(self.inputs.t2_file)

        # !!!!warning, in Regis bash, only .nii.gz are handled
        outputs["t1_debiased_file"] = os.path.abspath(
            t1_fname + self.inputs.os + ".nii.gz")
        outputs["t2_debiased_file"] = os.path.abspath(
            t2_fname + self.inputs.os + ".nii.gz")

        if self.inputs.aT2:
            outputs["t2_coreg_file"] = os.path.abspath(
                t2_fname + self.inputs.opt_as + ".nii.gz")

        if self.inputs.bet:
            outputs["t1_debiased_brain_file"] = os.path.abspath(
                t1_fname + self.inputs.os + self.inputs.bs + ".nii.gz")
            outputs["t2_debiased_brain_file"] = os.path.abspath(
                t2_fname + self.inputs.os + self.inputs.bs + ".nii.gz")
            outputs["debiased_mask_file"] = os.path.abspath(
                t1_fname + self.inputs.os + self.inputs.bs + "_mask.nii.gz")
        elif self.inputs.b:
            outputs["t1_debiased_brain_file"] = os.path.abspath(
                t1_fname + self.inputs.os + "_brain.nii.gz")
            outputs["t2_debiased_brain_file"] = os.path.abspath(
                t2_fname + self.inputs.os + "_brain.nii.gz")
        return outputs
