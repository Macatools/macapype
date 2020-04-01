
import os

import nibabel as nb
import numpy as np

from nipype.interfaces.base import (BaseInterface, BaseInterfaceInputSpec,
                                    TraitedSpec)
from nipype.interfaces.base import traits, File
from nipype.utils.filemanip import split_filename as split_f

from scipy.ndimage import binary_fill_holes


class BinaryFillHolesInputSpec(BaseInterfaceInputSpec):

    in_file = File(
        exists=True,
        desc='3D Nifti image to fill',
        mandatory=True)

    size = traits.Int(
        3, usedefault=True,
        desc='Size of the filling square',
        mandatory=True)


class BinaryFillHolesOutputSpec(TraitedSpec):

    out_file = File(
        exists=True,
        desc="Filled 3D Nifti image"
    )


class BinaryFillHoles(BaseInterface):
    """ Fill holes of the given 3D Nifti image slice by slice

    Inputs
    --------
    image: File (3D Nifti)


    Outputs
    ---------
    out_file: File (3D Nifti)
        Result filled 3D Nifti image.

    """
    input_spec = BinaryFillHolesInputSpec
    output_spec = BinaryFillHolesOutputSpec

    def _run_interface(self, runtime):

        in_file = self.inputs.in_file
        size = self.inputs.size

        path, fname, ext = split_f(in_file)
        self.out_nii = os.path.abspath(fname + '_filled' + ext)

        nii_image = nb.load(in_file)

        struc = np.ones((size, size, size))

        nii_data = nii_image.get_data()

        nii_data = binary_fill_holes(nii_data, struc)
        out_image = nb.Nifti1Image(nii_data.astype(int),
                                   affine=nii_image._affine)
        nb.save(out_image, self.out_nii)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self.out_nii

        return outputs
