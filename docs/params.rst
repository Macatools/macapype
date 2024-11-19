.. _params:

Parameters
__________

Adding -params
**************

All the params spefications are in each function of the API, as well the spefications available for :ref:`Individual Parameters <indiv_params>`.

**N.B. in the newest version of macapype, the -params can be replaced the option -species followed by the NHP species corresponding to the image, e.g. {macaque | marmo | baboon | chimp}, and a default parameter, tested for this species, will be used. It is however still possible to use the -params option and provide a params.json for advanced users**

Here is an example of the params.json corresponding to :class:`segment_pnh_spm_based pipeline <macapype.pipelines.full_pipelines.create_full_spm_subpipes>` for macaque:

.. include:: ../workflows/params_segment_macaque_ants.json
   :literal:

Advanced parameters settings
****************************
   TODO: all available nodes / pipelines
