.. _docker_install:

******
docker
******


Dockerfile
-----------

Downloading Dockerfile and building an image:

.. code:: bash

    $ wget https://github.com/Macatools/macapype/blob/master/Dockerfile

    $ docker build -t macapype .

Example of workflows (see :ref:`Workflows <workflows>` for more explanations):

.. code:: bash

    # given your data are located in ~/Data_maca
    $ docker run -ti -v ~/Data_maca:/data/macapype macapype python3 /root/packages/macapype/workflows/segment_pnh_regis.py -data /data/macapype -out /data/macapype -subjects Apache -sess ses-01
    $ docker run -ti -v ~/Data_maca:/data/macapype macapype python3 /root/packages/macapype/workflows/segment_pnh_kepkee.py -data /data/macapype -out /data/macapype -subjects Apache -sess ses-01
    $ docker run -ti -v ~/Data_maca:/data/macapype macapype python3 /root/packages/macapype/workflows/segment_pnh_regis.py -data /data/macapype -out /data/macapype
    $ docker run -ti -v ~/Data_maca:/data/macapype macapype python3 /root/packages/macapype/workflows/segment_pnh_kepkee.py -data /data/macapype -out /data/macapype -cropped True

Docker image
------------

A docker image can also be downloaded directly from DockerHub repo:

.. code:: bash

    $ docker pull macatools/macapype
    $ docker run -ti -v ~/Data_maca/Primavoice:/data/macapype macatools/macapype:latest python3 /root/packages/macapype/workflows/segment_pnh_regis.py -data /data/macapype -out /data/macapype



