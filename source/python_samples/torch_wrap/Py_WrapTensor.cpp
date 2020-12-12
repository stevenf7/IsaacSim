// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "Py_WrapTensor.h"

#include <torch/csrc/autograd/variable.h>
#include <torch/extension.h>

template <typename T>
torch::Tensor wrapTensor(PyTorchTensor<T>& tensorData)
{
    if (tensorData.numDimensions < 1)
    {
        return torch::autograd::make_variable(torch::Tensor());
    }

    std::vector<int64_t> dimensions;
    for (int i = 0; i < tensorData.numDimensions; ++i)
    {
        dimensions.push_back(tensorData.dimensions[i]);
    }

    std::vector<int64_t> strides;
    for (int i = 0; i < tensorData.numStrides; ++i)
    {
        strides.push_back(tensorData.strides[i]);
    }

    at::DeviceType device;
    at::ScalarType dtype;
    switch (tensorData.device)
    {
    case PyTorchTensorDeviceType::PYTORCH_CUDA:
        device = torch::kCUDA;
        break;
    case PyTorchTensorDeviceType::PYTORCH_CPU:
        device = torch::kCPU;
        break;
    default:
        return torch::autograd::make_variable(torch::Tensor());
    }

    switch (tensorData.dataType)
    {
    case PyTorchTensorDataType::PYTORCH_FLOAT32:
        dtype = torch::kFloat;
        break;
    case PyTorchTensorDataType::PYTORCH_DOUBLE64:
        dtype = torch::kDouble;
        break;
    case PyTorchTensorDataType::PYTORCH_INT32:
        dtype = torch::kInt;
        break;
    case PyTorchTensorDataType::PYTORCH_UINT8:
        dtype = torch::kUInt8;
        break;
    default:
        return torch::autograd::make_variable(torch::Tensor());
    }

    // Pytorch from_blob:
    // https://pytorch.org/cppdocs/api/function_namespacetorch_1aff6f8e6185457b2b67a1a9f292effe6b.html
    return torch::from_blob(tensorData.data, torch::IntArrayRef(dimensions), torch::IntArrayRef(strides),
                            torch::TensorOptions().dtype(dtype).device(device));
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m)
{
    m.def("wrap_tensor", &wrapTensor<float>);
    m.def("wrap_tensor", &wrapTensor<double>);
    m.def("wrap_tensor", &wrapTensor<int32_t>);
    m.def("wrap_tensor", &wrapTensor<uint8_t>);
}
