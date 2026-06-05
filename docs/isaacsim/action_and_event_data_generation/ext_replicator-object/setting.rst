..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _setting:

============================
Setting
============================

If the key-value pair in the description file is neither a :ref:`mutable` nor a :ref:`harmonizer`, it's a setting. You can define a description with only settings. 

Required Keys
------------------

There are several required keys for settings:

============================ ==================== ==============
Required Key                 Type                 Description
============================ ==================== ==============
output_path                  | string             | The output folders in which folders corresponding to 
                                                  | each :ref:`output switch<Output switches>` are created
num_frames                   | int                | Number of frames to output
screen_width                 | int                | Screen width of output images
screen_height                | int                | Screen height of output images
seed                         | int                | Global randomization seed
version                      | string             | Version number of isaacsim.replicator.object.core
============================ ==================== ==============

.. _Output switches:

.. dropdown:: output_switches 
 
  The setting `output_path` controls what is output to disk per frame. It has these switches:

  ============================ ====================
  Switch                       Data
  ============================ ====================
  images                       | The RGB image of the frame
  labels                       | 2D tight bounding box and the occlusion rate information for each visible tracked object. Each line corresponds to an object, and it has Kitti format ``usd_base_name 0 occlusion 0 x_min y_min x_max y_max 0 0 0 0 0 0 0``
  3d_labels                    | 3D bounding box information stored as Objectron format
  descriptions                 | A description file logging the current state of the scene - Using this file as input description, the same graphics content is output
  segmentation                 | The segmentation mask of tracked mutables
  depth                        | The depth map of the scene, showing the distance to image plane
  normal                       | The normal map of the frame
  ============================ ====================

  Setting a switch to `True` or not setting the switch creates the corresponding folder under ``output_path`` and writes corresponding data into it.

  ``usd_base_name`` is the mutable name or the USD file base name of USD file when a geometry ``mesh`` is loaded, which means it's not allowed to load different USD files with the same base name. Using ``${resource_root_1}/apple.usd`` and ``${resource_root_1}/inner/apple.usd`` in the same simulation causes unexpected behavior.

  For example, an output switch could be:

  .. code:: yaml

    output_switches:
      images: True
      labels: True
      descriptions: True
      3d_labels: True
      segmentation: True
      depth: False

To also write per-frame scene captions alongside this output, the ``Isaacsim.Replicator.Caption`` extension's ``CombinedIROSceneGraphWriter`` can replace the default writer, refer to :ref:`Use Isaacsim.Replicator.Caption in Isaacsim.Replicator.Object <using_iro_extension>`.

Optional Keys
------------------

There are also optional keys, where if not set, have default values:

============================================ ================ ======================= ==============
Optional Keys with Default Value                Type            Default value          Description
============================================ ================ ======================= ==============
parent_config                                | string         | None                  | Specifies the description file that this description file inherits from, in the same parent folder. Values re-defined in the current description file override values defined in parent configs.
path_tracing                                 | bool           | False                 | Render mode selection
inter_frame_time/simulation_time             | numeric        | 0                     | The simulation time between 2 frames
extra_rendering_time                         | numeric        | 0                     | Extra rendering time per frame
output_name                                  | string         | ``$[seed]_$[camera]`` | The output name of a frame that can be customized. Seed, camera, and frame macros are available.
skip_frames_with_no_visible_tracked_mutables | bool           | False                 | If set to true, and if there are no visible tracked mutables in the scene, the frame is skipped
gravity                                      | numeric        | 0                     | Resolves gravity during :ref:`physics resolution stage<simulation workflow>`
friction                                     | numeric        | 1                     | Friction among objects during physics resolution stage. Lower values indicate that the object is more slippery.
linear_damping                               | numeric        | 0                     | Linear damping of objects during physics resolution stage.
angular_damping                              | numeric        | 0                     | Angular damping of objects during physics resolution stage.
occlusion_threshold                          | numeric        | 1                     | If the occlusion of an object is bigger than this threshold, the object will be skipped in the labels.
max_area_threshold                           | numeric        | None                  | If the bounding box area of an object as a percentage of the screen area is bigger than this threshold, the object will be skipped in the labels.
min_area_threshold                           | numeric        | None                  | If the bounding box area of an object as a percentage of the screen area is smaller than this threshold, the object will be skipped in the labels.
============================================ ================ ======================= ==============

**Suggestions and More Information**

.. dropdown:: **path_tracing**

  Turning it on uses the path tracer, which makes simulation slower but image quality higher. Turning it off uses real-time RTX.

.. dropdown:: **inter_frame_time/simulation_time and extra_rendering_time**

  For complex scenes, leave more time for physics resolution and rendering.

.. dropdown:: **output_name**

  Three macros are available: 

  * `$[seed]` evaluates to the seed of the current frame 
  * `$[camera]` evaluates to the camera name
  * `$[frame]` evaluates to the frame index. Refer to `seed` for details.

.. _seed:

.. dropdown:: **$[seed]**

  Each frame is randomized with its own seed, which equals the global seed plus the frame index. For example, if global seed is ``2``, and three images are output, the frame indices for these three images are ``0, 1, 2``; and the seeds are ``2, 3, 4``, respectively.

.. _Physics simulation explained:

.. dropdown:: **Physics simulation explained**

  When objects are randomized in the scene for each frame, they can start at an overlapping position. Resolution of physics de-penetrates these objects. The de-penetration accelerates the objects, such that they can start off with a high speed. Increase linear/angular damping to keep object movement contained.

  However, if linear or angular damping is set too high, objects get lazy and they don't move much. This can be bad in a gravity enabled setting, where we want objects to be in close contact with a surface. Because different objects have different sizes and shapes, it's good to tune these physics properties to reach a good appearance.

  Similarly, too high of a value for friction makes objects cluster if they are in close contact; while too low of a value for friction makes them slippery and glide off surfaces.

  .. note:: If there is no object in the scene when you are expecting some objects, one reason might be that they flew away from the view frustum. Check your physics settings.

