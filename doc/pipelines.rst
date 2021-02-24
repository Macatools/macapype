.. _pipelines:

Pipelines
_________

.. _spm_pipelines:
SPM-based pipelines
~~~~~~~~~~~~~~~~~~~

Using T1w and T2w images
************************

:class:`full SPM pipeline <macapype.pipelines.full_pipelines.create_full_spm_subpipes>`, with the processing sequence:

* :class:`Data preparation <macapype.pipelines.prepare.create_short_preparation_pipe>` (See :ref:`Data preparation <data_prep>` for more details)
* :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`: iterative normalisation to template space
* :class:`IterREGBET <macapype.nodes.register.IterREGBET>`
* :class:`old_segment SPM based pipeline <macapype.pipelines.segment.create_old_segment_pipe>`


Using only a T1w image
**********************

:class:`full SPM T1 pipeline <macapype.pipelines.full_pipelines.create_full_T1_spm_subpipes>`, with the processing sequence:

* :class:`Data preparation <macapype.pipelines.prepare.create_short_preparation_pipe>` (See :ref:`Data preparation <data_prep>` for more details)
* :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>` but the T1w replaces the T2w
* :class:`IterREGBET <macapype.nodes.register.IterREGBET>`: iterative normalisation to template space
* ANTS non linear registration and FSL Apply XFM to tranform images to the template
* :class:`old_segment SPM based pipeline <macapype.pipelines.segment.create_old_segment_pipe>`

----

.. _ants_pipelines:
ANTS-based pipelines
~~~~~~~~~~~~~~~~~~~~

Using T1w and T2w images
************************

:class:`full ANTS pipeline <macapype.pipelines.full_pipelines.create_full_ants_subpipes>`, with the processing sequence :

* :class:`Short data preparation <macapype.pipelines.prepare.create_short_preparation_pipe>` or :class:`Long single data preparation <macapype.pipelines.prepare.create_long_single_preparation_pipe>` or :class:`Long multi data preparation <macapype.pipelines.prepare.create_long_multi_preparation_pipe>` (See :ref:`Data preparation <data_prep>` for more details)

* :class:`Brain extraction pipeline <macapype.pipelines.full_pipelines.create_brain_extraction_pipe>`
    - :class:`debias pipeline <macapype.pipelines.correct_bias.create_correct_bias_pipe>` (similar to :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`, but all steps are nipype nodes)
    - :class:`extract brain pipeline <macapype.pipelines.extract_brain.create_extract_pipe>` (using Atlax-Brex)

* :class:`Brain segment from mask <macapype.pipelines.full_pipelines.create_brain_segment_from_mask_pipe>` :
    - :class:`masked debias pipeline <macapype.pipelines.correct_bias.create_masked_correct_bias_pipe>`
    - :class:`register pipeline <macapype.pipelines.register.create_register_NMT_pipe>` from template (NMT) to subject space
    - :class:`segmentation pipeline <macapype.pipelines.segment.create_segment_atropos_pipe>` in subject space with Atropos

Using only T1w images
*********************

:class:`full ANTS T1 pipeline <macapype.pipelines.full_pipelines.create_full_T1_ants_subpipes>`, with the processing sequence :

* :class:`Short data T1 preparation <macapype.pipelines.prepare.create_short_preparation_T1_pipe>` (See :ref:`Data preparation <data_prep>` for more details)

* :class:`Brain extraction pipeline <macapype.pipelines.full_pipelines.create_brain_extraction_T1_pipe>`
    - :class:`extract brain pipeline <macapype.pipelines.extract_brain.create_extract_pipe>` (using Atlax-Brex)

* :class:`Brain segment from mask <macapype.pipelines.full_pipelines.create_brain_segment_from_mask_T1_pipe>` :
    - :class:`register pipeline <macapype.pipelines.register.create_register_NMT_pipe>` from template (NMT) to subject space
    - :class:`segmentation pipeline <macapype.pipelines.segment.create_segment_atropos_pipe>` in subject space with Atropos

----

.. _data_prep:
Data preparation
~~~~~~~~~~~~~~~~

Short data preparation
**********************

Short data preparation corresponds to the pipelines where T1 and T2 images are averaged by modality from the beginning, and T2 is aligned to T1, then cropped or betcropped, and denoised.

The "auto"" version corresponds to :class:`short data preparation <macapype.pipelines.prepare.create_short_preparation_pipe>` with "betcrop" option (using :class:`T1xT2BET <macapype.nodes.extract_brain.T1xT2BET>`)

The "manual" version corresponds to :class:`short data preparation <macapype.pipelines.prepare.create_short_preparation_pipe>` with "crop" option, and specify crop box in args for each subject in individual params

.. _short_prep:
.. |logo1| image:: ./img/short_manual_preparation_pipe/graph.png
    :scale: 100%

.. |logo2| image:: ./img/short_auto_preparation_pipe/graph.png
    :scale: 100%

.. table::
   :align: center

   +---------+---------+
   | |logo1| | |logo2| |
   +---------+---------+

The version with crop are used in :ref:`marmoset example <plot_segment_marmo_ants_based>`, the version with betcrop is used in both macaque examples with
:ref:`SPM <plot_segment_macaque_spm_based>` and :ref:`ANTS <plot_segment_macaque_ants_based>`

Long data preparation
*********************

In some cases, you may want some processing done prior to the alignement, if T1 and T2 are very different.

In this case, after aligning and averaging by modality (all T1s -> average_T1), you may crop, debias (N4) and denoise each image (average_T1 and average T2) indendantly before aligning average_T2 to average_T1 (:class:`long single data preparation <macapype.pipelines.prepare.create_long_single_preparation_pipe>`)

But in a very specific case, where the data of multiple sessions have been acquired with different settings (e.g. antenna contrast), you may have even all multiple modality data preprocessed (reorient, cropped, debiased, denoised) indendantly before being averaged and aligned by modality, and then av_T2 aligned to av_T1 (:class:`long multi data preparation <macapype.pipelines.prepare.create_long_multi_preparation_pipe>`)

.. _long_prep:
.. |logo3| image:: ./img/long_single_preparation_pipe/graph.png
    :scale: 80%

.. |logo4| image:: ./img/long_multi_preparation_pipe/graph.png
    :scale: 80%

.. table::
   :align: center

   +---------+---------+
   | |logo3| | |logo4| |
   +---------+---------+

The short version is used for the :ref:`baboon example <plot_segment_baboon_ants_based>`, the long version has been tested on a data set with multiple T1s (not shown in examples).

Options
*******

Reorient sub-pipeline
---------------------

For all the preparation pipelines, it is possible to add at the beginning of the pipeline a "reorient" subpipelines by specifying
An example can be found in :ref:`macaque sphinx <plot_segment_sphinx_macaque_ants_based>`

Denoise and denoise_first
-------------------------

By default, denoising is done at the end of the preparation pipeline, on the cropped data. It is however possible to move the denoise at the beginning at the pipeline, with option denoise first. *N.B.:  This option is only available in long preparation (single and multi) so far*

