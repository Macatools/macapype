

from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    TraitedSpec)
from nipype.interfaces.base import traits, File


# AtlasBREX
class AtlasBREXInputSpec(CommandLineInputSpec):


    package_directory = os.path.dirname(os.path.abspath(__file__))

    script_atlas_BREX = File(
        '{}/../bash/atlasBREX.sh'.format(package_directory),
        usedefault = True
        exists=True,
        desc='atlasBREX script',
        mandatory=True, position=0, argstr="%s")

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

    reg = traits.Enum(
        1, 0, 2, 3, usedefault=True, desc="Method: 0 = FNIRT w/ bending, \
            1 (default) = FNIRT membrane-energy regularization, \
            2 = ANTs/SyN w/, \
            3 = w/o N4Bias",
        position=5, argstr="-reg %d", mandatory=True)

    w = traits.String(
        "10,10,10", usedefault=True, desc="w", position=6, argstr="-w %s",
        mandatory=True)

    msk = traits.String(
        "a,0,0", usedefault=True, desc="msk", position=7, argstr="-msk %s",
        mandatory=True)


class AtlasBREXOutputSpec(TraitedSpec):

    brain_file = File(
        exists=True,
        desc="extracted brain from atlas_brex")


class AtlasBREX(CommandLine):
    """
    Description:
        Atlas based BrainExtraction

    Inputs:

        script_atlas_BREX:
        type = File, exists=True, desc='atlasBREX script',,
            mandatory=True, position=0, argstr="%s"

        NMT_SS_file:
        type = File, exists=True,
        desc='Skullstriped version of the template',
            mandatory=True, position=1, argstr="-b %s"

        NMT_file:
        type = File, exists=True, desc='template img',
        mandatory=True, position=2, argstr="-nb %s"

        t1_restored_file:
        type = File, exists=True, desc='T1 image to map',
            mandatory=True, position=3, argstr="-h %s"

        f:
        type = Float, default = 0.5, usedefault=True, desc='f', position=4,
        argstr="-f %f", mandatory=True

        reg : type = Enum, default = 1,0,2,3, usedefault=True,
        desc="Method: 0 = FNIRT w/ bending, \
                1 (default) = FNIRT membrane-energy regularization, \
                2 = ANTs/SyN w/, \
                3 = w/o N4Bias",
            position=5, argstr="-reg %d", mandatory=True

        w:
        type = String, default = "10,10,10", usedefault=True, desc="w",
        position=6, argstr="-w %s", mandatory=True

        msk:
        type = String, default = "a,0,0", usedefault=True, desc="msk",
        position=7, argstr="-msk %s", mandatory=True)


    Outputs:

        brain_file:
            type = File, exists=True, desc="extracted brain from atlas_brex"

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
