import os

from nipype.interfaces.afni.base import (AFNICommandBase,
                                         AFNICommandOutputSpec,
                                         isdefined)

from nipype.utils.filemanip import split_filename as split_f

from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    TraitedSpec, traits, File)


def interative_flirt(anat_file, anat_file_BET, template_brain_file,
                     template_mask_file, n_iter):
    """
    This funcion, from Regis script, aims at interatively building a better
    skull stripped version of the subject's. There is a need for an already
    computed skullstripped version to initiallized the procedure
    (anat_file_BET)

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
        # apply_mask = fsl.ApplyMask() ### a voir si plus pertinent...
        apply_mask = fsl.BinaryMaths()
        apply_mask.inputs.in_file = anat_file
        apply_mask.inputs.operation = 'mul'
        apply_mask.inputs.operand_file = anat_file_brain_mask
        apply_mask.inputs.out_file = anat_file_brain
        apply_mask.inputs.output_type = "NIFTI"
        apply_mask.run()

        flirt_ref_file = anat_file_brain

    return anat_file_brain, template_to_anat_file


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

        from nipype.utils.filemanip import split_filename as split_f

        outputs = self._outputs().get()

        path, fname, ext = split_f(self.inputs.T1_file)

        outputs["shft_aff_file"] = os.path.abspath(fname + "_shft_aff" + ext)
        outputs["warpinv_file"] = os.path.abspath(
            fname + "_shft_WARPINV.nii")

        # outputs["warpinv_file"] = os.path.abspath(
        #    fname + "_shft_WARPINV" + ext)

        outputs["transfo_file"] = os.path.abspath(
            fname + "_composite_linear_to_NMT.1D")
        outputs["inv_transfo_file"] = os.path.abspath(
            fname + "_composite_linear_to_NMT_inv.1D")

        return outputs


# should be added to nipype instead of here...
# NwarpApplyPriors
class NwarpApplyPriorsInputSpec(CommandLineInputSpec):
    in_file = traits.Either(
        File(exists=True),
        traits.List(File(exists=True)),
        mandatory=True,
        argstr='-source %s',
        desc='the name of the dataset to be warped '
        'can be multiple datasets')
    warp = traits.String(
        desc='the name of the warp dataset. '
        'multiple warps can be concatenated (make sure they exist)',
        argstr='-nwarp %s',
        mandatory=True)
    inv_warp = traits.Bool(
        desc='After the warp specified in \'-nwarp\' is computed, invert it',
        argstr='-iwarp')
    master = traits.File(
        exists=True,
        desc='the name of the master dataset, which defines the output grid',
        argstr='-master %s')
    interp = traits.Enum(
        'wsinc5',
        'NN',
        'nearestneighbour',
        'nearestneighbor',
        'linear',
        'trilinear',
        'cubic',
        'tricubic',
        'quintic',
        'triquintic',
        desc='defines interpolation method to use during warp',
        argstr='-interp %s',
        usedefault=True)
    ainterp = traits.Enum(
        'NN',
        'nearestneighbour',
        'nearestneighbor',
        'linear',
        'trilinear',
        'cubic',
        'tricubic',
        'quintic',
        'triquintic',
        'wsinc5',
        desc='specify a different interpolation method than might '
        'be used for the warp',
        argstr='-ainterp %s')
    out_file = traits.Either(
        File(),
        traits.List(File()),
        mandatory=True,
        argstr='-prefix %s',
        desc='output image file name')
    short = traits.Bool(
        desc='Write output dataset using 16-bit short integers, rather than '
        'the usual 32-bit floats.',
        argstr='-short')
    quiet = traits.Bool(
        desc='don\'t be verbose :(', argstr='-quiet', xor=['verb'])
    verb = traits.Bool(
        desc='be extra verbose :)', argstr='-verb', xor=['quiet'])


class NwarpApplyPriorsOutputSpec(AFNICommandOutputSpec):
    out_file = traits.Either(
            File(),
            traits.List(File()))


class NwarpApplyPriors(AFNICommandBase):
    """
    Over Wrap of NwarpApply (afni node) in order to generate files in the right
    node directory (instead of in the original data directory, or the script
    directory as is now)

    Modifications are made over inputs and outputs
    """

    _cmd = '3dNwarpApply'
    input_spec = NwarpApplyPriorsInputSpec
    output_spec = NwarpApplyPriorsOutputSpec

    def _format_arg(self, name, spec, value):

        import os
        import shutil

        cur_dir = os.getcwd()

        new_value = []
        if name == 'in_file':
            for in_file in value:
                print(in_file)

                # copy en local
                shutil.copy(in_file, cur_dir)

                new_value.append(os.path.join(cur_dir, in_file))

            value = new_value

        if name == 'out_file':
            for out_file in value[:3]:
                print(out_file)

                path, fname, ext = split_f(out_file)
                # out_files.append(os.path.join(path,fname + "_Nwarp" + ext))
                new_value.append(os.path.join(cur_dir, fname + "_Nwarp" + ext))

            for i in range(1, 4):
                new_value.append(os.path.join(cur_dir, "tmp_%02d.nii.gz" % i))
            value = new_value

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_file):

            if isinstance(self.inputs.out_file, list):
                print([os.path.abspath(out) for out in self.inputs.out_file])
                outputs['out_file'] = [
                    os.path.abspath(out) for out in self.inputs.out_file]
            else:
                outputs['out_file'] = os.path.abspath(self.inputs.out_file)

        return outputs
