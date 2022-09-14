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
#include <carb/logging/Log.h>

#include <cuda.h>
#include <memory>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string>
#include <unordered_map>

namespace omni
{
namespace isaac
{
namespace gxf_bridge
{

// Enumerates the type of memory isaac can return.
typedef enum isaac_memory_type
{
    isaac_memory_none = 0,
    isaac_memory_host = 1,
    isaac_memory_cuda = 2,
} isaac_memory_t;

class IsaacBuffer
{
public:
    virtual ~IsaacBuffer()
    {
    }
    virtual void resize(size_t size) = 0;
    virtual uint8_t* data() const = 0;
    virtual size_t size() const = 0;
    virtual isaac_memory_t type() const
    {
        return mMemoryType;
    }

protected:
    isaac_memory_t mMemoryType;
};

class IsaacDeviceBuffer : public IsaacBuffer
{
public:
    IsaacDeviceBuffer(size_t size = 0)
    {
        mMemoryType = isaac_memory_t::isaac_memory_cuda;
        resize(size);
    }
    virtual ~IsaacDeviceBuffer()
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
                CUDA_CHECK(cudaMalloc(&mBuffer, size));
            }
            mSize = size;
        }
    }
    virtual uint8_t* data() const
    {
        return mBuffer;
    }
    virtual size_t size() const
    {
        return mSize;
    }

private:
    uint8_t* mBuffer = nullptr;
    size_t mSize = 0;
};

class IsaacHostBuffer : public IsaacBuffer
{
public:
    IsaacHostBuffer(size_t size = 0)
    {
        mMemoryType = isaac_memory_t::isaac_memory_host;
        resize(size);
    }
    virtual void resize(size_t size)
    {
        mBuffer.resize(size);
    }
    virtual uint8_t* data() const
    {
        return (uint8_t*)mBuffer.data();
    }
    virtual size_t size() const
    {
        return mBuffer.size();
    }

    std::vector<uint8_t> mBuffer;
};


}
}
}
