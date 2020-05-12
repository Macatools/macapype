.. _examples:

Pipeline examples
__________________


SPM-based pipelines:
~~~~~~~~~~~~~~~~~~~~~

:ref:`Segmentation of PNH test dataset <plot_segment_pnh_spm_based>` processed with SPM-based :class:`full pipeline <macapype.pipelines.full_pipelines.create_full_segment_pnh_T1xT2>`, with the processing sequence:

* :class:`Data preparation <macapype.pipelines.prepare.create_data_preparation_pipe>`
* :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`
* :class:`IterREGBET <macapype.nodes.register.IterREGBET>`
* :class:`old_segment SPM based pipeline <macapype.pipelines.segment.create_old_segment_pipe>`

ANTS-based pipelines:
~~~~~~~~~~~~~~~~~~~~~

:ref:`Segmentation of PNH test dataset <plot_segment_pnh_ants_based>` processed with ANTS-based :class:`full pipeline <macapype.pipelines.full_pipelines.create_full_segment_pnh_subpipes>`, with the processing sequence :

* :class:`Data preparation <macapype.pipelines.prepare.create_data_preparation_pipe>`
    - Averaging multiple files from same nature
    - possibly :class:`reorientation pipeline <macapype.pipelines.prepare.create_reorient_pipeline>`
    - cropping (using :class:`T1xT2BET <macapype.nodes.extract_brain.T1xT2BET>` for cropping tool, or fslroi specifying cropbox)
    - denoising from Ants non-local mean

* :class:`Brain extraction pipeline <macapype.pipelines.full_pipelines.create_brain_extraction_pipe>`
    - :class:`debias pipeline <macapype.pipelines.correct_bias.create_correct_bias_pipe>` (similar to :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`, but all steps are nipype nodes)
    - :class:`extract brain pipeline <macapype.pipelines.correct_bias.create_correct_bias_pipe>` (using Atlax-Brex)

* :class:`Brain segment from mask <macapype.pipelines.full_pipelines.create_brain_segment_from_mask_pipe>` :
    - :class:`masked debias pipeline <macapype.pipelines.correct_bias.create_masked_correct_bias_pipe>`
    - :class:`register pipeline <macapype.pipelines.register.create_register_NMT_pipe>` from template (NMT) to subject space
    - :class:`segmentation pipeline <macapype.pipelines.segment.create_segment_atropos_pipe>` in subject space with Atropos


:ref:`Segmentation of PNH test dataset with reorientation <plot_segment_sphinx_pnh_ants_based>`, starting from a sphinx position, processed with ANTS-based :class:`full pipeline <macapype.pipelines.full_pipelines.create_full_segment_pnh_subpipes>`.

:ref:`Segmentation of marmoset test dataset <plot_segment_marmo_ants_based>`, processed using same ANTS-based :class:`full pipeline <macapype.pipelines.full_pipelines.create_full_segment_pnh_subpipes>`. The automated cropping did not work, hence manual cropping was used, cropbox has to be specified manually.
