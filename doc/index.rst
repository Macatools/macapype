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

API, describing the different pipelines and nodes, can be found :ref:`here <api_documentation>`

.. image:: ./img/logo/logo_macapype_0.3.jpg
    :width: 600
    :align: center


Choose your install
*******************

git install
-----------

.. code-block:: bash

    git clone https://github.com/Macatools/macapype.git

(see :ref:`Git install <git_install>`)

pip install
-----------

.. code-block:: bash

    pip install macapype

(see :ref:`Pypi install <pip_install>`)

docker/singularity install
--------------------------

.. code-block:: bash

    docker pull macatools/macapype:latest

(see :ref:`Docker install <docker_install>`)


Ressources
************

`Open Science Room OSR 2020 of OHBM congress presentation of macapype <https://docs.google.com/presentation/d/11RrcZW25MyLbc0_9T2zzhwy5RyUvcjYG4UAgzjuuv8M/edit?usp=sharing>`_


Forum macapype_users
**********************

The macapype_users forum can be be found `here <https://framateam.org/signup_user_complete/?id=ebtxf45nmiyqmkm8e6oh9qjsoe>`_ (requires a framateam/framagit account, but should be accessible with a github or bitbucket account).

See the section :ref:`Forum <forum>` for more information on how to connect.


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

Useful tips
***********

Some useful tips to reorient and crop images :ref:`here <utils>`

Contributing
*************
Some advices on how to contribute to the source code can be found :ref:`here <contribute>`

Table of contents
******************

.. toctree::
    :maxdepth: 2

    install
    docker_install
    workflows
    params
    indiv_params
    tutorial
    examples
    pipelines
    external_pipeline
    contribute
    utils
    brainhack
