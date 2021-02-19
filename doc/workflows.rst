:orphan:

.. _workflows:

************************
Definition of workflows
************************

SPM-based pipelines:
~~~~~~~~~~~~~~~~~~~~~

Using T1w and T2w images
************************

:class:`full SPM pipeline <macapype.pipelines.full_pipelines.create_full_spm_subpipes>`, with the processing sequence:

* :class:`Data preparation <macapype.pipelines.prepare.create_short_preparation_pipe.>`
* :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`
* :class:`IterREGBET <macapype.nodes.register.IterREGBET>`
* :class:`old_segment SPM based pipeline <macapype.pipelines.segment.create_old_segment_pipe>`


Using only a T1w image
***********************
:class:`full SPM T1 pipeline <macapype.pipelines.full_pipelines.create_full_spm_T1_subpipes>`, with the processing sequence:

* :class:`Data preparation <macapype.pipelines.prepare.create_short_preparation_pipe.>`
* :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>` but the T1w replaces the T2w
* :class:`IterREGBET <macapype.nodes.register.IterREGBET>`
* :class:`ANTS non linear registration and FSL Apply XFM to tranform images to the template`
* :class:`old_segment SPM based pipeline <macapype.pipelines.segment.create_old_segment_pipe>`


ANTS-based pipelines:
~~~~~~~~~~~~~~~~~~~~~

Using T1w and T2w images
************************

:class:`full ANTS pipeline <macapype.pipelines.full_pipelines.create_full_ants_subpipes>`, with the processing sequence :

* :class:`Short data preparation <macapype.pipelines.prepare.create_short_preparation_pipe>` or :class:`Long single data preparation <macapype.pipelines.prepare.create_long_single_preparation_pipe>` or :class:`Long multi data preparation <macapype.pipelines.prepare.create_long_multi_preparation_pipe>`

(See :ref:`Pipelines <pipelines>` for more details)

* :class:`Brain extraction pipeline <macapype.pipelines.full_pipelines.create_brain_extraction_pipe>`
    - :class:`debias pipeline <macapype.pipelines.correct_bias.create_correct_bias_pipe>` (similar to :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`, but all steps are nipype nodes)
    - :class:`extract brain pipeline <macapype.pipelines.macapype.pipelines.extract_brain.create_extract_pipe>` (using Atlax-Brex)

* :class:`Brain segment from mask <macapype.pipelines.full_pipelines.create_brain_segment_from_mask_pipe>` :
    - :class:`masked debias pipeline <macapype.pipelines.correct_bias.create_masked_correct_bias_pipe>`
    - :class:`register pipeline <macapype.pipelines.register.create_register_NMT_pipe>` from template (NMT) to subject space
    - :class:`segmentation pipeline <macapype.pipelines.segment.create_segment_atropos_pipe>` in subject space with Atropos

Using only T1w images
************************

:class:`full ANTS T1 pipeline <macapype.pipelines.full_pipelines.create_full_ants_T1_subpipes>`, with the processing sequence :


********************
How to run workflows
********************

* the main file is located in workflows and is called segment_pnh.py and should be called like a python script:

.. code:: bash

    $ python workflows/segment_pnh.py

* all the data have to be in BIDS format to run properly (see `BIDS specification <https://bids-specification.readthedocs.io/en/stable/index.html>`_ for more details)

* the following parameters are mandatory:

    * -data is the path to your data dataset (existing BIDS format directory)

    * -out is the path to the output results (an existing path)

    * -soft can be one of these : SPM or ANTS

        * with _T1 at the end if only T1w (and not T2w) are available

        * with _test to see if the full pipeline is coherent (will only generate the graph.dot and graph.png)

    * -params: a json file specifiying the global parameters of the analysis. See :ref:`Parameters <params>` for more details

.. code:: bash

    $ python workflows/segment_pnh.py -data ~/Data_maca -out ./local_test -soft SPM -params params.json

* the following parameters are optional:

    * -indiv or -indiv_params : a json file overwriting the default parameters (both macapype default and parameters specified in -params json file) for specific subjects/sessions. See :ref:`Individual Parameters <indiv_params>` for more details

    * -sub (-subjects), -ses (-sessions), -acq (-acquisions), -rec (-reconstructions) allows to specifiy a subset of the BIDS dataset respectively to a range of subjects, session, acquision types and reconstruction types. The arguments can be listed with space seperator.

.. code:: bash

    $ python workflows/segment_pnh.py -data ~/Data_maca -out ./local_test -soft SPM -params params.json -sub Apache Baron -ses 01 -rec mean

    * -mask allows to specify a precomputed binary mask file (skipping brain extraction). The bets usage of this option if precomputing the pipeline till brain_extraction_pipe, modify by hand the mask and use the mask for segmentation. Better if only one subject*session is specified.

        * warning: the mask should be in the same space as the data.

        * only works with -soft ANTS so far
