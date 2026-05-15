
..
   Copyright (c) 2025-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_assets_nurec:

================================
Neural Volume Rendering
================================

NuRec (Neural Reconstruction) enables scene rendering in |omni| using neural volumes derived from real-world images.
Compatible environments are published as USD stages that use OpenUSD **ParticleField** geometry (3D Gaussian splats and related radiance fields), which Omniverse RTX renders natively together with polygonal scene content.
For renderer behavior, import guidance, shadows, and color handling for particle fields, see `Gaussian Splats (Particle Fields) <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/particle-fields.html#particle-fields>`_ in the Omniverse Materials and Rendering documentation.

For NuRec-specific data preparation, reconstruction, rendering, and integration with |omni| applications such as |isaac-sim_short|, see the `NVIDIA Omniverse NuRec documentation <https://docs.nvidia.com/nurec/>`_.
To train splats and export **ParticleField** USD stages for |omni|, use the open-source `3DGruT <https://github.com/nv-tlabs/3dgrut>`_ project.

Example
-------

.. figure:: /images/isim_5.0_full_tut_viewport_usd_nurec_assets_carter.webp
    :align: center
    :alt: NuRec Carter NavigationScene

The following examples show how to load a NuRec USD scene into |isaac-sim_short| and run a simulation.
Use ``nurec_carter_script_editor.py`` from the :ref:`Script Editor <script-editor>` or ``nurec_carter.py`` as a :ref:`Standalone Application <standalone-application>`.
Each script iterates over the configured scenarios, opens the stage, loads the Carter navigation asset and sets the start location, optionally creates a collision ground plane at the spawn location, sets the navigation target, and steps the timeline so the wheeled robot drives toward the target.

.. note::

   * Rendering particle fields with DLSS Frame Generation enabled may show visual artifacts. If that happens, disable Frame Generation in Rendering Settings. See `Gaussian Splats (Particle Fields) <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/particle-fields.html#particle-fields>`_.

Prerequisites
##############

* Download the NVIDIA NuRec Dataset from `Hugging Face <https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-NuRec>`_.
* Update the ``USER_PATH`` variable in both scripts: ``USER_PATH = "/home/user/PhysicalAI-Robotics-NuRec"``

.. tab-set::

    .. tab-item:: Script Editor

        .. raw:: html

            <details open>
            <summary>Script Editor</summary>

        .. literalinclude:: ../snippets/assets/usd_assets_nurec/nurec_carter_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Standalone Application

        .. raw:: html

            <details open>
            <summary>Standalone Application</summary>

        .. literalinclude:: ../snippets/assets/usd_assets_nurec/nurec_carter.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

Known Limitations
-----------------

* Opening a ``.usdz`` file as the root stage and then adding another USD asset to it (via **Add Reference**, **Add Payload**, or drag-and-drop into the Stage) fails to load the added asset. The new prim appears empty with its name shown in red. As a workaround, open a ``.usd`` or ``.usda`` file (or create a new stage) as the root stage and reference the ``.usdz`` assets from there. This limitation will be addressed in a future release.
