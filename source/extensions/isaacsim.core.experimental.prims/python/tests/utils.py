# Copyright (c) 2021-2025, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import numpy as np
import warp as wp


def check_array(
    x: wp.array,
    shape: list[int] | None = None,
    dtype: type | None = None,
    device: str | wp.context.Device | None = None,
):
    assert isinstance(x, wp.array), f"{repr(x)} ({type(x)}) is not a Warp array"
    if shape is not None:
        assert tuple(x.shape) == tuple(shape), f"Unexpected shape: expected {shape}, got {x.shape}"
    if dtype is not None:
        assert x.dtype == dtype, f"Unexpected dtype: expected {dtype}, got {x.dtype}"
    if device is not None:
        assert x.device == wp.get_device(device), f"Unexpected device: expected {device}, got {x.device}"


def check_equal(a: np.ndarray, b: np.ndarray, *, msg: str = ""):
    assert a.shape == b.shape, f"Unexpected shape: expected {a.shape}, got {b.shape}\n{msg}"
    assert (a == b).all(), f"Unexpected value:\nExpected\n{a}\nGot\n{b}\n{msg}"


def check_allclose(a: np.ndarray, b: np.ndarray, *, rtol: float = 1e-03, atol: float = 1e-05, msg: str = ""):
    assert a.shape == b.shape, f"Unexpected shape: expected {a.shape}, got {b.shape}\n{msg}"
    assert np.allclose(
        a, b, rtol=rtol, atol=atol
    ), f"Unexpected value (within tolerance):\nExpected\n{a}\nGot\n{b}\n{msg}"


def draw_sample(
    *,
    shape: tuple,
    dtype: type,
    types=[list, np.ndarray, wp.array],
    low: int | float = 0.0,
    high: int | float = 1.0,
    normalized: bool = False,
    transform: callable = None,
):
    samples = []
    for _type in types:
        # sample according to dtype
        if dtype is wp.bool:
            sample = np.random.choice([True, False], size=shape).astype(np.bool_)
        elif dtype is wp.int32:
            sample = np.random.randint(low=low, high=high, size=shape).astype(np.int32)
        elif dtype is wp.uint32:
            sample = np.random.randint(low=low, high=high, size=shape).astype(np.uint32)
        elif dtype is wp.float32:
            sample = np.random.uniform(low=low, high=high, size=shape).astype(np.float32)
            if normalized:
                sample = (sample / np.linalg.norm(sample, axis=-1, keepdims=True)).astype(np.float32)
        else:
            raise ValueError(f"Invalid dtype: {dtype}")
        # apply transform if provided
        if transform:
            sample = transform(sample)
        # create single sample and broadcasted sample
        if sample.ndim == 2:
            single_sample = sample[[0]]
        elif sample.ndim == 3:
            single_sample = sample[[0], [0]]
        else:
            raise ValueError(f"Unsupported dimensionality: {sample.ndim}")
        single_sample_broadcasted = np.broadcast_to(single_sample, shape)
        # create samples
        if _type is list:
            samples.append((single_sample.reshape((shape[-1],)).tolist(), single_sample_broadcasted))
            samples.append((single_sample.reshape((1, shape[-1])).tolist(), single_sample_broadcasted))
            samples.append((sample.tolist(), sample))
        elif _type is np.ndarray:
            samples.append((single_sample.reshape((shape[-1],)).copy(), single_sample_broadcasted))
            samples.append((single_sample.reshape((1, shape[-1])).copy(), single_sample_broadcasted))
            samples.append((sample.copy(), sample))
        elif _type is wp.array:
            samples.append((wp.array(single_sample.reshape((shape[-1],)).copy()), single_sample_broadcasted))
            samples.append((wp.array(single_sample.reshape((1, shape[-1])).copy()), single_sample_broadcasted))
            samples.append((wp.array(sample.copy()), sample))
        else:
            raise ValueError(f"Invalid type: {_type}")
    return samples


def draw_choice(*, shape: tuple, choices: list) -> list:
    sample = np.random.choice(np.array(choices, dtype=object).flatten(), size=shape)
    # create single sample and broadcasted sample
    if sample.ndim == 1:
        single_sample = sample[[0]]
    elif sample.ndim == 2:
        single_sample = sample[[0]]
    else:
        raise ValueError(f"Unsupported dimensionality: {sample.ndim}")
    single_sample_broadcasted = np.broadcast_to(single_sample, shape)
    # create samples
    samples = [
        (single_sample.flatten().tolist(), single_sample_broadcasted.tolist()),
        (single_sample.tolist(), single_sample_broadcasted.tolist()),
        (sample.tolist(), sample.tolist()),
    ]
    return samples


def draw_indices(*, count: int, step: int = 2, types=[list, np.ndarray, wp.array, None]):
    indices = list(range(0, count, step))
    indices_list = []
    for _type in types:
        if _type is list:
            indices_list.append((indices[:], len(indices)))
        elif _type is np.ndarray:
            indices_list.append((np.array(indices), len(indices)))
        elif _type is wp.array:
            indices_list.append((wp.array(indices, dtype=wp.int32, device="cpu"), len(indices)))
        elif _type is None:
            indices_list.append((None, count))
    return indices_list
