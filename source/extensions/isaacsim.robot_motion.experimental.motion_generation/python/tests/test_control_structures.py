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
        return not self.should_error

    def forward(
        self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
    ) -> Optional[mg.RobotState]:
        if self.should_error:
            return None
        return mg.RobotState(
            joints=mg.JointState.from_name(
                robot_joint_space=["default", "other"],
                positions=(["default"], wp.array([0.0])),
                velocities=(["default"], wp.array([0.0])),
                efforts=(["default"], wp.array([0.0])),
            )
        )


class OtherController(mg.BaseController):
    def __init__(self):
        self.was_reset = False
        self.should_error = False

    def reset(
        self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
    ) -> bool:
        self.was_reset = True
        return not self.should_error

    def forward(
        self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
    ) -> Optional[mg.RobotState]:
        if self.should_error:
            return None
        return mg.RobotState(
            joints=mg.JointState.from_name(
                robot_joint_space=["default", "other"],
                positions=(["other"], wp.array([1.0])),
                velocities=(["other"], wp.array([1.0])),
                efforts=(["other"], wp.array([1.0])),
            )
        )


class AddOneController(mg.BaseController):
    def reset(
        self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
    ) -> bool:
        return True

    def forward(
        self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
    ) -> Optional[mg.RobotState]:
        if setpoint_state is None:
            return None
        return mg.RobotState(
            joints=mg.JointState.from_name(
                robot_joint_space=setpoint_state.joints.robot_joint_space,
                positions=(
                    setpoint_state.joints.position_names,
                    wp.array(setpoint_state.joints.positions.numpy() + 1.0),
                ),
                velocities=(
                    setpoint_state.joints.velocity_names,
                    wp.array(setpoint_state.joints.velocities.numpy() + 1.0),
                ),
                efforts=(setpoint_state.joints.effort_names, wp.array(setpoint_state.joints.efforts.numpy() + 1.0)),
            )
        )


class AlwaysFailsController(mg.BaseController):

    def reset(
        self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
    ) -> bool:
        return False

    def forward(
        self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
    ) -> Optional[mg.RobotState]:
        return None


class RootController(mg.BaseController):
    def reset(
        self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
    ) -> bool:
        return True

    def forward(
        self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
    ) -> Optional[mg.RobotState]:
        return mg.RobotState(
            root=mg.RootState(
                position=wp.array([1.0, 2.0, 3.0]),
                orientation=wp.array([0.0, 0.0, 0.0, 1.0]),
                linear_velocity=wp.array([0.1, 0.2, 0.3]),
                angular_velocity=wp.array([0.4, 0.5, 0.6]),
            )
        )


class LinkController(mg.BaseController):
    def reset(
        self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
    ) -> bool:
        return True

    def forward(
        self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
    ) -> Optional[mg.RobotState]:
        return mg.RobotState(
            links=mg.SpatialState.from_name(
                spatial_space=["link_a"],
                positions=(["link_a"], wp.array([[0.0, 0.0, 0.0]])),
                orientations=(["link_a"], wp.array([[0.0, 1.0, 0.0, 0.0]])),
                linear_velocities=(["link_a"], wp.array([[0.0, 0.0, 0.0]])),
                angular_velocities=(["link_a"], wp.array([[0.0, 0.0, 0.0]])),
            )
        )


class SiteController(mg.BaseController):
    def reset(
        self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
    ) -> bool:
        return True

    def forward(
        self, estimated_state: mg.RobotState, setpoint_state: Optional[mg.RobotState], t: float, **kwargs
    ) -> Optional[mg.RobotState]:
        return mg.RobotState(
            sites=mg.SpatialState.from_name(
                spatial_space=["site_a"],
                positions=(["site_a"], wp.array([[1.0, 0.0, 0.0]])),
                orientations=(["site_a"], wp.array([[0.0, 0.0, 1.0, 0.0]])),
                linear_velocities=(["site_a"], wp.array([[0.0, 0.0, 0.0]])),
                angular_velocities=(["site_a"], wp.array([[0.0, 0.0, 0.0]])),
            )
        )


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of the module will make it auto-discoverable by omni.kit.test
class TestControlStructures(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        pass

    # After running each test
    async def tearDown(self):
        pass

    async def test_controller_container(self):

        # creating a controller selection enum:
        class ControllerSelection(Enum):
            DEFAULT = 0
            OTHER = 1
            DOES_NOT_EXIST = 2

        # controller container must have at least one controller.
        self.assertRaises(
            ValueError,
            mg.ControllerContainer,
            controller_options={},
            initial_controller_selection=ControllerSelection.DEFAULT,
        )

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
        robot_state = mg.RobotState()

        # create a time:
        t = 0.0

        # reset the controller container:
        success = controller_container.reset(robot_state, None, t)
        self.assertTrue(success)

        # now, the default controller (DEFAULT) should have been reset,
        # but the OTHER controller should not have been reset:
        self.assertTrue(controller_container.get_controller(ControllerSelection.DEFAULT).was_reset)
        self.assertFalse(controller_container.get_controller(ControllerSelection.OTHER).was_reset)
        self.assertEqual(controller_container.get_active_controller_enum(), ControllerSelection.DEFAULT)

        # forward the controller container, confirming that the default is running.
        action = controller_container.forward(robot_state, None, t)
        self.assertIsNotNone(action)
        self.assertEqual(action.joints.position_names, ["default"])
        self.assertEqual(action.joints.velocity_names, ["default"])
        self.assertEqual(action.joints.effort_names, ["default"])
        self.assertTrue(np.allclose(action.joints.position_indices.numpy(), [0]))
        self.assertTrue(np.allclose(action.joints.velocity_indices.numpy(), [0]))
        self.assertTrue(np.allclose(action.joints.effort_indices.numpy(), [0]))
        self.assertTrue(np.allclose(action.joints.positions.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(action.joints.velocities.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(action.joints.efforts.numpy(), np.array([0.0])))

        # if the active controller fails without switching, forward returns None.
        controller_container.get_controller(ControllerSelection.DEFAULT).should_error = True
        action = controller_container.forward(robot_state, None, t)
        self.assertIsNone(action)
        controller_container.get_controller(ControllerSelection.DEFAULT).should_error = False

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
        action = controller_container.forward(robot_state, None, t)

        # the active controller enum should have changed to the OTHER controller:
        self.assertEqual(controller_container.get_active_controller_enum(), ControllerSelection.OTHER)

        # Now both controllers would have had reset called on them:
        self.assertTrue(controller_container.get_controller(ControllerSelection.DEFAULT).was_reset)
        self.assertTrue(controller_container.get_controller(ControllerSelection.OTHER).was_reset)

        # confirming that the OTHER controller is running, and that it did not throw an error.
        self.assertIsNotNone(action)
        self.assertEqual(action.joints.position_names, ["other"])
        self.assertEqual(action.joints.velocity_names, ["other"])
        self.assertEqual(action.joints.effort_names, ["other"])
        self.assertTrue(np.allclose(action.joints.position_indices.numpy(), [1]))
        self.assertTrue(np.allclose(action.joints.velocity_indices.numpy(), [1]))
        self.assertTrue(np.allclose(action.joints.effort_indices.numpy(), [1]))
        self.assertTrue(np.allclose(action.joints.positions.numpy(), np.array([1.0])))
        self.assertTrue(np.allclose(action.joints.velocities.numpy(), np.array([1.0])))
        self.assertTrue(np.allclose(action.joints.efforts.numpy(), np.array([1.0])))

        # arbitrary kwargs can be passed to the forward and reset calls:
        success = controller_container.reset(robot_state, None, t, first_kwarg="string", second_kwarg=None)
        self.assertTrue(success)
        controller_container.set_next_controller(ControllerSelection.OTHER)
        action = controller_container.forward(robot_state, None, t, first_kwarg="string", second_kwarg=None)
        self.assertIsNotNone(action)
        self.assertEqual(action.joints.position_names, ["other"])
        self.assertEqual(action.joints.velocity_names, ["other"])
        self.assertEqual(action.joints.effort_names, ["other"])
        self.assertTrue(np.allclose(action.joints.position_indices.numpy(), [1]))
        self.assertTrue(np.allclose(action.joints.velocity_indices.numpy(), [1]))
        self.assertTrue(np.allclose(action.joints.effort_indices.numpy(), [1]))
        self.assertTrue(np.allclose(action.joints.positions.numpy(), np.array([1.0])))
        self.assertTrue(np.allclose(action.joints.velocities.numpy(), np.array([1.0])))
        self.assertTrue(np.allclose(action.joints.efforts.numpy(), np.array([1.0])))

        # now, say that we should throw an error on the default controller,
        # set the desired controller to be the default controller again,
        # and then call forward again:
        controller_container.get_controller(ControllerSelection.DEFAULT).should_error = True
        controller_container.set_next_controller(ControllerSelection.DEFAULT)

        # attempting to call forward, but having an error while resetting the controller
        # causes an exception to be raised.
        self.assertRaises(RuntimeError, controller_container.forward, robot_state, None, t)

        # attempts to set the next enum, where the enum has not associated controller:
        self.assertRaises(LookupError, controller_container.set_next_controller, ControllerSelection.DOES_NOT_EXIST)

        # attempts to get the controller associated with the non-existant controller:
        self.assertRaises(LookupError, controller_container.get_controller, ControllerSelection.DOES_NOT_EXIST)

        # assert that we can get the controller for controllers that do exist:
        self.assertIsNotNone(controller_container.get_controller(ControllerSelection.DEFAULT))
        self.assertIsNotNone(controller_container.get_controller(ControllerSelection.OTHER))

    async def test_parallel_controller(self):
        # parallel controller must have at least two controllers.
        self.assertRaises(ValueError, mg.ParallelController, controllers=[])
        self.assertRaises(ValueError, mg.ParallelController, controllers=[DefaultController()])

        # create our parallel controller with two different controllers:
        parallel_controller = mg.ParallelController(
            controllers=[DefaultController(), OtherController()],
        )

        empty_robot_state = mg.RobotState()

        # reset the parallel controller:
        success = parallel_controller.reset(empty_robot_state, None, 0.0)
        self.assertTrue(success)

        # forward the parallel controller:
        desired_state = parallel_controller.forward(empty_robot_state, None, 0.0)
        self.assertIsNotNone(desired_state)
        self.assertEqual(desired_state.joints.position_names, ["default", "other"])
        self.assertEqual(desired_state.joints.velocity_names, ["default", "other"])
        self.assertEqual(desired_state.joints.effort_names, ["default", "other"])
        self.assertTrue(np.allclose(desired_state.joints.position_indices.numpy(), [0, 1]))
        self.assertTrue(np.allclose(desired_state.joints.velocity_indices.numpy(), [0, 1]))
        self.assertTrue(np.allclose(desired_state.joints.effort_indices.numpy(), [0, 1]))
        self.assertTrue(np.allclose(desired_state.joints.positions.numpy(), np.array([0.0, 1.0])))
        self.assertTrue(np.allclose(desired_state.joints.velocities.numpy(), np.array([0.0, 1.0])))
        self.assertTrue(np.allclose(desired_state.joints.efforts.numpy(), np.array([0.0, 1.0])))

        # trying to run with two identical controllers will be invalid:
        parallel_controller = mg.ParallelController(
            controllers=[DefaultController(), DefaultController()],
        )
        desired_state = parallel_controller.forward(empty_robot_state, None, 0.0)
        self.assertIsNone(desired_state)

        # if any controller fails, the whole parallel controller will fail:
        parallel_controller = mg.ParallelController(
            controllers=[DefaultController(), AlwaysFailsController()],
        )
        desired_state = parallel_controller.forward(empty_robot_state, None, 0.0)
        self.assertIsNone(desired_state)

        success = parallel_controller.reset(empty_robot_state, None, 0.0)
        self.assertFalse(success)

        # combining root, link, and site outputs in parallel is valid:
        parallel_controller = mg.ParallelController(
            controllers=[RootController(), LinkController(), SiteController()],
        )
        desired_state = parallel_controller.forward(empty_robot_state, None, 0.0)
        self.assertIsNotNone(desired_state)
        self.assertTrue(np.allclose(desired_state.root.position.numpy(), np.array([1.0, 2.0, 3.0])))
        self.assertEqual(desired_state.links.spatial_space, ["link_a"])
        self.assertEqual(desired_state.sites.spatial_space, ["site_a"])
        self.assertTrue(np.allclose(desired_state.links.positions.numpy(), np.array([[0.0, 0.0, 0.0]])))
        self.assertTrue(np.allclose(desired_state.links.orientations.numpy(), np.array([[0.0, 1.0, 0.0, 0.0]])))
        self.assertTrue(np.allclose(desired_state.links.linear_velocities.numpy(), np.array([[0.0, 0.0, 0.0]])))
        self.assertTrue(np.allclose(desired_state.links.angular_velocities.numpy(), np.array([[0.0, 0.0, 0.0]])))
        self.assertTrue(np.allclose(desired_state.sites.positions.numpy(), np.array([[1.0, 0.0, 0.0]])))
        self.assertTrue(np.allclose(desired_state.sites.orientations.numpy(), np.array([[0.0, 0.0, 1.0, 0.0]])))
        self.assertTrue(np.allclose(desired_state.sites.linear_velocities.numpy(), np.array([[0.0, 0.0, 0.0]])))
        self.assertTrue(np.allclose(desired_state.sites.angular_velocities.numpy(), np.array([[0.0, 0.0, 0.0]])))

    async def test_sequential_controller(self):
        # sequential controller must have at least two controllers.
        self.assertRaises(ValueError, mg.SequentialController, controllers=[])
        self.assertRaises(ValueError, mg.SequentialController, controllers=[DefaultController()])

        # create our sequential controller with the add one controller being the final controller.
        sequential_controller = mg.SequentialController(
            controllers=[DefaultController(), AddOneController()],
        )

        empty_robot_state = mg.RobotState()

        # reset the sequential controller:
        success = sequential_controller.reset(empty_robot_state, None, 0.0)
        self.assertTrue(success)

        # forward the sequential controller, all outputs have one added to them.
        desired_state = sequential_controller.forward(empty_robot_state, None, 0.0)
        self.assertIsNotNone(desired_state)
        self.assertEqual(desired_state.joints.position_names, ["default"])
        self.assertEqual(desired_state.joints.velocity_names, ["default"])
        self.assertEqual(desired_state.joints.effort_names, ["default"])
        self.assertTrue(np.allclose(desired_state.joints.position_indices.numpy(), [0]))
        self.assertTrue(np.allclose(desired_state.joints.velocity_indices.numpy(), [0]))
        self.assertTrue(np.allclose(desired_state.joints.effort_indices.numpy(), [0]))
        self.assertTrue(np.allclose(desired_state.joints.positions.numpy(), np.array([1.0])))
        self.assertTrue(np.allclose(desired_state.joints.velocities.numpy(), np.array([1.0])))
        self.assertTrue(np.allclose(desired_state.joints.efforts.numpy(), np.array([1.0])))

        # create our sequential controller with several add one controllers.
        sequential_controller = mg.SequentialController(
            controllers=[
                DefaultController(),
                AddOneController(),
                AddOneController(),
                AddOneController(),
            ],
        )

        empty_robot_state = mg.RobotState()

        # reset the sequential controller:
        success = sequential_controller.reset(empty_robot_state, None, 0.0)
        self.assertTrue(success)

        # forward the sequential controller, all outputs have 3 added to them (from 3 AddOneControllers).
        desired_state = sequential_controller.forward(empty_robot_state, None, 0.0)
        self.assertIsNotNone(desired_state)
        self.assertEqual(desired_state.joints.position_names, ["default"])
        self.assertEqual(desired_state.joints.velocity_names, ["default"])
        self.assertEqual(desired_state.joints.effort_names, ["default"])
        self.assertTrue(np.allclose(desired_state.joints.position_indices.numpy(), [0]))
        self.assertTrue(np.allclose(desired_state.joints.velocity_indices.numpy(), [0]))
        self.assertTrue(np.allclose(desired_state.joints.effort_indices.numpy(), [0]))
        self.assertTrue(np.allclose(desired_state.joints.positions.numpy(), np.array([3.0])))
        self.assertTrue(np.allclose(desired_state.joints.velocities.numpy(), np.array([3.0])))
        self.assertTrue(np.allclose(desired_state.joints.efforts.numpy(), np.array([3.0])))

        # if any controller fails, the whole sequential controller will fail:
        sequential_controller = mg.SequentialController(
            controllers=[DefaultController(), AlwaysFailsController(), AddOneController()],
        )
        desired_state = sequential_controller.forward(empty_robot_state, None, 0.0)
        self.assertIsNone(desired_state)

        success = sequential_controller.reset(empty_robot_state, None, 0.0)
        self.assertFalse(success)
