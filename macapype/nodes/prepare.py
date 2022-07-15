"""
copied from https://stackoverrun.com/fr/q/6768689
seems was never wrapped in nipype
"""
import os
import json

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
            nib.save(nib.Nifti1Image(avg_data, header=img_0.header,
                                     affine=img_0.affine),
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


def padding_cropped_img(cropped_img_file, orig_img_file, indiv_crop):

    import os

    import nibabel as nib
    import numpy as np

    from nipype.utils.filemanip import split_filename as split_f

    # cropping params
    crop = indiv_crop['crop_T1']['args'].split()
    print("cropping params {}".format(crop))

    xmin = int(crop[0])
    xmax = xmin + int(crop[1])

    ymin = int(crop[2])
    ymax = ymin + int(crop[3])

    zmin = int(crop[4])
    zmax = zmin + int(crop[5])

    # orig image
    orig_img = nib.load(orig_img_file)

    data_orig = orig_img.get_data()
    header_orig = orig_img.header
    affine_orig = orig_img.affine

    print("Orig img shape:", data_orig.shape)

    # cropped image
    cropped_img = nib.load(cropped_img_file)
    data_cropped = cropped_img.get_data()

    print("Cropped img shape:", data_cropped.shape)

    if len(data_orig.shape) == 3 and len(data_cropped.shape) == 4:
        print("Padding with 3D params on a 4D image")

        padded_img_data_shape = (*data_orig.shape, data_cropped.shape[3])
        print(padded_img_data_shape)

        padded_img_data = np.zeros(shape=padded_img_data_shape,
                                   dtype=data_cropped.dtype)
        print("Broscasted padded img shape:", padded_img_data_shape)

        for t in range(data_cropped.shape[3]):
            padded_img_data[xmin:xmax, ymin:ymax, zmin:zmax, t] = \
                data_cropped[:, :, :, t]

    else:

        padded_img_data = np.zeros(shape=data_orig.shape,
                                   dtype=data_cropped.dtype)
        print("Padded img shape:", padded_img_data.shape)

        padded_img_data[xmin:xmax, ymin:ymax, zmin:zmax] = data_cropped

    # saving padded image
    fpath, fname, ext = split_f(cropped_img_file)
    padded_img_file = os.path.abspath(fname + "_padded" + ext)
    img_padded_res = nib.Nifti1Image(padded_img_data, affine=affine_orig,
                                     header=header_orig)
    nib.save(img_padded_res, padded_img_file)

    return padded_img_file


def reg_aladin_dirty(reference, in_file):

    import os

    cwd = os.path.abspath("")
    os.chdir(cwd)
    out_file = os.path.abspath("outputResult.nii")
    cmd = "reg_aladin -flo {} -ref {} -res {}".format(
        in_file, reference, out_file)
    os.system(cmd)

    assert os.path.exists(out_file)
    return out_file


if __name__ == '__main__':

    data_path = "/hpc/meca/data/Macaques/Macaque_hiphop/results/ucdavis"

    orig_file = os.path.join(data_path, "sub-032139/ses-001/anat/\
                             sub-032139_ses-001_run-1_T1w.nii.gz")

    mask_file = os.path.join(
        data_path,
        "derivatives/macapype_ANTS/sub-032139/ses-001/anat/\
        sub-032139_ses-001_space-orig_desc-brain_mask.nii.gz")

    indiv_file = os.path.join(
        "/hpc/meca/users/essamlali.a/Packages",
        "indiv_params_segment_macaque_ants_based_crop.json")
    indiv = json.load(open(indiv_file))

    indiv_crop = indiv['sub-032139']['ses-001']

    res = padding_cropped_img(mask_file, orig_file, indiv_crop)

    print(res)
