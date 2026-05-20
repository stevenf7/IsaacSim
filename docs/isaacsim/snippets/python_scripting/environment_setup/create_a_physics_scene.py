from isaacsim.core.simulation_manager import PhysxScene

# Add a physics scene prim to stage
physics_scene = PhysxScene("/World/physicsScene")
# Set gravity vector
physics_scene.set_gravity([0.0, 0.0, -9.81])
