
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.







.. _isaac_assets_overview:

=========================
Isaac Sim Assets
=========================

|isaac-sim_short| provides a variety of assets and robots to help you build your virtual world. Some are made specifically for |isaac-sim_short| and robotics applications,
others are made for other NVIDIA |omni|-based applications. The ones that are available to you by default are all located in the **Window > Browsers** tab.

The :ref:`isaac_sim_app_gui_content_browser` is where you can find all of |isaac-sim_short| assets and files. This includes all of the assets listed below, as well as URDF file, config files, policy binaries, and more.

Sample assets are available for download with the :ref:`isaac_sim_latest_release` of Isaac Sim.
To use this content, you must download the files to the local disk or a |nuc_short| server.
All asset paths below are assumed to be relative to the default asset root path in the `persistent.isaac.asset_root.default` setting. See :ref:`isaac_sim_setup_assets_content_pack`



.. Note::
    Assets will take longer to load when they are accessed for the first time; robots may take multiple minutes to load and larger environment scenes may take as long as ten minutes or more.



Categories
================

.. toctree::
   :maxdepth: 1

   usd_assets_robots
   usd_assets_sensors
   usd_assets_props
   usd_assets_environments
   usd_assets_featured
   usd_assets_third_party
   usd_assets_nurec





Omniverse Activity UI
=====================

The `Omniverse Activity UI <https://docs.omniverse.nvidia.com/kit/docs/omni.activity.ui>`_ allows you to monitor the progress and activities when assets are being loaded.

Enable the ``omni.activity.ui`` extension in the Extension Manager (**Window > Extensions** menu),
or launch Isaac Sim from a terminal with the argument ``--enable omni.activity.ui``.
Then, open the **Activity Progress** window (**Window > Utilities > Activity Progress** menu) before opening or loading the USD asset to monitor its loading progress.

.. image:: /images/isim_6.0_base_ref_gui_asset_browsers.png
    :align: center
    :width: 40%



