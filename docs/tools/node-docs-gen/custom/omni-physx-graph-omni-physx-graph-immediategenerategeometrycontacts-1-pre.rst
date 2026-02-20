.. image:: /images/omnigraph-physx-immediate-generate-geometry-contacts.png
   :alt: Generate Geometry Contacts Node

**Generate Geometry Contacts** is an :doc:`Immediate Node </prod_extensions/ext_physics/omnigraph-immediate-nodes>` that tests if intersection exists on prims at corresponding indexes into the overlap pairs arrays.

In addition to :doc:`Compute Geometry Overlaps </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediatecomputegeometryoverlaps-1>` this node will generate contacts for the given geometries.


For example given the following overlap pairs arrays:

- ``overlapPairs0`` = [``'/Prim1'``, ``'/Prim2'``]
- ``overlapPairs1`` = [``'/Prim3'``, ``'/Prim4'``]

This node will test:

- ``'/Prim1'`` <--> ``'/Prim3'``
- ``'/Prim2'`` <--> ``'/Prim4'``

Such prims must exist in the prims bundle that passed to the ``primsBundle`` input, otherwise an error will be thrown.

Prims can be supplied to ``primsBundle`` connecting the output of a :doc:`Read Prims </prod_extensions/ext_omnigraph/node-library/nodes/omni-graph-nodes/readprims-3>` node or :doc:`Compute Geometry Bounds </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediatecomputegeometrybounds-1>` node.

The output is an array of booleans where every boolean at a given index returns true if the two prims at the same corresponding index in the ``overlapPairs0`` and ``overlapPairs1`` arrays do actually intersect.

The output is a bundle of child prims named ``prim0`` ... ``primN`` where ``N`` is one minus the length of the ``overlapPairs0`` (or ``overlapPairs1``) array.

It's possible to extract each child bundle output with the :doc:`Extract Prim </prod_extensions/ext_omnigraph/node-library/nodes/omni-graph-nodes/extractprim-1>` node with a *prim path* set to ``prim0`` ... ``primN``.

Each child bundle has the following attributes:

- ``points``: an array of ``float3`` indicating the contact points
- ``normals``: an array of ``float3`` indicating the normals at each corresponding contact point
- ``depths``: an array of ``float`` indicating the penetration depth at each contact point
