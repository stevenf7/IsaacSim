
..
.. _isaac_sim_benchmarks:

===========================================
|isaac-sim_short| Benchmarks
===========================================

This page contains key performance indicators (KPIs) for |isaac-sim_short|, captured across
different reference hardware and measured using the ``isaacsim.benchmark.services`` extension. It also
contains a guide on how to collect the same KPIs on your hardware, to compare to our published
performance specs.

.. _isaac_sim_benchmarks_gpu_independent:

GPU-Independent KPIs
====================

These KPIs measure |isaac-sim_short| performance independent of the GPU on which |isaac-sim_short| is running.

.. note:: These KPIs were measured on a standardized reference machine using an Intel i9-14900k CPU and 32GB of DDR5 RAM.

.. list-table:: GPU-Independent KPIs
    :widths: 25 35 15 10
    :header-rows: 1

    * - Name
      - Definition
      - Units
      - Value
    * - Binary package size (Windows)
      - Size of Windows binary package
      - GB
      - 9.90
    * - Binary package size (Linux)
      - Size of Linux binary package
      - GB
      - 12.2
    * - Docker container size
      - Size of Docker container before extraction on `NGC <https://ngc.nvidia.com/catalog/containers/nvidia:isaac-sim>`_
      - GB
      - 9.97
    * - ``pip`` package size
      - Size of ``pip`` package as downloaded
      - GB
      -
    * - Startup time (async)
      - Time from launching |isaac-sim_short| executable to ``app ready`` appearing in logs
      - seconds
      - 31.472 [#]_ |br|
        6.31 [#]_ |br|
    * - Startup time (non-async)
      - Time from initializing ``SimulationApp`` in standalone Python to ``app ready`` appearing in logs
      - seconds
      - 263 [#]_ |br|
        4.43 [#]_ |br|

.. [#] Includes shader installation, which is typically one-time when shaders are cached.
.. [#] Startup time (async) using cached shaders.
.. [#] Includes shader installation, which is typically one-time when shaders are cached.
.. [#] Startup time (non-async) using cached shaders.


.. _isaac_sim_benchmarks_gpu_dependent:

GPU-Dependent KPIs
=========================

These KPIs measure |isaac-sim_short| performance on reference hardware, including
frame rate for benchmark scenes and render rate for specific sensor combinations.
KPIs are reported as the average KPI value across 600 frames.

.. note:: For detailed explanations of each KPI, refer to :ref:`isaac_sim_benchmarks_measuring_kpis`. Instructions on how to measure the KPIs on local hardware as well as relevant optimization tips for similar workflows are provided.

Workstation GPUs
-----------------

.. tab-set::

    .. tab-item:: GeForce RTX 5080

        .. note:: These KPIs were measured on a standardized reference machine using an Intel i9-14900k CPU and 32GB of DDR5 RAM.

        .. list-table:: Hardware-Dependent KPIs
            :widths: 25 35 15 10 10
            :header-rows: 1

            * - Name
              - Definition
              - Units
              - Windows
              - Ubuntu
            * - Full Warehouse Sample Scene Load Time
              - Wall-clock time to load Full Warehouse Sample Scene
              - Seconds
              - 27.15
              - 27.45
            * - Full Warehouse Sample Scene FPS
              - Frame rate of Full Warehouse Sample Scene
              - Frames per second
              - 155.52
              - 161.55
            * - Physics steps per second
              - Number of physics steps executed per wall-clock second with 10 O3dyn robots
              - Hz
              - 32.95
              - 31.43
            * - Isaac ROS Sample Scene FPS
              - Frame rate of Isaac ROS Sample Scene
              - Frames per second
              - 28.34
              - 46.56
            * - ROS2 render & publishing speed
              - Frame rate rendered and published using :ref:`ROS2 bridge <isaac_sim_app_tutorial_ros2_navigation>` from Nova Carter ROS asset, per wall-clock second
              - Frames per second
              - 13.54
              - 18.34
            * - SDG images per second (simple)
              - Images rendered by SDG per second, with only RGBD annotators enabled, per wall-clock second
              - Images per second
              - 24.54
              - 40.83
            * - SDG images per second (complex)
              - Images rendered by SDG per second, with all annotators enabled, per wall-clock second
              - Images per second
              - 8.86
              - 13.77

    .. tab-item:: RTX PRO 6000 Blackwell

        .. note:: These KPIs were measured on a standardized reference machine using an Intel i9-14900k CPU and 32GB of DDR5 RAM.

        .. list-table:: Hardware-Dependent KPIs
            :widths: 25 35 15 10 10
            :header-rows: 1

            * - Name
              - Definition
              - Units
              - Windows
              - Ubuntu
            * - Full Warehouse Sample Scene Load Time
              - Wall-clock time to load Full Warehouse Sample Scene
              - Seconds
              - 32.86
              - 29.14
            * - Full Warehouse Sample Scene FPS
              - Frame rate of Full Warehouse Sample Scene
              - Frames per second
              - 159.72
              - 153.33
            * - Physics steps per second
              - Number of physics steps executed per wall-clock second with 10 O3dyn robots
              - Hz
              - 32.51
              - 35.40
            * - Isaac ROS Sample Scene FPS
              - Frame rate of Isaac ROS Sample Scene
              - Frames per second
              - 47.55
              - 51.94
            * - ROS2 render & publishing speed
              - Frame rate rendered and published using :ref:`ROS2 bridge <isaac_sim_app_tutorial_ros2_navigation>` from Nova Carter ROS asset, per wall-clock second
              - Frames per second
              - 26.78
              - 28.38
            * - SDG images per second (simple)
              - Images rendered by SDG per second, with only RGBD annotators enabled, per wall-clock second
              - Images per second
              - 29.27
              - 41.37
            * - SDG images per second (complex)
              - Images rendered by SDG per second, with all annotators enabled, per wall-clock second
              - Images per second
              - 9.57
              - 14.24

Server GPUs
------------

.. tab-set::

    .. tab-item:: L40

        .. note:: These KPIs were measured on a standardized OVX machine using 2x Intel 8362 CPU and 1024GB of DDR4 RAM, on Ubuntu 24.04.
          Some KPIs are measured on multi-GPU configurations, typically for 1, 4, or 8 GPUs.

        .. list-table:: Hardware-Dependent KPIs by GPU Count
            :widths: 25 35 15 5 5 5
            :header-rows: 1

            * - Name
              - Definition
              - Units
              - x1
              - x4
              - x8
            * - Full Warehouse Sample Scene Load Time
              - Wall-clock time to load Full Warehouse Sample Scene
              - Seconds
              - 101.23
              - 102.43
              - 100.28

            * - Full Warehouse Sample Scene FPS
              - Frame rate of Full Warehouse Sample Scene
              - Frames per second
              - 182.48
              - 151.75
              - 120.34

            * - Physics steps per second
              - Number of physics steps executed per wall-clock second with 10 O3dyn robots
              - Hz
              - 30.6
              - 31.53
              - 33.05

            * - Isaac ROS Sample Scene FPS
              - Frame rate of Isaac ROS Sample Scene
              - Frames per second
              - 44.62
              - 40.00
              - 36.40

            * - ROS2 render & publishing speed
              - Frame rate rendered and published using :ref:`ROS2 bridge <isaac_sim_app_tutorial_ros2_navigation>` from Nova Carter ROS asset, per wall-clock second
              - Frames per second
              - 33.12
              - 38.92
              - 39.41

            * - SDG images per second (simple)
              - Images rendered by SDG per second, with only RGBD annotators enabled, per wall-clock second
              - Images per second
              - 
              - 
              - 

            * - SDG images per second (complex)
              - Images rendered by SDG per second, with all annotators enabled, per wall-clock second
              - Images per second
              - 
              - 
              - 

    .. tab-item:: RTX PRO 6000 Blackwell Server Edition

        .. list-table:: Hardware-Dependent KPIs by GPU Count
            :widths: 25 35 15 5 5 5
            :header-rows: 1

            * - Name
              - Definition
              - Units
              - x1
              - x4
              - x8
            * - Full Warehouse Sample Scene Load Time
              - Wall-clock time to load Full Warehouse Sample Scene
              - Seconds
              - 102.34
              - 101.75
              - 101.45

            * - Full Warehouse Sample Scene FPS
              - Frame rate of Full Warehouse Sample Scene
              - Frames per second
              - 193.05
              - 173.01
              - 168.92

            * - Physics steps per second
              - Number of physics steps executed per wall-clock second with 10 O3dyn robots
              - Hz
              - 35.13
              - 34.88
              - 34.46

            * - Isaac ROS Sample Scene FPS
              - Frame rate of Isaac ROS Sample Scene
              - Frames per second
              - 109.77
              - 105.82
              - 97.47

            * - ROS2 render & publishing speed
              - Frame rate rendered and published using :ref:`ROS2 bridge <isaac_sim_app_tutorial_ros2_navigation>` from Nova Carter ROS asset, per wall-clock second
              - Frames per second
              - 38.61
              - 40.97
              - 39.15

            * - SDG images per second (simple)
              - Images rendered by SDG per second, with only RGBD annotators enabled, per wall-clock second
              - Images per second
              - 
              - 
              - 

            * - SDG images per second (complex)
              - Images rendered by SDG per second, with all annotators enabled, per wall-clock second
              - Images per second
              - 
              - 
              - 


.. _isaac_sim_benchmarks_measuring_kpis:

Measuring KPIs on Local Hardware
================================

.. |bt| raw:: html

    <code class="code docutils literal notranslate">`</code>

|isaac-sim_short| KPIs can be measured using the Python scripts provided in ``standalone_examples/benchmarks``. Select a category below to review benchmark details, commands, and configuration options as well as optimization tips for similar workflows.

More specific optimization guidance can be found in the :ref:`Isaac Sim Performance Optimization Handbook<isaac_sim_performance_optimization_handbook>`.

.. note::
   Commands are provided in ``bash`` syntax (for Ubuntu). For Windows, replace ``.sh`` with ``.bat`` and ``\`` for multiline commands to |bt|.

.. tab-set::

   .. tab-item:: Startup & Loading

      Benchmarks for measuring application initialization and scene loading performance.

      .. dropdown:: Startup Time (Async)
         :color: primary

         **Purpose:** Measure Isaac Sim initialization time in headless mode without blocking operations.

         **What it measures:** Time from application launch to ready state, measured as ``Runtime`` for ``phase: startup`` in the logs.

         **Command:**

         .. code-block:: bash

             ./isaac-sim.sh --no-window --/app/quitAfter=200 --/app/file/ignoreUnsavedOnExit=1 \
               --enable isaacsim.benchmark.services

         **Interpreting Results:** Look for the following in the console output:

         .. code-block:: text

             [INFO] Runtime for phase: startup = 15234 ms

         **Typical Values:** 10-30 seconds depending on hardware and system configuration.

      .. dropdown:: Startup Time (Non-Async)
         :color: primary

         **Purpose:** Measure Isaac Sim initialization time with synchronous loading using the Python API.

         **What it measures:** Time for complete application initialization through the Python API.

         **Command:**

         .. code-block:: bash

             ./python.sh standalone_examples/api/isaacsim.simulation_app/hello_world.py \
               --enable isaacsim.benchmark.services

         **Interpreting Results:** Look for ``Runtime`` for ``phase: startup`` in the logs.

         **Comparison:** Non-async startup is typically slower than async due to synchronous loading.

      .. dropdown:: Full Warehouse Load Time + FPS
         :color: primary

         **Purpose:** Measure scene loading performance and rendering FPS for complex warehouse environment.

         **What it measures:** Duration of stage loading phase and FPS at runtime for the given stage.

         **Command:**

         .. code-block:: bash

             ./python.sh standalone_examples/benchmarks/benchmark_scene_loading.py \
               --env-url /Isaac/Environments/Simple_Warehouse/full_warehouse.usd

         **Configuration:**

         - Environment: full warehouse sample scene

         **Interpreting Results:**

         .. code-block:: text

             [INFO] Runtime for phase: loading = 8123 ms
             [INFO] Mean FPS for phase: benchmark = 45.2

         **Performance Notes:** Loading time depends on asset complexity and storage speed. FPS varies with CPU and GPU capability.

         **Optimization Tips:**

         1. Use a simpler scene with fewer materials and textures.
         2. Disable material loading to reduce initial loading time (``--/app/renderer/skipMaterialLoading=1``).
         3. Reduce rendering quality to increase runtime FPS.

      .. dropdown:: Isaac ROS Sample Scene Load Time + FPS
         :color: primary

         **Purpose:** Measure load time and runtime performance in stages with the ROS2 bridge enabled.

         **What it measures:** Duration of stage loading phase and FPS at runtime for the given stage with the ROS2 bridge enabled. The stage uses the Nova Carter robot in a warehouse environment with animated human workers.

         **Measurement:** Loading time is measure by ``Runtime`` for ``phase: loading``. Runtime FPS is measured as ``Mean FPS`` for ``phase: benchmark``.

         **Command:**

         .. code-block:: bash

             ./python.sh standalone_examples/benchmarks/benchmark_scene_loading.py \
               --env-url /Isaac/Samples/ROS2/Scenario/carter_warehouse_apriltags_worker.usd

         **Interpreting Results:**

         .. code-block:: text

             [INFO] Runtime for phase: loading = 8556 ms
             [INFO] Mean FPS for phase: benchmark = 38.7

         **Optimization Tips:**

         1. Disable material loading to reduce initial loading time (``--/app/renderer/skipMaterialLoading=1``).
         2. Reduce rendering quality to increase runtime FPS.
         3. Use a simpler scene with fewer materials, textures, and lighting. This will simplify the rendering work done by each render product.

         **Multi-GPU:** Loading time is not impacted by the number of GPUs. Runtime FPS for this benchmark scales with GPU count - optimal GPU count is hardware dependent but typically 4 or 8 GPUs.

   .. tab-item:: Workflow Performance

      Benchmarks for measuring physics computation, rendering speed, and overall simulation performance.

      .. dropdown:: Physics Steps per Second
         :color: primary

         **Purpose:** Measure physics simulation performance and compare CPU vs GPU physics backends for a complex robot.

         **What it measures:** How many physics steps are executed per wall-clock second given a fixed step size, robot count, and Physics backend for the O3dyn robot in the full warehouse sample scene.

         **Measurement:** Measured as ``Mean FPS`` for ``phase: benchmark`` given a physics dt of 1/60s.

         **Command:**

         .. code-block:: bash

             ./python.sh standalone_examples/benchmarks/benchmark_robots_o3dyn.py \
               --num-robots 10 --num-gpus 1

         **Configurations:**

         - Robot Count
         - Physics Backend (CPU: numpy, GPU: torch, warp)

         .. code-block:: bash

             # CPU Physics
             ./python.sh standalone_examples/benchmarks/benchmark_robots_o3dyn.py \
               --num-robots 2 --physics numpy

             # GPU Physics (default: torch)
             ./python.sh standalone_examples/benchmarks/benchmark_robots_o3dyn.py \
               --num-robots 10 --physics warp

         **Interpreting Results:**

         .. code-block:: text

             Mean FPS: 51.706 FPS

         Given a physics dt of ``1/60``, the physics steps per second is equivalent to the FPS. A smaller physics dt will result in multiple physics steps per frame, changing the computation to be ``FPS * physics steps per frame``.

         **Performance Notes:** The O3dyn robot is very complex, particularly due to the simulation of the highly articulated wheels. Simpler robots will achieve faster framerates due to reduced physics computation work. Higher-spec GPUs will enable higher throughput as robot count or physics object count increases.

         **Optimization Tips:**

         1. Select the appropriate physics backend for the workload. It's recommended to test with both backends to determine the optimal choice.

          - `CPU Physics:` Low robot count and/or low complexity robots + scenes
          - `GPU Physics:` Higher robot counts and/or higher complexity robots + scenes

         2. Reduce the complexity of the robot by disabling unnecessary colliders, joints, and other components. Similarly decrease the complexity of the scene.

         **Performance Scaling:** The O3dyn robot is a good example to review how CPU and GPU physics performance scales with the number of robots and the complexity of the robots.

         - 1-4 robots: CPU physics is faster
         - ~5 robots: CPU and GPU physics are comparable (hardware-dependent)
         - 6+ robots: GPU physics is faster

         **Multi-GPU:** GPU physics performance does not scale with GPU count as PhysX runs on a single GPU.

      .. dropdown:: Rendering Speed
         :color: primary

         **Purpose:** Measure pure rendering performance with no additional physics computation.

         **What it measures:** The framerate of the simulation when rendering the full warehouse sample scene with a variable number of cameras.

         **Measurement:** Measured as ``Mean FPS`` for ``phase: benchmark``

         **Command:**

         .. code-block:: bash

             ./python.sh standalone_examples/benchmarks/benchmark_camera.py \
               --num-cameras 2 --resolution 1280 720 --num-gpus 1

         **Configurations:**

         - Camera count
         - Camera resolution (default: 1280x720)
         - GPU count (default: all available GPUs)

         **Interpreting Results:**

         .. code-block:: text

             Mean FPS: 45.36 FPS

         **Performance Notes:** Faster GPUs will achieve better performance as camera count and/or resolution increases. GPUs with lower VRAM may struggle to render multiple high resolution cameras or high counts of lower resolution cameras.

         **Optimization Tips:**

         1. Use minimum number of cameras and resolution to reduce rendering work.
         2. Use as many GPUs as cameras to maximize throughput. Very high resolution cameras will also benefit from multiple GPUs due to tiling.
         3. If visual quality is not critical, modify render settings to reduce realism of rendered images.
         4. Use a simpler scene with fewer materials, textures, and lighting. This will simplify the rendering work done by each render product.

         **Multi-GPU:** Camera rendering performance most effectively scales with the number of GPUs. The more GPUs, the more cameras can be rendered in parallel, improving throughput.

      .. dropdown:: ROS 2 Render & Publishing Speed (Rendering + Physics + ROS2 Workflow)
         :color: primary

         **Purpose:** Measure full SIL workflow performance - combining rendering, physics, ROS2 message publishing, and robot control.

         **What it measures:** Simulation framerate when publishing using ROS2 bridge using Nova Carter ROS asset, per wall-clock second. A total of 11 sensors are enabled: 3 lidars + 4 stereo camera pairs

         **Measurement:** Overall speed is measured as ``Mean FPS`` for ``phase: benchmark``.

         **Command:**

         .. code-block:: bash

             ./python.sh standalone_examples/benchmarks/benchmark_robots_nova_carter_ros2.py \
               --num-robots 1 --enable-3d-lidar 1 --enable-2d-lidar 2 --enable-hawks 4

         **Configuration:**

         - 1x Nova Carter Robot

           - 1x 3D LiDAR sensor
           - 2x 2D LiDAR sensors
           - 4x Hawk stereo cameras (8x render products at 1920x1200p each)

         **Interpreting Results:**

         .. code-block:: text

             [INFO] Mean FPS for phase: benchmark = 25.3

         **Performance Notes:** This benchmarks uses a heavy sensor suite by default, reducing the number or resolution of sensors will improve performance. Lower VRAM GPUs (under 12GB) may not be able to render all sensors. Performance with fast CPUs will be limited by rendering speed, performance benefits will be observed with higher-spec GPUs or multi-GPU configurations.

         **Optimization Tips:**

         1. Reduce the camera count (``--enable-hawks 2``). This command runs 8 render products at 1920x1200p each. Reducing the camera count will reduce the number of render products and improve performance.
         2. If visual quality is not critical, modify render settings to reduce accuracy of rendered images.
         3. Use a simpler scene with fewer materials, textures, and lighting. This will simplify the rendering work done by each render product.

         **Multi-GPU:** Performance scales with the sensor count. The more sensors, the more GPUs will help improve throughput. For server-grade hardware, simulating 4 Nova Carters with full sensor suites is feasible with 4x or 8x GPUs.

      .. dropdown:: RTX Lidar ROS2 PointCloud2 Metadata Publishing
         :color: primary

         **Purpose:** Measure RTX Lidar performance when publishing PointCloud2 messages with configurable metadata fields using ROS2.

         **What it measures:** Simulation framerate when creating multiple RTX Lidar sensors, each with their own ROS2 OmniGraph that publishes PointCloud2 messages with configurable metadata fields, in the full warehouse sample scene.

         **Measurement:** Overall speed is measured as ``Mean FPS`` for ``phase: benchmark``.

         **Command:**

         .. code-block:: bash

             ./python.sh standalone_examples/benchmarks/benchmark_rtx_lidar_ros2_pcl_metadata.py \
               --num-frames 10 --num-sensors 2 --metadata \
               Intensity \
               Timestamp \
               EmitterId \
               ChannelId \
               MaterialId \
               TickId \
               HitNormal \
               Velocity \
               ObjectId \
               EchoId \
               TickState

         **Configuration:**

         - 2x RTX Lidar sensors (Example_Rotary)
         - All metadata fields enabled (Intensity, Timestamp, EmitterId, ChannelId, MaterialId, TickId, HitNormal, Velocity, ObjectId, EchoId, TickState)
         - Full warehouse sample scene
         - ROS2 bridge publishing PointCloud2 messages per sensor

         **Configuration Options:**

         .. code-block:: bash

             # Fewer sensors
             ./python.sh standalone_examples/benchmarks/benchmark_rtx_lidar_ros2_pcl_metadata.py \
               --num-sensors 1 --metadata Intensity ObjectId

             # Solid state lidar
             ./python.sh standalone_examples/benchmarks/benchmark_rtx_lidar_ros2_pcl_metadata.py \
               --num-sensors 2 --lidar-type Solid_State --metadata Intensity ObjectId

             # Fewer metadata fields
             ./python.sh standalone_examples/benchmarks/benchmark_rtx_lidar_ros2_pcl_metadata.py \
               --num-sensors 2 --metadata Intensity ObjectId

         **Interpreting Results:**

         .. code-block:: text

             [INFO] Mean FPS for phase: benchmark = 25.3

         **Performance Notes:** Enabling more metadata fields increases the amount of data published per PointCloud2 message, which may reduce throughput. Performance depends on sensor count, metadata field count, and GPU capability.

         **Optimization Tips:**

         1. Reduce the number of metadata fields to only those required for your use case.
         2. Reduce the number of sensors to minimize parallel publishing overhead.
         3. Use a simpler scene with fewer materials, textures, and lighting to reduce rendering work.

   .. tab-item:: Synthetic Data Generation

      Benchmarks for measuring synthetic data generation performance and throughput.

      .. dropdown:: SDG Images per Second (Simple)
         :color: primary

         **Purpose:** Measure synthetic data generation performance with basic annotations

         **What it measures:** Image generation rate with RGB and depth annotations for 500 prims, randomizing pose/orientation/scale/color per frame.

         **Measurement:** Overall speed is measured as ``Mean FPS`` for ``phase: benchmark``. Images generated per second is measured as ``Mean FPS * number of cameras``.

         **Command:**

         .. code-block:: bash

             ./python.sh standalone_examples/benchmarks/benchmark_sdg.py \
               --num-cameras 2 --resolution 1280 720 --asset-count 100 \
               --annotators rgb distance_to_image_plane --skip-write

         **Configuration:**

         - 2 cameras at 1280x720 resolution
         - 100 count per asset type (5 types for total of 500 prims)
         - RGB + depth annotations only
         - Skip disk write for pure generation speed

         **Interpreting Results:**

         .. code-block:: text

             [INFO] Mean FPS for phase: benchmark = 15.8

         The throughput can be calculated as ``Mean FPS * number of cameras`` to yield the total number of images generated per second.

         **Performance Notes:** The usage of the `--skip-write` flag improves performance by skipping the disk write step, which can cause a bottleneck due to IO operations. Randomization of pose/orientation/material are CPU-intensive operations currently.

         **Optimization Tips:**

         1. If saving to disk, review the I/O Optimization Guide in the Replicator documentation to optimize throughput.
         2. Decrease total number of assets in the scene.
         3. Minimize randomization operations, review are CPU-intensive.

         **Multi-GPU:** Performance scales most effectively based on camera count and resolution. The more cameras, or higher the resolution, in the scene, the more GPUs will help improve throughput. This default benchmark with two 720p cameras does not scale well with more GPUs because it is limited by randomization operations.

      .. dropdown:: SDG Images per Second (Complex)
         :color: primary

         **Purpose:** Measure synthetic data generation performance with full suite of annotators enabled.

         **What it measures:** Image generation rate with all annotators enabled for 500 prims, randomizing pose/orientation/scale/color per frame.

         **Measurement:** Overall speed is measured as ``Mean FPS`` for ``phase: benchmark``. Images generated per second is measured as ``Mean FPS * number of cameras``.

         **Command:**

         .. code-block:: bash

             ./python.sh standalone_examples/benchmarks/benchmark_sdg.py \
               --num-cameras 2 --resolution 1280 720 --asset-count 100 \
               --annotators all --skip-write

         **Configuration:**

         - 2 cameras at 1280x720 resolution
         - 100 count per asset type (5 types for total of 500 prims)
         - All available annotators enabled
         - Skip disk write for pure generation speed

         **Annotators Available:**

         - RGB
         - Distance to Image Plane
         - Distance to Camera
         - Bounding Box 2D Tight
         - Bounding Box 2D Loose
         - Bounding Box 3D
         - Semantic Segmentation
         - Instance Segmentation
         - Occlusion
         - Normals
         - Motion vectors
         - Camera Parameters
         - Point Cloud
         - Skeleton Data

         **Interpreting Results:**

         .. code-block:: text

             [INFO] Mean FPS for phase: benchmark = 4.2

         The throughput can be calculated as ``Mean FPS * number of cameras`` to yield the total number of images generated per second.

         **Performance Notes:** The usage of the ``--skip-write`` flag improves performance by skipping the disk write step review can cause a bottleneck due to IO operations. Randomization of pose/orientation/material are CPU-intensive operations, limiting GPU scaling.

         **Optimization Tips:**

         1. Disable unneeded annotators to improve performance for specific use cases.
         2. If saving to disk, review the I/O Optimization Guide in the Replicator documentation to optimize throughput.
         3. Decrease total number of assets in the scene.
         4. Minimize randomization operations, review are CPU-intensive.

         **Multi-GPU:** Performance scales most effectively based on camera count and resolution. The more cameras, or higher the resolution, in the scene, the more GPUs will help improve throughput. This default benchmark with two 720p cameras does not scale with more GPUs because it is limited by randomization operations rather than rendering.

.. _isaac_sim_benchmark_metrics:

Understanding Benchmark Outputs
===============================

This section walks through the outputs of the benchmark script to explain the different metrics and how to interpret them.

The benchmark script outputs a summary report and a raw metric file. The summary report is a concise summary of the benchmark results. The metrics file contains the raw metrics that are parsed into the summary report. The log indicates where the metrics file is stored.

Summary Report
--------------

The summary report is output to the console for every benchmark script. It provides a concise summary of the benchmark results.

**Example Output:**

.. code-block:: text

    |----------------------------------------------------|
    |                   Summary Report                   |
    |----------------------------------------------------|
    | workflow_name: benchmark_robots_nova_carter_ros2   |
    | num_robots: 2                                      |
    | num_gpus: 1                                        |
    | num_3d_lidar: 1                                    |
    | num_2d_lidar: 2                                    |
    | num_hawks: 4                                       |
    | num_cpus: 32                                       |
    | gpu_device_name: NVIDIA GeForce RTX 4090           |
    |----------------------------------------------------|
    | Phase: loading                                     |
    | System Memory RSS: 17.021 GB                       |
    | System Memory VMS: 145.177 GB                      |
    | System Memory USS: 16.997 GB                       |
    | GPU Memory Tracked: 1.124 GB                       |
    | Runtime: 5549.776 ms                               |
    |----------------------------------------------------|
    | Phase: benchmark                                   |
    | System Memory RSS: 17.021 GB                       |
    | System Memory VMS: 145.177 GB                      |
    | System Memory USS: 16.997 GB                       |
    | GPU Memory Tracked: 1.124 GB                       |
    | Mean FPS: 51.706 FPS                               |
    | Real Time Factor: 0.849                            |
    | Runtime: 11772.105 ms                              |
    | Frametimes (ms):    mean |  stdev |   min |   max  |
    | App_Update         19.34 |   0.39 | 18.92 | 20.42  |
    | Physics            17.61 |   0.08 | 17.52 | 17.99  |
    |----------------------------------------------------|

Configuration Section
~~~~~~~~~~~~~~~~~~~~~

The first section shows the benchmark configuration and system information.

.. code-block:: text

    |----------------------------------------------------|
    | workflow_name: benchmark_robots_nova_carter_ros2   |
    | num_robots: 2                                      |
    | num_gpus: 1                                        |
    | num_3d_lidar: 1                                    |
    | num_2d_lidar: 2                                    |
    | num_hawks: 4                                       |
    | num_cpus: 32                                       |
    | gpu_device_name: NVIDIA GeForce RTX 4090           |
    |----------------------------------------------------|

It's populated with the ``workflow_metadata`` dictionary passed into the ``BaseIsaacBenchmark`` object defined in each benchmark script.

Loading Phase Metrics
~~~~~~~~~~~~~~~~~~~~~

The loading phase measures resource usage during scene loading and other setup steps:

- **System Memory RSS:** Resident Set Size of the process in GB
- **System Memory VMS:** Virtual Memory Size of the process in GB
- **System Memory USS:** Unique Set Size of the process in GB
- **GPU Memory Tracked:** VRAM utilized by the GPU in GB
- **Runtime:** Wall-clock time in milliseconds

Benchmark Phase Metrics
~~~~~~~~~~~~~~~~~~~~~~~

The benchmark phase measures performance during active simulation:

**Performance Metrics:**

- **Mean FPS:** Computed as ``1000/mean_app_update_frametime`` where ``mean_app_update_frametime`` is the average frametime of the app update phase in milliseconds.
- **Real Time Factor:** A ratio of how close simulation time is to wall-clock time. Computed as ``simulation_time / wall_clock_time`` where ``simulation_time`` is the total time simulated and ``wall_clock_time`` is the real-world time elapsed.
- **Runtime:** The wall-clock duration in milliseconds of the benchmark phase.

**Frametime Breakdown:**

The frametimes section shows detailed timing for different simulation components:

- **App_Update:** One app update represents one frame of the simulation. In default configurations, this typically involves one physics step and one render step.
- **Physics:** The duration of the physics step. This is a component of the total ``app_update`` frametime, representing the duration of physics computation work.
- **GPU:** The duration of GPU work. This is a component of the total ``app_update`` frametime, representing the duration of rendering work. This is only collected when the ``--gpu-frametime`` flag is enabled.

For further insight into how the frametime breaks down for a specific workflow, refer to :ref:`isaac_sim_app_profiling_performance` for details on using the Tracy profiler to profile the simulation.

.. note::
    One app update is characterized by some amount of physics compute and some amount of rendering work for the given frame. The sum of these two components are not expected to equal the app_update frametime due to parallelization, other overhead, and any dedicated per frame compute.

Interpreting Results
--------------------

This section details how to interpret some of the key results explained in the previous sections, specifically as they relate to hardware selection.

**Mean FPS:**

The Mean FPS is the key metric to consider when selecting hardware. It is the average frame rate of the simulation over the course of the benchmark. It is a good indicator of the overall performance of the hardware for a given workflow.

**GPU Memory Tracked:**

The GPU Memory Tracked metric indicates the amount of VRAM needed by the workflow. Workflows that involve large scenes, high resolution cameras, or large amounts of sensors will require more VRAM.

**Physics Frametime:**

A Physics Frametime very close to the App Update frametime indicates that the physics computation may be bottlenecking the performance. With GPU Physics, higher-spec GPUs will scale better with more physics objects and/or higher complexity robots.

**GPU Frametime:**

With a GPU frametime very close to the App Update frametime, it indicates that the GPU rendering might be bottlenecking the performance. Adding additional GPUs or using a higher-spec GPU will help improve performance. Otherwise, if the GPU frametime is much lower than the App_Update frametime, it indicates that CPU performance might be the bottleneck.

Benchmark Methodology Changes
=============================

This section tracks changes to benchmark methodologies, measurement scripts, and hardware configurations across |isaac-sim_short| versions to enable accurate version-to-version comparisons.

.. note:: When comparing benchmark results between versions, ensure you account for any methodology or hardware changes listed below.

Version 6.0.0
-------------

**Measurement Changes:**

- Updated reference hardware CPU for workstation hardware from Intel i9-14900k to Intel Core Ultra 9 285K for workstation GPU KPIs

**Script Changes:**

- No changes to benchmark scripts in this version

Version 5.1.0
--------------

**Measurement Changes:**

- Motion BVH disabled by default (previously enabled) - decreases rendering accuracy for motion-related sensor effects but improves rendering performance

**Script Changes:**

- Disabled default collection of GPU frametime due to slight performance impact on overall benchmark performance. Can be enabled with  ``--gpu-frametime`` flag.

Version 5.0.0
-------------

**Measurement Changes:**

- KPIs measured with Motion BVH (enabled by default in Isaac Sim 5.0.0) - increases rendering accuracy for motion-related sensor effects but decreases overall rendering performance

**Script Changes:**

- Disabled viewport updates by default in headless mode to improve performance (can be enabled with ``--viewport-updates``)
- Physics Steps per Second (``benchmark_robots_o3dyn.py``): Added support for both CPU and GPU physics backends (previously CPU only).

  - Backend default changed from CPU to GPU (torch) physics backend
  - Robot count default changed from 2 to 10

Version 4.5.0
--------------

**Measurement Changes:**

- Initial baseline measurements

**Script Changes:**

- Benchmark scripts introduced in ``standalone_examples/benchmarks/``
