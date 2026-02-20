Allows triggering other ActionGraph nodes whenever two :doc:`physics bodies </ext_physics/rigid-bodies>` either come, remain or cease to be in contact.

.. note:: This node is based on PhysX Contact Events. For contact between the input body prims and other prims to trigger, the following conditions must be met:

    * Both prims must be :doc:`physics bodies with colliders </ext_physics/rigid-bodies>`.
    * At least one of the two must have the Contact Reporter API applied. Notice however that it does not have to be the physics body specified on the node that carries the API.
    * Simulation must be active.
