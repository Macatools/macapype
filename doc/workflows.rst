.. _workflows:

********************
How to run workflows
********************

Following the BIDS format
=========================

.. code:: bash

    $ python workflows/segment_pnh_regis.py -data ~/Data_maca -out ./local_test -subjects Elouk -sess 01
    $ python workflows/segment_pnh_regis.py -data ~/Data_maca -out ./local_test -subjects Elouk

Will find the corresponding data if follows BIDS :

.. code:: bash

    $ python workflows/segment_pnh_regis.py -data ~/Data_maca -out ./local_test

-- Warning-- cropped data should be used for more efficient processing
-- Warning-- cropped data should also be saved as 'T1w.nii' instead of 'T1wCropped.nii'

.. code:: bash

    $ python workflows/segment_pnh_kepkee.py -data ~/Data_maca -out ./local_test -cropped True

-- Warning-- cropped data should be used for more efficient processing
-- Warning-- cropped T1 should also be saved as 'T1w.nii' instead of 'T1wCropped.nii'
-- Warning-- cropped T2 should also be saved as 'T2w.nii' instead of 'T2wRegT1wCropped.nii'

if already cropped, or no cropbox is provided:

.. code:: bash

    $ python segment_pnh_kepkee.py -data ~/Data_maca -out ./local_test -subjects 032311 -ses ses-001

Add the -crop_req if cropping is required, and .cropbox is provided

# TODO : follow the same syntax for datagrabber with pybids or not
