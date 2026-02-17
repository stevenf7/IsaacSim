.. _updating_extensions:

=====================================
Adding and Updating Extensions Guide
=====================================

This guide explains how to add or update an extension in Omniverse.

Steps to Add an Extension
=========================

Follow these steps to add an extension from a local folder path or a new extension registry.

1. **Open the Extensions Menu**

   Open the menu by navigating to **Window > Extensions**:

   .. image:: ../images/isim_4.5_base_ref_gui_update_extension_menu.png
      :alt: Extensions Menu
      :align: center

2. **Add the Path to the Extension (optional)**

   This step is optional if you have already added the path to the extension in the settings panel. Or if the extension you want to add is already in an existing extension registry.

   Click the dropdown in the top right and select the settings option.

   .. image:: ../images/isim_4.5_base_ref_gui_update_extension_settings_menu.png
      :alt: Settings Menu
      :align: center

   - If you have the extension in a local folder, you can add the path to the extension by clicking the green **+** button in the **Extension Search Paths** section at the top and then typing the full path to the parent folder containing the extension's folder. This path can contain multiple extensions.
   
   - If you want to add a new extension registry, click the green **+** button in the **Extension Registries** section at the bottom and type in the full URL of the extension registry.

   .. image:: ../images/isim_4.5_base_ref_gui_update_extension_settings.png
      :alt: Settings Panel
      :align: center

3. **Search for the Extension**

   In the search bar, type the name of the desired extension. For example, type: 
   
   .. code-block:: text

      omni.kit.window.tests

   you can then select it from the results and click **INSTALL**. 
   
   .. note::

      Custom or non NVIDIA extensions may show up under the **THIRD PARTY** tab

   .. image:: ../images/isim_4.5_base_ref_gui_update_extension_install.png
      :alt: Install Extension
      :align: center

   After installing, click the toggle next to the extension name to enable the extension.

   .. image:: ../images/isim_4.5_base_ref_gui_update_extension_enable.png
      :alt: Enable Extension
      :align: center

Steps to Update an Extension
============================

1. **Open the Extensions Menu**

   Open the menu by navigating to **Window > Extensions**:

   .. image:: ../images/isim_4.5_base_ref_gui_update_extension_menu.png
      :alt: Extensions Menu
      :align: center


2. **Search for the Extension**

   In the search bar, type the name of the desired extension. For example, to update the MJCF importer, type:

   .. code-block:: text

      isaacsim.asset.importer.mjcf

   .. image:: ../images/isim_4.5_base_ref_gui_update_extension_search.png
      :alt: Search Extension
      :align: center

3. **Click the Update Button**

   Once you find the extension, click the **UPDATE** button.

   .. image:: ../images/isim_4.5_base_ref_gui_update_extension_update.png
      :alt: Update Button
      :align: center

.. note::

   For some extensions, it may be required to reload Isaac Sim to properly load the newest version.

