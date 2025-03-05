// Copyright (c) 2023-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <omni/math/linalg/matrix.h>
#include <omni/sensors/lidar/LidarProfileTypes.h>

#include <GMOAuxiliaryData.h>
#include <GenericModelOutputTypes.h>

namespace isaacsim
{
namespace sensors
{
namespace rtx
{
using namespace omni::sensors;

inline constexpr float Deg2Rad(float deg)
{
    return (deg / 180.f) * 3.141592653589f;
}
inline uint32_t idxOfReturn(const uint32_t beamId,
                            const uint32_t echoId,
                            const uint32_t numEchos,
                            const uint32_t numBeams = 0,
                            const uint32_t tick = 0)
{
    return beamId * numEchos + echoId + tick * numEchos * numBeams;
}

template <class T>
void wrapCudaMemcpyAsync(T* dst, const T* src, uint32_t startLoc, uint32_t num, uint32_t numSpillover, cudaMemcpyKind kind)
{

    unsigned long dataSize = sizeof(T);
    cudaMemcpyAsync(dst + startLoc, src, num * dataSize, kind);
    cudaMemcpyAsync(dst, src + num, numSpillover * dataSize, kind);
}


void getTransformFromSensorPose(const omni::sensors::FrameAtTime& parm, omni::math::linalg::matrix4d& matrixOutput);

/**
 * @class LidarConfigHelper
 * @brief Helper class for managing LiDAR sensor configuration
 * @details Provides utilities for handling LiDAR profiles, scan types, and configuration parameters.
 *          Manages the storage and access of LiDAR-specific settings and profile data.
 */
class LidarConfigHelper
{
public:
    /** @brief Configuration string for the LiDAR sensor */
    std::string config;
    /** @brief Type of LiDAR scanning pattern */
    LidarScanType scanType{ LidarScanType::kUnknown };
    /** @brief Pointer to the active LiDAR profile */
    LidarProfile* profile;
    /** @brief Buffer storing the raw profile data */
    std::vector<uint8_t> profileBuffer;

    /** @brief Gets the minimum range of the LiDAR sensor */
    float getNearRange() const;
    /** @brief Gets the maximum range of the LiDAR sensor */
    float getFarRange() const;
    /** @brief Gets the number of vertical channels in the LiDAR */
    uint32_t getNumChannels() const;
    /** @brief Gets the number of echoes per beam */
    uint32_t getNumEchos() const;
    /** @brief Gets the total number of returns per complete scan */
    uint32_t getReturnsPerScan() const;
    /** @brief Gets the number of ticks required for a complete scan */
    uint32_t getTicksPerScan() const;
    /**
     * @brief Updates the LiDAR configuration from a render product path
     * @param[in] renderProductPath Path to the render product configuration
     * @return True if update was successful, false otherwise
     */
    bool updateLidarConfig(const char* renderProductPath);
};

// GenericModelOutputHelper is used when you want a host side copy of a
// gmo, and you want pointers in elements and aux to be kept from the input
/**
 * @class GenericModelOutputHelper
 * @brief Helper class for managing host-side copies of generic model outputs
 * @details Provides functionality to maintain and manage host-side copies of sensor data,
 *          preserving pointer relationships and handling data transfer between device and host.
 *          Supports different sensor types including LiDAR, ultrasonic, and radar.
 */
class GenericModelOutputHelper
{
public:
    /** @brief Generic model output structure containing sensor data */
    omni::sensors::GenericModelOutput m_gmo;
    /** @brief Union of auxiliary data structures for different sensor types */
    union
    {
        /** @brief LiDAR-specific auxiliary data */
        omni::sensors::LidarAuxiliaryData m_auxlidar;
        /** @brief Ultrasonic-specific auxiliary data */
        omni::sensors::USSAuxiliaryData m_auxUltrasonic;
        /** @brief Radar-specific auxiliary data */
        omni::sensors::RadarAuxiliaryData m_auxRadar;
    };

private:
    /** @brief CUDA pointer attributes for source data */
    cudaPointerAttributes srcAttrs;
    /** @brief Type of memory copy operation (device-to-host or host-to-host) */
    enum cudaMemcpyKind kind;
    /** @brief Pointer to raw data buffer */
    uint8_t* data;
    size_t offset;

public:
    /**
     * @brief Constructs a new Generic Model Output Helper
     * @param[in] gmoPtr Pointer to the source generic model output data
     */
    GenericModelOutputHelper(void* gmoPtr)
    {
        data = reinterpret_cast<uint8_t*>(gmoPtr);
        cudaPointerGetAttributes(&srcAttrs, gmoPtr);

        // const omni::sensors::GenericModelOutput& ingmo =
        //   *reinterpret_cast<const omni::sensors::GenericModelOutput*>(gmoPtr);
        kind = srcAttrs.type == cudaMemoryTypeDevice ? cudaMemcpyDeviceToHost : cudaMemcpyHostToHost;
        cudaMemcpyAsync(&m_gmo, gmoPtr, sizeof(omni::sensors::GenericModelOutput), kind);
        setGenericModelOutputPtrs();
    }
    /**
     * @brief Validates the generic model output configuration
     * @param[in] outType Expected output type
     * @param[in] coordType Expected coordinate system type
     * @param[in] modality Expected sensor modality
     * @return True if configuration is valid, false otherwise
     */
    bool isValid(const OutputType& outType, const CoordsType& coordType, const Modality& modality)
    {
        if (m_gmo.magicNumber != MAGIC_NUMBER_GMO || m_gmo.outputType != outType ||
            m_gmo.elementsCoordsType != coordType || m_gmo.modality != modality)
        {
            return false;
        }
        return true;
    }
    /**
     * @brief Gets the emitter ID for a specific element
     * @param[in] i Index of the element
     * @return Emitter ID value
     */
    uint32_t getEmitterId(int i) const
    {
        uint32_t returnMe;
        cudaMemcpyAsync(&returnMe, m_auxlidar.emitterId + sizeof(uint32_t) * i, sizeof(uint32_t), kind);
        return returnMe;
    }
    /**
     * @brief Gets the tick ID for a specific element
     * @param[in] i Index of the element
     * @return Tick ID value
     */
    uint32_t getTickId(int i) const
    {
        uint32_t returnMe;
        cudaMemcpyAsync(&returnMe, m_auxlidar.tickId + sizeof(uint32_t) * i, sizeof(uint32_t), kind);
        return returnMe;
    }

    /**
     * @brief Sets up pointers for the generic model output structure
     * @details Initializes and configures pointers for basic elements and auxiliary data
     */
    inline void setGenericModelOutputPtrs()
    {
        GenericModelOutput* modelOutput{ &m_gmo };
        if (m_gmo.magicNumber != MAGIC_NUMBER_GMO)
        {
            modelOutput->elements = BasicElements(); // nullptr
            modelOutput->auxiliaryData = nullptr;
            return;
        }
        offset = sizeof(GenericModelOutput);
        // Basic elements
        modelOutput->elements.timeOffsetNs = reinterpret_cast<int32_t*>(data + offset);
        offset += sizeof(int32_t) * modelOutput->numElements;
        modelOutput->elements.x = reinterpret_cast<float*>(data + offset);
        offset += sizeof(float) * modelOutput->numElements;
        modelOutput->elements.y = reinterpret_cast<float*>(data + offset);
        offset += sizeof(float) * modelOutput->numElements;
        modelOutput->elements.z = reinterpret_cast<float*>(data + offset);
        offset += sizeof(float) * modelOutput->numElements;
        modelOutput->elements.scalar = reinterpret_cast<float*>(data + offset);
        offset += sizeof(float) * modelOutput->numElements;
        modelOutput->elements.flags = reinterpret_cast<uint8_t*>(data + offset);
        offset += sizeof(uint8_t) * modelOutput->numElements;
        // For the contiguous buffer, additional padding bytes are added after the last flags element (just before the
        // auxiliary data struct) to ensure that the structure is aligned to a multiple of 8 bytes.
        if (offset % 8 != 0)
        {
            offset += 8 - (offset % 8); // This has to be done for reading the auxiliary data from the buffer
        }
        // aux elements
        if (modelOutput->modality == Modality::LIDAR)
        {
            setLidarAuxiliaryDataPtrs();
        }
        else if (modelOutput->modality == Modality::USS)
        {
            setUSSAuxiliaryDataPtrs();
        }
        else if (modelOutput->modality == Modality::RADAR)
        {
            setRadarAuxiliaryDataPtrs();
        }
    }
    /**
     * @brief Sets up pointers for LiDAR auxiliary data
     * @details Configures pointers for LiDAR-specific auxiliary data fields
     */
    inline void setLidarAuxiliaryDataPtrs()
    {
        // LidarAuxiliaryData auxData;
        cudaMemcpyAsync(&m_auxlidar, data + offset, sizeof(LidarAuxiliaryData), kind);
        LidarAuxiliaryData* auxData = &m_auxlidar;
        GenericModelOutput* modelOutput{ &m_gmo };
        modelOutput->auxiliaryData = reinterpret_cast<void*>(auxData);
        offset += sizeof(LidarAuxiliaryData);
        if ((auxData->filledAuxMembers & LidarAuxHas::EMITTER_ID) == LidarAuxHas::EMITTER_ID)
        {
            auxData->emitterId = reinterpret_cast<uint32_t*>(data + offset);
            offset += sizeof(uint32_t) * modelOutput->numElements;
        }
        else
        {
            auxData->emitterId = nullptr;
        }

        if ((auxData->filledAuxMembers & LidarAuxHas::CHANNEL_ID) == LidarAuxHas::CHANNEL_ID)
        {
            auxData->channelId = reinterpret_cast<uint32_t*>(data + offset);
            offset += sizeof(uint32_t) * modelOutput->numElements;
        }
        else
        {
            auxData->channelId = nullptr;
        }

        if ((auxData->filledAuxMembers & LidarAuxHas::MAT_ID) == LidarAuxHas::MAT_ID)
        {
            auxData->matId = reinterpret_cast<uint32_t*>(data + offset);
            offset += sizeof(uint32_t) * modelOutput->numElements;
        }
        else
        {
            auxData->matId = nullptr;
        }

        if ((auxData->filledAuxMembers & LidarAuxHas::TICK_ID) == LidarAuxHas::TICK_ID)
        {
            auxData->tickId = reinterpret_cast<uint32_t*>(data + offset);
            offset += sizeof(uint32_t) * modelOutput->numElements;
        }
        else
        {
            auxData->tickId = nullptr;
        }

        if ((auxData->filledAuxMembers & LidarAuxHas::HIT_NORMALS) == LidarAuxHas::HIT_NORMALS)
        {
            auxData->hitNormals = reinterpret_cast<float*>(data + offset);
            offset += sizeof(float) * modelOutput->numElements * 3;
        }
        else
        {
            auxData->hitNormals = nullptr;
        }
        if ((auxData->filledAuxMembers & LidarAuxHas::VELOCITIES) == LidarAuxHas::VELOCITIES)
        {
            auxData->velocities = reinterpret_cast<float*>(data + offset);
            offset += sizeof(float) * modelOutput->numElements * 3;
        }
        else
        {
            auxData->velocities = nullptr;
        }

        if ((auxData->filledAuxMembers & LidarAuxHas::OBJ_ID) == LidarAuxHas::OBJ_ID)
        {
            auxData->objId = reinterpret_cast<uint8_t*>(data + offset);
            offset += sizeof(uint8_t) * modelOutput->numElements;
        }
        else
        {
            auxData->objId = nullptr;
        }

        if ((auxData->filledAuxMembers & LidarAuxHas::ECHO_ID) == LidarAuxHas::ECHO_ID)
        {
            auxData->echoId = reinterpret_cast<uint8_t*>(data + offset);
            offset += sizeof(uint8_t) * modelOutput->numElements;
        }
        else
        {
            auxData->echoId = nullptr;
        }

        if ((auxData->filledAuxMembers & LidarAuxHas::TICK_STATES) == LidarAuxHas::TICK_STATES)
        {
            auxData->tickStates = reinterpret_cast<uint8_t*>(data + offset);
            offset += sizeof(uint8_t) * modelOutput->numElements;
        }
        else
        {
            auxData->tickStates = nullptr;
        }
    }
    /**
     * @brief Sets up pointers for ultrasonic auxiliary data
     * @details Configures pointers for ultrasonic-specific auxiliary data fields
     */
    inline void setUSSAuxiliaryDataPtrs()
    {
        // USSAuxiliaryData auxData;
        cudaMemcpyAsync(&m_auxUltrasonic, data + offset, sizeof(USSAuxiliaryData), kind);
        USSAuxiliaryData* auxData = &m_auxUltrasonic;
        GenericModelOutput* modelOutput{ &m_gmo };
        modelOutput->auxiliaryData = reinterpret_cast<void*>(auxData);
        offset += sizeof(USSAuxiliaryData);
    }
    /**
     * @brief Sets up pointers for radar auxiliary data
     * @details Configures pointers for radar-specific auxiliary data fields
     */
    inline void setRadarAuxiliaryDataPtrs()
    {
        cudaMemcpyAsync(&m_auxRadar, data + offset, sizeof(RadarAuxiliaryData), kind);
        RadarAuxiliaryData* auxData = &m_auxRadar;
        GenericModelOutput* modelOutput{ &m_gmo };
        modelOutput->auxiliaryData = reinterpret_cast<void*>(auxData);
        offset += sizeof(RadarAuxiliaryData);

        auxData->rv_ms = reinterpret_cast<float*>(data + offset);
        offset += sizeof(float) * modelOutput->numElements;
    }
};

}
}
}
