import time

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

from isaacsim.cortex.framework.cortex_world import CortexWorld
from isaacsim.cortex.framework.df import DfDecider, DfDecision, DfNetwork
from isaacsim.cortex.framework.dfb import DfBasicContext
from isaacsim.cortex.framework.robot import add_franka_to_stage


class CustomContext(DfBasicContext):
    def __init__(self, robot):
        super().__init__(robot)

    def reset(self):
        # Called before the behavior is run. This is where logical state can be initialized.
        self.has_work = False

    def monitor_work(self):
        # Set the self.has_work logical state member if there's currently work to do.
        pass


class GoHome(DfDecider):
    def __init__(self):
        pass


class DoWork(DfDecider):
    def __init__(self):
        pass


class Dispatch(DfDecider):
    def __init__(self):
        super().__init__()
        self.add_child("go_home", GoHome())
        self.add_child("do_work", DoWork())

    def decide(self):
        # The decide method has access to the context object
        if self.context.has_work:
            return DfDecision("do_work")
        else:
            return DfDecision("go_home")


world = CortexWorld()
robot = world.add_robot(add_franka_to_stage(name="franka", prim_path="/World/franka"))
world.scene.add_default_ground_plane()

decider_network = DfNetwork(Dispatch(), context=CustomContext(robot))
world.add_decider_network(decider_network)

start_time = time.time()
world.run(simulation_app, is_done_cb=lambda: time.time() - start_time > 10)
simulation_app.close()
