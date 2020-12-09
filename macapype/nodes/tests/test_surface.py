import macapype.nodes.surface as surf
import numpy as np
import nibabel as nb
import os


def test_meshify():
    # Create a temporary test image
    dt = np.zeros((100, 60, 100))
    dt[40:60, 20:40, 20:50] = 1
    tmp_file = "/tmp/macapype/test_meshify_input_image.nii"
    nb.save(nb.Nifti1Image(dt), tmp_file)

    # Test the node
    meshify = surf.Meshify
    meshify.input_spec.image_input = tmp_file
    meshify.run()

    assert os.path.exists(tmp_file[:-4] + ".gii")

    os.remove(tmp_file)
    pass
