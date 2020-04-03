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

The :ref:`plot_segment_pnh_regis_T1xT2 pipeline <plot_segment_pnh_regis_T1xT2>` runs the Regis pipeline, with:

* :class:`T1xT2Bet <macapype.nodes.bash_regis.T1xT2BET>`,
* :class:`T1xT2BiasFieldCorrection <macapype.nodes.bash_regis.T1xT2BiasFieldCorrection>`,
* :class:`IterREGBET <macapype.nodes.bash_regis.IterREGBET>`,
* :class:`old_segment SPM based pipeline <macapype.pipelines.segment.create_old_segment_pipe>`

The :ref:`plot_segment_pnh_kepkee pipeline <plot_segment_pnh_kepkee>` runs the Kepkee pipeline, with:

* T1xT2Bet (used for the cropping tool)
* debias pipeline (~ to T1xT2BiasFieldCorrection, but all steps are nipype nodes)
* denoise pipe (from Ants non-local mean)
* brain extraction using Atlax-Brex
