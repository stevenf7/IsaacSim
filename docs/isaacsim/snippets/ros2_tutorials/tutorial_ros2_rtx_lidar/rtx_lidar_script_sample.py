from isaacsim.sensors.experimental.rtx import Lidar

# Example_Rotary scans at 10 Hz; tick_rate must match scanRateBaseHz so that scan
# accumulation and multi-tick rendering produce a full scan per tick.
lidar = Lidar.create(
    path="/sensor",
    config="Example_Rotary",
    tick_rate=10.0,
    translations=[[0.0, 0.0, 1.0]],
)
