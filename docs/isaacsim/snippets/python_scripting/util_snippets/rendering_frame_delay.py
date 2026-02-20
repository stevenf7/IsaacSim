import os

from isaacsim import SimulationApp

SimulationApp({"headless": True}, experience=f"{os.environ['EXP_PATH']}/isaacsim.exp.base.zero_delay.kit")
