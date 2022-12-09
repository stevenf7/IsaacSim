from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp()

from omni.isaac.core import World
import omni.kit.app

world = World(stage_units_in_meters=1.0, physics_prim_path="/physicsScene", backend="numpy")
world.scene.add_default_ground_plane()
world.reset()

frame_idx = 0
while simulation_app.is_running():
    if world.is_playing():
        world.step(render=True)
    else:
        simulation_app.update()
        # we should exit this loop before we hit frame 200 unless we are stuck on an exit screen
        assert frame_idx < 200
    # try exiting, it should exit unless a save file dialog shows up.
    if frame_idx == 100:
        omni.kit.app.get_app().post_quit()
    frame_idx += 1

simulation_app.close()
