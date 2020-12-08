# Cross-platform tests
from .utils.test_surface_gripper import *
from .utils.test_nucleus_utils import *

from .dynamic_control.test_articulation import *
from .dynamic_control.test_pickles import *
from .dynamic_control.test_core import *

from .urdf.test_urdf import *

from .range_sensor.test_lidar import *

from .domain_randomizer.test_domain_randomizer import *

from .step_importer.test_step_importer import *

# linux only for now
from sys import platform
import carb

if platform == "linux" or platform == "linux2":
    from .motion_planning.test_motion_planning import *
    from .samples.test_ur10_samples import *
    from .robot_engine_bridge.test_core import *

    # try:
    #     import capnp
    # except (ImportError, ModuleNotFoundError):
    #     carb.log_warn("pycapnp not installed, please install to run pyalice tests")
    #     capnp = None
    # if capnp is not None:
    #     from .robot_engine_bridge.test_pyalice import *
