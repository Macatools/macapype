:orphan:

.. _docker_install:

*****************
Container install
*****************

Docker allows to provide all necessary softwares in extra to macapype packages. The Docker image we provide include ANTS 2.3.1, FSL 5.0.10 and AFNI (latest version). See at the bottom of this page for docker with SPM Stand-alone.

**Note 1** :the image is quite big (~5GB) so requires some space on your "/" partition.
**Note 2** : due to standard naming format, the repository on DockerHub is called "skullto3d", not "skullTo3d" - please note the difference in uppercase lowercase "T"...

Dockerfile
-----------

Downloading Dockerfile and building an image:

.. code:: bash

    # Downloading Dockerfile
    $ wget https://github.com/Macatools/skullTo3d/blob/master/Dockerfile

    # Building your image from the Dockerfile
    $ docker build -t skullTo3d_docker .

Docker image
------------

A docker image can also be downloaded directly from `DockerHub repo <https://hub.docker.com/r/macatools/skullto3d>`_ :

.. code:: bash

    $ docker pull macatools/skullto3d:latest

Starting from the release v0.2.1 on github, the docker images are tagged accordingly on Dockerhub:

.. code:: bash

    $ docker pull macatools/skullto3d:version-0.2.1


Note on Singularity
-------------------

It is possible (and recommanded) to use singularity version of container on shared computers/clusters. skullto3d docker version has been tested and is compatible with versions of singularity higher than 0.3 ("sif" version)

Here is an example of a command line to install and convert the docker image to singularity image :

.. code:: bash

    $ export SINGULARITY_TMPDIR=/tmp/; export SINGULARITY_CACHEDIR=/tmp/; sudo -E /path/to/bin/singularity build /path/to/containers/skullto3d_v0.0.4.1.sif docker://macatools/skullto3d:v0.0.4.1

It *seems* the sudo priviliges are required to install and build images, so in case you have trouble, ask the admin of your cluster to perform this operation

