.. note::

   Computation is done in parallel so it's better feeding all needed prims to a single node than creating many nodes with a single prim input if possible.

   Cooking data is cached in memory and on disk to avoid expensive re-computation, by checking the mesh hash.

   This approach improves performance of all other *Compute* and *Generate* Immediate nodes, if this node is executed at the very start of a longer multi-step OmniGraph computation.

.. include:: /prod_extensions/ext_omnigraph/node-library/nodes/custom/phys-x-immediate-demos-common.rst
