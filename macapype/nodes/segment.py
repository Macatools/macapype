
#def wrap_antsAtroposN4_dirty(dimension, brain_file, brainmask_file,
                             #numberOfClasses, ex_prior1, ex_prior2, ex_prior3):

    #import os
    #import shutil
    #from nipype.utils.filemanip import split_filename as split_f

    #_, prior_fname, prior_ext = split_f(ex_prior1)  # last element

    ## copying file locally
    #dest = os.path.abspath("")

    #shutil.copy(ex_prior1, dest)
    #shutil.copy(ex_prior2, dest)
    #shutil.copy(ex_prior3, dest)

    #shutil.copy(brain_file, dest)
    #shutil.copy(brainmask_file, dest)

    #_, bmask_fname, bmask_ext = split_f(brainmask_file)
    #_, brain_fname, brain_ext = split_f(brain_file)

    ## generating template_file
    ## TODO should be used by default
    #template_file = "tmp_%02d_allineate.nii.gz"

    ## generating bash_line
    #os.chdir(dest)


    #print(dimension)
    #print( brain_fname+brain_ext)
    #print(bmask_fname+bmask_ext)
    #print(numberOfClasses)
    #print( template_file)

    #out_pref = "segment_"
    #bash_line = "bash antsAtroposN4.sh -d {} -a {} -x {} -c {} -p {} -o {}".format(#noqa
        #dimension, brain_fname+brain_ext, bmask_fname+bmask_ext,
        #numberOfClasses, template_file, out_pref)
    #print("bash_line : "+bash_line)

    #os.system(bash_line)

    #seg_file = os.path.abspath(out_pref+"Segmentation"+prior_ext)
    #seg_post1_file = os.path.abspath(
        #out_pref+"SegmentationPosteriors01"+prior_ext)
    #seg_post2_file = os.path.abspath(
        #out_pref+"SegmentationPosteriors02"+prior_ext)
    #seg_post3_file = os.path.abspath(
        #out_pref+"SegmentationPosteriors03"+prior_ext)

    #out_files = [seg_file, seg_post1_file, seg_post2_file, seg_post3_file]

    ## TODO surely more robust way can be used
    #return out_files, seg_file, seg_post1_file, seg_post2_file, seg_post3_file

import os
from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    TraitedSpec, isdefined)
#from nipype.interfaces.fsl.base import (FSLCommand, FSLCommandInputSpec)
from nipype.interfaces.base import traits, File


class AtroposInputSpec(CommandLineInputSpec):

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
        desc='brain_file',
        mandatory=True, position=2, argstr="-x %s")

    numberOfClasses = traits.Int(
        3, usedefault=True,
        exists=True,
        desc='numberOfClasses',
        mandatory=True, position=3, argstr="-c %d")

    priors = traits.List(
        File(exists = True),
        desc='priors',
        mandatory=True)

    template_file = File(
        "tmp_%02d_allineate.nii.gz", usedefault = True
        exists=True,
        desc='template_file',
        mandatory=True, position=4, argstr="-p %s")

    out_pref = traits.String("segment_",true usedefault=True,
        desc="output prefix",
        mandatory=False, position = 5,  argstr="-o %s")


class AtroposOutputSpec(CommandLine):
    segemented_file = File(
        exists=True, desc="segemented_file")

    segemented_files = traits.List(
        File(exists = True), desc="segmented indivual files")


class Atropos(FSLCommand):
    """
    Description:
        Brain extraction using T1 and T2 images


    Inputs:

    Outputs:

        brain_file:
            type = File, exists=True, desc="extracted brain from Atropos.sh"

    """
    input_spec = AtroposInputSpec
    output_spec = AtroposOutputSpec

    package_directory = os.path.dirname(os.path.abspath(__file__))
    _cmd = 'bash antsAtroposN4.sh'.format(package_directory)

    def _format_arg(self, name, spec, value):
            import os
            import shutil

            cur_path = os.path.abspath("")

            #os.chdir(cur_path)
            # all the files have to be in local and
            if name == 'brain_file' or name == 'brainmask_file':
                ## requires local copy
                shutil.copy(value, cur_path)
                new_value = os.path.split(value)[1]

                #return spec.argstr%{"old":0, "standard":1, "new":2}[value]
            elif name == 'priors':
                new_value = []

                for prior_file in value:
                    shutil.copy(prior_file, cur_path)
                    new_value.append(os.path.split(prior_file)[1])

            return super(Atropos, self)._format_arg(name, spec, new_value)

    def _list_outputs(self):

        import os
        from nipype.utils.filemanip import split_filename as split_f

        outputs = self._outputs().get()

        t1_path, t1_fname, ext = split_f(self.inputs.t1_file)
        t2_path, t2_fname, ext = split_f(self.inputs.t2_file)


        return outputs

if __name__ == '__main__':

    path_to = "/hpc/crise/meunier.d"

    seg_path = os.path.join(path_to, "segment_pnh_subpipes", "segment_devel_NMT_sub_align")

    brain_file = os.path.join(
        seg_path, "segment_atropos_pipe", "_session_01_subject_Apache", "deoblique",
        "sub-Apache_ses-01_T1w_cropped_noise_corrected_maths_masked_corrected.nii.gz")

    brainmask_file = os.path.join(
        seg_path, "segment_atropos_pipe", "_session_01_subject_Apache", "bin_norm_intensity",
        "sub-Apache_ses-01_T1w_cropped_noise_corrected_maths_masked_corrected_bin.nii.gz")

    priors = [os.path.join(seg_path, "register_NMT_pipe", "_session_01_subject_Apache", "align_seg_csf", "NMT_segmentation_CSF_allineate.nii.gz",
              os.path.join(seg_path, "register_NMT_pipe", "_session_01_subject_Apache", "align_seg_gm", "NMT_segmentation_GM_allineate.nii.gz",
              os.path.join(seg_path, "register_NMT_pipe", "_session_01_subject_Apache", "align_seg_wm", "NMT_segmentation_WM_allineate.nii.gz"]

    seg_at = Atropos()

    seg_at.inputs.brain_file = brain_file
    seg_at.inputs.brainmask_file = brainmask_file

    seg_at.inputs.priors = priors

    val = seg_at.run().outputs

    print(val)
