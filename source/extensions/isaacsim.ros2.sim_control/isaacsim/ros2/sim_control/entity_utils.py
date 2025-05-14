# Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import re

import carb
import isaacsim.core.utils.prims as prim_utils
import omni.usd
from geometry_msgs.msg import Accel, Point, Pose, Quaternion, Twist, Vector3
from pxr import Gf, UsdGeom, UsdPhysics
from simulation_interfaces.msg import EntityState, Result
from std_msgs.msg import Header


def get_filtered_entities(filter_pattern=None):
    """Get filtered entities based on regex pattern

    Args:
        filter_pattern (str, optional): Regex pattern to filter entities

    Returns:
        tuple: (filtered_entities, error_message) - list of filtered entity paths and error message if any
    """
    # Get all prim paths from stage
    stage = omni.usd.get_context().get_stage()
    if not stage:
        return [], "USD Stage not available"

    # Get all prims from stage
    all_prim_paths = [prim.GetPath().pathString for prim in stage.Traverse()]

    # Apply name filter if provided
    if filter_pattern:
        try:
            # Use the filter as a regex pattern to match prim paths
            regex = re.compile(filter_pattern)
            filtered_prims = [path for path in all_prim_paths if regex.search(path)]
            return filtered_prims, ""
        except re.error as e:
            return [], f"Invalid regex pattern: {e}"
    else:
        # No filter, return all prims
        return all_prim_paths, ""


async def get_entity_state(entity_path):
    """Get state for a single entity

    Args:
        entity_path (str): Path to the entity

    Returns:
        tuple: (entity_state, error_message, status_code) - EntityState object, error message if any,
              and status code (Result.RESULT_OK, Result.RESULT_NOT_FOUND, etc.)
    """
    # Check if entity exists
    if not prim_utils.is_prim_path_valid(entity_path):
        return None, f"Entity '{entity_path}' does not exist", Result.RESULT_NOT_FOUND

    # Get the prim
    prim = prim_utils.get_prim_at_path(entity_path)

    # Get the frame_id - use isaac:nameOverride if available and not empty, otherwise use prim name
    if prim.HasAttribute("isaac:nameOverride"):
        override_value = prim.GetAttribute("isaac:nameOverride").Get()
        if override_value and override_value.strip():
            frame_id = override_value
        else:
            frame_id = prim.GetName()
    else:
        # Extract just the name part from the full path
        frame_id = prim.GetName()

    # Initialize the entity state
    entity_state = EntityState()
    entity_state.header = Header(frame_id=frame_id, stamp=Header().stamp)

    # Get the pose (position and orientation) using UsdGeom
    try:
        # TODO:  Update to use isaacsim.core.experimental.prims to allow fabric support
        # Get the xformable
        xformable = UsdGeom.Xformable(prim)

        # Get the world transform matrix
        world_transform = xformable.ComputeLocalToWorldTransform(0)  # time=0 for current time

        # Extract position from matrix
        position = world_transform.ExtractTranslation()

        # Extract rotation as quaternion
        rotation = world_transform.ExtractRotationQuat()

        # Set the pose in the response
        entity_state.pose = Pose(
            position=Point(x=position[0], y=position[1], z=position[2]),
            orientation=Quaternion(
                x=rotation.GetImaginary()[0],
                y=rotation.GetImaginary()[1],
                z=rotation.GetImaginary()[2],
                w=rotation.GetReal(),
            ),
        )
    except Exception as pose_error:
        carb.log_warn(f"Error getting pose for {entity_path}: {pose_error}")
        # Fallback to identity pose
        entity_state.pose = Pose(
            position=Point(x=0.0, y=0.0, z=0.0), orientation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
        )

    # Check if the prim has a rigid body API
    has_rigid_body = prim.HasAPI(UsdPhysics.RigidBodyAPI)

    # Set velocities and accelerations to zero by default
    entity_state.twist = Twist(linear=Vector3(x=0.0, y=0.0, z=0.0), angular=Vector3(x=0.0, y=0.0, z=0.0))
    entity_state.acceleration = Accel(linear=Vector3(x=0.0, y=0.0, z=0.0), angular=Vector3(x=0.0, y=0.0, z=0.0))

    if has_rigid_body:
        # For rigid body prims, get velocities using RigidBody View API
        try:
            # Import the RigidPrim view
            from isaacsim.core.prims import RigidPrim

            # Create a RigidPrim view for the rigid body prim
            rigid_prim = RigidPrim(prim_path=entity_path)

            # Get linear velocity
            lin_vel = rigid_prim.get_linear_velocity()
            if lin_vel is not None:
                try:
                    # Ensure all values are converted to float to avoid type errors
                    entity_state.twist.linear = Vector3(x=float(lin_vel[0]), y=float(lin_vel[1]), z=float(lin_vel[2]))
                except (TypeError, ValueError, IndexError) as e:
                    carb.log_warn(f"Cannot convert linear velocity to float for '{entity_path}': {e}")

            # Get angular velocity
            ang_vel = rigid_prim.get_angular_velocity()
            if ang_vel is not None:
                try:
                    # Ensure all values are converted to float to avoid type errors
                    entity_state.twist.angular = Vector3(x=float(ang_vel[0]), y=float(ang_vel[1]), z=float(ang_vel[2]))
                except (TypeError, ValueError, IndexError) as e:
                    carb.log_warn(f"Cannot convert angular velocity to float for '{entity_path}': {e}")
        except Exception as vel_error:
            carb.log_warn(f"Error getting velocities for rigid body '{entity_path}': {vel_error}")
            # Velocities remain at zero if there was an error

    return entity_state, "", Result.RESULT_OK


def create_empty_entity_state():
    """Create an empty entity state with default values

    Returns:
        EntityState: Empty entity state object with default values
    """
    from geometry_msgs.msg import Accel, Point, Pose, Quaternion, Twist, Vector3
    from std_msgs.msg import Header

    empty_state = EntityState()
    empty_state.header = Header(frame_id="", stamp=Header().stamp)
    empty_state.pose = Pose(position=Point(x=0.0, y=0.0, z=0.0), orientation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0))
    empty_state.twist = Twist(linear=Vector3(x=0.0, y=0.0, z=0.0), angular=Vector3(x=0.0, y=0.0, z=0.0))
    empty_state.acceleration = Accel(linear=Vector3(x=0.0, y=0.0, z=0.0), angular=Vector3(x=0.0, y=0.0, z=0.0))

    return empty_state
