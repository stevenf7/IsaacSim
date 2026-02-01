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

    async def test_body_state(self):
        # can create a BodyState:
        body_state = BodyState(
            names=["body_0"],
            positions=wp.array([wp.vec3(0.1, 0.0, 0.0)]),
            orientations=wp.array([wp.quat(0.0, 0.0, 0.0, 1.0)]),
            linear_velocities=wp.array([wp.vec3(0.2, 0.0, 0.0)]),
            angular_velocities=wp.array([wp.vec3(0.3, 0.0, 0.0)]),
        )
        self.assertEqual(body_state.names, ["body_0"])
        self.assertTrue(np.allclose(body_state.positions.numpy(), np.array([wp.vec3(0.1, 0.0, 0.0)])))
        self.assertTrue(np.allclose(body_state.orientations.numpy(), np.array([wp.quat(0.0, 0.0, 0.0, 1.0)])))
        self.assertTrue(np.allclose(body_state.linear_velocities.numpy(), np.array([wp.vec3(0.2, 0.0, 0.0)])))
        self.assertTrue(np.allclose(body_state.angular_velocities.numpy(), np.array([wp.vec3(0.3, 0.0, 0.0)])))

        # cannot make a body state with different lengths of names, positions, orientations, linear velocities, and angular velocities
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0", "body_1"],
            positions=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
            orientations=wp.array([wp.quat(0.0, 0.0, 0.0, 1.0)]),
            linear_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
            angular_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
        )
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0", "body_1"],
            positions=wp.array([wp.vec3(0.0, 0.0, 0.0), wp.vec3(0.0, 0.0, 0.0)]),
            orientations=wp.array([wp.quat(0.0, 0.0, 0.0, 1.0)]),
            linear_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
            angular_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0), wp.vec3(0.0, 0.0, 0.0)]),
        )

        # cannot create a body state with incorrect (non-warp) types:
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            positions=np.array([wp.vec3(0.0, 0.0, 0.0)]),
            orientations=np.array([wp.quat(0.0, 0.0, 0.0, 1.0)]),
            linear_velocities=np.array([wp.vec3(0.0, 0.0, 0.0)]),
            angular_velocities=np.array([wp.vec3(0.0, 0.0, 0.0)]),
        )
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            positions=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
            orientations=np.array([wp.quat(0.0, 0.0, 0.0, 1.0)]),
            linear_velocities=np.array([wp.vec3(0.0, 0.0, 0.0)]),
            angular_velocities=np.array([wp.vec3(0.0, 0.0, 0.0)]),
        )
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            positions=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
            orientations=wp.array([wp.quat(0.0, 0.0, 0.0, 1.0)]),
            linear_velocities=np.array([wp.vec3(0.0, 0.0, 0.0)]),
            angular_velocities=np.array([wp.vec3(0.0, 0.0, 0.0)]),
        )
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            positions=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
            orientations=wp.array([wp.quat(0.0, 0.0, 0.0, 1.0)]),
            linear_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
            angular_velocities=np.array([wp.vec3(0.0, 0.0, 0.0)]),
        )
        self.assertRaises(
            ValueError,
            BodyState,
            names=["body_0"],
            positions=[wp.vec3(0.0, 0.0, 0.0)],
            orientations=wp.array([wp.quat(0.0, 0.0, 0.0, 1.0)]),
            linear_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
            angular_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
        )

    async def test_root_state(self):
        # can create a RootState:
        root_state = RootState(
            position=wp.vec3(0.1, 0.0, 0.0),
            orientation=wp.quat(0.0, 0.0, 0.0, 1.0),
            linear_velocity=wp.vec3(0.2, 0.0, 0.0),
            angular_velocity=wp.vec3(0.3, 0.0, 0.0),
        )
        self.assertEqual(root_state.position, wp.vec3(0.1, 0.0, 0.0))
        self.assertEqual(root_state.orientation, wp.quat(0.0, 0.0, 0.0, 1.0))
        self.assertEqual(root_state.linear_velocity, wp.vec3(0.2, 0.0, 0.0))
        self.assertEqual(root_state.angular_velocity, wp.vec3(0.3, 0.0, 0.0))

        # cannot create a root state with incorrect (non-warp) types:
        self.assertRaises(
            ValueError,
            RootState,
            position=[0.0, 0.0, 0.0],
            orientation=wp.quat(0.0, 0.0, 0.0, 1.0),
            linear_velocity=wp.vec3(0.0, 0.0, 0.0),
            angular_velocity=wp.vec3(0.0, 0.0, 0.0),
        )
        self.assertRaises(
            ValueError,
            RootState,
            position=wp.vec3(0.0, 0.0, 0.0),
            orientation=[0.0, 0.0, 0.0, 1.0],
            linear_velocity=wp.vec3(0.0, 0.0, 0.0),
            angular_velocity=wp.vec3(0.0, 0.0, 0.0),
        )
        self.assertRaises(
            ValueError,
            RootState,
            position=wp.vec3(0.0, 0.0, 0.0),
            orientation=wp.quat(0.0, 0.0, 0.0, 1.0),
            linear_velocity=[0.0, 0.0, 0.0],
            angular_velocity=wp.vec3(0.0, 0.0, 0.0),
        )
        self.assertRaises(
            ValueError,
            RootState,
            position=wp.vec3(0.0, 0.0, 0.0),
            orientation=wp.quat(0.0, 0.0, 0.0, 1.0),
            linear_velocity=wp.vec3(0.0, 0.0, 0.0),
            angular_velocity=[0.0, 0.0, 0.0],
        )
        self.assertRaises(
            ValueError,
            RootState,
            position=np.array([0.0, 0.0, 0.0]),
            orientation=wp.quat(0.0, 0.0, 0.0, 1.0),
            linear_velocity=wp.vec3(0.0, 0.0, 0.0),
            angular_velocity=wp.vec3(0.0, 0.0, 0.0),
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
            position=wp.vec3(0.0, 0.0, 0.0),
            orientation=wp.quat(0.0, 0.0, 0.0, 1.0),
            linear_velocity=wp.vec3(0.0, 0.0, 0.0),
            angular_velocity=wp.vec3(0.0, 0.0, 0.0),
        )
        body_state = BodyState(
            names=["body_0"],
            positions=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
            orientations=wp.array([wp.quat(0.0, 0.0, 0.0, 1.0)]),
            linear_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
            angular_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
        )
        tool_frame_state = BodyState(
            names=["tool_0"],
            positions=wp.array([wp.vec3(1.0, 0.0, 0.0)]),
            orientations=wp.array([wp.quat(0.0, 0.0, 0.0, 1.0)]),
            linear_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
            angular_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
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

        # Combining states with parallel joint states is valid:
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

        # combining states which attempt to write to the same joint is invalid:
        state_with_root_1 = mg.RobotState(
            root=mg.RootState(
                position=wp.vec3(1.0, 2.0, 3.0),
                orientation=wp.quat(0.0, 0.0, 0.0, 1.0),
                linear_velocity=wp.vec3(3.0, 4.0, 5.0),
                angular_velocity=wp.vec3(6.0, 7.0, 8.0),
            )
        )
        state_with_root_2 = mg.RobotState(
            root=mg.RootState(
                position=wp.vec3(2.0, 0.0, 0.0),
                orientation=wp.quat(0.0, 0.0, 0.0, 1.0),
                linear_velocity=wp.vec3(9.0, 10.0, 11.0),
                angular_velocity=wp.vec3(12.0, 13.0, 14.0),
            )
        )
        out = combine_robot_states(state_with_root_1, state_with_root_2)
        self.assertIsNone(out)

        # combining when only one defines a root state is valid:
        out = combine_robot_states(state_with_root_1, state_with_joints_1)
        self.assertIsNotNone(out)
        self.assertEqual(out.root.position, wp.vec3(1.0, 2.0, 3.0))
        self.assertEqual(out.root.orientation, wp.quat(0.0, 0.0, 0.0, 1.0))
        self.assertEqual(out.root.linear_velocity, wp.vec3(3.0, 4.0, 5.0))
        self.assertEqual(out.root.angular_velocity, wp.vec3(6.0, 7.0, 8.0))
        self.assertEqual(out.joints.names, ["joint_0"])
        self.assertTrue(np.allclose(out.joints.positions.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(out.joints.velocities.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(out.joints.efforts.numpy(), np.array([0.0])))

        # cominbing when both define different body states is valid:
        state_with_body_1 = mg.RobotState(
            bodies=mg.BodyState(
                names=["body_0"],
                positions=wp.array([wp.vec3(1.0, 2.0, 3.0)]),
                orientations=wp.array([wp.quat(0.0, 0.0, 0.0, 1.0)]),
                linear_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
                angular_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
            )
        )
        state_with_body_2 = mg.RobotState(
            bodies=mg.BodyState(
                names=["body_1"],
                positions=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
                orientations=wp.array([wp.quat(0.0, 0.0, 1.0, 0.0)]),
                linear_velocities=wp.array([wp.vec3(0.0, 1.0, 0.0)]),
                angular_velocities=wp.array([wp.vec3(0.0, 0.0, 1.0)]),
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
        self.assertTrue(np.allclose(output_orientations, np.array([[0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 1.0, 0.0]])))
        self.assertTrue(np.allclose(output_linear_velocities, np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]])))
        self.assertTrue(np.allclose(output_angular_velocities, np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]])))

        # combining when the body states overlap is invalid:
        state_with_body_3 = mg.RobotState(
            bodies=mg.BodyState(
                names=["body_0"],
                positions=wp.array([wp.vec3(1.0, 2.0, 3.0)]),
                orientations=wp.array([wp.quat(0.0, 0.0, 0.0, 1.0)]),
                linear_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
                angular_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
            )
        )
        out = combine_robot_states(state_with_body_1, state_with_body_3)
        self.assertIsNone(out)

        # cominbing when both define different tool frames states is valid:
        state_with_tool_frame_1 = mg.RobotState(
            tool_frames=mg.BodyState(
                names=["tool_frame_0"],
                positions=wp.array([wp.vec3(1.0, 2.0, 3.0)]),
                orientations=wp.array([wp.quat(0.0, 0.0, 0.0, 1.0)]),
                linear_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
                angular_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
            )
        )
        state_with_tool_frame_2 = mg.RobotState(
            tool_frames=mg.BodyState(
                names=["tool_frame_1"],
                positions=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
                orientations=wp.array([wp.quat(0.0, 0.0, 1.0, 0.0)]),
                linear_velocities=wp.array([wp.vec3(0.0, 1.0, 0.0)]),
                angular_velocities=wp.array([wp.vec3(0.0, 0.0, 1.0)]),
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
        self.assertTrue(np.allclose(output_orientations, np.array([[0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 1.0, 0.0]])))
        self.assertTrue(np.allclose(output_linear_velocities, np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]])))
        self.assertTrue(np.allclose(output_angular_velocities, np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]])))

        # combining when tool frame states overlap is invalid:
        state_with_tool_frame_3 = mg.RobotState(
            tool_frames=mg.BodyState(
                names=["tool_frame_0"],
                positions=wp.array([wp.vec3(2.0, 0.0, 0.0)]),
                orientations=wp.array([wp.quat(0.0, 0.0, 0.0, 1.0)]),
                linear_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
                angular_velocities=wp.array([wp.vec3(0.0, 0.0, 0.0)]),
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
        self.assertEqual(out.root.position, wp.vec3(1.0, 2.0, 3.0))
        self.assertEqual(out.root.orientation, wp.quat(0.0, 0.0, 0.0, 1.0))
        self.assertEqual(out.root.linear_velocity, wp.vec3(3.0, 4.0, 5.0))
        self.assertEqual(out.root.angular_velocity, wp.vec3(6.0, 7.0, 8.0))
        self.assertEqual(out.tool_frames.names, ["tool_frame_0"])
        self.assertTrue(np.allclose(out.bodies.positions.numpy(), np.array([1.0, 2.0, 3.0])))
        self.assertTrue(np.allclose(out.bodies.orientations.numpy(), np.array([0.0, 0.0, 0.0, 1.0])))
        self.assertTrue(np.allclose(out.bodies.linear_velocities.numpy(), np.array([0.0, 0.0, 0.0])))
        self.assertTrue(np.allclose(out.bodies.angular_velocities.numpy(), np.array([0.0, 0.0, 0.0])))
