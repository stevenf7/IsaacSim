..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_intro_examples:


==========================================
Examples
==========================================



|isaac-sim_short| provides a library of examples and demos that serves as a showcase of |isaac-sim_short| capabilities and a learning resource for developing your own projects. Some are :ref:`isaac_sim_app_intro_examples_interactive` that can be opened while the simulator is open, some are :ref:`isaac_sim_app_intro_examples_standalone` for running |isaac-sim_short| from the command line using the :ref:`Standalone workflow <standalone-application>`.

.. toctree::
   :maxdepth: 1

   menu_examples
   standalone_examples_list
   

.. _isaac_sim_app_intro_examples_interactive:

Interactive Examples
======================

Interactive examples can be found by going to the top Menu Bar and clicking **Window > Examples > Robotics Examples**. A browser should appear on the bottom left of the screen, in the same space as the **Content** browser. Click on the **Robotics Examples** tab to bring the browser into view.

The examples are organized into categories shown on the left hand panel. Click through the categories and subcateogries to see the examples inside each. Click on the example thumbnail in the main browser window to load the interactive GUI on the right hand panel of the browser. Expand the **Information** tab to reveal the summary and instructions for the example. 


.. image:: /images/isim_4.5_base_ref_gui_example_browser.png
    :width: 900
    :align: center



========== ================================== ============================================================================
Ref #      Function                            Action
========== ================================== ============================================================================
1          Category Menu                      | Click on the category to see the included examples
2          Example                            | Click on the example to open the interactive GUI on the left hand panel, click again to refresh and reload the example
3          Information Window                 | Expand to see the summary and instructions for the example
4          Controls                           | Expand to see the buttons for running the example
5          Links                              | Quick Access to source code, source folder, and documentation
========== ================================== ============================================================================



.. _isaac_sim_app_intro_examples_standalone:

Standalone Examples
======================

In addition to the interactive examples, |isaac-sim_short| also provides standalone examples that can be run from the command line. These examples are located in the **<isaac_sim_root_dir>/standalone_examples** directory. 

To run an example:

1. Navigate to your `<isaac_sim_root_dir>`.
2. Run the example script using ``./python.sh`` for Linux or ``python.bat`` for Windows. 

For example, to run the ``hello_world`` example, navigate to the ``<isaac_sim_root_dir>`` and run the following command:


.. tab-set::
   .. tab-item:: Linux

         .. code-block:: bash

            ./python.sh standalone_examples/api/isaacsim.simulation_app/hello_world.py

   .. tab-item:: Windows

         .. code-block:: bash

            python.bat standalone_examples\api\isaacsim.simulation_app\hello_world.py





Physics Examples
======================

* `PhysX examples <https://docs.omniverse.nvidia.com/extensions/latest/ext_physics.html#explore-physics-demos>`_
* `Warp examples <https://nvidia.github.io/warp/>`_