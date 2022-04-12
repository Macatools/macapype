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

List of indiv params (recap):
*****************************

**N.B. any parameters available in a node can in principle be implemented as a params and indiv_params, please make the request to developers**


Data preparation (ANTS, ANTS_T1, SPM, SPM_T1)
---------------------------------------------

See :ref:`Data preparation <data_prep>`

- "crop" (args) in short_data_preparation, long_single_preparation and long_multi_preparation
- "denoise", "denoise_first" (see `Denoise <https://nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.interfaces.ants.segmentation.html#denoiseimage>`_ for arguments) for long_single_preparation and long_multi_preparation
- "norm_intensity" (see `N4BiasFieldCorrection <https://nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.interfaces.ants.segmentation.html#n4biasfieldcorrection>`_ for arguments) for long_single_preparation and long_multi_preparation

SPM based pipelines (SPM and SPM_T1)
------------------------------------

- "reg" (see :class:`IterREGBET <macapype.nodes.register.IterREGBET>` for arguments)
- "debias" (see :class:`T1xT2BiasFieldCorrection <macapype.nodes.correct_bias.T1xT2BiasFieldCorrection>` for arguments)

old_segment_pipe (SPM and SPM_T1)

- "threshold_gm", "threshold_wm", "threshold_csf" (thresh)

nii_to_mesh_fs_pipe (SPM only))

- "fill_wm" (args)

ANTS based pipelines
--------------------

Brain extraction (ANTS and ANTS_T1):

- "atlas_brex" (see :class:`AtlasBREX <macapype.nodes.extract_brain.AtlasBREX>` for arguments)

Brain segmentation (ANTS and ANTS_T1):

- "norm_intensity "(will be the same args as in Data preparation)
