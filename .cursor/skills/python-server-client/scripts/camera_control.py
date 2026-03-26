"""Control the viewport camera position, orientation, and properties.

Uses isaacsim.core.experimental for camera transforms and objects.Camera for properties.
Works in both windowed and --no-window headless modes.

Injected args (via isaacsim_send.py --arg):
    action: str — "get" (default), "set", "look_at", or "list_cameras".
    camera_path: str — Camera prim path (default: active viewport camera).
    position: str/tuple — x,y,z for set (e.g. "5,5,5").
    orientation: str/tuple — Quaternion w,x,y,z for set (e.g. "1,0,0,0").
    target: str/tuple — x,y,z look-at target for "look_at" action.
    focal_length: float — Focal length in mm (optional, for "set").

Examples:
    isaacsim_send.py --file camera_control.py
    isaacsim_send.py --file camera_control.py --arg action=set --arg "position=10,10,10"
    isaacsim_send.py --file camera_control.py --arg action=look_at --arg "target=0,0,0" --arg "position=5,5,5"
    isaacsim_send.py --file camera_control.py --arg action=list_cameras
"""

import numpy as np

if "action" not in dir():
    action = "get"
if "camera_path" not in dir():
    camera_path = None
if "position" not in dir():
    position = None
if "orientation" not in dir():
    orientation = None
if "target" not in dir():
    target = None
if "focal_length" not in dir():
    focal_length = None


def _parse_vec(val):
    """Parse a comma-separated string or tuple/list into a numpy array."""
    if val is None:
        return None
    if isinstance(val, (list, tuple)):
        return np.array([float(x) for x in val])
    return np.array([float(x.strip()) for x in str(val).split(",")])


import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.utils import prim as prim_utils
from isaacsim.core.experimental.utils import stage as stage_utils
from isaacsim.core.experimental.utils import xform


def _get_active_camera_path():
    from omni.kit.viewport.utility import get_active_viewport

    return get_active_viewport().camera_path


def _resolve_camera():
    if camera_path:
        return camera_path
    return _get_active_camera_path()


if action == "get":
    cam = _resolve_camera()
    cam_str = str(cam)
    pos, rot = xform.get_world_pose(cam_str)
    print(f"Camera: {cam_str}")
    print(f"Position (x, y, z): {pos}")
    print(f"Orientation (w, x, y, z): {rot}")
    try:
        from isaacsim.core.experimental.objects import Camera

        cam_obj = Camera(paths=cam_str)
        fl = cam_obj.get_focal_lengths()
        cr = cam_obj.get_clipping_ranges()
        print(f"Focal length: {fl[0]} mm")
        print(f"Clipping range: {cr[0]}")
    except Exception:
        try:
            fl = prim_utils.get_prim_attribute_value(cam_str, "focalLength")
            print(f"Focal length: {fl} mm")
        except Exception:
            pass

elif action == "set":
    from isaacsim.core.experimental.prims import XformPrim

    cam = _resolve_camera()
    cam_str = str(cam)
    xp = XformPrim(paths=cam_str)
    xp.reset_xform_op_properties()
    cur_poses = xp.get_world_poses()
    cur_pos = np.array(cur_poses[0].numpy())[0]
    cur_rot = np.array(cur_poses[1].numpy())[0]

    new_pos = _parse_vec(position) if position is not None else cur_pos
    new_rot = _parse_vec(orientation) if orientation is not None else cur_rot

    xp.set_world_poses(
        positions=np.array(new_pos, dtype=np.float32).reshape(1, 3),
        orientations=np.array(new_rot, dtype=np.float32).reshape(1, 4),
    )
    app_utils.update_app(steps=3)

    print(f"Camera: {cam}")
    print(f"Position set to: {new_pos}")
    print(f"Orientation set to: {new_rot}")

    if focal_length is not None:
        from isaacsim.core.experimental.objects import Camera

        cam_obj = Camera(paths=cam_str)
        cam_obj.set_focal_lengths(np.array([float(focal_length)]))
        print(f"Focal length set to: {focal_length} mm")

elif action == "look_at":
    if not target:
        raise ValueError("target required for 'look_at' (e.g. --arg target=0,0,0)")

    from isaacsim.core.experimental.prims import XformPrim
    from isaacsim.core.experimental.utils.transform import look_at_quaternion

    cam = _resolve_camera()
    cam_str = str(cam)
    target_pos = _parse_vec(target)

    if position is not None:
        eye_pos = _parse_vec(position)
    else:
        wp_pos = xform.get_world_pose(cam_str)[0]
        eye_pos = np.array(wp_pos.numpy()).flatten()

    quat_wp = look_at_quaternion(eye=eye_pos, target=target_pos)
    quat = np.array(quat_wp.numpy()).flatten()

    xp = XformPrim(paths=cam_str)
    xp.reset_xform_op_properties()
    xp.set_world_poses(
        positions=np.array(eye_pos, dtype=np.float32).reshape(1, 3),
        orientations=np.array(quat, dtype=np.float32).reshape(1, 4),
    )
    app_utils.update_app(steps=3)

    print(f"Camera: {cam_str}")
    print(f"Position: {eye_pos}")
    print(f"Looking at: {target_pos}")
    print(f"Orientation: {quat}")

elif action == "list_cameras":
    stage = stage_utils.get_current_stage()
    cameras = [p for p in stage.Traverse() if p.GetTypeName() == "Camera"]
    active = str(_get_active_camera_path())
    print(f"Cameras ({len(cameras)}):")
    for cam_prim in cameras:
        path = str(cam_prim.GetPath())
        marker = " (active)" if path == active else ""
        pos, _ = xform.get_world_pose(path)
        print(f"  {path}{marker} — pos={pos}")

else:
    print(f"ERROR: Unknown action '{action}'. Use: get, set, look_at, list_cameras")
