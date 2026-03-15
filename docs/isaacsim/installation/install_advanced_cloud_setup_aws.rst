..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _key pair: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html
.. _security group: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html
.. _DCV Client: https://www.amazondcv.com
.. _PuTTY: https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html
.. _AWS Marketplace: https://aws.amazon.com/marketplace/search/results?searchTerms=isaac+sim
.. _Isaac Sim Container: https://catalog.ngc.nvidia.com/orgs/nvidia/containers/isaac-sim

.. _isaac_sim_setup_aws_requirements:

AWS Deployment
############################################

Requirements
---------------------------

The requirements for running |isaac-sim| on Amazon Web Services (AWS) are:

1. An AWS account that is able to launch an EC2 instance with RTX GPU support.

2. An Amazon EC2 `key pair`_ for authentication.

3. An Amazon EC2 `security group`_ to control access to ports:

   - TCP Port 22 for SSH
   - TCP Port 8443 for DCV
   - TCP Port 49100 for WebRTC streaming
   - UDP Port 47998 for WebRTC streaming

4. `PuTTY`_, or other SSH terminal client to connect to the AMI instance.

5. `DCV Client`_ or Remote Desktop app (For Windows EC2 instance).

Setup
---------------------------

Follow these steps to launch an AWS EC2 instance:

1. Navigate to the `AWS Marketplace`_ and search for "isaac sim".
2. Select one of the instance type below:

.. tab-set::
    .. tab-item:: Linux Instance
        :sync: linux

        **NVIDIA Isaac Sim™ Development Workstation (Linux)**

        - This will create an EC2 instance based on Ubuntu.

    .. tab-item:: Windows Instance
        :sync: windows

        **NVIDIA Isaac Sim™ Development Workstation (Windows)**

        - This will create an EC2 instance based on Windows Server.

3. To deploy an AWS EC2 instance, click the **View purchase options** button.
4. If you have not already subscribed to the software, you will need to *Accept Terms* the first time. (This may take a few minutes to complete.)
5. When the subscription is complete, click the **Continue to Configuration** button.
6. On the *Configure this software* page, click the **Continue to Launch** button.
7. On the *Launch this software* page:

   - Set the **Choose Action** option to **Launch through EC2**.
   - Click the **Launch** button.

8.  On the *Launch an instance* page, name your instance.
9.  Set the *Instance type* to **g6e.2xlarge** or **g7e.8xlarge**, if not already listed.
10. Set the *Key Pair (login)* to use your pre-configured `key pair`_.
11. In the *Network settings* section, select the **Select existing security group** option. In the **Common security groups** dropdown, select your `security group`_.
12. In the **Summary** section on the right side of the page, click **Launch instance**.
13. Locate your named instance in the table. It will take a few moments for the instance state to change from *Initializing* to *Running*. Once it's running, it's available to be connected to.

Connect
---------------------------

Before you log in, make sure that:

- The AMI instance is running
- `PuTTY`_ (or other SSH terminal software) is installed
- The `DCV Client`_ is installed
- Your `key pair`_ is created

Follow the instructions below depending on the OS you are running and the instance type:

.. tab-set::
    .. tab-item:: Linux Instance
        :sync: linux

        1. Copy the Public IP Address of your instance. You can find this by:

           - Clicking the checkbox next to your instance to select it.

           - In the information panel below the table, find the **Public IPv4 address** and copy it.

        2. Open up PuTTY

           - In the *Host Name (or IP Address)* input, paste your instances Public IPv4 address.

           - Expand *Connection > SSH > Auth >* **Credentials**. Browse to the location of your Key Pair, and select it.

           - Select **Open** in the PuTTY dialog to connect.

           .. note:: Using the Terminal, you can connect using the command ``ssh -i <my_key_pair>.pem ubuntu@<public_ip>``.

        3. When you are connected to the AMI, change the password. The password **must** be changed for DCV to connect in a later step.

           - Change the password for the Ubuntu account in order to use the DCV client. Use the following command to change the password: ``sudo passwd ubuntu``.

           .. note:: The password needs to be set via SSH each time a new instance is created, this is by design for security.

           - Enter a new password.

           - Check your session is running by using the following command: ``sudo dcv list-sessions``. (There should be a 'console' session running.)

    .. tab-item:: Windows Instance
        :sync: windows

        #. Select your instance from the EC2 page and from the toolbar select **Connect**.

        #. On the *Connect to instance* page select the **RDP Client** tab.

        #. Set your username and then select **Get password**.

        #. Upload your private key file associated with the instance and select **Decrypt password**.

        #. Use this username and password to log in when you connect with the `DCV Client`_ or Remote Desktop app.

Connect to the Instance with DCV Client
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `DCV Client`_ is available for Windows, macOS, and Linux. Install it on your local machine, then:

1. Open the locally installed `DCV Client`_ and enter the Public IP Address of your instance in this format ``https://<public_ip>:8443``, followed by clicking **Connect**.

   - If you see the Server Identity Check message, click **Trust and Connect**.

   - Log in by entering the username ``ubuntu`` (or your Windows username) and the password that was set in a previous step, followed by clicking **Login**.

   - The desktop GUI will now be displayed in the DCV window.

.. note:: You can also use the DCV Web Browser Client by navigating to ``https://<public_ip>:8443`` on a browser.

You have now logged in and your AWS instance is ready for use.


Running Isaac Sim
------------------------------------------------------------------------------------------------

1. Follow the instructions below depending on the EC2 instance type selected in the previous section:

.. tab-set::
    .. tab-item:: Linux Instance
        :sync: linux

        1. Open Terminal and run the commands below:

        .. code-block:: console

            sudo chown -R ubuntu:root /opt/IsaacSim
            cd ~/IsaacSim
            ./post_install.sh
            ./warmup.sh
            ./isaac-sim.sh

        .. note:: The warm up script may take 15 minutes or longer to complete.

    .. tab-item:: Windows Instance
        :sync: windows

        1. Using the File Explorer, navigate to ``C:\IsaacSim``.
        2. Run ``post_install.bat``.
        3. Run ``warmup.bat``.
        4. Run ``isaac-sim.bat``.

        .. note:: The warm up script may take 15 minutes or longer to complete.

2.  Proceed to :ref:`isaac_sim_intro_quickstart_series` to begin the first Basic Tutorial.

.. seealso:: :doc:`developer_workstations:aws/overview`


Running Isaac Sim Container
------------------------------------------------------------------------------------------------

.. warning::

    |isaac-sim_short| livestreaming is designed for use on private or trusted networks. The streaming
    endpoints do not include authentication or encryption. When deploying on cloud VMs, restrict the
    streaming ports (49100/tcp, 47998/udp, 8210/tcp) to your client IP in the EC2 Security Group rather
    than allowing all traffic. If you need broader access, add a reverse proxy with HTTPS/TLS and
    authentication. Users are responsible for securing any public-facing deployments.

1. Follow the instructions below on a Linux EC2 instance:

.. tab-set::
    .. tab-item:: Linux Instance
        :sync: linux

        1. Open ports for WebRTC Streaming:

        .. code-block:: console

            sudo ufw allow 49100/tcp comment 'Isaac Sim WebRTC signal'
            sudo ufw allow 47998/udp comment 'Isaac Sim WebRTC stream'
            sudo ufw allow 8210/tcp  comment 'Isaac Sim web viewer (Docker Compose)'
            sudo ufw reload

        Also add corresponding inbound rules to the EC2 **Security Group**:

        .. list-table::
            :widths: 15 15 70
            :header-rows: 1

            * - Port
              - Protocol
              - Purpose
            * - ``49100``
              - TCP
              - WebRTC signaling
            * - ``47998``
              - UDP
              - WebRTC media stream
            * - ``8210``
              - TCP
              - Web viewer (Docker Compose only)

        Restrict the **Source** to your client IP (e.g. ``<your-ip>/32``) rather than ``0.0.0.0/0`` to avoid exposing the unauthenticated stream to the public Internet.

        2. Install the |nv| Container Toolkit:

        .. code-block:: console

            # Configure the repository
            $ curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
                && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
                sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
                sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list \
                && \
                sudo apt-get update

            # Install the NVIDIA Container Toolkit packages
            $ sudo apt-get install -y nvidia-container-toolkit
            $ sudo systemctl restart docker

            # Configure the container runtime
            $ sudo nvidia-ctk runtime configure --runtime=docker
            $ sudo systemctl restart docker

            # Verify NVIDIA Container Toolkit
            $ docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi

        3. Pull the `Isaac Sim Container`_:

        .. code-block:: console

            $ docker pull nvcr.io/nvidia/isaac-sim:6.0.0-dev2

        4. Create the cached volume mounts on host:

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

        5. Run the |isaac-sim_short| container with an interactive Bash session:

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

        6. Start |isaac-sim_short| with native livestream mode:

        .. code-block:: console

            $ PUBLIC_IP=$(curl -s ifconfig.me) && ./runheadless.sh --/exts/omni.kit.livestream.app/primaryStream/publicIp=$PUBLIC_IP --/exts/omni.kit.livestream.app/primaryStream/signalPort=49100 --/exts/omni.kit.livestream.app/primaryStream/streamPort=47998

        7. Connect to the same public IP address of the instance using the :ref:`isaac_sim_setup_livestream_webrtc` app.

        Alternatively, use Docker Compose to deploy |isaac-sim_short| with a browser-based web viewer instead of the native streaming client:

        .. code-block:: console

            $ ISAACSIM_HOST=$PUBLIC_IP ISAAC_SIM_IMAGE=nvcr.io/nvidia/isaac-sim:6.0.0-dev2 \
                docker compose -p isim -f tools/docker/docker-compose.yml up --build -d

        Then open ``http://<PUBLIC_IP>:8210`` in a Chromium-based browser. See :ref:`isaac_sim_docker_compose_deployment` or the `Docker README <https://github.com/isaac-sim/IsaacSim/blob/develop/tools/docker/README.md>`_ for full details.

.. seealso::

    - :ref:`isaac_sim_setup_remote_headless_container`
    - :ref:`isaac_sim_manual_livestream_client`
