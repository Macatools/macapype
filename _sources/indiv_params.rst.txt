.. _indiv_params:

Individual Parameters
_____________________

Adding -indiv
*************

You can include "-indiv indiv_params.json" in the python command, for specifiying parameters specific parameters:


.. code:: bash

    $ python workflows/segment_petra.py -data ~/Data_maca -out ./local_test -soft SPM -params params.json -indiv indiv_params.json


Advanced parameters settings
****************************


Here is json file with all possible nodes to be tuned in indiv_params; In particular, the specifications of sub- and ses- are mandatory before the specification of nodes; Also note that the nodes are specified directly, without specifiying the sub-pipelines they belong to.

The nodes belonging to "short_data_preparation" pipeline (see `Params<params>`_) are common to both -soft ANTS and SPM :

.. include:: ../examples_doc/indiv_params_preparation.json
   :literal:


For -soft SPM, here is the set of nodes that can be individually tuned:

.. include:: ../examples_doc/indiv_params_segment_spm.json
   :literal:

For -soft ANTS, here is the set of nodes that can be individually tuned:

.. include:: ../examples_doc/indiv_params_segment_ants.json
   :literal:

