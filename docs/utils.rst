:orphan:

.. _utils:

Useful tips (before processing)
_______________________________


**************************************
How to orient the labels your images ?
**************************************

In particular, the image should be in neurological convention, i.e. left label on the right of the image in FSL coronal representation, and x values increasion from left to right.

.. image:: ./img/crop/wrong_orient_mark.png
    :scale: 50%
    :align: center

If is not the case, use the following procedure to swap the X-axis

.. code-block:: bash

    cp Orig/sub-Iroquoise_ses-01_T1w.nii.gz .
    fslreorient2std sub-Iroquoise_ses-01_T1w.nii.gz sub-Iroquoise_ses-01_T1w_reorient.nii.gz
    fslorient -forceneurological sub-Iroquoise_ses-01_T1w_reorient.nii.gz
    fslswapdim sub-Iroquoise_ses-01_T1w_reorient.nii.gz -x y z sub-Iroquoise_ses-01_T1w_reorient_swapped.nii.gz
    mv sub-Iroquoise_ses-01_T1w_reorient_swapped.nii.gz sub-Iroquoise_ses-01_T1w.nii.gz

After the labels are reoriented:

.. image:: ./img/crop/good_orient_mark.png
    :scale: 50%
    :align: center

********************************************
How to tilt the orientation of your images ?
********************************************

Nudging the image with FSLEyes
##############################

In FSLEyes
----------

1. Open T1w image

.. code-block:: bash

    fsleyes Orig/sub-Pandore_ses-01_rec-mean_T1w.nii.gz

.. image:: ./img/nudge/Pandore_01_Orig.png
    :scale: 50%
    :align: center


2. Open Nudge Menu

In the upper bar menu of FSLEyes, click on "Tools" -> "Nudge"

.. image:: ./img/nudge/Pandore_01_NudgeMenu.png
    :scale: 50%
    :align: center


3. Change to World coordinates


Click on "Change display Space"

.. image:: ./img/nudge/Pandore_01_AfterChangeCoordToWorld.png
    :scale: 50%
    :align: center


4. Rotate the image

Should be: biggest dimension along the anterior-posterior axis (Y)
No Left/right tilt (equilibrated)
Facing straight when viewed from from the top

.. image:: ./img/nudge/Pandore_01_AfterRotate.png
    :scale: 50%
    :align: center



5.  Saving the affine

Click on "Save affine" in the lower menu of Nudge window, and
!!Important!! choose  "FLIRT" for file type and save the affine under your favorite name .mat (e.g nudge_T1w.mat)

.. image:: ./img/nudge/Pandore_01_SaveAffine.png
    :scale: 50%
    :align: center

Apply the nudge transfo to the Orig image
-----------------------------------------


.. code-block:: bash

    flirt -in sub-Pandore_ses-01_rec-mean_T1w.nii.gz -o sub-Pandore_ses-01_rec-mean_T1w_nudge.nii.gz -ref sub-Pandore_ses-01_rec-mean_T1w.nii.gz -applyxfm -init nudge_T1w.mat

(optionally, fslreorient2std matbe also be applied)

.. code-block:: bash

    fslreorient2std sub-Pandore_ses-01_rec-mean_T1w_nudge.nii.gz sub-Pandore_ses-01_rec-mean_T1w_nudge_std.nii.gz

Possibly, pre-apply the align T2 -> T1 before the launch of the script
(it should be done at the beginning of the script, but better to check if the command is working properly)

.. code-block:: bash

    flirt -in sub-Pandore_ses-01_T2w.nii.gz -ref sub-Pandore_ses-01_rec-mean_T1w.nii.gz -out sub-Pandore_ses-01_T2w_flirt.nii.gz -dof 6

rename everything back as intended in BIDS
------------------------------------------

.. code-block:: bash

    mv sub-Pandore_ses-01_rec-mean_T1w_nudge_std.nii.gz  sub-Pandore_ses-01_rec-mean_T1w.nii.gz
    mv sub-Pandore_ses-01_T2w_flirt.nii.gz  sub-Pandore_ses-01_T2w.nii.gz



************************************
How to compute cropping parameters ?
************************************

All the pipeline works with a default tool for automated cropping (bet_crop node) if no indiv_params.json are provided. However, the pipeline will give much better results when cropping values are provided.

Here is the different steps on how to compute crop_T1 args:

1. Open the original T1 file with FSLeyes

2. The image should be properly oriented and properly tilted. If not, look at previous sections (label reorient and tilt).

3. Consider the image in the middle (coronal view), and find the lowest value in x where the brain is contained (should be on the L label side, on the right side of the coronal view) and mark the value you see on the top rectangle of "Voxel location".

**N.B. A margin of 5-10 voxels is a good margin to ensure enclosing.**

.. image:: ./img/crop/crop_x_min_mark.png
    :scale: 50%
    :align: center

4. Point on the other side of the coronal view, and mark the highest value enclosing the brain.

.. image:: ./img/crop/crop_x_max_mark.png
    :scale: 50%
    :align: center


**N.B. we advice you to take note as follows: for a given axis, x: xmin xmax xmax-xmin**

For example in the case of the example:

    x: 149 361 361-149=212

5. do the same for the y and z axis, and you end up with the following values:

    x: **149** 361 361-149= **212**

    y: **88** 338 338-88= **250**

    z: **246** 413 413-246= **167**

Then you will be able to fill and individual paramater file (for example called indiv_params.json), following the model:

.. include:: ./img/crop/indiv_params_example.json
   :literal:

**N.B. the values to be added in the args line follow exactly the order of the highlighted parameters in the previous text.It also corresponds to the parameters provided for fslroi (see https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Fslutils for more details)**

The indiv_params.json file can be included in the command line with the -indiv option (see :ref:`indiv_params`. section and :ref:`workflows`. section on how to run command line)

