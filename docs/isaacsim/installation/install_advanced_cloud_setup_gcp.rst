..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _Key Pair Guide: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html#create-a-key-pair
.. _Connecting to Your Linux Instance from Windows Using PuTTY: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/putty.html
.. _Visual Studio Code: https://code.visualstudio.com/download
.. _Remote-SSH extension: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh
.. _Create a Linux virtual machine in the Azure portal: https://docs.microsoft.com/en-us/azure/virtual-machines/linux/quick-create-portal
.. _Launch Cloud Shell: https://cloud.google.com/shell/docs/launching-cloud-shell
.. _GPU Zones: https://cloud.google.com/compute/docs/gpus/gpu-regions-zones
.. _Connect to Linux VMs using Google tools: https://cloud.google.com/compute/docs/instances/connecting-to-instance
.. _Default VPC network: https://cloud.google.com/vpc/docs/create-modify-vpc-networks
.. _SSH connection to VM instances: https://cloud.google.com/community/tutorials/ssh-via-iap
.. _Install NVIDIA driver: https://cloud.google.com/compute/docs/gpus/install-drivers-gpu


.. _isaac_sim_setup_gcp_requirements:

Google Cloud Deployment
############################################

Requirements
---------------------------

The requirements for running |isaac-sim| on Google Cloud are:

* A Google Cloud account with Compute Engine access that is able to create a Virtual Machine with GPU support.

* A GCP virtual machine with the following recommended specifications:

    .. tab-set::

        .. tab-item:: T4

          * **GPU**: nvidia-tesla-t4
          * **Machine type**: n1-standard-8 or better
          * **Image**: Ubuntu 22.04 LTS

        .. tab-item:: L4

          * **GPU**: nvidia-l4
          * **Machine type**: g2-standard-4 or better
          * **Image**: Ubuntu 22.04 LTS

Setup
---------------------------

To launch the GCP virtual machine, use the following steps:

#. Search for `GPU Zones`_ with the NVIDIA T4 or L4 GPU model.

#. Create a `Default VPC network`_.

#. Setup `SSH connection to VM instances`_ using a browser.

#. Follow the steps in `Launch Cloud Shell`_ to start Cloud Shell session on GCP.

#. Run the following command in the Cloud Shell session to create a VM. Replace <project_name> and <instance_name>. The zone is set to **us-central1-a** in this example, but can be replaced with the zones from step 1.

    .. tab-set::

        .. tab-item:: T4

            .. code-block:: console

                $ gcloud compute \
                --project "<project_name>" \
                instances create "<instance_name>" \
                --zone "us-central1-a" \
                --machine-type "n1-standard-8" \
                --subnet "default" \
                --metadata="install-nvidia-driver=True" \
                --maintenance-policy "TERMINATE" \
                --accelerator type=nvidia-tesla-t4,count=1 \
                --image "ubuntu-2204-jammy-v20230919" \
                --image-project "ubuntu-os-cloud" \
                --boot-disk-size "100" \
                --boot-disk-type "pd-ssd"

        .. tab-item:: L4

            .. code-block:: console

                $ gcloud compute \
                --project "<project_name>" \
                instances create "<instance_name>" \
                --zone "us-central1-a" \
                --machine-type "g2-standard-4" \
                --subnet "default" \
                --metadata="install-nvidia-driver=True" \
                --maintenance-policy "TERMINATE" \
                --accelerator type=nvidia-l4,count=1 \
                --image "ubuntu-2204-jammy-v20230919" \
                --image-project "ubuntu-os-cloud" \
                --boot-disk-size "100" \
                --boot-disk-type "pd-ssd"

#. Follow the steps in `Connect to Linux VMs using Google tools`_ to connect to the VM.

#. Follow the steps in `Install NVIDIA driver`_.

    .. code-block:: console

        $ curl https://raw.githubusercontent.com/GoogleCloudPlatform/compute-gpu-installation/main/linux/install_gpu_driver.py --output install_gpu_driver.py
        $ sudo python3 install_gpu_driver.py

#. See :doc:`Container Installation </installation/install_container>` to install the Docker and NVIDIA Container Toolkit.

#. Proceed to :ref:`isaac_sim_setup_remote_headless_container`.
