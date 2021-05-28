import os

import nibabel as nb
import numpy as np

from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    TraitedSpec)
from nipype.interfaces.base import traits, File

from nipype.interfaces.base import (BaseInterface, BaseInterfaceInputSpec)
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


###############################################################################
# AtroposN4
class AtroposN4InputSpec(CommandLineInputSpec):

    dimension = traits.Int(
        3, default=True, usedefault=True,
        exists=True,
        desc='Dimension',
        mandatory=True, position=0, argstr="-d %d")

    brain_file = File(
        exists=True,
        desc='brain_file',
        mandatory=True, position=1, argstr="-a %s")

    brainmask_file = File(
        exists=True,
        desc='brainmask_file',
        mandatory=True, position=2, argstr="-x %s")

    numberOfClasses = traits.Int(
        3, usedefault=True,
        exists=True,
        desc='numberOfClasses',
        mandatory=True, position=3, argstr="-c %d")

    priors = traits.List(
        File(exists=True),
        desc='priors',
        mandatory=True)

    template_file = traits.String(
        "tmp_%02d_allineate.nii.gz", usedefault=True,
        exists=True,
        desc='template_file',
        mandatory=True, position=4, argstr="-p %s")

    out_pref = traits.String(
        "segment_", usedefault=True, desc="output prefix", mandatory=False,
        position=5,  argstr="-o %s")


class AtroposN4OutputSpec(TraitedSpec):
    segmented_file = File(
        exists=True, desc="segmented file with all tissues")

    segmented_files = traits.List(
        File(exists=True), desc="segmented indivual files")


class AtroposN4(CommandLine):
    """Description: Wrap of antsAtroposN4.sh

    Inputs:

        Mandatory:

            dimension
                Int, default=3 , 'Dimension'

            brain_file
                File, 'brain_file'

            brainmask_file
                File, 'brainmask_file'

            numberOfClasses
                Int, default=3, 'numberOfClasses'

            priors
                List of Files, 'priors'

            template_file
                String, default="tmp_%02d_allineate.nii.gz", 'template_file'

        Optional:

            out_pref:
                String, default = "segment_", "output prefix"

    Outputs:

        brain_file:
            File, "extracted brain from AtroposN4.sh"

    """
    input_spec = AtroposN4InputSpec
    output_spec = AtroposN4OutputSpec

    _cmd = 'bash antsAtroposN4.sh'

    def _format_arg(self, name, spec, value):
        import os
        import shutil

        cur_path = os.path.abspath("")

        # all the files have to be in local and
        if name == 'brain_file' or name == 'brainmask_file':
            # requires local copy
            shutil.copy(value, cur_path)
            value = os.path.split(value)[1]

        elif name == 'priors':
            new_value = []

            for prior_file in value:
                shutil.copy(prior_file, cur_path)
                new_value.append(os.path.split(prior_file)[1])

            value = new_value

        elif name == 'out_pref':

            pth, fname, ext = split_f(self.inputs.brain_file)
            value = fname+'_'
            self.inputs.out_pref = value

        return super(AtroposN4, self)._format_arg(name, spec, value)

    def _list_outputs(self):

        import os
        import glob

        outputs = self._outputs().get()

        outputs['segmented_file'] = os.path.abspath(
            self.inputs.out_pref + "Segmentation.nii.gz")

        print(self.inputs.out_pref)
        print(self.inputs.out_pref + "SegmentationPosteriors*.nii.gz")

        seg_files = glob.glob(
            self.inputs.out_pref + "SegmentationPosteriors*.nii.gz")

        print(seg_files)
        print(self.inputs.priors)

        assert len(seg_files) == len(self.inputs.priors), \
            "Error, there should {} SegmentationPosteriors ({})".format(
                len(self.inputs.priors),
                len(seg_files))

        outputs['segmented_files'] = [os.path.abspath(
            seg_file) for seg_file in seg_files]

        return outputs


def merge_masks(mask_csf_file, mask_wm_file, mask_gm_file, index_csf=1,
                index_gm=2, index_wm=3):

    import nibabel as nib
    import numpy as np
    import os.path as op

    from nipype.utils.filemanip import split_filename as split_f

    # csf (and init indexed_mask)
    path, fname, ext = split_f(mask_csf_file)

    mask_csf = nib.load(mask_csf_file)

    mask_csf_data = mask_csf.get_data()

    indexed_mask_data = np.zeros(shape=mask_csf_data.shape)

    indexed_mask_data[mask_csf_data == 1] = index_csf

    # gm
    mask_gm = nib.load(mask_gm_file)

    mask_gm_data = mask_gm.get_data()

    assert np.all(indexed_mask_data.shape == mask_gm_data.shape)

    indexed_mask_data[mask_gm_data == 1] = index_gm

    # wm
    mask_wm = nib.load(mask_wm_file)

    mask_wm_data = mask_wm.get_data()

    assert np.all(indexed_mask_data.shape == mask_wm_data.shape)

    indexed_mask_data[mask_wm_data == 1] = index_wm

    # creating indexed_mask
    indexed_mask = nib.Nifti1Image(dataobj=indexed_mask_data,
                                   affine=mask_csf.affine,
                                   header=mask_csf.header)

    # saving indexed_mask_file
    indexed_mask_file = op.abspath(fname+"_indexed_mask"+ext)

    nib.save(indexed_mask, indexed_mask_file)

    return indexed_mask_file


if __name__ == '__main__':
    # path_to = "/hpc/crise/meunier.d"
    path_to = "/hpc/crise/meunier.d/Data/Primavoice/test_pipeline_kepkee_crop"

    seg_path = os.path.join(path_to, "segment_pnh_subpipes",
                            "segment_devel_NMT_sub_align")

    brain_file = os.path.join(
        seg_path, "segment_atropos_pipe", "_session_01_subject_Apache",
        "deoblique",
        "sub-Apache_ses-01_T1w_cropped_noise_corrected_maths_masked_\
            corrected.nii.gz")

    brainmask_file = os.path.join(
        seg_path, "segment_atropos_pipe", "_session_01_subject_Apache",
        "bin_norm_intensity",
        "sub-Apache_ses-01_T1w_cropped_noise_corrected_maths_masked_\
            corrected_bin.nii.gz")

    priors = [os.path.join(
        seg_path, "register_NMT_pipe", "_session_01_subject_Apache",
        "align_seg_csf", "NMT_segmentation_CSF_allineate.nii.gz"),
              os.path.join(
                  seg_path, "register_NMT_pipe", "_session_01_subject_Apache",
                  "align_seg_gm", "NMT_segmentation_GM_allineate.nii.gz"),
              os.path.join(
                  seg_path, "register_NMT_pipe", "_session_01_subject_Apache",
                  "align_seg_wm", "NMT_segmentation_WM_allineate.nii.gz")]

    seg_at = AtroposN4()

    seg_at.inputs.brain_file = brain_file
    seg_at.inputs.brainmask_file = brainmask_file

    seg_at.inputs.priors = priors

    val = seg_at.run().outputs

    print(val)
