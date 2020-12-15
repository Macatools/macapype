from nipype.interfaces.base import TraitedSpec, SimpleInterface
from nipype.interfaces.base import traits, File


class MeshifyInputSpec(TraitedSpec):
    image_file = File(
        exists=True, desc='input file', mandatory=True)

    level = traits.Int(
        default=0.5, desc='Threshold used to detect surfaces',
        mandatory=False)

    smoothing_iter = traits.Int(
        default=0, desc='Number of Laplacian smoothing iterations',
        mandatory=False)

    smoothing_dt = traits.Int(
        default=0.1, desc='dt param of the Laplacian smoothing',
        mandatory=False)


class MeshifyOutputSpec(TraitedSpec):
    mesh_file = File(desc="out file", exists=True)


class Meshify(SimpleInterface):
    """ Create a Gifti mesh from a binary Nifti image """
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
        _, fname, _ = split_filename(self.input_spec.image_file)
        gii_file = op.abspath(op.join(runtime.cwd, fname + ".gii"))

        # Load the largest connected component of the input image
        img = nimg.largest_connected_component_img(self.input_spec.image_file)

        # TODO: check if the input image is correct (binary)

        # Run the marching cube algorithm
        verts, faces, normals, values = sm.marching_cubes(
            img.get_data(), self.input_spec.level)

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
            "volume_file": self.input_spec.image_file,
            "marching_cube_level": self.input_spec.level,
            "smoothing_iterations": self.input_spec.smoothing_iter,
            "smoothing_dt": self.input_spec.smoothing_dt
        })
        ng.write(gii, gii_file)

        # Optional: Smooth the marching cube output with SLAM
        if self.input_spec.smoothing_iter > 0:
            mesh = sdg.laplacian_mesh_smoothing(
                sio.load_mesh(gii_file),
                nb_iter=self.input_spec.smoothing_iter,
                dt=self.input_spec.smoothing_dt)
            sio.write_mesh(mesh, gii_file)
