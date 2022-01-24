// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <carb/cuda/CudaRuntime.h>

#include <cuda.h>
#include <vector>

namespace omni
{
namespace isaac
{
namespace buffer
{
enum class eMemoryType
{
    Host = 0,
    Device = 1,
};


template <typename T>
class Buffer
{
public:
    virtual ~Buffer()
    {
    }
    virtual void resize(size_t size) = 0;
    virtual T* data() const = 0;
    virtual size_t size() const = 0;
    virtual eMemoryType type() const
    {
        return mMemoryType;
    }

protected:
    eMemoryType mMemoryType;
};

template <typename T>
class DeviceBufferBase : public Buffer<T>
{
    using Buffer<T>::mMemoryType;

public:
    DeviceBufferBase(size_t size = 0)
    {
        mMemoryType = eMemoryType::Device;
        resize(size);
    }
    virtual ~DeviceBufferBase()
    {
        CUDA_CHECK(cudaFree(mBuffer));
        mBuffer = nullptr;
    }
    virtual void resize(size_t size)
    {
        if (size != mSize)
        {
            if (mBuffer)
            {
                CUDA_CHECK(cudaFree(mBuffer));
                mBuffer = nullptr;
            }
            if (size > 0)
            {
                CUDA_CHECK(cudaMalloc(&mBuffer, size * sizeof(T)));
            }
            mSize = size;
        }
    }
    virtual T* data() const
    {
        return mBuffer;
    }
    virtual size_t size() const
    {
        return mSize;
    }

private:
    T* mBuffer = nullptr;
    size_t mSize = 0;
};
template <typename T>
class HostBufferBase : public Buffer<T>
{
    using Buffer<T>::mMemoryType;

public:
    HostBufferBase(size_t size = 0)
    {
        mMemoryType = eMemoryType::Host;
        resize(size);
    }
    virtual void resize(size_t size)
    {
        mBuffer.resize(size);
    }
    virtual T* data() const
    {
        return (T*)mBuffer.data();
    }
    virtual size_t size() const
    {
        return mBuffer.size();
    }

    std::vector<T> mBuffer;
};

typedef DeviceBufferBase<uint8_t> DeviceBuffer;
typedef HostBufferBase<uint8_t> HostBuffer;
}
}
}
