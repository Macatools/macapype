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


# IterREGBET
class IterREGBETInputSpec(CommandLineInputSpec):

    # mandatory
    inw_file = File(
        exists=True,
        desc='Moving Whole-head image',
        mandatory=True, position=0, argstr="-inw %s")

    inb_file = File(
        exists=True,
        desc='Moving brain image',
        mandatory=True, position=1, argstr="-inb %s")

    refb_file = File(
        exists=True,
        desc='Fixed reference brain image',
        mandatory=True, position=2, argstr="-refb %s")

    # optional
    xp = traits.String(
        genfile=True,
        desc="Prefix for the registration outputs (\"in_FLIRT-to_ref\" if not \
            specified)",
        position=3, argstr="-xp %s", mandatory=False)

    bs = traits.String(
        "_IRbrain", usedefault=True,
        desc="Suffix for the brain files (\"in_IRbrain\" & \"in_IRbrain_mask\"\
            if not specified)",
        position=3, argstr="-bs %s", mandatory=False)

    dof = traits.Enum(
        12, 6, 7, desc='FLIRT degrees of freedom (6=rigid body, 7=scale, \
            12=affine (default)). Use dof 6 for intra-subject, 12 for \
            inter-subject registration',
        argstr='-dof %d',
        usedefault=True, mandatory=True)

    cost = traits.Enum(
        'normmi', 'leastsq', 'labeldiff', 'bbr', 'mutualinfo', 'corratio',
        'normcorr',
        desc='FLIRT cost {mutualinfo,corratio,normcorr,normmi,leastsq,\
            labeldiff,bbr}    (default is normmi)',
        argstr='-cost %s',
        usedefault=True, mandatory=False)

    # how to assert minimal value in traits def? is now in _parse_args
    n = traits.Int(
        2, usedefault=True,
        desc='n = the number of FLIRT iterations (>=2, default=2).',
        argstr="-n %d", mandatory=False)

    m = traits.Enum(
        'ref', 'union', 'inter', 'mix',
        desc='At each new iteration, either use:\
            - the reference brain mask, m=ref (default)\
            - the union of the reference and input brain masks, \
            m=union (use if your input brain is too small)\
            - the intersection of the reference and input brain masks, m=inter\
            (use if your input brain is too big)\
            - a mix between union & intersection, m=mix (give it a try!)',
        argstr='-m %s',
        usedefault=True, mandatory=False)

    refw_file = File(
        exists=True,
        desc='Do a whole-head non-linear registration (using FNIRT) during\
            last iteration (provide reference whole-head image)',
        mandatory=False, argstr="-refw %s")

    k = traits.Bool(
        False, usedefault=True,
        position=3, argstr="-k",
        desc="Will keep temporary files",
        mandatory=False)

    p = traits.String(
        desc="Prefix for running FSL functions\
            (can be a path or just a prefix)",
        position=3, argstr="-p %s")


class IterREGBETOutputSpec(TraitedSpec):
    brain_file = File(
        exists=True,
        desc="brain from IterREGBET.sh")

    brain_mask_file = File(
        exists=True,
        desc="masked brain from IterREGBET.sh")

    warp_file = File(
        exists=True,
        desc="warped image from IterREGBET.sh")

    transfo_file = File(
            exists=True,
            desc="transfo_file")

    inv_transfo_file = File(
            exists=True,
            desc="inv_transfo_file")


class IterREGBET(CommandLine):
    """
    Description: Iterative registration of the in-file to the ref file (
    registered brain mask of the ref image is used at each iteration). To use
    when the input brain mask is not optimal (eg. an output of FSL BET).
    Will output a better brain mask of the in-file.

    Inputs:

        Mandatory:

            inw_file
                Moving Whole-head image
            inb_file
                Moving brain image
            refb_file
                Fixed reference brain image

        Optional:

            xp
                Prefix for the registration outputs ("in_FLIRT-to_ref" if not
                specified)
            bs
                Suffix for the brain files ("in_IRbrain" & "in_IRbrain_mask"
                if not specified)
            dof
                FLIRT degrees of freedom (6=rigid body, 7=scale,
                12=affine (default)). Use dof 6 for intra-subject, 12 for
                inter-subject registration
            cost
                FLIRT cost {mutualinfo,corratio,normcorr,normmi,leastsq,\
                labeldiff,bbr}    (default is normmi)
            n
                n = the number of FLIRT iterations (>=2, default=2)
            m
                At each new iteration, either use:

                - the reference brain mask, m=ref (default)
                - the union of the reference and input brain masks, m=union \
                (use if your input brain is too small)
                - the intersection of the reference and input brain masks, \
                m=inter (use if your input brain is too big)
                - a mix between union & intersection, m=mix (give it a try!)
            refw_file
                Do a whole-head non-linear registration (using FNIRT) during
                last iteration (provide reference whole-head image)
            k
                Will keep temporary files
            p
                Prefix for running FSL functions (can be a path or just a
                prefix)

    Outputs:

        brain_file
            brain from IterREGBET.sh
        brain_mask_file
            masked brain from IterREGBET.sh
        warp_file
            warped image from IterREGBET.sh
        transfo_file
            transfo_file
        inv_transfo_file
            inv_transfo_file
    """
    input_spec = IterREGBETInputSpec
    output_spec = IterREGBETOutputSpec

    package_directory = os.path.dirname(os.path.abspath(__file__))
    _cmd = 'bash {}/../bash/IterREGBET.sh'.format(package_directory)

    def _gen_filename(self, name):
        if name == "xp":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        from nipype.utils.filemanip import split_filename as split_f

        _, in_brain, _ = split_f(self.inputs.inb_file)
        _, ref, _ = split_f(self.inputs.refb_file)

        if isdefined(self.inputs.xp):
            outname = self.inputs.xp
        else:
            outname = in_brain + "_FLIRT-to_" + ref
        return outname

    def _list_outputs(self):

        import os
        from nipype.utils.filemanip import split_filename as split_f

        outputs = self._outputs().get()

        path, fname, ext = split_f(self.inputs.inw_file)

        outputs["brain_file"] = os.path.abspath(
            fname + self.inputs.bs + ".nii.gz")
        outputs["brain_mask_file"] = os.path.abspath(
            fname + self.inputs.bs + "_mask.nii.gz")

        if isdefined(self.inputs.xp):
            outfile = self.inputs.xp
        else:
            outfile = self._gen_outfilename()

        outputs["warp_file"] = os.path.abspath(outfile + ".nii.gz")
        outputs["transfo_file"] = os.path.abspath(outfile + ".xfm")
        outputs["inv_transfo_file"] = os.path.abspath(outfile + "_inverse.xfm")
        return outputs


# NMTSubjectAlign
class NMTSubjectAlignInputSpec(CommandLineInputSpec):

    T1_file = File(
        exists=True,
        desc='Target file',
        mandatory=True, position=0, argstr="%s")

    NMT_SS_file = File(
        exists=True,
        desc='Align to T1',
        mandatory=True, position=1, argstr="%s")


class NMTSubjectAlignOutputSpec(TraitedSpec):

    aff_file = File(
        exists=True,
        desc="shft_aff")

    warp_file = File(
        exists=True,
        desc="shft_WARP.nii.gz")

    warpinv_file = File(
        exists=True,
        desc="shft_WARPINV.nii.gz")

    transfo_file = File(
        exists=True,
        desc="composite_linear_to_NMT.1D")

    inv_transfo_file = File(
        exists=True,
        desc="_composite_linear_to_NMT_inv.1D")


class NMTSubjectAlign(CommandLine):
    """
    Description: Align NMT subject to template (NMT 1.2)

    Inputs:

        Mandatory:

            T1_file:
                File, 'Target file'

            NMT_SS_file:
                File, 'Align to T1'


    Outputs:

        aff_file:
            File, "aff"

        warp_file:
            File, "shft_WARP"

        warpinv_file:
            File, "shft_WARPINV"

        transfo_file:
            File, "composite_linear_to_NMT"

        inv_transfo_file:
            File, "_composite_linear_to_NMT_inv"


    """
    input_spec = NMTSubjectAlignInputSpec
    output_spec = NMTSubjectAlignOutputSpec

    package_directory = os.path.dirname(os.path.abspath(__file__))
    _cmd = 'tcsh -x {}/../bash/NMT_subject_align.csh'.format(package_directory)

    def _list_outputs(self):

        from nipype.utils.filemanip import split_filename as split_f

        outputs = self._outputs().get()

        path, fname, ext = split_f(self.inputs.T1_file)

        outputs["aff_file"] = os.path.abspath(fname + "_shft_aff" + ext)

        # TODO will require some checks
        # outputs["warpinv_file"] = os.path.abspath(
        # fname + "_shft_WARPINV.nii")
        outputs["warpinv_file"] = os.path.abspath(
            fname + "_shft_WARPINV.nii.gz")

        outputs["warp_file"] = os.path.abspath(
            fname + "_shft_WARP.nii.gz")

        # outputs["warpinv_file"] = os.path.abspath(
        #    fname + "_shft_WARPINV" + ext)

        outputs["transfo_file"] = os.path.abspath(
            fname + "_composite_linear_to_NMT.1D")
        outputs["inv_transfo_file"] = os.path.abspath(
            fname + "_composite_linear_to_NMT_inv.1D")

        return outputs


# NMTSubjectAlign2
class NMTSubjectAlign2InputSpec(CommandLineInputSpec):

    T1_file = File(
        exists=True,
        desc='Target file',
        mandatory=True, position=0, argstr="-i %s")

    NMT_SS_file = File(
        exists=True,
        desc='Align to T1',
        mandatory=True, position=1, argstr="-r %s")


class NMTSubjectAlign2OutputSpec(TraitedSpec):

    aff_file = File(
        exists=True,
        desc="affine (subject image linearly transformed to the NMT template)")

    warp_file = File(
        exists=True,
        desc="WARP.nii.gz")

    warpinv_file = File(
        exists=True,
        desc="WARPINV.nii.gz")

    transfo_file = File(
        exists=True,
        desc="Combined Linear transform from subject to NMT)")

    inv_transfo_file = File(
        exists=True,
        desc="Inverse Linear Transform from NMT to subject")


class NMTSubjectAlign2(CommandLine):
    """
    Description: Align NMT subject to template (NMT 1.3)

    Inputs:

        Mandatory:

            T1_file:
                File, 'Target file'

            NMT_SS_file:
                File, 'Align to T1'

    Outputs:

        aff_file:
            File, "subject image linearly transformed to the NMT template"

        warp_file:
            File, "shft_WARP"

        warpinv_file:
            File, "shft_WARPINV"

        transfo_file:
            File, "Combined Linear transform from subject to NMT"

        inv_transfo_file:
            File, "Inverse Linear Transform from NMT to subject"
    """
    input_spec = NMTSubjectAlign2InputSpec
    output_spec = NMTSubjectAlign2OutputSpec

    package_directory = os.path.dirname(os.path.abspath(__file__))
    _cmd = 'bash {}/../bash/NMT_subject_align'.format(package_directory)

    def _list_outputs(self):

        from nipype.utils.filemanip import split_filename as split_f

        outputs = self._outputs().get()

        path, fname, ext = split_f(self.inputs.T1_file)

        outputs["aff_file"] = os.path.abspath(fname + "_affine" + ext)

        # TODO will require some checks
        # outputs["warpinv_file"] = os.path.abspath(
        # fname + "_shft_WARPINV.nii")
        outputs["warpinv_file"] = os.path.abspath(
            fname + "_WARPINV.nii.gz")

        outputs["warp_file"] = os.path.abspath(
            fname + "_WARP.nii.gz")

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
            if isinstance(value, list):

                print("A list for in_file")
                for in_file in value:
                    print(in_file)

                    # copy en local
                    shutil.copy(in_file, cur_dir)

                    new_value.append(os.path.join(cur_dir, in_file))

            else:
                print("Not a list for in_file {}".format(value))
                shutil.copy(value, cur_dir)

                path, fname, ext = split_f(value)
                new_value = os.path.join(cur_dir, fname + ext)
                print(new_value)

            value = new_value

        elif name == 'out_file':
            if isinstance(value, list):
                print("A list for out_file")
                for out_file in value[:1]:
                    print(out_file)

                    path, fname, ext = split_f(out_file)
                    new_value.append(os.path.join(cur_dir,
                                                  fname + "_Nwarp" + ext))

                for i in range(1, 4):
                    new_value.append(os.path.join(cur_dir,
                                                  "tmp_%02d.nii.gz" % i))
            else:
                print("Not a list for out_file {}".format(value))

                path, fname, ext = split_f(value)
                new_value = os.path.abspath(fname + "_Nwarp" + ext)
                print(new_value)

            value = new_value

        return super(NwarpApplyPriors, self)._format_arg(name, spec, value)

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
