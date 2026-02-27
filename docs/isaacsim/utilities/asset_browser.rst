..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_gui_asset_browser:

==========================================
Isaac Sim Asset Browser [Beta]
==========================================


The Isaac Sim Asset Browser allows you to browse and load USD assets into your scene. It is accessible from the **Window > Browser** tab.


.. image:: /images/isim_4.5_base_ref_gui_asset_browser.png
    :width: 900
    :align: center



========== ================================== ============================================================================
Ref #      Function                            Action
========== ================================== ============================================================================
1          Category Menu                      | Click on the category to see the included assets
2          Individual Asset                   | Click **once** to open the left hand option panel; **double click** to directly open the original file; **drag into viewport** to load asset as payload.
3          Load as Reference Button           | Click to load the asset as a reference in the scene
4          Open File Button                   | Click to open the original file in the viewport
5          Variant Options                    | If the USD file contains variants, you can pre-select the variants before loading the asset
6          Search Bar                         | Type to search for assets
7          File Path                          | Shows the file path of the selected asset, hover to see the full path if it is shortened
8          Additional Functions               | Click to see a list of additional functions
9          Option Panel Toggle                | Click to open/close the left hand option panel
========== ================================== ============================================================================



.. _isaac_sim_app_gui_asset_browser_additional_functions:


Notes
=====

The Asset Browser is in Beta and still have some limitations. Here are some known issues:

- It is recommended to use the :ref:`Content Browser <isaac_sim_app_gui_content_browser>` instead of the Isaac Sim Asset Browser.
- When searching, the Asset Browser will search for assets in the current category only. If you want to search for assets in all the categories, make sure click on the **All** category before typing in the search bar.
- Try not to click on other categories while searching, as it will reset the search category and confuse the search results.
- The Asset Browser is currently set to display only USD files. If you wish to see other file types, such as image or text files, you can switch to the :doc:`extensions:ext_core/ext_content-browser` if you have :ref:`isaac_sim_glossary_nucleus` installed. Or run the following snippet in the Script Editor to update the Asset Browser settings. Toggle line 6 and 7 depending on your preference. Consult :ref:`isaac_sim_carb_settings` for more permanent ways to changing Carb settings.
- For non-USD assets, the only available way to view them is to download it to your local computer for now. Use the Download button provided in the panel, or right click on the thumbnail to download.


.. literalinclude:: ../snippets/utilities/asset_browser/notes.py
    :language: python

.. note:: The assets are cached for faster loading, so when you change the settings and restart the extension, the browser will still show the cached assets at first. Clicking on each of the categories will trigger the browser to refresh, show the updated assets, and update the cache accordingly.
