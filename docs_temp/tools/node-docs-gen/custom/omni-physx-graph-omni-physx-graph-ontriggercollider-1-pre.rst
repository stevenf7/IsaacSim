.. image:: /images/omnigraph-phys-x-on-trigger-collider.png
   :alt: On Trigger Node

The **On Trigger Node** is an *Event Node* that can be used as source of events in ActionGraph.

It's a :doc:`Scene Node </prod_extensions/ext_physics/omnigraph-scene-nodes>` so it needs stepping simulation in order to be used.

The node will be listening for all trigger collider *Enter* or *Leave* events on the specified input paths, including both paths from the trigger relationships input and from the trigger paths array input.
Optionally the node can be flagged to listen to all triggers happening on current stage.
The *Enter* execution output will be activated when colliders are entering the trigger volume.
The *Leave* execution output will be activated when colliders are leaving the trigger volume.
Both execution outputs can be connected at the same time for a given node.

.. important::

    The prims that are setup as inputs to this node *MUST* have *Collider* in addition to the *TriggerAPI* or to the  *TriggerStateAPI* applied to it, otherwise no trigger notification will get generated.
    *TriggerAPI* can be applied anywhere a *ColliderAPI* is already applied (the physics add menu is selection context sensitive).
    For example select an existing Mesh or Shape on the stage, right click on it and then Add --> Physics --> *Collider* and after that again right click --> Add --> Physics --> *Trigger*
