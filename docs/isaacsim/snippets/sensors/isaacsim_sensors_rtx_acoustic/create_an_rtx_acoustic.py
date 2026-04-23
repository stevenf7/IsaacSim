import numpy as np
from isaacsim.sensors.experimental.rtx import Acoustic

# Create an RTX Acoustic sensor with a center frequency and two sensor mounts.
acoustic = Acoustic(
    path="/World/acoustic",
    tick_rate=20.0,
    translations=np.array([0.0, 0.0, 1.0]),
    attributes={
        "omni:sensor:WpmAcoustic:centerFrequency": 40000.0,
        # Sensor mount positions (transmitter/receiver locations)
        "omni:sensor:WpmAcoustic:sensorMount:m001:position": (0.0, 0.0, 0.0),
        "omni:sensor:WpmAcoustic:sensorMount:m002:position": (0.1, 0.0, 0.0),
        # Receiver group combining both mounts
        "omni:sensor:WpmAcoustic:rxGroup:g001:receiverIndices": [0, 1],
    },
)
