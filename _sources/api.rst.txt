:orphan:

.. _api_documentation:

=================
API Documentation
=================

Pipelines
^^^^^^^^^^

Correct bias (:py:mod:`macapype.pipelines.correct_bias`):

.. currentmodule:: macapype.pipelines.correct_bias

.. autosummary::
   :toctree: generated/

    create_correct_bias_pipe
    create_masked_correct_bias_pipe
    create_debias_N4_pipe


Register (:py:mod:`macapype.pipelines.register`):

.. currentmodule:: macapype.pipelines.register

.. autosummary::
   :toctree: generated/

    create_register_NMT_pipe

Brain extraction (:py:mod:`macapype.pipelines.extract_brain`):

.. currentmodule:: macapype.pipelines.extract_brain

.. autosummary::
   :toctree: generated/

    create_extract_pipe


Segment (:py:mod:`macapype.pipelines.segment`):

.. currentmodule:: macapype.pipelines.segment

.. autosummary::
   :toctree: generated/

    create_old_segment_pipe
    create_segment_atropos_pipe


Full segment (:py:mod:`macapype.pipelines.full_pipelines`):

.. currentmodule:: macapype.pipelines.full_pipelines

.. autosummary::
   :toctree: generated/

    create_full_pipelines_pnh_T1xT2
    create_full_pipelines_from_mask_pipe
    create_full_pipelines_pnh_subpipes


Nodes
^^^^^^

Extract brain (:py:mod:`macapype.nodes.extract_brain`):

.. currentmodule:: macapype.nodes.extract_brain

.. autosummary::
   :toctree: generated/

   T1xT2BET


Correct bias (:py:mod:`macapype.nodes.correct_bias`):

.. currentmodule:: macapype.nodes.correct_bias

.. autosummary::
   :toctree: generated/

   T1xT2BiasFieldCorrection


Register (:py:mod:`macapype.nodes.register`):

.. currentmodule:: macapype.nodes.register

.. autosummary::
   :toctree: generated/

   IterREGBET


Preproc (:py:mod:`macapype.nodes.prepare`):

.. currentmodule:: macapype.nodes.prepare

.. autosummary::
   :toctree: generated/

   CropVolume

Utils
^^^^^^

Utils tests (:py:mod:`macapype.utils.utils_tests`):

.. currentmodule:: macapype.utils.utils_tests

.. autosummary::
   :toctree: generated/

   load_test_data
