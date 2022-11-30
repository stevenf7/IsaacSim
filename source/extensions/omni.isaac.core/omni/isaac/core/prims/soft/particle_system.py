# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from typing import Optional, Sequence, Tuple

# omniverse
from pxr import PhysxSchema, Usd
import carb

# isaac-core
import omni.isaac.core.utils.stage as stage_utils
import omni.isaac.core.utils.prims as prim_utils
from omni.isaac.core.utils.prims import get_prim_at_path, is_prim_path_valid


class ParticleSystem:
    """A wrapper around PhysX particle system.

    PhysX uses GPU-accelerated position-based-dynamics (PBD) particle simulation [1]. The particle system
    can be used to simulate fluids, cloth and inflatables [2].

    The wrapper is useful for creating and setting solver parameters common to the particle objects
    associated with the system. The particle system's solver parameters cannot be changed once the scene
    is playing.

    Note:
        CPU simulation of particles is not supported. PhysX must be simulated with GPU enabled.

    Reference:
        [1] https://mmacklin.com/pbf_sig_preprint.pdf
        [2] https://docs.omniverse.nvidia.com/prod_extensions/prod_extensions/ext_physics.html#particle-simulation
    """

    def __init__(
        self,
        prim_path: str,
        particle_system_enabled: Optional[bool] = None,
        simulation_owner: Optional[str] = None,
        contact_offset: Optional[float] = None,
        rest_offset: Optional[float] = None,
        particle_contact_offset: Optional[float] = None,
        solid_rest_offset: Optional[float] = None,
        fluid_rest_offset: Optional[float] = None,
        enable_ccd: Optional[bool] = None,
        solver_position_iteration_count: Optional[float] = None,
        max_depenetration_velocity: Optional[float] = None,
        wind: Sequence[float] = None,
        max_neighborhood: Optional[int] = None,
        max_velocity: Optional[float] = None,
        global_self_collision_enabled: Optional[bool] = None,
        non_particle_collision_enabled: Optional[bool] = None,
    ):
        """ Initializes and Applies PhysxSchema.PhysxParticleSystem to the prim at prim_path

        All arguments are accepted as :obj:`None`. In this case, they either have the default values from
        `PhysxParticleSystem` schema (in case a new particle system is created), or the values present in the
        existing particle system.

        Args:
            prim_path (str): The path to the particle system.
            particle_system_enabled (Optional[bool], optional): Whether to enable or disable the particle system.
            simulation_owner (Optional[str], optional): Single PhysicsScene that simulates this particle system.
            contact_offset (Optional[float], optional): Contact offset used for collisions with non-particle
                objects such as rigid or deformable bodies.
            rest_offset (Optional[float], optional): Rest offset used for collisions with non-particle objects
                such as rigid or deformable bodies.
            particle_contact_offset (Optional[float], optional): Contact offset used for interactions
                between particles. Must be larger than solid and fluid rest offsets.
            solid_rest_offset (Optional[float], optional): Rest offset used for solid-solid or solid-fluid
                particle interactions. Must be smaller than particle contact offset.
            fluid_rest_offset (Optional[float], optional): Rest offset used for fluid-fluid particle interactions.
                Must be smaller than particle contact offset.
            enable_ccd (Optional[bool], optional): Enable continuous collision detection for particles to help
                avoid tunneling effects.
            solver_position_iteration_count (Optional[float], optional): Number of solver iterations for position.
            max_depenetration_velocity (Optional[float], optional): The maximum velocity permitted to be introduced
                by the solver to depenetrate intersecting particles.
            wind (Sequence[float], optional):The wind applied to the current particle system.
            max_neighborhood (Optional[int], optional): The particle neighborhood size.
            max_velocity (Optional[float], optional): Maximum particle velocity.
            global_self_collision_enabled (Optional[bool], optional): If True, self collisions follow
                particle-object-specific settings. If False, all particle self collisions are disabled, regardless
                of any other settings. Improves performance if self collisions are not needed.
            non_particle_collision_enabled (Optional[bool], optional): Enable or disable particle collision with
                non-particle objects for all particles in the system. Improves performance if non-particle collisions
                are not needed.
        """
        # store constants
        self._prim_path = prim_path

        # check whether to create or apply particle system
        if prim_utils.is_prim_path_valid(prim_path):
            carb.log_info(f"Physics particle system prim is already defined at path {self._prim_path}.")
            self._prim = prim_utils.get_prim_at_path(prim_path)
            self._particle_system = PhysxSchema.PhysxParticleSystem(self._prim)
        else:
            stage = stage_utils.get_current_stage()
            self._particle_system = PhysxSchema.PhysxParticleSystem.Define(stage, self._prim_path)
            self._prim = prim_utils.get_prim_at_path(prim_path)

        # set properties
        if particle_system_enabled is not None:
            self.set_particle_system_enabled(particle_system_enabled)
        if simulation_owner is not None:
            self.set_simulation_owner(simulation_owner)
        if contact_offset is not None:
            self.set_contact_offset(contact_offset)
        if rest_offset is not None:
            self.set_rest_offset(rest_offset)
        if particle_contact_offset is not None:
            self.set_particle_contact_offset(particle_contact_offset)
        if solid_rest_offset is not None:
            self.set_solid_rest_offset(solid_rest_offset)
        if fluid_rest_offset is not None:
            self.set_fluid_rest_offset(fluid_rest_offset)
        if enable_ccd is not None:
            self.set_enable_ccd(enable_ccd)
        if solver_position_iteration_count is not None:
            self.set_solver_position_iteration_count(solver_position_iteration_count)
        if max_depenetration_velocity is not None:
            self.set_max_depenetration_velocity(max_depenetration_velocity)
        if wind is not None:
            self.set_wind(wind)
        if max_neighborhood is not None:
            self.set_max_neighborhood(max_neighborhood)
        if max_velocity is not None:
            self.set_max_velocity(max_velocity)
        if global_self_collision_enabled is not None:
            self.set_global_self_collision_enabled(global_self_collision_enabled)
        if non_particle_collision_enabled is not None:
            self.set_non_particle_collision_enabled(non_particle_collision_enabled)

    """
    Properties.
    """

    @property
    def prim_path(self) -> str:
        """
        Returns:
            str: The stage path to the particle system.
        """
        return self._prim_path

    @property
    def prim(self) -> Usd.Prim:
        """
        Returns:
            Usd.Prim: The USD prim present.
        """
        return self._prim

    @property
    def particle_system(self) -> PhysxSchema.PhysxParticleSystem:
        """
        Returns:
            PhysxSchema.PhysxParticleSystem: The particle system.
        """
        return self._particle_system

    """
    Operations - Setters.
    """

    def set_particle_system_enabled(self, value: bool) -> None:
        """Set enabling of the particle system.

        Args:
            value (bool): Whether to enable or disable.
        """
        if self._particle_system.GetParticleSystemEnabledAttr().Get() is None:
            self._particle_system.CreateParticleSystemEnabledAttr().Set(value)
        else:
            self._particle_system.GetParticleSystemEnabledAttr().Set(value)

    def set_simulation_owner(self, value: str) -> None:
        """Set the PhysicsScene that simulates this particle system.

        Args:
            value (str): The prim path to the physics scene.
        """
        if self._particle_system.GetSimulationOwnerRel().GetTargets() is None:
            self._particle_system.CreateSimulationOwnerRel().SetTargets([value])
        else:
            self._particle_system.GetSimulationOwnerRel().SetTargets([value])

    def set_contact_offset(self, value: float) -> None:
        """Set the contact offset used for collisions with non-particle objects such as rigid or deformable bodies.

        Args:
            value (float): The contact offset.
        """
        if self._particle_system.GetContactOffsetAttr().Get() is None:
            self._particle_system.CreateContactOffsetAttr().Set(value)
        else:
            self._particle_system.GetContactOffsetAttr().Set(value)

    def set_rest_offset(self, value: float) -> None:
        """Set the rest offset used for collisions with non-particle objects such as rigid or deformable bodies.

        Args:
            value (float): The rest offset.
        """
        if self._particle_system.GetRestOffsetAttr().Get() is None:
            self._particle_system.CreateRestOffsetAttr().Set(value)
        else:
            self._particle_system.GetRestOffsetAttr().Set(value)

    def set_particle_contact_offset(self, value: float) -> None:
        """Set the contact offset used for interactions between particles.

        Note: Must be larger than solid and fluid rest offsets.

        Args:
            value (float): The contact offset.
        """
        if self._particle_system.GetParticleContactOffsetAttr().Get() is None:
            self._particle_system.CreateParticleContactOffsetAttr().Set(value)
        else:
            self._particle_system.GetParticleContactOffsetAttr().Set(value)

    def set_solid_rest_offset(self, value: float) -> None:
        """Set the rest offset used for solid-solid or solid-fluid particle interactions.

        Note: Must be smaller than particle contact offset.

        Args:
            value (float): The rest offset.
        """
        if self._particle_system.GetSolidRestOffsetAttr().Get() is None:
            self._particle_system.CreateSolidRestOffsetAttr().Set(value)
        else:
            self._particle_system.GetSolidRestOffsetAttr().Set(value)

    def set_fluid_rest_offset(self, value: float) -> None:
        """Set the rest offset used for fluid-fluid particle interactions.

        Note: Must be smaller than particle contact offset.

        Args:
            value (float): The rest offset.
        """
        if self._particle_system.GetSolidRestOffsetAttr().Get() is None:
            self._particle_system.CreateSolidRestOffsetAttr().Set(value)
        else:
            self._particle_system.GetSolidRestOffsetAttr().Set(value)

    def set_enable_ccd(self, value: bool) -> None:
        """Enable continuous collision detection for particles.

        Args:
            value (bool): Whether to enable or disable.
        """
        if self._particle_system.GetEnableCCDAttr().Get() is None:
            self._particle_system.CreateEnableCCDAttr().Set(value)
        else:
            self._particle_system.GetEnableCCDAttr().Set(value)

    def set_solver_position_iteration_count(self, value: int) -> None:
        """Set the number of solver iterations for position.

        Args:
            value (int): Number of solver iterations.
        """
        if self._particle_system.GetSolverPositionIterationCountAttr().Get() is None:
            self._particle_system.CreateSolverPositionIterationCountAttr().Set(value)
        else:
            self._particle_system.GetSolverPositionIterationCountAttr().Set(value)

    def set_max_depenetration_velocity(self, value: float) -> None:
        """Set the maximum velocity permitted to be introduced by the solver to
        depenetrate intersecting particles.

        Args:
            value (float): The maximum depenetration velocity.
        """
        if self._particle_system.GetMaxDepenetrationVelocityAttr().Get() is None:
            self._particle_system.CreateMaxDepenetrationVelocityAttr().Set(value)
        else:
            self._particle_system.GetMaxDepenetrationVelocityAttr().Set(value)

    def set_wind(self, value: Sequence[float]) -> None:
        """Set the wind velocity applied to the current particle system.

        Args:
            value (Sequence[float]): The wind applied to the current particle system.
        """
        if self._particle_system.GetWindAttr().Get() is None:
            self._particle_system.CreateWindAttr().Set(tuple(value))
        else:
            self._particle_system.GetWindAttr().Set(tuple(value))

    def set_max_neighborhood(self, value: int) -> None:
        """Set the particle neighborhood size.

        Args:
            value (int): The neighborhood size.
        """
        if self._particle_system.GetMaxNeighborhoodAttr().Get() is None:
            self._particle_system.CreateMaxNeighborhoodAttr().Set(value)
        else:
            self._particle_system.GetMaxNeighborhoodAttr().Set(value)

    def set_max_velocity(self, value: float) -> None:
        """Set the maximum particle velocity.

        Args:
            value (float): The maximum velocity.
        """
        if self._particle_system.GetMaxVelocityAttr().Get() is None:
            self._particle_system.CreateMaxVelocityAttr().Set(value)
        else:
            self._particle_system.GetMaxVelocityAttr().Set(value)

    def set_global_self_collision_enabled(self, value: bool) -> None:
        """Enable self collisions to follow particle-object-specific settings.

        If True, self collisions follow particle-object-specific settings. If False,
        all particle self collisions are disabled, regardless of any other settings.

        Note: Improves performance if self collisions are not needed.

        Args:
            value (bool): Whether to enable or disable.
        """
        if self._particle_system.GetGlobalSelfCollisionEnabledAttr().Get() is None:
            self._particle_system.CreateGlobalSelfCollisionEnabledAttr().Set(value)
        else:
            self._particle_system.GetGlobalSelfCollisionEnabledAttr().Set(value)

    """
    Operations - Getters.
    """

    def get_particle_system_enabled(self) -> bool:
        """
        Returns:
            float: Whether particle system is enabled or not.
        """
        return self._particle_system.GetParticleSystemEnabledAttr().Get()

    def get_simulation_owner(self) -> Usd.Prim:
        """
        Returns:
            Usd.Prim: The physics scene prim attached to particle system.
        """
        return self._particle_system.GetSimulationOwnerRel().Get()

    def get_contact_offset(self) -> float:
        """
        Returns:
            float: The contact offset  used for collisions with non-particle objects.
        """
        return self._particle_system.GetContactOffsetAttr().Get()

    def get_rest_offset(self) -> float:
        """
        Returns:
            float: The rest offset used for collisions with non-particle objects.
        """
        return self._particle_system.GetRestOffsetAttr().Get()

    def get_particle_contact_offset(self) -> float:
        """
        Returns:
            float: The contact offset used for interactions between particles.
        """
        return self._particle_system.GetParticleContactOffsetAttr().Get()

    def get_solid_rest_offset(self) -> float:
        """
        Returns:
            float: The rest offset used for solid-solid or solid-fluid particle interactions.
        """
        return self._particle_system.GetSolidRestOffsetAttr().Get()

    def get_fluid_rest_offset(self) -> float:
        """
        Returns:
            float: The rest offset used for fluid-fluid particle interactions.
        """
        return self._particle_system.GetSolidRestOffsetAttr().Get()

    def get_enable_ccd(self) -> bool:
        """
        Returns:
            bool: Whether continuous collision detection for particles is enabled or disabled.
        """
        return self._particle_system.GetEnableCCDAttr().Get()

    def get_solver_position_iteration_count(self) -> int:
        """
        Returns:
            int: The number of solver iterations for positions.
        """
        return self._particle_system.GetSolverPositionIterationCountAttr().Get()

    def get_max_depenetration_velocity(self) -> None:
        """
        Returns:
            float: The maximum velocity permitted between intersecting particles.
        """
        return self._particle_system.GetMaxDepenetrationVelocityAttr().Get()

    def get_wind(self) -> Tuple[float, float, float]:
        """
        Returns:
            Tuple[float, float, float]: The wind applied to the current particle system.
        """
        return self._particle_system.GetWindAttr().Get()

    def get_max_neighborhood(self) -> int:
        """
        Returns:
            int: The particle neighborhood size.
        """
        return self._particle_system.GetMaxNeighborhoodAttr().Get()

    def get_max_velocity(self) -> float:
        """
        Returns:
            float: The maximum particle velocity.
        """
        return self._particle_system.GetMaxVelocityAttr().Get()

    def get_global_self_collision_enabled(self) -> bool:
        """
        Returns:
            bool: Whether self collisions to follow particle-object-specific settings
                is enabled or disabled.
        """
        return self._particle_system.GetGlobalSelfCollisionEnabledAttr().Get()

    """
    Operations - WIP.
    """

    def apply_particle_anisotropy(self) -> PhysxSchema.PhysxParticleAnisotropyAPI:
        """Applies anisotropy to the particle system.

        This is used to compute anisotropic scaling of particles in a post-processing step.
        It only affects the rendering output including iso-surface generation.
        """
        return PhysxSchema.PhysxParticleAnisotropyAPI.Apply(self._prim)

    def apply_particle_smoothing(self) -> PhysxSchema.PhysxParticleSmoothingAPI:
        """Applies smoothing to the simulated particle system.

        This is used to control smoothing of particles in a post-processing step.
        It only affects the rendering output including iso-surface generation.
        """
        return PhysxSchema.PhysxParticleSmoothingAPI.Apply(self._prim)

    def apply_particle_isotropy(self) -> PhysxSchema.PhysxParticleAnisotropyAPI:
        """Applies iso-surface extraction to the particle system.

        This is used to define settings to extract an iso-surface from the particles
        in a post-processing step. It only affects the rendering output including iso-surface generation.
        """
        return PhysxSchema.PhysxParticleAnisotropyAPI.Apply(self._prim)
