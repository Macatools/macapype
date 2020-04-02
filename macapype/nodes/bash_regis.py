import os
from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    TraitedSpec, isdefined)
from nipype.interfaces.fsl.base import (FSLCommand, FSLCommandInputSpec)
from nipype.interfaces.base import traits, File


class T1xT2BETInputSpec(FSLCommandInputSpec):

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

    cog = traits.ListInt(
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
        argstr="-p %s", mandatory = False)


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

            os
                Suffix for the brain masked images (default is _BET)
            aT2
                Will coregrister T2w to T1w using flirt. Output will have the\
                    suffix provided. Will only work for spatially close images.
            opt_as
                Suffix for T2w to T1w registration (\"-in-T1w\" if not specified)
            n
                n = the number of iterations BET will be run to find center of \
                    gravity (n=1 if option -n is absent)
            m
                Will output the BET mask at the format \
                    output_prefixT1_mask.nii.gz)
            ms
                Suffix for the mask (default is _mask)
            c
                Will crop the inputs & outputs after brain extraction. c is the \
                space between the brain and the limits of the crop box expressed \
                in percentage of the brain size (eg. if the brain size is 200\
                voxels in one dimension and c=10: the sides of the brain in this \
                dimension will be 20 voxels away from the borders of the resulting\
                crop box in this dimension)
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
                Prefix for running FSL functions (can be a path or just a prefix)

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

    package_directory = os.path.dirname(os.path.abspath(__file__))
    _cmd = 'bash {}/../bash/T1xT2BET.sh'.format(package_directory)

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
                t1_fname + self.inputs.os + self.inputs.cs + ".nii.gz")
            outputs["t2_brain_file"] = os.path.abspath(
                t2_fname + self.inputs.os + self.inputs.cs + ".nii.gz")

            if self.inputs.m:
                # !!!!warning, in Regis bash, only .nii.gz are handled
                outputs["mask_file"] = os.path.abspath(
                    t1_fname + self.inputs.os + self.inputs.ms +
                    self.inputs.cs + ".nii.gz")

        else:

            outputs["t1_brain_file"] = os.path.abspath(
                t1_fname + self.inputs.os + ".nii.gz")
            outputs["t2_brain_file"] = os.path.abspath(
                t2_fname + self.inputs.os + ".nii.gz")

            if self.inputs.m:
                # !!!!warning, in Regis bash, only .nii.gz are handled
                outputs["mask_file"] = os.path.abspath(
                    t1_fname + self.inputs.os + self.inputs.ms + ".nii.gz")

        if self.inputs.aT2:
            outputs["t2_coreg_file"] = os.path.abspath(
                t2_fname + self.inputs.opt_as + ".nii.gz")

        return outputs


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
        argstr="-p %s", mandatory = False)


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
                Whole-head T2w image (use -aT2 if T2w image is not in the T1w space)

        Optional:

            os
                Suffix for the bias field corrected images (default is "_debiased")
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
                Will try to "smart" BET the anat files to get a brain mask: n =\
                    the number of iterations BET will be run to find center of gravity\
                    (default=0, will not BET if option -b has been specified).
            bs
                Suffix for the BET masked images (default is "_BET")
            f
                -f options of BET: fractional intensity threshold (0->1); \
                    default=0.5; smaller values give larger brain outline estimates
            g
                -g options of BET:\
                        vertical gradient in fractional intensity threshold (-1->1);\
                        default=0; positive values give larger brain outline at\
                        bottom, smaller at top
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
        usedefault=True, mandatory = True)

    cost = traits.Enum(
        'normmi', 'leastsq', 'labeldiff', 'bbr', 'mutualinfo', 'corratio',
        'normcorr',
        desc='FLIRT cost {mutualinfo,corratio,normcorr,normmi,leastsq,\
            labeldiff,bbr}    (default is normmi)',
        argstr='-cost %s',
        usedefault=True, mandatory = True)

    # how to assert minimal value in traits def? is now in _parse_args
    n = traits.Int(
        2, usedefault=True,
        desc='n = the number of FLIRT iterations (>=2, default=2).',
        argstr="-n %d", mandatory=True)

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
        usedefault=True, mandatory = True)

    refw_file = File(
        exists=True,
        desc='Do a whole-head non-linear registration (using FNIRT) during\
            last iteration (provide reference whole-head image)',
        mandatory=False, argstr="-refw %s")

    k = traits.Bool(
        False, usedefault=True,
        position=3, argstr="-k",
        desc="Will keep temporary files",
        mandatory=True)

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
                Prefix for running FSL functions (can be a path or just a prefix)

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
        print(outputs)
        return outputs


# CropVolume
class CropVolumeInputSpec(CommandLineInputSpec):

    # mandatory
    i_file = File(
        exists=True,
        desc='Volume to crop (you can specify as many -in as you want)',
        mandatory=True, position=0, argstr="-i %s")

    b_file = File(
        exists=True,
        desc='Brain image or brain mask, in the same space as the in-file(s)',
        mandatory=True, position=1, argstr="-b %s")

    # optional
    o = traits.String(
        desc="Prefix for the cropped image(s) (Must provide as many prefixes\
            as input images with -o, default is the base name of each input \
            image).",
        argstr="-o %s", mandatory=False)

    s = traits.String(
        "_cropped", usedefault=True,
        desc="Suffix for the cropped image(s) (default is \"_cropped\")",
        argstr="-s %s", mandatory=False)

    c = traits.Int(
        10, usedefault=True,
        desc='c is the space between the brain and the limits of\
            the crop box expressed in percentage of the brain size (eg. if the\
            brain size is 200 voxels in one dimension and c=10: the sides of\
            the brain in this dimension will be 20 voxels away from the\
            borders of the resulting crop box in this dimension). \
            Default: c=10',
        argstr="-c %d", mandatory=False)

    p = traits.String(
        desc="Prefix for running FSL functions\
            (can be a path or just a prefix)",
        argstr="-p %s", mandatory=False)


class CropVolumeOutputSpec(TraitedSpec):
    cropped_file = File(
        exists=True,
        desc="cropped image from CropVolume.sh")


class CropVolume(CommandLine):
    """
    Description:
        Crop image(s) based on a brain extraction. Multiple images can be \
        cropped at once. Will crop each volume preceeded by the -i option

    Inputs:

        Mandatory:

            i_file
                Volume to crop (you can specify as many -in as you want)
            b_file
                Brain image or brain mask, in the same space as the in-file(s)

        Optional:

            o
                Prefix for the cropped image(s) (Must provide as many prefixes\
                    as input images with -o, default is the base name of each input \
                    image).
            s
                Suffix for the cropped image(s) (default is "_cropped")
            c
                c is the space between the brain and the limits of\
                    the crop box expressed in percentage of the brain size (eg. if the\
                    brain size is 200 voxels in one dimension and c=10: the sides of\
                    the brain in this dimension will be 20 voxels away from the\
                    borders of the resulting crop box in this dimension). \
                    Default: c=10
            p
                Prefix for running FSL functions (can be a path or just a prefix)

    Outputs:

        cropped_file:

            cropped image from CropVolume.sh
    """
    input_spec = CropVolumeInputSpec
    output_spec = CropVolumeOutputSpec

    package_directory = os.path.dirname(os.path.abspath(__file__))
    _cmd = 'bash {}/../bash/CropVolume.sh'.format(package_directory)

    def _list_outputs(self):

        import os
        from nipype.utils.filemanip import split_filename as split_f

        outputs = self._outputs().get()

        path, fname, ext = split_f(self.inputs.i_file)

        outfile = fname + self.inputs.s

        if self.inputs.o:
            outfile = self.inputs.o + outfile

        outputs["cropped_file"] = os.path.abspath(outfile + ".nii.gz")
        return outputs
