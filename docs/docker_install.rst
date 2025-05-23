:orphan:

.. _docker_install:

*****************
Container install
*****************

Docker allows to provide all necessary softwares in extra to macapype packages. The Docker image we provide include ANTS 2.3.1, FSL 5.0.10 and AFNI (latest version). See at the bottom of this page for docker with SPM Stand-alone.

**Note 1** :the image is quite big (~5GB) so requires some space on your "/" partition.

Dockerfile
-----------

Downloading Dockerfile and building an image:

.. code:: bash

    # Downloading Dockerfile
    $ wget https://github.com/Macatools/macapype/blob/master/Dockerfile

    # Building your image from the Dockerfile
    $ docker build -t macapype_docker .

Docker image
------------

A docker image can also be downloaded directly from `DockerHub repo <https://hub.docker.com/r/macatools/macapype>`_ :

.. code:: bash

    $ docker pull macatools/macapype:latest

Starting from the release v0.2.1 on github, the docker images are tagged accordingly on Dockerhub:

.. code:: bash

    $ docker pull macatools/macapype:v0.6


See :ref:`Quick test <quick_test>` for testing if your docker installation works properly on test datasets.

Note on Singularity
-------------------

It is possible (and recommanded) to use singularity version of container on shared computers/clusters. macapype docker version has been tested and is compatible with versions of singularity higher than 0.3 ("sif" version)

Here is an example of a command line to install and convert the docker image to singularity image :

.. code:: bash

    $ singularity build /path/to/containers/macapype_v0.6.sif docker://macatools/macapype:v0.6

The container have been tested and can be installed without sudo privilieges; In case you have trouble or want the container to be accessible on a shared cluster, ask the admin of the cluster to perform this operation:

.. code:: bash

    $ export SINGULARITY_TMPDIR=/tmp/; export SINGULARITY_CACHEDIR=/tmp/; sudo -E /path/to/bin/singularity build /path/to/containers/macapype_v0.6.sif docker://macatools/macapype:v0.6

See :ref:`Quick test <quick_test>` for testing if your singularity installation works properly on test datasets.

