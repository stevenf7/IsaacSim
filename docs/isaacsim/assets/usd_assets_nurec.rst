
..
   Copyright (c) 2025, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_assets_nurec:

================================
Neural Volume Rendering
================================

NuRec (Neural Reconstruction) enables scene rendering in |omni| using neural volumes derived from real-world images. These scenes, based on 3D Gaussian models, can be loaded into |isaac-sim_short| as standard USD assets for visualization and simulation.

For more details on how NuRec works in |omni|, including data preparation, rendering settings, and known limitations, see the `NuRec documentation <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/neural-rendering.html>`_. To generate compatible scenes, you can use the open-source project `3DGruT <https://github.com/nv-tlabs/3dgrut>`_ which provides tools for training 3D Gaussian models from image collections and exporting them in a USDZ-based format suitable for use in |omni| applications.

Example
-------

.. figure:: /images/isim_5.0_full_tut_viewport_usd_nurec_assets_carter.webp
    :align: center
    :alt: NuRec Carter NavigationScene

The following example demonstrates how to load a NuRec scene into |isaac-sim_short| and run a simulation. The snippet iterates over the provided examples and starts by loading the provided stage, it then loads the carter navigation asset and sets the start location. It then checks if a collision ground plane needs to be created at the spawn location, and if so, creates a plane prim with a collision API applied. It then sets the carter navigation target prim location and runs the simulation for the given number of steps. During the simulation the wheeled robot will navigate towards the target location.

The example script can be run directly from the :ref:`Script Editor <script-editor>` or as a :ref:`Standalone Application <standalone-application>`.

.. note::

   For correct rendering of NuRec scenes, launch |isaac-sim_short| with ``./isaac-sim.sh --/UJITSO/geometry=true`` or ``./python.sh --/UJITSO/geometry=true``. This option is currently disabled by default.

Prerequisites
##############

* Download the NVIDIA NuRec Dataset from `Hugging Face <https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-NuRec>`_.
* Update the ``USER_PATH`` variable in the script: ``USER_PATH = "/home/user/PhysicalAI-Robotics-NuRec"``

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