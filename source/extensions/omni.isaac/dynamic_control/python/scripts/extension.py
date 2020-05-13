import os

import omni.ext
import omni.kit.commands
import omni.kit.editor
import omni.kit.ui
import gc
import omni.physx._physx as omni_physx
from .. import _dynamic_control

# from .test_body import test_body
# from .test_pickles import test_pickles
from .samples.articulation import articulation_info
from .samples.joint_monkey import joint_monkey

# from .test_dofs import test_dofs
# from .joint_monkey import get_joint_monkey
# from .test_attractor import get_test_attractor
# from .test_cartpole import get_cart_pole

# any unit tests for the extension should be imported here
from .tests.test_core import *
from .tests.test_articulation import *
from .tests.test_pickles import *

EXTENSION_NAME = "Dynamic Control"


class Extension(omni.ext.IExt):
    def on_startup(self):
        print("Loading Dynamic Control Extension")
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        self._sample_articulation_info = articulation_info(self._dc)
        self._sample_joint_monkey = joint_monkey(self._dc)

    def on_shutdown(self):
        print("Shutting down Dynamic Control")
        self._sample_articulation_info = None
        self._sample_joint_monkey = None
        _dynamic_control.release_dynamic_control_interface(self._dc)
        gc.collect()
