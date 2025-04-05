# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
import numpy as np


def matmul(matrix_a, matrix_b):
    return np.matmul(matrix_a, matrix_b)


def sin(data):
    return np.sin(data)


def cos(data):
    return np.cos(data)


def transpose_2d(data):
    return np.transpose(data)


def inverse(data):
    return np.linalg.inv(data)
