..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_replicator_caption:

====================================================================================
VLM Scene Captioning
====================================================================================


Vision-language models (VLMs) rely on paired 
image-caption datasets to learn the complex 
relationships between visual content and textual 
descriptions. Captions provide the semantic 
grounding necessary for models to understand 
objects, actions, and contexts within images. 
High-quality captions are essential for training 
VLMs capable of nuanced scene understanding and reasoning.

Leveraging 3D ground truth from NVIDIA 
Omniverse transforms the captioning process by 
enabling detailed, accurate, and scalable annotations. 
These captions include overall scene descriptions, 
object relationships, and spatial reasoning, such as 
relative positions and interactions between elements in a camera view. 
With 3D metadata, captions can describe not just what 
is visible but how elements are arranged and interact, 
offering richer contextual understanding.

This approach ensures more consistent and diverse 
datasets, allowing VLMs to excel in complex tasks like 
spatial reasoning and scene analysis, ultimately 
bridging the gap between visual and linguistic comprehension.

``Isaacsim.Replicator.Caption.Core`` (IRC) has the following features:

* Generate image-caption pairs for loaded scenes in Omniverse.
* Plug in to other ``Isaacsim.Replicator`` modules, including 
  ``Isaacsim.replicator.object (IRO)`` and ``Isaacsim.replicator.agent (IRA)`` to 
  generate captions for each frame at their runtime.
* Export scene graphs alongside caption outputs for customized postprocessing 
  and caption preparation.

.. image:: /images/isim_5.0_full_ext-isaacsim.replicator.caption-5.0.0_gui_IRC_demo.png 
   :align: center


Python API
##########

IRC provides a Python API (``CaptionAPI``) for programmatic model configuration and caption generation:

.. code-block:: python
   :caption: Setting up the IRC model

   import os
   from isaacsim.replicator.caption.core.api import CaptionAPI

   def setup_irc_model():
       CaptionAPI.set_model_params(
           url="https://integrate.api.nvidia.com/v1",
           name="meta/llama3-8b-instruct",
           key=os.environ.get("NVIDIA_API_KEY", "your_key"),
       )
       print("IRC model params set successfully.")

   setup_irc_model()

After setting up the model, you can generate captions programmatically:

.. code-block:: python
   :caption: Generating captions via the API

   import asyncio
   from isaacsim.replicator.caption.core.api import CaptionAPI

   def on_done(future):
       captions = future.result()
       print(f"Generated captions: {captions}")

   task = asyncio.ensure_future(CaptionAPI.get_captions())
   task.add_done_callback(on_done)

You can also load an IRC configuration file before generating captions:

.. code-block:: python
   :caption: Loading an IRC configuration file

   from isaacsim.replicator.caption.core.api import CaptionAPI

   CaptionAPI.load_config_file("/path/to/irc_config.yaml")


.. _concept_scene_graph:

Workflow
---------

``Isaacsim.Replicator.Caption.Core`` uses the following workflow to generate captions:

.. image:: /images/isim_5.0_full_ext-isaacsim.replicator.caption-5.0.0_gui_IRC_workflow.png
   :align: center

Scene Graph
############

A scene graph is an intermediate output for caption generation. It is
a structured representation of a visual scene, 
where nodes represent objects and edges denote spatial relationships 
between them. It captures how elements are arranged in space, 
such as relative positions and orientations. For example, in 
an image of a person sitting on a bench under a tree, the graph 
would include nodes for "person," "bench," and "tree," with edges 
like "sitting on" and "under." This spatial focus makes scene graphs 
valuable for tasks requiring detailed spatial reasoning and scene analysis.

You can export scene graphs alongside caption outputs to 
enable flexible and customizable management of scene graph data 
for your specific requirements.

.. _enabling_IRC:

Enable `Isaacsim.Replicator.Caption.Core` Extension
---------------------------------------------------
1. Follow the `Omniverse Extension Manager guide <https://docs.omniverse.nvidia.com/extensions/latest/ext_core/ext_extension-manager.html>`_ to enable the ``isaacsim.replicator.caption.core`` extension. 

    * The extension fetches sample assets from Isaac Sim Assets during start. Refer to :doc:`Isaac Sim Assets </assets/usd_assets_overview>` if you encounter issues for loading assets.
    * If loading the UI appears to be hanging, try starting Isaac Sim with the flag ``--/persistent/isaac/asset_root/timeout=1.0``.

2. The IRC UI panel is accessible by **Tools > Action and Event Data Generation > VLM Scene Captioning** and it opens on the right side of the screen.

.. image:: /images/isim_5.0_full_ext-isaacsim.replicator.caption-5.0.0_gui_IRC_start_1.png
    :align: center


IRC can be invoked using the following methods:

* :ref:`Using the UI panel <using_ui_panel>`
* :ref:`Using the IRA extension <using_ira_extension>`
* :ref:`Using the IRO extension <using_iro_extension>`

.. _using_ui_panel:

Using the UI Panel
##################
To launch scene caption generation with the UI panel: 

1. After enabling, the extension will appear in the UI panel: 

   .. image:: /images/isim_5.0_full_ext-isaacsim.replicator.caption-5.0.0_gui_IRC_start_1.png
      :align: center

2. To load the stage USD file, open up the ``Caption Settings`` panel, and then click on the file selector icon.

   .. image:: /images/isim_5.0_full_ext-isaacsim.replicator.caption-5.0.0_gui_IRC_start_2.png
      :align: center

3. Select the USD file you want to caption. There is a default USD file for demonstration.

   .. note::
      | We include an example USD. You can find it in ``[Isaac Sim Assets Path]/Samples/Replicator/Captioning/test_caption.usda``.
      |
      | ``[Isaac Sim Assets Path]`` is the path to :ref:`Isaac Sim Assets<isaac_assets_overview>`
      | Refer to :ref:`Isaac Sim Assets Check<isaac_sim_setup_assets_check>` for how to verify the assets access and how to retrieve the asset path.

   .. image:: /images/isim_5.0_full_ext-isaacsim.replicator.caption-5.0.0_gui_IRC_start_3.png
      :align: center

4. Click on the **Load Scene** button to load the scene.

   .. image:: /images/isim_5.0_full_ext-isaacsim.replicator.caption-5.0.0_gui_IRC_start_4.png
      :align: center

   The stage will be loaded in the stage view. If prompted to enable script execution, click **Yes**.

   .. image:: /images/isim_5.0_full_ext-isaacsim.replicator.caption-5.0.0_gui_IRC_start_5.png
      :align: center

5. Enter the LLM model credentials in the `API key <https://docs.nvidia.com/nim/large-language-models/latest/getting-started.html#generate-an-api-key>`_  field of the **Model Settings** panel; click **Accept** to continue.

   .. image:: /images/isim_5.0_full_ext-isaacsim.replicator.caption-5.0.0_gui_IRC_start_6.png
      :align: center

6. Under the **Caption Settings** panel, enter the desired caption level -- **Brief Caption** for short and **Full Caption** for a more elaborate description. Enter the camera prim path in the **Input Camera Prim Path** field.
   Input the **Output Path** to specify where to save the generated captions, the associated scene graphs, and metadata. Ensure the output path is a valid directory. Click **Generate Scene Graph**.

   .. image:: /images/isim_5.0_full_ext-isaacsim.replicator.caption-5.0.0_gui_IRC_start_7.png
      :align: center

   .. note::

      The default service URL and model name are provided as a convenience. The services are hosted by NVIDIA and provided free of charge on a trial basis.
      If the service associated with the default model is not reachable, a different model can be selected. Examples include:

      * ``meta/llama3-8b-instruct``
      * ``meta/llama3-70b-instruct``
      * ``meta/llama-3.1-405b-instruct``

      It's also possible to obtain the NVIDIA NIMs listed on the `LLM API reference page <https://docs.api.nvidia.com/nim/reference/llm-apis>`_ and host them locally.
      Visit `NVIDIA's NIM page <https://build.nvidia.com>`_ for more details.

7. The scene graph, the caption, and the corresponding images are generated and saved in the output directory.

   .. image:: /images/isim_5.0_full_ext-isaacsim.replicator.caption-5.0.0_gui_IRC_start_8.png
      :align: center

.. note::
   | Focusing on specific regions of interest (ROIs) in a complex scene can be achieved by positioning a camera appropriately.
   |
   | The following steps demonstrate how to generate captions for a region of interest (ROI).


8. To generate captions for a region of interest (ROI), select the desired camera from the camera drop-down as shown below:

   .. image:: /images/isim_6.0_full_ext-isaacsim.replicator.caption-6.0.0_gui_IRC_roi_2.png
      :align: center

9. Position the camera at the desired location so that the ROI dominates the view plane, as shown below:

   .. image:: /images/isim_6.0_full_ext-isaacsim.replicator.caption-6.0.0_gui_IRC_roi_3.png
      :align: center

10. Click on the **Generate Scene Graph** button to generate the captions for the ROI, after selecting the desired caption and output parameters described in earlier steps.

   .. image:: /images/isim_6.0_full_ext-isaacsim.replicator.caption-6.0.0_gui_IRC_roi_4.png
      :align: center


Using the IRA Extension
###############################
To launch scene caption generation with IRA, load the a YAML configuration file. 
Or use the default configuration file that comes with the extension and 
follow the steps below to prepare some environment variables.

The anatomy of an IRC configuration file, used to run the extension
under IRO and IRA, is explained.

1. Prepare the `NVIDIA NIM API key <https://docs.nvidia.com/nim/large-language-models/latest/getting-started.html#generate-an-api-key>`_ 
   for the extension to use. 

   The extension requires NVIDIA NIM AI to generate captions. 
   The credentials must be stored in the environment variables.

   **Linux/Mac:**

   Add to ``~/.bashrc`` or ``~/.bash_profile``:
      
   .. code:: bash

      export NVIDIA_API_KEY=<API_KEY>

   **Windows:**

   Command Prompt:

   .. code:: bat

      set NVIDIA_API_KEY=<API_KEY>

   .. note::

      * The NVIDIA NIM API key has a limited lifetime. The number of free credits is limited and is accessible through the account associated with the API key. After the credits are exhausted, you can apply for more credits through the developer portal. Refer to `the developer forum <https://forums.developer.nvidia.com/t/nim-pricing/290144>`_ for more details.

      * If you only need to generate scene graphs without captions, the AI credentials are not required.

Example ``Isaacsim.Replicator.Caption.Core`` Configuration File  
-----------------------------------------------------------------

For example, a configuration file is similar to the following:

.. code:: yaml

   isaacsim.replicator.caption.core:
      version: 0.6.6
      camera_prim_path: /World/Cameras/Camera
      scene_path: USD_FILE
      caption_configs:
         save_full_scene_graph: true
         save_pruned_scene_graph: true
         attach_label_to_usd: false
         use_ai_label: false
         visualize_caption: true
         max_object_capacity: 100
         export_edges: true
         global_caption: true
         qa_caption: false
         brief_caption: true
         pruning_ratio: 1.0
         verbose: true
         random_seed: 0
         caption_only: false
         export_world: true
      output_path: OUTPUT_PATH


Global Properties
##################
.. dropdown:: version

   The version of IRC extension. If version does not match, the extension will not work.
   
.. dropdown:: camera_prim_path

   The path to the camera prim in the scene. If not provided, the extension uses the default camera path defined in 
   the ``default_config.yaml`` file. However, if there is no camera in the scene, the extension will not work. 
   You must guarantee that the camera is available in the scene.

.. dropdown:: scene_path

   The path to the scene USD file. The extension can load the scene from this path. However, if the ``scene_path`` is
   not provided, the extension uses whatever scene is loaded in the app. If no scene is loaded, the extension will not work.

.. dropdown:: output_path

   The path to the output directory where the generated captions will be saved. If not provided, the extension will use the default output path.


Caption Configurations
#######################
.. dropdown:: save_full_scene_graph

   If True, it will save the full scene graph in the output directory.

   The file will be saved as ``<output_path>/<Camera Prim Name>/Captions/full_scene_graph.json``.

.. dropdown:: save_pruned_scene_graph
   
   If True, it will save the pruned scene graph in the output directory. The full scene graph includes 
   the edges between any two objects at the same level in the Support Tree.

   The file will be saved as ``<output_path>/<Camera Prim Name>/Captions/pruned_scene_graph.json``.

   .. note::

      **Support Tree:** A tree that represents the spatial relationships between objects in the scene.
      The root of the tree is the floor (0th level). The direct children of the root are the objects on the floor, which is considered the 1st level.
      The objects on the 2nd level are the objects supported by the objects on the 1st level, and so on.

.. dropdown:: pruning_ratio
   
   The ratio of the scene graph to be pruned. The scene graph will be pruned to a **Minimum Spanning Tree** (MST).
   The pruning ratio determines the percentage of the MST edges to be kept. For example, if ``pruning_ratio`` is set to ``0.5``,
   the scene graph is pruned to 50% of the MST edges.

   By default, ``pruning_ratio`` is set to ``1.0``, which means the scene graph will not be further pruned after the MST is generated.

.. dropdown:: random_seed
   
   An integer for the random process. When ``pruning_ratio`` is less than ``1.0``, the edges will be 
   randomly removed from the MST. The random seed is used to control the randomness of this process.

.. dropdown:: attach_label_to_usd

   If True, it will attach the automatically generated semantic labels to all prims with an USD address in the scene,
   if the prim does not have a semantic label pre-attached.
   The automatic semantic label is based on the prim path basename. For example, if the prim path is ``/World/Objects/Chair``, 
   the semantic label will be ``Chair``.

   With semantic label attached, Omniverse `annotators <https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator/annotators_details.html#annotators-information>`_ 
   are able to capture the prim for the annotation defined. This is critical for captioning tasks, because prims not 
   captured by annotators cannot be included in the scene graph and therefore will not be captioned.

.. dropdown:: use_ai_label
   
   If True, it will use the AI-generated labels for the prims with semantic labels in the scene. The AI-generated labels 
   are preprocessed and stored in the database, and they will be pulled from the database at runtime. This function can 
   be combined with ``attach_label_to_usd: true`` to handle the case when target prims does not have semantic labels pre-stored 
   in the scene file.

.. dropdown:: visualize_caption

   If True, it will visualize the scene graph on the output images. The visualization will be saved as 
   `<output_path>/<Camera Prim Name>/Captions/vis_camera_scene_graph.jpg`.

.. dropdown:: max_object_capacity

   The maximum number of objects that the scene graph can contain. The objects are selected by their 2D bounding
   box sizes in the camera view in a reverse order.

.. dropdown:: export_edges
   
   If True, the edges of the scene graph will be exported to scene graph files. The edges represent the spatial 
   relationships between objects. 

.. dropdown:: export_world

   If True, the extension will export 3D World locations of the prims in the scene graph, and save them in the scene
   graph files. The 3D World locations are the 3D coordinates of the prims in the world space. If not mentioned, all
   other locations are in the camera space.

.. dropdown:: global_caption

   If True, the extension will generate a global caption for the scene. The global caption describes the overall 
   scene content and context. This will be saved in the output file
   ``<output_path>/<Camera Prim Name>/Captions/scene_graph_caption.json``.

.. dropdown:: qa_caption

   If True, the extension will generate QA captions for the scene. The QA captions are questions and answers 
   that test the model's understanding of the scene.

   This will be saved in the output file
   ``<output_path>/<Camera Prim Name>/Captions/scene_graph_caption.json``.

.. dropdown:: brief_caption
   
   If True, the extension will generate brief captions for the scene. The brief captions are the short version of
   the global caption. This will be saved in the output file
   ``<output_path>/<Camera Prim Name>/Captions/scene_graph_caption.json``.

.. dropdown:: verbose
   
   If True, the extension will print the detailed information of the scene graph generation process, such as the ``support tree``,
   and the number of nodes and edges in the scene graph.

.. dropdown:: caption_only
   
   If True, only the prims whose corresponding USD files have their object caption preprocessed and stored in the database 
   will be included in the scene graph and following caption generation process.


.. _using_ira_extension:

Use IRC in ``Isaacsim.Replicator.Agent``
--------------------------------------------------------------

:ref:`Isaacsim.replicator.agent <isaac_sim_app_tutorial_replicator_character>` (IRA) is a module that generates 
synthetic data on human characters and robots across a variety of 3D environments. With the IRC extension enabled 
in IRA, you can generate captions for each frame at the same time. 

To enable IRC in IRA:

1. In the IRA configuration file, use IRC's ``SceneGraphWriter`` to write the captions to the output directory.

   Example:

   .. code:: yaml

      isaacsim.replicator.agent:
         version: 1.6.0
         simulation_duration: 5
         environment:
            base_stage_asset_path: "Isaac/Samples/Replicator/Captioning/test_caption.usda"
         sensor:
            groups:
               ceiling_cameras:
                  num: 2
                  aim_at_targets:
                     distance_range: [5, 10]
                     height_range: [7, 10]
                     focal_length_range: [10, 15]
                     look_down_angle_range: [30, 45]
         character:
            groups:
               warehouse_workers:
                  asset_path: "Isaac/People/Characters/"
                  num: 5
                  routines:
                  - wander:
                       weight: 1
                       repeat: 1
                       walk:
                          speed_range: [0.8, 1.5]
                          distance_range: [5.0, 10.0]
                       idle:
                          - animation: idle
                            weight: 1
                            time_range: [2.0, 5.0]
         replicator:
            writers:
               SceneGraphWriter:
                  semantic_filter_predicate: "class:*"
                  rgb: true
                  camera_params: true
                  object_info_bounding_box_2d_tight: true
                  object_info_bounding_box_2d_loose: true
                  object_info_bounding_box_3d: true
                  pruning_ratio: 1.0
                  global_caption: true
                  qa_caption: false
                  brief_caption: true
                  visualize_caption: true
                  max_object_capacity: 100
                  export_edges: true
                  save_full_scene_graph: true
                  save_pruned_scene_graph: true
                  export_world: false
                  attach_label_to_usd: false
                  use_ai_label: false
                  verbose: false
                  random_seed: 0
                  caption_only: false
                  scene_graph_interval: 10
                  caption_interval: 10

   The caption output will be stored in the output directory as:

   * pruned scene graph: ``<output_dir>/<Camera Prim Name>/caption_pruned_json/scene_graph_pruned_<frame id>.json``
   * full scene graph: ``<output_dir>/<Camera Prim Name>/caption_full_json/scene_graph_full_<frame id>.json``
   * captions: ``<output_dir>/<Camera Prim Name>/caption/scene_graph_caption_<frame id>.json``

   Below are the other parameters in the ``SceneGraphWriter``:


   .. dropdown:: output_dir

      The path to the output directory where the generated captions as well as IRA outputs will be saved. 
      If not provided, the extension will use the default output path.
   
   .. dropdown:: caption_interval
   
      The interval of the caption generation process. The caption will be generated every ``caption_interval`` frames.
      By default, ``caption_interval`` is set to ``1000``.
   
   .. dropdown:: scene_graph_interval
   
      The interval of the scene graph generation process. The scene graph will be generated every ``scene_graph_interval`` frames.
      By default, ``scene_graph_interval`` is set to ``1``.
   
   .. dropdown:: skip_frames
   
      The number of frames to skip before starting the caption generation process. 
      By default, ``skip_frames`` is set to ``0``.
   
   .. dropdown:: writer_interval
   
      The interval of the writer process. The writer will write the IRA outputs to the output directory every ``writer_interval`` frames.
      By default, ``writer_interval`` is set to ``1``.
   
   .. dropdown:: export_point_cloud
         
      If True, the extension will export the point cloud of the frame. The point cloud will be saved in the output directory because ``<output_dir>/<Camera Prim Name>/pointcloud/pointcloud_<frame id>.npy``. By default, ``export_point_cloud`` is set to False.
   
   .. dropdown:: export_depth
   
      If True, the extension will export the depth map of the frame. The depth map will be saved in the output directory as 
      ``<output_dir>/<Camera Prim Name>/depth/depth_<frame id>.npy``. By default, ``export_depth`` is set to False.

2. Follow the steps in the :ref:`Isaacsim.replicator.agent <isaac_sim_app_tutorial_replicator_character>` tutorial to start the data generation process.

.. _using_iro_extension:

Use IRC in ``Isaacsim.Replicator.Object``
-----------------------------------------

:ref:`Isaacsim.replicator.object <isaac_sim_app_tutorial_replicator_object>` (IRO) is a module that composes scenes that are 
uniquely domain randomized. With the IRC extension enabled in IRC, you can generate captions for each frame at the same time. 

To enable IRC in IRO:

1. In the IRO configuration file, use IRC's ``CombinedIROSceneGraphWriter`` to write the IRO output together with captions 
   to the output directory.

   Example:

   .. code:: yaml

      isaacsim.replicator.object:
         version: 0.x.y
         camera_parameters: ...
         caption_configs:
            save_full_scene_graph: true
            save_pruned_scene_graph: true
            attach_label_to_usd: false
            use_ai_label: false
            visualize_caption: true
            max_object_capacity: 100
            export_edges: true
            caption_only: false
            global_caption: true
            qa_caption: true
            brief_caption: true
            pruning_ratio: 1.0
            verbose: true
            random_seed: 0
            caption_writer: CombinedIROSceneGraphWriter
         output_switches:
            caption: True
            ...
   
   In the ``caption_configs`` field, the configurations are the same as in the IRC configuration file, with
   one additional field ``caption_writer``. 

   .. dropdown:: caption_writer

      The writer to write the captions to the output directory. The available writers are:

      * ``CombinedIROSceneGraphWriter``: This writer combines the IRO outputs with the captions.
      * ``IROSceneGraphWriter``: This writer only writes the captions to the output directory while suppressing other 
         IRO outputs, such as ``labels`` (The 2D detection labels). However, it can generate ``images``, ``distance_to_image_plane`` and ``pointcloud``.
      
   The caption output will be stored in the output directory as:

   * pruned scene graph: ``<output_dir>/caption/caption_pruned_json/<seed>_<camera_name>.json``
   * full scene graph: ``<output_dir>/caption/caption_full_json/<seed>_<camera_name>.json``
   * visualized scene graph: ``<output_dir>/caption_rgb/<seed>_<camera_name>.jpg``
   * captions: ``<output_dir>/<Camera Prim Name>/caption_dict/<seed>_<camera_name>.json``


2. Follow the steps in the :ref:`Isaacsim.replicator.object <isaac_sim_app_tutorial_replicator_object>` tutorial to start the data generation process.

