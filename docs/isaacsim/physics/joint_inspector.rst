..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_physics_joint_inspector:

======================================
Physics Inspector
======================================


Detailed documentation regarding the Physics Inspector can be found `here <https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/extensions/ux/source/omni.physx.supportui/docs/dev_guide/authoring_tools.html#physics-inspector>`_.

Note that the path to enable the Physics Inspector and the Physics Authoring Tool bar described on the page linked above is slightly different than in |isaac-sim_short|. In |isaac-sim_short|, the paths are below:

#. Physics Authoring Toolbar: Tools > Physics Toolbar
#. Physics Inspector: Tools > Physics > Physics Inspector

.. warning::

   Since the Physics Inspector partially initializes ``omni.physx``, it is expected for general simulations to not behave properly.
   Such behaviour can be reversed by simply closing the Physics Inspector window/panel.
