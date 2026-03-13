..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


==================================================
SimReady Content Browser Search Extension Tutorial
==================================================

The Content Browser Search extension offers a preview of upcoming enhancements that let you search for assets using filters and conditions. This tutorial explains how to install, configure, and use these features.

Overview
========

This release includes the **omni.simready.content.browser** UI extension and predefined filters for *name*, *profile*, and *feature*. The extension adds search tools that help you locate SimReady assets using these filters. Upcoming versions will extend this capability with natural‑language, phrase‑based USD search.

Installing SimReady Search Extension 
====================================

The SimReady Search extension will be automatically installed in all future builds. If it is not included in your build, you can manually install it using this procedure:

1. Open the Windows Extensions menu.
2. Search for the **omni.simready.content.browser** extension.
3. Click **Install** to install it.

   .. image:: ../images/isaac_asset_search_0.png
      :alt: Assets Search Menu
      :align: center

When the SimReady Search extension is installed, the Content Browser adds **Assets Search** to the Search dropdown menu. (If is not installed, your only option is **File Search**.)


Configuring SimReady Search Extension 
=====================================

You can configure the SimReady content location URL that the extension uses to search for assets using the following settings:

.. code-block:: toml

   [settings]
   # define the IsaacReady assets URL that the content browser can use advanced asset search in.
   exts."omni.simready.content.browser".content_root_urls = [
       "https://omniverse-content-production.s3-us-west-2.amazonaws.com/SimReady",
       "omniverse://isaac-dev.ov.nvidia.com/Isaac/SimReady"
   ]
   # default content root url index into the content_root_urls list above
   exts."omni.simready.content.browser".default_content_root_url_index = 0



Using SimReady Search Extension
===============================

To Initiate an Asset Search
---------------------------

Open the Search dropdown menu in the Content Browser and select **Assets Search**. This opens an **Asset Search Wizard** on the right.

   .. image:: ../images/isaac_asset_search_1.png
      :alt: Assets Search Wizard
      :align: center

The wizard has input fields for several filter classes, each providing auto-complete or menu-like behavior when selected. All allow multiple items to be entered. You can use **Match Any** or **Match All** to specify different combinations of filters and match conditions.

* **Match Any** lists all assets that match one or more of the filters. Assets that do not match any of the filters are not listed.
* **Match All** lists all assets that match all of the filters. Assets that do not match every filter are not listed.

Example
-------

To illustrate, if you were interested in assets that contain "food" in their name **and** include a **physx** feature, you would:

1. Enter *food* for **Name**.
2. Select **physx** for **Feature**.
3. Select **Match All**.

   .. image:: ../images/isaac_asset_search_2.png
      :alt: Assets Search Results
      :align: center

The Content Browser would list only those assets that satisfy both of these conditions.

Additional References
=====================

- :doc:`Content Browser <content_browser>`









