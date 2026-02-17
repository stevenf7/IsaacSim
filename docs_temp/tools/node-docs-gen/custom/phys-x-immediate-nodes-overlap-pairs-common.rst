For example given the following overlap pairs arrays:

- ``overlapPairs0`` = [``'/Prim1'``, ``'/Prim2'``]
- ``overlapPairs1`` = [``'/Prim3'``, ``'/Prim4'``]

This node will test:

- ``'/Prim1'`` <--> ``'/Prim3'``
- ``'/Prim2'`` <--> ``'/Prim4'``

Such prims must exist in the prims bundle that passed to the ``primsBundle`` input, otherwise an error will be thrown.

Prims can be supplied to ``primsBundle`` connecting the output of a :doc:`Read Prims </prod_extensions/ext_omnigraph/node-library/nodes/omni-graph-nodes/readprims-3>` node or :doc:`Compute Geometry Bounds </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediatecomputegeometrybounds-1>` node.

The output is an array of booleans where every boolean at a given index returns true if the two prims at the same corresponding index in the ``overlapPairs0`` and ``overlapPairs1`` arrays do actually intersect.

So looking at the previous example if only ``'/Prim2'`` overlaps with ``'/Prim4'`` then the overlaps will be:

- ``overlaps`` = [``false``, ``true``]
