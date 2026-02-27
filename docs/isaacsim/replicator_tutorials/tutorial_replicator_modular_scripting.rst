..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_tutorial_replicator_modular_scripting:

===========================
Modular Behavior Scripting
===========================

Overview
--------

This tutorial introduces the ``isaacsim.replicator.behavior`` extension, providing multiple examples of modular behavior scripts in |isaac-sim_short| Replicator for synthetic data generation (SDG). By utilizing `Behavior Scripts (Python Scripting Component) <https://docs.omniverse.nvidia.com/extensions/latest/ext_python-scripting-component/user_manual.html>`_, reusable, shareable, and easily modifiable behaviors can be developed and attached to prims in a USD stage, acting as randomizers or custom smart-asset behaviors.

The behavior script examples can be found under:

``/exts/isaacsim.replicator.behavior/isaacsim/replicator/behavior/behaviors/*``

Learning Objectives
####################

After completing this tutorial, you will understand how to:

* **Use pre-built behavior scripts** for common synthetic data generation tasks, including:

  * **Location Randomizer** - randomizes prim positions within specified bounds for object placement variety
  * **Rotation Randomizer** - applies random rotations to enhance orientation diversity in datasets
  * **Look At Behavior** - makes prims continuously face target locations or other prims for camera tracking
  * **Light Randomizer** - randomizes light properties like color and intensity to simulate different lighting conditions
  * **Texture Randomizer** - applies random textures to materials for increased visual variety
  * **Volume Stack Randomizer** - uses physics simulation to randomly stack objects for realistic arrangements

* **Understand behavior script architecture** - how modular Python scripts attach to prims and can be customized through exposed USD attributes, with configurable parameters like update intervals and randomization ranges

* **Control behavior execution** - configure behaviors to run on timeline events (start, update, stop) or trigger them independently using custom events for advanced workflows

* **Create custom behavior scripts** - develop your own behaviors using the provided templates and base classes for specific synthetic data generation needs

* **Build complex SDG pipelines** - combine multiple behaviors, simulations, and events to create sophisticated data generation workflows, such as physics-based object stacking followed by automated data capture

Prerequisites
#############

It is recommended that you have a basic understanding of the following concepts before proceeding with the tutorial:

* USD and |isaac-sim_short| APIs for creating and manipulating USD stages
* `Python Scripting Component <https://docs.omniverse.nvidia.com/extensions/latest/ext_python-scripting-component/user_manual.html>`_ in |isaac-sim_short|
* The :doc:`timeline <extensions:ext_animation-timeline>` and `custom events <https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/guide/events.html>`_ system
* :doc:`omni.replicator <extensions:ext_replicator>` and its |isaac-sim_short| :ref:`tutorials <isaac_sim_app_tutorial_replicator_getting_started>` for synthetic data generation
* :doc:`Writers <extensions:ext_replicator/writer_examples>` and :doc:`annotators <extensions:ext_replicator/annotators_details>` for data capture
* Running scripts using the :doc:`Script Editor <extensions:ext_script-editor>` to setup and run pipelines

Demonstration
##############

The :ref:`example section <isaac_sim_app_tutorial_replicator_modular_scripting_example>` provides a demonstration of how to use the behavior scripts to create a custom synthetic data generation pipeline:

.. image:: /images/isim_4.5_replicator_tut_viewport_behavior_scripts_sdg.webp
    :height: 230px
    :alt: Behavior script-based SDG

.. image:: /images/isim_4.5_replicator_tut_viewport_behavior_scripts_capture.jpg
    :height: 230px
    :alt: Data from the behavior script-based SDG

Behavior Scripts
################

**Behavior Scripts** are modular Python scripts attached to prims in a USD stage. By default, they include template code that responds to timeline events such as start, pause, stop, and update. These scripts define specific behaviors or randomizations applied to prims during simulation or data generation. 

Attaching scripts directly to prims integrates the behaviors into the USD, making them modular because scripts can be easily attached, detached, or swapped on prims without altering core logic. They are sharable because behaviors can be embedded within assets and shared across different projects or stages. 

They are configurable because variables can be exposed through USD attributes for customization without modifying the script code. Additionally, they are persistent; because scripts reside on the prims, they persist with the USD stage and can be versioned and managed accordingly.

The advantages of behavior scripts include reusability, allowing them to be written once and reused across multiple prims or projects. They offer encapsulation by containing behavior logic within the prims, reducing external dependencies. They provide interactivity because parameters can be adjusted through the UI, enabling modifications without programming. Finally, they ensure integration by becoming an integral part of the asset, which maintains consistency across different environments.

.. figure:: /images/isim_4.5_replicator_tut_gui_behavior_scripts_variables.jpg
    :align: center
    :alt: Behavior Scripts with Exposed Variables

Exposing Variables Through USD Attributes
#########################################

To enhance flexibility and accessibility, the input parameters in the provided behavior scripts examples can be exposed as USD attributes on prims. This approach allows you to modify behavior parameters directly from the UI without altering the script code.

The benefits of exposing variables include customization, interactivity, and consistency. Parameters such as target locations, ranges, or other settings can be adjusted per prim instance, using the UI to tweak behaviors and observe immediate effects, while maintaining a uniform interface for modifying behaviors across different scripts.

The exposed variables are implemented using the USD API to create custom attributes with appropriate namespaces on the prim. These attributes are then read by the behavior scripts during execution to adjust their logic accordingly.

The UI implementation for exposing the variables is done in ``isaacsim.replicator.behavior.ui``. It extends the **Property** panel of the selected prims in the stage with a custom section for the exposed variables. The UI is automatically generated based on the exposed variables defined in the behavior script, displaying them as editable fields in the generated widget.

**Example of Exposed Variables Definition:**

.. code-block:: python

    VARIABLES_TO_EXPOSE = [
        {
            "attr_name": "targetLocation",
            "attr_type": Sdf.ValueTypeNames.Vector3d,
            "default_value": Gf.Vec3d(0.0, 0.0, 0.0),
            "doc": "The 3D vector specifying the location to look at.",
        },
        {
            "attr_name": "targetPrimPath",
            "attr_type": Sdf.ValueTypeNames.String,
            "default_value": "",
            "doc": "The path of the target prim to look at. If specified, it has priority over the target location.",
        },
        # Additional variables...
    ]

Custom Event-Based Behavior Scripts
###################################

While behavior scripts are timeline-based by default, some behaviors need to operate independently of the simulation timeline. **Event-based scripting** allows behaviors to be triggered by `custom events <https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/guide/events.html>`_, providing greater control over when and how they execute. This is achieved by skipping the default behavior functions and instead listening to and publishing custom events.

Custom events are defined and managed within Omniverse using an event bus system, enabling scripts to publish or subscribe to these events and facilitating communication between different components or behaviors.

Event-based scripting offers flexibility by allowing customization of when behaviors are executed, independent of the simulation timeline. It enhances modularity by decoupling behaviors from the core simulation loop, making them more modular. Additionally, it improves scalability by managing complex workflows through orchestrating multiple behaviors via events.

For example, the `volume_stack_randomizer.py` script randomizes the stacking of objects by simulating physics before the simulation starts. By using custom events, behaviors can be triggered before the simulation, execution flow can be controlled by starting, stopping, or resetting behaviors based on specific events rather than timeline updates, and performance can be enhanced by avoiding unnecessary computations during each simulation frame through decoupling certain behaviors.


Script Examples
---------------

In this section, various behavior scripts available in the ``isaacsim.replicator.behavior`` extension are explored. Each script provides specific functionality that can enhance synthetic data generation workflows. The scripts are designed to be modular, reusable, and customizable through exposed variables.

The folder path for the behavior scripts is:

``/exts/isaacsim.replicator.behavior/isaacsim/replicator/behavior/behaviors/*``


Location Randomizer
###################

The ``location_randomizer.py`` script randomizes the location of prims within specified bounds during runtime, providing position variability for enhanced synthetic datasets.

.. tab-set::

    .. tab-item:: Overview

        **Purpose:** Randomizes prim positions within defined bounds to create variety in object placement.

        **Key Features:**

        * Position range randomization within minimum and maximum bounds
        * Relative positioning support using target prims as reference points
        * Child prim inclusion for hierarchical randomization
        * Configurable update intervals for performance control

        **Exposed Variables:**

        .. raw:: html

            <details open>
            <summary>Configuration Parameters</summary>

        * **range:minPosition** (`Vector3d`): Minimum position bounds for randomization
        * **range:maxPosition** (`Vector3d`): Maximum position bounds for randomization  
        * **frame:useRelativeFrame** (`Bool`): Enable relative positioning mode
        * **frame:targetPrimPath** (`String`): Reference prim path for relative positioning
        * **includeChildren** (`Bool`): Include child prims in randomization
        * **interval** (`UInt`): Update frequency (0 = every frame)

        .. raw:: html

            </details>

    .. tab-item:: Implementation Details

        **Child Prim Inclusion:**

        .. raw:: html

            <details open>
            <summary>Child Prim Selection Logic</summary>

        .. code-block:: python

            def _setup(self):
                include_children = self._get_exposed_variable("includeChildren")
                if include_children:
                    self._valid_prims = [prim for prim in Usd.PrimRange(self.prim) if prim.IsA(UsdGeom.Xformable)]
                elif self.prim.IsA(UsdGeom.Xformable):
                    self._valid_prims = [self.prim]
                else:
                    self._valid_prims = []
                    carb.log_warn(f"[{self.prim_path}] No valid prims found.")

        * When **includeChildren** is `True`: Uses `Usd.PrimRange` to select all transformable descendant prims
        * When **includeChildren** is `False`: Only includes the assigned prim if it's transformable
        * Logs warning if no valid prims are found

        .. raw:: html

            </details>

        **Randomization Logic:**

        .. raw:: html

            <details open>
            <summary>Core Randomization Implementation</summary>

        .. code-block:: python

            def _randomize_location(self, prim):
                # Generate random offset within bounds
                random_offset = Gf.Vec3d(
                    random.uniform(self._min_position[0], self._max_position[0]),
                    random.uniform(self._min_position[1], self._max_position[1]),
                    random.uniform(self._min_position[2], self._max_position[2]),
                )

                # Calculate final location based on target prim and relative frame settings
                if self._target_prim:
                    target_loc = get_world_location(self._target_prim)
                    loc = (
                        target_loc + self._target_offsets[prim] + random_offset
                        if self._use_relative_frame
                        else target_loc + random_offset
                    )
                else:
                    loc = self._initial_locations[prim] + random_offset if self._use_relative_frame else random_offset

                self._set_location(prim, loc)

        * Generates random offset within specified bounds
        * Handles target prim relative positioning
        * Applies relative frame calculations when enabled
        * Updates prim location using internal API

        .. raw:: html

            </details>

    .. tab-item:: Usage Example

        **Basic Setup:**

        .. raw:: html

            <details open>
            <summary>Step-by-Step Configuration</summary>

        1. **Attach Script**: Add `location_randomizer.py` to your target prim
        2. **Set Bounds**: Configure `range:minPosition` and `range:maxPosition`
        3. **Enable Children**: Set `includeChildren` to `True` for hierarchical randomization
        4. **Set Interval**: Use `interval` to control update frequency

        **Example Configuration:**

        * **range:minPosition**: `(-5.0, -5.0, 0.0)`
        * **range:maxPosition**: `(5.0, 5.0, 2.0)`
        * **includeChildren**: `True`
        * **interval**: `5` (updates every 5 frames)

        .. raw:: html

            </details>

        **Use Cases:**

        * **Background Objects**: Randomize prop positions for scene variety
        * **Relative Positioning**: Move objects relative to a moving target
        * **Hierarchical Randomization**: Apply randomization to object groups


Rotation Randomizer
###################

The ``rotation_randomizer_1.py`` script applies random rotations to prims during runtime, enhancing orientation diversity in synthetic datasets.

.. tab-set::

    .. tab-item:: Overview

        **Purpose:** Applies random rotations to prims within specified Euler angle bounds.

        **Key Features:**

        * Rotation range randomization within minimum and maximum angle bounds
        * Child prim inclusion for hierarchical rotation randomization
        * Configurable update intervals for performance optimization

        **Exposed Variables:**

        .. raw:: html

            <details open>
            <summary>Configuration Parameters</summary>

        * **range:minRotation** (`Vector3d`): Minimum rotation angles in degrees (X, Y, Z)
        * **range:maxRotation** (`Vector3d`): Maximum rotation angles in degrees (X, Y, Z)
        * **includeChildren** (`Bool`): Include child prims in rotation randomization
        * **interval** (`UInt`): Update frequency (0 = every frame)

        .. raw:: html

            </details>

    .. tab-item:: Implementation Details

        **Child Prim Selection:**

        .. raw:: html

            <details open>
            <summary>Child Prim Selection Logic</summary>

        .. code-block:: python

            def _setup(self):
                include_children = self._get_exposed_variable("includeChildren")
                if include_children:
                    self._valid_prims = [prim for prim in Usd.PrimRange(self.prim) if prim.IsA(UsdGeom.Xformable)]
                elif self.prim.IsA(UsdGeom.Xformable):
                    self._valid_prims = [self.prim]
                else:
                    self._valid_prims = []
                    carb.log_warn(f"[{self.prim_path}] No valid prims found.")

        * When **includeChildren** is `True`: All transformable descendant prims are included
        * When **includeChildren** is `False`: Only the assigned prim is considered if transformable
        * Warning logged if no valid prims found

        .. raw:: html

            </details>

        **Rotation Randomization:**

        .. raw:: html

            <details open>
            <summary>Core Rotation Implementation</summary>

        .. code-block:: python

            def _randomize_rotation(self, prim):
                rotation = (
                    Gf.Rotation(Gf.Vec3d.XAxis(), random.uniform(self._min_rotation[0], self._max_rotation[0]))
                    * Gf.Rotation(Gf.Vec3d.YAxis(), random.uniform(self._min_rotation[1], self._max_rotation[1]))
                    * Gf.Rotation(Gf.Vec3d.ZAxis(), random.uniform(self._min_rotation[2], self._max_rotation[2]))
                )
                set_rotation_with_ops(prim, rotation)

        * Generates random Euler angles within specified bounds for each axis
        * Creates composite rotation by multiplying X, Y, and Z axis rotations
        * Applies rotation using `set_rotation_with_ops` for proper transformation handling

        .. raw:: html

            </details>

    .. tab-item:: Usage Example

        **Basic Setup:**

        .. raw:: html

            <details open>
            <summary>Step-by-Step Configuration</summary>

        1. **Attach Script**: Add `rotation_randomizer_1.py` to your target prim
        2. **Set Rotation Bounds**: Configure `range:minRotation` and `range:maxRotation`
        3. **Enable Children**: Set `includeChildren` to `True` for hierarchical rotation
        4. **Set Interval**: Use `interval` to control update frequency

        **Example Configuration:**

        * **range:minRotation**: `(-180.0, -90.0, 0.0)` degrees
        * **range:maxRotation**: `(180.0, 90.0, 360.0)` degrees
        * **includeChildren**: `True`
        * **interval**: `10` (updates every 10 frames)

        .. raw:: html

            </details>

        **Use Cases:**

        * **Object Variety**: Randomize prop orientations for diverse scenes
        * **Tumbling Effects**: Simulate falling or floating objects
        * **Presentation Angles**: Vary object viewing angles for training data


Look At Behavior
#################

The ``look_at_behavior.py`` script orients prims to continuously face a specified target, ideal for camera tracking and sensor alignment.

.. tab-set::

    .. tab-item:: Overview

        **Purpose:** Orients prims to continuously face a target location or another prim.

        **Key Features:**

        * Target specification using fixed coordinates or dynamic prim tracking
        * Up axis control for maintaining consistent orientation
        * Child prim inclusion for hierarchical look-at behavior
        * Configurable update intervals for performance control

        **Exposed Variables:**

        .. raw:: html

            <details open>
            <summary>Configuration Parameters</summary>

        * **targetLocation** (`Vector3d`): Fixed 3D coordinates to look at
        * **targetPrimPath** (`String`): Path to target prim (overrides targetLocation)
        * **upAxis** (`Vector3d`): Up axis for orientation (e.g., `(0, 0, 1)` for +Z)
        * **includeChildren** (`Bool`): Include child prims in look-at behavior
        * **interval** (`UInt`): Update frequency (0 = every frame)

        .. raw:: html

            </details>

    .. tab-item:: Implementation Details

        **Target Prim Handling:**

        .. raw:: html

            <details open>
            <summary>Target Prim Resolution</summary>

        .. code-block:: python

            def _setup(self):
                target_prim_path = self._get_exposed_variable("targetPrimPath")
                if target_prim_path:
                    self._target_prim = self.stage.GetPrimAtPath(target_prim_path)
                    if not self._target_prim or not self._target_prim.IsValid() or not self._target_prim.IsA(UsdGeom.Xformable):
                        self._target_prim = None
                        carb.log_warn(f"[{self.prim_path}] Invalid target prim path: {target_prim_path}")

        * **targetPrimPath** takes precedence over **targetLocation** when specified
        * Validates target prim exists and is transformable
        * Logs warning if target prim is invalid

        .. raw:: html

            </details>

        **Orientation Calculation:**

        .. raw:: html

            <details open>
            <summary>Look-At Rotation Implementation</summary>

        .. code-block:: python

            def _apply_behavior(self):
                target_location = self._get_target_location()
                for prim in self._valid_prims:
                    eye = get_world_location(prim)
                    if (target_location - eye).GetLength() < 1e-9:
                        continue  # Already at target; skip rotation to avoid undefined look-at
                    look_at_rotation = calculate_look_at_rotation(eye, target_location, self._up_axis)
                    set_rotation_with_ops(prim, look_at_rotation)

        * Retrieves current prim position using `get_world_location`
        * Calculates required rotation using `calculate_look_at_rotation`
        * Applies rotation while preserving existing transformation operations

        .. raw:: html

            </details>

    .. tab-item:: Usage Example

        **Basic Setup:**

        .. raw:: html

            <details open>
            <summary>Step-by-Step Configuration</summary>

        1. **Attach Script**: Add `look_at_behavior.py` to your camera or sensor prim
        2. **Set Target**: Configure either `targetLocation` or `targetPrimPath`
        3. **Adjust Up Axis**: Set `upAxis` to maintain desired orientation
        4. **Set Interval**: Use `interval` to control update frequency

        **Example Configuration:**

        * **targetPrimPath**: `/World/MovingObject/Prim`
        * **upAxis**: `(0, 0, 1)` (Z-up orientation)
        * **includeChildren**: `False` (camera only)
        * **interval**: `1` (update every frame)

        .. raw:: html

            </details>

        **Use Cases:**

        * **Camera Tracking**: Make cameras follow moving subjects
        * **Sensor Alignment**: Point sensors at targets of interest
        * **Lighting Direction**: Orient lights to follow objects


Light Randomizer
################

The ``light_randomizer.py`` script randomizes light properties to simulate different lighting conditions for enhanced scene variability.

.. tab-set::

    .. tab-item:: Overview

        **Purpose:** Randomizes light color and intensity properties to create diverse lighting scenarios.

        **Key Features:**

        * Color randomization varying RGB values within specified ranges
        * Intensity randomization adjusting brightness between minimum and maximum values
        * Child light inclusion for hierarchical lighting randomization
        * Configurable update intervals for performance optimization

        **Exposed Variables:**

        .. raw:: html

            <details open>
            <summary>Configuration Parameters</summary>

        * **includeChildren** (`Bool`): Include child light prims in randomization
        * **interval** (`UInt`): Update frequency (0 = every frame)
        * **range:minColor** (`Color3f`): Minimum RGB values for color randomization
        * **range:maxColor** (`Color3f`): Maximum RGB values for color randomization
        * **range:intensity** (`Float2`): Intensity range as (min, max) values

        .. raw:: html

            </details>

    .. tab-item:: Implementation Details

        **Light Property Randomization:**

        .. raw:: html

            <details open>
            <summary>Color and Intensity Randomization</summary>

        .. code-block:: python

            def _apply_behavior(self):
                for prim in self._valid_prims:
                    rand_color = (
                        random.uniform(self._min_color[0], self._max_color[0]),
                        random.uniform(self._min_color[1], self._max_color[1]),
                        random.uniform(self._min_color[2], self._max_color[2]),
                    )
                    prim.GetAttribute("inputs:color").Set(rand_color)

                    rand_intensity = random.uniform(self._intensity_range[0], self._intensity_range[1])
                    prim.GetAttribute("inputs:intensity").Set(rand_intensity)

        * Generates random RGB values within specified color ranges
        * Applies random intensity values within defined bounds
        * Updates light attributes directly using USD API

        .. raw:: html

            </details>

        **Child Light Selection:**

        .. raw:: html

            <details open>
            <summary>Light Prim Discovery</summary>

        .. code-block:: python

            def _setup(self):
                include_children = self._get_exposed_variable("includeChildren")
                if include_children:
                    self._valid_prims = [prim for prim in Usd.PrimRange(self.prim) if prim.HasAPI(UsdLux.LightAPI)]
                elif self.prim.HasAPI(UsdLux.LightAPI):
                    self._valid_prims = [self.prim]
                else:
                    self._valid_prims = []
                    carb.log_warn(f"[{self.prim_path}] No valid light prims found.")

        * Uses `UsdLux.LightAPI` to identify valid light prims
        * Includes child lights when **includeChildren** is enabled
        * Validates that target prim or children have light API

        .. raw:: html

            </details>

    .. tab-item:: Usage Example

        **Basic Setup:**

        .. raw:: html

            <details open>
            <summary>Step-by-Step Configuration</summary>

        1. **Attach Script**: Add `light_randomizer.py` to a light prim or parent containing lights
        2. **Set Color Range**: Configure `range:minColor` and `range:maxColor`
        3. **Set Intensity Range**: Define `range:intensity` min/max values
        4. **Enable Children**: Set `includeChildren` to `True` for multiple lights

        **Example Configuration:**

        * **range:minColor**: `(0.8, 0.8, 0.8)` (warm white minimum)
        * **range:maxColor**: `(1.0, 1.0, 1.0)` (bright white maximum)
        * **range:intensity**: `(1000.0, 5000.0)` (intensity range)
        * **includeChildren**: `True`
        * **interval**: `0` (update every frame)

        .. raw:: html

            </details>

        **Use Cases:**

        * **Day/Night Cycles**: Simulate changing lighting conditions
        * **Dynamic Environments**: Create flickering or varying light sources
        * **Color Temperature**: Randomize between warm and cool lighting


Texture Randomizer
##################

The ``texture_randomizer.py`` script randomly applies textures to materials for increased visual variety of objects.

.. tab-set::

    .. tab-item:: Overview

        **Purpose:** Randomly applies textures to visual prims to create diverse material appearances.

        **Key Features:**

        * Texture selection from provided asset arrays or CSV lists
        * Material creation with randomized parameters (scale, rotation, UV projection)
        * Child prim inclusion for hierarchical texture randomization
        * Configurable update intervals for performance control

        **Exposed Variables:**

        .. raw:: html

            <details open>
            <summary>Configuration Parameters</summary>

        * **includeChildren** (`Bool`): Include child prims in texture randomization
        * **interval** (`UInt`): Update frequency (0 = every frame)
        * **textures:assets** (`AssetArray`): List of texture assets to use
        * **textures:csv** (`String`): CSV string of texture URLs
        * **projectUvwProbability** (`Float`): Probability of enabling `project_uvw`
        * **textureScaleRange** (`Float2`): Texture scale range as (min, max)
        * **textureRotateRange** (`Float2`): Texture rotation range in degrees (min, max)

        .. raw:: html

            </details>

    .. tab-item:: Implementation Details

        **Texture Application:**

        .. raw:: html

            <details open>
            <summary>Material and Shader Randomization</summary>

        .. code-block:: python

            def _apply_behavior(self):
                if not self._texture_urls:
                    carb.log_warn(f"[{self.prim_path}] No texture URLs provided; skipping.")
                    return
                for mat in self._texture_materials:
                    shader = UsdShade.Shader(omni.usd.get_shader_from_material(mat.GetPrim(), get_prim=True))
                    if not shader:
                        continue
                    diffuse_texture = random.choice(self._texture_urls)
                    if shader.GetInput("diffuse_texture"):
                        shader.GetInput("diffuse_texture").Set(diffuse_texture)

                    project_uvw = random.choices(
                        [True, False], weights=[self._project_uvw_probability, 1 - self._project_uvw_probability]
                    )[0]
                    shader.GetInput("project_uvw").Set(bool(project_uvw))

                    texture_scale = random.uniform(self._texture_scale_range[0], self._texture_scale_range[1])
                    shader.GetInput("texture_scale").Set((texture_scale, texture_scale))

                    texture_rotate = random.uniform(self._texture_rotate_range[0], self._texture_rotate_range[1])
                    shader.GetInput("texture_rotate").Set(texture_rotate)

        * Randomly selects textures from provided asset list
        * Applies probabilistic UV projection settings
        * Randomizes texture scale and rotation parameters
        * Updates shader inputs directly via USD API

        .. raw:: html

            </details>

        **Child Prim Selection:**

        .. raw:: html

            <details open>
            <summary>Geometric Prim Discovery</summary>

        .. code-block:: python

            def _setup(self):
                include_children = self._get_exposed_variable("includeChildren")
                if include_children:
                    self._valid_prims = [prim for prim in Usd.PrimRange(self.prim) if prim.IsA(UsdGeom.Gprim)]
                elif self.prim.IsA(UsdGeom.Gprim):
                    self._valid_prims = [self.prim]
                else:
                    self._valid_prims = []
                    carb.log_warn(f"[{self.prim_path}] No valid prims found.")

        * Uses `UsdGeom.Gprim` to identify geometric prims suitable for materials
        * Includes child prims when **includeChildren** is enabled
        * Validates that target prims can receive material bindings

        .. raw:: html

            </details>

    .. tab-item:: Usage Example

        **Basic Setup:**

        .. raw:: html

            <details open>
            <summary>Step-by-Step Configuration</summary>

        1. **Attach Script**: Add `texture_randomizer.py` to a geometric prim
        2. **Provide Textures**: Set `textures:assets` or `textures:csv` with texture paths
        3. **Configure Parameters**: Adjust scale, rotation, and UV projection settings
        4. **Enable Children**: Set `includeChildren` to `True` for multiple objects

        **Example Configuration:**

        * **textures:csv**: `"texture1.jpg,texture2.png,texture3.exr"`
        * **textureScaleRange**: `(0.5, 2.0)` (scale variation)
        * **textureRotateRange**: `(0.0, 360.0)` (full rotation)
        * **projectUvwProbability**: `0.3` (30% chance of UV projection)
        * **includeChildren**: `True`

        .. raw:: html

            </details>

        **Use Cases:**

        * **Material Variety**: Create diverse surface appearances for objects
        * **Background Variation**: Randomize textures on environmental elements
        * **Asset Augmentation**: Enhance object datasets with texture variation


Volume Stack Randomizer
#######################

The ``volume_stack_randomizer.py`` script uses physics simulation to randomly stack objects for realistic object arrangements.

.. tab-set::

    .. tab-item:: Overview

        **Purpose:** Randomly drops and stacks assets within specified areas using physics simulation.

        **Key Features:**

        * Asset randomization from provided lists or CSV paths
        * Physics simulation for natural stacking behavior
        * Event-based execution independent of simulation timeline
        * Customizable parameters for drop height, asset count, and rendering

        **Exposed Variables:**

        .. raw:: html

            <details open>
            <summary>Configuration Parameters</summary>

        * **includeChildren** (`Bool`): Include child prims in the behavior
        * **event:input** (`String`): Event name to subscribe to for behavior control
        * **event:output** (`String`): Event name to publish after behavior execution
        * **assets:assets** (`AssetArray`): List of asset references to spawn
        * **assets:csv** (`String`): CSV string of asset URLs to spawn
        * **assets:numRange** (`Int2`): Range for number of assets to spawn (min, max)
        * **dropHeight** (`Float`): Height from which to drop the assets
        * **renderSimulation** (`Bool`): Whether to render simulation steps
        * **removeRigidBodyDynamics** (`Bool`): Remove rigid body dynamics after simulation
        * **preserveSimulationState** (`Bool`): Keep final simulation state

        .. raw:: html

            </details>

    .. tab-item:: Implementation Details

        **Core Structure:**

        .. raw:: html

            <details open>
            <summary>Class Architecture</summary>

        .. code-block:: python

            class VolumeStackRandomizer(BehaviorScript):
                BEHAVIOR_NS = "volumeStackRandomizer"
                EVENT_NAME_IN = f"{EXTENSION_NAME}.{BEHAVIOR_NS}.in"
                EVENT_NAME_OUT = f"{EXTENSION_NAME}.{BEHAVIOR_NS}.out"
                ACTION_FUNCTION_MAP = {
                    "setup": "_setup_async",
                    "run": "_run_behavior_async",
                    "reset": "_reset_async",
                }

                async def _setup_async(self):
                    # Asynchronous setup logic...
                    pass

                async def _run_behavior_async(self):
                    # Asynchronous behavior execution...
                    pass

                async def _reset_async(self):
                    # Asynchronous reset logic...
                    pass

        * Event-based behavior using custom events for lifecycle management
        * Asynchronous methods for non-blocking physics simulation
        * Action function mapping for external event control

        .. raw:: html

            </details>

        **Child Prim Selection:**

        .. raw:: html

            <details open>
            <summary>Surface Area Discovery</summary>

        .. code-block:: python

            async def _setup_async(self):
                include_children = self._get_exposed_variable("includeChildren")
                if include_children:
                    self._valid_prims = [prim for prim in Usd.PrimRange(self.prim) if prim.IsA(UsdGeom.Gprim)]
                elif self.prim.IsA(UsdGeom.Gprim):
                    self._valid_prims = [self.prim]
                else:
                    self._valid_prims = []
                    carb.log_warn(f"[{self.prim_path}] No valid prims found.")

        * Identifies geometric prims suitable for object stacking surfaces
        * Includes child prims when **includeChildren** is enabled
        * Validates surface prims can receive physics objects

        .. raw:: html

            </details>

    .. tab-item:: Event-Based Control

        **Custom Event System:**

        .. raw:: html

            <details open>
            <summary>Event-Based Execution Control</summary>

        The Volume Stack Randomizer operates using custom events rather than timeline-based updates, allowing for precise control over when stacking operations occur.

        **Event Flow:**

        1. **Reset Phase**: Cleans up previous simulation state
        2. **Setup Phase**: Spawns assets and prepares physics simulation
        3. **Run Phase**: Executes physics simulation for object stacking
        4. **Completion**: Publishes completion event with final state

        **Event Control Example:**

        .. code-block:: python

            async def run_stacking_simulation_async(prim_path=None):
                actions = [("reset", "RESET", 10), ("setup", "SETUP", 500), ("run", "FINISHED", 1500)]
                for action, state, wait in actions:
                    await publish_event_and_wait_for_completion_async(
                        publish_payload={"prim_path": prim_path, "action": action},
                        expected_payload={"prim_path": prim_path, "state_name": state},
                        publish_event_name=VolumeStackRandomizer.EVENT_NAME_IN,
                        subscribe_event_name=VolumeStackRandomizer.EVENT_NAME_OUT,
                        max_wait_updates=wait,
                    )

        .. raw:: html

            </details>

        **Integration Benefits:**

        * **Precise Control**: Execute stacking at specific workflow points
        * **Sequential Operations**: Chain multiple stacking operations
        * **State Management**: Track completion of each simulation phase
        * **External Orchestration**: Control from external scripts or systems

    .. tab-item:: Usage Example

        **Basic Setup:**

        .. raw:: html

            <details open>
            <summary>Step-by-Step Configuration</summary>

        1. **Attach Script**: Add `volume_stack_randomizer.py` to surface prims
        2. **Configure Assets**: Set `assets:csv` or `assets:assets` with object paths
        3. **Set Parameters**: Define `assets:numRange`, `dropHeight`, and other settings
        4. **Control Events**: Use custom events to trigger stacking operations

        **Example Configuration:**

        * **assets:csv**: `"box1.usd,box2.usd,cylinder.usd"`
        * **assets:numRange**: `(5, 20)` (spawn 5-20 objects)
        * **dropHeight**: `2.0` (drop from 2 units above surface)
        * **renderSimulation**: `True` (show simulation steps)
        * **preserveSimulationState**: `True` (keep final arrangement)

        .. raw:: html

            </details>

        **Use Cases:**

        * **Object Arrangement**: Create realistic piles of objects
        * **Physics Validation**: Test object interactions and stability
        * **Scene Preparation**: Set up complex scenes before data capture
        * **Simulation Workflows**: Integrate physics-based randomization into pipelines


Templates
#########

This section provides template scripts that serve as starting points for creating custom behaviors.

.. raw:: html

    <details open>
    <summary>Available Templates</summary>

**Template Scripts:**

* **example_behavior.py**: Basic template with boilerplate code for new behaviors
* **base_behavior.py** and **example_base_behavior.py**: Demonstrate base behavior class inheritance for structured development
* **example_custom_event_behavior.py**: Shows implementation of event-based behaviors

**Key Template Features:**

* **Variable Exposure**: Demonstrates exposing variables as USD attributes for UI customization
* **Behavior Structure**: Provides necessary methods (`on_init`, `on_play`, `on_update`, `on_stop`, `on_destroy`) for timeline integration
* **Extensibility**: Base behavior classes enable easy extension and reuse in new behaviors
* **Event Integration**: Shows both timeline-based and custom event-based approaches

.. raw:: html

    </details>


.. _isaac_sim_app_tutorial_replicator_modular_scripting_example:


Example
-------

Below is an example demonstrating the use of behavior scripts to set up and run synthetic data generation in |isaac-sim_short|. It showcases how to utilize behavior scripts for stacking simulations, texture randomization, light behavior, and camera tracking, ultimately capturing synthetic data with randomized scene configurations.

**Key Highlights of the Example:**

- **Volume Stacking Simulation**: Randomly stack assets using physics simulation to create realistic arrangements.
- **Texture Randomization**: Apply randomized textures to assets for scene diversity.
- **Light and Camera Behaviors**: Add randomization to light properties and make the camera track a specific target.
- **Synthetic Data Capture**: Generate and save synthetic images with the configured behaviors.

**Example Script:**

The demo script can be run directly from the :ref:`Script Editor <script-editor>`:

.. raw:: html

    <details closed>
    <summary>Behavior script-based SDG script:</summary>

.. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_modular_scripting/behavior_sdg_pipeline_warehouse_script_editor.py
    :language: python
    :lines: 16-

.. raw:: html

    </details>
