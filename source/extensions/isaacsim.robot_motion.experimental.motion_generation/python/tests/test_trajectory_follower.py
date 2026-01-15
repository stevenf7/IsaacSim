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
import isaacsim.robot_motion.experimental.motion_generation as mg
import numpy as np
import omni.kit.test
import warp as wp


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of the module will make it auto-discoverable by omni.kit.test
class TestTrajectoryFollower(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        pass

    # After running each test
    async def tearDown(self):
        pass

    async def test_trajectory_follower(self):
        # create a trajectory:
        path = mg.Path(waypoints=np.array([[0.0], [1.0], [2.0]]))
        trajectory = path.to_minimal_time_trajectory(
            max_velocities=np.array([0.5]),
            max_accelerations=np.array([0.1]),
            active_joints=["joint_0"],
        )

        # create a trajectory follower:
        follower = mg.TrajectoryFollower()
        follower.set_trajectory(trajectory, 0.0)

        # create a dummy robot state:
        robot_state = mg.RobotState(
            joints=mg.JointState(
                names=["joint_0"],
                positions=wp.array([0.0]),
                velocities=wp.array([0.0]),
                efforts=wp.array([0.0]),
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

        # confirm that the trajectory follower has a trajectory:
        self.assertTrue(follower.has_trajectory())

        # by calling forward at t = 0.0, we should get the initial position:
        error, action = follower.forward(robot_state, None, 0.0)
        self.assertFalse(error)
        self.assertEqual(action.names, ["joint_0"])
        self.assertTrue(np.allclose(action.positions.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(action.velocities.numpy(), np.array([0.0])))
        self.assertEqual(action.efforts, None)

        # if we call forward at the end time of the trajectory, we should get the final position:
        error, action = follower.forward(robot_state, None, trajectory.duration)
        self.assertFalse(error)
        self.assertEqual(action.names, ["joint_0"])
        self.assertTrue(np.allclose(action.positions.numpy(), np.array([2.0])))
        self.assertTrue(np.allclose(action.velocities.numpy(), np.array([0.0])))
        self.assertEqual(action.efforts, None)

        # if I set a trajectory, and then I reset,
        # there should be no trajectory.
        follower.set_trajectory(trajectory, 0.0)
        follower.reset(robot_state, None, 0.0)
        self.assertFalse(follower.has_trajectory())

        # if I set a trajectory, and then give a time before the start time of the trajectory, we should get an error,
        # and we will no longer have a set trajectory. The action should be a null action.
        follower.set_trajectory(trajectory, 0.0)
        error, action = follower.forward(robot_state, None, -1.0)
        self.assertTrue(error)
        self.assertFalse(follower.has_trajectory())
        self.assertEqual(action.names, [])
        self.assertIsNone(action.positions)
        self.assertIsNone(action.velocities)
        self.assertIsNone(action.efforts)

        # if I give a time after the end-time of the trajectory,
        # we should get an error, and there will no longer be a trajectory.
        # the returned action is the null action.
        follower.set_trajectory(trajectory, 0.0)
        error, action = follower.forward(robot_state, None, trajectory.duration + 1.0)
        self.assertTrue(error)
        self.assertFalse(follower.has_trajectory())
        self.assertIsNone(action.positions)
        self.assertIsNone(action.velocities)
        self.assertIsNone(action.efforts)

        # if the trajectory is set with a start_time of 1.0,
        # then we should be at the end of the trajectory at
        # end_time + 1.0. There should still be a trajectory set.
        follower.set_trajectory(trajectory, 1.0)
        error, action = follower.forward(robot_state, None, trajectory.duration + 1.0)
        self.assertFalse(error)
        self.assertEqual(action.names, ["joint_0"])
        self.assertTrue(np.allclose(action.positions.numpy(), np.array([2.0])))
        self.assertTrue(np.allclose(action.velocities.numpy(), np.array([0.0])))
        self.assertEqual(action.efforts, None)
        self.assertTrue(follower.has_trajectory())
