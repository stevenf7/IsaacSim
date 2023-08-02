# Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import List, Optional, Tuple, Union

import carb
import numpy as np
import omni.kit.app
import torch
import warp as wp
from omni.isaac.core.simulation_context.simulation_context import SimulationContext
from omni.isaac.core.utils.prims import find_matching_prim_paths, get_prim_at_path
from pxr import PhysxSchema, UsdPhysics


class RigidContactView(object):
    """Provides high level functions to deal with rigid prims that track their contacts through filters
    as well as its attributes/ properties.
    This object wraps all matching Rigid Prims found at the regex provided at the prim_paths_expr.

    Note:  if the prim does not already have a rigid body api applied to it before init, it will NOT apply it.

    Args:
        prim_paths_expr (str): prim paths regex to encapsulate all prims that match it.
                                example: "/World/Env[1-5]/Cube" will match /World/Env1/Cube,
                                /World/Env2/Cube..etc.
                                (a non regex prim path can also be used to encapsulate one rigid prim).
        name (str, optional): shortname to be used as a key by Scene class.
                                Note: needs to be unique if the object is added to the Scene.
                                Defaults to "rigid_contact_view".
        prepare_contact_sensors (bool, Optional): if rigid prims in the view are not cloned from a prim in a prepared state,
                                                  (although slow for large number of prims) this ensures that
                                                  appropriate physics settings are applied on all the prim in the view.
        disable_stablization (bool, optional): disables the contact stablization parameter in the physics context
        apply_rigid_body_api (bool, optional): apply rigid body API to prims in prim_paths_expr and filter_paths_expr when prepare_contact_sensors=True
        max_contact_count (int, optional): maximum number of contact data to report when detailed contact information is needed
    """

    def __init__(
        self,
        prim_paths_expr: str,
        filter_paths_expr: List[str],
        name: str = "rigid_contact_view",
        prepare_contact_sensors: bool = True,
        disable_stablization: bool = True,
        apply_rigid_body_api: bool = True,
        max_contact_count: int = 0,
    ) -> None:
        self._name = name
        self._regex_prim_paths = prim_paths_expr
        self._regex_filter_paths = filter_paths_expr
        self._prim_paths = None
        self._physics_view = None
        self._num_shapes = None
        self._num_filters = None
        self.max_contact_count = max_contact_count

        if SimulationContext.instance() is not None:
            self._backend = SimulationContext.instance().backend
            self._device = SimulationContext.instance().device
            self._backend_utils = SimulationContext.instance().backend_utils
            if disable_stablization:
                SimulationContext.instance().get_physics_context().enable_stablization(False)
        else:
            import omni.isaac.core.utils.numpy as np_utils

            self._backend = "numpy"
            self._device = None
            self._backend_utils = np_utils

        if prepare_contact_sensors:
            self._prim_paths = find_matching_prim_paths(prim_paths_expr)
            for path in self._prim_paths:
                self._prepare_contact_reporter(get_prim_at_path(path), apply_rigid_body_api)

            for group_expr in filter_paths_expr:
                self._filter_paths = find_matching_prim_paths(group_expr)
                for path in self._filter_paths:
                    self._prepare_contact_reporter(get_prim_at_path(path), apply_rigid_body_api)
        return

    @property
    def num_shapes(self) -> int:
        """
        Returns:
            int: number of rigid shapes for the prims in the view.
        """
        return self._num_shapes

    @property
    def num_filters(self) -> int:
        """
        Returns:
            int: number of filters bodies that report their contact with the rigid prims.
        """
        return self._num_filters

    def _prepare_contact_reporter(self, prim_at_path, apply_rigid_body_api=False):
        """Prepares the contact reporter by removing the sleep/contact thresholds."""
        # disable sleeping, because sleeping bodies don't get contact reports
        if apply_rigid_body_api:
            if prim_at_path.HasAPI(UsdPhysics.RigidBodyAPI):
                rb_api = UsdPhysics.RigidBodyAPI(prim_at_path)
            else:
                rb_api = UsdPhysics.RigidBodyAPI.Apply(prim_at_path)

            rb_api = PhysxSchema.PhysxRigidBodyAPI.Apply(prim_at_path)
            rb_api.CreateSleepThresholdAttr().Set(0)

        # prepare contact sensors
        cr_api = PhysxSchema.PhysxContactReportAPI.Apply(prim_at_path)
        cr_api.CreateThresholdAttr().Set(0)

    def is_physics_handle_valid(self) -> bool:
        """
        Returns:
            bool: True if the physics handle of the view is valid (i.e physics is initialized for the view). Otherwise False.
        """
        return self._physics_view is not None

    def _invalidate_physics_handle_callback(self, event):
        if event.type == int(omni.timeline.TimelineEventType.STOP):
            self._physics_view = None
        return

    def initialize(self, physics_sim_view: omni.physics.tensors.SimulationView = None) -> None:
        """Create a physics simulation view if not passed and creates a rigid contact view in physX.

        Args:
            physics_sim_view (omni.physics.tensors.SimulationView, optional): current physics simulation view. Defaults to None.
        """
        if physics_sim_view is None:
            physics_sim_view = omni.physics.tensors.create_simulation_view(self._backend)
            physics_sim_view.set_subspace_roots("/")
        carb.log_info("initializing view for {}".format(self._name))
        self._physics_sim_view = physics_sim_view
        self._physics_view = physics_sim_view.create_rigid_contact_view(
            self._regex_prim_paths.replace(".*", "*"),
            filter_patterns=[path.replace(".*", "*") for path in self._regex_filter_paths],
            max_contact_data_count=self.max_contact_count,
        )
        carb.log_info("Rigid Contact View Device: {}".format(self._device))
        self._num_shapes = self._physics_view.sensor_count
        self._num_filters = self._physics_view.filter_count
        return

    def get_net_contact_forces(
        self, indices: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None, clone: bool = True, dt: float = 1.0
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the overall net contact forces on the prims in the view with respect to the world's frame.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.
            dt (float): time step multiplier to convert the underlying impulses to forces. The function returns contact impulses if the default dt is used

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: Net contact forces of the prims with shape (M,3).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self._num_shapes, self._device)
            self._physics_sim_view.enable_warnings(False)
            net_contact_forces = self._physics_view.get_net_contact_forces(dt)
            self._physics_sim_view.enable_warnings(True)
            if clone:
                net_contact_forces = self._backend_utils.clone_tensor(net_contact_forces, device=self._device)
            return net_contact_forces[indices]
        else:
            carb.log_warn("Physics Simulation View is not created yet")
            return None

    def get_contact_force_matrix(
        self,
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
        clone: bool = True,
        dt: float = 1.0,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the contact forces between the prims in the view and the filter prims. i.e., a matrix of dimension
        (self.num_shapes, self.num_filters, 3) where filter_count is the determined according to the filter_paths_expr parameter.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.
            dt (float): time step multiplier to convert the underlying impulses to forces. The function returns contact impulses if the default dt is used

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: Net contact forces between the view prim and the filter prims with shape (M, self.num_filters, 3).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self._num_shapes, self._device)
            self._physics_sim_view.enable_warnings(False)
            net_contact_forces = self._physics_view.get_contact_force_matrix(dt)
            self._physics_sim_view.enable_warnings(True)
            if clone:
                net_contact_forces = self._backend_utils.clone_tensor(net_contact_forces, device=self._device)
            return net_contact_forces[indices, :, :]
        else:
            carb.log_warn("Physics Simulation View is not created yet")
            return None

    def get_contact_force_data(
        self,
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
        clone: bool = True,
        dt: float = 1.0,
    ) -> Tuple[
        Union[np.ndarray, torch.Tensor, wp.indexedarray],
        Union[np.ndarray, torch.Tensor, wp.indexedarray],
        Union[np.ndarray, torch.Tensor, wp.indexedarray],
        Union[np.ndarray, torch.Tensor, wp.indexedarray],
        Union[np.ndarray, torch.Tensor, wp.indexedarray],
        Union[np.ndarray, torch.Tensor, wp.indexedarray],
    ]:
        """
        Gets more detailed contact information between the prims in the view and the filter prims. Specifically, this method provides individual
        contact normals, contact pointes, contact separations as well as contact forces for each pair
        (the sum of which equals the forces that the get_contact_force_matrix method provides as the force aggregate of a pair)
        Given to the dynamic nature of collision between bodies, this method will provide buffers of contact data which are arranged sequentially for each pair.
        The starting index and the number of contact data points for each pair in this stream can be realized from pair_contacts_start_indices,
        and pair_contacts_count tensors. They both have a dimension of (self.num_shapes, self.num_filters) where filter_count is determined
        according to the filter_paths_expr parameter.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.
            dt (float): time step multiplier to convert the underlying impulses to forces. If the default value is used then the forces are in fact contact impulses

        Returns:
            Tuple[Union[np.ndarray, torch.Tensor, wp.indexedarray], Union[np.ndarray, torch.Tensor, wp.indexedarray],
                Union[np.ndarray, torch.Tensor, wp.indexedarray], Union[np.ndarray, torch.Tensor, wp.indexedarray],
                Union[np.ndarray, torch.Tensor, wp.indexedarray], Union[np.ndarray, torch.Tensor, wp.indexedarray]]:
                A set of buffers for normal forces with shape (max_contact_count, 1), points with shape (max_contact_count, 3), normals with shape (max_contact_count, 3),
                and distances with shape (max_contact_count, 1), as well as two tensors with shape (M, self.num_filters)
                to indicate the starting index and the number of contact data points per pair in the aforementioned buffers.
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self._num_shapes, self._device)
            (
                forces,
                points,
                normals,
                distances,
                pair_contacts_count,
                pair_contacts_start_indices,
            ) = self._physics_view.get_contact_data(dt)
            if clone:
                forces = self._backend_utils.clone_tensor(forces, device=self._device)
                points = self._backend_utils.clone_tensor(points, device=self._device)
                normals = self._backend_utils.clone_tensor(normals, device=self._device)
                distances = self._backend_utils.clone_tensor(distances, device=self._device)
                pair_contacts_count = self._backend_utils.clone_tensor(pair_contacts_count, device=self._device)
                pair_contacts_start_indices = self._backend_utils.clone_tensor(
                    pair_contacts_start_indices, device=self._device
                )
            return (
                forces,
                points,
                normals,
                distances,
                pair_contacts_count[indices, :],
                pair_contacts_start_indices[indices, :],
            )

        else:
            carb.log_warn("Physics Simulation View is not created yet")
            return None
