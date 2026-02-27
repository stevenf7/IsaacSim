..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _NVIDIA Brev: https://developer.nvidia.com/brev
.. _Isaac Launchable: https://brev.nvidia.com/launchable/deploy/now?launchableID=env-35JP2ywERLgqtD0b0MIeK1HnF46
.. _Isaac Launchable Repository: https://github.com/isaac-sim/isaac-launchable
.. _Isaac Lab: https://github.com/isaac-sim/IsaacLab
.. _README: https://github.com/isaac-sim/isaac-launchable/blob/main/isaac-lab/vscode/README.md

.. _isaac_sim_setup_launchable_requirements:

Isaac Launchable Deployment
############################################

Isaac Launchable offers a simplified approach to trying `Isaac Lab`_ and Isaac Sim.

Through this project, users can interact with Isaac Sim and `Isaac Lab`_ purely from a web browser, with one tab running Visual Studio Code for development and command execution, and another tab providing the streamed user interface for Isaac Sim.

Launchables are provided by `NVIDIA Brev`_, using this repo as a template. Launchables are preconfigured, fully optimized compute and software environments. They allow users to start projects without extensive setup or configuration.

Requirements
---------------------------

The requirements for running the Isaac Launchable is:

1. An NVIDIA Brev account.

Setup
---------------------------

Follow these steps to deploy the Isaac Lab Launchable on NVIDIA Brev:

1. Navigate to the `Isaac Launchable`_ page.
2. Click the **Deploy Launchable** button to spin up the instance.
3. Wait for the instance to be fully ready on Brev: running, built, and the setup script has completed (the first launch can take a while).
4. On the Brev instance page, scroll to the "Using Secure Links" section.
5. Click the arrow icon next to the Shareable URL.
6. Login with your NVIDIA Brev account.
7. Inside Visual Studio Code, continue with the `README`_ instructions.
8. Now you're in the Visual Studio Code dev environment!

.. seealso::

    - `Isaac Launchable Repository`_
    - :ref:`isaac_sim_setup_brev_requirements`
