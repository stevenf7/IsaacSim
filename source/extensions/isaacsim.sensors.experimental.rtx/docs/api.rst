Python API
==========

.. warning::

    **The API featured in this extension is experimental and subject to change without deprecation cycles.**
    Although we will try to maintain backward compatibility in the event of a change, it may not always be possible.

.. Summary

The following table summarizes the available sensors.

.. currentmodule:: isaacsim.sensors.experimental.rtx

.. rubric:: sensors
.. autosummary::
    :nosignatures:

    RtxLidarSensor

.. rubric:: utils
.. autosummary::
    :nosignatures:

    parse_generic_model_output_data
    parse_stable_id_map_data

.. rubric:: lidar configuration
.. autosummary::
    :nosignatures:

    SUPPORTED_LIDAR_CONFIGS
    SUPPORTED_LIDAR_VARIANT_SET_NAME

Sensors
"""""""

.. autoclass:: isaacsim.sensors.experimental.rtx.RtxLidarSensor
    :members:
    :undoc-members:
    :inherited-members:
    :show-inheritance:

Utils
"""""

.. autofunction:: isaacsim.sensors.experimental.rtx.parse_generic_model_output_data

.. autofunction:: isaacsim.sensors.experimental.rtx.parse_stable_id_map_data

Lidar configuration registry
""""""""""""""""""""""""""""

.. py:data:: SUPPORTED_LIDAR_CONFIGS

   Mapping from known Isaac Sim lidar asset paths to optional variant name sets.

.. py:data:: SUPPORTED_LIDAR_VARIANT_SET_NAME

   Variant set name expected on supported lidar prims.
