# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


from typing import Optional

# omniverse
import omni, carb
from pxr import PhysxSchema, Usd, UsdShade

# isaac-core
import omni.isaac.core.utils.stage as stage_utils
import omni.isaac.core.utils.prims as prim_utils


class ParticleMaterial:
    """A wrapper around position-based-dynamics (PBD) material schema (PhysxPBDMaterialAPI) for particles used to
    simulate fluids, cloth and inflatables.

    Note:
        Currently, only a single material per particle system is supported which applies
        to all objects that are associated with the system.
    """

    def __init__(
        self,
        prim_path: str,
        name: Optional[str] = "particle_material",
        friction: Optional[float] = None,
        particle_friction_scale: Optional[float] = None,
        damping: Optional[float] = None,
        viscosity: Optional[float] = None,
        vorticity_confinement: Optional[float] = None,
        surface_tension: Optional[float] = None,
        cohesion: Optional[float] = None,
        adhesion: Optional[float] = None,
        particle_adhesion_scale: Optional[float] = None,
        adhesion_offset_scale: Optional[float] = None,
        gravity_scale: Optional[float] = None,
        lift: Optional[float] = None,
        drag: Optional[float] = None,
        cfl_coefficient: Optional[float] = None,
    ):
        """Applies the `PhysxSchema.PhysxPBDMaterialAPI` to a material prim.
        Note:
            If a prim does not exist at specified path, then a new UsdShade.Material prim is created.

        Args:
            prim_path (str): The prim path to create/apply PBD material properties.
            friction (float, optional): The friction coefficient.
            particle_friction_scale (float, optional): The coefficient that scales friction for
                solid particle-particle interactions.
            damping (float, optional): The global velocity damping coefficient
            viscosity (float, optional): The viscosity of fluid particles.
            vorticity_confinement (float, optional): The vorticity confinement for fluid particles.
            surface_tension (float, optional): The surface tension.
            cohesion (float, optional): The cohesion for interaction between fluid particles.
            adhesion (float, optional): The adhesion for interaction between particles (solid or fluid),
                and rigid or deformable objects.
            particle_adhesion_scale (float, optional): The coefficient that scales adhesion for solid
                particle-particle interations.
            adhesion_offset_scale (float, optional): The offset scale defines at which adhesion ceases
                to take effect.
            gravity_scale (float, optional): The gravitational acceleration scaling factor. It can be used
                to approximate lighter-than-air inflatables.
            lift (float, optional): The lift coefficient for cloth and inflatable particle objects.
            drag (float, optional): The drag coefficient for cloth and inflatable particle objects.
        """
        self._name = name
        self._prim_path = prim_path

        stage = omni.usd.get_context().get_stage()
        if stage.GetPrimAtPath(prim_path).IsValid():
            if not self._prim.IsA(UsdShade.Material):
                raise ValueError(f"A prim at path '{prim_path}' exists but is not a Usd.Material prim.")
            else:
                carb.log_warn(f"A material prim already defined at path: {prim_path}.")
                self._material = UsdShade.Material(stage.GetPrimAtPath(prim_path))
        else:
            self._material = UsdShade.Material.Define(stage, prim_path)

        self._prim = stage.GetPrimAtPath(prim_path)

        # apply PBD material API
        if self._prim.HasAPI(PhysxSchema.PhysxPBDMaterialAPI):
            self._material_api = PhysxSchema.PhysxPBDMaterialAPI(self._prim)
        else:
            self._material_api = PhysxSchema.PhysxPBDMaterialAPI.Apply(self._prim)

        # set properties
        if friction is not None:
            self.set_friction(friction)
        if particle_friction_scale is not None:
            self.set_particle_friction_scale(particle_friction_scale)
        if damping is not None:
            self.set_damping(damping)
        if viscosity is not None:
            self.set_viscosity(viscosity)
        if vorticity_confinement is not None:
            self.set_vorticity_confinement(vorticity_confinement)
        if surface_tension is not None:
            self.set_surface_tension(surface_tension)
        if cohesion is not None:
            self.set_cohesion(cohesion)
        if adhesion is not None:
            self.set_adhesion(adhesion)
        if particle_adhesion_scale is not None:
            self.set_particle_adhesion_scale(particle_adhesion_scale)
        if adhesion_offset_scale is not None:
            self.set_adhesion_offset_scale(adhesion_offset_scale)
        if gravity_scale is not None:
            self.set_gravity_scale(gravity_scale)
        if lift is not None:
            self.set_lift(lift)
        if drag is not None:
            self.set_drag(drag)
        self._prim_path = prim_path

    """
    Properties.
    """

    @property
    def prim_path(self) -> str:
        """
        Returns:
            str: The stage path to the material.
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
    def material(self) -> UsdShade.Material:
        """
        Returns:
            UsdShade.Material: The USD Material object.
        """
        return self._material

    """
    Operations - Setters.
    """

    def set_friction(self, value: float) -> None:
        """Sets the friction coefficient.

        The friction takes effect in all interactions between particles and rigids or deformables.
        For solid particle-particle interactions it is multiplied by the particle friction scale.

        Args:
            value (float): The friction coefficient.
                Range: [0, inf), Units: dimensionless
        """
        if value < 0:
            carb.log_error("The valid range of friction coefficient is [0. inf).")
        else:
            if "physxPBDMaterial:friction" not in self._prim.GetPropertyNames():
                self._material_api.CreateFrictionAttr().Set(value)
            else:
                self._material_api.GetFrictionAttr().Set(value)

    def set_particle_friction_scale(self, particle_friction_scale: float) -> None:
        """Sets the particle friction scale.

        The coefficient that scales friction for solid particle-particle interaction.

        Args:
            particle_friction_scale (float): The particle friction scale.
                Range: [0, inf), Units: dimensionless
        """
        if particle_friction_scale < 0:
            carb.log_error("The valid range of particle friction scale is [0. inf).")
        else:
            if "physxPBDMaterial:particleFrictionScale" not in self._prim.GetPropertyNames():
                self._material_api.CreateParticleFrictionScaleAttr().Set(particle_friction_scale)
            else:
                self._material_api.GetParticleFrictionScaleAttr().Set(particle_friction_scale)

    def set_damping(self, value: float) -> None:
        """Sets the global velocity damping coefficient.

        Args:
            value (float): The damping coefficient.
                Range: [0, inf), Units: dimensionless
        """
        if value < 0:
            carb.log_error("The valid range of damping coefficient is [0. inf).")
        else:
            if "physxPBDMaterial:damping" not in self._prim.GetPropertyNames():
                self._material_api.CreateDampingAttr().Set(value)
            else:
                self._material_api.GetDampingAttr().Set(value)

    def set_viscosity(self, value: float) -> None:
        """Sets the viscosity for fluid particles.

        Args:
            value (float): The viscosity.
                Range: [0, inf), Units: dimensionless
        """
        if value < 0:
            carb.log_error("The valid range of viscosity is [0. inf).")
        else:
            if "physxPBDMaterial:viscosity" not in self._prim.GetPropertyNames():
                self._material_api.CreateViscosityAttr().Set(value)
            else:
                self._material_api.GetViscosityAttr().Set(value)

    def set_vorticity_confinement(self, value: float) -> None:
        """Sets the vorticity confinement for fluid particles.

        This helps prevent energy loss due to numerical solver by adding vortex-like
        accelerations to the particles.

        Args:
            value (float): The vorticity confinement.
                Range: [0, inf), Units: dimensionless
        """
        if value < 0:
            carb.log_error("The valid range of vorticity confinement is [0. inf).")
        else:
            if "physxPBDMaterial:vorticityConfinement" not in self._prim.GetPropertyNames():
                self._material_api.CreateVorticityConfinementAttr().Set(value)
            else:
                self._material_api.GetVorticityConfinementAttr().Set(value)

    def set_surface_tension(self, value: float) -> None:
        """Sets the surface tension for fluid particles.

        Args:
            value (float): The surface tension.
                Range: [0, inf), Units: 1 / (distance * distance * distance)
        """
        if value < 0:
            carb.log_error("The valid range of damping coefficient is [0. inf).")
        else:
            if "physxPBDMaterial:surfaceTension" not in self._prim.GetPropertyNames():
                self._material_api.CreateSurfaceTensionAttr().Set(value)
            else:
                self._material_api.GetSurfaceTensionAttr().Set(value)

    def set_cohesion(self, value: float) -> None:
        """Sets the cohesion for interaction between fluid particles.

        Args:
            value (float): The cohesion.
                Range: [0, inf), Units: dimensionless

        """
        if value < 0:
            carb.log_error("The valid range of adhesion is [0. inf).")
        else:
            if "physxPBDMaterial:cohesion" not in self._prim.GetPropertyNames():
                self._material_api.CreateCohesionAttr().Set(value)
            else:
                self._material_api.GetCohesionAttr().Set(value)

    def set_adhesion(self, value: float) -> None:
        """Sets the adhesion for interaction between particles (solid or fluid), and rigid or deformable objects.

        Note:
            Adhesion also applies to solid-solid particle interactions, but is multiplied with the
            particle adhesion scale.

        Args:
            value (float): The adhesion.
                Range: [0, inf), Units: dimensionless

        """
        if value < 0:
            carb.log_error("The valid range of adhesion is [0. inf).")
        else:
            if "physxPBDMaterial:adhesion" not in self._prim.GetPropertyNames():
                self._material_api.CreateAdhesionAttr().Set(value)
            else:
                self._material_api.GetAdhesionAttr().Set(value)

    def set_particle_adhesion_scale(self, value: float) -> None:
        """Sets the particle adhesion scale.

        This coefficient scales the adhesion for solid particle-particle interaction.

        Args:
            value (float): The adhesion scale.
                Range: [0, inf), Units: dimensionless
        """
        if value < 0:
            carb.log_error("The valid range of particle adhesion scale is [0. inf).")
        else:
            if "physxPBDMaterial:particleAdhesionScale" not in self._prim.GetPropertyNames():
                self._material_api.CreateParticleAdhesionScaleAttr().Set(value)
            else:
                self._material_api.GetParticleAdhesionScaleAttr().Set(value)

    def set_adhesion_offset_scale(self, value: float) -> None:
        """Sets the adhesion offset scale.

        It defines the offset at which adhesion ceases to take effect. For interactions between
        particles (fluid or solid), and rigids or deformables, the adhesion offset is defined
        relative to the rest offset. For solid particle-particle interactions, the adhesion
        offset is defined relative to the solid rest offset.

        Args:
            value (float): The adhesion offset scale.
                Range: [0, inf), Units: dimensionless
        """
        if value < 0:
            carb.log_error("The valid range of adhesion offset scale is [0. inf).")
        else:
            if "physxPBDMaterial:adhesionOffsetScale" not in self._prim.GetPropertyNames():
                self._material_api.CreateAdhesionOffsetScaleAttr().Set(value)
            else:
                self._material_api.GetAdhesionOffsetScaleAttr().Set(value)

    def set_gravity_scale(self, value: float) -> None:
        """Sets the gravitational acceleration scaling factor.

        It can be used to approximate lighter-than-air inflatable.
        For example (-1.0 would invert gravity).

        Args:
            value (float): The gravity scale.
                Range: (-inf , inf), Units: dimensionless
        """
        if "physxPBDMaterial:gravityScale" not in self._prim.GetPropertyNames():
            self._material_api.CreateGravityScaleAttr().Set(value)
        else:
            self._material_api.GetGravityScaleAttr().Set(value)

    def set_lift(self, value: float) -> None:
        """Sets the lift coefficient, i.e. basic aerodynamic lift model coefficient.

        It is useful for cloth and inflatable particle objects.

        Args:
            value (float): The lift coefficient.
                Range: [0, inf), Units: dimensionless
        """
        if value < 0:
            carb.log_error("The valid range of lift coefficient is [0. inf).")
        else:
            if "physxPBDMaterial:lift" not in self._prim.GetPropertyNames():
                self._material_api.CreateLiftAttr().Set(value)
            else:
                self._material_api.GetLiftAttr().Set(value)

    def set_drag(self, value: float) -> None:
        """Sets the drag coefficient, i.e. basic aerodynamic drag model coefficient.

        It is useful for cloth and inflatable particle objects.

        Args:
            value (float): The drag coefficient.
                Range: [0, inf), Units: dimensionless
        """
        if value < 0:
            carb.log_error("The valid range of drag coefficient is [0. inf).")
        else:
            if "physxPBDMaterial:drag" not in self._prim.GetPropertyNames():
                self._material_api.CreateDragAttr().Set(value)
            else:
                self._material_api.GetDragAttr().Set(value)

    """
    Operations - Getters.
    """

    def get_friction(self) -> float:
        """
        Returns:
            float: The friction coefficient.
        """
        if "physxPBDMaterial:friction" not in self._prim.GetPropertyNames():
            carb.log_error(f"Friction is not defined on the PBD particle material of the prim: {self._prim_path}.")
        else:
            return self._material_api.GetFrictionAttr().Get()

    def get_particle_friction_scale(self) -> float:
        """
        Returns:
            float: The particle friction scale.
        """
        return self._material_api.GetParticleFrictionScaleAttr().Get()

    def get_damping(self) -> float:
        """
        Returns:
            float: The global velocity damping coefficient.
        """
        if "physxPBDMaterial:damping" not in self._prim.GetPropertyNames():
            carb.log_error(f"Damping is not defined on the PBD particle material of the prim: {self._prim_path}.")
        else:
            return self._material_api.GetDampingAttr().Get()

    def get_viscosity(self) -> float:
        """
        Returns:
            float: The viscosity.
        """
        if "physxPBDMaterial:viscosity" not in self._prim.GetPropertyNames():
            carb.log_error(f"Viscosity is not defined on the PBD particle material of the prim: {self._prim_path}.")
        else:
            return self._material_api.GetViscosityAttr().Get()

    def get_vorticity_confinement(self) -> float:
        """
        Returns:
            float: The vorticity confinement for fluid particles.
        """
        if "physxPBDMaterial:vorticityConfinement" not in self._prim.GetPropertyNames():
            carb.log_error(
                f"Vorticity confinement is not defined on the PBD particle material of the prim: {self._prim_path}."
            )
        else:
            return self._material_api.GetVorticityConfinementAttr().Get()

    def get_surface_tension(self) -> float:
        """
        Returns:
            float: The surface tension for fluid particles.
        """
        if "physxPBDMaterial:surfaceTension" not in self._prim.GetPropertyNames():
            carb.log_error(
                f"Surface tension is not defined on the PBD particle material of the prim: {self._prim_path}."
            )
        else:
            return self._material_api.GetSurfaceTensionAttr().Get()

    def get_cohesion(self) -> float:
        """
        Returns:
            float: The cohesion for interaction between fluid particles.
        """
        if "physxPBDMaterial:cohesion" not in self._prim.GetPropertyNames():
            carb.log_error(f"Cohesion is not defined on the PBD particle material of the prim: {self._prim_path}.")
        else:
            return self._material_api.GetCohesionAttr().Get()

    def get_adhesion(self) -> float:
        """
        Returns:
            float: The adhesion for interaction between particles (solid or fluid), and rigids or deformables.
        """
        if "physxPBDMaterial:adhesion" not in self._prim.GetPropertyNames():
            carb.log_error(f"Adhesion is not defined on the PBD particle material of the prim: {self._prim_path}.")
        else:
            return self._material_api.GetAdhesionAttr().Get()

    def get_particle_adhesion_scale(self) -> float:
        """
        Returns:
            float: The particle adhesion scale.
        """
        if "physxPBDMaterial:particleAdhesionScale" not in self._prim.GetPropertyNames():
            carb.log_error(
                f"Particle adhesion scale is not defined on the PBD particle material of the prim: {self._prim_path}."
            )
        else:
            return self._material_api.GetParticleAdhesionScaleAttr().Get()

    def get_adhesion_offset_scale(self) -> float:
        """
        Returns:
            float: The adhesion offset scale.
        """
        if "physxPBDMaterial:adhesionOffsetScale" not in self._prim.GetPropertyNames():
            carb.log_error(
                f"Adhesion offset scale is not defined on the PBD particle material of the prim: {self._prim_path}."
            )
        else:
            return self._material_api.GetAdhesionOffsetScaleAttr().Get()

    def get_gravity_scale(self) -> float:
        """
        Returns:
            float: The gravitational acceleration scaling factor.
        """
        if "physxPBDMaterial:gravityScale" not in self._prim.GetPropertyNames():
            carb.log_error(f"Gravity scale is not defined on the PBD particle material of the prim: {self._prim_path}.")
        else:
            return self._material_api.GetGravityScaleAttr().Get()

    def get_lift(self) -> float:
        """
        Returns:
            float: The lift coefficient, basic aerodynamic lift model coefficient.
        """
        if "physxPBDMaterial:lift" not in self._prim.GetPropertyNames():
            carb.log_error(f"Lift is not defined on the PBD particle material of the prim: {self._prim_path}.")
        else:
            return self._material_api.GetLiftAttr().Get()

    def get_drag(self) -> float:
        """
        Returns:
            float: The drag coefficient, basic aerodynamic drag model coefficient.
        """
        if "physxPBDMaterial:drag" not in self._prim.GetPropertyNames():
            carb.log_error(f"Drag is not defined on the PBD particle material of the prim: {self._prim_path}.")
        else:
            return self._material_api.GetDragAttr().Get()
