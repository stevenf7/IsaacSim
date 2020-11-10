#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np


def torch_isin(tensor, test_elements):
    """PyTorch version of the numpy `is1d` function
    https://github.com/numpy/numpy/blob/v1.17.0/numpy/lib/arraysetops.py#L484

    Test whether each elements of `tensor` are also present in `test_elements`.

    Returns:
        Bool array of same shape as `tensor` with values `True` if the
        corresponding tensor element is also found in `test_elements`.
    """

    import torch
    import torch.nn.functional as F

    ar1, rev_idx = torch.unique(tensor, return_inverse=True)
    ar2 = torch.unique(test_elements)

    ar = torch.cat((ar1, ar2))

    # Pytorch argsort is not stable, must use numpy with 'mergesort'.
    order = ar.cpu().numpy().argsort(kind="mergesort")
    sar = ar[order]

    bool_ar = sar[1:] == sar[:-1]

    flag = F.pad(bool_ar, (0, 1), value=False)
    ret = torch.zeros(ar.shape, dtype=bool, device=ar.device)
    ret[order] = flag

    return ret[rev_idx]


def to_numpy(data):
    """Helper to ensure data is on the CPU as a numpy array.
        """
    if isinstance(data, np.ndarray):
        return data
    elif type(data).__name__ == "Tensor":
        return data.cpu().numpy()
    else:
        raise ValueError(f"Unable to convert to numpy data of type {type(data)}.")
