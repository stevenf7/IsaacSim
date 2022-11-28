# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
import time

from pxr import Gf

from omni.isaac.core.utils.rotations import gf_quat_to_np_array

import omni.isaac.cortex.math_util as math_util
from omni.isaac.cortex.math_util import to_meters, to_stage_units


class CortexMeasuredPose(object):
    def __init__(self, stamp, pose_pq, timeout):
        self.stamp = stamp
        self.pq = pose_pq
        self.timeout = timeout

    def is_valid(self, time):
        return time - self.stamp < self.timeout


class CortexObject(object):
    """ A cortex object is always in units of meters independent of the stage units. It also has
    accessors for getting the measured pose from the cortex-specific measured pose attributes.

    Note that Isaac Sim defaults to meters, so by default the will be equivalent to the underlying
    stage units. However, if the stage is created in a different set of units these accessors create
    a consistent SI unit API for the object.
    """

    def __init__(self, obj, sync_throttle_dt=None):
        """ Create this cortex object to wrap the provided core API object. 

        The sync_throttle_dt ensures that calls to sync_to_measured_pose() will not sync within
        sync_throttle_dt of one another. i.e. it throttles the rate to < 1./sync_throttle_dt.
        """
        self.obj = obj
        self.time_at_last_sync = None
        self.sync_throttle_dt = sync_throttle_dt
        self.measured_pose = None
        self.sync_sim = False

    @property
    def name(self):
        """ The name of the underlying object.
        """
        return self.obj.name

    @property
    def prim(self):
        """ The underlying USD prim representing this object.
        """
        return self.obj.prim

    def set_world_pose(self, position, orientation):
        """ Set the object's world pose in units of meters.
        """
        # TODO: units conversion no longer needed
        self.obj.set_world_pose(to_stage_units(position), orientation)

    def get_world_pose(self):
        """ Get the object's world pose in units of meters.
        """
        # TODO: units conversion no longer needed
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

    def set_measured_pose(self, measured_pose):
        self.measured_pose = measured_pose

    def has_measured_pose(self):
        """ Returns the measured pose stored in this cortex object.

        If the object doesn't have the attributes, returns False. Also, if the information is too
        old based on its stamp and the timeout information, returns False. Otherwise, the
        information is available and valid.
        """
        return self.measured_pose is not None and self.measured_pose.is_valid(time.time())

    def get_measured_pq(self):
        """ Returns the measured pose as a (p,q) tuple in meters.
        
        This method doesn't check whether the measured pose is available. Use has_measured_pose() to
        verify.
        """
        return self.measured_pose.pq

    def get_measured_T(self):
        """ Returns the measured pose as a 4x4 homogeneous matrix in units of meters.

        This method doesn't check whether the measured pose is available. Use has_measured_pose() to
        verify.
        """
        p, q = self.measured_pose.pq
        return math_util.pq2T(p, q)

    def sync_to_measured_pose(self, use_throttle=True):
        """ Syncs the pose of the underlying USD object to match the measured pose.
        
        If use_throttle is True (default) when this method will prevent two syncs from happening
        within sync_throttle_dt seconds of one another.  i.e. it throttles the rate to <
        1./sync_throttle_dt.

        This method doesn't check whether the measured pose is available. Use has_measured_pose() to
        verify.
        """
        current_time = time.time()

        if not self.has_measured_pose():
            # There's nothing to sync to.
            return

        if (
            self.time_at_last_sync is not None
            and use_throttle
            and self.sync_throttle_dt is not None
            and (current_time - self.time_at_last_sync < self.sync_throttle_dt)
        ):
            # Don't sync this cycle.
            return

        # Write the measured pose to the object's USD. The TensorAPI will automatically pull that
        # in. (Note if we just use the core API, that'll directly access the tensor API and the USD
        # won't be updated if the object is asleep (w.r.t. PhysX), so visually the object won't
        # sync until it's moved.
        self.sync_tensor_api_to_usd(*self.get_measured_pq())
        self.time_at_last_sync = current_time

    def sync_tensor_api_to_usd(self, p, q):
        p = p.astype(float)
        q = q.astype(float)

        p_attr = self.obj.prim.GetAttribute("xformOp:translate")
        p_attr.Set(Gf.Vec3d(p[0], p[1], p[2]))

        w, x, y, z = q
        q_attr = self.obj.prim.GetAttribute("xformOp:orient")
        q_attr.Set(Gf.Quatd(w, Gf.Vec3d(x, y, z)))

        verbose = False
        if verbose:
            p_gf = p_attr.Get()
            q_gf = q_attr.Get()
            print("[{}] p: {}, p_gf: {} -- q: {}, q_gf: {}".format(self.name, p, p_gf, q, q_gf))
