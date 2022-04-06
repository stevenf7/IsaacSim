# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni
from pxr import UsdPhysics, UsdGeom, Gf, Usd, UsdShade
import omni.graph.core as og
import omni.physx as _physx


class ConveyorInternalState:
    def __init__(self):

        self.animationTextures = []
        self.textureStartCoordinates = []
        self.velocity = 0
        self._on_start = False
        self._on_end = False
        self._on_step = False
        self.dt = 0
        self.sub = None
        self.node = None

    @property
    def on_step(self):
        if self._on_step:
            self._on_step = False
            return True
        return False

    @on_step.setter
    def on_step(self, value):
        print("step")
        self._on_step = value

    @property
    def on_start(self):
        if self._on_start:
            self._on_start = False
            return True
        return False

    @on_start.setter
    def on_start(self, value):
        self._on_start = value

    @property
    def on_end(self):
        if self._on_end:
            self._on_end = False
            return True
        return False

    @on_end.setter
    def on_end(self, value):
        self._on_end = value

    def _on_stage_event(self, e):
        """The event callback"""
        self.on_start = e.type == int(omni.usd.StageEventType.ANIMATION_START_PLAY)
        self.on_end = e.type == int(omni.usd.StageEventType.ANIMATION_STOP_PLAY)

        if self.node.is_valid():
            self.node.request_compute()

    def first_time_subscribe(self, node: og.Node) -> bool:
        """Checked call to set up carb subscription
        Args:
            node: The node instance
            event_type: The stage event type
        Returns:
            True if we subscribed, False if we are already subscribed
        """
        if self.sub is None:
            # Add a subscription for the given event type. This is a pop subscription, so we expect a 1-frame
            # lag between send and receive
            self.sub = (
                omni.usd.get_context()
                .get_stage_event_stream()
                .create_subscription_to_pop(
                    self._on_stage_event, name=f"omni.graph.action.__onstageevent.{node.node_id()}"
                )
            )
            self.node = node

            return True

        return False

    def try_pop_event(self):
        """Pop the payload of the last event received, or None if there is no event to pop"""
        if self.is_set:
            self.is_set = False
            payload = self.payload
            self.payload = None
            return payload
        return None


class OgnConveyor:
    @staticmethod
    def internal_state():
        return ConveyorInternalState()

    @staticmethod
    def compute(db) -> bool:
        velocity_changed = db.internal_state.velocity != db.inputs.velocity

        if db.internal_state.first_time_subscribe(db.node):
            return True
        if db.inputs.enabled:
            if velocity_changed or db.internal_state._on_start:
                stage = omni.usd.get_context().get_stage()
                conveyor = stage.GetPrimAtPath(db.inputs.conveyorPrim.path)
                physx_conveyor = UsdPhysics.RigidBodyAPI(conveyor)
                if physx_conveyor:
                    if not physx_conveyor.GetKinematicEnabledAttr().Get():
                        physx_conveyor.GetKinematicEnabledAttr().Set(True)
                    m = omni.usd.utils.get_world_transform_matrix(conveyor)
                    m.Orthonormalize()
                    rotation = m.ExtractRotation()
                    direction = rotation.TransformDir(Gf.Vec3f(*db.inputs.direction.tolist()))
                    physx_conveyor.GetVelocityAttr().Set(direction * db.inputs.velocity)
                    db.internal_state.velocity = db.inputs.velocity
            if db.inputs.onStep and db.internal_state.velocity != 0:
                if db.inputs.animateTexture:
                    for attr in db.internal_state.animationTextures:
                        tx = attr.Get()
                        tx += Gf.Vec2f(
                            *(
                                db.inputs.delta
                                * db.inputs.animateDirection
                                * db.inputs.velocity
                                * db.inputs.animateScale
                            ).tolist()
                        )
                        attr.Set(tx)

            if db.internal_state.on_start:
                stage = omni.usd.get_context().get_stage()
                conveyor = stage.GetPrimAtPath(db.inputs.conveyorPrim.path)
                db.internal_state.textureStartCoordinates = []
                db.internal_state.animationTextures = []
                for usdMesh in [a for a in Usd.PrimRange(conveyor) if UsdGeom.Mesh(a)]:
                    mat, rel = UsdShade.MaterialBindingAPI(usdMesh).ComputeBoundMaterial()
                    for shader in Usd.PrimRange(mat.GetPrim()):
                        if shader.GetPrim().GetAttribute("inputs:texture_translate"):
                            db.internal_state.animationTextures.append(
                                shader.GetPrim().GetAttribute("inputs:texture_translate")
                            )
                            tx = db.internal_state.animationTextures[-1].Get()
                            db.internal_state.textureStartCoordinates.append(tx)

            if db.internal_state.on_end:
                for i, attr in enumerate(db.internal_state.animationTextures):
                    attr.Set(db.internal_state.textureStartCoordinates[i])

        return True
