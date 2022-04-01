# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import List, Optional, Tuple, Union
import numpy as np
import torch
import omni.kit.app
from collections import OrderedDict
from omni.isaac.core.prims.xform_prim_view import XFormPrimView
from omni.isaac.core.utils.types import JointsState, ArticulationActions
from pxr import Usd, UsdGeom
import carb
from omni.isaac.core.utils.prims import get_prim_parent


class ArticulationView(XFormPrimView):
    def __init__(
        self,
        prim_paths_expr: str,
        name: str = "rigid_prim_view",
        positions: Optional[Union[np.ndarray, torch.Tensor]] = None,
        translations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        scales: Optional[Union[np.ndarray, torch.Tensor]] = None,
        visibilities: Optional[Union[np.ndarray, torch.Tensor]] = None,
    ) -> None:
        """[summary]

        Args:
            prim_path (str): [description]
            name (Optional, optional): [description]. Defaults to None.
            position (Optional, optional): [description]. Defaults to None.
            orientation (Optional, optional): [description]. Defaults to None.
            articulation_controller (Optional, optional): [description]. Defaults to None.
        """
        self._physics_view = None
        XFormPrimView.__init__(
            self,
            prim_paths_expr=prim_paths_expr,
            name=name,
            positions=positions,
            translations=translations,
            orientations=orientations,
            scales=scales,
            visibilities=visibilities,
        )
        self._regex_prim_paths = prim_paths_expr
        # Handles related to robot
        self._num_dof = None
        self._default_joints_state = None
        self._dofs_infos = OrderedDict()
        self._dof_names = None
        self._dof_indices = None
        self._metadata = None

        return

    @property
    def num_dof(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return self._num_dof

    @property
    def dof_properties(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        raise NotImplementedError

    def initialize(self, physics_sim_view) -> None:
        """[summary]
        """
        carb.log_info("initializing view for {}".format(self._name))
        self._physics_view = physics_sim_view.create_articulation_view(self._regex_prim_paths.replace(".*", "*"))
        assert self._physics_view.is_homogeneous
        self._device = physics_sim_view.device
        self._metadata = self._physics_view.shared_metatype
        self._num_dof = self._physics_view.max_dofs
        self._dof_names = self._metadata.dof_names
        self._dof_indices = self._metadata.dof_indices
        carb.log_info("Articulation Prim View Device: {}".format(self._device))
        default_actions = self.get_applied_actions()
        # TODO: implement effort part
        self._default_joints_state = JointsState(
            positions=default_actions.joint_positions, velocities=default_actions.joint_velocities, efforts=None
        )
        return

    def get_dof_index(self, dof_name: str) -> int:
        """[summary]

        Args:
            dof_name (str): [description]

        Returns:
            int: [description]
        """
        return self._dof_indices[dof_name]

    def get_dof_types(self, dof_names: List[str]) -> List[str]:
        raise NotImplementedError

    def get_dof_limits(self):
        return self._physics_view.get_dof_limits()

    def read_kinematic_hierarchy(self) -> None:
        """[summary]
        """
        raise NotImplementedError

    def get_articulation_body_count(self):
        return self._metadata.link_count

    def disable_gravity(self) -> None:
        raise NotImplementedError()

    def set_joint_position_targets(
        self,
        joint_positions: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
    ) -> None:
        """[summary]

        Args:
            joint_positions (np.ndarray): [description]
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            new_dof_pos = self._backend_utils.create_zeros_tensor(
                shape=[self.count, self.num_dof], dtype="float32", device=self._device
            )
            new_dof_pos[self._backend_utils.expand_dims(indices, 1), joint_indices] = self._backend_utils.move_data(
                joint_positions, device=self._device
            )
            self._physics_view.set_dof_position_targets(new_dof_pos, indices)

        else:
            raise NotImplementedError
        return

    def set_joint_positions(
        self,
        joint_positions: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
    ) -> None:
        """[summary]

        Args:
            joint_positions (np.ndarray): [description]
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            new_dof_pos = self._backend_utils.clone_tensor(self._physics_view.get_dof_positions(), device=self._device)
            new_dof_pos[self._backend_utils.expand_dims(indices, 1), joint_indices] = self._backend_utils.move_data(
                joint_positions, device=self._device
            )
            self._physics_view.set_dof_positions(new_dof_pos, indices)
            self._physics_view.set_dof_position_targets(new_dof_pos, indices)
        else:
            raise NotImplementedError
        return

    def set_joint_velocity_targets(
        self,
        joint_velocities: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
    ) -> None:
        """[summary]

        Args:
            joint_velocities (np.ndarray): [description]
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            new_dof_vel = self._backend_utils.create_zeros_tensor(
                shape=[self.count, self.num_dof], dtype="float32", device=self._device
            )
            new_dof_vel[self._backend_utils.expand_dims(indices, 1), joint_indices] = self._backend_utils.move_data(
                joint_velocities, device=self._device
            )
            self._physics_view.set_dof_velocity_targets(new_dof_vel, indices)
        else:
            raise NotImplementedError
        return

    def set_joint_velocities(
        self,
        joint_velocities: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
    ) -> None:
        """[summary]

        Args:
            joint_positions (np.ndarray): [description]
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            new_dof_vel = self._backend_utils.clone_tensor(self._physics_view.get_dof_velocities(), device=self._device)
            new_dof_vel[self._backend_utils.expand_dims(indices, 1), joint_indices] = self._backend_utils.move_data(
                joint_velocities, device=self._device
            )
            self._physics_view.set_dof_velocities(new_dof_vel, indices)
            self._physics_view.set_dof_velocity_targets(new_dof_vel, indices)
        else:
            raise NotImplementedError
        return

    def set_joint_efforts(
        self,
        joint_efforts: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
    ) -> None:
        """[summary]

        Args:
            joint_positions (np.ndarray): [description]
        """

        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            # TODO: missing get_dof efforts/ forces?
            new_dof_efforts = self._backend_utils.create_zeros_tensor(
                shape=[self.count, self.num_dof], dtype="float32", device=self._device
            )
            new_dof_efforts[self._backend_utils.expand_dims(indices, 1), joint_indices] = self._backend_utils.move_data(
                joint_efforts, device=self._device
            )
            # TODO: double check this/ is this setting a force or applying a force?
            self._physics_view.set_dof_actuation_forces(new_dof_efforts, indices)
        else:
            raise NotImplementedError
        return

    def get_joint_positions(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor]:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            current_joint_positions = self._physics_view.get_dof_positions()
            result = current_joint_positions[self._backend_utils.expand_dims(indices, 1), joint_indices]
            if clone:
                result = self._backend_utils.clone_tensor(result, device=self._device)
            return result
        else:
            raise NotImplementedError

    def get_joint_velocities(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor]:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            current_joint_velocities = self._physics_view.get_dof_velocities()
            result = current_joint_velocities[self._backend_utils.expand_dims(indices, 1), joint_indices]
            if clone:
                result = self._backend_utils.clone_tensor(result, device=self._device)
            return result
        else:
            raise NotImplementedError

    def get_joint_efforts(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
    ) -> Union[np.ndarray, torch.Tensor]:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        raise NotImplementedError()

    def apply_action(
        self,
        control_actions: ArticulationActions,
        indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
    ) -> None:
        """[summary]

        Args:
            control_action (dict): [description]
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)

            if control_actions.joint_positions is not None:
                # TODO: optimize this operation
                action = self._backend_utils.clone_tensor(
                    self._physics_view.get_dof_position_targets(), device=self._device
                )
                action[self._backend_utils.expand_dims(indices, 1), joint_indices] = self._backend_utils.move_data(
                    control_actions.joint_positions, device=self._device
                )
                self._physics_view.set_dof_position_targets(action, indices)
            if control_actions.joint_velocities is not None:
                # TODO: optimize this operation
                action = self._backend_utils.clone_tensor(
                    self._physics_view.get_dof_velocity_targets(), device=self._device
                )
                action[self._backend_utils.expand_dims(indices, 1), joint_indices] = self._backend_utils.move_data(
                    control_actions.joint_positions, device=self._device
                )
                self._physics_view.set_dof_velocity_targets(action, indices)
            if control_actions.joint_efforts is not None:
                # TODO: optimize this operation
                # action = self._backend_utils.clone_tensor(self._physics_view.get_dof_actuation_forces(), device=self._device)
                action = self._backend_utils.create_zeros_tensor(
                    (self.count, self.num_dof), dtype="float32", device=self._device
                )
                action[self._backend_utils.expand_dims(indices, 1), joint_indices] = self._backend_utils.move_data(
                    control_actions.joint_positions, device=self._device
                )
                self._physics_view.set_dof_actuation_forces(action, indices)
        else:
            raise NotImplementedError
        return

    def get_applied_actions(self, clone=True):
        joint_positions = self._physics_view.get_dof_position_targets()
        if clone:
            joint_positions = self._backend_utils.clone_tensor(joint_positions, device=self._device)
        joint_velocities = self._physics_view.get_dof_velocity_targets()
        if clone:
            joint_velocities = self._backend_utils.clone_tensor(joint_velocities, device=self._device)
        # TODO: implement the effort part
        return ArticulationActions(
            joint_positions=joint_positions, joint_velocities=joint_velocities, joint_efforts=None
        )

    def set_root_transforms(
        self,
        transforms: Optional[Union[np.ndarray, torch.Tensor]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ):
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            root_trans = self._physics_view.get_root_transforms().clone()
            transforms[:, 3:7] = transforms[:, 3:7][:, [1, 2, 3, 0]]
            root_trans[indices, :] = self._backend_utils.move_data(transforms, self._device)
            self._physics_view.set_root_transforms(root_trans, indices)
        else:
            self.set_world_poses(positions=transforms[:, 0:3], orientations=transforms[:, 3:7], indices=indices)

    def get_root_transforms(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone=True
    ) -> Union[np.ndarray, torch.Tensor]:
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            transforms = self._physics_view.get_root_transforms()
            transforms[:, 3:7] = transforms[:, 3:7][:, [3, 0, 1, 2]]
            if not clone:
                return transforms[indices]
            else:
                return self._backend_utils.clone_tensor(transforms[indices], device=self._device)
        else:
            positions, orientations = self.get_world_poses(indices=indices, clone=clone)
            return self._backend_utils.tensor_cat([positions, orientations], dim=-1)[indices]

    def set_world_poses(
        self,
        positions: Optional[Union[np.ndarray, torch.Tensor]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets prim's pose in the view with respect to the world's frame.

        Args:
            positions (Optional[Union[np.ndarray, torch.Tensor]], optional): positiosn in the world frame of the prim. shape is (M, 3).
                                                                             Defaults to None, which means left unchanged.
            orientations (Optional[Union[np.ndarray, torch.Tensor]], optional): quaternion orientations in the world frame of the prims. 
                                                                                quaternion is scalar-first (w, x, y, z). shape is (M, 4).
                                                                                Defaults to None, which means left unchanged.
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Raises:
            Exception: [description]
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_positions, current_orientations = self.get_world_poses(clone=False)
            if positions is None:
                positions = current_positions[indices]
            if orientations is None:
                orientations = current_orientations[indices]
            orientations = orientations[:, [1, 2, 3, 0]]
            current_orientations = current_orientations[:, [1, 2, 3, 0]]
            old_pose = self._backend_utils.get_pose(current_positions, current_orientations, device=self._device)
            new_pose = self._backend_utils.get_pose(positions, orientations, device=self._device)
            old_pose[indices] = new_pose
            self._physics_view.set_root_transforms(old_pose, indices)
            return
        else:
            XFormPrimView.set_world_poses(self, positions=positions, orientations=orientations, indices=indices)
        return

    def get_world_poses(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone=True
    ) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]:
        """Gets prim's pose in the view with respect to the world's frame.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Raises:
            Exception: [description]

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]: 
                                          first index is positions in the world frame of the prims. shape is (M, 3). 
                                           second index is quaternion orientations in the world frame of the prims.
                                           quaternion is scalar-first (w, x, y, z). shape is (M, 4).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            pose = self._physics_view.get_root_transforms()
            if not clone:
                return pose[indices, 0:3], pose[indices, 3:7][:, [3, 0, 1, 2]]
            else:
                return (
                    self._backend_utils.clone_tensor(pose[indices, 0:3], device=self._device),
                    self._backend_utils.clone_tensor(pose[indices, 3:7][:, [3, 0, 1, 2]], device=self._device),
                )
        else:
            return XFormPrimView.get_world_poses(self, indices=indices)

    def get_local_poses(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone=True
    ) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]:
        """Gets prim's pose in the view with respect to the local frame (the prim's parent frame).

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        Raises:
            Exception: [description]

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]:
                                                    first index is positions in the local frame of the prims. shape is (M, 3). 
                                                    second index is quaternion orientations in the local frame of the prims.
                                                    quaternion is scalar-first (w, x, y, z). shape is (M, 4).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            world_positions, world_orientations = self.get_world_poses(indices=indices)
            parent_transforms = self._backend_utils.create_zeros_tensor(
                shape=[indices.shape[0], 4, 4], dtype="float32", device=self._device
            )
            write_idx = 0
            for i in indices:
                parent_transforms[write_idx] = self._backend_utils.create_tensor_from_list(
                    UsdGeom.Xformable(get_prim_parent(self._prims[i.tolist()])).ComputeLocalToWorldTransform(
                        Usd.TimeCode.Default()
                    ),
                    dtype="float32",
                    device=self._device,
                )
                write_idx += 1
            return self._backend_utils.get_local_from_world(
                parent_transforms, world_positions, world_orientations, self._device
            )
        else:
            return XFormPrimView.get_local_poses(self, indices=indices)

    def set_local_poses(
        self,
        translations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets prim's pose in the view with respect to the local frame (the prim's parent frame).

        Args:
            translations (Optional[Union[np.ndarray, torch.Tensor]], optional): 
                                                          translations in the local frame of the prims
                                                          (with respect to its parent prim). shape is (M, 3).
                                                          Defaults to None, which means left unchanged.
            orientations (Optional[Union[np.ndarray, torch.Tensor]], optional): 
                                                          quaternion orientations in the world frame of the prims. 
                                                          quaternion is scalar-first (w, x, y, z). shape is (M, 4).
                                                          Defaults to None, which means left unchanged.
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            parent_transforms = self._backend_utils.create_zeros_tensor(
                shape=[indices.shape[0], 4, 4], dtype="float32", device=self._device
            )
            write_idx = 0
            for i in indices:
                parent_transforms[write_idx] = self._backend_utils.create_tensor_from_list(
                    UsdGeom.Xformable(get_prim_parent(self._prims[i.tolist()])).ComputeLocalToWorldTransform(
                        Usd.TimeCode.Default()
                    ),
                    dtype="float32",
                    device=self._device,
                )
                write_idx += 1
            return self._backend_utils.get_world_from_local(parent_transforms, translations, orientations, self._device)
        else:
            XFormPrimView.set_local_poses(self, translations=translations, orientations=orientations, indices=indices)
        return

    def set_root_velocities(
        self,
        velocities: Optional[Union[np.ndarray, torch.Tensor]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ):
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            root_vel = self._physics_view.get_root_velocities().clone()
            root_vel[indices, :] = self._backend_utils.move_data(velocities, self._device)
            self._physics_view.set_root_velocities(root_vel, indices)
        else:
            self.set_linear_velocities(velocities[:, 0:3], indices=indices)
            self.set_angular_velocities(velocities[:, 3:6], indices=indices)

    def get_root_velocities(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone=True
    ) -> Union[np.ndarray, torch.Tensor]:
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            velocities = self._physics_view.get_root_velocities()
            if not clone:
                return velocities[indices]
            else:
                return self._backend_utils.clone_tensor(velocities[indices], device=self._device)
        else:
            linear_velocities = self.get_linear_velocities(indices, clone)
            angular_velocities = self.get_angular_velocities(indices, clone)
            return self._backend_utils.tensor_cat([linear_velocities, angular_velocities], dim=-1)[indices]

    def set_linear_velocities(
        self,
        linear_velocities: Optional[Union[np.ndarray, torch.Tensor]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ):
        """Sets the linear velocity of the prim in stage. The method does this through the physx API.
            Note: It has to be called while simulating i.e after .play() or .reset() is called

        Args:
            linear_velocity (np.ndarray): linear velocity to set the rigid prim to. Shape (3,).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            velocities = self._backend_utils.clone_tensor(self._physics_view.get_root_velocities(), device=self._device)
            velocities[indices, 0:3] = self._backend_utils.move_data(linear_velocities, device=self._device)
            self._physics_view.set_root_velocities(velocities, indices)
        else:
            raise NotImplementedError

    def get_linear_velocities(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone=True
    ) -> Union[np.ndarray, torch.Tensor]:
        """
        Returns:
            np.ndarray: current linear velocity of the the rigid prim. Shape (3,).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            linear_velocities = self._physics_view.get_root_velocities()
            if not clone:
                return linear_velocities[indices, 0:3]
            else:
                return self._backend_utils.clone_tensor(linear_velocities[indices, 0:3], device=self._device)
        else:
            raise NotImplementedError

    def set_angular_velocities(
        self,
        angular_velocities: Optional[Union[np.ndarray, torch.Tensor]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            velocities = self._backend_utils.clone_tensor(self._physics_view.get_root_velocities(), device=self._device)
            velocities[indices, 3:6] = self._backend_utils.move_data(angular_velocities, self._device)
            self._physics_view.set_root_velocities(velocities, indices)
        else:
            raise NotImplementedError
        return

    def get_angular_velocities(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone=True
    ) -> Union[np.ndarray, torch.Tensor]:
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            angular_velocities = self._physics_view.get_root_velocities()
            if not clone:
                return angular_velocities[indices, 3:6]
            else:
                return self._backend_utils.clone_tensor(angular_velocities[indices, 3:6], device=self._device)
        else:
            raise NotImplementedError

    def set_joints_default_state(
        self,
        positions: Optional[Union[np.ndarray, torch.Tensor]] = None,
        velocities: Optional[Union[np.ndarray, torch.Tensor]] = None,
        efforts: Optional[Union[np.ndarray, torch.Tensor]] = None,
    ) -> None:
        """[summary]

        Args:
            positions (Optional[np.ndarray], optional): [description]. Defaults to None.
            velocities (Optional[np.ndarray], optional): [description]. Defaults to None.
            efforts (Optional[np.ndarray], optional): [description]. Defaults to None.
        """
        if positions is not None:
            self._default_joints_state.positions = positions
        if velocities is not None:
            self._default_joints_state.velocities = velocities
        # TODO: implement effort part
        # if efforts is not None:
        #     self._default_joints_state.efforts = efforts
        return

    def get_joints_state(self) -> JointsState:
        """[summary]

        Returns:
            JointsState: [description]
        """
        # TODO: implement effort part
        return JointsState(positions=self.get_joint_positions(), velocities=self.get_joint_velocities(), efforts=None)

    def post_reset(self) -> None:
        """[summary]
        """
        XFormPrimView.post_reset(self)
        ArticulationView.set_joint_positions(self, self._default_joints_state.positions)
        ArticulationView.set_joint_velocities(self, self._default_joints_state.velocities)
        # ArticulationView.set_joint_efforts(self, self._default_joints_state.efforts)
        return

    def get_effort_modes(self) -> np.ndarray:
        """[summary]

        Raises:
            Exception: [description]
            NotImplementedError: [description]

        Returns:
            np.ndarray: [description]
        """
        raise NotImplementedError

    def set_effort_modes(self, mode: str, indices: Optional[Union[np.ndarray, list]] = None) -> None:
        """[summary]

        Args:
            mode (str): [description]
            indices (Optional[Union[np.ndarray, list]], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
            Exception: [description]
        """
        raise NotImplementedError

    def set_max_efforts(self, value: float = None, indices: Optional[Union[np.ndarray, list]] = None) -> None:
        """[summary]

        Args:
            value (float, optional): [description]. Defaults to None.
            indices (Optional[Union[np.ndarray, list]], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """
        raise NotImplementedError

    def get_max_efforts(self) -> np.ndarray:
        """[summary]

        Raises:
            Exception: [description]

        Returns:
            np.ndarray: [description]
        """
        raise NotImplementedError

    def set_gains(self, kps: Optional[np.ndarray] = None, kds: Optional[np.ndarray] = None) -> None:
        """[summary]

        Args:
            kps (Optional[np.ndarray], optional): [description]. Defaults to None.
            kds (Optional[np.ndarray], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """
        raise NotImplementedError

    def get_gains(self) -> Tuple[np.ndarray, np.ndarray]:
        """[summary]

        Raises:
            Exception: [description]

        Returns:
            Tuple[np.ndarray, np.ndarray]: [description]
        """
        raise NotImplementedError

    def switch_control_mode(self, mode: str) -> None:
        """[summary]

        Args:
            mode (str): [description]

        Raises:
            Exception: [description]
        """
        raise NotImplementedError

    def switch_dof_control_mode(self, dof_index: int, mode: str) -> None:
        """[summary]

        Args:
            dof_index (int): [description]
            mode (str): [description]

        Raises:
            Exception: [description]
        """
        raise NotImplementedError

    def set_solver_position_iteration_count(self, count: int) -> None:
        """[summary]

        Args:
            count (int): [description]
        """
        raise NotImplementedError

    def get_solver_position_iteration_count(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        raise NotImplementedError

    def set_solver_velocity_iteration_count(self, count: int):
        """[summary]

        Args:
            count (int): [description]
        """
        raise NotImplementedError

    def get_solver_velocity_iteration_count(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        raise NotImplementedError

    def set_stabilization_threshold(self, threshold: float) -> None:
        """[summary]

        Args:
            threshold (float): [description]
        """
        raise NotImplementedError

    def get_stabilization_threshold(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        raise NotImplementedError

    def set_enabled_self_collisions(self, flag: bool) -> None:
        """[summary]

        Args:
            flag (bool): [description]
        """
        raise NotImplementedError

    def get_enabled_self_collisions(self) -> bool:
        """[summary]

        Returns:
            bool: [description]
        """
        raise NotImplementedError

    def set_sleep_threshold(self, threshold: float) -> None:
        """[summary]

        Args:
            threshold (float): [description]
        """
        raise NotImplementedError

    def get_sleep_threshold(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        raise NotImplementedError
