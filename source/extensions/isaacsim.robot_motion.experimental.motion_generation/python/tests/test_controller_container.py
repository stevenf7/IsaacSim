# SPDX-FileCopyrightText: Copyright (c) 2021-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from enum import Enum
from typing import Optional

# Import extension python module we are testing with absolute import path, as if we are an external user (i.e. a different extension)
import isaacsim.robot_motion.experimental.motion_generation as mg
import numpy as np
import omni.kit.test
import warp as wp


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of the module will make it auto-discoverable by omni.kit.test
class TestControllerContainer(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        pass

    # After running each test
    async def tearDown(self):
        pass

    async def test_controller_container(self):
        # creating two dummy controller classes.
        # we can control whether or not they throw errors.
        # we can also see whether or not they were reset.
        class DefaultController(mg.BaseController):
            def __init__(self):
                self.was_reset = False
                self.should_error = False

            def reset(
                self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
            ) -> bool:
                self.was_reset = True
                return self.should_error

            def forward(
                self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
            ) -> tuple[bool, mg.Action]:
                return self.should_error, mg.Action(
                    names=["default"],
                    positions=wp.array([0.0]),
                    velocities=wp.array([0.0]),
                    efforts=wp.array([0.0]),
                )

        class OtherController(mg.BaseController):
            def __init__(self):
                self.was_reset = False
                self.should_error = False

            def reset(
                self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
            ) -> bool:
                self.was_reset = True
                return self.should_error

            def forward(
                self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
            ) -> tuple[bool, mg.Action]:
                return self.should_error, mg.Action(
                    names=["other"],
                    positions=wp.array([1.0]),
                    velocities=wp.array([1.0]),
                    efforts=wp.array([1.0]),
                )

        # creating a controller selection enum:
        class ControllerSelection(Enum):
            DEFAULT = 0
            OTHER = 1
            DOES_NOT_EXIST = 2

        # create a controller container:
        controller_container = mg.ControllerContainer(
            controller_options={
                ControllerSelection.DEFAULT: DefaultController(),
                ControllerSelection.OTHER: OtherController(),
            },
            initial_controller_selection=ControllerSelection.DEFAULT,
        )

        # before running either controller, we should get that they have
        # not been reset:
        self.assertFalse(controller_container.get_controller(ControllerSelection.DEFAULT).was_reset)
        self.assertFalse(controller_container.get_controller(ControllerSelection.OTHER).was_reset)

        # create a robot state:
        robot_state = mg.RobotState(
            joints=mg.JointState(
                names=[],
                positions=wp.array([]),
                velocities=wp.array([]),
                efforts=wp.array([]),
            ),
            root=mg.RootState(
                position=wp.vec3(0.0, 0.0, 0.0),
                orientation=wp.quat(0.0, 0.0, 0.0, 1.0),
                linear_velocity=wp.vec3(0.0, 0.0, 0.0),
                angular_velocity=wp.vec3(0.0, 0.0, 0.0),
            ),
            bodies=mg.BodyState(
                names=[],
                positions=wp.array([]),
                orientations=wp.array([]),
                linear_velocities=wp.array([]),
                angular_velocities=wp.array([]),
            ),
        )

        # create a time:
        t = 0.0

        # reset the controller container:
        error = controller_container.reset(robot_state, None, t)
        self.assertFalse(error)

        # now, the default controller (DEFAULT) should have been reset,
        # but the OTHER controller should not have been reset:
        self.assertTrue(controller_container.get_controller(ControllerSelection.DEFAULT).was_reset)
        self.assertFalse(controller_container.get_controller(ControllerSelection.OTHER).was_reset)
        self.assertEqual(controller_container.get_active_controller_enum(), ControllerSelection.DEFAULT)

        # forward the controller container, confirming that the default is running.
        error, action = controller_container.forward(robot_state, None, t)
        self.assertFalse(error)
        self.assertEqual(action.names, ["default"])
        self.assertTrue(np.allclose(action.positions.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(action.velocities.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(action.efforts.numpy(), np.array([0.0])))

        # The controller resets should still not have changed:
        self.assertTrue(controller_container.get_controller(ControllerSelection.DEFAULT).was_reset)
        self.assertFalse(controller_container.get_controller(ControllerSelection.OTHER).was_reset)

        # change the controller to be the OTHER controller:
        controller_container.set_next_controller(ControllerSelection.OTHER)

        # The controller resets should still not have changed,
        # since the next controller will be reset on the next forward call:
        self.assertTrue(controller_container.get_controller(ControllerSelection.DEFAULT).was_reset)
        self.assertFalse(controller_container.get_controller(ControllerSelection.OTHER).was_reset)

        # the active controller enum should still not have changed, since we haven't called forward yet:
        self.assertEqual(controller_container.get_active_controller_enum(), ControllerSelection.DEFAULT)

        # forward the controller container:
        error, action = controller_container.forward(robot_state, None, t)

        # the active controller enum should have changed to the OTHER controller:
        self.assertEqual(controller_container.get_active_controller_enum(), ControllerSelection.OTHER)

        # Now both controllers would have had reset called on them:
        self.assertTrue(controller_container.get_controller(ControllerSelection.DEFAULT).was_reset)
        self.assertTrue(controller_container.get_controller(ControllerSelection.OTHER).was_reset)

        # confirming that the OTHER controller is running, and that it did not throw an error.
        self.assertFalse(error)
        self.assertEqual(action.names, ["other"])
        self.assertTrue(np.allclose(action.positions.numpy(), np.array([1.0])))
        self.assertTrue(np.allclose(action.velocities.numpy(), np.array([1.0])))
        self.assertTrue(np.allclose(action.efforts.numpy(), np.array([1.0])))

        # arbitrary kwargs can be passed to the forward and reset calls:
        error = controller_container.reset(robot_state, None, t, first_kwarg="string", second_kwarg=None)
        self.assertFalse(error)
        controller_container.set_next_controller(ControllerSelection.OTHER)
        error, action = controller_container.forward(robot_state, None, t, first_kwarg="string", second_kwarg=None)
        self.assertFalse(error)

        # now, say that we should throw an error on the default controller,
        # set the desired controller to be the default controller again,
        # and then call forward again:
        controller_container.get_controller(ControllerSelection.DEFAULT).should_error = True
        controller_container.set_next_controller(ControllerSelection.DEFAULT)

        # attempting to call forward, but having an error while resetting the controller
        # causes an exception to be raised.
        self.assertRaises(RuntimeError, controller_container.forward, robot_state, None, t)

        # attempts to set the next enum, where the enum has not associated controller:
        self.assertRaises(RuntimeError, controller_container.set_next_controller, ControllerSelection.DOES_NOT_EXIST)

        # attempts to get the controller associated with the non-existant controller:
        self.assertRaises(LookupError, controller_container.get_controller, ControllerSelection.DOES_NOT_EXIST)

        # assert that we can get the controller for controllers that do exist:
        self.assertIsNotNone(controller_container.get_controller(ControllerSelection.DEFAULT))
        self.assertIsNotNone(controller_container.get_controller(ControllerSelection.OTHER))
