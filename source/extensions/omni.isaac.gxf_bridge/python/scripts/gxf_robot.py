# Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os
from enum import Enum
from typing import Optional, Sequence

import carb
from omni.isaac.core.prims._impl.single_prim_wrapper import _SinglePrimWrapper
from omni.isaac.core.prims.xform_prim_view import XFormPrimView
from omni.isaac.core.simulation_context.simulation_context import SimulationContext
from omni.isaac.core.utils.prims import get_prim_at_path, is_prim_path_valid
from omni.isaac.core.utils.stage import add_reference_to_stage
from pxr import Usd

from .amr_nucleus import AmrAssetTier, get_gxf_nucleus_path


class GxfRobotType(Enum):
    CARTER_V2_3 = 1
    CARTER_V2_4 = 2


ROBOT_FILE_PATHS = {
    GxfRobotType.CARTER_V2_3: "carter_v2_3_gxf.usd",
    GxfRobotType.CARTER_V2_4: "carter_v2_4_gxf.usd",
}

TCP_SERVER_OVERRIDE_YAML = """
# This YAML document is provided to optionally override
# the TCP server's address and port.
name: tcp_server
components:
- name: tcp_server
  parameters:
    address: {}
    port: {}
"""


class GxfRobot(_SinglePrimWrapper):
    """Provides high level functions to deal with GXF robot asset and its attributes/ properties.

    Note: the prim will have "xformOp:orient", "xformOp:translate" and "xformOp:scale" only post init,
            unless it is a non-root articulation link.

    Args:
        prim_path (str): prim path of the GXF robot to encapsulate or create.
        name (str, optional): shortname to be used as a key by Scene class.
                                Note: needs to be unique if the object is added to the Scene.
                                Defaults to "xform_prim".
        position (Optional[Sequence[float]], optional): position in the world frame of the prim. shape is (3, ).
                                                    Defaults to None, which means left unchanged.
        translation (Optional[Sequence[float]], optional): translation in the local frame of the prim
                                                        (with respect to its parent prim). shape is (3, ).
                                                        Defaults to None, which means left unchanged.
        orientation (Optional[Sequence[float]], optional): quaternion orientation in the world/ local frame of the prim
                                                        (depends if translation or position is specified).
                                                        quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                        Defaults to None, which means left unchanged.
        scale (Optional[Sequence[float]], optional): local scale to be applied to the prim's dimensions. shape is (3, ).
                                                Defaults to None, which means left unchanged.
        visible (bool, optional): set to false for an invisible prim in the stage while rendering. Defaults to True.

    Raises:
        Exception: if translation and position defined at the same time
    """

    def __init__(
        self,
        prim_path: str,
        name: str,
        robot_type: GxfRobotType = GxfRobotType.CARTER_V2_4,
        asset_tier: AmrAssetTier = AmrAssetTier.RELEASE_CANDIDATE,
        position: Optional[Sequence[float]] = None,
        translation: Optional[Sequence[float]] = None,
        orientation: Optional[Sequence[float]] = None,
        scale: Optional[Sequence[float]] = None,
        visible: Optional[bool] = None,
    ) -> None:

        if is_prim_path_valid(prim_path):
            self._prim = get_prim_at_path(prim_path)
        else:
            carb.log_info("Creating a new GXF robot prim at path {}".format(prim_path))
            self._robot_type = robot_type
            self._asset_tier = asset_tier
            self._prim = define_gxf_robot_prim(
                prim_path=prim_path, gxf_robot_type=self._robot_type, asset_tier=self._asset_tier
            )
        if SimulationContext.instance() is not None:
            self._backend = SimulationContext.instance().backend
            self._device = SimulationContext.instance().device
            self._backend_utils = SimulationContext.instance().backend_utils
        else:
            import omni.isaac.core.utils.numpy as np_utils

            self._backend = "numpy"
            self._device = None
            self._backend_utils = np_utils
        if position is not None:
            position = self._backend_utils.convert(position, self._device)
            position = self._backend_utils.expand_dims(position, 0)
        if translation is not None:
            translation = self._backend_utils.convert(translation, self._device)
            translation = self._backend_utils.expand_dims(translation, 0)
        if orientation is not None:
            orientation = self._backend_utils.convert(orientation, self._device)
            orientation = self._backend_utils.expand_dims(orientation, 0)
        if scale is not None:
            scale = self._backend_utils.convert(scale, self._device)
            scale = self._backend_utils.expand_dims(scale, 0)
        if visible is not None:
            visible = self._backend_utils.create_tensor_from_list([visible], dtype="bool", device=self._device)
        self._xform_prim_view = XFormPrimView(
            prim_paths_expr=prim_path,
            name=name,
            positions=position,
            translations=translation,
            orientations=orientation,
            scales=scale,
            visibilities=visible,
        )
        self._binding_api = None
        _SinglePrimWrapper.__init__(self, view=self._xform_prim_view)
        return

    def set_tcp_server_params(self, address: str = "127.0.0.1", port: int = 7000) -> None:

        node_name = "set_tcp_server_params"
        node_type = "omni.isaac.gxf_bridge.GXFYAML"
        for prim in Usd.PrimRange(self._prim):
            if (
                prim.GetName() == node_name
                and prim.HasAttribute("node:type")
                and node_type in prim.GetAttribute("node:type").Get()
            ):
                input_yaml = prim.GetAttribute("inputs:yaml")
                input_yaml.Set(TCP_SERVER_OVERRIDE_YAML.format(address, port))
                carb.log_warn(f"Set TCP server parameters for robot at {self._prim.GetPath()} to {address}:{port}")
                return
        carb.log_warn(
            f"Could not find '{node_name}' node of type '{node_type}'. Did not override TCP server parameters."
        )
        return


def define_gxf_robot_prim(
    prim_path: str, gxf_robot_type: GxfRobotType, asset_tier: AmrAssetTier, fabric=False
) -> Usd.Prim:
    """Create a GXF robot prim at the given prim_path of type prim_type unless one already exists

    Args:
        prim_path (str): path of the prim in the stage
        prim_type (str, optional): The type of the prim to create. Defaults to "Xform".

    Raises:
        Exception: If there is already a prim at the prim_path

    Returns:
        Usd.Prim: The created USD prim.
    """
    if is_prim_path_valid(prim_path, fabric=fabric):
        raise Exception("A prim already exists at prim path: {}".format(prim_path))
    usd_path = os.path.join(get_gxf_nucleus_path(asset_tier=asset_tier), "Robots", ROBOT_FILE_PATHS[gxf_robot_type])
    return add_reference_to_stage(usd_path=str(usd_path), prim_path=prim_path)
