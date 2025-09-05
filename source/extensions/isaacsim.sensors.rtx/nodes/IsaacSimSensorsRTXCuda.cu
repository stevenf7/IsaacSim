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

#include <cub/device/device_select.cuh>

#include "GenericModelOutput.h"
#include "isaacsim/core/includes/ScopedCudaDevice.h"
#include "isaacsim/core/includes/Buffer.h"
#include "IsaacSimSensorsRTXCuda.cuh"

namespace isaacsim
{
namespace sensors
{
namespace rtx
{

__global__ void getModelOutputFromBufferKernel(void* __restrict__ dataPtr, omni::sensors::GenericModelOutput* __restrict__ gmoPtrDevice) {
    *gmoPtrDevice = omni::sensors::getModelOutputFromBuffer(dataPtr);
}

__global__ void fillIndicesKernel(size_t* __restrict__ indices, const int length) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= length)
        return;
    indices[idx] = idx;
}

__global__ void fillPointsKernel(omni::sensors::GenericModelOutput* __restrict__ gmoPtr, float3* __restrict__ cartesianPoints, size_t* __restrict__ validIndices, const int numValidPoints) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= numValidPoints)
        return;
    if (gmoPtr->elementsCoordsType == omni::sensors::CoordsType::CARTESIAN) {
        cartesianPoints[idx].x = gmoPtr->elements.x[validIndices[idx]];
        cartesianPoints[idx].y = gmoPtr->elements.y[validIndices[idx]];
        cartesianPoints[idx].z = gmoPtr->elements.z[validIndices[idx]];
    } else if (gmoPtr->elementsCoordsType == omni::sensors::CoordsType::SPHERICAL) {
        float azimuthDeg = gmoPtr->elements.x[validIndices[idx]];
        float elevationDeg = gmoPtr->elements.y[validIndices[idx]];
        float cosAzimuth, sinAzimuth, cosElevation, sinElevation;
        sincospif(azimuthDeg/180.0f, &sinAzimuth, &cosAzimuth);
        sincospif(elevationDeg/180.0f, &sinElevation, &cosElevation);
        cartesianPoints[idx].x = gmoPtr->elements.z[validIndices[idx]] * cosElevation * cosAzimuth;
        cartesianPoints[idx].y = gmoPtr->elements.z[validIndices[idx]] * cosElevation * sinAzimuth;
        cartesianPoints[idx].z = gmoPtr->elements.z[validIndices[idx]] * sinElevation;
    }
}

__global__ void fillPointsKernel(float* __restrict__ x, float* __restrict__ y, float* __restrict__ z, float3* __restrict__ cartesianPoints, size_t* __restrict__ validIndices, const int numValidPoints, omni::sensors::CoordsType* __restrict__ elementsCoordsType) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= numValidPoints)
        return;
    if (*elementsCoordsType == omni::sensors::CoordsType::CARTESIAN) {
        cartesianPoints[idx].x = x[validIndices[idx]];
        cartesianPoints[idx].y = y[validIndices[idx]];
        cartesianPoints[idx].z = z[validIndices[idx]];
    } else if (*elementsCoordsType == omni::sensors::CoordsType::SPHERICAL) {
        float azimuthDeg = x[validIndices[idx]];
        float elevationDeg = y[validIndices[idx]];
        float range = z[validIndices[idx]];
        float cosAzimuth, sinAzimuth, cosElevation, sinElevation;
        sincospif(azimuthDeg/180.0f, &sinAzimuth, &cosAzimuth);
        sincospif(elevationDeg/180.0f, &sinElevation, &cosElevation);
        cartesianPoints[idx].x = range * cosElevation * cosAzimuth;
        cartesianPoints[idx].y = range * cosElevation * sinAzimuth;
        cartesianPoints[idx].z = range * sinElevation;
    }
}

struct IsValid
{
    uint8_t* __restrict__ flags{ nullptr }; // sensor specific flags

    __host__ __device__ __forceinline__
    IsValid(uint8_t* __restrict__ flags) : flags(flags) {}

    __host__ __device__ __forceinline__
    bool operator()(const int &i) const {
        const uint8_t fl = flags[i];
        return (fl & omni::sensors::ElementFlags::VALID) == omni::sensors::ElementFlags::VALID;
    }
};

void IsaacExtractRTXSensorPointCloudDeviceBuffers::initialize(void* dataPtr, cudaStream_t cudaStream) {

    cudaPointerAttributes attributes;
    CUDA_CHECK(cudaPointerGetAttributes(&attributes, dataPtr));

    this->cudaStream = cudaStream;
    this->gmoOnDevice = attributes.type == cudaMemoryTypeDevice;
    this->cudaDevice = attributes.device;

    isaacsim::core::includes::ScopedDevice scopedDevice(this->cudaDevice);
    if (!this->gmoOnDevice) {
        // We can get the GMO from the host pointer directly, then use that to size the buffers
        omni::sensors::GenericModelOutput gmoHost = omni::sensors::getModelOutputFromBuffer(dataPtr);
        // Allocate twice the size of the current number of elements to account for any variation in return count
        this->bufferSize = std::min(gmoHost.numElements * 2, IsaacExtractRTXSensorPointCloudDeviceBuffers::MAX_ELEMENTS);
        // Copy the elementsCoordsType from the GMO struct onto the device
        this->elementsCoordsType.setDevice(this->cudaDevice);
        this->elementsCoordsType.resize(1);
        CUDA_CHECK(cudaMemcpyAsync(this->elementsCoordsType.data(), &gmoHost.elementsCoordsType, sizeof(omni::sensors::CoordsType), cudaMemcpyHostToDevice, this->cudaStream));
    } else {
        // Pre-allocate device memory for the GenericModelOutput struct
        this->gmo.setDevice(this->cudaDevice);
        this->gmo.resize(1);
        getModelOutputFromBufferKernel<<<1, 1, 0, this->cudaStream>>>(dataPtr, this->gmo.data());
        uint32_t numElements = 0;
        CUDA_CHECK(cudaMemcpyAsync(&numElements, &this->gmo.data()->numElements, sizeof(uint32_t), cudaMemcpyDeviceToHost, this->cudaStream));
        CUDA_CHECK(cudaStreamSynchronize(this->cudaStream));
        this->bufferSize = std::min(numElements * 2, IsaacExtractRTXSensorPointCloudDeviceBuffers::MAX_ELEMENTS);
        CUDA_CHECK(cudaMallocHost(&this->gmoHostPtr, sizeof(omni::sensors::GenericModelOutput)));
    }

    // Get the maximum number of threads per block
    CUDA_CHECK(cudaDeviceGetAttribute(&this->maxThreadsPerBlock, cudaDevAttrMaxThreadsPerBlock, this->cudaDevice));

    this->numValidPoints.setDevice(this->cudaDevice);
    this->numValidPoints.resize(1);

    // Resize buffers
    this->resizeBuffers();
}

void IsaacExtractRTXSensorPointCloudDeviceBuffers::initialize(void* dataPtr, int cudaDeviceIndex) {

    cudaPointerAttributes attributes;
    CUDA_CHECK(cudaPointerGetAttributes(&attributes, dataPtr));

    this->gmoOnDevice = cudaDeviceIndex > -1;
    this->cudaDevice = this->gmoOnDevice? cudaDeviceIndex : 0;

    isaacsim::core::includes::ScopedDevice scopedDevice(this->cudaDevice);
    if (!this->gmoOnDevice) {
        // We can get the GMO from the host pointer directly, then use that to size the buffers
        omni::sensors::GenericModelOutput gmoHost = omni::sensors::getModelOutputFromBuffer(dataPtr);
        // Allocate twice the size of the current number of elements to account for any variation in return count
        this->bufferSize = std::min(gmoHost.numElements * 2, IsaacExtractRTXSensorPointCloudDeviceBuffers::MAX_ELEMENTS);
        // Copy the elementsCoordsType from the GMO struct onto the device
        this->elementsCoordsType.setDevice(this->cudaDevice);
        this->elementsCoordsType.resize(1);
        CUDA_CHECK(cudaMemcpy(this->elementsCoordsType.data(), &gmoHost.elementsCoordsType, sizeof(omni::sensors::CoordsType), cudaMemcpyHostToDevice));
    } else {
        // Pre-allocate device memory for the GenericModelOutput struct
        this->gmo.setDevice(this->cudaDevice);
        this->gmo.resize(1);
        getModelOutputFromBufferKernel<<<1, 1, 0>>>(dataPtr, this->gmo.data());
        CUDA_CHECK(cudaDeviceSynchronize());
        uint32_t numElements = 0;
        CUDA_CHECK(cudaMemcpy(&numElements, &this->gmo.data()->numElements, sizeof(uint32_t), cudaMemcpyDeviceToHost));
        // CUDA_CHECK(cudaStreamSynchronize(this->cudaStream));
        this->bufferSize = std::min(numElements * 2, IsaacExtractRTXSensorPointCloudDeviceBuffers::MAX_ELEMENTS);
        CUDA_CHECK(cudaMallocHost(&this->gmoHostPtr, sizeof(omni::sensors::GenericModelOutput)));
    }

    // Get the maximum number of threads per block
    CUDA_CHECK(cudaDeviceGetAttribute(&this->maxThreadsPerBlock, cudaDevAttrMaxThreadsPerBlock, this->cudaDevice));

    this->numValidPoints.setDevice(this->cudaDevice);
    this->numValidPoints.resize(1);

    // Resize buffers
    this->resizeBuffersNoStream();
}

void IsaacExtractRTXSensorPointCloudDeviceBuffers::resizeBuffers() {
    isaacsim::core::includes::ScopedDevice scopedDevice(this->cudaDevice);

    if (!this->gmoOnDevice) {
        this->x.setDevice(this->cudaDevice);
        this->x.resize(this->bufferSize);
        this->y.setDevice(this->cudaDevice);
        this->y.resize(this->bufferSize);
        this->z.setDevice(this->cudaDevice);
        this->z.resize(this->bufferSize);
        this->flags.setDevice(this->cudaDevice);
        this->flags.resize(this->bufferSize);
    }
    // Pre-allocate device memory for the output buffer
    this->pointCloudBuffer.setDevice(this->cudaDevice);
    this->pointCloudBuffer.resize(this->bufferSize);

    // Pre-allocate device memory for the valid indices buffers and temporary storage
    this->validIndicesIn.setDevice(this->cudaDevice);
    this->validIndicesIn.resize(this->bufferSize);
    const int nb_fillIndices = (this->bufferSize + this->maxThreadsPerBlock - 1) / this->maxThreadsPerBlock;
    fillIndicesKernel<<<nb_fillIndices, this->maxThreadsPerBlock, 0, cudaStream>>>(this->validIndicesIn.data(), this->bufferSize);

    this->validIndicesOut.setDevice(this->cudaDevice);
    this->validIndicesOut.resize(this->bufferSize);

    this->tempStorage.setDevice(this->cudaDevice);
    this->tempStorage.resize(this->bufferSize);
}

void IsaacExtractRTXSensorPointCloudDeviceBuffers::resizeBuffersNoStream() {
    isaacsim::core::includes::ScopedDevice scopedDevice(this->cudaDevice);

    if (!this->gmoOnDevice) {
        this->x.setDevice(this->cudaDevice);
        this->x.resize(this->bufferSize);
        this->y.setDevice(this->cudaDevice);
        this->y.resize(this->bufferSize);
        this->z.setDevice(this->cudaDevice);
        this->z.resize(this->bufferSize);
        this->flags.setDevice(this->cudaDevice);
        this->flags.resize(this->bufferSize);
    }
    // Pre-allocate device memory for the output buffer
    this->pointCloudBuffer.setDevice(this->cudaDevice);
    this->pointCloudBuffer.resize(this->bufferSize);

    // Pre-allocate device memory for the valid indices buffers and temporary storage
    this->validIndicesIn.setDevice(this->cudaDevice);
    this->validIndicesIn.resize(this->bufferSize);
    const int nb_fillIndices = (this->bufferSize + this->maxThreadsPerBlock - 1) / this->maxThreadsPerBlock;
    fillIndicesKernel<<<nb_fillIndices, this->maxThreadsPerBlock, 0>>>(this->validIndicesIn.data(), this->bufferSize);

    this->validIndicesOut.setDevice(this->cudaDevice);
    this->validIndicesOut.resize(this->bufferSize);

    this->tempStorage.setDevice(this->cudaDevice);
    this->tempStorage.resize(this->bufferSize);
}

void IsaacExtractRTXSensorPointCloudDeviceBuffers::fillPointCloudBuffer(void* dataPtr, size_t& numValidPointsHost, omni::sensors::FrameAtTime& frameAtEndHost) {
    isaacsim::core::includes::ScopedDevice scopedDevice(this->cudaDevice);

    uint32_t numReturns = 0;
    uint8_t* flagsDevicePtr = nullptr;

    omni::sensors::GenericModelOutput gmoHost;


    // Update number of returns and device pointer to flags
    if (this->gmoOnDevice) {
        // Incoming dataPtr is a device address
        // Instead of kernel + 3 DtoH copies + sync, one DtoH copy of the struct to pinned memory
        CUDA_CHECK(cudaMemcpyAsync(this->gmoHostPtr, dataPtr, sizeof(omni::sensors::GenericModelOutput), cudaMemcpyDeviceToHost, this->cudaStream));
        CUDA_CHECK(cudaStreamSynchronize(this->cudaStream));
        numReturns = this->gmoHostPtr->numElements;
        frameAtEndHost = this->gmoHostPtr->frameEnd;
        flagsDevicePtr = this->gmoHostPtr->elements.flags;
    } else {
        // Incoming dataPtr is a host address
        gmoHost = omni::sensors::getModelOutputFromBuffer(dataPtr);
        numReturns = gmoHost.numElements;
        frameAtEndHost = gmoHost.frameEnd;
    }

    if (numReturns > this->bufferSize) {
        this->bufferSize = numReturns;
        this->resizeBuffers();
    }

    if (!this->gmoOnDevice) {
        CUDA_CHECK(cudaMemcpyAsync(this->x.data(), gmoHost.elements.x, gmoHost.numElements * sizeof(float), cudaMemcpyHostToDevice, this->cudaStream));
        CUDA_CHECK(cudaMemcpyAsync(this->y.data(), gmoHost.elements.y, gmoHost.numElements * sizeof(float), cudaMemcpyHostToDevice, this->cudaStream));
        CUDA_CHECK(cudaMemcpyAsync(this->z.data(), gmoHost.elements.z, gmoHost.numElements * sizeof(float), cudaMemcpyHostToDevice, this->cudaStream));
        CUDA_CHECK(cudaMemcpyAsync(this->flags.data(), gmoHost.elements.flags, gmoHost.numElements * sizeof(uint8_t), cudaMemcpyHostToDevice, this->cudaStream));
        flagsDevicePtr = this->flags.data();
        CUDA_CHECK(cudaStreamSynchronize(this->cudaStream));
    }

    // Store indices of valid returns in the GMO buffer in the validIndices buffer
    // Call cub::DeviceSelect::If with a nullptr to get the size of the temporary storage buffer
    // Then allocate the temporary storage buffer and call cub::DeviceSelect::If again to fill validIndices.
    // Note the second operation automatically resizes validIndices to the number of valid points.
    void* d_temp_storage = nullptr;
    size_t tmpCubStorageBuffBytes = 0;
    cub::DeviceSelect::If(d_temp_storage, tmpCubStorageBuffBytes, this->validIndicesIn.data(), this->validIndicesOut.data(), this->numValidPoints.data(), numReturns, IsValid(flagsDevicePtr), this->cudaStream);
    if (tmpCubStorageBuffBytes > this->tempStorage.size()) {
        this->tempStorage.resizeAsync(tmpCubStorageBuffBytes, this->cudaStream);
    }
    cub::DeviceSelect::If(this->tempStorage.data(), tmpCubStorageBuffBytes, this->validIndicesIn.data(), this->validIndicesOut.data(), this->numValidPoints.data(), numReturns, IsValid(flagsDevicePtr), this->cudaStream);

    // Copy the number of valid points from the device to the host, then synchronize
    CUDA_CHECK(cudaMemcpyAsync(&numValidPointsHost, this->numValidPoints.data(), sizeof(size_t), cudaMemcpyDeviceToHost, this->cudaStream));
    CUDA_CHECK(cudaStreamSynchronize(this->cudaStream));

    // Fill the point cloud buffer with the valid points
    const int nb_fillPoints = (numValidPointsHost + this->maxThreadsPerBlock - 1) / this->maxThreadsPerBlock;
    if (this->gmoOnDevice) {
        fillPointsKernel<<<nb_fillPoints, this->maxThreadsPerBlock, 0, this->cudaStream>>>(reinterpret_cast<omni::sensors::GenericModelOutput*>(dataPtr), this->pointCloudBuffer.data(), this->validIndicesOut.data(), numValidPointsHost);
    } else {
        float* xDevicePtr = this->x.data();
        float* yDevicePtr = this->y.data();
        float* zDevicePtr = this->z.data();
        omni::sensors::CoordsType* elementsCoordsTypeDevicePtr = this->elementsCoordsType.data();
        fillPointsKernel<<<nb_fillPoints, this->maxThreadsPerBlock, 0, this->cudaStream>>>(xDevicePtr, yDevicePtr, zDevicePtr, this->pointCloudBuffer.data(), this->validIndicesOut.data(), numValidPointsHost, elementsCoordsTypeDevicePtr);
    }
    CUDA_CHECK(cudaStreamSynchronize(this->cudaStream));
}

IsaacExtractRTXSensorPointCloudDeviceBuffers::~IsaacExtractRTXSensorPointCloudDeviceBuffers() {
    if (this->gmoHostPtr) {
        CUDA_CHECK(cudaFreeHost(this->gmoHostPtr));
    }
}

// Version that uses pre-allocated temporary storage for vGPU compatibility
void findValidIndices(size_t* __restrict__ dataIn, size_t* __restrict__ dataOut, int* __restrict__ numValidPoints, size_t numPoints, uint8_t* __restrict__ flags, 
                           int cudaDeviceIndex, cudaStream_t stream, void** __restrict__ d_temp_storage, size_t* __restrict__ temp_storage_bytes, int* __restrict__ cached_numPoints) {
    isaacsim::core::includes::ScopedDevice scopedDevice(cudaDeviceIndex);
    
    cub::DeviceSelect::If(
        *d_temp_storage,
        *temp_storage_bytes,
        dataIn,
        dataOut,
        numValidPoints,
        numPoints,
        IsValid(flags),
        stream
    );
}

void fillIndices(size_t* __restrict__ indices, size_t numIndices, int maxThreadsPerBlock, int cudaDeviceIndex, cudaStream_t stream) {
    isaacsim::core::includes::ScopedDevice scopedDevice(cudaDeviceIndex);

    const int nt = maxThreadsPerBlock;
    const int nb = (numIndices + nt - 1) / nt;

    fillIndicesKernel<<<nb, nt, 0, stream>>>(indices, numIndices);
}

size_t getTempStorageSizeForValidIndices(size_t maxPoints, int cudaDeviceIndex) {
    isaacsim::core::includes::ScopedDevice scopedDevice(cudaDeviceIndex);
    
    void* d_temp_storage = nullptr;
    size_t temp_storage_bytes = 0;
    
    // Query temp storage size for max points
    cub::DeviceSelect::If(
        d_temp_storage,
        temp_storage_bytes,
        static_cast<size_t*>(nullptr),
        static_cast<size_t*>(nullptr),
        static_cast<int*>(nullptr),
        maxPoints,
        IsValid(static_cast<uint8_t*>(nullptr))
    );
    
    return temp_storage_bytes;
}

__global__ void fillValidCartesianPointsKernel(
    const float* __restrict__ azimuth, 
    const float* __restrict__ elevation, 
    const float* __restrict__ range, 
    float3* __restrict__ cartesianPoints, 
    const size_t* __restrict__ validIndices, 
    int numValidPoints)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= numValidPoints) return;
    
    size_t srcIdx = validIndices[idx];
    float azimuthDeg = azimuth[srcIdx];
    float elevationDeg = elevation[srcIdx];
    float rangeVal = range[srcIdx];
    
    float cosAzimuth, sinAzimuth, cosElevation, sinElevation;
    sincospif(azimuthDeg / 180.0f, &sinAzimuth, &cosAzimuth);
    sincospif(elevationDeg / 180.0f, &sinElevation, &cosElevation);
    
    // Compute intermediate value once
    float rangeXY = rangeVal * cosElevation;
    
    // Vectorized store using make_float3
    cartesianPoints[idx] = make_float3(
        rangeXY * cosAzimuth,      // x
        rangeXY * sinAzimuth,      // y
        rangeVal * sinElevation    // z
    );
}

// High-accuracy version with cached device properties
void fillValidCartesianPoints(float* __restrict__ azimuth, float* __restrict__ elevation, float* __restrict__ range, float3* __restrict__ cartesianPoints, 
                                                 size_t* __restrict__ validIndices, int* __restrict__ numValidPointsDevice, size_t maxPoints,
                                                 int maxThreadsPerBlock, int multiProcessorCount,
                                                 int cudaDeviceIndex, cudaStream_t stream) {
    isaacsim::core::includes::ScopedDevice scopedDevice(cudaDeviceIndex);

    // Get actual number of points to process
    int numValidPointsHost;
    CUDA_CHECK(cudaMemcpyAsync(&numValidPointsHost, numValidPointsDevice, sizeof(int), cudaMemcpyDeviceToHost, stream));
    CUDA_CHECK(cudaStreamSynchronize(stream));
    
    if (numValidPointsHost == 0) return;
    
    // optimize for occupancy
    if (numValidPointsHost < 1024) {
        // vectorized approach - high occupancy
        int nt = 256;
        int nb = (multiProcessorCount * 4); // Ensure high occupancy
        fillValidCartesianPointsKernel<<<nb, nt, 0, stream>>>(
            azimuth, elevation, range, cartesianPoints, validIndices, numValidPointsHost);
    } else {
        // use all available threads
        int nt = maxThreadsPerBlock;
        int nb = (numValidPointsHost + nt - 1) / nt;
        fillValidCartesianPointsKernel<<<nb, nt, 0, stream>>>(
            azimuth, elevation, range, cartesianPoints, validIndices, numValidPointsHost);
    }
}

template <typename T>
__global__ void selectValidPointsKernel(T* __restrict__ inData, T* __restrict__ outData, size_t* __restrict__ validIndices, int* __restrict__ numValidPoints, size_t stride) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= *numValidPoints) {
        return;
    }
    for (size_t i = 0; i < stride; i++) {
        outData[idx*stride + i] = inData[validIndices[idx]*stride + i];
    }
}

template <typename T>
void selectValidPoints(T* __restrict__ inData, T* __restrict__ outData, size_t* __restrict__ validIndices, int* __restrict__ numValidPoints, size_t maxPoints, int maxThreadsPerBlock, int cudaDeviceIndex, cudaStream_t stream, size_t stride) {
    isaacsim::core::includes::ScopedDevice scopedDevice(cudaDeviceIndex);

    const int nt = maxThreadsPerBlock;
    const int nb = (maxPoints + nt - 1) / nt;
    selectValidPointsKernel<<<nb, nt, 0, stream>>>(inData, outData, validIndices, numValidPoints, stride);
}

template void selectValidPoints<float>(float* __restrict__ inData, float* __restrict__ outData, size_t* __restrict__ validIndices, int* __restrict__ numValidPoints, size_t maxPoints, int maxThreadsPerBlock, int cudaDeviceIndex, cudaStream_t stream, size_t stride);
template void selectValidPoints<float3>(float3* __restrict__ inData, float3* __restrict__ outData, size_t* __restrict__ validIndices, int* __restrict__ numValidPoints, size_t maxPoints, int maxThreadsPerBlock, int cudaDeviceIndex, cudaStream_t stream, size_t stride);
template void selectValidPoints<int32_t>(int32_t* __restrict__ inData, int32_t* __restrict__ outData, size_t* __restrict__ validIndices, int* __restrict__ numValidPoints, size_t maxPoints, int maxThreadsPerBlock, int cudaDeviceIndex, cudaStream_t stream, size_t stride);
template void selectValidPoints<uint8_t>(uint8_t* __restrict__ inData, uint8_t* __restrict__ outData, size_t* __restrict__ validIndices, int* __restrict__ numValidPoints, size_t maxPoints, int maxThreadsPerBlock, int cudaDeviceIndex, cudaStream_t stream, size_t stride);
template void selectValidPoints<uint32_t>(uint32_t* __restrict__ inData, uint32_t* __restrict__ outData, size_t* __restrict__ validIndices, int* __restrict__ numValidPoints, size_t maxPoints, int maxThreadsPerBlock, int cudaDeviceIndex, cudaStream_t stream, size_t stride);

// fused kernel for required basic outputs (azimuth, elevation, distance, intensity)
__global__ void selectRequiredValidPointsKernel(
    const float* __restrict__ azimuthSrc, const float* __restrict__ elevationSrc, const float* __restrict__ distanceSrc, const float* __restrict__ intensitySrc,
    float* __restrict__ azimuthDst, float* __restrict__ elevationDst, float* __restrict__ distanceDst, float* __restrict__ intensityDst,
    const size_t* __restrict__ validIndices, int* __restrict__ numValidPoints, uint32_t enableMask)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= *numValidPoints) {
        return;
    }
    
    size_t srcIdx = validIndices[idx];
    
    // vectorized loads for better memory bandwidth
    if (enableMask & 0xF) {
        if (enableMask & 1) azimuthDst[idx] = azimuthSrc[srcIdx];      // bit 0: azimuth
        if (enableMask & 2) elevationDst[idx] = elevationSrc[srcIdx];  // bit 1: elevation  
        if (enableMask & 4) distanceDst[idx] = distanceSrc[srcIdx];    // bit 2: distance
        if (enableMask & 8) intensityDst[idx] = intensitySrc[srcIdx];  // bit 3: intensity
    }
}

// Optimized fused kernel for optional outputs
__global__ void selectOptionalValidPointsKernel(
    const int32_t* __restrict__ timestampSrc, const uint32_t* __restrict__ emitterIdSrc, const uint32_t* __restrict__ materialIdSrc, const uint8_t* __restrict__ objectIdSrc,
    const float3* __restrict__ normalSrc, const float3* __restrict__ velocitySrc,
    int32_t* __restrict__ timestampDst, uint32_t* __restrict__ emitterIdDst, uint32_t* __restrict__ materialIdDst, uint8_t* __restrict__ objectIdDst,
    float3* __restrict__ normalDst, float3* __restrict__ velocityDst,
    const size_t* __restrict__ validIndices, int* __restrict__ numValidPoints, uint32_t enableMask)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= *numValidPoints) {
        return;
    }
    
    size_t srcIdx = validIndices[idx];
    
    // Optional outputs - less frequently accessed together
    if (enableMask & (1 << 4)) timestampDst[idx] = timestampSrc[srcIdx];      // bit 4: timestamp
    if (enableMask & (1 << 5)) emitterIdDst[idx] = emitterIdSrc[srcIdx];      // bit 5: emitter ID
    if (enableMask & (1 << 6)) materialIdDst[idx] = materialIdSrc[srcIdx];    // bit 6: material ID
    if (enableMask & (1 << 7)) {                                              // bit 7: object ID
        for (size_t i = 0; i < 16; i++) {   // handle striding
            objectIdDst[idx * 16 + i] = objectIdSrc[srcIdx * 16 + i];
        }
    }
    if (enableMask & (1 << 8)) normalDst[idx] = normalSrc[srcIdx];            // bit 8: normal
    if (enableMask & (1 << 9)) velocityDst[idx] = velocitySrc[srcIdx];        // bit 9: velocity
}

// Host function to launch the required outputs kernel
void selectRequiredValidPoints(
    const float* __restrict__ azimuthSrc, const float* __restrict__ elevationSrc, const float* __restrict__ distanceSrc, const float* __restrict__ intensitySrc,
    float* __restrict__ azimuthDst, float* __restrict__ elevationDst, float* __restrict__ distanceDst, float* __restrict__ intensityDst,
    const size_t* __restrict__ validIndices, int* __restrict__ numValidPoints, size_t maxPoints, 
    uint32_t enableMask, int maxThreadsPerBlock, int cudaDeviceIndex, cudaStream_t stream)
{
    isaacsim::core::includes::ScopedDevice scopedDevice(cudaDeviceIndex);
    
    // Only launch if any required outputs are enabled
    if (enableMask == 0) return;
    
    const int nt = maxThreadsPerBlock;
    const int nb = (maxPoints + nt - 1) / nt;
    
    selectRequiredValidPointsKernel<<<nb, nt, 0, stream>>>(
        azimuthSrc, elevationSrc, distanceSrc, intensitySrc,
        azimuthDst, elevationDst, distanceDst, intensityDst,
        validIndices, numValidPoints, enableMask);
}

// Host function to launch the optional outputs kernel
void selectOptionalValidPoints(
    const int32_t* __restrict__ timestampSrc, const uint32_t* __restrict__ emitterIdSrc, const uint32_t* __restrict__ materialIdSrc, const uint8_t* __restrict__ objectIdSrc,
    const float3* __restrict__ normalSrc, const float3* __restrict__ velocitySrc,
    int32_t* __restrict__ timestampDst, uint32_t* __restrict__ emitterIdDst, uint32_t* __restrict__ materialIdDst, uint8_t* __restrict__ objectIdDst,
    float3* __restrict__ normalDst, float3* __restrict__ velocityDst,
    const size_t* __restrict__ validIndices, int* __restrict__ numValidPoints, size_t maxPoints,
    uint32_t enableMask, int maxThreadsPerBlock, int cudaDeviceIndex, cudaStream_t stream)
{
    isaacsim::core::includes::ScopedDevice scopedDevice(cudaDeviceIndex);
    
    // launch if any optional outputs are enabled
    if (enableMask == 0) return;
    
    const int nt = maxThreadsPerBlock;
    const int nb = (maxPoints + nt - 1) / nt;
    
    selectOptionalValidPointsKernel<<<nb, nt, 0, stream>>>(
        timestampSrc, emitterIdSrc, materialIdSrc, objectIdSrc,
        normalSrc, velocitySrc,
        timestampDst, emitterIdDst, materialIdDst, objectIdDst,
        normalDst, velocityDst,
        validIndices, numValidPoints, enableMask);
}

}   // namespace isaacsim
}   // namespace sensors
}   // namespace rtx
