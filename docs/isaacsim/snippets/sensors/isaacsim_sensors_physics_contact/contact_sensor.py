# -- Test setup --
import numpy as np
import omni.usd
from pxr import PhysxSchema, UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()
cube = UsdGeom.Cube.Define(stage, "/World/Cube")
cube.GetSizeAttr().Set(1.0)
UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
UsdPhysics.MassAPI.Apply(cube.GetPrim()).CreateMassAttr(1.0)
# -- End test setup --

# [create-python-api]
import numpy as np
from isaacsim.sensors.experimental.physics import Contact, ContactSensor

sensor = ContactSensor(
    Contact.create(
        "/World/Cube/Contact_Sensor",
        min_threshold=0.0001,
        max_threshold=100000,
        translations=np.array([[0.0, 0.0, 0.0]]),
    )
)
# [/create-python-api]

# [create-python-wrapper]
import numpy as np
from isaacsim.sensors.experimental.physics import Contact, ContactSensor

sensor = ContactSensor(
    Contact(
        "/World/Cube/Contact_Sensor",
        translations=np.array([[0.0, 0.0, 0.0]]),
    )
)
# [/create-python-wrapper]

# [contact-report-api]
stage = omni.usd.get_context().get_stage()
parent_prim = stage.GetPrimAtPath("/World/Cube")
contact_report = PhysxSchema.PhysxContactReportAPI.Apply(parent_prim)
# Set a minimum threshold for the contact report to zero
contact_report.CreateThresholdAttr(0.0)
# [/contact-report-api]

# [reading-backend]
from isaacsim.sensors.experimental.physics import ContactSensor

sensor = ContactSensor("/World/Cube/Contact_Sensor")
sensor.get_sensor_reading()
# [/reading-backend]

# [reading-wrapper]
import numpy as np
from isaacsim.sensors.experimental.physics import Contact, ContactSensor

sensor = ContactSensor(
    Contact(
        "/World/Cube/Contact_Sensor",
        translations=np.array([[0.0, 0.0, 0.0]]),
    )
)

value = sensor.get_data()
print(value)
# [/reading-wrapper]

# [reading-raw-data]
from isaacsim.sensors.experimental.physics import ContactSensor

sensor = ContactSensor("/World/Cube/Contact_Sensor")
raw_data = sensor.get_raw_data()
print(str(raw_data))
# [/reading-raw-data]
