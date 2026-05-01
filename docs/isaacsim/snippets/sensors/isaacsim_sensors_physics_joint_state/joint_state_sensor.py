# -- Test setup --
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.storage.native import get_assets_root_path

asset_path = get_assets_root_path() + "/Isaac/Robots/IsaacSim/SimpleArticulation/simple_articulation.usd"
stage_utils.add_reference_to_stage(asset_path, path="/World/simple_articulation")
# -- End test setup --

# [create-sensor]
from isaacsim.sensors.experimental.physics import JointStateSensor

sensor = JointStateSensor(path="/World/simple_articulation", enabled=True)
# [/create-sensor]

# [read-sensor]
reading = sensor.get_sensor_reading()
if reading.is_valid:
    for name, pos, vel, eff in zip(reading.dof_names, reading.positions, reading.velocities, reading.efforts):
        print(f"{name}: pos={pos:.4f} vel={vel:.4f} eff={eff:.4f}")
# [/read-sensor]

# [read-frame]
frame = sensor.get_data()
if frame["is_valid"]:
    print(f"DOFs: {frame['dof_names']}")
    print(f"Positions: {frame['positions']}")
    print(f"Velocities: {frame['velocities']}")
    print(f"Efforts: {frame['efforts']}")
    print(f"Time: {frame['time']}, physics step: {frame['physics_step']}")
# [/read-frame]
