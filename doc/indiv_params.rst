.. _indiv_params:

Individual Parameters
_____________________

Adding -indiv
*************

You can include "-indiv indiv_params.json" in the python command, for specifiying parameters specific parameters:


.. code:: bash

    $ python workflows/segment_pnh.py -data ~/Data_maca -out ./local_test -soft SPM -params params.json -indiv indiv_params.json


Here is an example of the params.json corresponding to :class:`segment_pnh_spm_based pipeline <macapype.pipelines.full_segment.create_full_spm_subpipes>`:

.. include:: ./img/crop/indiv_params_example.json
   :literal:
