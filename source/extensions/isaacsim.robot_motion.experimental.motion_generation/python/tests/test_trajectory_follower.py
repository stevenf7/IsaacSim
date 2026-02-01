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
        trajectory = path.to_minimal_time_joint_trajectory(
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
            )
        )

        # confirm that the trajectory follower has a trajectory:
        self.assertTrue(follower.has_trajectory())

        # by calling forward at t = 0.0, we should get the initial position:
        desired_state = follower.forward(robot_state, None, 0.0)
        self.assertIsNotNone(desired_state)
        self.assertEqual(desired_state.joints.names, ["joint_0"])
        self.assertTrue(np.allclose(desired_state.joints.positions.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(desired_state.joints.velocities.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(desired_state.joints.efforts.numpy(), np.array([0.0])))

        # if we call forward at the end time of the trajectory, we should get the final position:
        desired_state = follower.forward(robot_state, None, trajectory.duration)
        self.assertIsNotNone(desired_state)
        self.assertEqual(desired_state.joints.names, ["joint_0"])
        self.assertTrue(np.allclose(desired_state.joints.positions.numpy(), np.array([2.0])))
        self.assertTrue(np.allclose(desired_state.joints.velocities.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(desired_state.joints.efforts.numpy(), np.array([0.0])))

        # if I set a trajectory, and then I reset,
        # there should be no trajectory.
        follower.set_trajectory(trajectory, 0.0)
        follower.reset(robot_state, None, 0.0)
        self.assertFalse(follower.has_trajectory())

        # if I set a trajectory, and then give a time before the start time of the trajectory, we should get an error,
        # and we will no longer have a set trajectory. The desired state should be None.
        follower.set_trajectory(trajectory, 0.0)
        desired_state = follower.forward(robot_state, None, -1.0)
        self.assertIsNone(desired_state)
        self.assertFalse(follower.has_trajectory())

        # if I give a time after the end-time of the trajectory,
        # we should get None, and there will no longer be a trajectory.
        # the returned desired state is None.
        follower.set_trajectory(trajectory, 0.0)
        desired_state = follower.forward(robot_state, None, trajectory.duration + 1.0)
        self.assertIsNone(desired_state)
        self.assertFalse(follower.has_trajectory())

        # if the trajectory is set with a start_time of 1.0,
        # then we should be at the end of the trajectory at
        # end_time + 1.0. There should still be a trajectory set.
        follower.set_trajectory(trajectory, 1.0)
        desired_state = follower.forward(robot_state, None, trajectory.duration + 1.0)
        self.assertIsNotNone(desired_state)
        self.assertEqual(desired_state.joints.names, ["joint_0"])
        self.assertTrue(np.allclose(desired_state.joints.positions.numpy(), np.array([2.0])))
        self.assertTrue(np.allclose(desired_state.joints.velocities.numpy(), np.array([0.0])))
        self.assertTrue(np.allclose(desired_state.joints.efforts.numpy(), np.array([0.0])))
        self.assertTrue(follower.has_trajectory())
