.. image:: /images/omnigraph-physx-immediate-compute-bounds-overlaps.png
   :alt: Compute Bounds Overlaps Node

**Compute Bounds Overlap** is an :doc:`Immediate Node </prod_extensions/ext_physics/omnigraph-immediate-nodes>` that takes a set of *Axis Aligned Bounding Boxes* (*AABB* s) and can quickly find pairs of them that intersect each other.

This node can be used as a fast filter to avoid doing unnecessary and more expensive intersection tests, like for example the ones done by:

- :doc:`Compute Geometry Penetrations </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediatecomputegeometrypenetrations-1>`
- :doc:`Compute Geometry Overlaps </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediatecomputegeometryoverlaps-1>`
- :doc:`Compute Mesh Intersecting Faces </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediatecomputemeshintersectingfaces-1>`.
- :doc:`Generate Geometry Contacts </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediategenerategeometrycontacts-1>`.

The input *Prims Bundle* can be an arbitrary number of child prim bundles with bounding box min and max attributes.
