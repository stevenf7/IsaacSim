// Copyright (c) 2023-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once
#include <carb/cuda/CudaRuntime.h>
#include <carb/logging/Log.h> // CudaRintime.h does not have CARB_LOG_ERROR

#include <cuda.h>

namespace isaacsim
{
namespace core
{
namespace utils
{

/**
 * @class ScopedDevice
 * @brief RAII wrapper for CUDA device context management.
 * @details
 * Provides automatic CUDA device context switching and restoration.
 * When constructed, switches to the specified device (if different from current).
 * When destroyed, restores the previous device context.
 *
 * Key features:
 * - Automatic device context management
 * - Exception-safe device restoration
 * - Support for CPU-only mode (-1 device)
 * - Thread-safe device switching
 *
 * @note Uses RAII pattern to ensure device context is always properly restored
 * @warning CUDA API calls must be error-checked for proper device management
 */
class ScopedDevice
{
public:
    /**
     * @brief Constructs a scoped device context manager.
     * @details
     * Saves the current device and switches to the specified device if different.
     * If device is -1 or CUDA is unavailable, operates in CPU-only mode.
     *
     * @param[in] device CUDA device ID to switch to (-1 for CPU mode)
     *
     * @note Device -1 indicates CPU-only mode
     * @warning Ensure CUDA runtime is initialized before using this class
     */
    ScopedDevice(const int device = -1) : mDevice(device)
    {
        // if we want cpu or can't get a cuda device, then do nothing.
        if (device == -1 || cudaGetDevice(&mOldDevice) != cudaError::cudaSuccess)
        {
            mOldDevice = mDevice = -1;
            return;
        }

        // if we want a device, and its not the current threads host device, then set it.
        if (mDevice != mOldDevice)
        {
            CUDA_CHECK(cudaSetDevice(mDevice));
            // NOTE: what do you want to do with an error here?  set mOldDevice to mDevice so you do nothing in dtor?
        }
    }

    /**
     * @brief Destructor that restores the previous device context.
     * @details
     * Automatically switches back to the original device if a switch was performed.
     * Ensures device context is restored even if exceptions occur.
     */
    ~ScopedDevice()
    {
        // return device back to what we had before if we set earlier
        if (mDevice != mOldDevice)
        {
            CUDA_CHECK(cudaSetDevice(mOldDevice));
        }
    }

private:
    /** @brief Target CUDA device ID (or -1 for CPU mode) */
    int mDevice = 0;
    /** @brief Original CUDA device ID before context switch */
    int mOldDevice = 0;
};

/**
 * @class ScopedCudaTextureObject
 * @brief RAII wrapper for CUDA texture object management.
 * @details
 * Manages the lifecycle of a CUDA texture object, including creation and cleanup.
 * Automatically handles:
 * - Texture object creation from mipmapped arrays
 * - Resource and texture descriptor setup
 * - Automatic cleanup on destruction
 *
 * @note Uses RAII pattern to ensure texture resources are properly freed
 * @warning Requires valid CUDA context when constructed
 */
class ScopedCudaTextureObject final
{
    /** @brief Handle to the CUDA texture object */
    cudaTextureObject_t _texObj = 0;

public:
    /**
     * @brief Constructs a texture object from a mipmapped array.
     * @details
     * Creates a texture object with specified properties:
     * - Clamp address mode
     * - Point filtering
     * - Element-type read mode
     * - Normalized coordinates
     *
     * @param[in] mmarr CUDA mipmapped array handle
     * @param[in] mipLevel Mipmap level to use (default: 0)
     *
     * @note Fails gracefully if input array is invalid
     * @warning Ensure mipmapped array remains valid during object lifetime
     */
    ScopedCudaTextureObject(cudaMipmappedArray_t mmarr, int mipLevel = 0)
    {
        if (!mmarr)
        {
            return;
        }
        cudaArray_t levelArray = 0;
        CUDA_CHECK(cudaGetMipmappedArrayLevel(&levelArray, mmarr, mipLevel));
        if (!levelArray)
        {
            return;
        }
        struct cudaResourceDesc resDesc;
        memset(&resDesc, 0, sizeof(resDesc));
        resDesc.resType = cudaResourceTypeArray;
        resDesc.res.array.array = levelArray;
        struct cudaTextureDesc texDesc;
        memset(&texDesc, 0, sizeof(texDesc));
        texDesc.addressMode[0] = cudaAddressModeClamp;
        texDesc.addressMode[1] = cudaAddressModeClamp;
        texDesc.filterMode = cudaFilterModePoint;
        texDesc.readMode = cudaReadModeElementType;
        texDesc.normalizedCoords = 1;
        CUDA_CHECK(cudaCreateTextureObject(&_texObj, &resDesc, &texDesc, nullptr));
    }

    /**
     * @brief Destructor that cleans up the texture object.
     * @details Automatically destroys the texture object if it was successfully created.
     */
    ~ScopedCudaTextureObject()
    {
        if (_texObj)
        {
            CUDA_CHECK(cudaDestroyTextureObject(_texObj));
        }
    }

    /**
     * @brief Implicit conversion operator to texture object handle.
     * @return Reference to the underlying CUDA texture object
     */
    operator cudaTextureObject_t&()
    {
        return _texObj;
    }
};

}
}
}
