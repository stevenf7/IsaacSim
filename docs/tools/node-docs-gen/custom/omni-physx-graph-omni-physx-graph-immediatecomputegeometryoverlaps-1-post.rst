.. note::
   Connecting the output of :doc:`Compute Geometry Bounds </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediatecomputegeometrybounds-1>` node is often a better choice because that node allows precompute mesh hash and cooking data structures at the start of a graph, avoiding such computation at every invocation of this node.

.. include:: /prod_extensions/ext_omnigraph/node-library/nodes/custom/phys-x-immediate-demos-common.rst
