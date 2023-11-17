from nipype.interfaces.base import TraitedSpec, SimpleInterface
from nipype.interfaces.base import traits, File


def keep_gcc(nii_file):

    import os
    import nibabel as nib
    import numpy as np

    from nipype.utils.filemanip import split_filename as split_f

    def getLargestCC(segmentation):

        from skimage.measure import label

        labels = label(segmentation)
        assert labels.max() != 0  # assume at least 1 CC
        largestCC = labels == np.argmax(np.bincount(labels.flat)[1:])+1
        return largestCC

    # nibabel (nifti -> np.array)
    img = nib.load(nii_file)
    data = img.get_fdata().astype("int32")
    print(data.shape)

    # numpy
    data[data > 0] = 1
    binary = np.array(data, dtype="bool")

    # skimage

    # skimage GCC
    new_data = getLargestCC(binary)

    # nibabel (np.array -> nifti)
    new_img = nib.Nifti1Image(dataobj=new_data,
                              header=img.header,
                              affine=img.affine)

    path, fname, ext = split_f(nii_file)

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

    mask_data = np.zeros(shape=dseg_data.shape)

    for index in keep_indexes:
        if index in np.unique(dseg_data):

            mask_data[dseg_data == index] = 1
        else:
            print("Error, could not find index {} in dseg file".format(index))

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


# ### wrapping afni IsoSurface
def wrap_afni_IsoSurface(nii_file):

    import os
    from nipype.utils.filemanip import split_filename as split_f

    path, fname, ext = split_f(nii_file)

    stl_file = os.path.abspath(fname + ".stl")

    # parameters
    isoval = 1
    remesh = 0.5

    # Tsmooth
    KPB = 0.1
    NITER = 100

    # remesh
    remesh = 0.5

    # options
    overwrite = True
    autocrop = True

    # command
    cmd = "IsoSurface"
    cmd += " -isoval {}".format(isoval)
    cmd += " -input {}".format(nii_file)
    cmd += " -Tsmooth {} {}".format(KPB, NITER)
    cmd += " -remesh {}".format(remesh)
    if overwrite:
        cmd += " -overwrite"
    if autocrop:
        cmd += " -autocrop"
    cmd += " -o {}".format(stl_file)

    print(cmd)

    ret = os.system(cmd)

    print(ret)

    assert ret == 0, "Error, cmd {} did not work".format(cmd)
    return stl_file


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
