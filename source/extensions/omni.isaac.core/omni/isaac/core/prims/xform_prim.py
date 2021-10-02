# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Tuple, Optional, Union
from pxr import Usd, UsdGeom, Gf
from omni.isaac.core.utils.types import PrimState
import numpy as np
from omni.isaac.core.utils.prims import set_usd_visibility
from omni.isaac.core.utils.xforms import set_xform_orientation, set_xform_position, set_xform_scale
from omni.isaac.core.utils.rotations import gf_quatd_to_np_array


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
        if position is not None or orientation is not None or scale is not None:
            self.set_usd_pose(position, orientation, scale)
        self.set_usd_visibility(visible=visible)
        self._visible = visible
        default_position, default_orientation, default_scale = self.get_usd_pose()
        self._default_state = PrimState(position=default_position, orientation=default_orientation, scale=default_scale)
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

    def set_usd_visibility(self, visible: bool) -> None:
        """Sets the visibility of the prim in stage. The method does this through the USD API.

        Args:
            visible (bool): flag to set the visibility of the usd prim in stage.
        """
        set_usd_visibility(prim=self._prim, visible=visible)
        self._visible = visible
        return

    def get_usd_visibility(self) -> bool:
        """
        Returns:
            bool: true if the prim is visible in stage. false otherwise.
        """
        return self._visible

    def set_usd_scale(self, scale: np.ndarray) -> None:
        """Sets the scale of the prim in stage. The method does this through the USD API.

        Args:
            scale (np.ndarray): scale to be applied to the usd prim. shape (3,).

        Raises:
            NotImplementedError: will be provided in a later iteration.
        """
        # scale = scale.tolist()
        # # convert scale to Usd matrix.
        # matrix = Gf.Matrix4d()
        # matrix.SetScale(scale)
        # # set attribute properties for the transform on the primitive
        # properties = self._prim.GetPropertyNames()
        # if "xformOp:transform" in properties:
        #     transform_attr = self._prim.GetAttribute("xformOp:transform")
        # else:
        #     xform = UsdGeom.Xformable(self._prim)
        #     transform_attr = xform.AddTransformOp()
        # transform_attr.Set(matrix)
        raise NotImplementedError

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
        set_xform_position(self._prim, position)

        return

    def _set_usd_orientation(self, quat: np.ndarray) -> None:
        """Sets the orientation of the prim in stage. The method does this through the USD API.

        Args:
            quat (np.ndarray): orientation represented as a quaternion. quaternion is scalar-first (w, x, y, z). 
                               shape (4,). 
        """
        set_xform_orientation(self._prim, quat)

        return

    def _set_usd_scale(self, scale: np.ndarray) -> None:
        """Sets the scale of the prim in stage. The method does this through the USD API.

        Args:
            scale (np.ndarray): scale of the prim to set in stage. shape (3,).
        """
        set_xform_scale(self._prim, scale)

        return

    def set_usd_pose(
        self,
        position: Optional[np.ndarray] = None,
        quat: Optional[np.ndarray] = None,
        scale: Optional[np.ndarray] = None,
    ) -> None:
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
        if scale is not None:
            self._set_usd_scale(quat=quat)
        return

    def get_usd_pose(self, as_matrix: bool = False) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
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
        scale = transform.GetScale()
        return np.array(position), gf_quatd_to_np_array(orientation), np.array(scale)

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

    def set_default_state(self, position: np.ndarray, orientation: np.ndarray) -> None:
        """Sets the default state of the prim (position and orientation), that will be used with each reset. 

        Args:
            position (np.ndarray): position of the prim to set in stage. shape (3,).
            orientation (np.ndarray): orientation represented as a quaternion. 
                                      quaternion is scalar-first (w, x, y, z). shape (4,).
        """
        self._default_state = PrimState(position=position, orientation=orientation)
        return

    def get_AABB(self):
        """Provides the current AABB bounding box.

        Raises:
            NotImplementedError: will be provided in a later iteration.
        """
        raise NotImplementedError

    def get_OBB(self):
        """Provides the current OBB bounding box.

        Raises:
            NotImplementedError: will be provided in a later iteration.
        """
        raise NotImplementedError
