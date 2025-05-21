.. _macapype:

********
Macapype
********
..
.. .. _short_logo:
.. .. |logo1| image:: ./img/logo/logo_macapype_0.3.jpg
..     :scale: 100%
..
.. .. table::
..    :align: center
..
..    +---------+
..    | |logo1| |
..    +---------+
..

Macapype is an open-source multi-modal brain data analysis kit which provides **Python-based pipelines** for advanced multi-thread processing of MRI anatomical data of NPH brain images. Macapype is based on `Nipype <https://nipype.readthedocs.io/en/latest>`_, a tool developed in fMRI field, which facilitates data analyses by wrapping many commonly-used neuro-imaging software into a common python framework.

.. image:: ./img/logo/logo_macapype_0.3.jpg
    :width: 600
    :align: center

Installation
************

See :ref:`Quick Installation <quick_install>` for installation on your local system if you have adequate softwares (i.e. FSL, AFNI, Ants, SPM) running on your machine/clusters

See :ref:`Container installation <docker_install>` for fully compliant installation (no MRI softwares, or Windows / MacOS operating system)

Once installed, see :ref:`Quick test <quick_test>` for testing if your installation is working properly

Command line parameters
***********************

macapype is fairly flexible, but requires to specify multiples parameters in command line

See :ref:`Commands <command>` for a description on the avalaible command parameters

If ``-deriv``` is provided, see :ref:`Derivatives <derivatives>` for a descrition of the outputs

Table of contents
******************

.. toctree::
    :maxdepth: 2

    quick_install
    docker_install
    quick_test
    command
    derivatives
    params
    indiv_params


