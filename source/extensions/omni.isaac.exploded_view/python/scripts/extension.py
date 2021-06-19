# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni
import carb
from pxr import Gf, UsdGeom, Usd, Sdf, UsdPhysics
from enum import Enum


def TraversePrim(prim, filterfn=None):
    """
    Extract all sub-childrens from a given prim, on a breadth-first search, cutting the search if a sub-prim does not
    match the filter function criteria
    """
    childrenStack = [prim]
    out = prim.GetChildren()
    while len(childrenStack) > 0:
        prim = childrenStack.pop(0)
        if filterfn and filterfn(prim):
            children = prim.GetChildren()
            childrenStack = childrenStack + children
            out = out + children
    return out


def filterlight(prim: Usd.Prim):
    return "Light" not in prim.GetTypeName()


def get_session_layer_identifier():
    context = omni.usd.get_context()
    layers = context.get_layers()
    auth_layer = layers.get_authoring_layer_global_id()
    session_layer_id = layers.get_session_layer_global_id()
    layers.set_authoring_layer_by_global_id(session_layer_id)
    session_identifier = layers.get_authoring_layer_identifier()
    layers.set_authoring_layer_by_global_id(auth_layer)

    return session_identifier


class ExplodeDirection(Enum):
    GlobalOrigin = 0
    GlobalAxisX = 1
    GlobalAxisY = 2
    GlobalAxisZ = 3
    LocalOrigin = 4
    LocalAxisX = 5
    LocalAxisY = 6
    LocalAxisZ = 7


def getExplodeDirection(prim, dir_base: ExplodeDirection):
    """
    Returns un-normalized explode direction, to be used by ExplodedViewItem to determine the explode direction and base scale
    """
    if dir_base in [
        ExplodeDirection.GlobalOrigin,
        ExplodeDirection.GlobalAxisX,
        ExplodeDirection.GlobalAxisY,
        ExplodeDirection.GlobalAxisZ,
    ]:
        pose = omni.usd.utils.get_world_transform_matrix(prim)
        r = Gf.Matrix4d().SetRotate(pose.ExtractRotation())
        out = pose.ExtractTranslation()
        out[0] = out[0] if dir_base in [ExplodeDirection.GlobalOrigin, ExplodeDirection.GlobalAxisX] else 0
        out[1] = out[1] if dir_base in [ExplodeDirection.GlobalOrigin, ExplodeDirection.GlobalAxisY] else 0
        out[2] = out[2] if dir_base in [ExplodeDirection.GlobalOrigin, ExplodeDirection.GlobalAxisZ] else 0
        return r.Transform(out)
    else:
        pose = omni.usd.utils.get_local_transform_matrix(prim)
        out = pose.ExtractTranslation()
        out[0] = out[0] if dir_base in [ExplodeDirection.LocalOrigin, ExplodeDirection.LocalAxisX] else 0
        out[1] = out[1] if dir_base in [ExplodeDirection.LocalOrigin, ExplodeDirection.LocalAxisY] else 0
        out[2] = out[2] if dir_base in [ExplodeDirection.LocalOrigin, ExplodeDirection.LocalAxisZ] else 0
        return out


def disablePhysicsApi(api, get_fn, create_fn):
    apiEnabledAttr = get_fn(api)
    if not apiEnabledAttr:
        create_fn(api)
    else:
        apiEnabledAttr.Set(False)


class ExplodedViewItem:
    def __init__(self, stage: Usd.Stage, explode_base: str, base_prim: Usd.Prim, base_direction: Gf.Vec3d):
        self.stage = stage
        self.base_prim = base_prim
        # Base direction is local to parent transform, and not global.
        self.base_direction = base_direction
        self.base_scale = self.base_direction.Normalize()
        self.explode_scale = 0.0
        exploded_path = (
            explode_base + base_prim.GetPath().pathString.split(stage.GetDefaultPrim().GetPath().pathString)[-1]
        )
        self.explode_prim = stage.GetPrimAtPath(exploded_path)

        self.enabled = True
        # Create additional translate component on duplicate referred item
        # Temporarily enter on the edit layer context
        # Get usd xform operation
        xprim_form = UsdGeom.Xformable(self.explode_prim)
        if xprim_form:
            self.xform_op = xprim_form.AddXformOp(
                UsdGeom.XformOp.TypeTranslate, UsdGeom.XformOp.PrecisionDouble, "Explode"
            )
            # Reorder operations to have the explode transform applied first
            ops = xprim_form.GetOrderedXformOps()
            ops = [ops[-1]] + ops[:-1]
            xprim_form.SetXformOpOrder(ops)
        else:
            self.xform_op = None

    def edit_explode(self, explode_scale=None, base_direction: Gf.Vec3d = None):
        if base_direction:
            self.base_direction = base_direction
            self.base_scale = self.base_direction.Normalize()
        if self.enabled and explode_scale is not None:
            self.explode_scale = abs(explode_scale)  # Ensure the scale is >= zero
        explode_scale = self.explode_scale if self.enabled else 0
        offset = explode_scale * self.base_scale * self.base_direction
        if self.xform_op:
            self.xform_op.Set(offset)

    def enable(self):
        self.enabled = True
        self.edit_explode()

    def disable(self):
        self.enabled = False
        self.edit_explode()

    def __del__(self):
        self.disable()


def singleton(cls):
    instances = {}

    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper


class Exploded_view_manager:
    def __init__(self):
        self._context = omni.usd.get_context()
        self._events = self._context.get_stage_event_stream()
        self._stage_event_subscription = self._events.create_subscription_to_pop(
            self._on_stage_event, name="Exploded View Stage Change Watch"
        )

        self._layers = self._context.get_layers()

        self._physicsApis = {
            UsdPhysics.PhysicsAPI: [lambda a: a.GetPhysicsEnabledAttr(), lambda a: a.CreatePhysicsEnabledAttr(False)],
            UsdPhysics.CollisionAPI: [
                lambda a: a.GetCollisionEnabledAttr(),
                lambda a: a.CreateCollisionEnabledAttr(False),
            ],
            UsdPhysics.PhysicsJoint: [lambda a: a.GetJointEnabledAttr(), lambda a: a.CreateJointEnabledAttr(False)],
        }

        self.xview_layer = None

        self.ExplodeItems = {}

        self.ExplodeDirection = ExplodeDirection.GlobalOrigin

        self.enabled = False

        self.explode_base = None

        self.current_update_to_usd = carb.settings.get_settings().get("/persistent/physics/updateToUsd")
        self.current_use_fast_cache = carb.settings.get_settings().get("/persistent/physics/useFastCache")

    def _on_stage_event(self, event):
        """Called with omni.usd.context when stage event"""

        if event.type == int(omni.usd.StageEventType.OPENED):
            self._on_stage_opened()
        if event.type == int(omni.usd.StageEventType.CLOSED):
            self._on_stage_closed()

    def _on_stage_opened(self):
        self.disable()
        if self.xview_layer:
            self.xview_layer = None
        self.ExplodeItems.clear()

    def _on_stage_closed(self):
        self.disable()
        if self.xview_layer:
            self.xview_layer = None
        self.ExplodeItems.clear()

    def shutdown(self):
        self.disable()
        if self.xview_layer:
            xview_layer_pos = omni.kit.widget.layers.LayerUtils.get_sublayer_position_in_parent(
                self.session_layer_id, self.xview_layer.identifier
            )
            self._layers.remove_sublayer(self.session_layer_id, xview_layer_pos)
        if self.explode_base:
            self._context.get_stage().RemovePrim(self.explode_base)
            omni.kit.commands.execute(
                "RemoveLayerPrimSpecCommand", layer_identifier=self.session_layer_id, prim_spec_path=self.explode_base
            )
            self.explode_base = None

    def __del__(self):
        carb.log_warn("Deleting Explode Manager")
        self.disable()
        if self.xview_layer:
            xview_layer_pos = omni.kit.widget.layers.LayerUtils.get_sublayer_position_in_parent(
                self.session_layer_id, self.xview_layer.identifier
            )
            self._layers.remove_sublayer(self.session_layer_id, xview_layer_pos)
        if self.explode_base:
            self._context.get_stage().RemovePrim(self.explode_base)
            omni.kit.commands.execute(
                "RemoveLayerPrimSpecCommand", layer_identifier=self.session_layer_id, prim_spec_path=self.explode_base
            )
            self.explode_base = None

    def disable(self):
        if self.xview_layer:
            self._layers.mute_layer(self.xview_layer.identifier)
        self.enabled = False
        carb.settings.get_settings().set("/persistent/physics/updateToUsd", self.current_update_to_usd)
        carb.settings.get_settings().set("/persistent/physics/useFastCache", self.current_use_fast_cache)

    def enable(self):
        if self.xview_layer:
            self._layers.unmute_layer(self.xview_layer.identifier)
            carb.settings.get_settings().set("/persistent/physics/updateToUsd", True)
            carb.settings.get_settings().set("/persistent/physics/useFastCache", False)
            self.enabled = True
            return

        stage = self._context.get_stage()

        self.explode_base = omni.usd.get_stage_next_free_path(stage, "/Exploded", False)
        self.session_layer_id = get_session_layer_identifier()
        # Get current authoring layer
        auth_layer = self._layers.get_authoring_layer_identifier()
        # Create sub-layer withing Session layer to contain all changes done for Exploded View
        # This is done so that if the user saves the asset, the exploded view will not become part of it.
        omni.kit.commands.execute(
            "CreateLayerCommand",
            layer_identifier=self.session_layer_id,
            sublayer_position=0,
            new_layer_path="",
            transfer_root_content=False,
            create_or_insert=True,
            layer_name="Exploded_View",
        )
        self.xview_layer = Sdf.Layer.Find(self._layers.get_authoring_layer_identifier())

        # When creating a new layer kit defaults to set it as the authoring layer
        # (which is convenient to get the newly created layer)
        # But then we need to return the authoring to the base layer
        self._layers.set_authoring_layer_by_identifier(auth_layer)

        # Enter explode_view authnoring layer:

        with Usd.EditContext(stage, Sdf.Layer.Find(self.xview_layer.identifier)):
            if stage.GetDefaultPrim():
                xprim = stage.OverridePrim(self.explode_base)
                xprim.GetReferences().AddReference(auth_layer)
                # Gets the length of the default prim name to replace it with the epxloded view base
                root_path_len = len(stage.GetDefaultPrim().GetPath().pathString)
                for p in TraversePrim(stage.GetDefaultPrim(), filterlight):
                    path = p.GetPath().pathString
                    exploded_path = self.explode_base + path[root_path_len:]
                    xprim = stage.GetPrimAtPath(exploded_path)
                    if xprim:
                        carb.log_info("processing " + xprim.GetPath().pathString)
                        # Override instanceable option, to allow changes
                        if xprim.IsInstanceable():
                            xprim.SetInstanceable(False)
                        # Search for Physics Schemas applied to the prim and disable them
                        for api in self._physicsApis.keys():
                            disablePhysicsApi(api.Get(stage, exploded_path), *self._physicsApis[api])

                self.enabled = True
                prim = stage.GetDefaultPrim()
                imageable = UsdGeom.Imageable(prim)
                imageable.MakeInvisible()
        # Ready to start explode views!
        carb.settings.get_settings().set("/persistent/physics/updateToUsd", True)
        carb.settings.get_settings().set("/persistent/physics/useFastCache", False)

    def add_explode_view_item(self, prim: Usd.Prim, explode_direction=None):
        if self.enabled:
            stage = self._context.get_stage()
            if prim.GetPath().pathString.startswith(stage.GetDefaultPrim().GetPath().pathString):
                with Usd.EditContext(stage, Sdf.Layer.Find(self.xview_layer.identifier)):
                    self._add_explode_view_item(prim, explode_direction)
            else:
                carb.log_error("Explode view only works on the default prim tree")

    def _add_explode_view_item(self, prim, explode_direction):
        explode_direction = (
            ExplodeDirection(explode_direction) if explode_direction is not None else self.ExplodeDirection
        )
        stage = self._context.get_stage()
        for p in TraversePrim(prim, filterlight):
            # If it's something that will be rendered
            if UsdGeom.Imageable(p) and prim.GetProperty("purpose").Get() in ["default", "render"]:
                if p.GetPath() not in self.ExplodeItems:
                    self.ExplodeItems[p.GetPath()] = ExplodedViewItem(
                        stage, self.explode_base, p, getExplodeDirection(p, explode_direction)
                    )
                else:
                    self.ExplodeItems[p.GetPath()].edit_explode(
                        base_direction=getExplodeDirection(p, explode_direction)
                    )

    def explode(self, value):
        if self.enabled:
            stage = self._context.get_stage()
            with Usd.EditContext(stage, Sdf.Layer.Find(self.xview_layer.identifier)):
                for item in self.ExplodeItems.values():
                    item.edit_explode(value)

    def disable_view_item(self, prim: Usd.Prim):
        stage = self._context.get_stage()
        with Usd.EditContext(stage, Sdf.Layer.Find(self.xview_layer.identifier)):
            for p in TraversePrim(prim, filterlight):
                if prim.GetPath() in self.ExplodeItems:
                    self.ExplodeItems[prim.GetPath()].disable()

    def enable_view_item(self, prim: Usd.Prim):
        stage = self._context.get_stage()
        with Usd.EditContext(stage, Sdf.Layer.Find(self.xview_layer.identifier)):
            for p in TraversePrim(prim, filterlight):
                if prim.GetPath() in self.ExplodeItems:
                    self.ExplodeItems[prim.GetPath()].enable()

    def remove_view_item(self, prim: Usd.Prim):
        stage = self._context.get_stage()
        with Usd.EditContext(stage, Sdf.Layer.Find(self.xview_layer.identifier)):
            for p in TraversePrim(prim, filterlight):
                if prim.GetPath() in self.ExplodeItems:
                    self.ExplodeItems[prim.GetPath()].pop()
