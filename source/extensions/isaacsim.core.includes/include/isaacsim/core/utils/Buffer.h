// Copyright (c) 2021-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include "ScopedCudaDevice.h"

#include <carb/cuda/CudaRuntime.h>
#include <carb/cudainterop/CudaInterop.h>

#include <cuda.h>
#include <iostream>
#include <vector>

namespace isaacsim
{
namespace core
{
namespace utils
{

/**
 * @brief Enumeration specifying the type of memory allocation.
 * @details Defines whether the buffer resides in host (CPU) or device (GPU) memory.
 */
enum class eMemoryType
{
    /** @brief Memory allocated in host (CPU) RAM */
    Host = 0,
    /** @brief Memory allocated in device (GPU) VRAM */
    Device = 1,
};

/**
 * @class Buffer
 * @brief Abstract base class for memory buffer management.
 * @details
 * Provides a common interface for managing memory buffers, whether they reside in
 * host (CPU) or device (GPU) memory. This class defines the basic operations that
 * all buffer implementations must support.
 *
 * @tparam T The data type stored in the buffer
 *
 * @note All derived classes must implement resize(), data(), and size() functions
 */
template <typename T>
class Buffer
{
public:
    /** @brief Virtual destructor for proper cleanup of derived classes */
    virtual ~Buffer() = default;

    /**
     * @brief Resizes the buffer to hold the specified number of elements.
     * @param[in] size The new size of the buffer in number of elements
     */
    virtual void resize(size_t size) = 0;

    /**
     * @brief Gets a pointer to the buffer's data.
     * @return Pointer to the buffer's data
     */
    virtual T* data() const = 0;

    /**
     * @brief Gets the number of elements in the buffer.
     * @return Number of elements in the buffer
     */
    virtual size_t size() const = 0;

    /**
     * @brief Gets the size of a single element in bytes.
     * @return Size of type T in bytes
     */
    size_t sizeofType() const
    {
        return sizeof(T);
    }

    /**
     * @brief Gets the total size of the buffer in bytes.
     * @return Total size of the buffer in bytes
     */
    size_t sizeInBytes() const
    {
        return size() * sizeofType();
    }

    /**
     * @brief Gets the memory type of the buffer.
     * @return Memory type (Host or Device)
     */
    eMemoryType type() const
    {
        return mMemoryType;
    }

protected:
    /** @brief Type of memory where the buffer resides */
    eMemoryType mMemoryType;
};

/**
 * @class DeviceBufferBase
 * @brief CUDA device (GPU) memory buffer implementation.
 * @details
 * Manages a buffer of memory allocated on a CUDA device. Provides functionality for:
 * - Memory allocation and deallocation
 * - Device selection and switching
 * - Memory copying between host and device
 * - Debug printing of buffer contents
 *
 * @tparam T The data type stored in the buffer
 *
 * @note Uses RAII principles for automatic resource management
 * @warning Requires proper CUDA environment setup
 */
template <typename T>
class DeviceBufferBase : public Buffer<T>
{
    using Buffer<T>::mMemoryType;

public:
    /**
     * @brief Constructs a new device buffer.
     * @param[in] size Initial size of the buffer in elements (default: 0)
     * @param[in] device CUDA device ID to allocate on (default: -1 for CPU)
     */
    DeviceBufferBase(const size_t& size = 0, const int device = -1)
    {
        mMemoryType = eMemoryType::Device;
        mDevice = device;
        resize(size);
    }

    /**
     * @brief Destructor that ensures proper cleanup of device memory.
     */
    virtual ~DeviceBufferBase()
    {
        ScopedDevice scopedDevice(mDevice);
        CUDA_CHECK(cudaFree(mBuffer));
        mBuffer = nullptr;
    }

    /**
     * @brief Changes the CUDA device for this buffer.
     * @details
     * If the device changes, existing memory is freed on the old device
     * and reallocated on the new device.
     *
     * @param[in] device New CUDA device ID (-1 for CPU)
     */
    virtual void setDevice(const int device = -1)
    {
        if (device != mDevice)
        {
            // if the device doesn't match and we had a buffer allocated, release it on the old device and switch
            if (mBuffer)
            {
                ScopedDevice scopedDevice(mDevice);
                CUDA_CHECK(cudaFree(mBuffer));
                mBuffer = nullptr;
            }
            mDevice = device;
            resize(mSize);
        }
    }

    /**
     * @brief Resizes the device buffer.
     * @details
     * Reallocates memory if the new size is different from the current size.
     * Handles deallocation of existing memory if necessary.
     *
     * @param[in] size New size in number of elements
     */
    virtual void resize(size_t size)
    {
        if ((size != mSize && size > 0) || mBuffer == nullptr)
        {
            ScopedDevice scopedDevice(mDevice);
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

    /**
     * @brief Gets a pointer to the device memory.
     * @return Raw pointer to the device memory
     */
    virtual T* data() const
    {
        return mBuffer;
    }

    /**
     * @brief Gets the current size of the buffer.
     * @return Number of elements in the buffer
     */
    virtual size_t size() const
    {
        return mSize;
    }

    /**
     * @brief Synchronously copies data to the device buffer.
     * @param[in] src Source pointer to copy from
     * @param[in] size Number of elements to copy
     * @param[in] kind Type of memory copy operation
     */
    virtual void copy(const void* src, size_t size, enum cudaMemcpyKind kind = cudaMemcpyDeviceToHost)
    {
        ScopedDevice scopedDevice(mDevice);
        CUDA_CHECK(cudaMemcpy(mBuffer, src, size * sizeof(T), kind));
    }

    /**
     * @brief Asynchronously copies data to the device buffer.
     * @param[in] src Source pointer to copy from
     * @param[in] size Number of elements to copy
     * @param[in] kind Type of memory copy operation
     */
    virtual void copyAsync(const void* src, size_t size, enum cudaMemcpyKind kind = cudaMemcpyDeviceToHost)
    {
        ScopedDevice scopedDevice(mDevice);
        CUDA_CHECK(cudaMemcpyAsync(mBuffer, src, size * sizeof(T), kind));
    }

    /**
     * @brief Prints the buffer contents for debugging.
     * @param[in] start String to print before the buffer contents
     * @param[in] end String to print after the buffer contents
     */
    void debugPrint(const std::string& start, const std::string& end)
    {
        ScopedDevice scopedDevice(mDevice);
        printf("%s", start.c_str());
        std::vector<T> hostBuffer(mSize);
        CUDA_CHECK(cudaMemcpyAsync(hostBuffer.data(), mBuffer, mSize * sizeof(T), cudaMemcpyDeviceToHost));
        for (size_t i; i < mSize; ++i)
        {
            std::cout << hostBuffer[i];
            if (i != mSize - 1)
            {
                std::cout << ", ";
            }
        }
        printf("%s", end.c_str());
    }

private:
    /** @brief Pointer to device memory */
    T* mBuffer = nullptr;
    /** @brief Current size of the buffer in elements */
    size_t mSize = 0;
    /** @brief CUDA device ID where memory is allocated */
    int mDevice = 0;
};

/**
 * @class HostBufferBase
 * @brief Host (CPU) memory buffer implementation.
 * @details
 * Manages a buffer of memory allocated in host RAM using std::vector.
 * Provides a simple wrapper around std::vector with the Buffer interface.
 *
 * @tparam T The data type stored in the buffer
 */
template <typename T>
class HostBufferBase : public Buffer<T>
{
    using Buffer<T>::mMemoryType;

public:
    /**
     * @brief Constructs a new host buffer.
     * @param[in] size Initial size of the buffer in elements (default: 0)
     */
    HostBufferBase(size_t size = 0)
    {
        mMemoryType = eMemoryType::Host;
        resize(size);
    }

    /**
     * @brief Resizes the host buffer.
     * @param[in] size New size in number of elements
     */
    virtual void resize(size_t size)
    {
        mBuffer.resize(size);
    }

    /**
     * @brief Resizes the host buffer and initializes new elements.
     * @param[in] size New size in number of elements
     * @param[in] val Value to initialize new elements with
     */
    virtual void resize(size_t size, const T& val)
    {
        mBuffer.resize(size, val);
    }

    /**
     * @brief Gets a pointer to the host memory.
     * @return Raw pointer to the host memory
     */
    virtual T* data() const
    {
        return (T*)mBuffer.data();
    }

    /**
     * @brief Gets the current size of the buffer.
     * @return Number of elements in the buffer
     */
    virtual size_t size() const
    {
        return mBuffer.size();
    }

    /** @brief Underlying vector storing the data */
    std::vector<T> mBuffer;
};

/** @brief Type alias for a device buffer of bytes */
typedef DeviceBufferBase<uint8_t> DeviceBuffer;
/** @brief Type alias for a host buffer of bytes */
typedef HostBufferBase<uint8_t> HostBuffer;

}
}
}
