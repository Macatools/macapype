:orphan:

.. _workflows:

********************
How to run workflows
********************

Following the BIDS format
=========================

To run the pipeline over a full BIDS dataset:

.. code:: bash

    $ python workflows/segment_pnh_spm_based.py -data ~/Data_maca -out ./local_test

To specify with subjects/sessions you want to run the pipeline on:

.. code:: bash

    $ python workflows/segment_pnh -data ~/Data_maca -out ./local_test -soft SPM -subjects Elouk -sess 01
    $ python workflows/segment_pnh -data ~/Data_maca -out ./local_test -soft SPM -subjects Elouk

You can also specify a json file containing the parameters of your analysis

.. code:: bash

    $ python workflows/segment_pnh.py -data ~/Data_maca -out ./local_test -soft SPM -params params.json

Here is an example of the params.json corresponding to :class:`segment_pnh_spm_based pipeline <macapype.pipelines.full_segment.create_full_segment_pnh_T1xT2>`:

.. include:: ../workflows/params_segment_pnh_spm_based.json
   :literal:

You can also include multi_params.json, for specifiying parameters specific parameters:


.. code:: bash

    $ python workflows/segment_pnh.py -data ~/Data_maca -out ./local_test -soft SPM -params params.json -multi_params multi_params.json
