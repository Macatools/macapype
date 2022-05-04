pass

"""
import macapype.nodes.surface as surf
import numpy as np
import nibabel as nb
import os


def test_meshify():
    # Create a temporary test image
    print("Generate fake Nifti image")
    dt = np.zeros((100, 60, 100))
    dt[40:60, 20:40, 20:50] = 1
    affine = np.eye(4)

    tmp_file = "./test_meshify_input_image.nii"
    nb.save(nb.Nifti1Image(dt, affine), tmp_file)

    try:
        # Test the node
        print("Create Meshify node")
        meshify = surf.Meshify()
        meshify.inputs.image_file = tmp_file
        print("Run Meshify node")
        meshify.run()

        print("Assert output")
        assert os.path.exists(tmp_file[:-4] + ".gii")
        pass
    finally:
        print("Remove temporary data")
        os.remove(tmp_file)
        os.remove(tmp_file[:-4] + ".gii")

"""
