..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _NVIDIA Brev: https://developer.nvidia.com/brev
.. _Isaac Sim Container: https://catalog.ngc.nvidia.com/orgs/nvidia/containers/isaac-sim

.. _isaac_sim_setup_brev_requirements:

NVIDIA Brev Deployment
############################################

Requirements
---------------------------

The requirements for running |isaac-sim| on NVIDIA Brev are:

1. An NVIDIA Brev account.

Setup
---------------------------

Follow these steps to launch a GPU instance in VM Mode on NVIDIA Brev:

1. Navigate to `NVIDIA Brev`_.
2. Click **Get Started** to sign in or create and account.
3. Click **Create New Instance**

.. figure:: /images/isim_5.0_full_ref_external_brev_start.png
    :align: center
    :alt: Create New Instance

4. Select **1x NVIDIA L40S** GPU.

.. figure:: /images/isim_5.0_full_ref_external_brev_gpu_seelect.png
    :align: center
    :alt: Select your Compute

5. Name the instance and click **Deploy**.

.. figure:: /images/isim_5.0_full_ref_external_brev_deploy.png
    :align: center
    :alt: Configure and Deploy

6. Wait for the VM to be ready.

.. figure:: /images/isim_5.0_full_ref_external_brev_instance_start.png
    :align: center
    :alt: Instance creation

7. Expose ports **49100**, **47998**, and **8210** only to your IP for security and access to WebRTC live streaming. Port 8210 is used by the web viewer when using Docker Compose.

.. figure:: /images/isim_5.0_full_ref_external_brev_expose_ports.png
    :align: center
    :alt: Expose ports

8. Click **Open Notebook** at the top of the page.

.. figure:: /images/isim_5.0_full_ref_external_brev_open_notebook.png
    :align: center
    :alt: Open notebook

9. Open the **Terminal** in the Jupyter Notebook page.

.. figure:: /images/isim_5.0_full_ref_external_brev_notebook.png
    :align: center
    :alt: Terminal access


Running Isaac Sim Container
------------------------------------------------------------------------------------------------

For container deployment and livestreaming, see :ref:`isaac_sim_setup_remote_headless_container` for full setup instructions.

The recommended approach for streaming on a cloud VM is to use **Docker Compose**, which handles volume mounts,
GPU assignment, networking, and health checks automatically. Retrieve the public IP and launch with:

.. code-block:: console

    $ PUBLIC_IP=$(curl -s ifconfig.me)
    $ mkdir -p ~/docker/isaac-sim/{cache/main,cache/computecache,config,data,logs,pkg}
    $ sudo chown -R 1234:1234 ~/docker
    $ ISAACSIM_HOST=$PUBLIC_IP ISAAC_SIM_IMAGE=nvcr.io/nvidia/isaac-sim:6.0.0 \
        docker compose -p isim -f tools/docker/docker-compose.yml up --build -d

Then open ``http://<PUBLIC_IP>:8210`` in a Chromium-based browser.

.. warning::

    |isaac-sim_short| livestreaming is designed for use on private or trusted networks. The streaming
    endpoints do not include authentication or encryption. Make sure the exposed ports are restricted
    to your client IP. If you need broader access, add a reverse proxy with HTTPS/TLS and authentication.
    Users are responsible for securing any public-facing deployments.

.. seealso::

    - :ref:`isaac_sim_setup_remote_headless_container` for manual ``docker run`` instructions
    - :ref:`isaac_sim_docker_compose_deployment` for Docker Compose configuration details
    - :ref:`isaac_sim_manual_livestream_client` for streaming client options
    - `Docker README <https://github.com/isaac-sim/IsaacSim/blob/develop/tools/docker/README.md>`_ for advanced Docker options and multi-instance deployment
