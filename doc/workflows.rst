:orphan:

.. _workflows:

********************
How to run workflows
********************

Following the BIDS format
=========================

To run the pipeline over a full BIDS dataset:

.. code:: bash

    $ python workflows/segment_pnh_regis.py -data ~/Data_maca -out ./local_test

To specify with subjects/sessions you want to run the pipeline on

.. code:: bash

    $ python workflows/segment_pnh_regis.py -data ~/Data_maca -out ./local_test -subjects Elouk -sess 01
    $ python workflows/segment_pnh_regis.py -data ~/Data_maca -out ./local_test -subjects Elouk
