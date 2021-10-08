# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Tuple, Optional, Union
from pxr import Gf, Usd, UsdGeom, UsdShade
from omni.isaac.core.utils.types import PrimState
from omni.isaac.core.materials import PreviewSurface
from omni.isaac.core.utils.rotations import gf_quatd_to_np_array
import numpy as np
import carb
import omni.kit.app


class XFormPrim(object):
    def __init__(
        self,
        prim: Usd.Prim,
        name: str,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        scale: Optional[np.ndarray] = None,
        visible: bool = True,
    ) -> None:
        """Provides common functionalities to prims already existing in the stage

        Args:
            prim (Usd.Prim): prim object to encapsulate
            name (np.ndarray, optional): name given to the prim, this can be different than the prim path. Defaults to None.
            position (np.ndarray, optional): position in the world frame to set the prim. shape is (3, ) Defaults to None.
            orientation (np.ndarray, optional): quaternion orientation in the world frame to set the prim.
                                                quaternion is scalar-first (w, x, y, z). shape is (4, ). Defaults to None.
            visible (bool, optional): set to false for an invisible prim in the stage while rendering. Defaults to True.
        """
        self._prim = prim
        self._name = name
        self._set_xform_properties()
        if position is not None or orientation is not None:
            self.set_usd_pose(position, orientation)
        self.set_usd_visibility(visible=visible)
        if scale is None:
            scale = np.array([1.0, 1.0, 1.0])
        self.set_usd_scale(scale)
        default_position, default_orientation = self.get_usd_pose()
        self._default_state = PrimState(position=default_position, orientation=default_orientation)
        self._applied_visual_material = None
        self._binding_api = None
        return

    @property
    def prim_path(self) -> str:
        """
        Returns:
            str: prim path in the stage.
        """
        return self._prim.GetPath().pathString

    @property
    def name(self) -> Optional[str]:
        """
        Returns:
            str: name given to the prim when instantiating it. Otherwise None.
        """
        return self._name

    @property
    def prim(self) -> Usd.Prim:
        """
        Returns:
            Usd.Prim: USD Prim object that this object tracks.
        """
        return self._prim

    def _set_xform_properties(self) -> None:
        current_position, current_orientation = self.get_usd_pose()
        properties_to_remove = [
            "xformOp:rotateX",
            "xformOp:rotateXZY",
            "xformOp:rotateY",
            "xformOp:rotateYXZ",
            "xformOp:rotateYZX",
            "xformOp:rotateZ",
            "xformOp:rotateZYX",
            "xformOp:rotateZXY",
            "xformOp:rotateXYZ",
            "xformOp:transform",
        ]
        prop_names = self.prim.GetPropertyNames()
        xformable = UsdGeom.Xformable(self.prim)
        xformable.ClearXformOpOrder()
        # TODO: wont be able to delete props for non root links on articulated objects
        for prop_name in prop_names:
            if prop_name in properties_to_remove:
                self.prim.RemoveProperty(prop_name)
        if "xformOp:scale" not in prop_names:
            xform_op_scale = xformable.AddXformOp(UsdGeom.XformOp.TypeScale, UsdGeom.XformOp.PrecisionFloat, "")
            xform_op_scale.Set(Gf.Vec3d([1.0, 1.0, 1.0]))
        else:
            xform_op_scale = UsdGeom.XformOp(self.prim.GetAttribute("xformOp:scale"))

        if "xformOp:translate" not in prop_names:
            xform_op_tranlsate = xformable.AddXformOp(UsdGeom.XformOp.TypeTranslate, UsdGeom.XformOp.PrecisionFloat, "")
            xform_op_tranlsate.Set(Gf.Vec3d(*current_position.tolist()))
        else:
            xform_op_tranlsate = UsdGeom.XformOp(self.prim.GetAttribute("xformOp:translate"))

        if "xformOp:orient" not in prop_names:
            xform_op_rot = xformable.AddXformOp(UsdGeom.XformOp.TypeOrient, UsdGeom.XformOp.PrecisionFloat, "")
            xform_op_rot.Set(Gf.Quatf(*current_orientation.tolist()))
        else:
            xform_op_rot = UsdGeom.XformOp(self.prim.GetAttribute("xformOp:orient"))
        xformable.SetXformOpOrder([xform_op_tranlsate, xform_op_rot, xform_op_scale])
        return

    def set_usd_visibility(self, visible: bool) -> None:
        """Sets the visibility of the prim in stage. The method does this through the USD API.

        Args:
            visible (bool): flag to set the visibility of the usd prim in stage.
        """
        imageable = UsdGeom.Imageable(self.prim)
        if visible:
            imageable.MakeVisible()
        else:
            imageable.MakeInvisible()
        return

    def get_usd_visibility(self) -> bool:
        """
        Returns:
            bool: true if the prim is visible in stage. false otherwise.
        """
        return UsdGeom.Imageable(self.prim).ComputeVisibility(Usd.TimeCode.Default()) != UsdGeom.Tokens.invisible

    def set_usd_scale(self, scale: np.ndarray) -> None:
        """Sets the scale of the prim in stage. The method does this through the USD API.

        Args:
            scale (np.ndarray): scale to be applied to the usd prim. shape (3,).
        """
        scale = Gf.Vec3d(*scale.tolist())
        properties = self.prim.GetPropertyNames()
        if "xformOp:scale" not in properties:
            carb.log_error("Scale property needs to be set for {} before setting its scale".format(self.name))
        xform_op = self.prim.GetAttribute("xformOp:scale")
        xform_op.Set(scale)
        return

    def apply_usd_transformation(self, transformation_matrix: np.ndarray) -> None:
        """
        Applies a transformation matrix to the prim in stage. The method does this through the USD API.

        Args:
            transformation_matrix (np.ndarray): transformation matrix to be applied. shape (4, 4).

        Raises:
            NotImplementedError: will be provided in a later iteration.
        """
        raise NotImplementedError

    def _set_usd_position(self, position: np.ndarray) -> None:
        """Sets the position of the prim in stage. The method does this through the USD API.

        Args:
            position (np.ndarray): position of the prim to set in stage. shape (3,).
        """
        position = Gf.Vec3d(*position.tolist())
        properties = self.prim.GetPropertyNames()
        if "xformOp:translate" not in properties:
            carb.log_error("Translate property needs to be set for {} before setting its position".format(self.name))
        xform_op = self.prim.GetAttribute("xformOp:translate")
        xform_op.Set(position)
        return

    def _set_usd_orientation(self, quat: np.ndarray) -> None:
        """Sets the orientation of the prim in stage. The method does this through the USD API.

        Args:
            quat (np.ndarray): orientation represented as a quaternion. quaternion is scalar-first (w, x, y, z).
                               shape (4,).
        """

        properties = self.prim.GetPropertyNames()
        rotq = Gf.Quatf(*quat.tolist())
        if "xformOp:orient" not in properties:
            carb.log_error("Orient property needs to be set for {} before setting its orientation".format(self.name))
        xform_op = self.prim.GetAttribute("xformOp:orient")
        xform_op.Set(rotq)
        return

    def set_usd_pose(self, position: Optional[np.ndarray] = None, quat: Optional[np.ndarray] = None) -> None:
        """Sets the pose of the prim in stage. The method does this through the USD API.

        Args:
            position (np.ndarray, optional): position of the prim to set in stage. shape (3,). Defaults to None.
            quat (np.ndarray, optional): orientation represented as a quaternion. quaternion is
                                         scalar-first (w, x, y, z). shape (4,). Defaults to None.
        """
        if position is not None:
            self._set_usd_position(position=position)
        if quat is not None:
            self._set_usd_orientation(quat=quat)
        return

    def get_usd_pose(self, as_matrix: bool = False) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """Gets the pose of the prim in stage. The method does this through the USD API.

        Args:
            as_matrix (bool, optional): set to True to return the pose as a transformation matrix from World frame to
                                        local frame. Defaults to False.

        Returns:
            Union(np.ndarray, Tuple(np.ndarray, np.ndarray, np.ndarray)): Either the pose as matrix if specified in the
                                                              argument or a tuple where the first position (3,)
                                                              is the usd position, second is the orientation
                                                              as a quaternion. quaternion is scalar-first (w, x, y, z).
                                                              shape (4,), and third is the scale (3,)
        """
        prim_tf = UsdGeom.Xformable(self._prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        if as_matrix:
            return np.transpose(prim_tf)

        transform = Gf.Transform()
        transform.SetMatrix(prim_tf)

        position = transform.GetTranslation()
        orientation = transform.GetRotation().GetQuat()
        return np.array(position), gf_quatd_to_np_array(orientation)

    def reset(self) -> None:
        """Resets the prim to its default state (position and orientation).
        """
        self.set_usd_pose(self._default_state.position, self._default_state.orientation)
        return

    def get_default_state(self) -> PrimState:
        """
        Returns:
            PrimState: returns the default state of the prim (position and orientation) that is used with each reset.
        """
        return self._default_state

    def set_default_state(
        self, position: Optional[np.ndarray] = None, orientation: Optional[np.ndarray] = None
    ) -> None:
        """Sets the default state of the prim (position and orientation), that will be used with each reset. 

        Args:
            position (np.ndarray): position of the prim to set in stage. shape (3,).
            orientation (np.ndarray): orientation represented as a quaternion.
                                      quaternion is scalar-first (w, x, y, z). shape (4,).
        """
        if position is not None:
            self._default_state.position = position
        if orientation is not None:
            self._default_state.orientation = orientation
        return

    def apply_visual_material(self, visual_material, weaker_than_descendants=False):
        if self._binding_api is None:
            if self._prim.HasAPI(UsdShade.MaterialBindingAPI):
                self._binding_api = UsdShade.MaterialBindingAPI(self.prim)
            else:
                self._binding_api = UsdShade.MaterialBindingAPI.Apply(self.prim)
        if weaker_than_descendants:
            self._binding_api.Bind(visual_material.material, bindingStrength=UsdShade.Tokens.weakerThanDescendants)
        else:
            self._binding_api.Bind(visual_material.material, bindingStrength=UsdShade.Tokens.strongerThanDescendants)
        self._applied_visual_material = visual_material
        return

    def get_applied_visual_material(self):
        if self._binding_api is None:
            if self._prim.HasAPI(UsdShade.MaterialBindingAPI):
                self._binding_api = UsdShade.MaterialBindingAPI(self.prim)
            else:
                self._binding_api = UsdShade.MaterialBindingAPI.Apply(self.prim)
        if self._applied_visual_material is not None:
            return self._applied_visual_material
        else:
            visual_binding = self._binding_api.GetDirectBinding()
            path = visual_binding.GetMaterialPath()
            if path == "":
                return None
            else:
                stage = omni.usd.get_context().get_stage()
                shader = UsdShade.Shader(stage.GetPrimAtPath(str(path) + "/shader"))  # TODO: improve this
                print(shader.GetIdAttr().Get())
                if shader.GetIdAttr().Get() == "UsdPreviewSurface":
                    self._applied_visual_material = PreviewSurface(prim_path=path)
                    return self._applied_visual_material
                else:
                    carb.log_warn("The visual material you are trying to get is not supported yet")
        return

    def set_world_position(self, position):
        raise NotImplementedError

    def set_local_translation(self, translation):
        translation = Gf.Vec3d(*translation.tolist())
        properties = self.prim.GetPropertyNames()
        if "xformOp:translate" not in properties:
            carb.log_error("Translate property needs to be set for {} before setting its position".format(self.name))
        xform_op = self.prim.GetAttribute("xformOp:translate")
        xform_op.Set(translation)
        return

    def set_world_orientation(self, orientation):
        raise NotImplementedError

    def set_local_orientation(self, orientation):
        properties = self.prim.GetPropertyNames()
        rotq = Gf.Quatf(*orientation.tolist())
        if "xformOp:orient" not in properties:
            carb.log_error("Orient property needs to be set for {} before setting its orientation".format(self.name))
        xform_op = self.prim.GetAttribute("xformOp:orient")
        xform_op.Set(rotq)
        return

    def set_world_scale(self, scale):
        raise NotImplementedError

    def get_world_scale(self):
        prim_tf = UsdGeom.Xformable(self._prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        transform = Gf.Transform()
        transform.SetMatrix(prim_tf)
        return np.array(transform.GetScale())

    def set_local_scale(self, scale):
        raise NotImplementedError
