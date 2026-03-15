..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaac_sim_license_faq:

=======================
License FAQ
=======================

.. dropdown:: What license is Isaac Sim released under?
   :open:

   The Isaac Sim source code in the `GitHub repository <https://github.com/isaac-sim/IsaacSim/>`__ is released under the
   `Apache 2.0 License <https://github.com/isaac-sim/IsaacSim?tab=License-1-ov-file#readme>`__.

   Building or running Isaac Sim requires additional components (such as the Omniverse Kit SDK, 3D models, and textures)
   that are covered under separate license terms. See :doc:`/common/license-isaac-sim-additional` for details.

.. dropdown:: Is Isaac Sim free to use for commercial R&D?

   Yes. Isaac Sim is free to use for internal R&D and development purposes. The only exception is if you are
   redistributing Isaac Sim (with Omniverse Kit) as part of an application to third parties, or delivering
   Isaac Sim (with Omniverse Kit) as a service to third parties. In those cases, an
   `NVIDIA Omniverse Enterprise (OVE) license <https://docs.nvidia.com/ai-enterprise/planning-resource/licensing-guide/latest/licensing.html>`__
   is required for the underlying usage of Omniverse Kit.

.. dropdown:: Do I need a license if I only sell simulation outputs (videos, reports, data)?

   No. If you run the simulation internally and only sell the outputs (for example, simulation videos, analytic
   reports, or datasets) to clients, an Omniverse Enterprise license is **not** required.

.. dropdown:: Do I need a license to sell custom code or USD assets that work with Isaac Sim?

   No. If you sell only your custom Python code and ``.usd`` assets to a client, and the client runs them on
   their own Isaac Sim environment, no redistribution fees or royalties to NVIDIA are required. An Omniverse
   Enterprise license is **not** required in this case.

.. dropdown:: Do I need a license to deliver a turn-key Isaac Sim solution to a client?

   Yes. If you provide a turn-key service where you install and configure the entire Isaac Sim (with Omniverse Kit)
   environment on a client's hardware, an
   `NVIDIA Omniverse Enterprise (OVE) license <https://docs.nvidia.com/ai-enterprise/planning-resource/licensing-guide/latest/licensing.html>`__
   **is** required because Isaac Sim (with Omniverse Kit) is being redistributed as part of an application
   or service to a third party.

.. dropdown:: Can I modify and redistribute Isaac Sim?

   You may modify and redistribute the Apache 2.0 licensed source code in compliance with the
   `Apache 2.0 License <https://github.com/isaac-sim/IsaacSim?tab=License-1-ov-file#readme>`__.

   The additional NVIDIA-licensed components (Omniverse Kit SDK, assets, etc.) may not be modified or redistributed
   except as expressly permitted by their license terms. Redistribution of Isaac Sim (with Omniverse Kit) to third
   parties requires an :doc:`NVIDIA Omniverse Enterprise license </common/NVIDIA_Omniverse_License_Agreement>`.
   See :doc:`/common/license-isaac-sim-additional` for specifics.

.. dropdown:: What is the difference between the Isaac Sim open source license and the additional components license?

   Isaac Sim has a dual-license structure:

   - **Isaac Sim source code** — Released under the `Apache 2.0 License <https://github.com/isaac-sim/IsaacSim?tab=License-1-ov-file#readme>`__,
     which permits free use, modification, and redistribution for any purpose, including commercial use.

   - **Additional components** — Building and running Isaac Sim requires additional NVIDIA-owned components such as the
     Omniverse Kit SDK, 3D models, and textures. These are covered under the
     :doc:`NVIDIA Isaac Sim Additional Software and Materials License </common/license-isaac-sim-additional>`,
     which has separate terms regarding use, modification, and redistribution.

   When considering redistribution or service delivery to third parties, it is the additional components (specifically
   Omniverse Kit) that trigger the requirement for an :doc:`Omniverse Enterprise license </common/NVIDIA_Omniverse_License_Agreement>`
   — not the Apache 2.0 source code.

.. dropdown:: Is there a per-user or per-seat limit for using Isaac Sim?

   No. The Isaac Sim source code is released under the `Apache 2.0 License <https://github.com/isaac-sim/IsaacSim?tab=License-1-ov-file#readme>`__,
   which does not impose any per-user, per-seat, or team size restrictions. Any number of developers within your
   organization may install, run, and collaborate on Isaac Sim.

   The :doc:`NVIDIA Isaac Sim Additional Software and Materials License </common/license-isaac-sim-additional>` for the
   additional components (Omniverse Kit SDK, assets, etc.) also does not define per-user limits for internal use.
   Redistribution or service delivery to third parties requires an
   :doc:`NVIDIA Omniverse Enterprise license </common/NVIDIA_Omniverse_License_Agreement>`.

.. dropdown:: Where can I find Omniverse Enterprise pricing?

   Omniverse Enterprise licensing and pricing information is available on the
   `NVIDIA Enterprise Licensing pricing page <https://docs.nvidia.com/ai-enterprise/planning-resource/licensing-guide/latest/pricing.html>`__.

.. dropdown:: What license applies to NVIDIA-provided assets (3D models, textures, etc.)?

   NVIDIA-provided assets are covered under the
   :doc:`NVIDIA Isaac Sim Additional Software and Materials License </common/license-isaac-sim-additional>`.
   Review this license for details on usage rights and restrictions.

.. dropdown:: Where can I find the full license texts?

   - :doc:`Isaac Sim License (Apache 2.0) </common/licenses-isaac-sim>`
   - :doc:`Isaac Sim Additional Software and Materials License </common/license-isaac-sim-additional>`
   - :doc:`Isaac Sim WebRTC Streaming Client License </common/license-isaac-sim-webrtc-streaming-client>`
   - :doc:`NVIDIA Omniverse License </common/NVIDIA_Omniverse_License_Agreement>`
   - :doc:`Licensing Disclaimer </common/licensing-notices-disclaimers>`
   - :doc:`Third-Party Licenses </common/licenses>`

.. dropdown:: Does Isaac Sim include third-party open source software?

   Yes. Isaac Sim includes components licensed under various open source licenses. A list of these
   third-party licenses is available at :doc:`/common/licenses`.

.. dropdown:: Can I use Isaac Sim in an air-gapped or offline environment?

   Yes. You can download the Isaac Sim assets packs for offline use. See the
   :ref:`installation FAQ <isaac_sim_setup_faq>` for instructions on setting up local assets.
   The same license terms apply regardless of whether Isaac Sim is used online or offline.
