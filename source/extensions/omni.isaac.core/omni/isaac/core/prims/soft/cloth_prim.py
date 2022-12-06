# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from typing import Optional, Sequence
import numpy as np

# omniverse
import omni
import carb
from pxr import Gf, UsdGeom, Sdf, UsdPhysics, UsdShade, PhysxSchema
from omni.physx.scripts import particleUtils

# isaac-core
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.utils.types import DynamicState
from omni.isaac.core.utils.stage import get_current_stage
from omni.isaac.core.materials import ParticleMaterial

# isaac.core.soft
from omni.isaac.core.prims.soft.particle_system import ParticleSystem


class ClothPrim(XFormPrim):
    """A wrapper around PhysX particle simulation for cloth.
    Note:
        Currently this prim is managed by PhysxSchema.PhysxAutoParticleClothAPI without relying on the ClothPrimView class.
        In the future, methods of this class will delegate the calls to an underlying ClothPrimView object.
    """

    def __init__(
        self,
        prim_path: str,
        particle_system: ParticleSystem,
        particle_material: Optional[ParticleMaterial] = None,
        name: Optional[str] = "cloth",
        color: Optional[Sequence[float]] = None,
        pressure: Optional[float] = None,
        particle_group: Optional[int] = 0,
        self_collision: Optional[bool] = True,
        self_collision_filter: Optional[bool] = True,
        stretch_stiffness: Optional[float] = None,
        bend_stiffness: Optional[float] = None,
        shear_stiffness: Optional[float] = None,
        spring_damping: Optional[float] = None,
        particle_mass: Optional[float] = 0.01,
        position: Optional[Sequence[float]] = None,
        orientation: Optional[Sequence[float]] = None,
        scale: Optional[Sequence[float]] = None,
        visible: Optional[bool] = True,
    ) -> None:
        """Applies PhysxAutoParticleClothAPI to the primitive in prim_path given a particle_system and binds particle_material to it.
        Args:
            prim_path (str): the absolute path that the prim is supposed to be registered in.
            particle_system (ParticleSystem): the particle system that this cloth is using.
            particle_material (ParticleMaterial): the particle material that is cloth is using.
            name (str, optional): name given to the prim, this can be different than the prim path. Defaults to None.
            color(Sequence[float], optional): the color of the cloth.
            position (Sequence[float], optional): the position of the center of the cloth.
            orientation (Sequence[float], optional): the initial orientation of the cloth, assuming cloth is flat.
            scale (Sequence[float], optional): the scale of the cloth.
            visible (bool, optional): True if the cloth is supposed to be visible, False otherwise.
            particle_mass (float, optional): the mass of one single particle.
            ==================================== particle physic cloth coefficients ====================================
            pressure (float, optional): if > 0, a particle cloth has an additional pressure constraint that provides
                                        inflatable (i.e. balloon-like) dynamics. The pressure times the rest volume
                                        defines the volume the inflatable tries to match. Pressure only works well for
                                        closed or approximately closed meshes, range: [0, inf), units: dimensionless
            particle_group (int, optional): group Id of the particles, range: [0, 2^20)
            self_collision (bool, optional): enable self collision of the particles or of the particle object.
            self_collision_filter (bool, optional): whether the simulation should filter particle-particle collisions
                                                    based on the rest position distances.
            stretch_stiffness (float, optional): represents a stiffness for linear springs placed between particles to
                                                 counteract stretching, range: [0, inf), units: force / distance =
                                                 mass / second / second
            bend_stiffness (float, optional): represents a stiffness for linear springs placed in a way to counteract
                                              bending, range: [0, inf), units: force / distance = mass / second / second
            shear_stiffness (float, optional): represents a stiffness for linear springs placed in a way to counteract
                                               shear, range: [0, inf), units: force / distance = mass / second / second
            spring_damping (float, optional): damping on cloth spring constraints. Applies to all constraints
                                              parameterized by stiffness attributes, range: [0, inf),
                                              units: force * second / distance = mass / second

        Note:
            Particles / objects in different groups in the same system collide with each other. Within the same group in
            the same system, the collision behavior is controlled by the self_collision parameter.
        """
        self._stage = get_current_stage()
        self._prim = self._stage.GetPrimAtPath(prim_path)
        self._mesh = UsdGeom.Mesh.Get(self._stage, prim_path)
        # add physics material
        if particle_material is not None:
            # TODO: should the material be bound to cloth prim or the particle system?
            binding_api = UsdShade.MaterialBindingAPI.Apply(self._prim)
            binding_api.Bind(
                UsdShade.Material(particle_material.material), UsdShade.Tokens.weakerThanDescendants, "physics"
            )
            UsdShade.MaterialBindingAPI.Apply(particle_system.prim).Bind(
                particle_material.material, UsdShade.Tokens.weakerThanDescendants, "physics"
            )
        # configure as cloth
        particleUtils.add_physx_particle_cloth(
            self._stage,
            path=prim_path,
            dynamic_mesh_path=None,
            particle_system_path=particle_system.prim_path,
            spring_stretch_stiffness=stretch_stiffness,
            spring_bend_stiffness=bend_stiffness,
            spring_shear_stiffness=shear_stiffness,
            spring_damping=spring_damping,
            self_collision=self_collision,
            self_collision_filter=self_collision_filter,
            particle_group=particle_group,
            pressure=pressure,
        )
        # PhysxAutoParticleClothAPI is applied above
        self._cloth_auto_api = PhysxSchema.PhysxAutoParticleClothAPI(self._prim)

        # configure mass:
        num_verts = len(self._mesh.GetPointsAttr().Get())
        mass = particle_mass * num_verts
        mass_api = UsdPhysics.MassAPI.Apply(self._mesh.GetPrim())
        mass_api.GetMassAttr().Set(mass)
        # add render material:
        if color is None:
            color = [71.0 / 255.0, 165.0 / 255.0, 1.0]
        create_list = []
        omni.kit.commands.execute(
            "CreateAndBindMdlMaterialFromLibrary",
            mdl_name="OmniPBR.mdl",
            mtl_name="OmniPBR",
            mtl_created_list=create_list,
            bind_selected_prims=False,
        )
        shader = UsdShade.Shader.Get(self._stage, create_list[0] + "/Shader")
        shader.CreateInput("diffuse_color_constant", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
        omni.kit.commands.execute(
            "BindMaterialCommand", prim_path=prim_path, material_path=create_list[0], strength=None
        )

        XFormPrim.__init__(
            self,
            prim_path=prim_path,
            name=name,
            position=position,
            orientation=orientation,
            scale=scale,
            visible=visible,
        )

    """
    Properties.
    """

    @property
    def mesh(self) -> UsdGeom.Mesh:
        """
        Returns:
            Usd.Prim: USD Prim object that this object tracks.
        """
        return self._mesh

    """
    Operations- State.
    """

    def get_current_dynamic_state(self) -> DynamicState:
        """Return the DynamicState that contains the position and orientation of the cloth prim
        Returns:
            DynamicState:
                position (np.ndarray, optional): position in the world frame of the prim. shape is (3, ).
                                                       Defaults to None, which means left unchanged.
                orientation (np.ndarray, optional): quaternion orientation in the world frame of the prim.
                                                          quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                          Defaults to None, which means left unchanged.
        """
        position, orientation = self.get_world_pose()
        return DynamicState(position=position, orientation=orientation)

    def _get_points_pose(self):
        """Return the position of the points of the cloth prim with respect to the center of the cloth prim
        Returns:
            pxr.Vt.Vec3fArray: Vec3fArray of points that the cloth is composed of.
        """
        points = self._prim.GetAttribute("points").Get()
        if points is None:
            raise Exception(f"The prim {self.name} does not have points attribute.")
        return self._prim.GetAttribute("points").Get()

    def get_local_points_pose(self):
        """Return the local position of the points of the cloth prim
        Returns:
            pxr.Vt.Vec3fArray: Vec3fArray of points that the cloth is composed of.
        """
        return self.get_local_pose()[0] + self._get_points_pose()

    def get_world_points_pose(self):
        """Return the global position of the points of the cloth prim
        Returns:
            pxr.Vt.Vec3fArray: Vec3fArray of points that the cloth is composed of.
        """
        return self.get_world_pose()[0] + self._get_points_pose()

    """
    Operations- Setters.
    """

    def set_stretch_stiffness(self, stretch_stiffness: float) -> None:
        """Sets the stretch stiffness.

        It represents a stiffness for linear springs placed between particles to counteract stretching.

        Args:
            stretch_stiffness (float): The stretch stiffness.
                Range: [0 , inf), Units: force/distance = mass/second/second
        """
        if stretch_stiffness < 0:
            carb.log_error("The range of stretch stiffness is [0. inf).")
        if "physxAutoParticleCloth:springStretchStiffness" not in self._prim.GetPropertyNames():
            self._cloth_auto_api.CreateSpringStretchStiffnessAttr().Set(stretch_stiffness)
        else:
            self._cloth_auto_api.GetSpringStretchStiffnessAttr().Set(stretch_stiffness)

    def set_bend_stiffness(self, bend_stiffness: float) -> None:
        """Sets the bend stiffness

        It represents a stiffness for linear springs placed in a way to counteract bending.

        Args:
            bend_stiffness (float): The bend stiffness.
                Range: [0 , inf), Units: mass/second/second
        """
        if bend_stiffness < 0:
            carb.log_error("The range of bend stiffness is [0. inf).")
        if "physxAutoParticleCloth:springBendStiffness" not in self._prim.GetPropertyNames():
            self._cloth_auto_api.CreateSpringBendStiffnessAttr().Set(bend_stiffness)
        else:
            self._cloth_auto_api.GetSpringBendStiffnessAttr().Set(bend_stiffness)

    def set_shear_stiffness(self, shear_stiffness: float) -> None:
        """Sets the shear stiffness

        It represents a stiffness for linear springs placed in a way to counteract shear.

        Args:
            shear_stiffness (float): The shear stiffness.
                Range: [0 , inf), Units: force/distance = mass/second/second
        """
        if shear_stiffness < 0:
            carb.log_error("The range of shear stiffness is [0. inf).")
        if "physxAutoParticleCloth:springShearStiffness" not in self._prim.GetPropertyNames():
            self._cloth_auto_api.CreateSpringShearStiffnessAttr().Set(shear_stiffness)
        else:
            self._cloth_auto_api.GetSpringShearStiffnessAttr().Set(shear_stiffness)

    def set_spring_damping(self, spring_damping: float) -> None:
        """Sets damping on cloth spring constraints

        Note: It applies to all constraints parameterized by stiffness attributes.

        Args:
            spring_damping (float): The spring damping.
                Range: [0 , inf), Units: force/distance = mass/second/second
        """
        if spring_damping < 0:
            carb.log_error("The range of spring damping is [0. inf).")
        if "physxAutoParticleCloth:springDamping" not in self._prim.GetPropertyNames():
            self._cloth_auto_api.CreateSpringDampingAttr().Set(spring_damping)
        else:
            self._cloth_auto_api.GetSpringDampingAttr().Set(spring_damping)

    """
    Operations- Getters.
    """

    def get_stretch_stiffness(self) -> float:
        """
        Returns:
            float: The stretch stiffness.
        """
        if "physxAutoParticleCloth:springStretchStiffness" not in self._prim.GetPropertyNames():
            carb.log_error(f"Stretch stiffness is not defined on the cloth prim: {self.name}.")
        else:
            return self._cloth_auto_api.GetSpringStretchStiffnessAttr().Get()

    def get_bend_stiffness(self) -> float:
        """
        Returns:
            float: The bend stiffness.
        """
        if "physxAutoParticleCloth:springBendStiffness" not in self._prim.GetPropertyNames():
            carb.log_error(f"Bend stiffness is not defined on the cloth prim: {self.name}.")
        else:
            return self._cloth_auto_api.GetSpringBendStiffnessAttr().Get()

    def get_shear_stiffness(self) -> float:
        """
        Returns:
            float: The shear stiffness.
        """
        if "physxAutoParticleCloth:springShearStiffness" not in self._prim.GetPropertyNames():
            carb.log_error(f"Shear stiffness is not defined on the cloth prim: {self.name}.")
        else:
            return self._cloth_auto_api.GetSpringShearStiffnessAttr().Get()

    def get_spring_damping(self) -> float:
        """
        Returns:
            float: The spring damping.
        """
        if "physxAutoParticleCloth:springDamping" not in self._prim.GetPropertyNames():
            carb.log_error(f"Spring damping is not defined on the cloth prim: {self.name}.")
        else:
            return self._cloth_auto_api.GetSpringDampingAttr().Get()
