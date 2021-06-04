Dynamic Control [omni.isaac.dynamic_control]
######################################################

The Dynamic Control extension provides a set of utilities to control physics objects. 
It provides opaque handles for different physics objects that remain valid between PhysX scene resets, which occur whenever play or stop is pressed.


.. automethod:: omni.isaac.dynamic_control._dynamic_control.acquire_dynamic_control_interface
.. automethod:: omni.isaac.dynamic_control._dynamic_control.release_dynamic_control_interface


.. autoclass:: omni.isaac.dynamic_control._dynamic_control.DynamicControl
    :members:
    :undoc-members:
    :exclude-members: 

Transform and Velocity
======================

.. autoclass:: omni.isaac.dynamic_control._dynamic_control.Transform
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: omni.isaac.dynamic_control._dynamic_control.Velocity
    :members:
    :undoc-members:
    :show-inheritance:



Types
=====

.. autoclass:: omni.isaac.dynamic_control._dynamic_control.ObjectType
    :members:
    :show-inheritance:
    :exclude-members: name

.. autoclass:: omni.isaac.dynamic_control._dynamic_control.DofType
    :members:
    :show-inheritance:
    :exclude-members: name

.. autoclass:: omni.isaac.dynamic_control._dynamic_control.JointType
    :members:
    :show-inheritance:
    :exclude-members: name

.. autoclass:: omni.isaac.dynamic_control._dynamic_control.DriveMode
    :members:
    :show-inheritance:
    :exclude-members: name


Properties
==========

.. autoclass:: omni.isaac.dynamic_control._dynamic_control.RigidBodyProperties
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: omni.isaac.dynamic_control._dynamic_control.DofProperties
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: omni.isaac.dynamic_control._dynamic_control.AttractorProperties
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: omni.isaac.dynamic_control._dynamic_control.D6JointProperties
    :members:
    :undoc-members:
    :show-inheritance:




States
==========

.. autoclass:: omni.isaac.dynamic_control._dynamic_control.RigidBodyState
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: omni.isaac.dynamic_control._dynamic_control.DofState
    :members:
    :undoc-members:
    :show-inheritance:

Constants
=========

Object handles
--------------

.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.INVALID_HANDLE


State Flags
-----------

.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.STATE_NONE
.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.STATE_POS
.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.STATE_VEL
.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.STATE_EFFORT
.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.STATE_ALL


Axis Flags
----------

.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.AXIS_NONE
.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.AXIS_X
.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.AXIS_Y
.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.AXIS_Z
.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.AXIS_TWIST
.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.AXIS_SWING_1
.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.AXIS_SWING_2
.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.AXIS_ALL_TRANSLATION
.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.AXIS_ALL_ROTATION
.. autoattribute:: omni.isaac.dynamic_control._dynamic_control.AXIS_ALL
    