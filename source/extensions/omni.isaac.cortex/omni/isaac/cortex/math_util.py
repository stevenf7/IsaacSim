# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

""" Module containing a collection of math utilities.

Conventions:
- Quaternion has elements (w,x,y,z) compatible with the core API.
- Function names with "T" are referring to a homogeneous transform matrix.
- Functions with pq in their name are referencing the "position, quaternion" rotation
  representation. For instance, T2pq(T) takes a transform represented as a homogeneous transform
  matrix T and converts it to a pair (p,q) where p is the position, and q is the quaternion
  rotation. Note: "2" is shorthand for "to".
"""

from __future__ import print_function

import copy
import math
import numpy as np
from numpy.linalg import norm

from omni.isaac.core.utils.rotations import quat_to_rot_matrix, matrix_to_euler_angles, euler_angles_to_quat
from omni.isaac.core.utils.math import normalized
from omni.isaac.core.utils.stage import get_stage_units


def to_meters(p_stage):
    """ Converts the position p_stage from stage units to meters. By default, a stage uses meters,
    so this method does nothing. But if the world is constructed with different units, this method
    will convert those units to meters.
    """
    return p_stage * get_stage_units()


def T_to_meters(T_stage):
    """ Convert the homogeneous transform to meters. This method simply makes a copy of T_stage and
    converts the translation components to meters using a call to to_meters().
    """
    T_meters = copy.deepcopy(T_stage)
    T_meters[:3, 3] = to_meters(T_meters[:3, 3])
    return T_meters


def to_stage_units(p_meters):
    """ Converts the position p_meters from meters to stage units.
    """
    return p_meters / get_stage_units()


def transform_dist(T1, T2, position_scalar, rotation_matrix_scalar):
    """ Measures the distance between the provided transforms.
    
    Generally translation and rotational distances are not composable into a unique distance metric
    since transform distance between two geometric objects in a scene is really a function of the
    geometry of the objects (e.g. distance between surface points) rather than an object-independent
    function of translation and rotation.
    
    However, a reasonable proxy is to measure the simple Euclidean distance between the position
    components and rotation matrices. Those two components won't be comparable, but they can be
    weighed together into a good metric.

    <description of dist between R1, R2>

    Note that a rotation matrix is defined by placing the frame's (normalized) axes into the columns
    of a matrix. Specifically, if the frame is defined by {o, ax, ay, az}, where o is the origin
    (position) and a{x,y,z} are the three 3D axes, the rotation matrix is R = [ax, ay, az].
    Therefore, the Euclidean distance between two rotation matrices R1 and R2 is simply the distance
    between end-points of the axes of the two frames extending from a common origin.

    Equation:

      dist = position_scalar * |o1 - o2| + rotation_matrix_scalar * |R1 - R2|

    params
    - T1, T2: The transforms to be compared. These should both be homogeneous transform matrices.
    - position_scalar: The scalar weight on the position distance.
    - rotation_matrix_scalar: the scalar weight on the rotation matrix distance.

    """
    R1, p1 = unpack_T(T1)
    R2, p2 = unpack_T(T2)
    n = np.linalg.norm
    return position_scalar * n(p2 - p1) + rotation_matrix_scalar * n(R2 - R1)


def transforms_are_close(T1, T2, p_thresh, R_thresh, verbose=False):
    """ Measures whether the two provided transforms T1 and T2 are close to each other.

    T1, T2 should both be 4x4 homogeneous matrices. p_thresh is the "close" threshold for the
    position difference, and R_thresh is the "close" threshold for the average rotation difference
    of the axes. 

    See the comment in transform_dist() for a description of rotational distances.

    Formula:

      close = |p1-p2| <= p_thresh and |R1-R2|/3 <= R_thresh

    Note that the rotation matrix columns are the frame axes.
    """
    Te = T1 - T2
    Re, pe = unpack_T(Te)

    npe = np.linalg.norm(pe)
    nRe = np.linalg.norm(Re)

    # Since there are three axes, we look at the average rotational error to make the units
    # comparable.
    thresh_met = npe <= p_thresh and nRe / 3 <= R_thresh
    if verbose:
        print("npe: {} vs p_thresh: {}; nRe: {} vs R_thresh: {}".format(npe, p_thresh, nRe, R_thresh))
    return thresh_met


def matrix_to_quat(mat: np.ndarray) -> np.ndarray:
    """ Converts the provided rotation matrix into a quaternion in (w, x, y, z) order.
    """
    return euler_angles_to_quat(matrix_to_euler_angles(mat))


class Quaternion:
    def __init__(self, vals):
        """ vals should be ordered [w,x,y,z]
        """
        self.vals = vals

    def __mul__(self, other):
        w0, x0, y0, z0 = self.vals
        w1, x1, y1, z1 = other.vals

        w = w0 * w1 - x0 * x1 - y0 * y1 - z0 * z1
        x = w0 * x1 + x0 * w1 + y0 * z1 - z0 * y1
        y = w0 * y1 - x0 * z1 + y0 * w1 + z0 * x1
        z = w0 * z1 + x0 * y1 - y0 * x1 + z0 * w1

        return Quaternion([w, x, y, z])


def usd_quat_to_numpy(quat):
    """ Converts a USD quaternion to a numpy vector in (w, x, y, z) order.
    """
    qw = quat.GetReal()
    qxyz = quat.GetImaginary()
    return np.array([qw, qxyz[0], qxyz[1], qxyz[2]])


def reorder_q_xyzw2wxyz(q):
    """ Reorders the given quaternion from (x, y, z, w) order (ROS convention) to (w, x, y, z) order
    (Isaac Sim core API convention).
    """
    return np.array([q[3], q[0], q[1], q[2]])


def reorder_q_wxyz2xyzw(q):
    """ Reorders the given quaternion from (w, x, y, z) order (Isaac Sim core API convention) to 
    (x, y, z, w) order (ROS convention).
    """
    return np.array([q[1], q[2], q[3], q[0]])


def to_homogeneous_vec(v):
    """ Converts the provided 3D vector into a 4D homogeneous vector padded with 1 in the final
    dimension.
    """
    hv = np.ones(4)
    hv[:3] = v
    return hv


def apply_T(T, v):
    """ Applies the 4x4 homogeneous transform matrix T to the provided 3D vector v. Returns the
    transformed 3D vector.
    """
    return T.dot(to_homogeneous_vec(v))[:3]


def T2pq(T):
    """ Converts a 4d homogeneous matrix to a position-quaternion representation.
    """
    R, p = unpack_T(T)
    return p, matrix_to_quat(R)


def pq2T(p, q):
    """ Converts a pose given as (<position>,<quaternion>) to a 4x4 homogeneous transform matrix.
    """
    return pack_Rp(quat_to_rot_matrix(q), p)


def R2T(R):
    """ Expands a rotation matrix to be a 4x4 homogeneous matrix by padding it with a zero position
    vector.
    """
    T = np.eye(4)
    T[:3, :3] = R
    return T


def proj_orth(v1, v2, normalize_res=False, eps=1e-5):
    """ Projects v1 orthogonal to v2. If v2 is zero (within eps), v1 is returned
    unchanged. If normalize_res is true, normalizes the result before returning.
    """
    v2_norm = norm(v2)
    if v2_norm < eps:
        return v1

    v2n = v2 / v2_norm
    v1 = v1 - np.dot(v1, v2n) * v2n
    if normalize_res:
        return normalized(v1)
    else:
        return v1


def unpack_T(T):
    """ Returns the rotation matrix and translation separately

    Returns (R, p)
    """
    return T[:3, :3], T[:3, 3]


def unpack_R(R):
    """ Returns the individual axes of the rotation matrix.
    """
    return R[:3, 0], R[:3, 1], R[:3, 2]


def pack_R(ax, ay, az, as_homogeneous=False):
    """ Returns a rotation matrix with the supplied axis columns.

    R = [ax, ay, az]
    """
    if as_homogeneous:
        R = np.eye(4)
    else:
        R = np.eye(3)
    R[:3, 0] = ax
    R[:3, 1] = ay
    R[:3, 2] = az
    return R


def pack_Rp(R, p):
    """ Packs the provided rotation matrix (R) and position (p) into a homogeneous transform
    matrix.
    """
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = p
    return T


def invert_T(T):
    """ Inverts the provided transform matrix using the explicit formula leveraging the
    orthogonality of R and the sparsity of the transform.

    Specifically, denote T = h(R, t) where h(.,.) is a function mapping the rotation R and
    translation t to a homogeneous matrix defined by those parameters. Then

      inv(T) = inv(h(R,t)) = h(R', -R't).
    """
    R, t = unpack_T(T)
    R_trans = R.T
    return pack_Rp(R_trans, -R_trans.dot(t))


def numpy_vec(vec3):
    """ Create a 3D numpy vector from a vec3 message type.

    vec3 can be any type with fields x, y, z. Returns numpy vector with
    elements [x,y,z].
    """
    v = np.array([vec3.x, vec3.y, vec3.z])
    return v


def numpy_quat(quat, normalize=False):
    """ Create a 4D quaternion vector from a quaternion message type.

    quat can be any type with fields x, y, z, w. Returns numpy vector with
    elements [x,y,z,w] (in that order to be compatible with the
    tf.transformations library).
    """

    q = np.array([quat.x, quat.y, quat.z, quat.w])
    if normalize:
        q /= np.linalg.norm(q)
    return q


class ExpAvg(object):
    """ Computes the exponential weighted average of a stream of values.

    Represents the weighted average defined recursively by
        
      avg_val_t = gamma avg_val_{t-1} + (1-gamma) val_t

    Expanding recursively, this gives the following weighed average

      avg_val_t = w_1 val_1 + ... + w_t val_t
    
    with w_t = (1-gamma) gamma^t. These weights are geometric so the sum is
    
      w_1 + ... + w_t = 1-gamma^t

    which converges exponentially to 1 as t increases. So the running average converges
    exponentially on a running geometrically weighted average, updating continually with each
    incoming value.

    The current average value can be accessed by self.val_avg.
    """

    def __init__(self, gamma, prior_avg=None):
        """ Initialize the tool to use the provided gamma. See the top-level comment for gamma
        semantics. Intuitively, gammas closer to 1 correspond to larger effective window size, while
        gammas closer to 0 correspond to smaller window size.

        If a ballpark estimate of the average is available, that can be provided as prior_avg to
        reduce bias of the initial estimates. Providing a prior_avg will set the initial value of
        self.val_avg to the prior_avg, and that prior value will be available immediately via
        self.val_avg.
        
        By default, that prior value is None, so it will take one update before an average value is
        available.
        """
        self.gamma = gamma
        self.prior_avg = prior_avg
        self.reset()

    def reset(self):
        """ Reset this exponential average, clearing the previous value.
        """
        self.val_avg = self.prior_avg

    def is_ready(self):
        """ Returns true if at least one value has been consumed, and false otherwise.
        """
        return self.val_avg is not None

    def update(self, val):
        """ Update the average with the provided value. When the first value is consumed, the
        average is set to that value explicitly is no prior value is specified.
        """
        if self.val_avg is None:
            self.val_avg = val
            return

        self.val_avg = self.gamma * self.val_avg + (1.0 - self.gamma) * val


def proj_R(R):
    """ Projects a rotational matrix to make it a valid rotation.

    The projection is performed by first converting the rotation matrix components into a
    quaternion followed by normalizing the quaternion.
    """

    q = matrix_to_quat(R)
    q /= np.linalg.norm(q)
    R = quat_to_rot_matrix(q)
    return R


def proj_T(T):
    """ Projects the rotational matrix portion of the provide homogeneous transform matrix to make
    it a valid rotation.

    The projection is performed by first converting the rotation matrix components into a
    quaternion followed by normalizing the quaternion.

    The modification is not performed inline, so a copy of the transform is created for returning
    and the parameter t is left untouched.
    """
    T = copy.deepcopy(T)
    T[:3, :3] = proj_R(T[:3, :3])
    return T


def make_rotation_matrix(az_dominant, ax_suggestion):
    """ Constructs a rotation matrix with the z-axis given by az_dominant (normalized), and the
    x-axis given by a orthogonally projected version of ax_suggestion. The y-axis is formed via the
    right hand rule.
    """
    az = normalized(az_dominant)
    ax = proj_orth(ax_suggestion, az)
    ay = np.cross(az, ax)
    return pack_R(ax, ay, az)
