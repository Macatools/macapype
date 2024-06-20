
from nipype.interfaces.ants.base import (ANTSCommand, ANTSCommandInputSpec)
from nipype.interfaces.base import TraitedSpec, File, traits, isdefined


class DenoiseImageInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        2,
        3,
        4,
        argstr="-d %d",
        desc="This option forces the image to be treated "
        "as a specified-dimensional image. If not "
        "specified, the program tries to infer the "
        "dimensionality from the input image.",
    )
    input_image = File(
        exists=True,
        argstr="-i %s",
        mandatory=True,
        desc="A scalar image is expected as input for noise correction.",
    )

    mask_image = File(
        exists=True,
        argstr="-x %s",
        mandatory=False,
        desc="Restriction of computation on the mask only",
    )
    noise_model = traits.Enum(
        "Gaussian",
        "Rician",
        argstr="-n %s",
        usedefault=True,
        desc=("Employ a Rician or Gaussian noise model."),
    )
    shrink_factor = traits.Int(
        default_value=1,
        usedefault=True,
        argstr="-s %s",
        desc=(
            "Running noise correction on large images can"
            " be time consuming. To lessen computation time,"
            " the input image can be resampled. The shrink"
            " factor, specified as a single integer, describes"
            " this resampling. Shrink factor = 1 is the default."
        ),
    )
    output_image = File(
        argstr="-o %s",
        name_source=["input_image"],
        hash_files=False,
        keep_extension=True,
        name_template="%s_noise_corrected",
        desc="The output consists of the noise corrected"
        " version of the input image.",
    )
    save_noise = traits.Bool(
        False,
        mandatory=True,
        usedefault=True,
        desc=("True if the estimated noise should be saved to file."),
        xor=["noise_image"],
    )
    noise_image = File(
        name_source=["input_image"],
        hash_files=False,
        keep_extension=True,
        name_template="%s_noise",
        desc="Filename for the estimated noise.",
    )
    verbose = traits.Bool(False, argstr="-v", desc=("Verbose output."))


class DenoiseImageOutputSpec(TraitedSpec):
    output_image = File(exists=True)
    noise_image = File()


class DenoiseImage(ANTSCommand):
    """
    Examples
    --------
    >>> import copy
    >>> from nipype.interfaces.ants import DenoiseImage
    >>> denoise = DenoiseImage()
    >>> denoise.inputs.dimension = 3
    >>> denoise.inputs.input_image = 'im1.nii'
    >>> denoise.cmdline
    'DenoiseImage -d 3 -i im1.nii -n Gaussian -o im1_noise_corrected.nii -s 1'

    >>> denoise_2 = copy.deepcopy(denoise)
    >>> denoise_2.inputs.output_image = 'output_corrected_image.nii.gz'
    >>> denoise_2.inputs.noise_model = 'Rician'
    >>> denoise_2.inputs.shrink_factor = 2
    >>> denoise_2.cmdline
    'DenoiseImage -d 3 -i im1.nii -n Rician
    -o output_corrected_image.nii.gz -s 2'

    >>> denoise_3 = DenoiseImage()
    >>> denoise_3.inputs.input_image = 'im1.nii'
    >>> denoise_3.inputs.save_noise = True
    >>> denoise_3.cmdline
    'DenoiseImage -i im1.nii -n Gaussian
    -o [ im1_noise_corrected.nii, im1_noise.nii ] -s 1'

    """

    input_spec = DenoiseImageInputSpec
    output_spec = DenoiseImageOutputSpec
    _cmd = "DenoiseImage"

    def _format_arg(self, name, trait_spec, value):
        if (name == "output_image") and (
            self.inputs.save_noise or isdefined(self.inputs.noise_image)
        ):
            newval = "[ {}, {} ]".format(
                self._filename_from_source("output_image"),
                self._filename_from_source("noise_image"),
            )
            return trait_spec.argstr % newval

        return super()._format_arg(name, trait_spec, value)
