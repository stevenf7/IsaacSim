.. note::
   Connecting the output of :doc:`Compute Geometry Bounds </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediatecomputegeometrybounds-1>` node is often a better choice because that node allows precompute mesh hash and cooking data structures at the start of a graph, avoiding such computation at every invocation of this node.

.. note::
   You can use  :doc:`Bundle Inspector </prod_extensions/ext_omnigraph/node-library/nodes/omni-graph-nodes/bundleinspector-3>` to print the content of the contacts bundle output to console to better understand its structure.
