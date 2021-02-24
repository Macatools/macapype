:orphan:

.. _workflows:

********************
How to run workflows
********************

* the main file is located in workflows and is called segment_pnh.py and should be called like a python script:

.. code:: bash

    $ python workflows/segment_pnh.py

* all the data have to be in BIDS format to run properly (see `BIDS specification <https://bids-specification.readthedocs.io/en/stable/index.html>`_ for more details)

* the following parameters are mandatory:

    * -data is the path to your data dataset (existing BIDS format directory)

    * -out is the path to the output results (an existing path)

    * -soft can be one of these : SPM or ANTS

        * with _T1 at the end if only T1w (and not T2w) are available

        * with _test to see if the full pipeline is coherent (will only generate the graph.dot and graph.png)

        * with _seq to run in sequential mode (all iterables will be processed one after the other; equivalent to -nprocs 0)

    * -params: a json file specifiying the global parameters of the analysis. See :ref:`Parameters <params>` for more details

.. code:: bash

    $ python workflows/segment_pnh.py -data ~/Data_maca -out ./local_test -soft SPM -params params.json

* the following parameters are optional:

    * -indiv or -indiv_params : a json file overwriting the default parameters (both macapype default and parameters specified in -params json file) for specific subjects/sessions. See :ref:`Individual Parameters <indiv_params>` for more details

    * -sub (-subjects), -ses (-sessions), -acq (-acquisions), -rec (-reconstructions) allows to specifiy a subset of the BIDS dataset respectively to a range of subjects, session, acquision types and reconstruction types. The arguments can be listed with space seperator.

    .. code:: bash

        $ python workflows/segment_pnh.py -data ~/Data_maca -out ./local_test -soft SPM -params params.json -sub Apache Baron -ses 01 -rec mean

    * -mask allows to specify a precomputed binary mask file (skipping brain extraction). The bets usage of this option if precomputing the pipeline till brain_extraction_pipe, modify by hand the mask and use the mask for segmentation. Better if only one subject*session is specified.

        * warning: the mask should be in the same space as the data.

        * only works with -soft ANTS so far

    * -nprocs : an integer, to specifiy the number of processes that should be allocated by the parralel engine of macapype

        * typically equals to the number of subjects*session (i.e. iterables).

        * can be multiplied by 2 if T1*T2 pipelines are run (the first steps at least will benefit from it)

        * default = 4 if unspecified ; if is put to 0, then the sequential processing is used (equivalent to -soft with _seq, see before)
