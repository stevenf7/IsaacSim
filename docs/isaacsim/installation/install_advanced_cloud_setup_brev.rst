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

2. The :ref:`isaac_sim_setup_livestream_webrtc` app.

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

7. Expose ports **49100** and **47998** only to your IP for security and access to WebRTC live streaming.

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

Follow the instructions below on a terminal:

1. Get the public IP address of the instance:

.. code-block:: console

    $ curl -s ifconfig.me

2. Pull the `Isaac Sim Container`_:

.. code-block:: console

    $ docker pull nvcr.io/nvidia/isaac-sim:6.0.0-dev2

3. Create the cached volume mounts on host:

.. code-block:: console

    $ mkdir -p ~/docker/isaac-sim/cache/main/ov
    $ mkdir -p ~/docker/isaac-sim/cache/main/warp
    $ mkdir -p ~/docker/isaac-sim/cache/computecache
    $ mkdir -p ~/docker/isaac-sim/config
    $ mkdir -p ~/docker/isaac-sim/data/documents
    $ mkdir -p ~/docker/isaac-sim/data/Kit
    $ mkdir -p ~/docker/isaac-sim/logs
    $ mkdir -p ~/docker/isaac-sim/pkg
    $ sudo chown -R 1234:1234 ~/docker/isaac-sim

4. Run the |isaac-sim_short| container with an interactive Bash session:

.. code-block:: console

    $ docker run --name isaac-sim --entrypoint bash -it --gpus all -e "ACCEPT_EULA=Y" --rm --network=host \
        -e "PRIVACY_CONSENT=Y" \
        -v ~/docker/isaac-sim/cache/main:/isaac-sim/.cache:rw \
        -v ~/docker/isaac-sim/cache/computecache:/isaac-sim/.nv/ComputeCache:rw \
        -v ~/docker/isaac-sim/logs:/isaac-sim/.nvidia-omniverse/logs:rw \
        -v ~/docker/isaac-sim/config:/isaac-sim/.nvidia-omniverse/config:rw \
        -v ~/docker/isaac-sim/data:/isaac-sim/.local/share/ov/data:rw \
        -v ~/docker/isaac-sim/pkg:/isaac-sim/.local/share/ov/pkg:rw \
        -u 1234:1234 \
        nvcr.io/nvidia/isaac-sim:6.0.0-dev2

.. note::

    * By using the ``-e "ACCEPT_EULA=Y"`` flag, you accept the license agreement of the image found at :doc:`NVIDIA Omniverse License Agreement</common/NVIDIA_Omniverse_License_Agreement>`.
    * By using the ``-e "PRIVACY_CONSENT=Y"`` flag, you opt-in to the data collection agreement found at :doc:`../common/data-collection`. You may opt-out by not setting this flag.
    * The ``-e "PRIVACY_USERID=<email>"`` flag can optionally be set for tagging the session logs.
    * Add the ``--runtime=nvidia`` flag if there are issues detecting the GPU in the container.

5. Start |isaac-sim_short| with native livestream mode:

.. code-block:: console

    $ PUBLIC_IP=$(curl -s ifconfig.me) && ./runheadless.sh --/exts/omni.kit.livestream.app/primaryStream/publicIp=$PUBLIC_IP --/exts/omni.kit.livestream.app/primaryStream/signalPort=49100 --/exts/omni.kit.livestream.app/primaryStream/streamPort=47998

6. Connect to the same public IP address of the instance using the :ref:`isaac_sim_setup_livestream_webrtc` app.

.. seealso::

    - :ref:`isaac_sim_setup_remote_headless_container`
    - :ref:`isaac_sim_manual_livestream_client`
