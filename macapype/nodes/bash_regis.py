
from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    TraitedSpec)
from nipype.interfaces.base import traits, File


class T1xT2BETInputSpec(CommandLineInputSpec):

    t1_file = File(
        exists=True,
        desc='Whole-head T1w image',
        mandatory=True, position=0, argstr="-t1 %s")

    t2_file = File(
        exists=True,
        desc='Whole-head T2w image',
        mandatory=True, position=1, argstr="-t2 %s")

    os = traits.String(
        "_BET", usedefault=True,
        desc="Suffix for the brain masked images (default is _BET)",
        position=2, argstr="-os %s", mandatory=True)

    aT2 = traits.Bool(
        True, usedefault=True,
        position=3, argstr="-aT2",
        desc="Will coregrister T2w to T1w using flirt. Output will have the\
            suffix provided. Will only work for spatially close images.",
        mandatory=False)

    # as -> opt_as, as is already a part of python keywords...
    opt_as = traits.Bool(
        False, usedefault=True,
        position=3, argstr="-as",
        desc="Suffix for T2w to T1w registration \
            (\"-in-T1w\" if not specified)",
        mandatory=False)

    n = traits.Int(
        1, usedefault=True,
        desc='n = the number of iterations BET will be run to find center of \
            gravity (n=1 if option -n is absent)',
        position=3, argstr="-n %d", mandatory=True)

    m = traits.Bool(
        False, usedefault=True,
        position=3, argstr="-m",
        desc="Will output the BET mask at the format \
            output_prefixT1_mask.nii.gz)",
        mandatory=True)

    ms = traits.String(
        "_mask", usedefault=True,
        desc="Suffix for the mask (default is _mask)",
        position=3, argstr="-ms %s", mandatory=True)

    c = traits.Int(
        desc='Will crop the inputs & outputs after brain extraction. c is the \
            space between the brain and the limits of the crop box expressed \
            in percentage of the brain size (eg. if the brain size is 200\
            voxels in one dimension and c=10: the sides of the brain in this \
            dimension will be 20 voxels away from the borders of the resulting\
            crop box in this dimension).',
        position=3, argstr="-c %d", mandatory=False)

    cs = traits.String(
        "_cropped", usedefault=True,
        desc="Suffix for the cropped images (default is _cropped)",
        position=3, argstr="-cs %s", mandatory=False)

    f = traits.Float(
        0.5, usedefault=True,
        desc='-f options of BET: fractional intensity threshold (0->1); \
            default=0.5; smaller values give larger brain outline estimates',
        position=3, argstr="-f %f", mandatory=True)

    g = traits.Float(
        0.0, usedefault=True, desc='-g options of BET:\
                  vertical gradient in fractional intensity threshold (-1->1);\
                  default=0; positive values give larger brain outline at\
                  bottom, smaller at top',
        position=2, argstr="-g %f", mandatory=True)

    cog = traits.ListInt(
        desc='For difficult cases, you can directly provide a center of \
            gravity. Only one iteration will be performed.',
        position=3, argstr="-cog %d %d %d", mandatory=False)

    k = traits.Bool(
        False, usedefault=True,
        position=3, argstr="-k",
        desc="Will keep temporary files",
        mandatory=True)

    p = traits.String(
        desc="Prefix for running FSL functions\
            (can be a path or just a prefix)",
        position=3, argstr="-p %s")


class T1xT2BETOutputSpec(TraitedSpec):
    brain_file = File(
        exists=True,
        desc="extracted brain from T1xT2BET.sh")


class T1xT2BET(CommandLine):
    """
    Description:
        Brain extraction using T1 and T2 images


    Inputs:

    Outputs:

        brain_file:
            type = File, exists=True, desc="extracted brain from T1xT2BET.sh"

    """
    input_spec = T1xT2BETInputSpec
    output_spec = T1xT2BETOutputSpec

    _cmd = 'bash ../bash/T1xT2BET.sh'

    def _list_outputs(self):

        import os
        from nipype.utils.filemanip import split_filename as split_f

        outputs = self._outputs().get()

        path, fname, ext = split_f(self.inputs.t1_file)

        fname = fname + self.inputs.os

        if self.inputs.c:
            fname = fname + self.inputs.cs

        outputs["brain_file"] = os.path.abspath(fname + ext)
        return outputs
