.. _macapype:

********
Macapype
********

Macapype is an open-source multi-modal brain data analysis kit which provides **Python-based
pipelines** for advanced multi-thread processing of fMRI anat in PNH. Neuropycon is based on `Nipype <http://nipype.readthedocs.io/en/latest/#>`_,
a tool developed in fMRI field, which facilitates data analyses by wrapping many commonly-used neuro-imaging software into a common
python framework.

Installation
************

See :ref:`Installation <install>` for installation on your local system if you have adequate softwares (i.e. FSL, AFNI, Ants, SPM) running on your machine/clusters.
Running subsequent workflows can be found :ref:`here <workflows>`

Docker
******

A docker image is also available, explanation can be found :ref:`here <docker_install>`

Examples
********

An exemple of :ref:`reorientation <plot_segment_pnh_isabelle>`, starting from a sphinx position.

The :ref:`plot_segment_pnh_regis_T1xT2 workflow <plot_segment_pnh_regis_T1xT2>` based on Regis' :class:`full pipeline <macapype.pipelines.full_segment.create_full_segment_pnh_T1xT2>`, with the processing sequence:

* :class:`T1xT2Bet <macapype.nodes.extract_brain.T1xT2BET>`
* :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>`
* :class:`IterREGBET <macapype.nodes.register.IterREGBET>`
* :class:`old_segment SPM based pipeline <macapype.pipelines.segment.create_old_segment_pipe>`


The :ref:`plot_segment_pnh_kepkee workflow <plot_segment_pnh_kepkee>` based on Kepkee's :class:`full pipeline <macapype.pipelines.full_segment.create_full_segment_pnh_subpipes>`, with the processing sequence :

* :class:`T1xT2Bet <macapype.nodes.extract_brain.T1xT2BET>` (used for the cropping tool only)
* :class:`debias pipeline <macapype.pipelines.correct_bias.create_correct_bias_pipe>` (~ to T1xT2BiasFieldCorrection, but all steps are nipype nodes)
* :class:`denoise pipeline <macapype.pipelines.denoise.create_denoised_pipe>` (from Ants non-local mean)
* :class:`brain extraction pipeline <macapype.pipelines.extract_brain.create_brain_extraction_pipe>` using Atlax-Brex
* :class:`full segment from mask <macapype.pipelines.full_segment.create_full_segment_from_mask_pipe>` (starting from the mask, the following steps are computed):
    - :class:`denoise pipeline <macapype.pipelines.denoise.create_denoised_pipe>`
    - :class:`masked debias pipeline <macapype.pipelines.correct_bias.create_masked_correct_bias_pipe>`
    - :class:`register pipeline <macapype.pipelines.register.create_register_NMT_pipe>` from template (NMT) to subject space
    - :class:`segmentation pipeline <macapype.pipelines.segment.create_segment_atropos_pipe>` in subject space with Atropos

The same :class:`full pipeline <macapype.pipelines.full_segment.create_full_segment_pnh_subpipes>`, used on marmouset data (:ref:`link to example <plot_segment_marmo_test>`). The automated cropping did not work, hence manual cropping was used

