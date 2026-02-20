.. image:: /images/omnigraph-physx-immediate-compute-geometry-bounds.png
   :alt: Compute Geometry Bounds Node

**Compute Geometry Bounds** is an :doc:`Immediate Node </prod_extensions/ext_physics/omnigraph-immediate-nodes>` that takes all Prims in the input bundle and computes their *Axis Aligned Bounding Boxes* (or *AABB*).

The output bundle will contain a pass-through copy of the input bundle with new attributes added (or overwriting them if they already exists with the same name).
The new ``bboxMinCorner`` and ``bboxMaxCorner`` are world space corners of the bounding box for each prim.

This node will also compute the hash of mesh data and cooking data structures needed for most intersection queries, like the ones done by:

- :doc:`Compute Geometry Penetrations </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediatecomputegeometrypenetrations-1>`
- :doc:`Compute Geometry Overlaps </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediatecomputegeometryoverlaps-1>`
- :doc:`Compute Mesh Intersecting Faces </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediatecomputemeshintersectingfaces-1>`.
- :doc:`Generate Geometry Contacts </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediategenerategeometrycontacts-1>`
