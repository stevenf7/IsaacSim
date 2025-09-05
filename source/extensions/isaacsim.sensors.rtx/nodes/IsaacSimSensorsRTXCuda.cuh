// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#pragma once

#include "GenericModelOutput.h"
#include "isaacsim/core/includes/Buffer.h"

namespace isaacsim
{
namespace sensors
{
namespace rtx
{

/**
 * @class IsaacExtractRTXSensorPointCloudDeviceBuffers
 * @brief CUDA device buffer management class for RTX sensor point cloud extraction
 * @details
 * Manages CUDA device buffers and resources for processing RTX sensor point cloud data.
 * Handles memory allocation, data transfer, and buffer management for point cloud processing
 * on the GPU. This class is designed to work with NVIDIA RTX sensors and provides
 * efficient point cloud data handling capabilities.
 */
class IsaacExtractRTXSensorPointCloudDeviceBuffers final {
public:
    /** @brief Maximum number of elements that can be processed in a single operation */
    static constexpr uint32_t MAX_ELEMENTS{1000000};

    /** @brief Size of device buffers, set during initialization */
    size_t bufferSize;

    /** @brief Device buffer for Generic Model Output data */
    isaacsim::core::includes::DeviceBufferBase<omni::sensors::GenericModelOutput> gmo;

    /** @brief Device buffer for point cloud data storage */
    isaacsim::core::includes::DeviceBufferBase<float3> pointCloudBuffer;

    /** @brief Device buffer for input valid indices */
    isaacsim::core::includes::DeviceBufferBase<size_t> validIndicesIn;

    /** @brief Device buffer for output valid indices */
    isaacsim::core::includes::DeviceBufferBase<size_t> validIndicesOut;

    /** @brief Device buffer for storing the number of valid points */
    isaacsim::core::includes::DeviceBufferBase<size_t> numValidPoints;

    /** @brief Temporary storage buffer for CUDA operations */
    isaacsim::core::includes::DeviceBufferBase<uint8_t> tempStorage;

    /** @brief Device buffer for x coordinates of GMO point cloud, if provided on host */
    isaacsim::core::includes::DeviceBufferBase<float> x;

    /** @brief Device buffer for y coordinates of GMO point cloud, if provided on host */
    isaacsim::core::includes::DeviceBufferBase<float> y;

    /** @brief Device buffer for z coordinates of GMO point cloud, if provided on host */
    isaacsim::core::includes::DeviceBufferBase<float> z;

    /** @brief Device buffer for elementsCoordsType of GMO point cloud, if provided on host */
    isaacsim::core::includes::DeviceBufferBase<omni::sensors::CoordsType> elementsCoordsType;

    /** @brief Device buffer for flags of GMO point cloud, if provided on host */
    isaacsim::core::includes::DeviceBufferBase<uint8_t> flags;

    /** @brief CUDA stream for asynchronous operations */
    cudaStream_t cudaStream;

    /** @brief CUDA device ID */
    int cudaDevice;

    /** @brief Maximum number of threads per CUDA block */
    int maxThreadsPerBlock;

    /** @brief Flag indicating if Generic Model Output is on device */
    bool gmoOnDevice;

    /** @brief Pinned host memory for Generic Model Output data */
    omni::sensors::GenericModelOutput* gmoHostPtr;

    /** @brief Default constructor */
    IsaacExtractRTXSensorPointCloudDeviceBuffers() : bufferSize(0), cudaDevice(0), maxThreadsPerBlock(0), gmoOnDevice(false), gmoHostPtr(nullptr) {}

    /** @brief Default destructor */
    ~IsaacExtractRTXSensorPointCloudDeviceBuffers();

    /** @brief Deleted copy constructor */
    IsaacExtractRTXSensorPointCloudDeviceBuffers(const IsaacExtractRTXSensorPointCloudDeviceBuffers&) = delete;

    /** @brief Deleted copy assignment operator */
    IsaacExtractRTXSensorPointCloudDeviceBuffers& operator=(const IsaacExtractRTXSensorPointCloudDeviceBuffers&) = delete;

    /**
     * @brief Initializes the CUDA device buffers and resources
     * @param[in] dataPtr Pointer to the input data
     * @param[in] cudaStream CUDA stream for asynchronous operations
     * @throws std::runtime_error If CUDA initialization fails
     */
    void initialize(void* dataPtr, cudaStream_t cudaStream);

    /**
     * @brief Initializes the CUDA device buffers and resources
     * @param[in] dataPtr Pointer to the input data
     * @param[in] cudaDeviceIndex Index of the device on which data was originally generated
     * @throws std::runtime_error If CUDA initialization fails
     */
    void initialize(void* dataPtr, int cudaDeviceIndex);

    /**
     * @brief Resizes the device buffers to the current buffer size
     */
    void resizeBuffers();

    /**
     * @brief Resizes the device buffers to the current buffer size
     */
    void resizeBuffersNoStream();

    /**
     * @brief Fills the point cloud buffer with data from the input pointer
     * @param[in] dataPtr Pointer to the input data
     * @param[out] numValidPointsHost Reference to store the number of valid points
     * @param[out] frameAtEndHost Reference to store the GenericModelOutput frame at end of scan
     * @throws std::runtime_error If data transfer or processing fails
     */
    void fillPointCloudBuffer(void* dataPtr, size_t& numValidPointsHost, omni::sensors::FrameAtTime& frameAtEndHost);

};


// Cached version that reuses temp storage to avoid reallocation every frame
void findValidIndices(size_t* dataIn, size_t* dataOut, int* numValidPoints, size_t numPoints, uint8_t* flags, 
                           int cudaDeviceIndex, cudaStream_t stream, void** d_temp_storage, size_t* temp_storage_bytes, int* cached_numPoints);

void fillIndices(size_t* indices, size_t numIndices, int maxThreadsPerBlock, int cudaDeviceIndex, cudaStream_t stream = 0);

size_t getTempStorageSizeForValidIndices(size_t maxPoints, int cudaDeviceIndex);

void fillValidCartesianPoints(float* azimuth, float* elevation, float* range, float3* cartesianPoints, size_t* validIndices, int* numValidPoints, size_t maxPoints, int maxThreadsPerBlock, int multiProcessorCount, int cudaDeviceIndex, cudaStream_t stream);

template <typename T>
void selectValidPoints(T* inData, T* outData, size_t* validIndices, int* numValidPoints, size_t maxPoints, int maxThreadsPerBlock, int cudaDeviceIndex, cudaStream_t stream, size_t stride);

// Fused function for required basic outputs (azimuth, elevation, distance, intensity)
void selectRequiredValidPoints(
    const float* azimuthSrc, const float* elevationSrc, const float* distanceSrc, const float* intensitySrc,
    float* azimuthDst, float* elevationDst, float* distanceDst, float* intensityDst,
    const size_t* validIndices, int* numValidPoints, size_t maxPoints, 
    uint32_t enableMask, int maxThreadsPerBlock, int cudaDeviceIndex, cudaStream_t stream);

// Fused function for optional outputs (timestamp, IDs, normals, velocities)
void selectOptionalValidPoints(
    const int32_t* timestampSrc, const uint32_t* emitterIdSrc, const uint32_t* materialIdSrc, const uint8_t* objectIdSrc,
    const float3* normalSrc, const float3* velocitySrc,
    int32_t* timestampDst, uint32_t* emitterIdDst, uint32_t* materialIdDst, uint8_t* objectIdDst,
    float3* normalDst, float3* velocityDst,
    const size_t* validIndices, int* numValidPoints, size_t maxPoints,
    uint32_t enableMask, int maxThreadsPerBlock, int cudaDeviceIndex, cudaStream_t stream);

}
}
}
