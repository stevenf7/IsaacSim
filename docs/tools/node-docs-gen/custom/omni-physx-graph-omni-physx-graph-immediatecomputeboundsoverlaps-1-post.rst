.. note::

   Input *Prims Bundle* can be obtained for example using the :doc:`Read Prims </prod_extensions/ext_omnigraph/node-library/nodes/omni-graph-nodes/readprims-3>` node and flagging the **Compute bounding box** boolean option to *True*.

   As an alternative, input *Prims Bundle* can more efficiently obtained by using the :doc:`Read Prims </prod_extensions/ext_omnigraph/node-library/nodes/omni-graph-nodes/readprims-3>` node, with **Compute bounding box** option set to *False* and chain its bundle output to a :doc:`Compute Geometry Bounds </prod_extensions/ext_omnigraph/node-library/nodes/omni-physx-graph/omni-physx-graph-immediatecomputegeometrybounds-1>` node, that will add the required ``bboxMinCorner`` and ``bboxMaxCorner`` attributes.

.. include:: /prod_extensions/ext_omnigraph/node-library/nodes/custom/phys-x-immediate-demos-common.rst
