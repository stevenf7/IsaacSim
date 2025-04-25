# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from __future__ import annotations

import weakref

import carb
import isaacsim.core.utils.numpy as numpy_utils
import numpy as np
import omni.kit.app
import omni.physics.tensors
import omni.physx
import omni.physx.bindings
import omni.physx.bindings._physx
import omni.usd
import warp as wp
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.core.utils.prims import get_articulation_root_api_prim_path, get_prim_at_path, get_prim_parent
from pxr import PhysicsSchemaTools, PhysxSchema, Sdf, Usd, UsdGeom, UsdPhysics

from . import _backend, _ops
from .prim import _MSG_PHYSICS_TENSOR_ENTITY_NOT_INITIALIZED, _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID, _MSG_PRIM_NOT_VALID
from .xform_prim import XformPrim


class Articulation(XformPrim):
    """High level wrapper for manipulating prims (that have the Root Articulation API applied) and their attributes.

    This class is a wrapper over one or more USD prims in the stage to provide
    high-level functionality for manipulating articulation properties, and other attributes.
    The prims are specified using paths that can include regular expressions for matching multiple prims.

    Args:
        paths: Single path or list of paths to USD prims. Can include regular expressions for matching multiple prims.
        positions: Positions in the world frame (shape ``(N, 3)``).
            If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
        translations: Translations in the local frame (shape ``(N, 3)``).
            If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
        orientations: Orientations in the world frame (shape ``(N, 4)``, quaternion ``wxyz``).
            If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
        scales: Scales to be applied to the prims (shape ``(N, 3)``).
            If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
        reset_xform_op_properties: Whether to reset the transformation operation attributes of the prims to a standard set.
            See :py:meth:`reset_xform_op_properties` for more details.
        enable_residual_reports: Whether to enable residual reporting for the articulations.

    Raises:
        ValueError: If no prims are found matching the specified path(s).
        AssertionError: If both positions and translations are specified.

    Example:

    .. code-block:: python

        >>> import numpy as np
        >>> import omni.timeline
        >>> from isaacsim.core.experimental.prims import Articulation
        >>>
        >>> # given a USD stage with the prims: /World/prim_0, /World/prim_1, and /World/prim_2
        >>> # where each prim is a reference to the Isaac Sim's Franka Panda USD asset
        >>> # - create wrapper over single prim
        >>> prim = Articulation("/World/prim_0")  # doctest: +NO_CHECK
        >>> # - create wrapper over multiple prims using regex
        >>> prims = Articulation(
        ...     "/World/prim_.*",
        ...     positions=[[x, 0, 0] for x in range(3)],
        ...     reset_xform_op_properties=True,
        ...     enable_residual_reports=True,
        ... )  # doctest: +NO_CHECK
        >>>
        >>> # play the simulation so that the Physics tensor entity becomes valid
        >>> omni.timeline.get_timeline_interface().play()
    """

    def __init__(
        self,
        paths: str | list[str],
        *,
        # XformPrim
        positions: list | np.ndarray | wp.array | None = None,
        translations: list | np.ndarray | wp.array | None = None,
        orientations: list | np.ndarray | wp.array | None = None,
        scales: list | np.ndarray | wp.array | None = None,
        reset_xform_op_properties: bool = False,
        # Articulation
        enable_residual_reports: bool = False,
    ) -> None:
        paths = [paths] if isinstance(paths, str) else paths
        paths = [get_articulation_root_api_prim_path(path) for path in paths]
        super().__init__(
            paths,
            positions=positions,
            translations=translations,
            orientations=orientations,
            scales=scales,
            reset_xform_op_properties=reset_xform_op_properties,
        )
        # default state properties
        self._default_linear_velocities = None
        self._default_angular_velocities = None
        self._default_dof_positions = None
        self._default_dof_velocities = None
        self._default_dof_efforts = None
        self._default_dof_stiffnesses = None
        self._default_dof_dampings = None
        # initialize instance from arguments
        self._enable_residual_reports = enable_residual_reports
        if enable_residual_reports:
            Articulation.ensure_api(self.prims, PhysxSchema.PhysxResidualReportingAPI)
        # physics tensor entity properties
        # - links
        self._num_links = None
        self._link_names = None
        self._link_index_dict = None
        self._link_paths = None
        # - joints
        self._num_joints = None
        self._joint_names = None
        self._joint_index_dict = None
        self._joint_paths = None
        self._joint_types = None
        # - DOFs
        self._num_dofs = None
        self._dof_names = None
        self._dof_index_dict = None
        self._dof_paths = None
        self._dof_types = None
        # - other properties
        self._num_shapes = 0
        self._num_fixed_tendons = 0
        # - articulation physics view
        self._physics_articulation_view = None
        self._physics_tensor_entity_initialized = False
        self._subscription_to_timeline_stop_event = (
            SimulationManager._timeline.get_timeline_event_stream().create_subscription_to_pop_by_type(
                int(omni.timeline.TimelineEventType.STOP),
                lambda event, obj=weakref.proxy(self): obj._on_timeline_stop(event),
            )
        )
        # setup physics-related configuration if simulation is running
        if SimulationManager._physics_sim_view__warp is not None:
            SimulationManager._physx_sim_interface.flush_changes()
            self._on_physics_ready(None)

    def __del__(self):
        """Clean up instance by deregistering callbacks and resetting internal state."""
        super().__del__()
        self._subscription_to_timeline_stop_event = None
        if hasattr(self, "_physics_articulation_view"):
            del self._physics_articulation_view

    """
    Properties.
    """

    @property
    def num_dofs(self) -> int:
        """Number of degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`usd`, :guilabel:`tensor`.

        Returns:
            Number of DOFs.

        Example:

        .. code-block:: python

            >>> prims.num_dofs
            9
        """
        if self._num_dofs is None:
            self._query_articulation_properties()
        return self._num_dofs

    @property
    def dof_names(self) -> list[str]:
        """Degree of freedom (DOFs) names of the prims.

        Backends: :guilabel:`usd`, :guilabel:`tensor`.

        Returns:
            Ordered list of DOF names.

        Example:

        .. code-block:: python

            >>> prims.dof_names
            ['panda_joint1', 'panda_joint2', 'panda_joint3',
             'panda_joint4', 'panda_joint5', 'panda_joint6',
             'panda_joint7', 'panda_finger_joint1', 'panda_finger_joint2']
        """
        if self._dof_names is None:
            self._query_articulation_properties()
        return self._dof_names

    @property
    def dof_paths(self) -> list[list[str]]:
        """Degree of freedom (DOFs) paths of the prims.

        Backends: :guilabel:`usd`, :guilabel:`tensor`.

        Returns:
            Ordered list of DOF names.

        Example:

        .. code-block:: python

            >>> prims.dof_paths
            [['/World/prim_0/panda_link0/panda_joint1', '/World/prim_0/panda_link1/panda_joint2', '/World/prim_0/panda_link2/panda_joint3',
              '/World/prim_0/panda_link3/panda_joint4', '/World/prim_0/panda_link4/panda_joint5', '/World/prim_0/panda_link5/panda_joint6',
              '/World/prim_0/panda_link6/panda_joint7', '/World/prim_0/panda_hand/panda_finger_joint1', '/World/prim_0/panda_hand/panda_finger_joint2'],
             ['/World/prim_1/panda_link0/panda_joint1', '/World/prim_1/panda_link1/panda_joint2', '/World/prim_1/panda_link2/panda_joint3',
              '/World/prim_1/panda_link3/panda_joint4', '/World/prim_1/panda_link4/panda_joint5', '/World/prim_1/panda_link5/panda_joint6',
              '/World/prim_1/panda_link6/panda_joint7', '/World/prim_1/panda_hand/panda_finger_joint1', '/World/prim_1/panda_hand/panda_finger_joint2'],
             ['/World/prim_2/panda_link0/panda_joint1', '/World/prim_2/panda_link1/panda_joint2', '/World/prim_2/panda_link2/panda_joint3',
              '/World/prim_2/panda_link3/panda_joint4', '/World/prim_2/panda_link4/panda_joint5', '/World/prim_2/panda_link5/panda_joint6',
              '/World/prim_2/panda_link6/panda_joint7', '/World/prim_2/panda_hand/panda_finger_joint1', '/World/prim_2/panda_hand/panda_finger_joint2']]
        """
        if self._dof_paths is None:
            self._query_articulation_properties()
        return self._dof_paths

    @property
    def dof_types(self) -> list[omni.physics.tensors.DofType]:
        """Degree of freedom (DOFs) types of the prims.

        Backends: :guilabel:`usd`, :guilabel:`tensor`.

        Returns:
            Ordered list of DOF types.

        Example:

        .. code-block:: python

            >>> prims.dof_types
            [<DofType.Rotation: 0>, <DofType.Rotation: 0>, <DofType.Rotation: 0>,
             <DofType.Rotation: 0>, <DofType.Rotation: 0>, <DofType.Rotation: 0>,
             <DofType.Rotation: 0>, <DofType.Translation: 1>, <DofType.Translation: 1>]
        """
        if self._dof_types is None:
            self._query_articulation_properties()
        return self._dof_types

    @property
    def num_joints(self) -> int:
        """Number of joints of the prims.

        Backends: :guilabel:`usd`, :guilabel:`tensor`.

        Returns:
            Number of joints.

        Example:

        .. code-block:: python

            >>> prims.num_joints
            11
        """
        if self._num_joints is None:
            self._query_articulation_properties()
        return self._num_joints

    @property
    def joint_names(self) -> list[str]:
        """Joint names of the prims.

        Backends: :guilabel:`usd`, :guilabel:`tensor`.

        Returns:
            Ordered list of joint names.

        Example:

        .. code-block:: python

            >>> prims.joint_names
            ['panda_joint1', 'panda_joint2', 'panda_joint3', 'panda_joint4',
             'panda_joint5', 'panda_joint6', 'panda_joint7', 'panda_joint8',
             'panda_hand_joint', 'panda_finger_joint1', 'panda_finger_joint2']
        """
        if self._joint_names is None:
            self._query_articulation_properties()
        return self._joint_names

    @property
    def joint_paths(self) -> list[list[str]]:
        """Joint paths of the prims.

        Backends: :guilabel:`usd`, :guilabel:`tensor`.

        Returns:
            Ordered list of joint paths.

        Example:

        .. code-block:: python

            >>> prims.joint_paths
            [['/World/prim_0/panda_link0/panda_joint1', '/World/prim_0/panda_link1/panda_joint2', '/World/prim_0/panda_link2/panda_joint3',
              '/World/prim_0/panda_link3/panda_joint4', '/World/prim_0/panda_link4/panda_joint5', '/World/prim_0/panda_link5/panda_joint6',
              '/World/prim_0/panda_link6/panda_joint7', '/World/prim_0/panda_link7/panda_joint8', '/World/prim_0/panda_link8/panda_hand_joint',
              '/World/prim_0/panda_hand/panda_finger_joint1', '/World/prim_0/panda_hand/panda_finger_joint2'],
             ['/World/prim_1/panda_link0/panda_joint1', '/World/prim_1/panda_link1/panda_joint2', '/World/prim_1/panda_link2/panda_joint3',
              '/World/prim_1/panda_link3/panda_joint4', '/World/prim_1/panda_link4/panda_joint5', '/World/prim_1/panda_link5/panda_joint6',
              '/World/prim_1/panda_link6/panda_joint7', '/World/prim_1/panda_link7/panda_joint8', '/World/prim_1/panda_link8/panda_hand_joint',
              '/World/prim_1/panda_hand/panda_finger_joint1', '/World/prim_1/panda_hand/panda_finger_joint2'],
             ['/World/prim_2/panda_link0/panda_joint1', '/World/prim_2/panda_link1/panda_joint2', '/World/prim_2/panda_link2/panda_joint3',
              '/World/prim_2/panda_link3/panda_joint4', '/World/prim_2/panda_link4/panda_joint5', '/World/prim_2/panda_link5/panda_joint6',
              '/World/prim_2/panda_link6/panda_joint7', '/World/prim_2/panda_link7/panda_joint8', '/World/prim_2/panda_link8/panda_hand_joint',
              '/World/prim_2/panda_hand/panda_finger_joint1', '/World/prim_2/panda_hand/panda_finger_joint2']]
        """
        if self._joint_paths is None:
            self._query_articulation_properties()
        return self._joint_paths

    @property
    def joint_types(self) -> list[omni.physics.tensors.JointType]:
        """Joint types of the prims.

        Backends: :guilabel:`tensor`.

        Returns:
            Ordered list of joint types.

        Raises:
            AssertionError: Physics tensor entity is not initialized.

        Example:

        .. code-block:: python

            >>> prims.joint_types
            [<JointType.Revolute: 1>, <JointType.Revolute: 1>, <JointType.Revolute: 1>,
             <JointType.Revolute: 1>, <JointType.Revolute: 1>, <JointType.Revolute: 1>, <JointType.Revolute: 1>,
             <JointType.Fixed: 0>, <JointType.Fixed: 0>, <JointType.Prismatic: 2>, <JointType.Prismatic: 2>]
        """
        assert self._physics_tensor_entity_initialized, _MSG_PHYSICS_TENSOR_ENTITY_NOT_INITIALIZED
        return self._joint_types

    @property
    def num_links(self) -> int:
        """Number of links of the prims.

        Backends: :guilabel:`usd`, :guilabel:`tensor`.

        Returns:
            Number of links.

        Example:

        .. code-block:: python

            >>> prims.num_links
            12
        """
        if self._num_links is None:
            self._query_articulation_properties()
        return self._num_links

    @property
    def link_names(self) -> list[str]:
        """Link names of the prims.

        Backends: :guilabel:`usd`, :guilabel:`tensor`.

        Returns:
            Ordered list of link names.

        Example:

        .. code-block:: python

            >>> prims.link_names
            ['panda_link0', 'panda_link1', 'panda_link2', 'panda_link3',
             'panda_link4', 'panda_link5', 'panda_link6', 'panda_link7',
             'panda_link8', 'panda_hand', 'panda_leftfinger', 'panda_rightfinger']
        """
        if self._link_names is None:
            self._query_articulation_properties()
        return self._link_names

    @property
    def link_paths(self) -> list[list[str]]:
        """Link paths of the prims.

        Backends: :guilabel:`usd`, :guilabel:`tensor`.

        Returns:
            Ordered list of link paths.

        Example:

        .. code-block:: python

            >>> prims.link_paths
            [['/World/prim_0/panda_link0', '/World/prim_0/panda_link1', '/World/prim_0/panda_link2', '/World/prim_0/panda_link3',
              '/World/prim_0/panda_link4', '/World/prim_0/panda_link5', '/World/prim_0/panda_link6', '/World/prim_0/panda_link7',
              '/World/prim_0/panda_link8', '/World/prim_0/panda_hand', '/World/prim_0/panda_leftfinger', '/World/prim_0/panda_rightfinger'],
             ['/World/prim_1/panda_link0', '/World/prim_1/panda_link1', '/World/prim_1/panda_link2', '/World/prim_1/panda_link3',
              '/World/prim_1/panda_link4', '/World/prim_1/panda_link5', '/World/prim_1/panda_link6', '/World/prim_1/panda_link7',
              '/World/prim_1/panda_link8', '/World/prim_1/panda_hand', '/World/prim_1/panda_leftfinger', '/World/prim_1/panda_rightfinger'],
             ['/World/prim_2/panda_link0', '/World/prim_2/panda_link1', '/World/prim_2/panda_link2', '/World/prim_2/panda_link3',
              '/World/prim_2/panda_link4', '/World/prim_2/panda_link5', '/World/prim_2/panda_link6', '/World/prim_2/panda_link7',
              '/World/prim_2/panda_link8', '/World/prim_2/panda_hand', '/World/prim_2/panda_leftfinger', '/World/prim_2/panda_rightfinger']]
        """
        if self._link_paths is None:
            self._query_articulation_properties()
        return self._link_paths

    @property
    def num_shapes(self) -> int:
        """Number of rigid shapes of the prims.

        Backends: :guilabel:`tensor`.

        Returns:
            Number of rigid shapes.

        Raises:
            AssertionError: Physics tensor entity is not initialized.

        Example:

        .. code-block:: python

            >>> prims.num_shapes
            25
        """
        assert self._physics_tensor_entity_initialized, _MSG_PHYSICS_TENSOR_ENTITY_NOT_INITIALIZED
        return self._num_shapes

    @property
    def num_fixed_tendons(self) -> int:
        """Number of fixed tendons of the prims.

        Backends: :guilabel:`tensor`.

        Returns:
            Number of fixed tendons.

        Raises:
            AssertionError: Physics tensor entity is not initialized.

        Example:

        .. code-block:: python

            >>> prims.num_fixed_tendons
            0
        """
        assert self._physics_tensor_entity_initialized, _MSG_PHYSICS_TENSOR_ENTITY_NOT_INITIALIZED
        return self._num_fixed_tendons

    @property
    def jacobian_matrix_shape(self) -> tuple[int, int, int]:
        """Jacobian matrix shape.

        Backends: :guilabel:`tensor`.

        The Jacobian matrix shape depends on the number of links, DOFs, and whether the articulation base is fixed
        (e.g.: robotic manipulators) or not (e.g.: mobile robots).

        * Fixed articulation base: ``(num_links - 1, 6, num_dofs)``
        * Non-fixed (floating) articulation base: ``(num_links, 6, num_dofs + 6)``

        Each link has 6 values in the Jacobian representing its linear and angular motion along the
        three coordinate axes. The extra 6 DOFs in the last dimension, for floating bases,
        correspond to the linear and angular degrees of freedom of the free root link.

        Returns:
            Shape of Jacobian matrix (for one prim).

        Raises:
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # for the Franka Panda (a robotic manipulator with fixed base):
            >>> # - num_links: 12
            >>> # - num_dofs: 9
            >>> prims.jacobian_matrix_shape
            (11, 6, 9)
        """
        assert self._physics_tensor_entity_initialized, _MSG_PHYSICS_TENSOR_ENTITY_NOT_INITIALIZED
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        shape = self._physics_articulation_view.jacobian_shape
        return (shape[0] // 6, 6, shape[1])

    @property
    def mass_matrix_shape(self) -> tuple[int, int]:
        """Mass matrix shape.

        Backends: :guilabel:`tensor`.

        The mass matrix shape depends on the number of DOFs, and whether the articulation base is fixed
        (e.g.: robotic manipulators) or not (e.g.: mobile robots).

        * Fixed articulation base: ``(num_dofs, num_dofs)``
        * Non-fixed (floating) articulation base: ``(num_dofs + 6, num_dofs + 6)``

        Returns:
            Shape of mass matrix (for one prim).

        Raises:
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # for the Franka Panda:
            >>> # - num_dofs: 9
            >>> prims.mass_matrix_shape
            (9, 9)
        """
        assert self._physics_tensor_entity_initialized, _MSG_PHYSICS_TENSOR_ENTITY_NOT_INITIALIZED
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        return self._physics_articulation_view.generalized_mass_matrix_shape

    """
    Methods.
    """

    def is_physics_tensor_entity_valid(self) -> bool:
        """Check if the physics tensor entity is valid.

        Returns:
            Whether the physics tensor entity is valid.
        """
        return SimulationManager._physics_sim_view__warp is not None and self._physics_articulation_view is not None

    def is_physics_tensor_entity_initialized(self) -> bool:
        """Check if the physics tensor entity is initialized.

        Returns:
            Whether the physics tensor entity is initialized.
        """
        return self._physics_tensor_entity_initialized

    def get_link_indices(self, names: str | list[str]) -> wp.array:
        """Get the indices of one or more links of the prims.

        Backends: :guilabel:`usd`, :guilabel:`tensor`.

        Args:
            names: Single name or list of names of links to get indices for.

        Returns:
            Indices of the specified link names.

        Example:

        .. code-block:: python

            >>> # show all link names and their indices
            >>> for name in prims.link_names:
            ...     print(prims.get_link_indices(name), name)
            [0] panda_link0
            [1] panda_link1
            [2] panda_link2
            [3] panda_link3
            [4] panda_link4
            [5] panda_link5
            [6] panda_link6
            [7] panda_link7
            [8] panda_link8
            [9] panda_hand
            [10] panda_leftfinger
            [11] panda_rightfinger
            >>>
            >>> # get the indices of Franka Panda's finger links
            >>> indices = prims.get_link_indices(["panda_leftfinger", "panda_rightfinger"])
            >>> print(indices)
            [10 11]
        """
        indices = []
        for name in [names] if isinstance(names, str) else names:
            assert name in self.link_names, f"Invalid link name ({name}). Available links: {self.link_names}"
            indices.append(self._link_index_dict[name])
        return _ops.place(indices, dtype=wp.int32, device=self._device)

    def get_joint_indices(self, names: str | list[str]) -> wp.array:
        """Get the indices of one or more joints of the prims.

        Backends: :guilabel:`usd`, :guilabel:`tensor`.

        Args:
            names: Single name or list of names of joints to get indices for.

        Returns:
            Indices of the specified joint names.

        Example:

        .. code-block:: python

            >>> # show all joint names and their indices
            >>> for name in prims.joint_names:
            ...     print(prims.get_joint_indices(name), name)
            [0] panda_joint1
            [1] panda_joint2
            [2] panda_joint3
            [3] panda_joint4
            [4] panda_joint5
            [5] panda_joint6
            [6] panda_joint7
            [7] panda_joint8
            [8] panda_hand_joint
            [9] panda_finger_joint1
            [10] panda_finger_joint2
            >>>
            >>> # get the indices of Franka Panda's finger joints
            >>> indices = prims.get_joint_indices(["panda_finger_joint1", "panda_finger_joint2"])
            >>> print(indices)
            [ 9 10]
        """
        indices = []
        for name in [names] if isinstance(names, str) else names:
            assert name in self.joint_names, f"Invalid joint name ({name}). Available joints: {self.joint_names}"
            indices.append(self._joint_index_dict[name])
        return _ops.place(indices, dtype=wp.int32, device=self._device)

    def get_dof_indices(self, names: str | list[str]) -> wp.array:
        """Get the indices of one or more degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`usd`, :guilabel:`tensor`.

        Args:
            names: Single name or list of names of DOFs to get indices for.

        Returns:
            Indices of the specified DOF names.

        Example:

        .. code-block:: python

            >>> # show all DOF names and their indices
            >>> for name in prims.dof_names:
            ...     print(prims.get_dof_indices(name), name)
            [0] panda_joint1
            [1] panda_joint2
            [2] panda_joint3
            [3] panda_joint4
            [4] panda_joint5
            [5] panda_joint6
            [6] panda_joint7
            [7] panda_finger_joint1
            [8] panda_finger_joint2
            >>>
            >>> # get the indices of Franka Panda's finger DOFs
            >>> indices = prims.get_dof_indices(["panda_finger_joint1", "panda_finger_joint2"])
            >>> print(indices)
            [7 8]
        """
        indices = []
        for name in [names] if isinstance(names, str) else names:
            assert name in self.dof_names, f"Invalid DOF name ({name}). Available DOFs: {self.dof_names}"
            indices.append(self._dof_index_dict[name])
        return _ops.place(indices, dtype=wp.int32, device=self._device)

    def get_dof_limits(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> tuple[wp.array, wp.array]:
        """Get the limits of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            Two-element tuple: 1) Lower limits (shape ``(N, D)``). 2) Upper limits (shape ``(N, D)``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the DOF limits of all prims
            >>> lower, upper = prims.get_dof_limits()
            >>> lower.shape, upper.shape
            ((3, 9), (3, 9))
            >>>
            >>> # get the DOF limits of the first and last prims
            >>> lower, upper = prims.get_dof_limits(indices=[0, 2])
            >>> lower.shape, upper.shape
            ((2, 9), (2, 9))
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_dof_limits()  # shape: (N, max_dofs, 2)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            return (
                data[indices, dof_indices, wp.array([0], dtype=wp.int32, device=data.device)]
                .contiguous()
                .reshape((indices.shape[0], dof_indices.shape[0]))
                .to(self._device),
                data[indices, dof_indices, wp.array([1], dtype=wp.int32, device=data.device)]
                .contiguous()
                .reshape((indices.shape[0], dof_indices.shape[0]))
                .to(self._device),
            )
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            lower = np.zeros((indices.shape[0], dof_indices.shape[0]), dtype=np.float32)
            upper = np.zeros((indices.shape[0], dof_indices.shape[0]), dtype=np.float32)
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    dof_prim = get_prim_at_path(self.dof_paths[index][dof_index])
                    if self.dof_types[dof_index] == omni.physics.tensors.DofType.Translation:
                        joint_api = UsdPhysics.PrismaticJoint(dof_prim)
                        lower[i][j] = joint_api.GetLowerLimitAttr().Get()
                        upper[i][j] = joint_api.GetUpperLimitAttr().Get()
                    else:
                        joint_api = UsdPhysics.RevoluteJoint(dof_prim)
                        lower[i][j] = np.deg2rad(joint_api.GetLowerLimitAttr().Get())
                        upper[i][j] = np.deg2rad(joint_api.GetUpperLimitAttr().Get())
            return _ops.place(lower, device=self._device), _ops.place(upper, device=self._device)

    def set_dof_limits(
        self,
        lower: list | np.ndarray | wp.array | None = None,
        upper: list | np.ndarray | wp.array | None = None,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the limits of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            lower: Lower limits (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            upper: Upper limits (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Raises:
            AssertionError: If neither lower nor upper limits are specified.
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set the DOF lower limits for all prims to -0.25
            >>> prims.set_dof_limits(lower=[-0.25])
        """
        assert (
            lower is not None or upper is not None
        ), "Both 'lower' and 'upper' are not defined. Define at least one of them"
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_dof_limits()  # shape: (N, max_dofs, 2)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            if lower is not None:
                lower = _ops.broadcast_to(
                    lower, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=data.device
                ).reshape((indices.shape[0], dof_indices.shape[0], 1))
                wp.copy(data[indices, dof_indices, wp.array([0], dtype=wp.int32, device=data.device)], lower)
            if upper is not None:
                upper = _ops.broadcast_to(
                    upper, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=data.device
                ).reshape((indices.shape[0], dof_indices.shape[0], 1))
                wp.copy(data[indices, dof_indices, wp.array([1], dtype=wp.int32, device=data.device)], upper)
            self._physics_articulation_view.set_dof_limits(data, indices)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            if lower is not None:
                lower = _ops.broadcast_to(
                    lower,
                    shape=(indices.shape[0], dof_indices.shape[0]),
                    dtype=wp.float32,
                    device=self._device,
                ).numpy()
            if upper is not None:
                upper = _ops.broadcast_to(
                    upper,
                    shape=(indices.shape[0], dof_indices.shape[0]),
                    dtype=wp.float32,
                    device=self._device,
                ).numpy()
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    dof_prim = get_prim_at_path(self.dof_paths[index][dof_index])
                    if self.dof_types[dof_index] == omni.physics.tensors.DofType.Translation:
                        joint_api = UsdPhysics.PrismaticJoint(dof_prim)
                        drive_type = "linear"
                    else:
                        joint_api = UsdPhysics.RevoluteJoint(dof_prim)
                        drive_type = "angular"
                    if lower is not None:
                        lower_limit = lower[i][j]
                        if drive_type == "angular":
                            lower_limit = np.rad2deg(lower_limit)
                        joint_api.GetLowerLimitAttr().Set(lower_limit.item())
                    if upper is not None:
                        upper_limit = upper[i][j]
                        if drive_type == "angular":
                            upper_limit = np.rad2deg(upper_limit)
                        joint_api.GetUpperLimitAttr().Set(upper_limit.item())

    def set_dof_friction_coefficients(
        self,
        coefficients: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the friction coefficients of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Search for *Articulation Joint Friction* in |physx_docs| for more details.

        Args:
            coefficients: Friction coefficients (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set the DOF friction coefficients for all prims
            >>> prims.set_dof_friction_coefficients([0.5])
            >>>
            >>> # set the friction coefficients for the first and last prims' finger DOFs
            >>> prims.set_dof_friction_coefficients([1.5], indices=[0, 2], dof_indices=[7, 8])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_dof_friction_coefficients()  # shape: (N, max_dofs)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            coefficients = _ops.broadcast_to(
                coefficients, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=data.device
            )
            wp.copy(data[indices, dof_indices], coefficients)
            self._physics_articulation_view.set_dof_friction_coefficients(data, indices)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            coefficients = _ops.broadcast_to(
                coefficients,
                shape=(indices.shape[0], dof_indices.shape[0]),
                dtype=wp.float32,
                device=self._device,
            ).numpy()
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    dof_prim = get_prim_at_path(self.dof_paths[index][dof_index])
                    physx_joint_api = Articulation.ensure_api([dof_prim], PhysxSchema.PhysxJointAPI)[0]
                    physx_joint_api.GetJointFrictionAttr().Set(float(coefficients[i][j].item()))

    def get_dof_friction_coefficients(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the friction coefficients of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Search for *Articulation Joint Friction* in |physx_docs| for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            Friction coefficients (shape ``(N, D)``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the DOF friction coefficients of all prims
            >>> friction_coefficients = prims.get_dof_friction_coefficients()
            >>> friction_coefficients.shape
            (3, 9)
            >>>
            >>> # get the DOF friction coefficients of the first and last prims' finger DOFs
            >>> friction_coefficients = prims.get_dof_friction_coefficients(indices=[0, 2], dof_indices=[7, 8])
            >>> friction_coefficients.shape
            (2, 2)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_dof_friction_coefficients()  # shape: (N, max_dofs)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            return data[indices, dof_indices].contiguous().to(self._device)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            data = np.zeros((indices.shape[0], dof_indices.shape[0]), dtype=np.float32)
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    dof_prim = get_prim_at_path(self.dof_paths[index][dof_index])
                    physx_joint_api = Articulation.ensure_api([dof_prim], PhysxSchema.PhysxJointAPI)[0]
                    data[i][j] = physx_joint_api.GetJointFrictionAttr().Get()
            return _ops.place(data, device=self._device)

    def set_dof_armatures(
        self,
        armatures: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the armatures of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Search for *Armature* in |physx_docs| for more details.

        Args:
            armatures: Armatures (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set the DOF armatures for all prims
            >>> prims.set_dof_armatures([0.5])
            >>>
            >>> # set the armatures for the first and last prims' finger DOFs
            >>> prims.set_dof_armatures([1.5], indices=[0, 2], dof_indices=[7, 8])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_dof_armatures()  # shape: (N, max_dofs)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            armatures = _ops.broadcast_to(
                armatures, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=data.device
            )
            wp.copy(data[indices, dof_indices], armatures)
            self._physics_articulation_view.set_dof_armatures(data, indices)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            armatures = _ops.broadcast_to(
                armatures,
                shape=(indices.shape[0], dof_indices.shape[0]),
                dtype=wp.float32,
                device=self._device,
            ).numpy()
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    dof_prim = get_prim_at_path(self.dof_paths[index][dof_index])
                    physx_joint_api = Articulation.ensure_api([dof_prim], PhysxSchema.PhysxJointAPI)[0]
                    physx_joint_api.GetArmatureAttr().Set(float(armatures[i][j].item()))

    def get_dof_armatures(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the armatures of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Search for *Armature* in |physx_docs| for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            Armatures (shape ``(N, D)``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the DOF armatures of all prims
            >>> armatures = prims.get_dof_armatures()
            >>> armatures.shape
            (3, 9)
            >>>
            >>> # get the DOF armatures of the first and last prims' finger DOFs
            >>> armatures = prims.get_dof_armatures(indices=[0, 2], dof_indices=[7, 8])
            >>> armatures.shape
            (2, 2)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_dof_armatures()  # shape: (N, max_dofs)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            return data[indices, dof_indices].contiguous().to(self._device)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            data = np.zeros((indices.shape[0], dof_indices.shape[0]), dtype=np.float32)
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    dof_prim = get_prim_at_path(self.dof_paths[index][dof_index])
                    physx_joint_api = Articulation.ensure_api([dof_prim], PhysxSchema.PhysxJointAPI)[0]
                    data[i][j] = physx_joint_api.GetArmatureAttr().Get()
            return _ops.place(data, device=self._device)

    def set_dof_position_targets(
        self,
        positions: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the position targets of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        .. note::

            This method set the desired target position for the DOFs, not the instantaneous positions.
            It may take several simulation steps to reach the target position
            (depending on the DOFs' stiffness and damping values).

        .. hint::

            High stiffness causes the DOF to move faster and harder towards the desired target,
            while high damping softens but also slows the DOF's movement towards the target.

            * For position control, set relatively high stiffness and non-zero low damping (to reduce vibrations).

        Args:
            positions: Position targets (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set random DOF position targets for all prims
            >>> prims.set_dof_position_targets(np.random.uniform(low=-0.25, high=0.25, size=(3, 9)))
            >>>
            >>> # open all the Franka Panda fingers (finger DOFs to 0.04)
            >>> prims.set_dof_position_targets([0.04], dof_indices=[7, 8])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_dof_position_targets()  # shape: (N, max_dofs)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            positions = _ops.broadcast_to(
                positions, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=data.device
            )
            wp.copy(data[indices, dof_indices], positions)
            self._physics_articulation_view.set_dof_position_targets(data, indices)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            positions = _ops.broadcast_to(
                positions,
                shape=(indices.shape[0], dof_indices.shape[0]),
                dtype=wp.float32,
                device=self._device,
            ).numpy()
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    drive_api, drive_type = self._get_drive_api_and_type(index, dof_index)
                    position = positions[i][j].item()
                    if drive_type == "angular":
                        position = np.rad2deg(position)
                    drive_api.GetTargetPositionAttr().Set(position)

    def set_dof_positions(
        self,
        positions: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the positions of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`.

        .. warning::

            This method *teleports* prims to the specified DOF positions.
            Use the :py:meth:`set_dof_position_targets` method to control the DOFs' positions.

        Args:
            positions: Positions (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # set random DOF positions for all prims
            >>> prims.set_dof_positions(np.random.uniform(low=-0.25, high=0.25, size=(3, 9)))
            >>>
            >>> # set all the Franka Panda fingers to closed position immediately (finger DOFs to 0.0)
            >>> prims.set_dof_positions([0.0], dof_indices=[7, 8])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_dof_positions()  # shape: (N, max_dofs)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
        positions = _ops.broadcast_to(
            positions, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=data.device
        )
        wp.copy(data[indices, dof_indices], positions)
        self._physics_articulation_view.set_dof_positions(data, indices)
        self._physics_articulation_view.set_dof_position_targets(data, indices)

    def set_dof_velocity_targets(
        self,
        velocities: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the velocity targets of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        .. note::

            This method set the desired target velocity for the DOFs, not the instantaneous velocities.
            It may take several simulation steps to reach the target velocity
            (depending on the DOFs' stiffness and damping values).

        .. hint::

            High stiffness causes the DOF to move faster and harder towards the desired target,
            while high damping softens but also slows the DOF's movement towards the target.

            * For velocity control, set zero stiffness and non-zero damping.

        Args:
            velocities: Velocity targets (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set random DOF velocity targets for all prims
            >>> prims.set_dof_velocity_targets(np.random.uniform(low=-10, high=10, size=(3, 9)))
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_dof_velocity_targets()  # shape: (N, max_dofs)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            velocities = _ops.broadcast_to(
                velocities, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=data.device
            )
            wp.copy(data[indices, dof_indices], velocities)
            self._physics_articulation_view.set_dof_velocity_targets(data, indices)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            velocities = _ops.broadcast_to(
                velocities,
                shape=(indices.shape[0], dof_indices.shape[0]),
                dtype=wp.float32,
                device=self._device,
            ).numpy()
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    drive_api, drive_type = self._get_drive_api_and_type(index, dof_index)
                    velocity = velocities[i][j].item()
                    if drive_type == "angular":
                        velocity = np.rad2deg(velocity)
                    drive_api.GetTargetVelocityAttr().Set(velocity)

    def set_dof_velocities(
        self,
        velocities: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the velocities of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`.

        .. warning::

            This method set the specified DOF velocities immediately.
            Use the :py:meth:`set_dof_velocity_targets` method to control the DOFs' velocities.

        Args:
            velocities: Velocities (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # set random DOF velocities for all prims
            >>> prims.set_dof_velocities(np.random.uniform(low=-10, high=10, size=(3, 9)))
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_dof_velocities()  # shape: (N, max_dofs)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
        velocities = _ops.broadcast_to(
            velocities, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=data.device
        )
        wp.copy(data[indices, dof_indices], velocities)
        self._physics_articulation_view.set_dof_velocities(data, indices)
        self._physics_articulation_view.set_dof_velocity_targets(data, indices)

    def set_dof_efforts(
        self,
        efforts: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the efforts of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`.

        .. note::

            For effort control, this method must be used.
            In contrast to the methods that set a target for DOF position/velocity,
            this method must be called at every update step to ensure effort control.

        .. hint::

            For effort control, set zero stiffness and damping, or remove DOF's drive.

        Args:
            efforts: Efforts (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # set random DOF efforts for all prims
            >>> prims.set_dof_efforts(np.random.randn(3, 9))
            >>>
            >>> # set random efforts for the first and last prims' finger DOFs
            >>> prims.set_dof_efforts(np.random.randn(2, 2), indices=[0, 2], dof_indices=[7, 8])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_dof_actuation_forces()  # shape: (N, max_dofs)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
        efforts = _ops.broadcast_to(
            efforts, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=data.device
        )
        wp.copy(data[indices, dof_indices], efforts)
        self._physics_articulation_view.set_dof_actuation_forces(data, indices)

    def get_dof_efforts(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the efforts of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            DOF efforts (shape ``(N, D)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # get the DOF efforts of all prims
            >>> efforts = prims.get_dof_efforts()
            >>> efforts.shape
            (3, 9)
            >>>
            >>> # get the DOF efforts of the first and last prims' finger DOFs
            >>> efforts = prims.get_dof_efforts(indices=[0, 2], dof_indices=[7, 8])
            >>> efforts.shape
            (2, 2)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_dof_actuation_forces()  # shape: (N, max_dofs)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
        return data[indices, dof_indices].contiguous().to(self._device)

    def get_dof_projected_joint_forces(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the degrees of freedom (DOF) projected joint forces of the prims.

        Backends: :guilabel:`tensor`.

        This method projects the links incoming joint forces in the motion direction
        and hence is the active component of the force.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            DOF projected joint forces (shape ``(N, D)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # get the DOF projected joint forces of all prims
            >>> forces = prims.get_dof_projected_joint_forces()
            >>> forces.shape
            (3, 9)
            >>>
            >>> # get the projected joint forces of the first and last prims' finger DOFs
            >>> forces = prims.get_dof_projected_joint_forces(indices=[0, 2], dof_indices=[7, 8])
            >>> forces.shape
            (2, 2)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_dof_projected_joint_forces()  # shape: (N, max_dofs)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
        return data[indices, dof_indices].contiguous().to(self._device)

    def get_link_incoming_joint_force(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        link_indices: list | np.ndarray | wp.array | None = None,
    ) -> tuple[wp.array, wp.array]:
        """Get the link incoming joint forces and torques to external loads of the prims.

        Backends: :guilabel:`tensor`.

        In a kinematic tree, each link has a single incoming joint.
        This method provides the total 6D force/torque of links incoming joints.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            link_indices: Indices of links to process (shape ``(L,)``). If not defined, all links are processed.

        Returns:
            Two-elements tuple. 1) The link incoming joint forces (shape ``(N, L, 3)``).
            2) The link incoming joint torques (shape ``(N, L, 3)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # get the incoming joint forces and torques of the links of all prims
            >>> forces, torques = prims.get_link_incoming_joint_force()
            >>> forces.shape, torques.shape
            ((3, 12, 3), (3, 12, 3))
            >>>
            >>> # get the incoming joint forces and torques of the first and last prims' finger links
            >>> forces, torques = prims.get_link_incoming_joint_force(indices=[0, 2], link_indices=[10, 11])
            >>> forces.shape, torques.shape
            ((2, 2, 3), (2, 2, 3))
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_link_incoming_joint_force()  # shape: (N, max_links, 6)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        link_indices = _ops.resolve_indices(link_indices, count=self.num_links, device=data.device)
        return (
            data[indices, link_indices, :3].contiguous().to(self._device),
            data[indices, link_indices, 3:].contiguous().to(self._device),
        )

    def get_dof_positions(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the positions of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            DOF positions (shape ``(N, D)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # get the DOF position of all prims
            >>> positions = prims.get_dof_positions()
            >>> positions.shape
            (3, 9)
            >>>
            >>> # get the DOF position of the first and last prims' finger DOFs
            >>> positions = prims.get_dof_positions(indices=[0, 2], dof_indices=[7, 8])
            >>> positions.shape
            (2, 2)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_dof_positions()  # shape: (N, max_dofs)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
        return data[indices, dof_indices].contiguous().to(self._device)

    def get_dof_position_targets(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the position targets of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            DOF position targets (shape ``(N, D)``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the DOF position targets of all prims
            >>> position_targets = prims.get_dof_position_targets()
            >>> position_targets.shape
            (3, 9)
            >>>
            >>> # get the DOF position targets of the first and last prims' finger DOFs
            >>> position_targets = prims.get_dof_position_targets(indices=[0, 2], dof_indices=[7, 8])
            >>> position_targets.shape
            (2, 2)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_dof_position_targets()  # shape: (N, max_dofs)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            return data[indices, dof_indices].contiguous().to(self._device)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            data = np.zeros((indices.shape[0], dof_indices.shape[0]), dtype=np.float32)
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    drive_api, drive_type = self._get_drive_api_and_type(index, dof_index)
                    position = drive_api.GetTargetPositionAttr().Get()
                    if drive_type == "angular":
                        position = np.deg2rad(position)
                    data[i][j] = position
            return _ops.place(data, device=self._device)

    def get_dof_velocities(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the velocities of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            DOF velocities (shape ``(N, D)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # get the DOF velocities of all prims
            >>> velocities = prims.get_dof_velocities()
            >>> velocities.shape
            (3, 9)
            >>>
            >>> # get the DOF velocity of the first and last prims' finger DOFs
            >>> velocities = prims.get_dof_velocities(indices=[0, 2], dof_indices=[7, 8])
            >>> velocities.shape
            (2, 2)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_dof_velocities()  # shape: (N, max_dofs)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
        return data[indices, dof_indices].contiguous().to(self._device)

    def get_dof_velocity_targets(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the velocity targets of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            DOF velocity targets (shape ``(N, D)``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the DOF velocity targets of all prims
            >>> velocity_targets = prims.get_dof_velocity_targets()
            >>> velocity_targets.shape
            (3, 9)
            >>>
            >>> # get the DOF velocity target of the first and last prims' finger DOFs
            >>> velocity_targets = prims.get_dof_velocity_targets(indices=[0, 2], dof_indices=[7, 8])
            >>> velocity_targets.shape
            (2, 2)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_dof_velocity_targets()  # shape: (N, max_dofs)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            return data[indices, dof_indices].contiguous().to(self._device)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            data = np.zeros((indices.shape[0], dof_indices.shape[0]), dtype=np.float32)
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    drive_api, drive_type = self._get_drive_api_and_type(index, dof_index)
                    velocity = drive_api.GetTargetVelocityAttr().Get()
                    if drive_type == "angular":
                        velocity = np.deg2rad(velocity)
                    data[i][j] = velocity
            return _ops.place(data, device=self._device)

    def set_world_poses(
        self,
        positions: list | np.ndarray | wp.array | None = None,
        orientations: list | np.ndarray | wp.array | None = None,
        *,
        indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the root poses (positions and orientations) in the world frame of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`, :guilabel:`usdrt`, :guilabel:`fabric`.

        .. note::

            This method *teleports* prims to the specified poses.

        Args:
            positions: Root positions in the world frame (shape ``(N, 3)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            orientations: Root orientations in the world frame (shape ``(N, 4)``, quaternion ``wxyz``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Raises:
            AssertionError: If neither positions nor orientations are specified.
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set poses (fixed positions and random orientations) for all prims
            >>> positions = [[0, y, 0] for y in range(3)]
            >>> orientations = np.random.randn(3, 4)
            >>> orientations = orientations / np.linalg.norm(orientations, axis=-1, keepdims=True)  # normalize quaternions
            >>> prims.set_world_poses(positions, orientations)
        """
        assert (
            positions is not None or orientations is not None
        ), "Both 'positions' and 'orientations' are not defined. Define at least one of them"
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd", "usdrt", "fabric"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_root_transforms()  # shape: (N, 7)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            if positions is not None:
                positions = _ops.broadcast_to(
                    positions, shape=(indices.shape[0], 3), dtype=wp.float32, device=data.device
                )
                wp.copy(data[indices, :3], positions)
            if orientations is not None:
                orientations = _ops.broadcast_to(
                    orientations, shape=(indices.shape[0], 4), dtype=wp.float32, device=data.device
                )
                wp.copy(data[indices, wp.array([6, 3, 4, 5], dtype=wp.int32, device=data.device)], orientations)
            self._physics_articulation_view.set_root_transforms(data, indices)
        # USD/USDRT/Fabric API
        else:
            super().set_world_poses(positions=positions, orientations=orientations, indices=indices)

    def get_world_poses(self, *, indices: list | np.ndarray | wp.array | None = None) -> tuple[wp.array, wp.array]:
        """Get the root poses (positions and orientations) in the world frame of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`, :guilabel:`usdrt`, :guilabel:`fabric`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            Two-elements tuple. 1) The root positions in the world frame (shape ``(N, 3)``).
            2) The root orientations in the world frame (shape ``(N, 4)``, quaternion ``wxyz``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the world poses of all prims
            >>> positions, orientations = prims.get_world_poses()
            >>> positions.shape, orientations.shape
            ((3, 3), (3, 4))
            >>>
            >>> # get the world pose of the first prim
            >>> positions, orientations = prims.get_world_poses(indices=[0])
            >>> positions.shape, orientations.shape
            ((1, 3), (1, 4))
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd", "usdrt", "fabric"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_root_transforms()  # shape: (N, 7), quaternion is xyzw
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            return (
                data[indices, :3].contiguous().to(self._device),
                data[indices, wp.array([6, 3, 4, 5], dtype=wp.int32, device=data.device)].contiguous().to(self._device),
            )
        # USD/USDRT/Fabric API
        else:
            return super().get_world_poses(indices=indices)

    def get_local_poses(self, *, indices: list | np.ndarray | wp.array | None = None) -> tuple[wp.array, wp.array]:
        """Get the root poses (translations and orientations) in the local frame of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`, :guilabel:`usdrt`, :guilabel:`fabric`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            Two-elements tuple. 1) The root translations in the local frame (shape ``(N, 3)``).
            2) The root orientations in the local frame (shape ``(N, 4)``, quaternion ``wxyz``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the local poses of all prims
            >>> translations, orientations = prims.get_local_poses()
            >>> translations.shape, orientations.shape
            ((3, 3), (3, 4))
            >>>
            >>> # get the local pose of the first prim
            >>> translations, orientations = prims.get_local_poses(indices=[0])
            >>> translations.shape, orientations.shape
            ((1, 3), (1, 4))
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd", "usdrt", "fabric"]))
        # Tensor API
        if backend == "tensor":
            indices = _ops.resolve_indices(indices, count=len(self), device=self._device)
            world_positions, world_orientations = self.get_world_poses(indices=indices)
            parent_transforms = np.zeros(shape=(indices.shape[0], 4, 4), dtype=np.float32)
            for i, index in enumerate(indices.numpy()):
                parent_transforms[i] = np.array(
                    UsdGeom.Xformable(get_prim_parent(self.prims[index])).ComputeLocalToWorldTransform(
                        Usd.TimeCode.Default()
                    ),
                    dtype=np.float32,
                )
            local_translations, local_orientations = numpy_utils.transformations.get_local_from_world(
                parent_transforms, world_positions.numpy(), world_orientations.numpy()
            )
            return (
                _ops.place(local_translations, device=self._device),
                _ops.place(local_orientations, device=self._device),
            )
        # USD/USDRT/Fabric API
        else:
            return super().get_local_poses(indices=indices)

    def set_local_poses(
        self,
        translations: list | np.ndarray | wp.array | None = None,
        orientations: list | np.ndarray | wp.array | None = None,
        *,
        indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the root poses (translations and orientations) in the local frame of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`, :guilabel:`usdrt`, :guilabel:`fabric`.

        .. note::

            This method *teleports* prims to the specified poses.

        Args:
            translations: Root translations in the local frame (shape ``(N, 3)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            orientations: Root orientations in the local frame (shape ``(N, 4)``, quaternion ``wxyz``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Raises:
            AssertionError: If neither translations nor orientations are specified.
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set poses (fixed translations and random orientations) for all prims
            >>> translations = [[0, y, 0] for y in range(3)]
            >>> orientations = np.random.randn(3, 4)
            >>> orientations = orientations / np.linalg.norm(orientations, axis=-1, keepdims=True)  # normalize quaternions
            >>> prims.set_local_poses(translations, orientations)
        """
        assert (
            translations is not None or orientations is not None
        ), "Both 'translations' and 'orientations' are not defined. Define at least one of them"
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd", "usdrt", "fabric"]))
        # Tensor API
        if backend == "tensor":
            indices = _ops.resolve_indices(indices, count=len(self), device=self._device)
            if translations is None or orientations is None:
                current_translations, current_orientations = self.get_local_poses(indices=indices)
                translations = current_translations if translations is None else translations
                orientations = current_orientations if orientations is None else orientations
            translations = _ops.broadcast_to(
                translations, shape=(indices.shape[0], 3), dtype=wp.float32, device=self._device
            )
            orientations = _ops.broadcast_to(
                orientations, shape=(indices.shape[0], 4), dtype=wp.float32, device=self._device
            )
            # compute transforms
            parent_transforms = np.zeros(shape=(indices.shape[0], 4, 4), dtype=np.float32)
            for i, index in enumerate(indices.numpy()):
                parent_transforms[i] = np.array(
                    UsdGeom.Xformable(get_prim_parent(self.prims[index])).ComputeLocalToWorldTransform(
                        Usd.TimeCode.Default()
                    ),
                    dtype=np.float32,
                )
            world_positions, world_orientations = numpy_utils.transformations.get_world_from_local(
                parent_transforms, translations.numpy(), orientations.numpy()
            )
            self.set_world_poses(positions=world_positions, orientations=world_orientations, indices=indices)
        # USD/USDRT/Fabric API
        else:
            super().set_local_poses(translations=translations, orientations=orientations, indices=indices)

    def set_velocities(
        self,
        linear_velocities: list | np.ndarray | wp.array | None = None,
        angular_velocities: list | np.ndarray | wp.array | None = None,
        *,
        indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the root velocities (linear and angular) of the prims.

        Backends: :guilabel:`tensor`.

        Args:
            linear_velocities: Root linear velocities (shape ``(N, 3)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            angular_velocities: Root angular velocities (shape ``(N, 3)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Raises:
            AssertionError: If neither linear_velocities nor angular_velocities are specified.
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # set random velocities for all prims
            >>> linear_velocities = np.random.uniform(low=-1, high=1, size=(3, 3))
            >>> angular_velocities = np.random.uniform(low=-1, high=1, size=(3, 3))
            >>> prims.set_velocities(linear_velocities, angular_velocities)
        """
        assert (
            linear_velocities is not None or angular_velocities is not None
        ), "Both 'linear_velocities' and 'angular_velocities' are not defined. Define at least one of them"
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_root_velocities()  # shape: (N, 6)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        if linear_velocities is not None:
            linear_velocities = _ops.broadcast_to(
                linear_velocities, shape=(indices.shape[0], 3), dtype=wp.float32, device=data.device
            )
            wp.copy(data[indices, :3], linear_velocities)
        if angular_velocities is not None:
            angular_velocities = _ops.broadcast_to(
                angular_velocities, shape=(indices.shape[0], 3), dtype=wp.float32, device=data.device
            )
            wp.copy(data[indices, 3:], angular_velocities)
        self._physics_articulation_view.set_root_velocities(data, indices)

    def get_velocities(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
    ) -> tuple[wp.array, wp.array]:
        """Get the root velocities (linear and angular) of the prims.

        Backends: :guilabel:`tensor`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            Two-elements tuple. 1) The root linear velocities (shape ``(N, 3)``).
            2) The root angular velocities (shape ``(N, 3)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # get the velocities of all prims
            >>> linear_velocities, angular_velocities = prims.get_velocities()
            >>> linear_velocities.shape, angular_velocities.shape
            ((3, 3), (3, 3))
            >>>
            >>> # get the velocities of the first prim
            >>> linear_velocities, angular_velocities = prims.get_velocities(indices=[0])
            >>> linear_velocities.shape, angular_velocities.shape
            ((1, 3), (1, 3))
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_root_velocities()  # shape: (N, 6)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        return data[indices, :3].contiguous().to(self._device), data[indices, 3:].contiguous().to(self._device)

    def get_solver_residual_reports(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        report_maximum: bool = True,
    ) -> tuple[wp.array, wp.array]:
        """Get the physics solver residuals (position and velocity) of the prims.

        Backends: :guilabel:`usd`.

        The solver residual quantifies the convergence of the iterative physics solver.
        A perfectly converged solution has a residual value of zero.
        For articulations, the solver residual is computed across all joints that are part of the articulations.

        Search for *Solver Residual* in |physx_docs| for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            report_maximum: Whether to report the maximum (true) or the root mean square (false) residual.

        Returns:
            Two-elements tuple. 1) The solver residuals for position (shape ``(N, 1)``).
            2) The solver residuals for velocity (shape ``(N, 1)``).

        Raises:
            AssertionError: Residual reporting is not enabled.
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the solver residuals of all prims
            >>> position_residuals, velocity_residuals = prims.get_solver_residual_reports()
            >>> position_residuals.shape, velocity_residuals.shape
            ((3, 1), (3, 1))
            >>>
            >>> # get the solver residuals of the first and last prims
            >>> position_residuals, velocity_residuals = prims.get_solver_residual_reports(indices=[0, 2])
            >>> position_residuals.shape, velocity_residuals.shape
            ((2, 1), (2, 1))
        """
        assert (
            self._enable_residual_reports
        ), "Enable residual reporting in Articulation class constructor to use residuals API"
        assert self.valid, _MSG_PRIM_NOT_VALID
        # USD API
        indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
        position_residuals = np.zeros(shape=(indices.shape[0], 1), dtype=np.float32)
        velocity_residuals = np.zeros(shape=(indices.shape[0], 1), dtype=np.float32)
        for i, index in enumerate(indices.numpy()):
            residual_api = Articulation.ensure_api([self.prims[index]], PhysxSchema.PhysxResidualReportingAPI)[0]
            if report_maximum:
                position_residuals[i] = residual_api.GetPhysxResidualReportingMaxResidualPositionIterationAttr().Get()
                velocity_residuals[i] = residual_api.GetPhysxResidualReportingMaxResidualVelocityIterationAttr().Get()
            else:
                position_residuals[i] = residual_api.GetPhysxResidualReportingRmsResidualPositionIterationAttr().Get()
                velocity_residuals[i] = residual_api.GetPhysxResidualReportingRmsResidualVelocityIterationAttr().Get()
        return _ops.place(position_residuals, device=self._device), _ops.place(velocity_residuals, device=self._device)

    def set_default_state(
        self,
        positions: list | np.ndarray | wp.array | None = None,
        orientations: list | np.ndarray | wp.array | None = None,
        linear_velocities: list | np.ndarray | wp.array | None = None,
        angular_velocities: list | np.ndarray | wp.array | None = None,
        dof_positions: list | np.ndarray | wp.array | None = None,
        dof_velocities: list | np.ndarray | wp.array | None = None,
        dof_efforts: list | np.ndarray | wp.array | None = None,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the default state (root positions, orientations, linear velocities and angular velocities,
        and DOF positions, velocities and efforts) of the prims.

        Backends: :guilabel:`usd`.

        .. hint::

            Prims can be reset to their default state by calling the :py:meth:`reset_to_default_state` method.

        Args:
            positions: Default root positions in the world frame (shape ``(N, 3)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            orientations: Default root orientations in the world frame (shape ``(N, 4)``, quaternion ``wxyz``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            linear_velocities: Default root linear velocities (shape ``(N, 3)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            angular_velocities: Default root angular velocities (shape ``(N, 3)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            dof_positions: Default DOF positions (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            dof_velocities: Default DOF velocities (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            dof_efforts: Default DOF efforts (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        indices = _ops.resolve_indices(indices, count=len(self), device=self._device)
        dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=self._device)
        # update default values
        # - positions and orientations
        if positions is not None or orientations is not None:
            super().set_default_state(positions=positions, orientations=orientations, indices=indices)
        # - linear velocities
        if linear_velocities is not None:
            if self._default_linear_velocities is None:
                self._default_linear_velocities = wp.zeros((len(self), 3), dtype=wp.float32, device=self._device)
            linear_velocities = _ops.broadcast_to(
                linear_velocities, shape=(indices.shape[0], 3), dtype=wp.float32, device=self._device
            )
            wp.copy(self._default_linear_velocities[indices], linear_velocities)
        # - angular velocities
        if angular_velocities is not None:
            if self._default_angular_velocities is None:
                self._default_angular_velocities = wp.zeros((len(self), 3), dtype=wp.float32, device=self._device)
            angular_velocities = _ops.broadcast_to(
                angular_velocities, shape=(indices.shape[0], 3), dtype=wp.float32, device=self._device
            )
            wp.copy(self._default_angular_velocities[indices], angular_velocities)
        # - dof positions
        if dof_positions is not None:
            if self._default_dof_positions is None:
                self._default_dof_positions = wp.zeros(
                    (len(self), self.num_dofs), dtype=wp.float32, device=self._device
                )
            dof_positions = _ops.broadcast_to(
                dof_positions, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=self._device
            )
            wp.copy(self._default_dof_positions[indices, dof_indices], dof_positions)
        # - dof velocities
        if dof_velocities is not None:
            if self._default_dof_velocities is None:
                self._default_dof_velocities = wp.zeros(
                    (len(self), self.num_dofs), dtype=wp.float32, device=self._device
                )
            dof_velocities = _ops.broadcast_to(
                dof_velocities, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=self._device
            )
            wp.copy(self._default_dof_velocities[indices, dof_indices], dof_velocities)
        # - dof efforts
        if dof_efforts is not None:
            if self._default_dof_efforts is None:
                self._default_dof_efforts = wp.zeros((len(self), self.num_dofs), dtype=wp.float32, device=self._device)
            dof_efforts = _ops.broadcast_to(
                dof_efforts, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=self._device
            )
            wp.copy(self._default_dof_efforts[indices, dof_indices], dof_efforts)

    def get_default_state(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> tuple[
        wp.array | None,
        wp.array | None,
        wp.array | None,
        wp.array | None,
        wp.array | None,
        wp.array | None,
        wp.array | None,
    ]:
        """Get the default state (root positions, orientations, linear velocities and angular velocities,
        and DOF positions, velocities and efforts) of the prims.

        Backends: :guilabel:`usd`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            Seven-elements tuple. 1) The default root positions in the world frame (shape ``(N, 3)``).
            2) The default root orientations in the world frame (shape ``(N, 4)``, quaternion ``wxyz``).
            3) The default root linear velocities (shape ``(N, 3)``). 4) The default root angular velocities (shape ``(N, 3)``).
            5) The default DOF positions (shape ``(N, D)``). 6) The default DOF velocities (shape ``(N, D)``).
            7) The default DOF efforts (shape ``(N, D)``).
            If the default state is not set using the :py:meth:`set_default_state` method, ``None`` is returned.

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not initialized.
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        indices = _ops.resolve_indices(indices, count=len(self), device=self._device)
        dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=self._device)
        # get default values
        # - positions and orientations
        default_positions, default_orientations = super().get_default_state(indices=indices)
        # - linear velocities
        default_linear_velocities = self._default_linear_velocities
        if default_linear_velocities is not None:
            default_linear_velocities = default_linear_velocities[indices].contiguous()
        # - angular velocities
        default_angular_velocities = self._default_angular_velocities
        if default_angular_velocities is not None:
            default_angular_velocities = default_angular_velocities[indices].contiguous()
        # - DOF positions
        default_dof_positions = self._default_dof_positions
        if default_dof_positions is not None:
            default_dof_positions = default_dof_positions[indices, dof_indices].contiguous()
        # - DOF velocities
        default_dof_velocities = self._default_dof_velocities
        if default_dof_velocities is not None:
            default_dof_velocities = default_dof_velocities[indices, dof_indices].contiguous()
        # - DOF efforts
        default_dof_efforts = self._default_dof_efforts
        if default_dof_efforts is not None:
            default_dof_efforts = default_dof_efforts[indices, dof_indices].contiguous()
        return (
            default_positions,
            default_orientations,
            default_linear_velocities,
            default_angular_velocities,
            default_dof_positions,
            default_dof_velocities,
            default_dof_efforts,
        )

    def reset_to_default_state(self) -> None:
        """Reset the prims to the specified default state.

        Backends: :guilabel:`tensor`.

        This method applies the default state defined using the :py:meth:`set_default_state` method.

        .. note::

            This method *teleports* prims to the specified default state (positions and orientations)
            and sets the linear and angular velocities and the DOF positions, velocities and efforts immediately.

        .. warning::

            This method has no effect when no default state is set. In this case, a warning message is logged.

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # get default state (no default state set at this point)
            >>> prims.get_default_state()
            (None, None, None, None, None, None, None)
            >>>
            >>> # set default state
            >>> # - random root positions for each prim
            >>> # - same fixed orientation for all prims
            >>> # - zero root velocities for all prims
            >>> # - random DOF positions for all DOFs
            >>> # - zero DOF velocities for all DOFs
            >>> # - zero DOF efforts for all DOFs
            >>> positions = np.random.uniform(low=-1, high=1, size=(3, 3))
            >>> prims.set_default_state(
            ...     positions=positions,
            ...     orientations=[1.0, 0.0, 0.0, 0.0],
            ...     linear_velocities=np.zeros(3),
            ...     angular_velocities=np.zeros(3),
            ...     dof_positions=np.random.uniform(low=-0.25, high=0.25, size=(3, 9)),
            ...     dof_velocities=np.zeros(9),
            ...     dof_efforts=np.zeros(9),
            ... )
            >>>
            >>> # get default state (default state is set)
            >>> prims.get_default_state()
            (<warp.types.array object at 0x...>,
             <warp.types.array object at 0x...>,
             <warp.types.array object at 0x...>,
             <warp.types.array object at 0x...>,
             <warp.types.array object at 0x...>,
             <warp.types.array object at 0x...>,
             <warp.types.array object at 0x...>)
            >>>
            >>> # reset prims to default state
            >>> prims.reset_to_default_state()
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        if self._non_root_articulation_link:
            carb.log_warn("The prim is a non-root link in an articulation. The default state will not be set")
            return
        if self._default_linear_velocities is None and self._default_angular_velocities is None:
            carb.log_error("The default state is not initialized. Call '.set_default_state(..)' first to initialize it")
            return
        if self._default_positions is not None or self._default_orientations is not None:
            self.set_world_poses(self._default_positions, self._default_orientations)
        else:
            carb.log_warn(
                "No default positions or orientations to reset. Call '.set_default_state(..)' first to initialize them"
            )
        if self._default_linear_velocities is not None or self._default_angular_velocities is not None:
            self.set_velocities(self._default_linear_velocities, self._default_angular_velocities)
        else:
            carb.log_warn(
                "No default linear or angular velocities to reset. Call '.set_default_state(..)' first to initialize them"
            )
        if self._default_dof_positions is not None:
            self.set_dof_positions(self._default_dof_positions)
            self.set_dof_position_targets(self._default_dof_positions)
        else:
            carb.log_warn("No default DOF positions to reset. Call '.set_default_state(..)' first to initialize them")
        if self._default_dof_velocities is not None:
            self.set_dof_velocities(self._default_dof_velocities)
            self.set_dof_velocity_targets(self._default_dof_velocities)
        else:
            carb.log_warn("No default DOF velocities to reset. Call '.set_default_state(..)' first to initialize them")
        if self._default_dof_efforts is not None:
            self.set_dof_efforts(self._default_dof_efforts)
        else:
            carb.log_warn("No default DOF efforts to reset. Call '.set_default_state(..)' first to initialize them")

    def get_dof_drive_types(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> list[list[str]]:
        """Get the drive types of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            The drive types. Possible values are ``acceleration`` or ``force`` (shape ``(N, D)``).
            If the drive type is not set, ``None`` is returned.
        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the drive types of the first prim
            >>> drive_types = prims.get_dof_drive_types(indices=[0])
            >>> print(drive_types)
            [['force', 'force', 'force', 'force', 'force', 'force', 'force', 'force', 'none']]
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_drive_types()  # shape: (N, max_dofs)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            data = data[indices, dof_indices].numpy()
            types = np.full_like(data, "none", dtype=object)
            types = np.where(data == 1, "force", types)
            types = np.where(data == 2, "acceleration", types)
            return types.tolist()
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            data = np.empty((indices.shape[0], dof_indices.shape[0]), dtype=object)
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    drive_api, _ = self._get_drive_api_and_type(index, dof_index)
                    data[i][j] = drive_api.GetTypeAttr().Get()
            return data.tolist()

    def set_dof_drive_types(
        self,
        types: str | list[list[str]],
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the drive types of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`usd`.

        Args:
            types: Drive types. Can be a single string or list of strings (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set the DOF drive types for all prims to 'acceleration'
            >>> # note that dof indices 8 is a mimic joint, it does not have a DOF drive
            >>> prims.set_dof_drive_types("acceleration", dof_indices=[0, 1, 2, 3, 4, 5, 6, 7])
            >>>
            >>> # set the drive types for the all prims' finger DOFs to 'force'
            >>> prims.set_dof_drive_types("force", dof_indices=[7])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        # USD API
        indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
        dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
        types = [types] if isinstance(types, str) else types
        types = np.broadcast_to(np.array(types, dtype=object), (indices.shape[0], dof_indices.shape[0]))
        for i, index in enumerate(indices.numpy()):
            for j, dof_index in enumerate(dof_indices.numpy()):
                drive_api, _ = self._get_drive_api_and_type(index, dof_index)
                drive_api.GetTypeAttr().Set(types[i][j])

    def set_dof_max_efforts(
        self,
        max_efforts: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the maximum forces applied by the drive of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            max_efforts: Maximum forces (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set the maximum DOF efforts for all prims to 1000
            >>> prims.set_dof_max_efforts([1000])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_dof_max_forces()  # shape: (N, max_dofs)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            max_efforts = _ops.broadcast_to(
                max_efforts, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=data.device
            )
            wp.copy(data[indices, dof_indices], max_efforts)
            self._physics_articulation_view.set_dof_max_forces(data, indices)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            max_efforts = _ops.broadcast_to(
                max_efforts,
                shape=(indices.shape[0], dof_indices.shape[0]),
                dtype=wp.float32,
                device=self._device,
            ).numpy()
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    drive_api, _ = self._get_drive_api_and_type(index, dof_index)
                    drive_api.GetMaxForceAttr().Set(float(max_efforts[i][j].item()))

    def get_dof_max_efforts(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the maximum forces applied by the drive of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            Maximum forces applied by the drive (shape ``(N, D)``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the DOF maximum efforts of all prims
            >>> max_efforts = prims.get_dof_max_efforts()
            >>> max_efforts.shape
            (3, 9)
            >>>
            >>> # get the DOF maximum efforts of the first and last prims' finger DOFs
            >>> max_efforts = prims.get_dof_max_efforts(indices=[0, 2], dof_indices=[7, 8])
            >>> max_efforts.shape
            (2, 2)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_dof_max_forces()  # shape: (N, max_dofs)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            return data[indices, dof_indices].contiguous().to(self._device)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            data = np.zeros((indices.shape[0], dof_indices.shape[0]), dtype=np.float32)
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    drive_api, _ = self._get_drive_api_and_type(index, dof_index)
                    data[i][j] = drive_api.GetMaxForceAttr().Get()
            return _ops.place(data, device=self._device)

    def set_dof_max_velocities(
        self,
        max_velocities: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the maximum velocities of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            max_velocities: Maximum velocities (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set the maximum DOF velocities for all prims to 100
            >>> prims.set_dof_max_velocities([100])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_dof_max_velocities()  # shape: (N, max_dofs)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            max_velocities = _ops.broadcast_to(
                max_velocities, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=data.device
            )
            wp.copy(data[indices, dof_indices], max_velocities)
            self._physics_articulation_view.set_dof_max_velocities(data, indices)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            max_velocities = _ops.broadcast_to(
                max_velocities,
                shape=(indices.shape[0], dof_indices.shape[0]),
                dtype=wp.float32,
                device=self._device,
            ).numpy()
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    dof_prim = get_prim_at_path(self.dof_paths[index][dof_index])
                    physx_joint_api = Articulation.ensure_api([dof_prim], PhysxSchema.PhysxJointAPI)[0]
                    max_velocity = max_velocities[i][j].item()
                    if self.dof_types[dof_index] == omni.physics.tensors.DofType.Rotation:
                        max_velocity = np.rad2deg(max_velocity)
                    physx_joint_api.GetMaxJointVelocityAttr().Set(max_velocity)

    def get_dof_max_velocities(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the maximum velocities of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            Maximum velocities (shape ``(N, D)``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the DOF maximum velocities of all prims
            >>> max_velocities = prims.get_dof_max_velocities()
            >>> max_velocities.shape
            (3, 9)
            >>>
            >>> # get the DOF maximum velocities of the first and last prims' finger DOFs
            >>> max_velocities = prims.get_dof_max_velocities(indices=[0, 2], dof_indices=[7, 8])
            >>> max_velocities.shape
            (2, 2)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_dof_max_velocities()  # shape: (N, max_dofs)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
            return data[indices, dof_indices].contiguous().to(self._device)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            data = np.zeros((indices.shape[0], dof_indices.shape[0]), dtype=np.float32)
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    dof_prim = get_prim_at_path(self.dof_paths[index][dof_index])
                    physx_joint_api = Articulation.ensure_api([dof_prim], PhysxSchema.PhysxJointAPI)[0]
                    max_velocity = physx_joint_api.GetMaxJointVelocityAttr().Get()
                    if self.dof_types[dof_index] == omni.physics.tensors.DofType.Rotation:
                        max_velocity = np.deg2rad(max_velocity)
                    data[i][j] = max_velocity
            return _ops.place(data, device=self._device)

    def set_dof_gains(
        self,
        stiffnesses: list | np.ndarray | wp.array | None = None,
        dampings: list | np.ndarray | wp.array | None = None,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
        update_default_gains: bool = True,
    ) -> None:
        """Set the implicit Proportional-Derivative (PD) controller's gains (stiffnesses and dampings)
        of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            stiffnesses: Stiffnesses (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            dampings: Dampings (shape ``(N, D)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.
            update_default_gains: Whether to update the default gains with the given values.

        Raises:
            AssertionError: If neither stiffnesses nor dampings are specified.
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set the DOF gains for all prims
            >>> stiffnesses = np.array([100000, 100000, 100000, 100000, 80000, 80000, 80000, 50000, 50000])
            >>> dampings = np.array([8000, 8000, 8000, 8000, 5000, 5000, 5000, 2000, 2000])
            >>> prims.set_dof_gains(stiffnesses, dampings)
        """
        assert (
            stiffnesses is not None or dampings is not None
        ), "Both 'stiffnesses' and 'dampings' are not defined. Define at least one of them"
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            view_stiffnesses = self._physics_articulation_view.get_dof_stiffnesses()  # shape: (N, max_dofs)
            view_dampings = self._physics_articulation_view.get_dof_dampings()  # shape: (N, max_dofs)
            device = view_stiffnesses.device
            indices = _ops.resolve_indices(indices, count=len(self), device=device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=device)
            if stiffnesses is not None:
                stiffnesses = _ops.broadcast_to(
                    stiffnesses, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=device
                )
                wp.copy(view_stiffnesses[indices, dof_indices], stiffnesses)
                self._physics_articulation_view.set_dof_stiffnesses(view_stiffnesses, indices)
            if dampings is not None:
                dampings = _ops.broadcast_to(
                    dampings, shape=(indices.shape[0], dof_indices.shape[0]), dtype=wp.float32, device=device
                )
                wp.copy(view_dampings[indices, dof_indices], dampings)
                self._physics_articulation_view.set_dof_dampings(view_dampings, indices)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            if stiffnesses is not None:
                stiffnesses = _ops.broadcast_to(
                    stiffnesses,
                    shape=(indices.shape[0], dof_indices.shape[0]),
                    dtype=wp.float32,
                    device=self._device,
                ).numpy()
            if dampings is not None:
                dampings = _ops.broadcast_to(
                    dampings,
                    shape=(indices.shape[0], dof_indices.shape[0]),
                    dtype=wp.float32,
                    device=self._device,
                ).numpy()
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    drive_api, drive_type = self._get_drive_api_and_type(index, dof_index)
                    if stiffnesses is not None:
                        stiffness = stiffnesses[i][j]
                        if drive_type == "angular" and stiffness:
                            stiffness = 1.0 / np.rad2deg(1.0 / stiffness)
                        drive_api.GetStiffnessAttr().Set(stiffness.item())
                    if dampings is not None:
                        damping = dampings[i][j]
                        if drive_type == "angular" and damping:
                            damping = 1.0 / np.rad2deg(1.0 / damping)
                        drive_api.GetDampingAttr().Set(damping.item())
        # update default gains (used to switch DOF control mode)
        if update_default_gains:
            self._default_dof_stiffnesses, self._default_dof_dampings = self.get_dof_gains()

    def get_dof_gains(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> tuple[wp.array, wp.array]:
        """Get the implicit Proportional-Derivative (PD) controller's gains (stiffnesses and dampings)
        of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            Two-elements tuple. 1) Stiffnesses (shape ``(N, D)``). 2) Dampings (shape ``(N, D)``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the DOF gains of all prims
            >>> stiffnesses, dampings = prims.get_dof_gains()
            >>> stiffnesses.shape, dampings.shape
            ((3, 9), (3, 9))
            >>>
            >>> # get the DOF gains of the first and last prims' finger DOFs
            >>> stiffnesses, dampings = prims.get_dof_gains(indices=[0, 2], dof_indices=[7, 8])
            >>> stiffnesses.shape, dampings.shape
            ((2, 2), (2, 2))
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            view_stiffnesses = self._physics_articulation_view.get_dof_stiffnesses()  # shape: (N, max_dofs)
            view_dampings = self._physics_articulation_view.get_dof_dampings()  # shape: (N, max_dofs)
            indices = _ops.resolve_indices(indices, count=len(self), device=view_stiffnesses.device)
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=view_stiffnesses.device)
            return (
                view_stiffnesses[indices, dof_indices].contiguous().to(self._device),
                view_dampings[indices, dof_indices].contiguous().to(self._device),
            )
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device="cpu")
            stiffnesses = np.zeros((indices.shape[0], dof_indices.shape[0]), dtype=np.float32)
            dampings = np.zeros((indices.shape[0], dof_indices.shape[0]), dtype=np.float32)
            for i, index in enumerate(indices.numpy()):
                for j, dof_index in enumerate(dof_indices.numpy()):
                    drive_api, drive_type = self._get_drive_api_and_type(index, dof_index)
                    stiffness = drive_api.GetStiffnessAttr().Get()
                    damping = drive_api.GetDampingAttr().Get()
                    if drive_type == "linear":
                        stiffnesses[i][j] = stiffness
                        dampings[i][j] = damping
                    else:
                        stiffnesses[i][j] = 1.0 / np.deg2rad(1.0 / stiffness) if stiffness else 0.0
                        dampings[i][j] = 1.0 / np.deg2rad(1.0 / damping) if damping else 0.0
            return _ops.place(stiffnesses, device=self._device), _ops.place(dampings, device=self._device)

    def switch_dof_control_mode(
        self,
        mode: str,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Switch the control mode (understood as the gain adjustment) of the degrees of freedom (DOFs) of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        This method sets the implicit Proportional-Derivative (PD) controller's gains (stiffnesses and dampings)
        according to the following rules:

        .. list-table::
            :header-rows: 1

            * - Control mode
              - Stiffnesses
              - Dampings
            * - ``"position"``
              - default stiffnesses
              - default dampings
            * - ``"velocity"``
              - 0.0
              - default dampings
            * - ``"effort"``
              - 0.0
              - 0.0

        Args:
            mode: Control mode. Supported modes are ``"position"``, ``"velocity"`` and ``"effort"``.
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.
            ValueError: Invalid control mode.

        Example:

        .. code-block:: python

            >>> # switch to 'velocity' control mode for all prims' arm DOFs (except for the fingers)
            >>> prims.switch_dof_control_mode("velocity", dof_indices=np.arange(7))
            >>>
            >>> # switch to 'effort' control mode for all prims' fingers (last 2 DOFs)
            >>> prims.switch_dof_control_mode("effort", dof_indices=[7, 8])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        # get default gains if not defined
        if self._default_dof_stiffnesses is None or self._default_dof_dampings is None:
            stiffnesses, dampings = self.get_dof_gains()
            if self._default_dof_stiffnesses is None:
                self._default_dof_stiffnesses = stiffnesses
            if self._default_dof_dampings is None:
                self._default_dof_dampings = dampings
        # switch control mode
        indices = _ops.resolve_indices(indices, count=len(self), device=self._device)
        dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=self._device)
        if mode == "position":
            stiffnesses = self._default_dof_stiffnesses[indices, dof_indices].contiguous()
            dampings = self._default_dof_dampings[indices, dof_indices].contiguous()
        elif mode == "velocity":
            stiffnesses = [0.0]
            dampings = self._default_dof_dampings[indices, dof_indices].contiguous()
        elif mode == "effort":
            stiffnesses, dampings = [0.0], [0.0]
        else:
            raise ValueError(f"Invalid control mode: {mode}. Supported modes are: 'position', 'velocity', 'effort'")
        self.set_dof_gains(
            stiffnesses,
            dampings,
            indices=indices,
            dof_indices=dof_indices,
            update_default_gains=False,
        )

    def set_solver_iteration_counts(
        self,
        position_counts: list | np.ndarray | wp.array | None = None,
        velocity_counts: list | np.ndarray | wp.array | None = None,
        *,
        indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the physics solver iteration counts (position and velocity) of the prims.

        Backends: :guilabel:`usd`.

        The solver iteration count determines how accurately contacts, drives, and limits are resolved.
        Search for *Solver Iteration Count* in |physx_docs| for more details.

        .. warning::

            The more iterations, the more accurate the results, at the cost of decreasing simulation performance.

        Args:
            position_counts: Number of iterations for the position solver (shape ``(N, 1)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            velocity_counts: Number of iterations for the velocity solver (shape ``(N, 1)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Raises:
            AssertionError: Neither ``position_counts`` nor ``velocity_counts`` are defined.
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set the solver iteration counts (position: 16, velocity: 4) for all prims
            >>> prims.set_solver_iteration_counts([16], [4])
        """
        assert (
            position_counts is not None or velocity_counts is not None
        ), "Both 'position_counts' and 'velocity_counts' are not defined. Define at least one of them"
        assert self.valid, _MSG_PRIM_NOT_VALID
        # USD API
        indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
        if position_counts is not None:
            position_counts = _ops.place(position_counts, device="cpu").numpy().reshape((-1, 1))
        if velocity_counts is not None:
            velocity_counts = _ops.place(velocity_counts, device="cpu").numpy().reshape((-1, 1))
        for i, index in enumerate(indices.numpy()):
            prim = self.prims[index]
            if position_counts is not None:
                prim.GetAttribute("physxArticulation:solverPositionIterationCount").Set(
                    int(position_counts[0 if position_counts.shape[0] == 1 else i].item())
                )
            if velocity_counts is not None:
                prim.GetAttribute("physxArticulation:solverVelocityIterationCount").Set(
                    int(velocity_counts[0 if velocity_counts.shape[0] == 1 else i].item())
                )

    def get_solver_iteration_counts(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
    ) -> tuple[wp.array, wp.array]:
        """Get the physics solver iteration counts (position and velocity) of the prims.

        Backends: :guilabel:`usd`.

        The solver iteration count determines how accurately contacts, drives, and limits are resolved.
        Search for *Solver Iteration Count* in |physx_docs| for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            Two-element tuple: 1) Position iteration counts (shape ``(N, 1)``).
            2) Velocity iteration counts (shape ``(N, 1)``).

        Example:

        .. code-block:: python

            >>> # get the solver iteration counts of all prims
            >>> position_counts, velocity_counts = prims.get_solver_iteration_counts()
            >>> position_counts.shape, velocity_counts.shape
            ((3, 1), (3, 1))
            >>>
            >>> # get the solver iteration counts of the first and last prims
            >>> position_counts, velocity_counts = prims.get_solver_iteration_counts(indices=[0, 2])
            >>> position_counts.shape, velocity_counts.shape
            ((2, 1), (2, 1))
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        # USD API
        indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
        position_counts = np.zeros(shape=(indices.shape[0], 1), dtype=np.int32)
        velocity_counts = np.zeros(shape=(indices.shape[0], 1), dtype=np.int32)
        for i, index in enumerate(indices.numpy()):
            prim = self.prims[index]
            position_counts[i] = prim.GetAttribute("physxArticulation:solverPositionIterationCount").Get()
            velocity_counts[i] = prim.GetAttribute("physxArticulation:solverVelocityIterationCount").Get()
        return _ops.place(position_counts, device=self._device), _ops.place(velocity_counts, device=self._device)

    def set_stabilization_thresholds(
        self,
        thresholds: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the mass-normalized kinetic energy below which the prims may participate in stabilization.

        Backends: :guilabel:`usd`.

        Search for *Stabilization Threshold* in |physx_docs| for more details.

        Args:
            thresholds: Stabilization thresholds to be applied (shape ``(N, 1)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set the stabilization thresholds for all prims
            >>> prims.set_stabilization_thresholds([1e-5])
            >>>
            >>> # set the stabilization thresholds for the first and last prims
            >>> prims.set_stabilization_thresholds([1.5e-5], indices=[0, 2])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        # USD API
        indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
        thresholds = _ops.place(thresholds, device="cpu").numpy().reshape((-1, 1))
        for i, index in enumerate(indices.numpy()):
            self.prims[index].GetAttribute("physxArticulation:stabilizationThreshold").Set(
                float(thresholds[0 if thresholds.shape[0] == 1 else i].item())
            )

    def get_stabilization_thresholds(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the mass-normalized kinetic energy below which the prims may participate in stabilization.

        Backends: :guilabel:`usd`.

        Search for *Stabilization Threshold* in |physx_docs| for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            Stabilization thresholds (shape ``(N, 1)``).

        Example:

        .. code-block:: python

            >>> # get the stabilization thresholds of all prims
            >>> thresholds = prims.get_stabilization_thresholds()
            >>> thresholds.shape
            (3, 1)
            >>>
            >>> # get the stabilization threshold of the first and last prims
            >>> thresholds = prims.get_stabilization_thresholds(indices=[0, 2])
            >>> thresholds.shape
            (2, 1)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        # USD API
        indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
        data = np.zeros((indices.shape[0], 1), dtype=np.float32)
        for i, index in enumerate(indices.numpy()):
            data[i] = self.prims[index].GetAttribute("physxArticulation:stabilizationThreshold").Get()
        return _ops.place(data, device=self._device)

    def set_enabled_self_collisions(
        self,
        enabled: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Enable or disable the self-collisions processing of the prims.

        Backends: :guilabel:`usd`.

        Args:
            enabled: Boolean flags to enable/disable self-collisions (shape ``(N, 1)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # disable the self-collisions for all prims
            >>> prims.set_enabled_self_collisions([False])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        # USD API
        indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
        enabled = _ops.place(enabled, device="cpu").numpy().reshape((-1, 1))
        for i, index in enumerate(indices.numpy()):
            self.prims[index].GetAttribute("physxArticulation:enabledSelfCollisions").Set(
                bool(enabled[0 if enabled.shape[0] == 1 else i].item())
            )

    def get_enabled_self_collisions(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the enable state of the self-collisions processing of the prims.

        Backends: :guilabel:`usd`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            Boolean flags indicating if the self-collisions processing is enabled (shape ``(N, 1)``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the self-collisions enabled state of all prims
            >>> print(prims.get_enabled_self_collisions())
            [[False]
             [False]
             [False]]
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        # USD API
        indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
        data = np.zeros((indices.shape[0], 1), dtype=np.bool_)
        for i, index in enumerate(indices.numpy()):
            data[i] = self.prims[index].GetAttribute("physxArticulation:enabledSelfCollisions").Get()
        return _ops.place(data, device=self._device)

    def set_sleep_thresholds(
        self,
        thresholds: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the sleep thresholds of the prims.

        Backends: :guilabel:`usd`.

        Search for *Articulations and Sleeping* in |physx_docs| for more details.

        Args:
            thresholds: Sleep thresholds (shape ``(N, 1)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set the sleep thresholds for all prims
            >>> prims.set_sleep_thresholds([1e-5])
            >>>
            >>> # set the sleep thresholds for the first and last prims
            >>> prims.set_sleep_thresholds([1.5e-5], indices=[0, 2])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        # USD API
        indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
        thresholds = _ops.place(thresholds, device="cpu").numpy().reshape((-1, 1))
        for i, index in enumerate(indices.numpy()):
            self.prims[index].GetAttribute("physxArticulation:sleepThreshold").Set(
                float(thresholds[0 if thresholds.shape[0] == 1 else i].item())
            )

    def get_sleep_thresholds(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the sleep thresholds of the prims.

        Backends: :guilabel:`usd`.

        Search for *Articulations and Sleeping* in |physx_docs| for more details

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            The sleep thresholds (shape ``(N, 1)``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the sleep thresholds of all prims
            >>> thresholds = prims.get_sleep_thresholds()
            >>> thresholds.shape
            (3, 1)
            >>>
            >>> # get the sleep threshold of the first and last prims
            >>> thresholds = prims.get_sleep_thresholds(indices=[0, 2])
            >>> thresholds.shape
            (2, 1)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        # USD API
        indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
        data = np.zeros((indices.shape[0], 1), dtype=np.float32)
        for i, index in enumerate(indices.numpy()):
            data[i] = self.prims[index].GetAttribute("physxArticulation:sleepThreshold").Get()
        return _ops.place(data, device=self._device)

    def get_jacobian_matrices(self, *, indices: list | np.ndarray | wp.array | None = None) -> wp.array:
        """Get the Jacobian matrices of the prims.

        Backends: :guilabel:`tensor`.

        .. note::

            The first dimension corresponds to the amount of wrapped prims while the last 3 dimensions are the
            Jacobian matrix shape. Refer to the :py:attr:`jacobian_matrix_shape` property for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            The Jacobian matrices of the prims (shape ``(N, *jacobian_matrix_shape)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # get the Jacobian matrices of all prims
            >>> jacobians = prims.get_jacobian_matrices()
            >>> jacobians.shape
            (3, 11, 6, 9)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_jacobians()
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        return data[indices].contiguous().to(self._device)

    def get_mass_matrices(self, *, indices: list | np.ndarray | wp.array | None = None) -> wp.array:
        """Get the mass matrices of the prims.

        Backends: :guilabel:`tensor`.

        .. note::

            The first dimension corresponds to the amount of wrapped prims while the last 2 dimensions are the
            mass matrix shape. Refer to the :py:attr:`mass_matrix_shape` property for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            The mass matrices of the prims (shape ``(N, *mass_matrix_shape)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # get the mass matrices of all prims
            >>> mass_matrices = prims.get_mass_matrices()
            >>> mass_matrices.shape
            (3, 9, 9)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_generalized_mass_matrices()
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        return data[indices].contiguous().to(self._device)

    def get_dof_coriolis_and_centrifugal_compensation_forces(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the Coriolis and centrifugal compensation forces (DOF forces required to counteract Coriolis and
        centrifugal forces for the given articulation state) of the prims

        Backends: :guilabel:`tensor`.

        Search for *Coriolis and Centrifugal Compensation Force* in |physx_docs| for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            The Coriolis and centrifugal compensation forces of the prims.
            For fixed articulation base shape is ``(N, D)``. For non-fixed (floating) articulation base shape
            is ``(N, D + 6)`` since the forces acting on the root are also provided.

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # get the coriolis and centrifugal compensation forces (fixed articulation base) of all prims
            >>> forces = prims.get_dof_coriolis_and_centrifugal_compensation_forces()
            >>> forces.shape
            (3, 9)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = (
            self._physics_articulation_view.get_coriolis_and_centrifugal_compensation_forces()
        )  # shape: (N, max_dofs) or (N, max_dofs + 6)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
        return data[indices, dof_indices].contiguous().to(self._device)

    def get_dof_gravity_compensation_forces(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        dof_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the gravity compensation forces (DOF forces required to counteract gravitational
        forces for the given articulation pose) of the prims

        Backends: :guilabel:`tensor`.

        Search for *Gravity Compensation Force* in |physx_docs| for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            dof_indices: Indices of DOFs to process (shape ``(D,)``). If not defined, all DOFs are processed.

        Returns:
            The gravity compensation forces of the prims.
            For fixed articulation base shape is ``(N, D)``. For non-fixed (floating) articulation base shape
            is ``(N, D + 6)`` since the forces acting on the root are also provided.

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # get the gravity compensation forces of all prims
            >>> forces = prims.get_dof_gravity_compensation_forces()
            >>> forces.shape
            (3, 9)
            >>>
            >>> # get the gravity compensation forces of the first and last prims' finger DOFs
            >>> forces = prims.get_dof_gravity_compensation_forces(indices=[0, 2], dof_indices=[7, 8])
            >>> forces.shape
            (2, 2)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = (
            self._physics_articulation_view.get_gravity_compensation_forces()
        )  # shape: (N, max_dofs) or (N, max_dofs + 6)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        dof_indices = _ops.resolve_indices(dof_indices, count=self.num_dofs, device=data.device)
        return data[indices, dof_indices].contiguous().to(self._device)

    def get_link_masses(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        link_indices: list | np.ndarray | wp.array | None = None,
        inverse: bool = False,
    ) -> wp.array:
        """Get the masses of the links of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            link_indices: Indices of links to process (shape ``(L,)``). If not defined, all links are processed.
            inverse: Whether to return inverse masses (true) or masses (false).

        Returns:
            The link masses (shape ``(N, L)``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the masses of the links of all prims
            >>> masses = prims.get_link_masses()
            >>> masses.shape
            (3, 12)
            >>>
            >>> # get the inverse masses of the first and last prims' finger links
            >>> inverse_masses = prims.get_link_masses(indices=[0, 2], link_indices=[10, 11], inverse=True)
            >>> inverse_masses.shape
            (2, 2)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            if inverse:
                data = self._physics_articulation_view.get_inv_masses()  # shape: (N, max_links)
            else:
                data = self._physics_articulation_view.get_masses()  # shape: (N, max_links)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            link_indices = _ops.resolve_indices(link_indices, count=self.num_links, device=data.device)
            return data[indices, link_indices].contiguous().to(self._device)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            link_indices = _ops.resolve_indices(link_indices, count=self.num_links, device="cpu")
            data = np.zeros((indices.shape[0], link_indices.shape[0]), dtype=np.float32)
            for i, index in enumerate(indices.numpy()):
                for j, link_index in enumerate(link_indices.numpy()):
                    link_prim = get_prim_at_path(self.link_paths[index][link_index])
                    mass_api = Articulation.ensure_api([link_prim], UsdPhysics.MassAPI)[0]
                    data[i][j] = mass_api.GetMassAttr().Get()
            if inverse:
                data = 1.0 / (data + 1e-8)
            return _ops.place(data, device=self._device)

    def get_link_coms(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        link_indices: list | np.ndarray | wp.array | None = None,
    ) -> tuple[wp.array, wp.array]:
        """Get the center of mass (COM) pose (position and orientation) of the links of the prims.

        Backends: :guilabel:`tensor`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            link_indices: Indices of links to process (shape ``(L,)``). If not defined, all links are processed.

        Returns:
            Two-elements tuple. 1) The center of mass positions (shape ``(N, L, 3)``).
            2) The center of mass orientations (shape ``(N, L, 4)``, quaternion ``wxyz``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # get the COM poses of the links of all prims
            >>> positions, orientations = prims.get_link_coms()
            >>> positions.shape, orientations.shape
            ((3, 12, 3), (3, 12, 4))
            >>>
            >>> # get the COM poses of the first and last prims' finger links
            >>> positions, orientations = prims.get_link_coms(indices=[0, 2], link_indices=[10, 11])
            >>> positions.shape, orientations.shape
            ((2, 2, 3), (2, 2, 4))
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_coms()  # shape: (N, max_links, 7), quaternion is xyzw
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        link_indices = _ops.resolve_indices(link_indices, count=self.num_links, device=data.device)
        return (
            data[indices, link_indices, :3].contiguous().to(self._device),
            data[indices, link_indices, wp.array([6, 3, 4, 5], dtype=wp.int32, device=data.device)]
            .contiguous()
            .to(self._device),
        )

    def get_link_inertias(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        link_indices: list | np.ndarray | wp.array | None = None,
        inverse: bool = False,
    ) -> wp.array:
        """Get the inertias tensors of the links of the prims.

        Backends: :guilabel:`tensor`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            link_indices: Indices of links to process (shape ``(L,)``). If not defined, all links are processed.
            inverse: Whether to return inverse inertia tensors (true) or inertia tensors (false).

        Returns:
            The inertia tensors or inverse inertia tensors (shape ``(N, L, 9)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # get the inertia tensors of the links of all prims
            >>> inertias = prims.get_link_inertias()
            >>> inertias.shape
            (3, 12, 9)
            >>>
            >>> # get the inverse inertia tensors of the first and last prims' finger links
            >>> inertias = prims.get_link_inertias(indices=[0, 2], link_indices=[10, 11], inverse=True)
            >>> inertias.shape
            (2, 2, 9)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        if inverse:
            data = self._physics_articulation_view.get_inv_inertias()  # shape: (N, max_links, 9)
        else:
            data = self._physics_articulation_view.get_inertias()  # shape: (N, max_links, 9)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        link_indices = _ops.resolve_indices(link_indices, count=self.num_links, device=data.device)
        return data[indices, link_indices].contiguous().to(self._device)

    def get_link_enabled_gravities(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        link_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the enabled state of the gravity on the links of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            link_indices: Indices of links to process (shape ``(L,)``). If not defined, all links are processed.

        Returns:
            Boolean flags indicating if the gravity is enabled on the links (shape ``(N, L)``).

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # get the gravity enabled state of the links of all prims
            >>> enabled = prims.get_link_enabled_gravities()
            >>> enabled.shape
            (3, 12)
            >>>
            >>> # get the gravity enabled state of the first and last prims' finger links
            >>> enabled = prims.get_link_enabled_gravities(indices=[0, 2], link_indices=[10, 11])
            >>> enabled.shape
            (2, 2)
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_disable_gravities()  # shape: (N, max_links)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            link_indices = _ops.resolve_indices(link_indices, count=self.num_links, device=data.device)
            enabled = np.logical_not(data[indices, link_indices].contiguous().numpy()).astype(np.bool_)  # negate values
            return _ops.place(enabled, device=self._device)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            link_indices = _ops.resolve_indices(link_indices, count=self.num_links, device="cpu")
            data = np.zeros((indices.shape[0], link_indices.shape[0]), dtype=np.bool_)
            for i, index in enumerate(indices.numpy()):
                for j, link_index in enumerate(link_indices.numpy()):
                    link_prim = get_prim_at_path(self.link_paths[index][link_index])
                    rigid_body_api = Articulation.ensure_api([link_prim], PhysxSchema.PhysxRigidBodyAPI)[0]
                    data[i][j] = not rigid_body_api.GetDisableGravityAttr().Get()
            return _ops.place(data, device=self._device)

    def set_link_masses(
        self,
        masses: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        link_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the masses of the links of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            masses: The link masses (shape ``(N, L)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            link_indices: Indices of links to process (shape ``(L,)``). If not defined, all links are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # set the masses of the links for all prims
            >>> prims.set_link_masses([10.0])
            >>>
            >>> # set the masses for the first and last prims' finger links
            >>> prims.set_link_masses([0.5], indices=[0, 2], link_indices=[10, 11])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_masses()  # shape: (N, max_links)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            link_indices = _ops.resolve_indices(link_indices, count=self.num_links, device=data.device)
            masses = _ops.broadcast_to(
                masses, shape=(indices.shape[0], link_indices.shape[0]), dtype=wp.float32, device=data.device
            )
            wp.copy(data[indices, link_indices], masses)
            self._physics_articulation_view.set_masses(data, indices)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            link_indices = _ops.resolve_indices(link_indices, count=self.num_links, device="cpu")
            masses = _ops.broadcast_to(
                masses,
                shape=(indices.shape[0], link_indices.shape[0]),
                dtype=wp.float32,
                device="cpu",
            ).numpy()
            for i, index in enumerate(indices.numpy()):
                for j, link_index in enumerate(link_indices.numpy()):
                    link_prim = get_prim_at_path(self.link_paths[index][link_index])
                    mass_api = Articulation.ensure_api([link_prim], UsdPhysics.MassAPI)[0]
                    mass_api.GetMassAttr().Set(float(masses[i][j].item()))

    def set_link_inertias(
        self,
        inertias: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        link_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the inertias of the links of the prims.

        Backends: :guilabel:`tensor`.

        Args:
            inertias: The link inertias (shape ``(N, L, 9)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            link_indices: Indices of links to process (shape ``(L,)``). If not defined, all links are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # set the inertia tensors of the links for all prims
            >>> inertias = np.diag([0.1, 0.1, 0.1]).flatten()  # shape: (9,)
            >>> prims.set_link_inertias(inertias)
            >>>
            >>> # set the inertia tensors for the first and last prims' finger links
            >>> inertias = np.diag([0.2, 0.2, 0.2]).flatten()  # shape: (9,)
            >>> prims.set_link_inertias(inertias, indices=[0, 2], link_indices=[10, 11])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_inertias()  # shape: (N, max_links, 9)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        link_indices = _ops.resolve_indices(link_indices, count=self.num_links, device=data.device)
        inertias = _ops.broadcast_to(
            inertias, shape=(indices.shape[0], link_indices.shape[0], 9), dtype=wp.float32, device=data.device
        )
        wp.copy(data[indices, link_indices], inertias)
        self._physics_articulation_view.set_inertias(data, indices)

    def set_link_coms(
        self,
        positions: list | np.ndarray | wp.array | None = None,
        orientations: list | np.ndarray | wp.array | None = None,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        link_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the center of mass (COM) pose (position and orientation) of the links of the prims.

        Backends: :guilabel:`tensor`.

        Args:
            positions: Center of mass positions (shape ``(N, L, 3)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            orientations: Center of mass orientations (shape ``(N, L, 4)``, quaternion ``wxyz``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            link_indices: Indices of links to process (shape ``(L,)``). If not defined, all links are processed.

        Raises:
            AssertionError: If neither positions nor orientations are specified.
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.

        Example:

        .. code-block:: python

            >>> # set random COM link positions for all prims
            >>> positions = np.random.uniform(low=-1, high=1, size=(3, 12, 3))
            >>> prims.set_link_coms(positions)
        """
        assert (
            positions is not None or orientations is not None
        ), "Both 'positions' and 'orientations' are not defined. Define at least one of them"
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_coms()  # shape: (N, max_links, 7)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        link_indices = _ops.resolve_indices(link_indices, count=self.num_links, device=data.device)
        if positions is not None:
            positions = _ops.broadcast_to(
                positions, shape=(indices.shape[0], link_indices.shape[0], 3), dtype=wp.float32, device=data.device
            )
            wp.copy(data[indices, link_indices, :3], positions)
        if orientations is not None:
            orientations = _ops.broadcast_to(
                orientations, shape=(indices.shape[0], link_indices.shape[0], 4), dtype=wp.float32, device=data.device
            )
            wp.copy(
                data[indices, link_indices, wp.array([6, 3, 4, 5], dtype=wp.int32, device=data.device)], orientations
            )
        self._physics_articulation_view.set_coms(data, indices)

    def set_link_enabled_gravities(
        self,
        enabled: list | np.ndarray | wp.array,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        link_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the enabled state of the gravity on the links of the prims.

        Backends: :guilabel:`tensor`, :guilabel:`usd`.

        Args:
            enabled: Boolean flags to enable/disable gravity on the links (shape ``(N, L)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            link_indices: Indices of links to process (shape ``(L,)``). If not defined, all links are processed.

        Raises:
            AssertionError: Wrapped prims are not valid.

        Example:

        .. code-block:: python

            >>> # enable the gravity of the links for all prims
            >>> prims.set_link_enabled_gravities([True])
            >>>
            >>> # disable the gravity for the first and last prims' finger links
            >>> prims.set_link_enabled_gravities([False], indices=[0, 2], link_indices=[10, 11])
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        backend = self._check_for_tensor_backend(_backend.get_current_backend(["tensor", "usd"]))
        # Tensor API
        if backend == "tensor":
            data = self._physics_articulation_view.get_disable_gravities()  # shape: (N, max_links)
            indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
            link_indices = _ops.resolve_indices(link_indices, count=self.num_links, device=data.device)
            enabled = _ops.place(enabled, dtype=wp.uint8, device=data.device)
            disabled = np.logical_not(enabled.numpy()).astype(np.uint8)  # negate input values
            disabled = _ops.broadcast_to(
                disabled,
                shape=(indices.shape[0], link_indices.shape[0]),
                dtype=wp.uint8,
                device=data.device,
            )
            wp.copy(data[indices, link_indices], disabled)
            self._physics_articulation_view.set_disable_gravities(data, indices)
        # USD API
        else:
            indices = _ops.resolve_indices(indices, count=len(self), device="cpu")
            link_indices = _ops.resolve_indices(link_indices, count=self.num_links, device="cpu")
            enabled = _ops.broadcast_to(
                enabled,
                shape=(indices.shape[0], link_indices.shape[0]),
                dtype=wp.bool,
                device="cpu",
            ).numpy()
            for i, index in enumerate(indices.numpy()):
                for j, link_index in enumerate(link_indices.numpy()):
                    link_prim = get_prim_at_path(self.link_paths[index][link_index])
                    rigid_body_api = Articulation.ensure_api([link_prim], PhysxSchema.PhysxRigidBodyAPI)[0]
                    rigid_body_api.GetDisableGravityAttr().Set(not enabled[i][j].item())

    def get_fixed_tendon_stiffnesses(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        tendon_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the stiffness of the fixed tendons of the prims.

        Backends: :guilabel:`tensor`.

        Search for *Fixed Tendons* in |physx_docs| for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            The stiffnesses of the fixed tendons (shape ``(N, T)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_fixed_tendon_stiffnesses()  # shape: (N, num_fixed_tendons)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        tendon_indices = _ops.resolve_indices(tendon_indices, count=self._num_fixed_tendons, device=data.device)
        return data[indices, tendon_indices].contiguous().to(self._device)

    def get_fixed_tendon_dampings(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        tendon_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the dampings of the fixed tendons of the prims.

        Backends: :guilabel:`tensor`.

        Search for *Fixed Tendons* in |physx_docs| for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            The dampings of the fixed tendons (shape ``(N, T)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_fixed_tendon_dampings()  # shape: (N, num_fixed_tendons)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        tendon_indices = _ops.resolve_indices(tendon_indices, count=self._num_fixed_tendons, device=data.device)
        return data[indices, tendon_indices].contiguous().to(self._device)

    def get_fixed_tendon_limit_stiffnesses(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        tendon_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the limit stiffnesses of the fixed tendons of the prims.

        Backends: :guilabel:`tensor`.

        Search for *Fixed Tendons* in |physx_docs| for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            The limit stiffnesses of the fixed tendons (shape ``(N, T)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_fixed_tendon_limit_stiffnesses()  # shape: (N, num_fixed_tendons)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        tendon_indices = _ops.resolve_indices(tendon_indices, count=self._num_fixed_tendons, device=data.device)
        return data[indices, tendon_indices].contiguous().to(self._device)

    def get_fixed_tendon_limits(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        tendon_indices: list | np.ndarray | wp.array | None = None,
    ) -> tuple[wp.array, wp.array]:
        """Get the limits of the fixed tendons of the prims.

        Backends: :guilabel:`tensor`.

        Search for *Fixed Tendons* in |physx_docs| for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            Two-elements tuple. 1) The lower limits of the fixed tendons (shape ``(N, T)``).
            2) The upper limits of the fixed tendons (shape ``(N, T)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_fixed_tendon_limits()  # shape: (N, num_fixed_tendons, 2)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        tendon_indices = _ops.resolve_indices(tendon_indices, count=self._num_fixed_tendons, device=data.device)
        return (
            data[indices, tendon_indices, wp.array([0], dtype=wp.int32, device=data.device)]
            .contiguous()
            .reshape((indices.shape[0], tendon_indices.shape[0]))
            .to(self._device),
            data[indices, tendon_indices, wp.array([1], dtype=wp.int32, device=data.device)]
            .contiguous()
            .reshape((indices.shape[0], tendon_indices.shape[0]))
            .to(self._device),
        )

    def get_fixed_tendon_rest_lengths(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        tendon_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the rest length of the fixed tendons of the prims.

        Backends: :guilabel:`tensor`.

        Search for *Fixed Tendons* in |physx_docs| for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            The rest lengths of the fixed tendons (shape ``(N, T)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_fixed_tendon_rest_lengths()  # shape: (N, num_fixed_tendons)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        tendon_indices = _ops.resolve_indices(tendon_indices, count=self._num_fixed_tendons, device=data.device)
        return data[indices, tendon_indices].contiguous().to(self._device)

    def get_fixed_tendon_offsets(
        self,
        *,
        indices: list | np.ndarray | wp.array | None = None,
        tendon_indices: list | np.ndarray | wp.array | None = None,
    ) -> wp.array:
        """Get the offsets of the fixed tendons of the prims.

        Backends: :guilabel:`tensor`.

        Search for *Fixed Tendons* in |physx_docs| for more details.

        Args:
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.

        Returns:
            The offsets of the fixed tendons (shape ``(N, T)``).

        Raises:
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.
        """
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self.is_physics_tensor_entity_valid(), _MSG_PHYSICS_TENSOR_ENTITY_NOT_VALID
        # Tensor API
        data = self._physics_articulation_view.get_fixed_tendon_offsets()  # shape: (N, num_fixed_tendons)
        indices = _ops.resolve_indices(indices, count=len(self), device=data.device)
        tendon_indices = _ops.resolve_indices(tendon_indices, count=self._num_fixed_tendons, device=data.device)
        return data[indices, tendon_indices].contiguous().to(self._device)

    def set_fixed_tendon_properties(
        self,
        *,
        stiffnesses: list | np.ndarray | wp.array | None = None,
        dampings: list | np.ndarray | wp.array | None = None,
        limit_stiffnesses: list | np.ndarray | wp.array | None = None,
        lower_limits: list | np.ndarray | wp.array | None = None,
        upper_limits: list | np.ndarray | wp.array | None = None,
        rest_lengths: list | np.ndarray | wp.array | None = None,
        offsets: list | np.ndarray | wp.array | None = None,
        indices: list | np.ndarray | wp.array | None = None,
        tendon_indices: list | np.ndarray | wp.array | None = None,
    ) -> None:
        """Set the fixed tendon properties of the prims.

        Backends: :guilabel:`tensor`.

        Search for *Fixed Tendons* in |physx_docs| for more details.

        Args:
            stiffnesses: The stiffnesses (shape ``(N, T)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            dampings: The dampings (shape ``(N, T)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            limit_stiffnesses: The limit stiffnesses (shape ``(N, T)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            lower_limits: The lower limits (shape ``(N, T)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            upper_limits: The upper limits (shape ``(N, T)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            rest_lengths: The rest lengths (shape ``(N, T)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            offsets: The offsets (shape ``(N, T)``).
                If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
            indices: Indices of prims to process (shape ``(N,)``). If not defined, all wrapped prims are processed.
            tendon_indices: Indices of tendons to process (shape ``(T,)``). If not defined, all tendons are processed.

        Raises:
            AssertionError: None of the fixed tendon properties are defined.
            AssertionError: Wrapped prims are not valid.
            AssertionError: Physics tensor entity is not valid.
        """
        assert (
            stiffnesses is not None
            or dampings is not None
            or limit_stiffnesses is not None
            or lower_limits is not None
            or upper_limits is not None
            or rest_lengths is not None
            or offsets is not None
        ), "None of the fixed tendon properties are defined. Define at least one of them"
        assert self.valid, _MSG_PRIM_NOT_VALID
        assert self._physics_tensor_entity_initialized, _MSG_PHYSICS_TENSOR_ENTITY_NOT_INITIALIZED
        # Tensor API
        view_stiffnesses = (
            self._physics_articulation_view.get_fixed_tendon_stiffnesses()
        )  # shape: (N, max_fixed_tendons)
        view_dampings = self._physics_articulation_view.get_fixed_tendon_dampings()  # shape: (N, max_fixed_tendons)
        view_limit_stiffnesses = (
            self._physics_articulation_view.get_fixed_tendon_limit_stiffnesses()
        )  # shape: (N, max_fixed_tendons)
        view_limits = self._physics_articulation_view.get_fixed_tendon_limits()  # shape: (N, max_fixed_tendons, 2)
        view_rest_lengths = (
            self._physics_articulation_view.get_fixed_tendon_rest_lengths()
        )  # shape: (N, max_fixed_tendons)
        view_offsets = self._physics_articulation_view.get_fixed_tendon_offsets()  # shape: (N, max_fixed_tendons)
        device = view_stiffnesses.device
        indices = _ops.resolve_indices(indices, count=len(self), device=device)
        tendon_indices = _ops.resolve_indices(tendon_indices, count=self._num_fixed_tendons, device=device)
        shape = (indices.shape[0], tendon_indices.shape[0])
        if stiffnesses is not None:
            stiffnesses = _ops.broadcast_to(stiffnesses, shape=shape, dtype=wp.float32, device=device)
            wp.copy(view_stiffnesses[indices, tendon_indices], stiffnesses)
        if dampings is not None:
            dampings = _ops.broadcast_to(dampings, shape=shape, dtype=wp.float32, device=device)
            wp.copy(view_dampings[indices, tendon_indices], dampings)
        if limit_stiffnesses is not None:
            limit_stiffnesses = _ops.broadcast_to(limit_stiffnesses, shape=shape, dtype=wp.float32, device=device)
            wp.copy(view_limit_stiffnesses[indices, tendon_indices], limit_stiffnesses)
        if lower_limits is not None:
            lower_limits = _ops.broadcast_to(lower_limits, shape=shape, dtype=wp.float32, device=device)
            lower_limits = lower_limits.reshape((*shape, 1))
            wp.copy(view_limits[indices, tendon_indices, wp.array([0], dtype=wp.int32, device=device)], lower_limits)
        if upper_limits is not None:
            upper_limits = _ops.broadcast_to(upper_limits, shape=shape, dtype=wp.float32, device=device)
            upper_limits = upper_limits.reshape((*shape, 1))
            wp.copy(view_limits[indices, tendon_indices, wp.array([1], dtype=wp.int32, device=device)], upper_limits)
        if rest_lengths is not None:
            rest_lengths = _ops.broadcast_to(rest_lengths, shape=shape, dtype=wp.float32, device=device)
            wp.copy(view_rest_lengths[indices, tendon_indices], rest_lengths)
        if offsets is not None:
            offsets = _ops.broadcast_to(offsets, shape=shape, dtype=wp.float32, device=device)
            wp.copy(view_offsets[indices, tendon_indices], offsets)
        self._physics_articulation_view.set_fixed_tendon_properties(
            view_stiffnesses,
            view_dampings,
            view_limit_stiffnesses,
            view_limits,
            view_rest_lengths,
            view_offsets,
            indices,
        )

    """
    Internal methods.
    """

    def _check_for_tensor_backend(self, backend: str, *, fallback_backend: str = "usd") -> str:
        """Check if the tensor backend is valid."""
        if backend == "tensor" and not self.is_physics_tensor_entity_valid():
            if _backend.is_backend_set():
                if _backend.should_raise_on_fallback():
                    raise RuntimeError(
                        f"Physics tensor entity is not valid. Fallback set to '{fallback_backend}' backend."
                    )
                carb.log_warn(
                    f"Physics tensor entity is not valid for use with 'tensor' backend. Falling back to '{fallback_backend}' backend."
                )
            return fallback_backend
        return backend

    def _get_drive_api_and_type(self, index: int, dof_index: int) -> tuple[UsdPhysics.DriveAPI, str]:
        """Get the drive API and type for a given degree of freedom (DOF).

        Args:
            index: Index of the prim to process.
            dof_index: Index of the DOF to process.

        Returns:
            Two-elements tuple. 1) The drive API. 2) The type of the DOF.
        """
        if self.dof_types[dof_index] == omni.physics.tensors.DofType.Rotation:
            drive_type = "angular"
        elif self.dof_types[dof_index] == omni.physics.tensors.DofType.Translation:
            drive_type = "linear"
        else:
            carb.log_warn(f"Invalid DOF type ({self.dof_types[dof_index]}) at index {dof_index}")
            drive_type = ""
        dof_prim = get_prim_at_path(self.dof_paths[index][dof_index])
        return Articulation.ensure_api([dof_prim], UsdPhysics.DriveAPI, drive_type)[0], drive_type

    def _query_articulation_properties(self) -> None:
        """Query articulation properties."""

        def query_report(response: omni.physx.bindings._physx.PhysxPropertyQueryArticulationResponse) -> None:
            link_names, link_paths = [], []
            joint_names, joint_paths = [], []
            dof_names, dof_paths, dof_types = [], [], []
            # parse metadata
            for link in response.links:
                # parse link
                if link.rigid_body:
                    link_path = Sdf.Path(link.rigid_body_name)
                    link_names.append(link_path.name)
                    link_paths.append(link_path.pathString)
                # parse joint
                if link.joint:
                    joint_path = Sdf.Path(link.joint_name)
                    joint_names.append(joint_path.name)
                    joint_paths.append(joint_path.pathString)
                    # TODO: differentiate between joint_types: eFixed, eRevolute, ePrismatic, eSpherical, eInvalid
                    # parse DOF
                    if link.joint_dof:
                        dof_names.append(joint_path.name)
                        dof_paths.append(joint_path.pathString)
                        dof_type = omni.physics.tensors.DofType.Invalid
                        for attr in stage.GetPrimAtPath(joint_path).GetAttributes():
                            attr_name = attr.GetName()
                            if attr_name.startswith("drive:"):
                                if attr_name.startswith("drive:linear:"):
                                    dof_type = omni.physics.tensors.DofType.Translation
                                elif attr_name.startswith("drive:angular:"):
                                    dof_type = omni.physics.tensors.DofType.Rotation
                                break
                        dof_types.append(dof_type)
            # register properties
            self._link_names = link_names
            self._joint_names = joint_names
            self._dof_names = dof_names
            self._dof_types = dof_types
            self._link_paths.append(link_paths)
            self._joint_paths.append(joint_paths)
            self._dof_paths.append(dof_paths)

        self._link_paths, self._joint_paths, self._dof_paths = [], [], []
        # query articulation metadata for each prim
        stage = omni.usd.get_context().get_stage()
        stage_id = omni.usd.get_context().get_stage_id()
        for prim_path in self.prim_paths:
            omni.physx.get_physx_property_query_interface().query_prim(
                stage_id=stage_id,
                query_mode=omni.physx.bindings._physx.PhysxPropertyQueryMode.QUERY_ARTICULATION,
                prim_id=PhysicsSchemaTools.sdfPathToInt(prim_path),
                articulation_fn=query_report,
            )
        # update amounts and indices
        self._num_links = len(self._link_names)
        self._link_index_dict = {name: i for i, name in enumerate(self._link_names)}
        self._num_joints = len(self._joint_names)
        self._joint_index_dict = {name: i for i, name in enumerate(self._joint_names)}
        self._num_dofs = len(self._dof_names)
        self._dof_index_dict = {name: i for i, name in enumerate(self._dof_names)}

    """
    Internal callbacks.
    """

    def _on_physics_ready(self, event) -> None:
        """Handle physics ready event."""
        super()._on_physics_ready(event)
        physics_simulation_view = SimulationManager._physics_sim_view__warp
        if physics_simulation_view is None:
            carb.log_warn("Invalid physics simulation view")
            return
        self._physics_articulation_view = physics_simulation_view.create_articulation_view(
            [path.replace(".*", "*") for path in self._paths]
        )
        if self._physics_articulation_view is None:
            carb.log_warn(f"Unable to create articulation view for {self._paths}")
            return
        try:
            if self._physics_articulation_view._backend is None:
                carb.log_warn(f"Unable to create articulation view for {self._paths}. Physics backend not found.")
                self._physics_articulation_view = None
                return
        except AttributeError as e:
            carb.log_warn(f"Unable to create articulation view for {self._paths}. {e}")
            return
        if not self._physics_articulation_view.check():
            carb.log_warn(
                f"Unable to create articulation view for {self._paths}. Underlying physics objects are not valid."
            )
            self._physics_articulation_view = None
            return
        if not self._physics_articulation_view.is_homogeneous:
            carb.log_warn(f"Articulation view for {self._paths} is not homogeneous")
            self._physics_articulation_view = None
            return
        # get internal properties
        if not getattr(
            self, "_physics_tensor_entity_initialized", False
        ):  # HACK: make sure attribute exists if callback is called first
            self._physics_tensor_entity_initialized = True
            # links
            # - number of links
            num_links = self._physics_articulation_view.max_links  # or view.shared_metatype.link_count
            if self._num_links is not None and self._num_links != num_links:
                carb.log_warn(f"Number of links mismatch: USD ({self._num_links}) != Physics tensor ({num_links})")
            self._num_links = num_links
            # - link names
            link_names = self._physics_articulation_view.shared_metatype.link_names
            if self._link_names is not None and self._link_names != link_names:
                carb.log_warn(f"Link names mismatch: USD ({self._link_names}) != Physics tensor ({link_names})")
            self._link_names = link_names
            # - link indices
            link_index_dict = self._physics_articulation_view.shared_metatype.link_indices
            if self._link_index_dict is not None and self._link_index_dict != link_index_dict:
                carb.log_warn(
                    f"Link indices mismatch: USD ({self._link_index_dict}) != Physics tensor ({link_index_dict})"
                )
            self._link_index_dict = link_index_dict
            # - link paths
            link_paths = self._physics_articulation_view.link_paths
            if self._link_paths is not None and self._link_paths != link_paths:
                carb.log_warn(f"Link paths mismatch: USD ({self._link_paths}) != Physics tensor ({link_paths})")
            self._link_paths = link_paths
            # joints
            # - number of joints
            num_joints = self._physics_articulation_view.shared_metatype.joint_count
            if self._num_joints is not None and self._num_joints != num_joints:
                carb.log_warn(f"Number of joints mismatch: USD ({self._num_joints}) != Physics tensor ({num_joints})")
            self._num_joints = num_joints
            # - joint names
            joint_names = self._physics_articulation_view.shared_metatype.joint_names
            if self._joint_names is not None and self._joint_names != joint_names:
                carb.log_warn(f"Joint names mismatch: USD ({self._joint_names}) != Physics tensor ({joint_names})")
            self._joint_names = joint_names
            # - joint indices
            joint_index_dict = self._physics_articulation_view.shared_metatype.joint_indices
            if self._joint_index_dict is not None and self._joint_index_dict != joint_index_dict:
                carb.log_warn(
                    f"Joint indices mismatch: USD ({self._joint_index_dict}) != Physics tensor ({joint_index_dict})"
                )
            self._joint_index_dict = joint_index_dict
            # - joint paths  # TODO: get it from the physics articulation view
            # - joint types
            self._joint_types = self._physics_articulation_view.shared_metatype.joint_types
            # DOFs
            # - number of DOFs
            num_dofs = self._physics_articulation_view.max_dofs
            if self._num_dofs is not None and self._num_dofs != num_dofs:
                carb.log_warn(f"Number of DOFs mismatch: USD ({self._num_dofs}) != Physics tensor ({num_dofs})")
            self._num_dofs = num_dofs
            # - DOF names
            dof_names = self._physics_articulation_view.shared_metatype.dof_names
            if self._dof_names is not None and self._dof_names != dof_names:
                carb.log_warn(f"DOF names mismatch: USD ({self._dof_names}) != Physics tensor ({dof_names})")
            self._dof_names = dof_names
            # - DOF indices
            dof_index_dict = self._physics_articulation_view.shared_metatype.dof_indices
            if self._dof_index_dict is not None and self._dof_index_dict != dof_index_dict:
                carb.log_warn(
                    f"DOF indices mismatch: USD ({self._dof_index_dict}) != Physics tensor ({dof_index_dict})"
                )
            self._dof_index_dict = dof_index_dict
            # - DOF paths
            dof_paths = self._physics_articulation_view.dof_paths
            if self._dof_paths is not None and self._dof_paths != dof_paths:
                carb.log_warn(f"DOF paths mismatch: USD ({self._dof_paths}) != Physics tensor ({dof_paths})")
            self._dof_paths = dof_paths
            # - DOF types
            dof_types = self._physics_articulation_view.shared_metatype.dof_types
            if self._dof_types is not None and self._dof_types != dof_types:
                carb.log_warn(f"DOF types mismatch: USD ({self._dof_types}) != Physics tensor ({dof_types})")
            self._dof_types = dof_types
            # other properties
            self._num_shapes = self._physics_articulation_view.max_shapes
            self._num_fixed_tendons = self._physics_articulation_view.max_fixed_tendons

    def _on_timeline_stop(self, event):
        """Handle timeline stop event."""
        # invalidate articulation view
        self._physics_articulation_view = None
