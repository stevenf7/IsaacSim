from isaacsim.sensors.experimental.rtx import Acoustic, AcousticSensor

sensor = AcousticSensor(
    Acoustic.create(
        "/World/Acoustic",
        translations=[[0.0, 0.0, 0.0]],
    ),
    annotators=["generic-model-output"],
)
data, info = sensor.get_data("generic-model-output")
