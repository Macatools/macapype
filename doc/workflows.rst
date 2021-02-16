:orphan:

.. _workflows:

************************
Definition of workflows
************************

SPM-based pipelines:
~~~~~~~~~~~~~~~~~~~~~

Using T1w and T2w images
************************

SPM-based :class:`full pipeline <macapype.pipelines.full_pipelines.create_full_segment_pnh_T1xT2>`, with the processing sequence:

* :class:`Data preparation <macapype.pipelines.prepare.create_data_preparation_pipe>`
* :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`
* :class:`IterREGBET <macapype.nodes.register.IterREGBET>`
* :class:`old_segment SPM based pipeline <macapype.pipelines.segment.create_old_segment_pipe>`


Unsing only a T1w image
***********************
<macapype.pipelines.full_pipelines.create_full_spm_subpipes>`, with the processing sequence:

* :class:`Data preparation <macapype.pipelines.prepare.create_data_preparation_pipe>`
* :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>` but the T1w replaces the T2w
* :class:`IterREGBET <macapype.nodes.register.IterREGBET>`
* :class:`ANTS non linear registration and FSL Apply XFM to tranform images to the template`
* :class:`old_segment SPM based pipeline <macapype.pipelines.segment.create_old_segment_pipe>`


ANTS-based pipelines:
~~~~~~~~~~~~~~~~~~~~~

ANTS-based :class:`full pipeline <macapype.pipelines.full_pipelines.create_full_segment_pnh_subpipes>`, with the processing sequence :

* :class:`Data preparation <macapype.pipelines.prepare.create_data_preparation_pipe>`
    - Averaging multiple files from same nature
    - possibly :class:`reorientation pipeline <macapype.pipelines.prepare.create_reorient_pipeline>`
    - cropping (using :class:`T1xT2BET <macapype.nodes.extract_brain.T1xT2BET>` for cropping tool, or fslroi specifying cropbox)
    - denoising from Ants non-local mean

* :class:`Brain extraction pipeline <macapype.pipelines.full_pipelines.create_brain_extraction_pipe>`
    - :class:`debias pipeline <macapype.pipelines.correct_bias.create_correct_bias_pipe>` (similar to :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`, but all steps are nipype nodes)
    - :class:`extract brain pipeline <macapype.pipelines.macapype.pipelines.extract_brain.create_extract_pipe>` (using Atlax-Brex)

* :class:`Brain segment from mask <macapype.pipelines.full_pipelines.create_brain_segment_from_mask_pipe>` :
    - :class:`masked debias pipeline <macapype.pipelines.correct_bias.create_masked_correct_bias_pipe>`
    - :class:`register pipeline <macapype.pipelines.register.create_register_NMT_pipe>` from template (NMT) to subject space
    - :class:`segmentation pipeline <macapype.pipelines.segment.create_segment_atropos_pipe>` in subject space with Atropos


********************
How to run workflows
********************

Following the BIDS format
=========================

To run the pipeline over a full BIDS dataset:

.. code:: bash

    $ python workflows/segment_pnh_spm_based.py -data ~/Data_maca -out ./local_test

To specify with subjects/sessions you want to run the pipeline on:

.. code:: bash

    $ python workflows/segment_pnh -data ~/Data_maca -out ./local_test -soft SPM -sub Elouk -ses 01
    $ python workflows/segment_pnh -data ~/Data_maca -out ./local_test -soft SPM -sub Elouk

You can also specify a json file containing the parameters of your analysis

.. code:: bash

    $ python workflows/segment_pnh.py -data ~/Data_maca -out ./local_test -soft SPM -params params.json

Here is an example of the params.json corresponding to :class:`segment_pnh_spm_based pipeline <macapype.pipelines.full_segment.create_full_segment_pnh_T1xT2>`:

.. include:: ../workflows/params_segment_pnh_spm_based.json
   :literal:


Indiv params:
=============

Adding -indiv
*************

You can also include indiv_params.json, for specifiying parameters specific parameters:


.. code:: bash

    $ python workflows/segment_pnh.py -data ~/Data_maca -out ./local_test -soft SPM -params params.json -indiv indiv_params.json

List of indiv params:
*********************

Data preparation (ANTS, ANTS_T1, SPM, SPM_T1):

- "crop" (args) in short_data_preparation, long_single_preparation and long_multi_preparation
- "denoise", "denoise_first" (see `Denoise <https://nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.interfaces.ants.segmentation.html#denoiseimage>`_ for arguments) for long_single_preparation and long_multi_preparation
- "norm_intensity" (see `N4BiasFieldCorrection<https://nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.interfaces.ants.segmentation.html#n4biasfieldcorrection>` for arguments) for long_single_preparation and long_multi_preparation

SPM based pipeline (SPM and SPM_T1):
- "reg" (see :class:`IterREGBET <macapype.nodes.register.IterREGBET>` for arguments)
- "debias" (see :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>` for arguments)

Old segment (SPM and SPM_T1):
- "threshold_gm", "threshold_wm", "threshold_csf" (thresh)

nii_to_mesh_fs_pipe (SPM):
- "fill_wm" (args)

Brain extraction (ANTS and ANTS_T1):
- "atlas_brex" (see :class:`AtlasBREX <macapype.nodes.extract_brain.AtlasBREX>` for arguments)

Brain segmentation (ANTS and ANTS_T1):
- "norm_intensity "(will be the same args as in Data preparation)
