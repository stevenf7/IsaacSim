# The most basic usage for creating a simulation app
from isaacsim import SimulationApp

kit = SimulationApp()
import carb

server_check = carb.settings.get_settings().get_as_string("/persistent/isaac/asset_root/default")
print(server_check)
for i in range(100):
    kit.update()
kit.close()  # Cleanup application
