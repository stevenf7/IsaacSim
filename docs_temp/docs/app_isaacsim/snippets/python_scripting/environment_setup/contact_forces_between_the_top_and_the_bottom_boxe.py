import asyncio

import numpy as np
from isaacsim.core.api.materials.physics_material import PhysicsMaterial
from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.core.api.world import World
from isaacsim.core.prims import RigidPrim
from isaacsim.core.utils.stage import create_new_stage_async, update_stage_async


async def contact_force_example():
    g = 10
    await create_new_stage_async()
    if World.instance():
        World.instance().clear_instance()
    world = World()
    world.scene.add_default_ground_plane()
    await world.initialize_simulation_context_async()
    material = PhysicsMaterial(
        prim_path="/World/PhysicsMaterials",
        static_friction=0.5,
        dynamic_friction=0.5,
    )
    # create three rigid cubes sitting on top of three others
    for i in range(3):
        DynamicCuboid(
            prim_path=f"/World/Box_{i+1}", size=2, color=np.array([0, 0, 0.5]), mass=1.0
        ).apply_physics_material(material)

    # Creating RigidPrim with contact relevant keywords allows receiving contact information
    # In the following we indicate that we are interested in receiving up to 30 contact points data between the boxes and the ground plane
    box_view = RigidPrim(
        prim_paths_expr="/World/Box_*",
        positions=np.array([[0, 0, 1.0], [-5.0, 0, 1.0], [5.0, 0, 1.0]]),
        contact_filter_prim_paths_expr=["/World/defaultGroundPlane/GroundPlane/CollisionPlane"],
        max_contact_count=3 * 10,  # we don't expect more than 10 contact points for each box
    )

    world.scene.add(box_view)
    await world.reset_async()

    forces = np.array([[g, 0, 0], [g, 0, 0], [g, 0, 0]])
    box_view.apply_forces(forces)
    await update_stage_async()

    # tangential forces
    friction_forces, friction_points, friction_pair_contacts_count, friction_pair_contacts_start_indices = (
        box_view.get_friction_data(dt=1 / 60)
    )
    # normal forces
    forces, points, normals, distances, pair_contacts_count, pair_contacts_start_indices = (
        box_view.get_contact_force_data(dt=1 / 60)
    )
    # pair_contacts_count, pair_contacts_start_indices are tensors of size num_sensors x num_filters
    # friction_pair_contacts_count, friction_pair_contacts_start_indices are tensors of size num_sensors x num_filters
    # use the following tensors to sum across all the contact points
    force_aggregate = np.zeros((box_view._contact_view.num_shapes, box_view._contact_view.num_filters, 3))
    friction_force_aggregate = np.zeros((box_view._contact_view.num_shapes, box_view._contact_view.num_filters, 3))

    # process contacts for each pair i, j
    for i in range(pair_contacts_count.shape[0]):
        for j in range(pair_contacts_count.shape[1]):
            start_idx = pair_contacts_start_indices[i, j]
            friction_start_idx = friction_pair_contacts_start_indices[i, j]
            count = pair_contacts_count[i, j]
            friction_count = friction_pair_contacts_count[i, j]
            # sum/average across all the contact points for each pair
            pair_forces = forces[start_idx : start_idx + count]
            pair_normals = normals[start_idx : start_idx + count]
            force_aggregate[i, j] = np.sum(pair_forces * pair_normals, axis=0)

            # sum/average across all the friction pairs
            pair_forces = friction_forces[friction_start_idx : friction_start_idx + friction_count]
            friction_force_aggregate[i, j] = np.sum(pair_forces, axis=0)

    print("friction forces: \n", friction_force_aggregate)
    print("contact forces: \n", force_aggregate)
    # get_contact_force_matrix API is equivalent to the summation of the individual contact forces computed above
    print("contact force matrix: \n", box_view.get_contact_force_matrix(dt=1 / 60))
    # get_net_contact_forces API is the summation of the all forces
    # in the current example because all the potential contacts are captured by the choice of our filter prims (/World/defaultGroundPlane/GroundPlane/CollisionPlane)
    # the following is similar to the reduction of the contact force matrix above across the filters
    print("net contact force: \n", box_view.get_net_contact_forces(dt=1 / 60))


asyncio.ensure_future(contact_force_example())
