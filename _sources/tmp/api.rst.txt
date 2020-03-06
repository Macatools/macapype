:orphan:

.. _api_documentation:

=================
API Documentation
=================

Pipelines (:py:mod:`graphpype.pipelines`):

.. currentmodule:: graphpype.pipelines

.. autosummary::
   :toctree: generated/

   create_pipeline_nii_to_conmat
   create_pipeline_nii_to_conmat_seg_template
   create_pipeline_nii_to_conmat_simple
   create_pipeline_nii_to_subj_ROI
   create_pipeline_nii_to_weighted_conmat
   create_pipeline_intmat_to_graph_threshold
   create_pipeline_net_list_to_graph
   create_pipeline_conmat_to_graph_threshold
   create_pipeline_conmat_to_graph_density


Nodes (:py:mod:`graphpype.nodes.graph_stats`):

.. currentmodule:: graphpype.nodes.graph_stats

.. autosummary::
   :toctree: generated/
   
   PrepareCormat
   SwapLists
   ShuffleMatrix
   StatsPairTTest

   
Utils (:py:mod:`graphpype.utils_stats`):

.. currentmodule:: graphpype.utils_stats

.. autosummary::
   :toctree: generated/
   
   compute_pairwise_ttest_fdr
   compute_pairwise_oneway_ttest_fdr
   compute_pairwise_mannwhitney_fdr
   

