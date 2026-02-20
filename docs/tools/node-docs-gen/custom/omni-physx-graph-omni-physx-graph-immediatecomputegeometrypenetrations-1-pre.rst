.. image:: /images/omnigraph-physx-immediate-compute-geometry-penetrations.png
   :alt: Compute Geometry Penetrations Node

**Compute Geometry Penetrations** is an :doc:`Immediate Node </prod_extensions/ext_physics/omnigraph-immediate-nodes>` that tests if intersection exists on prims at corresponding indexes into the overlap pairs arrays.

In addition to :doc:`Compute Geometry Overlaps </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediatecomputegeometryoverlaps-1>` this node will return also penetration depth and penetration vector.

.. include:: ../custom/phys-x-immediate-nodes-overlap-pairs-common.rst

Penetration specific outputs could be for example:

- ``penetrationDepths`` = [``0``, ``0.5``]
- ``penetrationVectors`` = [``[0, 0, 0]``, ``[0, 0, 1.0]``]
