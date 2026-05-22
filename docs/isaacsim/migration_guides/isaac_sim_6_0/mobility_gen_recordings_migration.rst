..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _mobility_gen_recordings_migration:

======================
MobilityGen Recordings
======================

Recordings made with Isaac Sim 5.x store robot state in ``state/common/*.npy`` files
(pickled Python dicts).  Starting with Isaac Sim 6.0, MobilityGen switched to
``state/common/*.npz`` (named NumPy arrays).  The reader only supports the new format,
so older recordings must be converted before replay.

To convert all recordings in a directory tree in-place, run:

.. code-block:: bash

   ./python.sh \
       standalone_examples/replicator/mobility_gen/migrate_recordings.py \
       ~/MobilityGenData/recordings --recursive

The script takes a positional recording path; pass ``--recursive`` when the
path is a parent directory containing multiple recordings.

If a recording still uses the old format, the reader will log an error and produce
zero steps — convert it with the script above before replaying.

For the MobilityGen tutorial, see :ref:`isaac_sim_app_tutorial_replicator_mobility_gen`.
