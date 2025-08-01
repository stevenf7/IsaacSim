# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import math

import isaacsim.core.experimental.utils.transform as transform_utils
import numpy as np
import omni.kit.test
import warp as wp


class TestTransform(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()
        # ---------------
        # Do custom setUp
        # ---------------
        self.tolerance = 1e-6

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        # ------------------
        # Do custom tearDown
        # ------------------
        super().tearDown()

    # --------------------------------------------------------------------

    async def test_rotation_matrix_to_quaternion_single(self):
        """Test rotation_matrix_to_quaternion with single rotation matrix"""
        # Test identity matrix
        identity = np.eye(3)
        result = transform_utils.rotation_matrix_to_quaternion(identity)

        # Check that result is a warp array
        self.assertIsInstance(result, wp.array)
        self.assertEqual(result.shape, (4,))

        # Identity should produce quaternion [1, 0, 0, 0] (w, x, y, z)
        result_np = result.numpy()
        expected = np.array([1.0, 0.0, 0.0, 0.0])
        self.assertTrue(np.allclose(result_np, expected, atol=self.tolerance))

    async def test_rotation_matrix_to_quaternion_batch(self):
        """Test rotation_matrix_to_quaternion with batch of rotation matrices"""
        # Test batch of identity matrices
        batch = np.array([np.eye(3), np.eye(3)], dtype=np.float32)
        result = transform_utils.rotation_matrix_to_quaternion(batch)

        # Check that result is a warp array with correct shape
        self.assertIsInstance(result, wp.array)
        self.assertEqual(result.shape, (2, 4))

        # Check that all quaternions are unit quaternions
        result_np = result.numpy()
        norms = np.linalg.norm(result_np, axis=1)
        expected_norms = np.ones(2)
        self.assertTrue(np.allclose(norms, expected_norms, atol=self.tolerance))

    async def test_euler_angles_to_rotation_matrix_single(self):
        """Test euler_angles_to_rotation_matrix with single Euler angles"""
        # Test zero rotation
        euler = [0.0, 0.0, 0.0]
        result = transform_utils.euler_angles_to_rotation_matrix(euler)

        # Check that result is a warp array
        self.assertIsInstance(result, wp.array)
        self.assertEqual(result.shape, (3, 3))

        # Should produce identity matrix
        result_np = result.numpy()
        expected = np.eye(3)
        self.assertTrue(np.allclose(result_np, expected, atol=self.tolerance))

    async def test_euler_angles_to_rotation_matrix_batch(self):
        """Test euler_angles_to_rotation_matrix with batch of Euler angles"""
        # Test batch of zero rotations
        euler_batch = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=np.float32)
        result = transform_utils.euler_angles_to_rotation_matrix(euler_batch)

        # Check that result is a warp array with correct shape
        self.assertIsInstance(result, wp.array)
        self.assertEqual(result.shape, (2, 3, 3))

        # Check that all matrices are orthogonal (det = 1)
        result_np = result.numpy()
        for i in range(2):
            det = np.linalg.det(result_np[i])
            self.assertAlmostEqual(det, 1.0, places=5)

    async def test_euler_angles_to_quaternion_single(self):
        """Test euler_angles_to_quaternion with single Euler angles"""
        # Test zero rotation
        euler = [0.0, 0.0, 0.0]
        result = transform_utils.euler_angles_to_quaternion(euler)

        # Check that result is a warp array
        self.assertIsInstance(result, wp.array)
        self.assertEqual(result.shape, (4,))

        # Should produce identity quaternion [1, 0, 0, 0]
        result_np = result.numpy()
        expected = np.array([1.0, 0.0, 0.0, 0.0])
        self.assertTrue(np.allclose(result_np, expected, atol=self.tolerance))

    async def test_euler_angles_to_quaternion_batch(self):
        """Test euler_angles_to_quaternion with batch of Euler angles"""
        # Test batch of zero rotations
        euler_batch = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=np.float32)
        result = transform_utils.euler_angles_to_quaternion(euler_batch)

        # Check that result is a warp array with correct shape
        self.assertIsInstance(result, wp.array)
        self.assertEqual(result.shape, (2, 4))

        # Check that all quaternions are unit quaternions
        result_np = result.numpy()
        norms = np.linalg.norm(result_np, axis=1)
        expected_norms = np.ones(2)
        self.assertTrue(np.allclose(norms, expected_norms, atol=self.tolerance))

    async def test_degrees_vs_radians(self):
        """Test that degrees and radians produce consistent results"""
        # Test conversion consistency for zero rotation
        euler_deg = [0.0, 0.0, 0.0]
        euler_rad = [0.0, 0.0, 0.0]

        # Test rotation matrix
        result_deg = transform_utils.euler_angles_to_rotation_matrix(euler_deg, degrees=True)
        result_rad = transform_utils.euler_angles_to_rotation_matrix(euler_rad, degrees=False)

        self.assertTrue(np.allclose(result_deg.numpy(), result_rad.numpy(), atol=self.tolerance))

        # Test quaternion
        result_deg = transform_utils.euler_angles_to_quaternion(euler_deg, degrees=True)
        result_rad = transform_utils.euler_angles_to_quaternion(euler_rad, degrees=False)

        self.assertTrue(np.allclose(result_deg.numpy(), result_rad.numpy(), atol=self.tolerance))

    async def test_basic_mathematical_properties(self):
        """Test basic mathematical properties of the results"""
        # Test identity rotation
        euler = [0.0, 0.0, 0.0]

        # Test rotation matrix properties
        rotation_matrix = transform_utils.euler_angles_to_rotation_matrix(euler)
        R = rotation_matrix.numpy()

        # Check that it's close to identity
        identity = np.eye(3)
        self.assertTrue(np.allclose(R, identity, atol=self.tolerance))

        # Check determinant is 1
        det = np.linalg.det(R)
        self.assertAlmostEqual(det, 1.0, places=5)

        # Test quaternion properties
        quaternion = transform_utils.euler_angles_to_quaternion(euler)
        q = quaternion.numpy()

        # Check that it's a unit quaternion
        norm = np.linalg.norm(q)
        self.assertAlmostEqual(norm, 1.0, places=5)

    async def test_quaternion_multiplication_single(self):
        """Test quaternion_multiplication with single quaternions"""
        # Test identity quaternion multiplication
        identity = [1.0, 0.0, 0.0, 0.0]
        result = transform_utils.quaternion_multiplication(identity, identity)

        # Check that result is a warp array
        self.assertIsInstance(result, wp.array)
        self.assertEqual(result.shape, (4,))

        # Identity * Identity should be identity
        result_numpy = result.numpy()
        expected = np.array([1.0, 0.0, 0.0, 0.0])
        self.assertTrue(np.allclose(result_numpy, expected, atol=self.tolerance))

    async def test_quaternion_multiplication_batch(self):
        """Test quaternion_multiplication with batch of quaternions"""
        # Test batch of identity quaternions
        identity_batch = np.array([[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]], dtype=np.float32)
        result = transform_utils.quaternion_multiplication(identity_batch, identity_batch)

        # Check that result is a warp array with correct shape
        self.assertIsInstance(result, wp.array)
        self.assertEqual(result.shape, (2, 4))

        # Check that all results are unit quaternions
        result_numpy = result.numpy()
        norms = np.linalg.norm(result_numpy, axis=1)
        expected_norms = np.ones(2)
        self.assertTrue(np.allclose(norms, expected_norms, atol=self.tolerance))

    async def test_quaternion_conjugate_single(self):
        """Test quaternion_conjugate with single quaternion"""
        # Test with a rotation around X axis
        quaternion = [0.7071, 0.7071, 0.0, 0.0]  # 90 degrees around X
        result = transform_utils.quaternion_conjugate(quaternion)

        # Check that result is a warp array
        self.assertIsInstance(result, wp.array)
        self.assertEqual(result.shape, (4,))

        # Conjugate should negate vector components
        result_numpy = result.numpy()
        expected = np.array([0.7071, -0.7071, 0.0, 0.0])
        self.assertTrue(np.allclose(result_numpy, expected, atol=self.tolerance))

    async def test_quaternion_conjugate_batch(self):
        """Test quaternion_conjugate with batch of quaternions"""
        # Test batch of rotations
        quaternion_batch = np.array(
            [[0.7071, 0.7071, 0.0, 0.0], [0.7071, 0.0, 0.7071, 0.0]],  # 90 degrees around X  # 90 degrees around Y
            dtype=np.float32,
        )
        result = transform_utils.quaternion_conjugate(quaternion_batch)

        # Check that result is a warp array with correct shape
        self.assertIsInstance(result, wp.array)
        self.assertEqual(result.shape, (2, 4))

        # Check that all results are unit quaternions
        result_numpy = result.numpy()
        norms = np.linalg.norm(result_numpy, axis=1)
        expected_norms = np.ones(2)
        self.assertTrue(np.allclose(norms, expected_norms, atol=self.tolerance))

    async def test_quaternion_multiplication_associativity(self):
        """Test that quaternion multiplication is associative"""
        # Test (first_quaternion * second_quaternion) * third_quaternion = first_quaternion * (second_quaternion * third_quaternion)
        first_quaternion = np.array([0.7071, 0.7071, 0.0, 0.0])  # 90 deg around X
        second_quaternion = np.array([0.7071, 0.0, 0.7071, 0.0])  # 90 deg around Y
        third_quaternion = np.array([0.7071, 0.0, 0.0, 0.7071])  # 90 deg around Z

        # Compute (first_quaternion * second_quaternion) * third_quaternion
        quaternion_first_second = transform_utils.quaternion_multiplication(first_quaternion, second_quaternion)
        quaternion_result_left = transform_utils.quaternion_multiplication(quaternion_first_second, third_quaternion)

        # Compute first_quaternion * (second_quaternion * third_quaternion)
        quaternion_second_third = transform_utils.quaternion_multiplication(second_quaternion, third_quaternion)
        quaternion_result_right = transform_utils.quaternion_multiplication(first_quaternion, quaternion_second_third)

        # Results should be equal
        self.assertTrue(
            np.allclose(quaternion_result_left.numpy(), quaternion_result_right.numpy(), atol=self.tolerance)
        )

    async def test_input_types(self):
        """Test that different input types work correctly for all transform functions"""
        # Test euler_angles_to_quaternion with different input types
        euler_list = [0.0, 0.0, 0.0]
        euler_numpy = np.array([0.0, 0.0, 0.0])
        euler_warp = wp.array(euler_numpy)

        result_list = transform_utils.euler_angles_to_quaternion(euler_list)
        result_numpy = transform_utils.euler_angles_to_quaternion(euler_numpy)
        result_warp = transform_utils.euler_angles_to_quaternion(euler_warp)

        # All results should be approximately equal
        self.assertTrue(np.allclose(result_list.numpy(), result_numpy.numpy(), atol=self.tolerance))
        self.assertTrue(np.allclose(result_numpy.numpy(), result_warp.numpy(), atol=self.tolerance))

        # Test quaternion functions with different input types
        quaternion_list = [1.0, 0.0, 0.0, 0.0]
        quaternion_numpy = np.array([1.0, 0.0, 0.0, 0.0])
        quaternion_warp = wp.array(quaternion_numpy)

        # Test quaternion_multiplication
        result_list_multiplication = transform_utils.quaternion_multiplication(quaternion_list, quaternion_list)
        result_numpy_multiplication = transform_utils.quaternion_multiplication(quaternion_numpy, quaternion_numpy)
        result_warp_multiplication = transform_utils.quaternion_multiplication(quaternion_warp, quaternion_warp)

        self.assertTrue(
            np.allclose(result_list_multiplication.numpy(), result_numpy_multiplication.numpy(), atol=self.tolerance)
        )
        self.assertTrue(
            np.allclose(result_numpy_multiplication.numpy(), result_warp_multiplication.numpy(), atol=self.tolerance)
        )

        # Test quaternion_conjugate
        result_list_conjugate = transform_utils.quaternion_conjugate(quaternion_list)
        result_numpy_conjugate = transform_utils.quaternion_conjugate(quaternion_numpy)
        result_warp_conjugate = transform_utils.quaternion_conjugate(quaternion_warp)

        self.assertTrue(np.allclose(result_list_conjugate.numpy(), result_numpy_conjugate.numpy(), atol=self.tolerance))
        self.assertTrue(np.allclose(result_numpy_conjugate.numpy(), result_warp_conjugate.numpy(), atol=self.tolerance))
