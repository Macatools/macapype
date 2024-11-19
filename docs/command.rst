:orphan:

.. command:

----------------------
Launching a processing
----------------------

Commands
********

The main file is located in workflows and is called segment_petra.py and should be called like a python script:

.. code:: bash

    $ python workflows/segment_petra.py

**N.B. if you have installed the pypi version (e.g. using pip install macapype) or a docker/singularity version, you can replace the previous command by the following command:**

.. code:: bash

    $ segment_petra



For container (docker and singularity), here are some examples - add your proper bindings:

.. code:: bash

    $ docker run -B binding_to_host:binding_guest macatools/skullto3d:latest segment_petra

.. code:: bash

    $ singularity run -v binding_to_host:binding_guest /path/to/containers/skullto3d_v0.0.4.1.sif segment_petra

Expected input data
*******************


All the data have to be in BIDS format to run properly (see `BIDS specification <https://bids-specification.readthedocs.io/en/stable/index.html>`_ for more details)

In particular:

* _T1w (BIDS) extension is expected for T1 weighted images (BIDS)
* _T2w (BIDS) extension is expected for T2 weighted images (BIDS)
* _PDw (BIDS) or petra (non-BIDS) extensions are expected for petra images

* _acq-CT_T2star (BIDS, but non canonical) extension is expected for CT images
* _angio extension is expected for angiography images


Command line parameters
***********************

--------------------------------------
The following parameters are mandatory
--------------------------------------

* -data  *like in macapype*
the path to your data dataset (existing BIDS format directory)

* -out  *like in macapype*
the path to the output results (an existing path)

* -soft  *like in macapype*
can be one of these : SPM or ANTS
    * with _skull after SPM or ANTS if you want to process skull or angio *specific to skullTo3d*; otherwise the main pipelines of macapype will be launched (only brain segmentation will be performed)
    * with _robustreg (at the end) to have a more robust registration (in two steps) *like in macapype*
    * with _test (at the end) to check if the full pipeline is coherent (will only generate the graph.dot and graph.png) *like in macapype*
    * with _prep (at the end) will perform data preparation (no brain extraction and segmentation) *like in macapype*
    * with _noseg (at the end) will perform data preparation and brain extraction (no segmentation) *like in macapype*
    * with _seq (at the end) to run in sequential mode (all iterables will be processed one after the other; equivalent to -nprocs 1) *like in macapype*


--------------------------------------
The following parameters are exclusive
--------------------------------------
*(but one is mandatory)*

* -params  *(mandatory if -species is omitted)*
a json file specifiying the global parameters of the analysis. See :ref:`Parameters <params>` for more details

* -species  *(mandatory if -params is omitted)*
followed the NHP species corresponding to the image, e.g. {macaque | marmo | baboon | chimp}

--------------------------------------
The following parameters are optional
--------------------------------------
*(but highly recommanded)*

* -brain_dt  *equivalent to -dt in macapype*
specifies the datatype available to perform brain segmentation (can be "T1", or "T1 T2").
**Note** : default is T1 if the attribute is omitted

* -skull_dt  *specific to skullTo3d*
specifies the datatype available for skull segmentation (can be, "T1", "petra", "CT", "angio" or a combination of the latter (with space(s) in between).
**Note** : default is T1 if the attribute is omitted.

* -deriv  creates a derivatives directory, with all important files, properly named following BIDS derivatives convertion

* -pad  exports (in derivatives) important files in native (original) space

--------------------------------------
The following parameters are optional
--------------------------------------

* -indiv or -indiv_params : a json file overwriting the default parameters (both macapype default and parameters specified in -params json file) for specific subjects/sessions. See :ref:`Individual Parameters <indiv_params>` for more details

* -sub (-subjects), -ses (-sessions), -acq (-acquisions), -rec (-reconstructions) allows to specifiy a subset of the BIDS dataset respectively to a range of subjects, session, acquision types and reconstruction types. The arguments can be listed with space seperator. **Note** if not specified, the full BIDS dataset will be processed

* -mask allows to specify a precomputed binary mask file (skipping brain extraction). The best usage of this option is: precomputing the pipeline till brain_extraction_pipe, modify by hand the mask and use the mask for segmentation. Better if only one subject*session is specified (one file is specified at a time...).

**Warning: the mask should be in the same space as the data. And only works with -soft ANTS so far**

* -nprocs : an integer, to specifiy the number of processes that should be allocated by the parralel engine of macapype
    * typically equals to the number of subjects*session (i.e. iterables).
    * can be multiplied by 2 if T1*T2 pipelines are run (the first steps at least will benefit from it)
    * default = 4 if unspecified ; if is put to 0, then the sequential processing is used (equivalent to -soft with _seq, see before)

***********************
Command line examples
***********************


.. code:: bash

    $ python workflows/segment_petra.py -data ~/Data_maca -out ./local_test -soft ANTS_skull -params params.json


.. code:: bash

    $ python workflows/segment_petra.py -data ~/Data_maca -out ./local_test -soft ANTS_skull_robustreg -species macaque

.. code:: bash

    $ python workflows/segment_petra.py -data ~/Data_maca -out ./local_test -soft ANTS_skull -params params.json -sub Apache Baron -ses 01 -rec mean -deriv -pad
