#def apply_binary_fill_holes_dirty(in_file, size=3):
    #from scipy.ndimage import binary_fill_holes
    #import nibabel as nb
    #import numpy as np
    #import os

    #from nipype.utils.filemanip import split_filename as split_f

    #path, fname, ext = split_f(in_file)

    #out_nii = os.path.abspath(fname + '_filled.' + ext)

    #nii_image = nb.load(in_file)

    #struc = np.ones((size, size, size))

    #nii_data = nii_image.get_data()

    #nii_data = binary_fill_holes(nii_data, struc)
    #out_image = nb.Nifti1Image(nii_data.astype(int), affine=nii_image._affine)
    #nb.save(out_image, out_nii)
    #return out_nii


"""
    Apply scipy's binary_fill_holes on 3D Nifti image
"""

from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    TraitedSpec)
from nipype.interfaces.base import traits, File

from scipy.ndimage import binary_fill_holes
import nibabel as nb
import numpy as np
import argparse


class BinaryFillHolesInputSpec(CommandLineInputSpec):

    in_file = File(
        exists=True,
        desc='3D Nifti image to fill',
        mandatory=True)

    size = traits.Int(
        3, usedefault=True,
        desc='Size of the filling square',
        mandatory=True)
    )

class BinaryFillHolesOutputSpec(TraitedSpec):

    out_file = File(
        exists=True,
        desc="Filled 3D Nifti image"
    )


class BinaryFillHoles(CommandLine):
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

        from scipy.ndimage import binary_fill_holes
        import nibabel as nb
        import numpy as np
        import os

        from nipype.utils.filemanip import split_filename as split_f

        in_file = self.inputs.in_file
        size = self.inputs.size

        path, fname, ext = split_f(in_file)
        self.out_nii = os.path.abspath(fname + '_filled.' + ext)

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
        outputs["outfile"] = self.out_nii

        return outputs

# if __name__ == "__main__":
#     # Command line parser
#     parser = argparse.ArgumentParser(
#         description="Apply scipy's binary_fill_holes on 3D Nifti image")
#     parser.add_argument("-in", dest="in_image", type=str,
#                         help="Image to process", required=True)
#     parser.add_argument("-out", dest="out_image", type=str,
#                         help="Out image", default=None)
#     parser.add_argument("-size", dest="size", type=str,
#                         help="Size of the structure (in voxels)", default=3)
#     args = parser.parse_args()
#
#     # Default output filename
#     if args.out_image is None:
#         args.out_image = args.in_image[:-4] + "_filled.nii"
#
#     # Work
#     apply_binary_fill_holes(args.in_image, args.out_image, args.size)
