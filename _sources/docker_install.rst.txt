:orphan:

.. _docker_install:

**************
Docker install
**************

Docker allows to provide all necessary softwares in extra to macapype packages. The Docker image we provide include ANTS 2.3.1, FSL 5.0.10 and AFNI (latest version). See at the bottom of this page for docker with SPM Stand-alone.

Also note that the image is quite big (~5GB) so requires some space on your "/" partition.

Dockerfile
-----------

Downloading Dockerfile and building an image:

.. code:: bash

    # Downloading Dockerfile
    $ wget https://github.com/Macatools/macapype/blob/master/Dockerfile

    # Building your image from the Dockerfile
    $ docker build -t macapype_docker .

Example of workflows (see :ref:`Workflows <workflows>` for more explanations):

.. code:: bash

    # Given your dataset follows BIDS standard and is located in ~/Data_maca
    # - running the workflow ants_based on full dataset
    $ docker run -ti -v ~/Data_maca:/data/macapype macapype_docker python /opt/packages/macapype/workflows/segment_pnh.py -soft ANTS -data /data/macapype -out /data/macapype -params /opt/packages/macapype/workflows/params_segment_pnh_ants_based.json

    # - running the workflow segment_multi_pnh_ants_based on one subject/session
    $ docker run -ti -v ~/Data_maca:/data/macapype macapype_docker python /opt/packages/macapype/workflows/segment_pnh.py -soft ANTS -data /data/macapype -out /data/macapype -sub Apache -ses 01 -params /opt/packages/macapype/workflows/params_segment_pnh_ants_based.json

Docker image
------------

A docker image can also be downloaded directly from `DockerHub repo <https://hub.docker.com/r/macatools/macapype>`_ :

.. code:: bash

    $ docker pull macatools/macapype:latest

    # Given your dataset follows BIDS standard and is located in ~/Data_maca
    # - running the workflow ants_based on full dataset
    $ docker run -ti -v ~/Data_maca:/data/macapype macatools/macapype:latest python /opt/packages/macapype/workflows/segment_pnh.py -soft ANTS -data /data/macapype -out /data/macapype -params /opt/packages/macapype/workflows/params_segment_pnh_ants_based.json

    # - running the workflow segment_multi_pnh_ants_based on one subject/session
    $ docker run -ti -v ~/Data_maca:/data/macapype macatools/macapype:latest python /opt/packages/macapype/workflows/segment_pnh.py -soft ANTS -data /data/macapype -out /data/macapype -sub Apache -ses 01 -params /opt/packages/macapype/workflows/params_segment_pnh_ants_based.json

Starting from the release v0.2.1 on github, the docker images are tagged accordingly on Dockerhub:

.. code:: bash

    $ docker pull macatools/macapype:version-0.2.1


Note on SPM Docker
------------------

We also provide an "un-build" Dockerfile version of macapype, providing SPM as stand-alone version, using MCR (Matlab Compile Runtime). However, when including SPM in the Dockerfile, the image size triples (5GB -> 15GB), so we consider this image to be used with caution.

The corresponding `Dockerfile <https://github.com/Macatools/macapype/blob/master/Dockerfile_spm_mcr>`_ should be rename *Dockerfile* and build as specified earlier in this page.
