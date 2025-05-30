# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from typing import Optional

import carb
import omni.isaac.IsaacSensorSchema as IsaacSensorSchema
import omni.kit.commands
import omni.kit.utils
import omni.replicator.core as rep
import omni.usd
from isaacsim.core.utils.stage import add_reference_to_stage, get_next_free_path
from isaacsim.core.utils.xforms import reset_and_set_xform_ops
from isaacsim.storage.native import get_assets_root_path
from pxr import Gf, Sdf, Usd, UsdGeom


class IsaacSensorCreateRtxSensor(omni.kit.commands.Command):
    _replicator_api = None
    _sensor_type = "sensor"
    _supported_configs = []
    _schema = None
    _sensor_plugin_name = ""
    _camera_config_name = ""

    def __init__(
        self,
        path: Optional[str] = None,
        parent: Optional[str] = None,
        config: Optional[str] = None,
        translation: Optional[Gf.Vec3d] = Gf.Vec3d(0, 0, 0),
        orientation: Optional[Gf.Quatd] = Gf.Quatd(1, 0, 0, 0),
        visibility: Optional[bool] = False,
        variant: Optional[str] = None,
        force_camera_prim=False,
        **kwargs,
    ):
        self._parent = parent
        self._config = config
        self._translation = translation
        self._orientation = orientation
        self._visibility = visibility
        self._variant = variant
        self._force_camera_prim = force_camera_prim
        self._prim_creation_kwargs = kwargs
        self._prim = None
        self._path = path or f"/Rtx{self._sensor_type.capitalize()}"
        self._desired_prim_type = f"Omni{self._sensor_type.capitalize()}"
        self._camera_config = self._config

    def _add_reference(self) -> Usd.Prim:
        """Adds a reference to the stage if a config is provided, and sets that prim's variant if provided. Otherwise, returns None."""
        if self._config:
            found_config = False
            for config in self._supported_configs:
                if os.path.splitext(os.path.basename(config))[0] == self._config:
                    found_config = True
                    prim = add_reference_to_stage(
                        usd_path=get_assets_root_path() + config,
                        prim_path=self._prim_path,
                        prim_type=self._desired_prim_type if config.endswith(".usda") else "Xform",
                    )
                    reset_and_set_xform_ops(prim.GetPrim(), self._translation, self._orientation)
                    if self._variant:
                        variant_set = prim.GetVariantSet("Sensor")
                        if not variant_set:
                            carb.log_warn(
                                f"Variant set 'Sensor' not found for Omni{self._sensor_type.capitalize()} at {self._prim_path}."
                            )
                        if not variant_set.SetVariantSelection(self._variant):
                            carb.log_warn(
                                f"Variant '{self._variant}' not found for Omni{self._sensor_type.capitalize()} at {self._prim_path}."
                            )
                    # If necessary, traverse children of referenced asset to find OmniSensor prim
                    # Note: if multiple children of the referenced asset are OmniSensor types, this will select the first one
                    if prim.GetTypeName() == "Xform":
                        for child in Usd.PrimRange(prim):
                            if child.GetTypeName() == self._desired_prim_type:
                                carb.log_info(f"Using {self._desired_prim_type} prim at path {child.GetPath()}")
                                prim = child
                    return prim
            if not found_config:
                carb.log_warn(
                    f"Config '{self._config}' not found for Omni{self._sensor_type.capitalize()} at {self._prim_path}."
                )
        return None

    def _call_replicator_api(self) -> Usd.Prim:
        if self._replicator_api is not None:
            # Convert position and orientation into tuples for Replicator API.
            position = (self._translation[0], self._translation[1], self._translation[2])
            rotation = Gf.Rotation(self._orientation)
            euler_angles_as_vec = rotation.Decompose(Gf.Vec3d.XAxis(), Gf.Vec3d.YAxis(), Gf.Vec3d.ZAxis())
            euler_angles = (euler_angles_as_vec[0], euler_angles_as_vec[1], euler_angles_as_vec[2])
            # Construct prim
            if self._prim_path.startswith("/"):
                self._prim_path = self._prim_path[1:]
            return self._replicator_api(
                position=position,
                rotation=euler_angles,
                name=self._prim_path,
                parent=self._parent,
                **self._prim_creation_kwargs,
            )
        return None

    def _create_camera_prim(self) -> Usd.Prim:
        carb.log_warn(
            "Support for creating RTX sensors as camera prims is deprecated as of Isaac Sim 5.0, and support will be removed in a future release. Please use an OmniSensor prim instead."
        )
        prim = UsdGeom.Camera.Define(self._stage, Sdf.Path(self._prim_path)).GetPrim()
        if self._schema:
            self._schema.Apply(prim)
        camSensorTypeAttr = prim.CreateAttribute("cameraSensorType", Sdf.ValueTypeNames.Token, False)
        camSensorTypeAttr.Set(self._sensor_type)
        tokens = camSensorTypeAttr.GetMetadata("allowedTokens")
        prim.CreateAttribute("sensorModelPluginName", Sdf.ValueTypeNames.String, False).Set(self._sensor_plugin_name)
        if not tokens:
            camSensorTypeAttr.SetMetadata("allowedTokens", ["camera", "radar", "lidar", "ids", "ultrasonic"])
        if self._camera_config:
            prim.CreateAttribute("sensorModelConfig", Sdf.ValueTypeNames.String, False).Set(self._camera_config)
        return prim

    def do(self):
        self._stage = omni.usd.get_context().get_stage()
        self._prim_path = get_next_free_path(self._path, self._parent)
        self._prim = (
            not self._force_camera_prim and (self._add_reference() or self._call_replicator_api())
        ) or self._create_camera_prim()
        return self._prim

    def undo(self):
        pass


class IsaacSensorCreateRtxLidar(IsaacSensorCreateRtxSensor):
    _replicator_api = staticmethod(rep.functional.create.omni_lidar)
    _sensor_type = "lidar"
    _supported_configs = carb.settings.get_settings().get("exts/isaacsim.sensors.rtx/supportedLidarConfigs")
    _schema = IsaacSensorSchema.IsaacRtxLidarSensorAPI
    _sensor_plugin_name = "omni.sensors.nv.lidar.lidar_core.plugin"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self._config and self._config.startswith("OS"):
            carb.log_warn(
                "Support for adding variant lidar models to the stage via config name only has been deprecated in Isaac Sim 5.0. Please use the config (model name) and variant (model variant) arguments instead."
            )
            # In Isaac Sim 5.0, Ouster lidar configs were implemented as variants on the same prim in the main USD file
            self._variant = self._config
            self._config = self._config[:3]  # truncate to OS0, OS1, or OS2
            self._camera_config = self._variant
            carb.log_warn(
                f"Example: omni.kit.commands.execute('IsaacSensorCreateRtxLidar', config='{self._config}', variant='{self._variant}')"
            )


class IsaacSensorCreateRtxRadar(IsaacSensorCreateRtxSensor):
    _replicator_api = staticmethod(rep.functional.create.omni_radar)
    _sensor_type = "radar"
    _schema = IsaacSensorSchema.IsaacRtxRadarSensorAPI
    _sensor_plugin_name = "omni.sensors.nv.radar.wpm_dmatapprox.plugin"


class IsaacSensorCreateRtxIDS(IsaacSensorCreateRtxSensor):
    _sensor_type = "ids"
    _sensor_plugin_name = "omni.sensors.nv.ids.ids.plugin"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self._config is None:
            self._config = "idsoccupancy"
            self._camera_config = "idsoccupancy"


class IsaacSensorCreateRtxUltrasonic(IsaacSensorCreateRtxSensor):
    _sensor_type = "ultrasonic"
    _sensor_plugin_name = "omni.sensors.nv.ultrasonic.wpm_ultrasonic.plugin"


omni.kit.commands.register_all_commands_in_module(__name__)
