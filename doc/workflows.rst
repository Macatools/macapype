:orphan:

.. _workflows:

************************
Definition of workflows
************************

SPM-based pipelines:
~~~~~~~~~~~~~~~~~~~~~

SPM-based :class:`full pipeline <macapype.pipelines.full_pipelines.create_full_segment_pnh_T1xT2>`, with the processing sequence:

* :class:`Data preparation <macapype.pipelines.prepare.create_data_preparation_pipe>`
* :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`
* :class:`IterREGBET <macapype.nodes.register.IterREGBET>`
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
    - :class:`extract brain pipeline <macapype.pipelines.correct_bias.create_correct_bias_pipe>` (using Atlax-Brex)

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

    $ python workflows/segment_pnh -data ~/Data_maca -out ./local_test -soft SPM -subjects Elouk -sess 01
    $ python workflows/segment_pnh -data ~/Data_maca -out ./local_test -soft SPM -subjects Elouk

You can also specify a json file containing the parameters of your analysis

.. code:: bash

    $ python workflows/segment_pnh.py -data ~/Data_maca -out ./local_test -soft SPM -params params.json

Here is an example of the params.json corresponding to :class:`segment_pnh_spm_based pipeline <macapype.pipelines.full_segment.create_full_segment_pnh_T1xT2>`:

.. include:: ../workflows/params_segment_pnh_spm_based.json
   :literal:

You can also include multi_params.json, for specifiying parameters specific parameters:


.. code:: bash

    $ python workflows/segment_pnh.py -data ~/Data_maca -out ./local_test -soft SPM -params params.json -multi_params multi_params.json
