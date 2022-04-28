# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
import time

from pxr.Vt import Bool

from omni.isaac.core.utils.rotations import gf_quat_to_np_array

import math_util
from math_util import to_meters, to_stage_units


class CortexObject(object):
    """ A cortex object is always in units of meters independent of the stage units. It also has
    accessors for getting the measured pose from the cortex-specific measured pose attributes.
    """

    def __init__(self, obj, sync_throttle_dt=None):
        self.obj = obj
        self.time_at_last_sync = None
        self.sync_throttle_dt = sync_throttle_dt

    @property
    def name(self):
        return self.obj.name

    @property
    def prim(self):
        return self.obj.prim

    def set_world_pose(self, position, orientation):
        """ Set the object's world pose in units of meters.
        """
        self.obj.set_world_pose(to_stage_units(position), orientation)

    def get_world_pose(self):
        """ Get the object's world pose in units of meters.
        """
        position, orientation = self.obj.get_world_pose()
        return to_meters(position), orientation

    def get_transform(self):
        """ Returns the object's world pose (in meters) as a 4x4 homogeneous matrix.
        """
        position, orientation = self.get_world_pose()
        return math_util.pq2T(position, orientation)

    def get_T(self):
        """ Convenience accessor for get_transform() using T naming convention.
        """
        return self.get_transform()

    def has_cortex_measured_pose_attributes(self):
        """ Returns true if the underlying USD object has the cortex measured pose attributes.
        """
        prim = self.obj.prim
        return (
            prim.HasAttribute("cortex:measured_pose:stamp")
            and prim.HasAttribute("cortex:measured_pose:position")
            and prim.HasAttribute("cortex:measured_pose:orient")
            and prim.HasAttribute("cortex:measured_pose:timeout")
        )

    def has_measured_pose(self):
        """ Returns the measured pose stored in this cortex object.

        If the object doesn't have the attributes, returns False. Also, if the information is too
        old based on its stamp and the timeout information, returns False. Otherwise, the
        information is available and valid.
        """
        if not self.has_cortex_measured_pose_attributes():
            return False

        # Ignore transforms more than a quarter of a second old.
        prim = self.obj.prim
        measured_pose_stamp = prim.GetAttribute("cortex:measured_pose:stamp").Get()
        measured_pose_timeout = prim.GetAttribute("cortex:measured_pose:timeout").Get()
        return time.time() - measured_pose_stamp < measured_pose_timeout

    def get_measured_pq(self):
        """ Returns the measured pose as a (p,q) tuple in meters.
        
        This method doesn't check whether the measured pose is available. Use has_measured_pose() to
        verify.
        """
        prim = self.obj.prim
        gf_p = prim.GetAttribute("cortex:measured_pose:position").Get()
        gf_q = prim.GetAttribute("cortex:measured_pose:orient").Get()

        p = to_meters(np.array(gf_p))
        q = gf_quat_to_np_array(gf_q)

        return p, q

    def get_measured_T(self):
        """ Returns the measured pose as a 4x4 homogeneous matrix in units of meters.

        This method doesn't check whether the measured pose is available. Use has_measured_pose() to
        verify.
        """
        p, q = self.get_measured_pq()
        return math_util.pq2T(p, q)

    def sync_to_measured_pose(self):
        """ Syncs the pose of the underlying USD object to match the measured pose.

        This method doesn't check whether the measured pose is available. Use has_measured_pose() to
        verify.
        """
        if not self.has_measured_pose():
            return

        if self.time_at_last_sync is None:
            self.time_at_last_sync = time.time()

        if self.sync_throttle_dt is not None and (time.time() - self.time_at_last_sync < self.sync_throttle_dt):
            return

        prim = self.obj.prim
        p, q = self.get_measured_pq()
        self.obj.set_world_pose(to_stage_units(p), q)

        self.time_at_last_sync = time.time()

    def set_sync_sim(self, sync_sim):
        """ Sets a the object USD cortex:sync_sim attribute to the provided value. Setting it to
        True will cause cortex_sim to sync the simulated version of the object with this object pose
        if a sim world exists.
        """
        self.obj.prim.GetAttribute("cortex:sync_sim").Set(Bool(sync_sim))

    def sync_sim(self):
        """ Sets the cortex:sync_sim attribute to True to cause a sync if there's a sim world.
        """
        self.set_sync_sim(True)
