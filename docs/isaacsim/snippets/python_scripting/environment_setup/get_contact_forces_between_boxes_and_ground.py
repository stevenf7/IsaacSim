import asyncio

import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.materials import RigidBodyMaterial
from isaacsim.core.experimental.objects import Cube, GroundPlane
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim
from isaacsim.core.simulation_manager import SimulationManager
from pxr import PhysxSchema


async def contact_force_example():
    g = 10
    await stage_utils.create_new_stage_async()
    stage_utils.define_prim("/World/physicsScene", "PhysicsScene")
    ground_plane = GroundPlane("/World/GroundPlane")
    material = RigidBodyMaterial(
        "/World/PhysicsMaterials",
        static_frictions=[0.5],
        dynamic_frictions=[0.5],
    )
    # create three rigid cubes sitting on top of three others
    cube_paths = [f"/World/Box_{i+1}" for i in range(3)]
    Cube(cube_paths, sizes=2, colors=np.array([0, 0, 0.5]))
    cube_geoms = GeomPrim(cube_paths, apply_collision_apis=True)
    cube_geoms.apply_physics_materials(material)

    # Creating RigidPrim with contact relevant keywords allows receiving contact information
    # In the following we indicate that we are interested in receiving up to 30 contact points data between the boxes and the ground plane
    box_view = RigidPrim(
        cube_paths,
        masses=[1.0],
        positions=np.array([[0, 0, 1.0], [-5.0, 0, 1.0], [5.0, 0, 1.0]]),
        contact_filter_paths=["/World/GroundPlane/collisionPlane"],
        max_contact_count=3 * 10,  # we don't expect more than 10 contact points for each box
    )
    if SimulationManager.get_active_physics_engine() == "physx":
        box_view.set_sleep_thresholds([0.0])
        box_view.set_enabled_contact_tracking([True])
        GeomPrim.ensure_api(ground_plane.planes.prims, PhysxSchema.PhysxContactReportAPI)

    app_utils.play()
    await app_utils.update_app_async()

    forces = np.array([[g, 0, 0], [g, 0, 0], [g, 0, 0]])
    box_view.apply_forces(forces)
    await app_utils.update_app_async(steps=5)

    # tangential forces
    friction_forces, friction_points, friction_pair_contacts_count, friction_pair_contacts_start_indices = (
        box_view.get_friction_data(dt=1 / 60)
    )
    # normal forces
    forces, points, normals, distances, pair_contacts_count, pair_contacts_start_indices = (
        box_view.get_contact_force_data(dt=1 / 60)
    )
    friction_forces = friction_forces.numpy()
    forces = forces.numpy()
    normals = normals.numpy()
    pair_contacts_count = pair_contacts_count.numpy()
    pair_contacts_start_indices = pair_contacts_start_indices.numpy()
    friction_pair_contacts_count = friction_pair_contacts_count.numpy()
    friction_pair_contacts_start_indices = friction_pair_contacts_start_indices.numpy()
    # pair_contacts_count, pair_contacts_start_indices are tensors of size num_sensors x num_filters
    # friction_pair_contacts_count, friction_pair_contacts_start_indices are tensors of size num_sensors x num_filters
    # use the following tensors to sum across all the contact points
    force_aggregate = np.zeros((len(box_view), box_view.num_contact_filters, 3))
    friction_force_aggregate = np.zeros((len(box_view), box_view.num_contact_filters, 3))

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
    print("contact force matrix: \n", box_view.get_contact_force_matrix(dt=1 / 60).numpy())
    # get_net_contact_forces API is the summation of the all forces
    # in the current example because all the potential contacts are captured by the choice of our filter prims (/World/GroundPlane/collisionPlane)
    # the following is similar to the reduction of the contact force matrix above across the filters
    print("net contact force: \n", box_view.get_net_contact_forces(dt=1 / 60).numpy())
    app_utils.stop()


asyncio.ensure_future(contact_force_example())
