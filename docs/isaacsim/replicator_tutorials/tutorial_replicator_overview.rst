..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. meta::
    :title: Replicator Tutorials
    :keywords: lang=en isaac isaac-sim replicator sdg synthetic-data-generation

.. _isaac_sim_app_tutorial_replicator_overview:

==========
Overview
==========

|isaac-sim_short| Replicator offers various tools and workflows for synthetic data generation (SDG), with its core functionalities mostly provided by, but not limited to, the :doc:`omni.replicator<extensions:ext_replicator>` extension. This page provides an overview of these tools and extensions, including semantic labeling, sensor visualization, GUI-based data recording, config file-based SDG workflows, and getting started scripts (examples). To enable SDG relevant UI panels you can use the :ref:`Synthetic Data Generation Layout<isaac_sim_app_gui_layouts>`.

The Semantics Schema Editor
----------------------------

The :doc:`Semantics Schema Editor <extensions:ext_replicator/semantics_schema_editor>` is a GUI-based extension that enables you to view, add, edit, or remove semantic labels on prims in a stage. Semantically labeling prims is necessary for annotators like semantic segmentation or bounding boxes to include semantic information in the synthetic data. You can access the editor through **Tools > Replicator > Semantics Schema Editor**. To programmatically label prims in a stage, see the following :ref:`example snippet <apply-semantic-data-on-entire-stage>`.

.. figure:: /images/isim_4.5_replicator_tut_gui_semantics_editor_window.jpg
    :align: center
    :alt: Semantics Schema Editor

.. _the-synthetic-data-visualizer:

The Synthetic Data Visualizer
-------------------------------

.. |visualizer| image:: /images/isim_4.5_replicator_tut_gui_data_visualizer_icon.png
    :width: 30

The :doc:`Synthetic Data Visualizer <extensions:ext_replicator/visualization>` tool enables sensor output visualization directly in the `Viewport` window, it can be accessed using the |visualizer| icon and selecting the desired output formats.

.. figure:: /images/isim_4.5_replicator_tut_gui_data_visualizer_sensors.jpg
    :align: center
    :alt: Synthetic Data Visualizer

.. note::
   * Cross Correspondence visualization requires a specific two-camera setup explained in the Cross Correspondence section of the :doc:`annotator details <extensions:ext_replicator/annotators_details>` page.

The Synthetic Data Recorder
-------------------------------

The :ref:`isaac_sim_app_tutorial_replicator_recorder` is a GUI-based tool that allows you to record synthetic data directly from the editor. It is built on top of ``omni.replicator`` using ``BasicWriter`` as its default writer, it is useful for rapid iterations of synthetic data recordings for testing purposes. You can access the recorder via **Tools > Replicator > Synthetic Data Recorder**.

.. figure:: /images/isim_4.5_replicator_tut_gui_sd_recorder_editor.jpg
    :align: center
    :alt: Synthetic Data Recorder

Replicator YAML
----------------

:doc:`Replicator YAML<extensions:ext_replicator/yaml_workflow>` is a configuration file-based workflow built on top of the Replicator API. It allows you to define randomizations and data capture pipelines as configuration files. These configurations are transformed through the Replicator API into an :doc:`OmniGraph<extensions:ext_omnigraph>` workflow for synthetic data generation. You can access the YAML workflow using **Tools > Replicator > Replicator YAML**.

Getting Started Scripts
------------------------

The :ref:`isaac_sim_app_tutorial_replicator_getting_started` provides a starting point for typical |isaac-sim_short| Replicator workflows. These tutorials cover basic topics such as accessing data from :doc:`annotators<extensions:ext_replicator/annotators_details>` or :doc:`writers<extensions:ext_replicator/writer_examples>`, and using Replicator randomizers together with custom USD/|isaac-sim_short| API randomizers triggered independently from the data capture.