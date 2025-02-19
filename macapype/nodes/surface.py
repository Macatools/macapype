from nipype.interfaces.base import (
    TraitedSpec, SimpleInterface, traits, File, CommandLineInputSpec)

from nipype.interfaces.afni.base import AFNICommandBase


def keep_gcc(nii_file):
    import os
    import nibabel as nib
    import numpy as np
    from nipype.utils.filemanip import split_filename as split_f

    def getLargestCC(segmentation):

        from skimage.measure import label

        labels = label(segmentation)
        print(np.unique(labels))
        assert labels.max() != 0  # assume at least 1 CC
        largestCC = labels == np.argmax(np.bincount(labels.flat)[1:])+1
        return largestCC, labels

    # nibabel (nifti -> np.array)
    img = nib.load(nii_file)
    data = img.get_fdata().astype(np.int16)
    print(data.shape)
    print(data.dtype)
    print(np.unique(data))

    # skimage GCC
    new_data, labels = getLargestCC(data)

    # nibabel (np.array -> nifti)

    path, fname, ext = split_f(nii_file)

    labels_img = nib.Nifti1Image(dataobj=labels,
                                 header=img.header,
                                 affine=img.affine)

    labels_file = os.path.abspath(fname + "_labels" + ext)

    nib.save(labels_img, labels_file)

    # nibabel (np.array -> nifti)
    new_img = nib.Nifti1Image(dataobj=new_data,
                              header=img.header,
                              affine=img.affine)

    gcc_nii_file = os.path.abspath(fname + "_gcc" + ext)

    nib.save(new_img, gcc_nii_file)

    return gcc_nii_file


def merge_tissues(dseg_file, keep_indexes):

    import os
    import nibabel as nib
    import numpy as np

    from nipype.utils.filemanip import split_filename as split_f

    print(dseg_file)

    dseg_img = nib.load(dseg_file)
    dseg_data = dseg_img.get_fdata()

    print(dseg_data.shape)
    print(dseg_data.dtype)
    print(np.unique(dseg_data))

    mask_data = np.zeros(shape=dseg_data.shape, dtype=np.int16)

    for index in keep_indexes:
        if index in np.unique(dseg_data):

            mask_data[dseg_data == index] = 1
        else:
            print("Error, could not find index {} in dseg file".format(index))

    print(np.unique(mask_data))

    mask_img = nib.Nifti1Image(dataobj=mask_data,
                               header=dseg_img.header,
                               affine=dseg_img.affine)

    path, fname, ext = split_f(dseg_file)

    mask_file = os.path.abspath(fname + "_mask" + ext)

    nib.save(mask_img, mask_file)

    return mask_file


# ### wrapping nii2mesh
def wrap_nii2mesh_old(nii_file):

    import os
    from nipype.utils.filemanip import split_filename as split_f

    path, fname, ext = split_f(nii_file)

    stl_file = os.path.abspath(fname + ".stl")

    cmd = "nii2mesh_old_gcc {} {}".format(nii_file, stl_file)

    ret = os.system(cmd)

    print(ret)

    assert ret == 0, "Error, cmd {} did not work".format(cmd)
    return stl_file


def wrap_nii2mesh(nii_file):

    import os
    from nipype.utils.filemanip import split_filename as split_f

    path, fname, ext = split_f(nii_file)

    stl_file = os.path.abspath(fname + ".stl")

    cmd = "nii2mesh {} {}".format(nii_file, stl_file)

    ret = os.system(cmd)

    print(ret)

    assert ret == 0, "Error, cmd {} did not work".format(cmd)
    return stl_file


# IsoSurface
class IsoSurfaceInputSpec(CommandLineInputSpec):

    nii_file = File(
        exists=True,
        desc='brain_file',
        mandatory=True, position=1, argstr="-input %s")

    stl_file = File(
        name_source=["nii_file"],
        name_template="%s.stl",
        desc="stl file",
        exists=True,
        keep_extension=False,
        position=2, argstr="-o %s")

    isoval = traits.Float(
        1.0,
        usedefault=True,
        desc='isoval',
        mandatory=True, argstr="-isoval %f")

    KPB = traits.Float(
        0.01,
        usedefault=True,
        desc='Smoothing ',
        requires=["NITER"],
        mandatory=True, position=-2, argstr="-Tsmooth %f")

    NITER = traits.Int(
        100,
        usedefault=True,
        desc='NITER',
        requires=["KPB"],
        mandatory=True, position=-1, argstr="%d")

    remesh = traits.Float(
        0.5, usedefault=True,
        desc='EDGE_FRACTION',
        mandatory=True, argstr="-remesh %f")

    autocrop = traits.Bool(
        True,
        desc='autocrop',
        mandatory=False, argstr="-autocrop")

    overwrite = traits.Bool(
        True,
        desc='overwrite',
        mandatory=False, argstr="-overwrite")


class IsoSurfaceOutputSpec(TraitedSpec):
    stl_file = File(
        exists=True, desc="stl file")


class IsoSurface(AFNICommandBase):
    """Description: Wrap of antsIsoSurface.sh

    Inputs:

        Mandatory:

            nii_file
                File, 'brain_file',

            stl_file:
                File, "stl file",

            isoval
                Float, 1, desc='isoval',

    ,       KPB
                Float, 0.01, 'Smoothing'

            NITER
                Int, 100 , 'NITER'

            remesh
                Float, 0.5 'EDGE_FRACTION',

        Optional:

            autocrop :
                Bool, 'autocrop',

            overwrite :
                Bool, 'overwrite'

    Outputs:

        stl_file :
            File, desc="stl file"

    """
    input_spec = IsoSurfaceInputSpec
    output_spec = IsoSurfaceOutputSpec

    _cmd = 'IsoSurface'


def split_LR_mask(LR_mask_file, left_index=1, right_index=2):

    import os

    import nibabel as nib
    import numpy as np

    from nipype.utils.filemanip import split_filename as split_f

    path, fname, ext = split_f(LR_mask_file)

    LR_mask_img = nib.load(LR_mask_file)

    LR_mask_data = LR_mask_img.get_fdata()

    # L_mask
    L_mask_data = np.zeros(shape=LR_mask_data.shape)

    L_mask_data[LR_mask_data == left_index] = 1

    L_mask_file = os.path.abspath("L_mask"+ext)

    nib.save(
        nib.Nifti1Image(L_mask_data, affine=LR_mask_img.affine,
                        header=LR_mask_img.header),
        L_mask_file)

    # R_mask
    R_mask_data = np.zeros(shape=LR_mask_data.shape)

    R_mask_data[LR_mask_data == right_index] = 1

    R_mask_file = os.path.abspath("R_mask"+ext)

    nib.save(
        nib.Nifti1Image(R_mask_data, affine=LR_mask_img.affine,
                        header=LR_mask_img.header),
        R_mask_file)

    return L_mask_file, R_mask_file


# Meshify
class MeshifyInputSpec(TraitedSpec):
    image_file = File(
        exists=True, desc='input file', mandatory=True)

    level = traits.Float(
        0.5, usedefault=True,
        desc='Threshold used to detect surfaces',
        mandatory=False)

    smoothing_iter = traits.Int(
        0, usedefault=True,
        desc='Number of Laplacian smoothing iterations',
        mandatory=False)

    smoothing_dt = traits.Float(
        0.1, usedefault=True,
        desc='dt param of the Laplacian smoothing',
        mandatory=False)


class MeshifyOutputSpec(TraitedSpec):
    mesh_file = File(desc="out file", exists=True)


class Meshify(SimpleInterface):
    """
    Definition: Create a Gifti mesh from a binary Nifti image
    """
    _cmd = 'fslorient'
    input_spec = MeshifyInputSpec
    output_spec = MeshifyOutputSpec

    def _run_interface(self, runtime):
        import os.path as op
        import nibabel.gifti as ng
        import numpy as np
        import skimage.measure as sm
        import nilearn.image as nimg

        import slam.io as sio
        import slam.differential_geometry as sdg

        from nipype.utils.filemanip import split_filename

        # Generate output mesh filename from the input image name
        _, fname, _ = split_filename(self.inputs.image_file)
        gii_file = op.abspath(op.join(runtime.cwd, fname + ".gii"))

        # Load the largest connected component of the input image
        img = nimg.largest_connected_component_img(self.inputs.image_file)

        # TODO: check if the input image is correct (binary)

        # Run the marching cube algorithm
        verts, faces, normals, values = sm.marching_cubes_lewiner(
            img.get_data(), self.inputs.level)

        # Convert vertices coordinates to image space
        # TODO: check that is correct by plotting the mesh on the image
        x, y, z = nimg.coord_transform(
            verts[:, 0], verts[:, 1], verts[:, 2], img.affine)
        mm_verts = np.array([x, y, z]).T

        # Save the mesh as Gifti
        # FIXME: FreeView can not open the mesh (but anatomist do)
        gii = ng.GiftiImage(darrays=[
            ng.GiftiDataArray(mm_verts, intent='NIFTI_INTENT_POINTSET'),
            ng.GiftiDataArray(faces, intent='NIFTI_INTENT_TRIANGLE')])
        gii.meta = ng.GiftiMetaData().from_dict({
            "volume_file": self.inputs.image_file,
            "marching_cube_level": str(self.inputs.level),
            "smoothing_iterations": str(self.inputs.smoothing_iter),
            "smoothing_dt": str(self.inputs.smoothing_dt)
        })
        ng.write(gii, gii_file)

        # Optional: Smooth the marching cube output with SLAM
        if self.inputs.smoothing_iter > 0:
            mesh = sdg.laplacian_mesh_smoothing(
                sio.load_mesh(gii_file),
                nb_iter=self.inputs.smoothing_iter,
                dt=self.inputs.smoothing_dt)
            sio.write_mesh(mesh, gii_file)

        return runtime
