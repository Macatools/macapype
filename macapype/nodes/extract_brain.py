

from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    TraitedSpec)
from nipype.interfaces.base import traits, File, isdefined


import os
from nipype.interfaces.fsl.base import (FSLCommand, FSLCommandInputSpec)


class T1xT2BETInputSpec(FSLCommandInputSpec):

    t1_file = File(
        exists=True,
        desc='Whole-head T1w image',
        mandatory=True, position=0, argstr="-t1 %s")

    t2_file = File(
        exists=True,
        desc='Whole-head T2w image',
        mandatory=True, position=1, argstr="-t2 %s")

    opt_os = traits.String(
        "_BET", usedefault=True,
        desc="Suffix for the brain masked images (default is _BET)",
        argstr="-os %s", mandatory=False)

    aT2 = traits.Bool(
        False, usedefault=True, argstr="-aT2",
        desc="Will coregrister T2w to T1w using flirt. Output will have the\
            suffix provided. Will only work for spatially close images.",
        mandatory=False)

    # as -> opt_as, as is already a part of python keywords...
    opt_as = traits.String(
        "-in-T1w", usedefault=True, argstr="-as %s",
        desc="Suffix for T2w to T1w registration \
            (\"-in-T1w\" if not specified)",
        mandatory=False)

    n = traits.Int(
        1, usedefault=True,
        desc='n = the number of iterations BET will be run to find center of \
            gravity (n=1 if option -n is absent)',
        argstr="-n %d", mandatory=False)

    m = traits.Bool(
        False, usedefault=True, argstr="-m",
        desc="Will output the BET mask at the format \
              output_prefixT1_mask.nii.gz)",
        mandatory=False)

    ms = traits.String(
        "_mask", usedefault=True,
        desc="Suffix for the mask (default is _mask)",
        argstr="-ms %s", mandatory=False)

    c = traits.Int(
        desc='Will crop the inputs & outputs after brain extraction. c is the \
            space between the brain and the limits of the crop box expressed \
            in percentage of the brain size (eg. if the brain size is 200\
            voxels in one dimension and c=10: the sides of the brain in this \
            dimension will be 20 voxels away from the borders of the resulting\
            crop box in this dimension).',
        argstr="-c %d", mandatory=False)

    cs = traits.String(
        "_cropped", usedefault=True,
        desc="Suffix for the cropped images (default is _cropped)",
        argstr="-cs %s", mandatory=False)

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

    cog = traits.List(
        desc='For difficult cases, you can directly provide a center of \
            gravity. Only one iteration will be performed.',
        argstr="-cog %d %d %d", mandatory=False)

    k = traits.Bool(
        False, usedefault=True, argstr="-k",
        desc="Will keep temporary files",
        mandatory=False)

    p = traits.String(
        desc="Prefix for running FSL functions\
              (can be a path or just a prefix)",
        argstr="-p %s", mandatory=False)


class T1xT2BETOutputSpec(TraitedSpec):
    t1_brain_file = File(
        exists=True, desc="extracted brain from T1")

    t2_brain_file = File(
        exists=True, desc="extracted brain from T2")

    t2_coreg_file = File(
        desc="coreg T2 from T1")

    mask_file = File(
        desc="extracted mask from T1")

    t1_cropped_file = File(
        desc="extracted cropped brain from T1")

    t2_cropped_file = File(
        desc="extracted cropped brain from T2")


class T1xT2BET(FSLCommand):
    """
    Description: Brain extraction using T1 and T2 images

    Inputs:

        Mandatory:

            t1_file
                Whole-head T1w image
            t2_file
                Whole-head T2w image

        Optional:

            opt_os
                Suffix for the brain masked images (default is _BET)
            aT2
                Will coregrister T2w to T1w using flirt. Output will have the
                suffix provided. Will only work for spatially close images.
            opt_as
                Suffix for T2w to T1w registration (\"-in-T1w\" if not
                specified)
            n
                the number of iterations BET will be run to find center of
                gravity (n=1 if option -n is absent)
            m
                Will output the BET mask at the format
                output_prefixT1_mask.nii.gz)
            ms
                Suffix for the mask (default is _mask)
            c
                Will crop the inputs & outputs after brain extraction. c is the
                space between the brain and the limits of the crop box
                expressed in percentage of the brain size (eg. if the brain
                size is 200 voxels in one dimension and c=10: the sides of the
                brain in this dimension will be 20 voxels away from the borders
                of the resulting crop box in this dimension)
            cs
                Suffix for the cropped images (default is _cropped)
            f
                -f options of BET: fractional intensity threshold (0->1); \
                default=0.5; smaller values give larger brain outline estimates
            g
                '-g options of BET: \
                vertical gradient in fractional intensity threshold (-1->1);\
                default=0; positive values give larger brain outline at\
                bottom, smaller at top
            cog
                For difficult cases, you can directly provide a center of \
                gravity. Only one iteration will be performed.
            k
                Will keep temporary files
            p
                Prefix for running FSL functions (can be a path or just a
                prefix)

    Outputs:

        t1_brain_file
            extracted brain from T1
        t2_brain_file
            extracted brain from T2
        t2_coreg_file
            coreg T2 from T1
        mask_file
            extracted mask from T1
        t1_cropped_file
            extracted cropped brain from T1
        t2_cropped_file
            extracted cropped brain from T2


    """
    input_spec = T1xT2BETInputSpec
    output_spec = T1xT2BETOutputSpec

    path_to_current_dir = os.path.dirname(os.path.abspath(__file__))
    package_directory = os.path.dirname(path_to_current_dir)

    _cmd = 'bash {}/bash/T1xT2BET.sh'.format(package_directory)

    def _list_outputs(self):

        import os
        from nipype.utils.filemanip import split_filename as split_f

        outputs = self._outputs().get()

        t1_path, t1_fname, ext = split_f(self.inputs.t1_file)
        t2_path, t2_fname, ext = split_f(self.inputs.t2_file)

        if self.inputs.c:
            # !!!!warning, in Regis bash, only .nii.gz are handled
            outputs["t1_cropped_file"] = os.path.abspath(
                t1_fname + self.inputs.cs + ".nii.gz")

            if self.inputs.aT2:
                outputs["t2_cropped_file"] = os.path.abspath(
                    t2_fname + self.inputs.opt_as + self.inputs.cs + ".nii.gz")
            else:
                outputs["t2_cropped_file"] = os.path.abspath(
                    t2_fname + self.inputs.cs + ".nii.gz")

            outputs["t1_brain_file"] = os.path.abspath(
                t1_fname + self.inputs.opt_os + self.inputs.cs + ".nii.gz")
            outputs["t2_brain_file"] = os.path.abspath(
                t2_fname + self.inputs.opt_os + self.inputs.cs + ".nii.gz")

            if self.inputs.m:
                # !!!!warning, in Regis bash, only .nii.gz are handled
                outputs["mask_file"] = os.path.abspath(
                    t1_fname + self.inputs.opt_os + self.inputs.ms +
                    self.inputs.cs + ".nii.gz")

        else:

            outputs["t1_brain_file"] = os.path.abspath(
                t1_fname + self.inputs.opt_os + ".nii.gz")
            outputs["t2_brain_file"] = os.path.abspath(
                t2_fname + self.inputs.opt_os + ".nii.gz")

            if self.inputs.m:
                # !!!!warning, in Regis bash, only .nii.gz are handled
                outputs["mask_file"] = os.path.abspath(
                    t1_fname + self.inputs.opt_os + self.inputs.ms + ".nii.gz")

        if self.inputs.aT2:
            outputs["t2_coreg_file"] = os.path.abspath(
                t2_fname + self.inputs.opt_as + ".nii.gz")

        return outputs


# AtlasBREX
class AtlasBREXInputSpec(CommandLineInputSpec):

    import os

    path_to_current_dir = os.path.dirname(os.path.abspath(__file__))
    package_directory = os.path.dirname(path_to_current_dir)

    script_atlas_BREX = File('{}/bash/atlasBREX.sh'.format(
            package_directory), usedefault=True,
        exists=True,
        desc='atlasBREX script',
        mandatory=False, position=0, argstr="%s")

    NMT_SS_file = File(
        exists=True,
        desc='Skullstriped version of the template',
        mandatory=True, position=1, argstr="-b %s")

    NMT_file = File(
        exists=True,
        desc='template img',
        mandatory=True, position=2, argstr="-nb %s")

    t1_restored_file = File(
        exists=True,
        desc='T1 image to map',
        mandatory=True, position=3, argstr="-h %s")

    f = traits.Float(
        0.5, usedefault=True, desc='f', position=4, argstr="-f %f",
        mandatory=True)

    wrp = traits.String(
        "10,10,10", usedefault=True, desc="wrp", position=5, argstr="-wrp %s",
        mandatory=True)

    reg = traits.Enum(
        1, 0, 2, 3, usedefault=True, desc="Method: 0 = FNIRT w/ bending, \
            1 (default) = FNIRT membrane-energy regularization, \
            2 = ANTs/SyN w/, \
            3 = w/o N4Bias",
        position=6, argstr="-reg %d", mandatory=True)

    msk = traits.String(
        "a,0,0", usedefault=True, desc="msk", position=7, argstr="-msk %s",
        mandatory=True)

    dil = traits.Int(desc="dil", argstr="-dil %d")

    nrm = traits.Enum(1, 2, desc="nrm", argstr="-nrm %d")

    vox = traits.Int(desc="vox",  argstr="-vox %d")

    args = traits.String(desc="args", position=-1, argstr=" %s",
                         mandatory=False)


class AtlasBREXOutputSpec(TraitedSpec):

    brain_file = File(
        exists=True,
        desc="extracted brain from atlas_brex")


class AtlasBREX(CommandLine):
    """
    Description: Atlas based BrainExtraction

    Inputs:

        Mandatory:

            script_atlas_BREX:
                File, 'atlasBREX script'

            NMT_SS_file:
                File, 'Skullstriped version of the template',

            NMT_file:
                File, 'template img'

            t1_restored_file:
                File, 'T1 image to map'

            f:
                Float, default = 0.5, f


            reg :

                Enum, default = 1,0,2,3, "Method: 0 = FNIRT w/ bending, \
                1 (default) = FNIRT membrane-energy regularization, \
                2 = ANTs/SyN w/, \
                3 = w/o N4Bias"

            w:
                String, default = "10,10,10", "w"

            msk:
                String, default = "a,0,0", "msk",

    Outputs:

        brain_file:
            File, "extracted brain from atlas_brex"

    """
    input_spec = AtlasBREXInputSpec
    output_spec = AtlasBREXOutputSpec

    _cmd = 'bash'

    def _format_arg(self, name, spec, value):

        import os
        import shutil

        cur_dir = os.getcwd()

        if name == 'script_atlas_BREX':
            shutil.copy(value, cur_dir)
            value = os.path.split(value)[1]

        if name == 'NMT_SS_file':
            shutil.copy(value, cur_dir)
            value = os.path.split(value)[1]

        if name == 'NMT_file':
            shutil.copy(value, cur_dir)
            value = os.path.split(value)[1]

        if name == 't1_restored_file':
            shutil.copy(value, cur_dir)
            value = os.path.split(value)[1]

        return super(AtlasBREX, self)._format_arg(name, spec, value)

    def _list_outputs(self):

        import os
        from nipype.utils.filemanip import split_filename as split_f

        outputs = self._outputs().get()

        path, fname, ext = split_f(self.inputs.t1_restored_file)
        outputs["brain_file"] = os.path.abspath(fname + '_brain' + ext)

        return outputs


# HDBET
class HDBETInputSpec(CommandLineInputSpec):

    import os

    in_file = File(
        exists=True,
        desc='T1 image to map',
        mandatory=True, position=0, argstr="-i %s")

    out_file = File(
        desc='name of output skull stripped image',
        name_source=["in_file"],
        name_template="%s_brain",
        keep_extension=True,
        hash_files=False,
        position=1, argstr="-o %s")

    disable_tta = traits.Bool(
        True, usedefault=True, desc='disable_tta',
        argstr="--disable_tta", mandatory=False)

    device = traits.Enum(
        "cpu", 'cuda', 'mps', usedefault=True, desc="",
        argstr="-device %s", mandatory=True)

    verbose = traits.Bool(
        True, usedefault=True, desc='verbose', argstr="--verbose",
        mandatory=True)


class HDBETOutputSpec(TraitedSpec):
    out_file = File(
        exists=True,
        desc="extracted brain from hd-bet")

    mask_file = File(
        exists=True,
        desc="brain mask from hd-bet")


class HDBET(CommandLine):
    """
    Description: Atlas based BrainExtraction

    Inputs:

        Mandatory:

    Outputs:

        brain_file:
            File, "extracted brain from atlas_brex"

    """
    input_spec = HDBETInputSpec
    output_spec = HDBETOutputSpec

    _cmd = 'hd-bet --save_bet_mask '

    def _gen_maskfilename(self):
        from nipype.utils.filemanip import split_filename as split_f
        # Generate default mask filename
        if isdefined(self.inputs.in_file):
            path, fname, ext = split_f(self.inputs.in_file)
            mask_file = fname + "_brain_bet" + ext
            return os.path.abspath(mask_file)

    def _list_outputs(self):

        import os
        outputs = self._outputs().get()
        outputs["out_file"] = self.inputs.out_file
        outputs["mask_file"] = os.path.abspath(self._gen_maskfilename())

        return outputs


# Bet4Animal
class Bet4AnimalInputSpec(CommandLineInputSpec):

    import os

    in_file = File(
        exists=True,
        desc='T1 image to map',
        mandatory=True, position=0, argstr="%s")

    out_file = File(
        desc='name of output skull stripped image',
        name_source=["in_file"],
        name_template="%s_brain",
        keep_extension=True,
        hash_files=False,
        position=1, argstr="%s")

    outline = traits.Bool(
        False, usedefault=True, desc='outline',
        argstr="--outline", mandatory=False)

    mask = traits.Bool(
        True, usedefault=True, desc='mask',
        argstr="--mask", mandatory=False)

    label = traits.Enum(
        2, 0, 1, 3, usedefault=True, desc="label (default 2 = macaque)",
        argstr="-z %d", mandatory=True)

    robust = traits.Bool(
        True, usedefault=True,
        desc='robust brain centre estimation (iterates BET several times)',
        argstr="-R",)

    f = traits.Float(
        desc='fractional intensity threshold (0->1); default=0.5; \
        smaller values give larger brain outline estimates', argstr="-f %f",
        mandatory=False)


class Bet4AnimalOutputSpec(TraitedSpec):

    out_file = File(
        exists=True,
        desc="masked T1 from hd-bet")

    mask_file = File(
        exists=True,
        desc="brain mask from hd-bet")


class Bet4Animal(CommandLine):
    """
    Description: Atlas based BrainExtraction

    Inputs:

        Mandatory:

    Outputs:

        brain_file:
            File, "extracted brain from atlas_brex"

    """
    input_spec = Bet4AnimalInputSpec
    output_spec = Bet4AnimalOutputSpec

    _cmd = 'bet4animal '

    def _gen_maskfilename(self):
        from nipype.utils.filemanip import split_filename as split_f
        # Generate default mask filename
        if isdefined(self.inputs.in_file) and self.inputs.mask is True:
            path, fname, ext = split_f(self.inputs.in_file)
            mask_file = fname + "_brain_mask" + ext
            return os.path.abspath(mask_file)

    def _list_outputs(self):

        outputs = self._outputs().get()

        outputs["out_file"] = self.inputs.out_file
        if self.inputs.mask is True:
            outputs["mask_file"] = os.path.abspath(self._gen_maskfilename())

        return outputs


if __name__ == '__main__':
    ab = AtlasBREX()

    print(ab.cmdline)
