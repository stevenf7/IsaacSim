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

"""NumPy-based tensor operations and data manipulation utilities for Isaac Sim."""


import numpy as np


def as_type(data, dtype):
    """Convert data to the specified data type.

    Args:
        data: The input data to convert.
        dtype: Target data type ("float32", "bool", "int32", "int64", "long", "uint8").

    Returns:
        The data converted to the specified type, or None if the type is not supported.
    """
    if dtype == "float32":
        return data.astype(np.float32)
    elif dtype == "bool":
        return data.astype(bool)
    elif dtype == "int32":
        return data.astype(np.int32)
    elif dtype == "int64":
        return data.astype(np.int64)
    elif dtype == "long":
        return data.astype(np.long)
    elif dtype == "uint8":
        return data.astype(np.uint8)
    else:
        print(f"Type {dtype} not supported.")


def convert(data, device=None, dtype="float32", indexed=None):
    """Convert data to a NumPy array with specified data type.

    Args:
        data: Input data to convert.
        device: Device parameter (not used in NumPy implementation).
        dtype: Target data type for conversion.
        indexed: Indexing parameter (not used in current implementation).

    Returns:
        The converted NumPy array with the specified data type.
    """
    return as_type(np.asarray(data), dtype)


def create_zeros_tensor(shape, dtype, device=None):
    """Create a tensor of zeros with specified shape and data type.

    Args:
        shape: Shape of the tensor to create.
        dtype: Data type for the tensor elements.
        device: Device parameter (not used in NumPy implementation).

    Returns:
        A tensor filled with zeros of the specified shape and data type.
    """
    return as_type(np.zeros(shape), dtype)


def create_tensor_from_list(data, dtype, device=None):
    """Create a tensor from a list with specified data type.

    Args:
        data: List data to convert to tensor.
        dtype: Target data type for the tensor.
        device: Device parameter (not used in NumPy implementation).

    Returns:
        A tensor created from the list with the specified data type.
    """
    return as_type(np.array(data), dtype)


def clone_tensor(data, device=None):
    """Create a copy of the input data.

    Args:
        data: The data to clone.
        device: Device parameter (not used in NumPy implementation).

    Returns:
        A copy of the input data.
    """
    return np.copy(data)


def resolve_indices(indices, count, device=None):
    """Resolve indices into a NumPy array format.

    Args:
        indices: Input indices as list, array, or None.
        count: Total count for generating indices when indices is None.
        device: Device parameter (not used in NumPy implementation).

    Returns:
        Resolved indices as a NumPy array.
    """
    result = indices
    if isinstance(indices, list):
        result = np.array(indices)
    if indices is None:
        result = np.arange(count)
    return result


def move_data(data, device=None):
    """Move data to the specified device.

    Args:
        data: Data to move.
        device: Target device (not used in NumPy implementation).

    Returns:
        The input data unchanged.
    """
    return data


def tensor_cat(data, device=None, dim=-1):
    """Concatenate tensors along a specified dimension.

    Args:
        data: List of numpy arrays to concatenate.
        device: Device to place the result on (ignored in numpy backend).
        dim: Dimension along which to concatenate the arrays.

    Returns:
        The concatenated numpy array.
    """
    return np.concatenate(data, axis=dim)


def expand_dims(data, axis):
    """Expand the dimensions of the data array.

    Args:
        data: Input data array.
        axis: Axis along which to expand dimensions.

    Returns:
        Array with expanded dimensions.
    """
    return np.expand_dims(data, axis)


def pad(data, pad_width, mode="constant", value=None):
    """Pad an array with specified padding mode and values.

    Args:
        data: Input array to pad.
        pad_width: Number of values padded to the edges of each axis.
        mode: Padding mode ("constant", "linear_ramp", etc.).
        value: Values to use for padding depending on the mode.

    Returns:
        Padded array.
    """
    if mode == "constant" and value is not None:
        return np.pad(data, pad_width, mode, constant_values=value)
    if mode == "linear_ramp" and value is not None:
        return np.pad(data, pad_width, mode, end_values=value)
    return np.pad(data, pad_width, mode)


def tensor_stack(data, dim=0):
    """Stack tensors along a new dimension.

    Args:
        data: List of numpy arrays to stack.
        dim: Dimension along which to stack the arrays.

    Returns:
        The stacked numpy array.
    """
    return np.stack(data, axis=dim)


def to_list(data):
    """Convert numpy array to list format.

    Args:
        data: Data to convert to list. If already a list, returns unchanged.

    Returns:
        List representation of the input data.
    """
    if not isinstance(data, list):
        return data.tolist()
    return data


def to_numpy(data):
    """Convert data to numpy array format.

    Args:
        data: Data to convert to numpy format.

    Returns:
        The input data unchanged (already in numpy format).
    """
    return data


def assign(src, dst, indices):
    """Assign source data to destination array at specified indices.

    Args:
        src: Source data to assign.
        dst: Destination array to modify.
        indices: Indices where to assign the source data.

    Returns:
        The modified destination array.
    """
    if isinstance(indices, list):
        dst[tuple(indices)] = src
    else:
        dst[indices] = src
    return dst
