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

# Import extension python module we are testing with absolute import path, as if we are an external user (i.e. a different extension)
import numpy as np
import omni.kit.test
import warp as wp
from isaacsim.robot_motion.experimental.motion_generation import (
    Action,
    BodyState,
    JointState,
    RobotState,
    RootState,
)


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

    async def test_action(self):
        # can create an Action:
        action = Action(
            names=["joint_0"], positions=wp.array([0.1]), velocities=wp.array([0.2]), efforts=wp.array([0.3])
        )
        self.assertEqual(action.names, ["joint_0"])
        self.assertTrue(np.allclose(action.positions.numpy(), np.array([0.1])))
        self.assertTrue(np.allclose(action.velocities.numpy(), np.array([0.2])))
        self.assertTrue(np.allclose(action.efforts.numpy(), np.array([0.3])))

        # cannot make an action with different lengths of names, positions, velocities, and efforts
        self.assertRaises(
            ValueError,
            Action,
            names=["joint_0", "joint_1"],
            positions=wp.array([0.0]),
            velocities=wp.array([0.0]),
            efforts=wp.array([0.0]),
        )
        self.assertRaises(
            ValueError,
            Action,
            names=["joint_0", "joint_1"],
            positions=wp.array([0.0, 1.0]),
            velocities=wp.array([0.0]),
            efforts=wp.array([0.0]),
        )
        self.assertRaises(
            ValueError,
            Action,
            names=["joint_0", "joint_1"],
            positions=wp.array([0.0, 1.0]),
            velocities=wp.array([0.0, 1.0]),
            efforts=wp.array([0.0]),
        )

        # cannot create an action with incorrect (non-warp) types
        self.assertRaises(
            ValueError,
            Action,
            names=["joint_0"],
            positions=np.array([0.0]),
            velocities=np.array([0.0]),
            efforts=np.array([0.0]),
        )
        self.assertRaises(
            ValueError,
            Action,
            names=["joint_0"],
            positions=wp.array([0.0]),
            velocities=np.array([0.0]),
            efforts=np.array([0.0]),
        )
        self.assertRaises(
            ValueError,
            Action,
            names=["joint_0"],
            positions=wp.array([0.0]),
            velocities=wp.array([0.0]),
            efforts=np.array([0.0]),
        )
        self.assertRaises(
            ValueError,
            Action,
            names=["joint_0"],
            positions=[0.0],
            velocities=wp.array([0.0]),
            efforts=np.array([0.0]),
        )

        # can create an Action with any combination of positions, velocities, and efforts
        action = Action(names=["joint_0"], positions=wp.array([0.0]))
        self.assertEqual(action.names, ["joint_0"])
        self.assertTrue(np.allclose(action.positions.numpy(), np.array([0.0])))
        self.assertIsNone(action.velocities)
        self.assertIsNone(action.efforts)
        action = Action(names=["joint_0"], velocities=wp.array([0.0]))
        self.assertEqual(action.names, ["joint_0"])
        self.assertIsNone(action.positions)
        self.assertTrue(np.allclose(action.velocities.numpy(), np.array([0.0])))
        self.assertIsNone(action.efforts)
        action = Action(names=["joint_0"], efforts=wp.array([0.0]))
        self.assertEqual(action.names, ["joint_0"])
        self.assertIsNone(action.positions)
        self.assertIsNone(action.velocities)
        self.assertTrue(np.allclose(action.efforts.numpy(), np.array([0.0])))

        # can create a null Action:
        null_action = Action(names=[])
        self.assertEqual(null_action.names, [])
        self.assertIsNone(null_action.positions)
        self.assertIsNone(null_action.velocities)
        self.assertIsNone(null_action.efforts)
