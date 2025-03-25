:orphan:

.. _quick_test:

**********
Quick test
**********

Download datasets
#################

.. code:: bash

    $ cd /path/to/data

    $ curl https://amubox.univ-amu.fr/public.php/dav/files/YGrYLjRb8AyQoQp --output macapype_CI_v2.zip

    $ unzip -o macapype_CI_v2.zip -d macapype_CI_v2

Testing depending on the installation
#####################################

Testing from Singularity image
------------------------------

.. code:: bash

    $ singularity run -B /path/to/data:/data /path/to/containers/macapype_v0.5.sif segment_pnh -data /data/macapype_CI_v2/cerimed_marmo -out /data/macapype_CI_v2/cerimed_marmo/results -soft ANTS_test -species marmo -sub Tresor -ses 01 -deriv -pad -dt T1 T2

    $ singularity run -B /path/to/data:/data /path/to/containers/macapype_v0.5.sif segment_pnh -data /data/macapype_CI_v2/cerimed_marmo -out /data/macapype_CI_v2/cerimed_marmo/results -soft ANTS_prep -species marmo -sub Tresor -ses 01 -deriv -pad -dt T1 T2

    $ singularity run -B /path/to/data:/data /path/to/containers/macapype_v0.5.sif segment_pnh -data /data/macapype_CI_v2/cerimed_marmo -out /data/macapype_CI_v2/cerimed_marmo/results -soft ANTS_noseg -species marmo -sub Tresor -ses 01 -deriv -pad -dt T1 T2

    $ singularity run -B /path/to/data:/data /path/to/containers/macapype_v0.5.sif segment_pnh -data /data/macapype_CI_v2/cerimed_marmo -out /data/macapype_CI_v2/cerimed_marmo/results -soft ANTS -species marmo -sub Tresor -ses 01 -deriv -pad -dt T1 T2


The 4 commands earlier corresponds to brain segmentation performed on an example of marmoset (Tresor) . The 4 steps corresponds to incremental processings, and can performed in the given order. It is possible to test directly the last command (with *-soft ANTS*), but the caching system of nipype should work and the previous steps will not be performed again.

* The first one (*-soft ANTS_test*) is to test the workflow graph. If it works, the representation graph of the pipeline is available as:

.. code:: bash

    /path/to/data/macapype_CI_v2/cerimed_marmo/results/macapype_crop_aladin_ants_t1_t2/graph.png

* The second one (*-soft ANTS_prep*) is to run data preparation pipeline (corresponding to preprocessing). If it works, you should be able to see the data after automated croping and alignement in the template space:

.. code:: bash

    /path/to/data/macapype_CI_v2/cerimed_marmo/results/derivatives/macapype_crop_aladin_ants_t1_t2/sub-Tresor/ses-01/anat/sub-Tresor_ses-01_space-stereo_T1w.nii.gz

* The third one (*-soft ANTS_noseg*) will perform brain extraction and stop afterward. This is normally the longest step (ranging from 45min to a few hours depending on the image resolution. If it works, you should be able to see the brain mask as :

.. code:: bash

    /path/to/data/macapype_CI_v2/cerimed_marmo/results/derivatives/macapype_crop_aladin_ants_t1_t2/sub-Tresor/ses-01/anat/sub-Tresor_ses-01_space-stereo_desc-brain_mask.nii.gz

* The fourth and last one (*-soft ANTS*) will perform brain segmentation and mesh. If it works, you should be able to see the brain segmented mask and brain mesh as :

.. code:: bash

    /path/to/data/macapype_CI_v2/cerimed_marmo/results/derivatives/macapype_crop_aladin_ants_t1_t2/sub-Tresor/ses-01/anat/sub-Tresor_ses-01_space-stereo_desc-brain_desc-desg_mask.nii.gz


Testing from docker image
------------------------

For testing the docker installation, the beginning of the commands should be replaced by docker run -v /path/to/data:/data macatools/macapype:v0.3.1, e.g.

.. code:: bash

    $ docker run -v /path/to/data:/data macatools/macapype:v0.5 segment_pnh -data /data/macapype_CI_v2/cerimed_marmo -out /data/macapype_CI_v2/cerimed_marmo/results -soft ANTS -species marmo -sub Tresor -ses 01 -deriv -pad -dt T1 T2


Testing from python package install
-----------------------------------

From pip install
~~~~~~~~~~~~~~~~
.. code:: bash

    $ segment_pnh -data /path/to/data/macapype_CI_v2/cerimed_marmo -out /path/to/data/macapype_CI_v2/cerimed_marmo/results -soft ANTS -species marmo -sub Tresor -ses 01 -deriv -pad -dt T1 T2

From github install
~~~~~~~~~~~~~~~~
.. code:: bash

    $ python workflows/segment_pnh.py -data /path/to/data/macapype_CI_v2/cerimed_marmo -out /path/to/data/macapype_CI_v2/cerimed_marmo/results -soft ANTS -species marmo -sub Tresor -ses 01 -deriv -pad -dt T1 T2

**Note the /path/to/data instead of /data (as in the container install) in the arguments**



Testing the macaque and baboon datasets
#######################################

Two other dataset, corresponding to one macaque and one baboon, are available in the test dataset. Please not that due to higher image resolution, the preprocessing will take a longer time.

Baboon
******

.. code:: bash

    $ singularity run -B /path/to/data/:/data /path/to/containers/macapype_v0.5.sif segment_pnh -data /data/macapype_CI_v2/cerimed_baboon -out /data/macapype_CI_v2/cerimed_baboon/results -soft ANTS -species baboon -sub Prune -ses 3 -deriv -pad -dt T1 T2


Macaque
*******

.. code:: bash

    $ singularity run -B /path/to/data/:/data /path/to/containers/macapype_v0.5.sif segment_pnh -data segment_pnh -data /data/macapype_CI_v2/macaque_prime-de -out /data/macapype_CI_v2/macaque_prime-de/results -soft ANTS -sub Stevie -ses 01 -deriv -pad -dt T1 T2 -species macaque

Testing different pipelines and options
#######################################

    It is possible to run the pipeline with only T1w available with *-dt T1* (instead of *-dt T1 T2* previously). Please see `Commands <command>`_ for further information on the parameters available for command line
