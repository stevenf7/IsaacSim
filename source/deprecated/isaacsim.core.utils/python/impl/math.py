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

import copy
from typing import Union

import numpy as np


def radians_to_degrees(rad_angles: np.ndarray) -> np.ndarray:
    """Converts input angles from radians to degrees.

    Args:
        rad_angles: Input array of angles (in radians).

    Returns:
        Array of angles in degrees.
    """
    return rad_angles * (180.0 / np.pi)


def cross(a: Union[np.ndarray, list], b: Union[np.ndarray, list]) -> list:
    """Computes the cross-product between two 3-dimensional vectors.

    Args:
        a: A 3-dimensional vector.
        b: A 3-dimensional vector.

    Returns:
        Cross product between input vectors.
    """
    return [a[1] * b[2] - a[2] * b[1], a[0] * b[2] - a[2] * b[0], a[0] * b[1] - a[1] * b[0]]


def normalize(v: np.ndarray) -> np.ndarray:
    """Normalizes the vector inline (and also returns it).

    Args:
        v: The vector to normalize.

    Returns:
        The normalized vector.
    """
    v /= np.linalg.norm(v)
    return v


def normalized(v: np.ndarray | None) -> np.ndarray | None:
    """Returns a normalized copy of the provided vector.

    Args:
        v: The vector to normalize.

    Returns:
        A normalized copy of the vector, or None if input is None.
    """
    if v is None:
        return None
    return normalize(copy.deepcopy(v))
