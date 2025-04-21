# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
__all__ = ["IconModel"]

from pathlib import Path

import omni.kit.app
import omni.usd
from isaacsim.core.utils.prims import get_all_matching_child_prims, get_prim_at_path
from omni.ui import scene as sc
from pxr import Gf, Tf, Trace, Usd, UsdGeom

ICON_POSITION_ATTR = "xformOp:translate"
ICON_ORIENTATION_ATTR = "xformOp:orient"
ICON_TRANSFORM_ATTR = "xformOp:transform"


class IconModel(sc.AbstractManipulatorModel):
    """
    User part. The model tracks the icon object.
    """

    SENSOR_TYPES = ["Lidar", "OmniLidar", "IsaacContactSensor", "IsaacLightBeamSensor", "IsaacImuSensor", "Generic"]

    class IconItem(sc.AbstractManipulatorItem):
        """
        The Model Item represents the icon
        """

        def __init__(self, prim, icon_url, prim_path):
            super().__init__()
            self.prim = prim
            self.icon_url = icon_url
            self.prim_path = prim_path
            self.on_click = None
            self.removed = False
            self.visible = True

    def __init__(self):
        # this should re-create when open stage
        super().__init__()
        self._sensor_icon_dir = omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module(__name__)
        self._sensor_icon_path = str(Path(self._sensor_icon_dir).joinpath("icons/icoSensors.svg"))
        self._usd_context = omni.usd.get_context()
        stage = self._usd_context.get_stage()
        self._world_unit = 0.0
        if stage:
            self._world_unit = UsdGeom.GetStageMetersPerUnit(stage)
        if self._world_unit == 0.0:
            self._world_unit = 0.1
        self._usd_listener = Tf.Notice.Register(Usd.Notice.ObjectsChanged, self._on_usd_changed, stage)
        self._icons = {}
        self._stage_sub = self._usd_context.get_stage_event_stream().create_subscription_to_pop(self._on_stage)

    def _on_stage(self, stage_event):
        if stage_event.type == int(omni.usd.StageEventType.OPENED):
            self._usd_listener = None
            self.clear()
            stage = self._usd_context.get_stage()
            self._world_unit = UsdGeom.GetStageMetersPerUnit(stage)
            if self._world_unit == 0.0:
                self._world_unit = 0.1
            self._usd_listener = Tf.Notice.Register(Usd.Notice.ObjectsChanged, self._on_usd_changed, stage)
            for prim in stage.Traverse():
                if prim.GetTypeName() in self.SENSOR_TYPES:
                    prim_path = prim.GetPath()
                    self._icons[prim_path] = IconModel.IconItem(prim, self._sensor_icon_path, prim_path)
            self._item_changed(None)

    def get_world_unit(self):
        return max(self._world_unit, 0.1)

    def __del__(self):
        self._stage_sub = None
        self._usd_listener = None
        self.destroy()

    def destroy(self):
        self._icons = {}
        self._usd_listener = None

    def get_item(self, identifier):
        return self._icons

    def get_prim_paths(self):
        return self._icons.keys()

    def get_position(self, prim_path):
        if prim_path in self.get_prim_paths():
            prim = get_prim_at_path(prim_path)
            if prim.IsValid():
                xformCache = UsdGeom.XformCache(Usd.TimeCode.Default())
                worldTransform = xformCache.GetLocalToWorldTransform(prim)
                translation = worldTransform.ExtractTranslation()
                return Gf.Vec3d(translation[0], translation[1], translation[2])
        return None

    def get_on_click(self, prim_path):
        if prim_path in self._icons.keys():
            return self._icons[prim_path].on_click
        return None

    def get_icon_url(self, prim_path):
        if prim_path in self._icons.keys():
            return self._icons[prim_path].icon_url
        return ""

    @Trace.TraceFunction
    def _on_usd_changed(self, notice, stage):
        for path in set(notice.GetResyncedPaths() + notice.GetChangedInfoOnlyPaths()):
            prim_path = path.GetPrimPath() if path.IsPropertyPath() else path
            # If the prim is not valid, skip
            if stage and not stage.GetPrimAtPath(prim_path):
                # If the prim path is in our icons dictionary, remove the sensor icon
                if prim_path in self._icons:
                    self.remove_sensor_icon(prim_path)
                continue

            pose_attributes = [ICON_POSITION_ATTR, ICON_ORIENTATION_ATTR, ICON_TRANSFORM_ATTR]
            property_changed = str(path).split(".")[-1] if path.IsPropertyPath() else None
            sensor_predicate = lambda path: (
                stage.GetPrimAtPath(path).GetTypeName() in self.SENSOR_TYPES if stage else False
            )
            all_sensor_children = get_all_matching_child_prims(prim_path, sensor_predicate)

            # Remove stale sensor icons
            for sensor in list(self._icons.keys()):
                sensor_prim = stage.GetPrimAtPath(sensor)
                # the the sensor prim is not valid, remove the icon
                if not sensor_prim:
                    self.remove_sensor_icon(sensor)
                # the prim is valid but no longer a sensor, remove the icon
                elif sensor_prim and sensor_prim.GetTypeName() not in self.SENSOR_TYPES:
                    self.remove_sensor_icon(sensor)

            # Add any new sensor icons
            for child in all_sensor_children:
                child_path = child.GetPath()
                child_prim = stage.GetPrimAtPath(child_path)
                if child_prim and child_path not in self._icons.keys():
                    self.add_sensor_icon(child_path)

            # update the icon position if the property changed is a pose attribute
            if property_changed in pose_attributes:
                # need to check if any of the changed-prim's children is a sensor (on top of the changed-prim itself)
                for child in all_sensor_children:
                    child_path = child.GetPath()
                    if child_path in self._icons.keys():
                        self._item_changed(self._icons[child_path])

    def clear(self):
        self._icons = {}
        self._item_changed(None)

    def add_sensor_icon(self, prim_path, icon_url=None):
        if not icon_url:
            icon_url = self._sensor_icon_path
        stage = omni.usd.get_context().get_stage()
        prim = stage.GetPrimAtPath(prim_path)
        if not prim:
            return
        self._icons[prim_path] = IconModel.IconItem(prim, icon_url, prim_path)
        self._item_changed(self._icons[prim_path])

    def remove_sensor_icon(self, prim_path):
        if prim_path in self._icons.keys():
            self._icons[prim_path].removed = True
            self._item_changed(self._icons[prim_path])
            self._icons.pop(prim_path)

    def set_icon_click_fn(self, prim_path, call_back):
        for prim_path in self._icons.keys():
            self._icons[prim_path].on_click = call_back

    def show_sensor_icon(self, prim_path):
        if prim_path in self._icons.keys():
            self._icons[prim_path].visible = True
            self._item_changed(self._icons[prim_path])

    def hide_sensor_icon(self, prim_path):
        if prim_path in self._icons.keys():
            self._icons[prim_path].visible = False
            self._item_changed(self._icons[prim_path])

    def show_all(self):
        for prim_path in self._icons.keys():
            self._icons[prim_path].visible = True
            self._item_changed(self._icons[prim_path])
        # TODO: _item_changed(None) not works here now
        # self._item_changed(None)

    def hide_all(self):
        for prim_path in self._icons.keys():
            self._icons[prim_path].visible = False
            self._item_changed(self._icons[prim_path])
        # TODO: _item_changed(None) not works here now
        # self._item_changed(None)
