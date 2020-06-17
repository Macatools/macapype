.. _macapype:

********
Macapype
********

Macapype is an open-source multi-modal brain data analysis kit which provides **Python-based
pipelines** for advanced multi-thread processing of MRI anatomical data of PNH brain images.
Neuropycon is based on `Nipype <http://nipype.readthedocs.io/en/latest/#>`_, a tool developed in fMRI field, which facilitates data analyses by wrapping many commonly-used neuro-imaging software into a common python framework.

API, describing the different pipelines and nodes, can be found :ref:`here <api_documentation>`

Installation
************

See :ref:`Installation <install>` for installation on your local system if you have adequate softwares (i.e. FSL, AFNI, Ants, SPM) running on your machine/clusters.


Docker
******

A Dockerfile, and a docker image are also available, explanations can be found :ref:`here <docker_install>`

Workflows
**********
Running workflows can be found :ref:`here <workflows>`

Tutorial
********

Explanations on how to modify the processing can be found :ref:`here <tutorial>`

Explanations of the various pipelines are found :ref:`here <pipelines>`

Examples
********

Several examples can be found :ref:`here <examples>`

Contributing
*************
Some advices on how to contribute to the source code can be found :ref:`here <contribute>`

Table of contents
******************

.. toctree::
    :maxdepth: 2

    api
    install
    docker_install
    workflows
    tutorial
    examples
    pipelines
    contribute
