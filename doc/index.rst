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

* the :ref:`plot_segment pipeline <plot_segment>` runs the graph computation and graph-theoretical tools over connectivity matrices.
