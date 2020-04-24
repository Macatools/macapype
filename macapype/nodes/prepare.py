"""
copied from https://stackoverrun.com/fr/q/6768689
seems was never wrapped in nipype
"""
import os

from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec
from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    TraitedSpec, File, traits)


# FslOrient
class FslOrientInputSpec(FSLCommandInputSpec):

    main_option = traits.Str(
        desc='main option', argstr='-%s', position=0, mandatory=True)

    code = traits.Int(
        argstr='%d', desc='code for setsformcode', position=1)

    in_file = File(
        exists=True, desc='input file', argstr='%s', position=2,
        mandatory=True)


class FslOrientOutputSpec(TraitedSpec):

    out_file = File(desc="out file", exists=True)


class FslOrient(FSLCommand):
    """
    copied and adapted from https://stackoverrun.com/fr/q/6768689
    seems was never wrapped in nipype
    """
    _cmd = 'fslorient'
    input_spec = FslOrientInputSpec
    output_spec = FslOrientOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.in_file)
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
    Description: Crop image(s) based on a brain extraction. Multiple images
    can be cropped at once. Will crop each volume preceeded by the -i option

    Inputs:

        Mandatory:

            i_file
                Volume to crop (you can specify as many -in as you want)
            b_file
                Brain image or brain mask, in the same space as the in-file(s)

        Optional:

            o
                Prefix for the cropped image(s) (Must provide as many prefixes
                    as input images with -o, default is the base name of each
                    input image).
            s
                Suffix for the cropped image(s) (default is "_cropped")
            c
                c is the space between the brain and the limits of\
                    the crop box expressed in percentage of the brain size (eg.
                    if the brain size is 200 voxels in one dimension and c=10:
                    the sides of the brain in this dimension will be 20 voxels
                    away from the  borders of the resulting crop box in this
                    dimension). Default: c=10
            p
                Prefix for running FSL functions (can be a path or just a
                prefix)

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


###############################################################################
# Equivalent of flirt_average in FSL
def average_align(list_img):

    import os
    import nibabel as nib
    import numpy as np

    from nipype.utils.filemanip import split_filename as split_f
    import nipype.interfaces.fsl as fsl

    print("average_align:", list_img)

    if isinstance(list_img, list):

        assert len(list_img) > 0, "Error, list should have at least one file"

        if len(list_img) == 1:
            assert os.path.exists(list_img[0])
            av_img_file = list_img[0]
        else:

            img_0 = nib.load(list_img[0])
            path, fname, ext = split_f(list_img[0])

            list_data = [img_0.get_data()]
            for i, img in enumerate(list_img[1:]):

                print("running flirt on {}".format(img))
                flirt = fsl.FLIRT(dof=6)
                flirt.inputs.in_file = img
                flirt.inputs.reference = list_img[0]
                flirt.inputs.interp = "sinc"
                flirt.inputs.no_search = True
                out_file = flirt.run().outputs.out_file
                print(out_file)

                data = nib.load(out_file).get_data()
                list_data.append(data)

            avg_data = np.mean(np.array(list_data), axis=0)
            print(avg_data.shape)

            av_img_file = os.path.abspath("avg_" + fname + ext)
            nib.save(nib.Nifti1Image(avg_data, header=img_0.get_header(),
                                     affine=img_0.get_affine()),
                     av_img_file)

    else:
        assert os.path.exists(list_img)
        av_img_file = list_img

    return av_img_file


# on the fly
def read_cropbox(cropbox_file):

    import os.path as op

    assert op.exists(cropbox_file), \
        "Error {} do not exists".format(cropbox_file)

    with open(cropbox_file) as f:
        crop_list = []
        for line in f.readlines():
            print(line.strip().split())
            crop_list.append(tuple(map(int, map(float, line.strip().split()))))

    return crop_list
