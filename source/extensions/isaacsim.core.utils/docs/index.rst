Utilities [isaacsim.core.utils]
##################################

.. automodule:: isaacsim.core.utils._isaac_utils.math
    :platform: Windows-x86_64, Linux-x86_64
    :members:
    :undoc-members:
    :show-inheritance:
    :imported-members:
    :exclude-members: 

.. automodule:: isaacsim.core.utils._isaac_utils.transforms
    :platform: Windows-x86_64, Linux-x86_64
    :members:
    :undoc-members:
    :show-inheritance:
    :imported-members:
    :exclude-members: 

Warp Utils
--------------

Bounds Utils
================

Utils for computing the Axis-Aligned Bounding Box (AABB) and the Oriented Bounding Box (OBB) of a prim.

* The AABB is the smallest cuboid that can completely contain the prim it represents.
  It is defined by the following 3D coordinates: :math:`(x_{min}, y_{min}, z_{min}, x_{max}, y_{max}, z_{max})`.
* Unlike the AABB, which is aligned with the coordinate axes, the OBB can be oriented at any angle in 3D space.

.. automodule:: isaacsim.core.utils.bounds
    :members:
    :undoc-members:
    :exclude-members:

|

Carb Utils
================

Carb settings is a generalized subsystem designed to provide a simple to use interface to Kit's various subsystems,
which can be automated, enumerated, serialized and so on.

The most common types of settings are:

* Persistent (saved between sessions): ``"/persistent/<setting>"``
  |br| (e.g., ``"/persistent/physics/numThreads"``)
* Application: ``"/app/<setting>"`` (e.g., ``"/app/viewport/grid/enabled"``)
* Extension: ``"/exts/<extension>/<setting>"`` (e.g., ``"/exts/omni.kit.debug.python/host"``)

.. automodule:: isaacsim.core.utils.carb
    :members:
    :undoc-members:
    :exclude-members:

Collisions Utils
==================

.. automodule:: isaacsim.core.utils.collisions
    :members:
    :undoc-members:
    :exclude-members:

|

Commands
========
.. automodule:: isaacsim.core.utils.scripts.commands
    :platform: Windows-x86_64, Linux-x86_64
    :members:
    :undoc-members:
    :show-inheritance:
    :imported-members:
    :exclude-members: do, undo

|

Constants Utils
==================

.. automodule:: isaacsim.core.utils.constants
    :members:
    :undoc-members:
    :exclude-members:

Distance Metrics Utils
=======================

.. automodule:: isaacsim.core.utils.distance_metrics
    :members:
    :undoc-members:
    :exclude-members:

|

Extensions Utils
==================

Utilities for enabling and disabling extensions from the Extension Manager and knowing their locations

.. automodule:: isaacsim.core.utils.extensions
    :members:
    :undoc-members:
    :exclude-members:
    

|

Interoperability Utils
========================

Utilities for interoperability between different (ML) frameworks.
|br| Supported frameworks are:

* `Warp <https://nvidia.github.io/warp/index.html>`_
* `PyTorch <https://pytorch.org>`_
* `JAX <https://jax.readthedocs.io/>`_
* `TensorFlow <https://www.tensorflow.org>`_
* `NumPy <https://numpy.org>`_

.. automodule:: isaacsim.core.utils.interops
    :members:
    :undoc-members:
    :exclude-members:

Math Utils
==================

.. automodule:: isaacsim.core.utils.math
    :members:
    :undoc-members:
    :exclude-members:

|

Mesh Utils
==================

.. automodule:: isaacsim.core.utils.mesh
    :members:
    :undoc-members:
    :exclude-members:

|

Physics Utils
==================

.. automodule:: isaacsim.core.utils.physics
    :members:
    :undoc-members:
    :exclude-members:

|

Prims Utils
==================

.. automodule:: isaacsim.core.utils.prims
    :members:
    :undoc-members:
    :exclude-members:

Random Utils
==================

.. automodule:: isaacsim.core.utils.random
    :members:
    :undoc-members:
    :exclude-members:

Render Product Utils
=====================

.. automodule:: isaacsim.core.utils.render_product
    :members:
    :undoc-members:
    :exclude-members:

Rotations Utils
=====================

.. automodule:: isaacsim.core.utils.rotations
    :members:
    :undoc-members:
    :exclude-members:

Semantics Utils
=====================

.. automodule:: isaacsim.core.utils.semantics
    :members:
    :undoc-members:
    :exclude-members:

|

Stage Utils
=====================

.. automodule:: isaacsim.core.utils.stage
    :members:
    :undoc-members:
    :exclude-members:

String Utils
=====================

.. automodule:: isaacsim.core.utils.string
    :members:
    :undoc-members:
    :exclude-members:

Transformations Utils
=======================

.. automodule:: isaacsim.core.utils.transformations
    :members:
    :undoc-members:
    :exclude-members:

Types Utils
=======================

.. automodule:: isaacsim.core.utils.types
    :members:
    :undoc-members:
    :exclude-members:

Viewports Utils
=======================

.. automodule:: isaacsim.core.utils.viewports
    :members:
    :undoc-members:
    :exclude-members:

XForms Utils
=======================

.. automodule:: isaacsim.core.utils.xforms
    :members:
    :undoc-members:
    :exclude-members:

Numpy Utils
--------------

Rotations
================

.. automodule:: isaacsim.core.utils.numpy.rotations
    :members:
    :undoc-members:
    :exclude-members:
    :noindex:

Maths
================

.. automodule:: isaacsim.core.utils.numpy.maths
    :members:
    :undoc-members:
    :exclude-members:
    :noindex:

Tensor
================

.. automodule:: isaacsim.core.utils.numpy.tensor
    :members:
    :undoc-members:
    :exclude-members:
    :noindex:

Transformations
================

.. automodule:: isaacsim.core.utils.numpy.transformations
    :members:
    :undoc-members:
    :exclude-members:
    :noindex:

Torch Utils
--------------

Rotations
================

.. automodule:: isaacsim.core.utils.torch.rotations
    :members:
    :undoc-members:
    :exclude-members:
    :noindex:

Maths
================

.. automodule:: isaacsim.core.utils.torch.maths
    :members:
    :undoc-members:
    :exclude-members:
    :noindex:

Tensor
================

.. automodule:: isaacsim.core.utils.torch.tensor
    :members:
    :undoc-members:
    :exclude-members:
    :noindex:

Transformations
================

.. automodule:: isaacsim.core.utils.torch.transformations
    :members:
    :undoc-members:
    :exclude-members:
    :noindex:

Warp Utils
--------------

Rotations
================

.. automodule:: isaacsim.core.utils.torch.rotations
    :members:
    :undoc-members:
    :exclude-members:
    :noindex:

Tensor
================

.. automodule:: isaacsim.core.utils.torch.tensor
    :members:
    :undoc-members:
    :exclude-members:
    :noindex:

Transformations
================

.. automodule:: isaacsim.core.utils.torch.transformations
    :members:
    :undoc-members:
    :exclude-members:
    :noindex:
