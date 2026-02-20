.. image:: /images/omnigraph-physx-immediate-compute-mesh-intersecting-faces.png
   :alt: Compute Mesh Intersecting Faces

**Compute Mesh Intersecting Faces** is an:doc:`Immediate Node </prod_extensions/ext_physics/omnigraph-immediate-nodes>` that tests if intersection exists on prims at corresponding indexes into the overlap pairs arrays.

In addition to :doc:`Compute Geometry Overlaps </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediatecomputegeometryoverlaps-1>` this node will return also the actual faces in the mesh in ``overlapPair0`` that intersect the corresponding mesh at the same index in the ``overlapPair1``

.. include:: ../custom/phys-x-immediate-nodes-overlap-pairs-common.rst

Specific output of this node is the *Output Face Indices* bundle. It's possible to extract each child bundle output with the :doc:`Extract Prim </prod_extensions/ext_omnigraph/node-library/nodes/omni-graph-nodes/extractprim-1>` node with a *prim path* set to ``prim0`` ... ``primN``. Each child bundle has the ``faces0`` and ``faces1`` attributes.

Going back to the previous example, extracting the second output (``prim1``) from the *Output Face Indices* with an :doc:`Extract Prim </prod_extensions/ext_omnigraph/node-library/nodes/omni-graph-nodes/extractprim-1>` node, the extracted child bundle will have two outputs, like for example:

- ``faces0`` = [``0``, ``2``, ``4``]
- ``faces1`` = [``2``, ``5``, ``7``]

This output indicates that:

-  face at index ``0`` of ``'/Prim2'`` intersects face at index ``2`` of ``'/Prim4'``
-  face at index ``2`` of ``'/Prim2'`` intersects face at index ``5`` of ``'/Prim4'``
-  face at index ``4`` of ``'/Prim2'`` intersects face at index ``7`` of ``'/Prim4'``
