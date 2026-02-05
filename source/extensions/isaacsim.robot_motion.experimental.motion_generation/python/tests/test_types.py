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

import isaacsim.robot_motion.experimental.motion_generation as mg

# Import extension python module we are testing with absolute import path, as if we are an external user (i.e. a different extension)
import numpy as np
import omni.kit.test
import warp as wp
from isaacsim.robot_motion.experimental.motion_generation import (
    BodyState,
    JointState,
    RobotState,
    RootState,
)
from isaacsim.robot_motion.experimental.motion_generation.impl.controller_structures import combine_robot_states


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of the module will make it auto-discoverable by omni.kit.test
class TestTypes(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        pass

    # After running each test
    async def tearDown(self):
        pass

    async def test_joint_state(self):
        # can create a JointState:
        joint_state = JointState(
            names=["joint_0"], positions=wp.array([0.0]), velocities=wp.array([0.0]), efforts=wp.array([0.0])
        )

        # cannot make a joint state with different lengths of names, positions, velocities, and efforts
        self.assertRaises(
            ValueError,
            JointState,
            names=["joint_0", "joint_1"],
            positions=wp.array([0.0]),
            velocities=wp.array([0.0]),
            efforts=wp.array([0.0]),
        )
        self.assertRaises(
            ValueError,
            JointState,
            names=["joint_0", "joint_1"],
            positions=wp.array([0.0, 1.0]),
            velocities=wp.array([0.0]),
            efforts=wp.array([0.0]),
        )
        self.assertRaises(
            ValueError,
            JointState,
            names=["joint_0", "joint_1"],
            positions=wp.array([0.0, 1.0]),
            velocities=wp.array([0.0, 1.0]),
            efforts=wp.array([0.0]),
        )

        # cannot create a joint state with incorrect (non-warp) types
        self.assertRaises(
            ValueError,
            JointState,
            names=["joint_0"],
            positions=np.array([0.0]),
            velocities=np.array([0.0]),
            efforts=np.array([0.0]),
        )
        self.assertRaises(
            ValueError,
            JointState,
            names=["joint_0"],
            positions=wp.array([0.0]),
            velocities=np.array([0.0]),
            efforts=np.array([0.0]),
        )
        self.assertRaises(
            ValueError,
            JointState,
            names=["joint_0"],
            positions=wp.array([0.0]),
            velocities=wp.array([0.0]),
            efforts=np.array([0.0]),
        )
        self.assertRaises(
            ValueError,
            JointState,
            names=["joint_0"],
            positions=[0.0],
            velocities=wp.array([0.0]),
            efforts=np.array([0.0]),
        )

        # we can build partial joint-states:
        only_positions = JointState(
            names=["joint_0"],
            positions=wp.array([0.0]),
        )
        only_velocities = JointState(
            names=["joint_0"],
            velocities=wp.array([0.0]),
        )
        only_efforts = JointState(
            names=["joint_0"],
            efforts=wp.array([0.0]),
        )

        # cannot build a joint state with no entries:
        self.assertRaises(
            ValueError,
            JointState,
            names=[],
            positions=wp.array([]),
            velocities=wp.array([]),
            efforts=wp.array([]),
        )

    async def test_body_state(self):
        # can create a BodyState:
        body_state = BodyState(
            names=["body_0"],
            positions=wp.array([[0.1, 0.0, 0.0]]),
            orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
            linear_velocities=wp.array([[0.2, 0.0, 0.0]]),
            angular_velocities=wp.array([[0.3, 0.0, 0.0]]),
        )
        self.assertEqual(body_state.names, ["body_0"])
        self.assertTrue(np.allclose(body_state.positions.numpy(), np.array([[0.1, 0.0, 0.0]])))
        self.assertTrue(np.allclose(body_state.orientations.numpy(), np.array([[1.0, 0.0, 0.0, 0.0]])))
        self.assertTrue(np.allclose(body_state.linear_velocities.numpy(), np.array([[0.2, 0.0, 0.0]])))
        self.assertTrue(np.allclose(body_state.angular_velocities.numpy(), np.array([[0.3, 0.0, 0.0]])))

        # cannot make a body state with different lengths of names, positions, orientations, linear velocities, and angular velocities
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0", "body_1"],
            positions=wp.array([[0.0, 0.0, 0.0]]),
            orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
            linear_velocities=wp.array([[0.0, 0.0, 0.0]]),
            angular_velocities=wp.array([[0.0, 0.0, 0.0]]),
        )
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0", "body_1"],
            positions=wp.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]),
            orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
            linear_velocities=wp.array([[0.0, 0.0, 0.0]]),
            angular_velocities=wp.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]),
        )

        # cannot create a body state with incorrect (non-warp) types:
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            positions=np.array([[0.0, 0.0, 0.0]]),
            orientations=np.array([[1.0, 0.0, 0.0, 0.0]]),
            linear_velocities=np.array([[0.0, 0.0, 0.0]]),
            angular_velocities=np.array([[0.0, 0.0, 0.0]]),
        )
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            positions=wp.array([[0.0, 0.0, 0.0]]),
            orientations=np.array([[1.0, 0.0, 0.0, 0.0]]),
            linear_velocities=np.array([[0.0, 0.0, 0.0]]),
            angular_velocities=np.array([[0.0, 0.0, 0.0]]),
        )
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            positions=wp.array([[0.0, 0.0, 0.0]]),
            orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
            linear_velocities=np.array([[0.0, 0.0, 0.0]]),
            angular_velocities=np.array([[0.0, 0.0, 0.0]]),
        )
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            positions=wp.array([[0.0, 0.0, 0.0]]),
            orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
            linear_velocities=wp.array([[0.0, 0.0, 0.0]]),
            angular_velocities=np.array([[0.0, 0.0, 0.0]]),
        )
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            positions=[[0.0, 0.0, 0.0]],
            orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
            linear_velocities=wp.array([[0.0, 0.0, 0.0]]),
            angular_velocities=wp.array([[0.0, 0.0, 0.0]]),
        )

        # we can build partial body-states:
        only_positions = BodyState(
            names=["body_0"],
            positions=wp.array([[0.0, 0.0, 0.0]]),
        )
        only_orientations = BodyState(
            names=["body_0"],
            orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
        )
        only_linear_velocities = BodyState(
            names=["body_0"],
            linear_velocities=wp.array([[0.0, 0.0, 0.0]]),
        )
        only_angular_velocities = BodyState(
            names=["body_0"],
            angular_velocities=wp.array([[0.0, 0.0, 0.0]]),
        )

        # cannot build a body state with no entries:
        self.assertRaises(
            ValueError,
            BodyState,
            names=[],
            positions=wp.array([[]]),
            orientations=wp.array([[]]),
            linear_velocities=wp.array([[]]),
            angular_velocities=wp.array([[]]),
        )

    async def test_root_state(self):
        # can create a RootState:
        root_state = RootState(
            position=wp.array([0.1, 0.0, 0.0]),
            orientation=wp.array([1.0, 0.0, 0.0, 0.0]),
            linear_velocity=wp.array([0.2, 0.0, 0.0]),
            angular_velocity=wp.array([0.3, 0.0, 0.0]),
        )
        self.assertTrue(np.allclose(root_state.position.numpy(), np.array([0.1, 0.0, 0.0])))
        self.assertTrue(np.allclose(root_state.orientation.numpy(), np.array([1.0, 0.0, 0.0, 0.0])))
        self.assertTrue(np.allclose(root_state.linear_velocity.numpy(), np.array([0.2, 0.0, 0.0])))
        self.assertTrue(np.allclose(root_state.angular_velocity.numpy(), np.array([0.3, 0.0, 0.0])))

        # cannot create a root state with incorrect (non-warp) types:
        self.assertRaises(
            ValueError,
            RootState,
            position=[0.0, 0.0, 0.0],
            orientation=wp.array([1.0, 0.0, 0.0, 0.0]),
            linear_velocity=wp.array([0.0, 0.0, 0.0]),
            angular_velocity=wp.array([0.0, 0.0, 0.0]),
        )
        self.assertRaises(
            ValueError,
            RootState,
            position=wp.array([0.0, 0.0, 0.0]),
            orientation=[1.0, 0.0, 0.0, 0.0],
            linear_velocity=wp.array([0.0, 0.0, 0.0]),
            angular_velocity=wp.array([0.0, 0.0, 0.0]),
        )
        self.assertRaises(
            ValueError,
            RootState,
            position=wp.array([0.0, 0.0, 0.0]),
            orientation=wp.array([1.0, 0.0, 0.0, 0.0]),
            linear_velocity=[0.0, 0.0, 0.0],
            angular_velocity=wp.array([0.0, 0.0, 0.0]),
        )
        self.assertRaises(
            ValueError,
            RootState,
            position=wp.array([0.0, 0.0, 0.0]),
            orientation=wp.array([1.0, 0.0, 0.0, 0.0]),
            linear_velocity=wp.array([0.0, 0.0, 0.0]),
            angular_velocity=[0.0, 0.0, 0.0],
        )
        self.assertRaises(
            ValueError,
            RootState,
            position=np.array([0.0, 0.0, 0.0]),
            orientation=wp.array([1.0, 0.0, 0.0, 0.0]),
            linear_velocity=wp.array([0.0, 0.0, 0.0]),
            angular_velocity=wp.array([0.0, 0.0, 0.0]),
        )

        # we can build partial root-states:
        only_position = RootState(
            position=wp.array([0.0, 0.0, 0.0]),
        )
        only_orientation = RootState(
            orientation=wp.array([1.0, 0.0, 0.0, 0.0]),
        )
        only_linear_velocity = RootState(
            linear_velocity=wp.array([0.0, 0.0, 0.0]),
        )
        only_angular_velocity = RootState(
            angular_velocity=wp.array([0.0, 0.0, 0.0]),
        )

        # cannot build a root state with all None entries:
        self.assertRaises(
            ValueError,
            RootState,
            position=None,
            orientation=None,
            linear_velocity=None,
            angular_velocity=None,
        )

        # cannot build a root state with the wrong types:
        self.assertRaises(
            ValueError,
            RootState,
            position=wp.array([[]]),
            orientation=wp.array([[]]),
            linear_velocity=wp.array([[]]),
            angular_velocity=wp.array([[]]),
        )

    async def test_robot_state(self):
        # create valid component states for testing
        joint_state = JointState(
            names=["joint_0", "joint_1"],
            positions=wp.array([0.0, 1.0]),
            velocities=wp.array([0.0, 0.0]),
            efforts=wp.array([0.0, 0.0]),
        )
        root_state = RootState(
            position=wp.array([0.0, 0.0, 0.0]),
            orientation=wp.array([1.0, 0.0, 0.0, 0.0]),
            linear_velocity=wp.array([0.0, 0.0, 0.0]),
            angular_velocity=wp.array([0.0, 0.0, 0.0]),
        )
        body_state = BodyState(
            names=["body_0"],
            positions=wp.array([[0.0, 0.0, 0.0]]),
            orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
            linear_velocities=wp.array([[0.0, 0.0, 0.0]]),
            angular_velocities=wp.array([[0.0, 0.0, 0.0]]),
        )
        tool_frame_state = BodyState(
            names=["tool_0"],
            positions=wp.array([[1.0, 0.0, 0.0]]),
            orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
            linear_velocities=wp.array([[0.0, 0.0, 0.0]]),
            angular_velocities=wp.array([[0.0, 0.0, 0.0]]),
        )

        # can create a RobotState with all components:
        robot_state = RobotState(
            joints=joint_state,
            root=root_state,
            bodies=body_state,
            tool_frames=tool_frame_state,
        )
        self.assertEqual(robot_state.joints, joint_state)
        self.assertEqual(robot_state.root, root_state)
        self.assertEqual(robot_state.bodies, body_state)
        self.assertEqual(robot_state.tool_frames, tool_frame_state)

        # can create a RobotState with joints only:
        robot_state = RobotState(joints=joint_state)
        self.assertEqual(robot_state.joints, joint_state)
        self.assertIsNone(robot_state.root)
        self.assertIsNone(robot_state.bodies)
        self.assertIsNone(robot_state.tool_frames)

        # can create a RobotState root only:
        robot_state = RobotState(root=root_state)
        self.assertIsNone(robot_state.joints)
        self.assertEqual(robot_state.root, root_state)
        self.assertIsNone(robot_state.bodies)
        self.assertIsNone(robot_state.tool_frames)

        # can create a RobotState bodies only:
        robot_state = RobotState(bodies=body_state)
        self.assertIsNone(robot_state.joints)
        self.assertIsNone(robot_state.root)
        self.assertEqual(robot_state.bodies, body_state)
        self.assertIsNone(robot_state.tool_frames)

        # can create a RobotState tool_frames only:
        robot_state = RobotState(tool_frames=tool_frame_state)
        self.assertIsNone(robot_state.joints)
        self.assertIsNone(robot_state.root)
        self.assertIsNone(robot_state.bodies)
        self.assertEqual(robot_state.tool_frames, tool_frame_state)

        # can create an empty RobotState:
        robot_state = RobotState()
        self.assertIsNone(robot_state.joints)
        self.assertIsNone(robot_state.root)
        self.assertIsNone(robot_state.bodies)
        self.assertIsNone(robot_state.tool_frames)

    async def test_combine_robot_states(self):
        # If either robot state is None, return is None:
        empty_state = mg.RobotState()
        out = combine_robot_states(empty_state, None)
        self.assertIsNone(out)
        out = combine_robot_states(None, empty_state)
        self.assertIsNone(out)
        out = combine_robot_states(None, None)
        self.assertIsNone(out)
        out = combine_robot_states(empty_state, empty_state)
        self.assertIsNotNone(out)

        # Combining states with non-overlapping joint states is valid:
        state_with_joints_1 = mg.RobotState(
            joints=mg.JointState(
                names=["joint_0"], positions=wp.array([0.0]), velocities=wp.array([0.0]), efforts=wp.array([0.0])
            )
        )
        state_with_joints_2 = mg.RobotState(
            joints=mg.JointState(
                names=["joint_1"], positions=wp.array([1.0]), velocities=wp.array([1.0]), efforts=wp.array([1.0])
            )
        )
        out = combine_robot_states(state_with_joints_1, state_with_joints_2)
        self.assertIsNotNone(out)
        self.assertEqual(out.joints.names, ["joint_0", "joint_1"])
        self.assertTrue(np.allclose(out.joints.positions.numpy(), np.array([0.0, 1.0])))
        self.assertTrue(np.allclose(out.joints.velocities.numpy(), np.array([0.0, 1.0])))
        self.assertTrue(np.allclose(out.joints.efforts.numpy(), np.array([0.0, 1.0])))

        out = combine_robot_states(empty_state, state_with_joints_1)
        self.assertIsNotNone(out)
        self.assertEqual(out.joints.names, ["joint_0"])
        self.assertTrue(np.allclose(out.joints.positions.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(out.joints.velocities.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(out.joints.efforts.numpy(), np.array([0.0])))

        out = combine_robot_states(state_with_joints_2, empty_state)
        self.assertIsNotNone(out)
        self.assertEqual(out.joints.names, ["joint_1"])
        self.assertTrue(np.allclose(out.joints.positions.numpy(), np.array([1.0])))
        self.assertTrue(np.allclose(out.joints.velocities.numpy(), np.array([1.0])))
        self.assertTrue(np.allclose(out.joints.efforts.numpy(), np.array([1.0])))

        # combining states which attempt to write to the same joint is invalid:
        state_with_joint_overlap = mg.RobotState(
            joints=mg.JointState(
                names=["joint_0"],
                positions=wp.array([2.0]),
                velocities=wp.array([2.0]),
                efforts=wp.array([2.0]),
            )
        )
        out = combine_robot_states(state_with_joints_1, state_with_joint_overlap)
        self.assertIsNone(out)

        # combining states which both fully define the root-state is invalid.
        state_with_root_1 = mg.RobotState(
            root=mg.RootState(
                position=wp.array([1.0, 2.0, 3.0]),
                orientation=wp.array([1.0, 0.0, 0.0, 0.0]),
                linear_velocity=wp.array([3.0, 4.0, 5.0]),
                angular_velocity=wp.array([6.0, 7.0, 8.0]),
            )
        )
        state_with_root_2 = mg.RobotState(
            root=mg.RootState(
                position=wp.array([2.0, 0.0, 0.0]),
                orientation=wp.array([1.0, 0.0, 0.0, 0.0]),
                linear_velocity=wp.array([9.0, 10.0, 11.0]),
                angular_velocity=wp.array([12.0, 13.0, 14.0]),
            )
        )
        out = combine_robot_states(state_with_root_1, state_with_root_2)
        self.assertIsNone(out)

        # combining when only one defines a root state is valid:
        out = combine_robot_states(state_with_root_1, state_with_joints_1)
        self.assertIsNotNone(out)
        self.assertTrue(np.allclose(out.root.position.numpy(), np.array([1.0, 2.0, 3.0])))
        self.assertTrue(np.allclose(out.root.orientation.numpy(), np.array([1.0, 0.0, 0.0, 0.0])))
        self.assertTrue(np.allclose(out.root.linear_velocity.numpy(), np.array([3.0, 4.0, 5.0])))
        self.assertTrue(np.allclose(out.root.angular_velocity.numpy(), np.array([6.0, 7.0, 8.0])))
        self.assertEqual(out.joints.names, ["joint_0"])
        self.assertTrue(np.allclose(out.joints.positions.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(out.joints.velocities.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(out.joints.efforts.numpy(), np.array([0.0])))

        # cominbing when both define different body states is valid:
        state_with_body_1 = mg.RobotState(
            bodies=mg.BodyState(
                names=["body_0"],
                positions=wp.array([[1.0, 2.0, 3.0]]),
                orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
                linear_velocities=wp.array([[0.0, 0.0, 0.0]]),
                angular_velocities=wp.array([[0.0, 0.0, 0.0]]),
            )
        )
        state_with_body_2 = mg.RobotState(
            bodies=mg.BodyState(
                names=["body_1"],
                positions=wp.array([[0.0, 0.0, 0.0]]),
                orientations=wp.array([[0.0, 0.0, 1.0, 0.0]]),
                linear_velocities=wp.array([[0.0, 1.0, 0.0]]),
                angular_velocities=wp.array([[0.0, 0.0, 1.0]]),
            )
        )
        out = combine_robot_states(state_with_body_1, state_with_body_2)
        self.assertIsNotNone(out)

        output_positions = np.array(out.bodies.positions.numpy(), dtype=np.float32)
        output_orientations = np.array(out.bodies.orientations.numpy(), dtype=np.float32)
        output_linear_velocities = np.array(out.bodies.linear_velocities.numpy(), dtype=np.float32)
        output_angular_velocities = np.array(out.bodies.angular_velocities.numpy(), dtype=np.float32)

        self.assertEqual(out.bodies.names, ["body_0", "body_1"])
        self.assertTrue(np.allclose(output_positions, np.array([[1.0, 2.0, 3.0], [0.0, 0.0, 0.0]])))
        self.assertTrue(np.allclose(output_orientations, np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]])))
        self.assertTrue(np.allclose(output_linear_velocities, np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]])))
        self.assertTrue(np.allclose(output_angular_velocities, np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]])))

        # combining when the body states overlap is invalid:
        state_with_body_3 = mg.RobotState(
            bodies=mg.BodyState(
                names=["body_0"],
                positions=wp.array([[1.0, 2.0, 3.0]]),
                orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
                linear_velocities=wp.array([[0.0, 0.0, 0.0]]),
                angular_velocities=wp.array([[0.0, 0.0, 0.0]]),
            )
        )
        out = combine_robot_states(state_with_body_1, state_with_body_3)
        self.assertIsNone(out)

        # cominbing when both define different tool frames states is valid:
        state_with_tool_frame_1 = mg.RobotState(
            tool_frames=mg.BodyState(
                names=["tool_frame_0"],
                positions=wp.array([[1.0, 2.0, 3.0]]),
                orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
                linear_velocities=wp.array([[0.0, 0.0, 0.0]]),
                angular_velocities=wp.array([[0.0, 0.0, 0.0]]),
            )
        )
        state_with_tool_frame_2 = mg.RobotState(
            tool_frames=mg.BodyState(
                names=["tool_frame_1"],
                positions=wp.array([[0.0, 0.0, 0.0]]),
                orientations=wp.array([[0.0, 0.0, 1.0, 0.0]]),
                linear_velocities=wp.array([[0.0, 1.0, 0.0]]),
                angular_velocities=wp.array([[0.0, 0.0, 1.0]]),
            )
        )
        out = combine_robot_states(state_with_tool_frame_1, state_with_tool_frame_2)
        self.assertIsNotNone(out)

        output_positions = np.array(out.tool_frames.positions.numpy(), dtype=np.float32)
        output_orientations = np.array(out.tool_frames.orientations.numpy(), dtype=np.float32)
        output_linear_velocities = np.array(out.tool_frames.linear_velocities.numpy(), dtype=np.float32)
        output_angular_velocities = np.array(out.tool_frames.angular_velocities.numpy(), dtype=np.float32)

        self.assertEqual(out.tool_frames.names, ["tool_frame_0", "tool_frame_1"])
        self.assertTrue(np.allclose(output_positions, np.array([[1.0, 2.0, 3.0], [0.0, 0.0, 0.0]])))
        self.assertTrue(np.allclose(output_orientations, np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]])))
        self.assertTrue(np.allclose(output_linear_velocities, np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]])))
        self.assertTrue(np.allclose(output_angular_velocities, np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]])))

        # combining when tool frame states overlap is invalid:
        state_with_tool_frame_3 = mg.RobotState(
            tool_frames=mg.BodyState(
                names=["tool_frame_0"],
                positions=wp.array([[2.0, 0.0, 0.0]]),
                orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
                linear_velocities=wp.array([[0.0, 0.0, 0.0]]),
                angular_velocities=wp.array([[0.0, 0.0, 0.0]]),
            )
        )
        out = combine_robot_states(state_with_tool_frame_1, state_with_tool_frame_3)
        self.assertIsNone(out)

        # We can combine all of these different types of states together:
        out = combine_robot_states(state_with_body_1, state_with_joints_1)
        out = combine_robot_states(out, state_with_root_1)
        out = combine_robot_states(out, state_with_tool_frame_1)
        self.assertIsNotNone(out)
        self.assertEqual(out.bodies.names, ["body_0"])
        self.assertEqual(out.joints.names, ["joint_0"])
        self.assertTrue(np.allclose(out.root.position.numpy(), np.array([1.0, 2.0, 3.0])))
        self.assertTrue(np.allclose(out.root.orientation.numpy(), np.array([1.0, 0.0, 0.0, 0.0])))
        self.assertTrue(np.allclose(out.root.linear_velocity.numpy(), np.array([3.0, 4.0, 5.0])))
        self.assertTrue(np.allclose(out.root.angular_velocity.numpy(), np.array([6.0, 7.0, 8.0])))
        self.assertEqual(out.tool_frames.names, ["tool_frame_0"])
        self.assertTrue(np.allclose(out.bodies.positions.numpy(), np.array([1.0, 2.0, 3.0])))
        self.assertTrue(np.allclose(out.bodies.orientations.numpy(), np.array([1.0, 0.0, 0.0, 0.0])))
        self.assertTrue(np.allclose(out.bodies.linear_velocities.numpy(), np.array([0.0, 0.0, 0.0])))
        self.assertTrue(np.allclose(out.bodies.angular_velocities.numpy(), np.array([0.0, 0.0, 0.0])))

    async def test_combine_robot_state_with_nonoverlapping_fields(self):
        # I can combine two robot states if they define exactly
        # the same joints, as long as no fields are overlapping:
        robot_state_1 = mg.RobotState(
            joints=mg.JointState(
                names=["joint_0"],
                velocities=wp.array([0.0]),
                efforts=wp.array([0.0]),
            )
        )
        robot_state_2 = mg.RobotState(
            joints=mg.JointState(
                names=["joint_0"],
                positions=wp.array([1.0]),
            )
        )

        out = combine_robot_states(robot_state_1, robot_state_2)
        self.assertIsNotNone(out)
        self.assertEqual(out.joints.names, ["joint_0"])
        self.assertTrue(np.allclose(out.joints.positions.numpy(), np.array([1.0])))
        self.assertTrue(np.allclose(out.joints.velocities.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(out.joints.efforts.numpy(), np.array([0.0])))

        # I cannot do the same with partial overlap in joints:
        robot_state_3 = mg.RobotState(
            joints=mg.JointState(
                names=["joint_0", "joint_1"],
                positions=wp.array([0.0, 1.0]),
            )
        )
        out = combine_robot_states(robot_state_1, robot_state_3)
        self.assertIsNone(out)

    async def test_joint_state_rejects_2d_arrays(self):
        # JointState should reject 2D warp arrays (must be 1D)
        self.assertRaises(
            ValueError,
            JointState,
            names=["joint_0"],
            positions=wp.array([[0.0]]),  # 2D array, should fail
        )
        self.assertRaises(
            ValueError,
            JointState,
            names=["joint_0"],
            velocities=wp.array([[0.0]]),  # 2D array, should fail
        )
        self.assertRaises(
            ValueError,
            JointState,
            names=["joint_0"],
            efforts=wp.array([[0.0]]),  # 2D array, should fail
        )

    async def test_body_state_shape_validation(self):
        # BodyState positions must have shape[1] == 3
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            positions=wp.array([[0.0, 0.0]]),  # shape is (1, 2), not (1, 3)
        )
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            positions=wp.array([[0.0, 0.0, 0.0, 0.0]]),  # shape is (1, 4), not (1, 3)
        )

        # BodyState orientations must have shape[1] == 4
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            orientations=wp.array([[0.0, 0.0, 0.0]]),  # shape is (1, 3), not (1, 4)
        )
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            orientations=wp.array([[0.0, 0.0, 0.0, 0.0, 0.0]]),  # shape is (1, 5), not (1, 4)
        )

        # BodyState linear_velocities must have shape[1] == 3
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            linear_velocities=wp.array([[0.0, 0.0]]),  # shape is (1, 2), not (1, 3)
        )

        # BodyState angular_velocities must have shape[1] == 3
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            angular_velocities=wp.array([[0.0, 0.0, 0.0, 0.0]]),  # shape is (1, 4), not (1, 3)
        )

    async def test_combine_root_states_with_nonoverlapping_fields(self):
        # We can combine two root states if they define non-overlapping fields
        state_with_position = mg.RobotState(root=mg.RootState(position=wp.array([1.0, 2.0, 3.0])))
        state_with_orientation = mg.RobotState(root=mg.RootState(orientation=wp.array([1.0, 0.0, 0.0, 0.0])))

        out = combine_robot_states(state_with_position, state_with_orientation)
        self.assertIsNotNone(out)
        self.assertTrue(np.allclose(out.root.position.numpy(), np.array([1.0, 2.0, 3.0])))
        self.assertTrue(np.allclose(out.root.orientation.numpy(), np.array([1.0, 0.0, 0.0, 0.0])))
        self.assertIsNone(out.root.linear_velocity)
        self.assertIsNone(out.root.angular_velocity)

        # We can combine all four root fields from different states:
        state_with_linear_velocity = mg.RobotState(root=mg.RootState(linear_velocity=wp.array([4.0, 5.0, 6.0])))
        state_with_angular_velocity = mg.RobotState(root=mg.RootState(angular_velocity=wp.array([7.0, 8.0, 9.0])))

        out = combine_robot_states(state_with_position, state_with_orientation)
        out = combine_robot_states(out, state_with_linear_velocity)
        out = combine_robot_states(out, state_with_angular_velocity)
        self.assertIsNotNone(out)
        self.assertTrue(np.allclose(out.root.position.numpy(), np.array([1.0, 2.0, 3.0])))
        self.assertTrue(np.allclose(out.root.orientation.numpy(), np.array([1.0, 0.0, 0.0, 0.0])))
        self.assertTrue(np.allclose(out.root.linear_velocity.numpy(), np.array([4.0, 5.0, 6.0])))
        self.assertTrue(np.allclose(out.root.angular_velocity.numpy(), np.array([7.0, 8.0, 9.0])))

    async def test_combine_body_states_with_nonoverlapping_fields(self):
        # We can combine two body states on the same bodies if they define non-overlapping fields
        body_state_with_positions = mg.RobotState(
            bodies=mg.BodyState(
                names=["body_0"],
                positions=wp.array([[1.0, 2.0, 3.0]]),
            )
        )
        body_state_with_orientations = mg.RobotState(
            bodies=mg.BodyState(
                names=["body_0"],
                orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
            )
        )

        out = combine_robot_states(body_state_with_positions, body_state_with_orientations)
        self.assertIsNotNone(out)
        self.assertEqual(out.bodies.names, ["body_0"])
        self.assertTrue(np.allclose(out.bodies.positions.numpy(), np.array([[1.0, 2.0, 3.0]])))
        self.assertTrue(np.allclose(out.bodies.orientations.numpy(), np.array([[1.0, 0.0, 0.0, 0.0]])))
        self.assertIsNone(out.bodies.linear_velocities)
        self.assertIsNone(out.bodies.angular_velocities)

        # Same test for tool_frames:
        tool_frame_with_positions = mg.RobotState(
            tool_frames=mg.BodyState(
                names=["tool_0"],
                positions=wp.array([[1.0, 2.0, 3.0]]),
            )
        )
        tool_frame_with_orientations = mg.RobotState(
            tool_frames=mg.BodyState(
                names=["tool_0"],
                orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
            )
        )

        out = combine_robot_states(tool_frame_with_positions, tool_frame_with_orientations)
        self.assertIsNotNone(out)
        self.assertEqual(out.tool_frames.names, ["tool_0"])
        self.assertTrue(np.allclose(out.tool_frames.positions.numpy(), np.array([[1.0, 2.0, 3.0]])))
        self.assertTrue(np.allclose(out.tool_frames.orientations.numpy(), np.array([[1.0, 0.0, 0.0, 0.0]])))

    async def test_combine_body_states_fails_with_mismatched_fields(self):
        # When combining body states with different names, they must define the same fields.
        # This should fail because body_0 defines positions but body_1 defines orientations.
        body_state_with_positions = mg.RobotState(
            bodies=mg.BodyState(
                names=["body_0"],
                positions=wp.array([[1.0, 2.0, 3.0]]),
            )
        )
        body_state_with_orientations = mg.RobotState(
            bodies=mg.BodyState(
                names=["body_1"],
                orientations=wp.array([[1.0, 0.0, 0.0, 0.0]]),
            )
        )

        out = combine_robot_states(body_state_with_positions, body_state_with_orientations)
        self.assertIsNone(out)

        # Same test for tool_frames:
        tool_frame_with_linear_velocities = mg.RobotState(
            tool_frames=mg.BodyState(
                names=["tool_0"],
                linear_velocities=wp.array([[1.0, 2.0, 3.0]]),
            )
        )
        tool_frame_with_angular_velocities = mg.RobotState(
            tool_frames=mg.BodyState(
                names=["tool_1"],
                angular_velocities=wp.array([[4.0, 5.0, 6.0]]),
            )
        )

        out = combine_robot_states(tool_frame_with_linear_velocities, tool_frame_with_angular_velocities)
        self.assertIsNone(out)

    async def test_combine_joint_states_fails_with_mismatched_fields(self):
        # When combining joint states with different names, they must define the same fields.
        # This should fail because joint_0 defines positions but joint_1 defines velocities.
        joint_state_with_positions = mg.RobotState(
            joints=mg.JointState(
                names=["joint_0"],
                positions=wp.array([0.0]),
            )
        )
        joint_state_with_velocities = mg.RobotState(
            joints=mg.JointState(
                names=["joint_1"],
                velocities=wp.array([1.0]),
            )
        )

        out = combine_robot_states(joint_state_with_positions, joint_state_with_velocities)
        self.assertIsNone(out)

        # Also test positions vs efforts mismatch:
        joint_state_with_efforts = mg.RobotState(
            joints=mg.JointState(
                names=["joint_2"],
                efforts=wp.array([2.0]),
            )
        )

        out = combine_robot_states(joint_state_with_positions, joint_state_with_efforts)
        self.assertIsNone(out)
