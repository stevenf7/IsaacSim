..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_telemetry:

===============================================
Telemetry and Performance Tracking
===============================================

The Action and Event Data Generation extensions include built-in telemetry capabilities to track performance metrics and usage patterns. The telemetry system captures various metrics across extensions, providing valuable insights into system behavior, performance characteristics, and usage patterns.

Overview
--------

Telemetry in the Action and Event Data Generation ecosystem helps developers and users:

* **Monitor Performance**: Track execution times, resource usage, and system performance
* **Understand Usage Patterns**: Gain insights into how features are being used
* **Identify Issues**: Detect bottlenecks and performance problems early
* **Improve User Experience**: Use data-driven insights to optimize workflows

The telemetry system is implemented across multiple extensions and provides a standardized approach to metric collection and reporting.

Local telemetry logs can be found in the ``~/.nvidia-omniverse/logs/`` directory.

Telemetry Architecture
-----------------------

The telemetry system is built on NVIDIA Omniverse's structured logging framework and consists of:

* **Schema Definition**: Structured schemas defining telemetry events and their attributes
* **Event Generation**: Automated Python bindings generated from schema definitions
* **Data Collection**: Instrumented code that emits telemetry events
* **Storage and Analysis**: Events logged locally and transmitted to analysis platforms

For more details, refer to the `Omniverse Telemetry Walkthrough <https://docs.omniverse.nvidia.com/kit/docs/carbonite/latest/docs/structuredlog/Walkthrough.html>`_.

Telemetry Modes
---------------

The telemetry system supports different operational modes:

* **Production Mode**: ``--/telemetry/mode=prod`` - Default mode for production deployments.
* **Test Mode**: ``--/telemetry/mode=test`` - Internal mode for QA, validation, and testing.
* **Dev Mode**: ``--/telemetry/mode=dev`` - Internal mode for development.

Note that different modes have different data collection and transmission policies. To disable transmission or structured logging, refer to :ref:`Configuring Telemetry <configuring-telemetry>` below.

If you are running using headless mode, telemetry is disabled by default. To enable telemetry, pass ``--/telemetry/mode=dev`` using the application config:

.. code-block:: python

    import os
    from isaacsim import SimulationApp

    base_exp_path = os.path.join(
        os.environ["EXP_PATH"],
        "isaacsim.exp.action_and_event_data_generation.base.kit"
    )
    app_config = {
        "headless": True,
        "width": 1920,
        "height": 1080,
        "extra_args": ["--/telemetry/mode=dev"], # Enables telemetry in dev mode
    }
    sim_app = SimulationApp(launch_config=app_config, experience=base_exp_path)

Regardless of the mode, data is saved locally to the user's home directory in the ``~/.nvidia-omniverse/logs/`` directory.

.. _configuring-telemetry:

Configuring Telemetry
----------------------

To disable telemetry transmission (data collection), set ``--/telemetry/enableAnonymousData=false`` (or 0) on the command line or in the application config. Telemetry events will still be logged locally. Alternatively, in the app's ``.kit`` file, set ``enableAnonymousData = false`` under ``[settings.telemetry]`` (refer to :doc:`Data Collection & Usage <../common/data-collection>`).

To disable all telemetry (transmission and local logging), set ``--/structuredLog/enable=false`` (or 0) on the command line or in the application config.

Telemetry can also be enabled or disabled at the extension level through individual ``extension.toml`` files.

The following extensions contain specific telemetry settings:

* ``isaacsim.replicator.agent`` — config at ``EXTS_PATH/isaacsim.replicator.agent.core/config/extension.toml``
* ``omni.metropolis.utils`` — config at ``EXTS_PATH/omni.metropolis.utils/config/extension.toml``

.. note::

   ``isaacsim.replicator.agent`` has two parts (``isaacsim.replicator.agent.core`` and ``isaacsim.replicator.agent.ui``). Updating the setting in the **core** extension affects both.

   ``EXTS_PATH`` varies by platform. For example, on **Windows** it might look like ``C:\isaacsim\extscache\isaacsim.replicator.agent.core-1.x.y\config\extension.toml``; on **Linux**, like ``~/isaacsim/extscache/isaacsim.replicator.agent.core-1.x.y/config/extension.toml`` (version ``1.x.y`` might differ).

.. code-block:: toml

    [settings]
    exts."isaacsim.replicator.agent".telemetry_enabled = true

To modify telemetry settings at runtime:

.. code-block:: python

    import carb.settings
    
    settings = carb.settings.get_settings()
    
    # Enable telemetry for specific extensions
    settings.set("/exts/isaacsim.replicator.agent/telemetry_enabled", True)
    settings.set("/exts/omni.metropolis.utils/telemetry_enabled", True)
    
    # Disable telemetry for specific extensions
    settings.set("/exts/isaacsim.replicator.agent/telemetry_enabled", False)
    settings.set("/exts/omni.metropolis.utils/telemetry_enabled", False)

Available Telemetry Events
~~~~~~~~~~~~~~~~~~~~~~~~~~

The following telemetry events are available across the Action and Event Data Generation extensions:

**omni.metropolis.utils**

* ``file_read`` - Tracks file read operations
* ``file_write`` - Tracks file write operations

**isaacsim.replicator.agent.core**

* ``data_generation`` - Tracks data generation operations
* ``load_asset_to_scene`` - Tracks asset loading events
* ``stage_setup_event`` - Tracks stage setup operations
* ``writer_initialized_event`` - Tracks writer initialization events

Related Documentation
---------------------

* :doc:`Action and Event Data Generation Overview <index>`
* :doc:`Actor Simulation and Synthetic Data Generation <tutorial_replicator_agent>`
* :doc:`Object Simulation and Synthetic Data Generation <tutorial_replicator_object>`

Additional Resources
--------------------

* `Omniverse Telemetry Walkthrough <https://docs.omniverse.nvidia.com/kit/docs/carbonite/latest/docs/structuredlog/Walkthrough.html>`_
