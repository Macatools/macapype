def apply_binary_fill_holes_dirty(in_file, size=3):
    from scipy.ndimage import binary_fill_holes
    import nibabel as nb
    import numpy as np
    
    out_nii = in_file[:-4] + '_filled.nii'
    
    nii_image = nb.load(in_file)

    struc = np.ones((size, size, size))

    nii_data = nii_image.get_data()

    nii_data = binary_fill_holes(nii_data, struc)
    out_image = nb.Nifti1Image(nii_data.astype(int), affine=nii_image._affine)
    nb.save(out_image, out_nii)
    return out_nii
    

# """
#     Apply scipy's binary_fill_holes on 3D Nifti image
# """
#
# from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
#                                     TraitedSpec)
# from nipype.interfaces.base import traits, File
#
# from scipy.ndimage import binary_fill_holes
# import nibabel as nb
# import numpy as np
# import argparse
#
#
# class BinaryFillHolesInputSpec(CommandLineInputSpec):
#
#     in_file = File(
#         exists=True,
#         desc='3D Nifti image to fill',
#         mandatory=True, position=1, argstr="-in %s"
#     )
#
#     out_file = File(
#         None, desc='Output image',
#         mandatory=False, position=2, argstr="-out %s"
#     )
#
#     size = traits.Int(
#         3, usedefault=True, desc='Size of the filling square', position=3,
#         argstr="-size %f", mandatory=True
#     )
#
#
# class BinaryFillHolesOutputSpec(TraitedSpec):
#
#     out_file = File(
#         exists=True,
#         desc="Filled 3D Nifti image"
#     )
#
#
# class BinaryFillHoles(CommandLine):
#     """ Fill holles of the given 3D Nifti image slice by slice
#
#
#     Inputs
#     --------
#     image: File (3D Nifti)
#
#
#     Outputs
#     ---------
#     out_file: File (3D Nifti)
#         Result filled 3D Nifti image.
#
#     """
#     input_spec = BinaryFillHolesInputSpec
#     output_spec = BinaryFillHolesOutputSpec
#
#     _cmd = 'python ' + __file__
#
#     def _format_arg(self, name, spec, value):
#         import os
#
#         if name == 'out_file' and value is None:
#             out_fname = os.path.split(value)[1][:-4] + '_filled.nii'
#             value = os.path.join(os.getcwd(), out_fname)
#
#         return super(BinaryFillHoles, self)._format_arg(name, spec, value)
#
#
# def apply_binary_fill_holes(in_nii, out_nii, size=3):
#     nii_image = nb.load(in_nii)
#
#     struc = np.ones((size, size))
#
#     nii_data = nii_image.get_data()
#     nii_data = binary_fill_holes(nii_data, struc)
#
#     out_image = nb.Nifti1Image(nii_data, affine=nii_image._affine)
#     nb.save(out_image, out_nii)
#
#
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
