# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional, Tuple
from omni.isaac.core.materials.visual_material import VisualMaterial
from pxr import Gf, Usd, UsdGeom, UsdShade
from omni.isaac.core.utils.types import XFormPrimState
from omni.isaac.core.materials import PreviewSurface, OmniGlass, OmniPBR
from omni.isaac.core.utils.rotations import gf_quatd_to_np_array
from omni.isaac.core.utils.transformations import tf_matrix_from_pose
from omni.isaac.core.utils.prims import (
    get_prim_at_path,
    move_prim,
    query_parent_path,
    is_prim_path_valid,
    define_prim,
    get_prim_parent,
    get_prim_object_type,
)
import numpy as np
import carb
from omni.isaac.core.utils.stage import get_current_stage


class XFormPrim(object):
    """Provides high level functions to deal with an Xform prim and its attributes/ properties.
        If there is an Xform prim present at the path, it will use it. Otherwise, a new XForm prim at
        the specified prim path will be created.

        Note: the prim will have "xformOp:orient", "xformOp:translate" and "xformOp:scale" only post init, 
                unless it is a non-root articulation link.

        Args:
            prim_path (str): prim path of the Prim to encapsulate or create.
            name (str, optional): shortname to be used as a key by Scene class. 
                                    Note: needs to be unique if the object is added to the Scene.
                                    Defaults to "xform_prim".
            position (Optional[np.ndarray], optional): position in the world frame of the prim. shape is (3, ).
                                                        Defaults to None, which means left unchanged.
            translation (Optional[np.ndarray], optional): translation in the local frame of the prim
                                                            (with respect to its parent prim). shape is (3, ).
                                                            Defaults to None, which means left unchanged.
            orientation (Optional[np.ndarray], optional): quaternion orientation in the world/ local frame of the prim
                                                            (depends if translation or position is specified).
                                                            quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                            Defaults to None, which means left unchanged.
            scale (Optional[np.ndarray], optional): local scale to be applied to the prim's dimensions. shape is (3, ).
                                                    Defaults to None, which means left unchanged.
            visible (bool, optional): set to false for an invisible prim in the stage while rendering. Defaults to True.

        Raises:
            Exception: if translation and position defined at the same time
    """

    def __init__(
        self,
        prim_path: str,
        name: str = "xform_prim",
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        scale: Optional[np.ndarray] = None,
        visible: bool = True,
    ) -> None:
        if is_prim_path_valid(prim_path):
            self._prim = get_prim_at_path(prim_path)
        else:
            carb.log_info("Creating a new XForm prim at path {}".format(prim_path))
            self._prim = define_prim(prim_path=prim_path, prim_type="Xform")
        non_root_link_flag = query_parent_path(
            prim_path=prim_path, query_fn=lambda a: get_prim_object_type(a) == "articulation"
        )
        self._name = name
        self._prim_path = prim_path
        if translation is not None and position is not None:
            raise Exception("You can not define translation and position at the same time")
        if not non_root_link_flag:
            XFormPrim._set_xform_properties(self)
            if position is not None or orientation is not None or translation is not None:
                if translation is not None:
                    XFormPrim.set_local_pose(self, position, orientation)
                else:
                    XFormPrim.set_world_pose(self, position, orientation)
            if scale is not None:
                XFormPrim.set_local_scale(self, scale)
        XFormPrim.set_visibility(self, visible=visible)
        default_position, default_orientation = XFormPrim.get_world_pose(self)
        self._default_state = XFormPrimState(position=default_position, orientation=default_orientation)
        self._applied_visual_material = None
        self._binding_api = None
        return

    @property
    def prim_path(self) -> str:
        """
        Returns:
            str: prim path in the stage.
        """
        return self._prim_path

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
            Usd.Prim: USD Prim object that this object holds.
        """
        return self._prim

    def _set_xform_properties(self) -> None:
        current_position, current_orientation = XFormPrim.get_world_pose(self)
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
        else:
            xform_op_tranlsate = UsdGeom.XformOp(self.prim.GetAttribute("xformOp:translate"))

        if "xformOp:orient" not in prop_names:
            xform_op_rot = xformable.AddXformOp(UsdGeom.XformOp.TypeOrient, UsdGeom.XformOp.PrecisionFloat, "")
        else:
            xform_op_rot = UsdGeom.XformOp(self.prim.GetAttribute("xformOp:orient"))
        xformable.SetXformOpOrder([xform_op_tranlsate, xform_op_rot, xform_op_scale])
        XFormPrim.set_world_pose(self, position=current_position, orientation=current_orientation)
        return

    def set_visibility(self, visible: bool) -> None:
        """Sets the visibility of the prim in stage.

        Args:
            visible (bool): flag to set the visibility of the usd prim in stage.
        """
        imageable = UsdGeom.Imageable(self.prim)
        if visible:
            imageable.MakeVisible()
        else:
            imageable.MakeInvisible()
        return

    def get_visibility(self) -> bool:
        """
        Returns:
            bool: true if the prim is visible in stage. false otherwise.
        """
        return UsdGeom.Imageable(self.prim).ComputeVisibility(Usd.TimeCode.Default()) != UsdGeom.Tokens.invisible

    def post_reset(self) -> None:
        """Resets the prim to its default state (position and orientation).
        """
        XFormPrim.set_world_pose(self, self._default_state.position, self._default_state.orientation)
        return

    def get_default_state(self) -> XFormPrimState:
        """
        Returns:
            XFormPrimState: returns the default state of the prim (position and orientation) that is used after each reset.
        """
        return self._default_state

    def set_default_state(
        self, position: Optional[np.ndarray] = None, orientation: Optional[np.ndarray] = None
    ) -> None:
        """Sets the default state of the prim (position and orientation), that will be used after each reset.

        Args:
            position (Optional[np.ndarray], optional): position in the world frame of the prim. shape is (3, ).
                                                       Defaults to None, which means left unchanged.
            orientation (Optional[np.ndarray], optional): quaternion orientation in the world frame of the prim. 
                                                          quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                          Defaults to None, which means left unchanged.
        """

        if position is not None:
            self._default_state.position = position
        if orientation is not None:
            self._default_state.orientation = orientation
        return

    def apply_visual_material(self, visual_material: VisualMaterial, weaker_than_descendants: bool = False) -> None:
        """Used to apply visual material to the held prim and optionally its descendants.

        Args:
            visual_material (VisualMaterial): visual material to be applied to the held prim. Currently supports
                                              PreviewSurface, OmniPBR and OmniGlass.
            weaker_than_descendants (bool, optional): True if the material shouldn't override the descendants  
                                                      materials, otherwise False. Defaults to False.
        """
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

    def get_applied_visual_material(self) -> VisualMaterial:
        """Returns the current applied visual material in case it was applied using apply_visual_material OR
           it's one of the following materials that was already applied before: PreviewSurface, OmniPBR and OmniGlass.

        Returns:
            VisualMaterial: the current applied visual material if its type is currently supported.
        """
        if self._binding_api is None:
            if self._prim.HasAPI(UsdShade.MaterialBindingAPI):
                self._binding_api = UsdShade.MaterialBindingAPI(self.prim)
            else:
                self._binding_api = UsdShade.MaterialBindingAPI.Apply(self.prim)
        if self._applied_visual_material is not None:
            return self._applied_visual_material
        else:
            visual_binding = self._binding_api.GetDirectBinding()
            material_path = str(visual_binding.GetMaterialPath())
            if material_path == "":
                return None
            else:
                stage = get_current_stage()
                material = UsdShade.Material(stage.GetPrimAtPath(material_path))
                # getting the shader
                shader_info = material.ComputeSurfaceSource()
                if shader_info[0].GetPath() != "":
                    shader = shader_info[0]
                elif is_prim_path_valid(material_path + "/shader"):
                    shader_path = material_path + "/shader"
                    shader = UsdShade.Shader(get_prim_at_path(shader_path))
                elif is_prim_path_valid(material_path + "/Shader"):
                    shader_path = material_path + "/Shader"
                    shader = UsdShade.Shader(get_prim_at_path(shader_path))
                else:
                    carb.log_warn("the shader on xform prim {} is not supported".format(self.prim_path))
                    return None
                implementation_source = shader.GetImplementationSource()
                asset_sub_identifier = shader.GetPrim().GetAttribute("info:mdl:sourceAsset:subIdentifier").Get()
                shader_id = shader.GetShaderId()
                if implementation_source == "id" and shader_id == "UsdPreviewSurface":
                    self._applied_visual_material = PreviewSurface(prim_path=material_path, shader=shader)
                    return self._applied_visual_material
                elif asset_sub_identifier == "OmniGlass":
                    self._applied_visual_material = OmniGlass(prim_path=material_path, shader=shader)
                    return self._applied_visual_material
                elif asset_sub_identifier == "OmniPBR":
                    self._applied_visual_material = OmniPBR(prim_path=material_path, shader=shader)
                    return self._applied_visual_material
                else:
                    carb.log_warn("the shader on xform prim {} is not supported".format(self.prim_path))
                    return None

    def is_visual_material_applied(self) -> bool:
        """
        Returns:
            bool: True if there is a visual material applied. False otherwise.
        """
        if self._binding_api is None:
            if self._prim.HasAPI(UsdShade.MaterialBindingAPI):
                self._binding_api = UsdShade.MaterialBindingAPI(self.prim)
            else:
                self._binding_api = UsdShade.MaterialBindingAPI.Apply(self.prim)
        visual_binding = self._binding_api.GetDirectBinding()
        material_path = str(visual_binding.GetMaterialPath())
        if material_path == "":
            return False
        else:
            return True

    def set_world_pose(self, position: Optional[np.ndarray] = None, orientation: Optional[np.ndarray] = None) -> None:
        """Sets prim's pose with respect to the world's frame.

        Args:
            position (Optional[np.ndarray], optional): position in the world frame of the prim. shape is (3, ).
                                                       Defaults to None, which means left unchanged.
            orientation (Optional[np.ndarray], optional): quaternion orientation in the world frame of the prim. 
                                                          quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                          Defaults to None, which means left unchanged.
        """
        current_position, current_orientation = XFormPrim.get_world_pose(self)
        if position is None:
            position = current_position
        if orientation is None:
            orientation = current_orientation
        my_world_transform = tf_matrix_from_pose(translation=position, orientation=orientation)
        parent_world_tf = UsdGeom.Xformable(get_prim_parent(self._prim)).ComputeLocalToWorldTransform(
            Usd.TimeCode.Default()
        )
        local_transform = np.matmul(np.linalg.inv(np.transpose(parent_world_tf)), my_world_transform)
        transform = Gf.Transform()
        transform.SetMatrix(Gf.Matrix4d(np.transpose(local_transform)))
        calculated_translation = transform.GetTranslation()
        calculated_orientation = transform.GetRotation().GetQuat()
        XFormPrim.set_local_pose(
            self, translation=np.array(calculated_translation), orientation=gf_quatd_to_np_array(calculated_orientation)
        )
        return

    def get_world_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """Gets prim's pose with respect to the world's frame.

        Returns:
            Tuple[np.ndarray, np.ndarray]: first index is position in the world frame of the prim. shape is (3, ). 
                                           second index is quaternion orientation in the world frame of the prim.
                                           quaternion is scalar-first (w, x, y, z). shape is (4, ).
        """
        prim_tf = UsdGeom.Xformable(self._prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        transform = Gf.Transform()
        transform.SetMatrix(prim_tf)
        position = transform.GetTranslation()
        orientation = transform.GetRotation().GetQuat()
        return np.array(position), gf_quatd_to_np_array(orientation)

    def get_local_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """Gets prim's pose with respect to the local frame (the prim's parent frame).

        Returns:
            Tuple[np.ndarray, np.ndarray]: first index is position in the local frame of the prim. shape is (3, ). 
                                           second index is quaternion orientation in the local frame of the prim.
                                           quaternion is scalar-first (w, x, y, z). shape is (4, ).
        """
        xform_translate_op = self.prim.GetAttribute("xformOp:translate")
        xform_orient_op = self.prim.GetAttribute("xformOp:orient")
        return np.array(xform_translate_op.Get()), gf_quatd_to_np_array(xform_orient_op.Get())

    def set_local_pose(
        self, translation: Optional[np.ndarray] = None, orientation: Optional[np.ndarray] = None
    ) -> None:
        """Sets prim's pose with respect to the local frame (the prim's parent frame).

        Args:
            translation (Optional[np.ndarray], optional): translation in the local frame of the prim
                                                          (with respect to its parent prim). shape is (3, ).
                                                          Defaults to None, which means left unchanged.
            orientation (Optional[np.ndarray], optional): quaternion orientation in the world frame of the prim. 
                                                          quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                          Defaults to None, which means left unchanged.
        """
        properties = self.prim.GetPropertyNames()
        if translation is not None:
            translation = Gf.Vec3d(*translation.tolist())
            if "xformOp:translate" not in properties:
                carb.log_error(
                    "Translate property needs to be set for {} before setting its position".format(self.name)
                )
            xform_op = self.prim.GetAttribute("xformOp:translate")
            xform_op.Set(translation)
        if orientation is not None:
            rotq = Gf.Quatf(*orientation.tolist())
            if "xformOp:orient" not in properties:
                carb.log_error(
                    "Orient property needs to be set for {} before setting its orientation".format(self.name)
                )
            xform_op = self.prim.GetAttribute("xformOp:orient")
            xform_op.Set(rotq)
        return

    def get_world_scale(self) -> np.ndarray:
        """Gets prim's scale with respect to the world's frame.

        Returns:
            np.ndarray: scale applied to the prim's dimensions in the world frame. shape is (3, ).
        """
        prim_tf = UsdGeom.Xformable(self._prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        transform = Gf.Transform()
        transform.SetMatrix(prim_tf)
        return np.array(transform.GetScale())

    def set_local_scale(self, scale: Optional[np.ndarray]) -> None:
        """Sets prim's scale with respect to the local frame (the prim's parent frame).

        Args:
            scale (Optional[np.ndarray]): scale to be applied to the prim's dimensions. shape is (3, ).
                                          Defaults to None, which means left unchanged.
        """
        scale = Gf.Vec3d(*scale.tolist())
        properties = self.prim.GetPropertyNames()
        if "xformOp:scale" not in properties:
            carb.log_error("Scale property needs to be set for {} before setting its scale".format(self.name))
        xform_op = self.prim.GetAttribute("xformOp:scale")
        xform_op.Set(scale)
        return

    def get_local_scale(self) -> np.ndarray:
        """Gets prim's scale with respect to the local frame (the parent's frame).

        Returns:
            np.ndarray: scale applied to the prim's dimensions in the local frame. shape is (3, ).
        """
        xform_op = self.prim.GetAttribute("xformOp:scale")
        return np.array(xform_op.Get())

    def is_valid(self) -> bool:
        """
        Returns:
            bool: True is the current prim path corresponds to a valid prim in stage. False otherwise.
        """
        return is_prim_path_valid(self.prim_path)

    def change_prim_path(self, new_prim_path: str) -> None:
        """Moves prim from the old path to a new one.

        Args:
            new_prim_path (str): new path of the prim to be moved to.
        """
        move_prim(path_from=self.prim_path, path_to=new_prim_path)
        self._prim_path = new_prim_path
        self._prim = get_prim_at_path(self._prim_path)
        return
