// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <vector>

#define MAX_TENSOR_DIMENSIONS 8

#ifndef TORCH_EXTENSION_NAME
#    define TORCH_EXTENSION_NAME Py_TorchWrap
#endif

// FIXME - move to common include location to avoid duplicate header

enum PyTorchTensorDataType
{
    PYTORCH_FLOAT32,
    PYTORCH_DOUBLE64,
    PYTORCH_INT32,
    PYTORCH_UINT8
};

enum PyTorchTensorDeviceType
{
    PYTORCH_CUDA,
    PYTORCH_CPU
};

template <typename T>
struct PyTorchTensor
{
    int numDimensions = 0;
    int dimensions[MAX_TENSOR_DIMENSIONS];
    int dataType = PyTorchTensorDataType::PYTORCH_FLOAT32;
    int device = PyTorchTensorDeviceType::PYTORCH_CPU;
    int numStrides = 0;
    int strides[MAX_TENSOR_DIMENSIONS];
    T* data;
};
