# Cross-platform tests
from .utils.test_surface_gripper import *

from .dynamic_control.test_articulation import *
from .dynamic_control.test_pickles import *
from .dynamic_control.test_core import *

from .urdf.test_urdf import *

from .lidar.test_lidar import *

from .domain_randomizer.test_domain_randomizer import *

# linux only for now
from sys import platform

if platform == "linux" or platform == "linux2":
    from .motion_planning.test_motion_planning import *
    from .samples.test_ur10_samples import *
