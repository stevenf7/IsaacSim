// SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#pragma once

#include "rapidjson/document.h"

#include <omni/String.h>
#include <omni/math/linalg/matrix.h>

#include <GMOAuxiliaryData.h>
#include <GenericModelOutputTypes.h>

namespace isaacsim
{
namespace sensors
{
namespace rtx
{
using namespace omni::sensors;

inline constexpr float deg2Rad(float deg)
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


enum class LidarScanType
{
    kUnknown,
    kRotary,
    kSolidState
};
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
    // /** @brief Pointer to the active LiDAR profile */
    // LidarProfile* profile;
    // /** @brief Buffer storing the raw profile data */
    // std::vector<uint8_t> profileBuffer;

    struct EmitterState
    {
        std::vector<float> elevationDeg{
            -15.0f,  -14.19f, -13.39f, -12.58f, -11.77f, -10.97f, -10.16f, -9.35f,  -8.55f,  -7.74f,  -6.94f,  -6.13f,
            -5.32f,  -4.52f,  -3.71f,  -2.9f,   -2.1f,   -1.29f,  -0.48f,  0.32f,   1.13f,   1.94f,   2.74f,   3.55f,
            4.35f,   5.16f,   5.97f,   6.77f,   7.58f,   8.39f,   9.19f,   10.0f,   -15.0f,  -14.19f, -13.39f, -12.58f,
            -11.77f, -10.97f, -10.16f, -9.35f,  -8.55f,  -7.74f,  -6.94f,  -6.13f,  -5.32f,  -4.52f,  -3.71f,  -2.9f,
            -2.1f,   -1.29f,  -0.48f,  0.32f,   1.13f,   1.94f,   2.74f,   3.55f,   4.35f,   5.16f,   5.97f,   6.77f,
            7.58f,   8.39f,   9.19f,   10.0f,   -15.0f,  -14.19f, -13.39f, -12.58f, -11.77f, -10.97f, -10.16f, -9.35f,
            -8.55f,  -7.74f,  -6.94f,  -6.13f,  -5.32f,  -4.52f,  -3.71f,  -2.9f,   -2.1f,   -1.29f,  -0.48f,  0.32f,
            1.13f,   1.94f,   2.74f,   3.55f,   4.35f,   5.16f,   5.97f,   6.77f,   7.58f,   8.39f,   9.19f,   10.0f,
            -15.0f,  -14.19f, -13.39f, -12.58f, -11.77f, -10.97f, -10.16f, -9.35f,  -8.55f,  -7.74f,  -6.94f,  -6.13f,
            -5.32f,  -4.52f,  -3.71f,  -2.9f,   -2.1f,   -1.29f,  -0.48f,  0.32f,   1.13f,   1.94f,   2.74f,   3.55f,
            4.35f,   5.16f,   5.97f,   6.77f,   7.58f,   8.39f,   9.19f,   10.0f
        };
        std::vector<float> azimuthDeg{
            -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f,
            -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f, -3.0f,
            -3.0f, -3.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f,
            -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f, -1.0f,
            -1.0f, -1.0f, -1.0f, -1.0f, 1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,
            1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,
            1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  1.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,
            3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,
            3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f,  3.0f
        };
    };
    enum class LidarRotationDirection
    {
        CW,
        CCW
    };
    /** @brief Minimum range of the LiDAR sensor */
    float nearRangeM{ 0.3f };
    /** @brief Maximum range of the LiDAR sensor */
    float farRangeM{ 200.0f };
    /** @brief Start azimuth angle of the LiDAR sensor */
    float azimuthStartDeg{ 0.0f };
    /** @brief End azimuth angle of the LiDAR sensor */
    float azimuthEndDeg{ 360.0f };
    /** @brief Horizontal resolution of the LiDAR sensor */
    float horizontalResolutionDeg{ 0.1f };
    /** @brief Report rate base Hz of the LiDAR sensor */
    uint32_t reportRateBaseHz{ 36000 };
    /** @brief Rotation rate of the LiDAR sensor */
    uint32_t scanRateBaseHz{ 10 };
    /** @brief Number of emitters in the LiDAR sensor */
    uint32_t numberOfEmitters{ 128 };
    uint32_t emitterStateCount{ 0 };
    uint32_t maxReturns{ 2 };
    std::vector<uint32_t> numRaysPerLine;
    std::vector<EmitterState> emitterStates;
    uint32_t numLines{ 1 };
    LidarRotationDirection rotationDirection{ LidarRotationDirection::CW };
    /** @brief Whether the LiDAR sensor is 2D */
    bool is2D{ false };


    std::unique_ptr<rapidjson::Document> m_doc{ nullptr };


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

    /**
     * init document
     * @param json [in] json file name with path
     */
    void init(const char* json);

    // TODO: maybe pass in init the profile name as a string and use the getProfile internally
    // Then, we don't need an extra call to getProfileJsonAtPaths -- but we lose the flexibility to pass just a read
    // json

    /**
     * get json from given filename -- looking at internal path or at given paths
     * @param json [in] json file name with path
     */
    omni::string getProfileJsonAtPaths(const char* fileName);

    static std::string ReadWholeTextFile(std::string fullPath);
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
    omni::sensors::GenericModelOutput mGmo;
    /** @brief Union of auxiliary data structures for different sensor types */
    union
    {
        /** @brief LiDAR-specific auxiliary data */
        omni::sensors::LidarAuxiliaryData mAuxlidar;
        /** @brief Ultrasonic-specific auxiliary data */
        omni::sensors::USSAuxiliaryData mAuxUltrasonic;
        /** @brief Radar-specific auxiliary data */
        omni::sensors::RadarAuxiliaryData mAuxRadar;
    };

private:
    /** @brief CUDA pointer attributes for source data */
    cudaPointerAttributes m_srcAttrs;
    /** @brief Type of memory copy operation (device-to-host or host-to-host) */
    enum cudaMemcpyKind m_kind;
    /** @brief Pointer to raw data buffer */
    uint8_t* m_data;
    size_t m_offset;

public:
    /**
     * @brief Constructs a new Generic Model Output Helper
     * @param[in] gmoPtr Pointer to the source generic model output data
     */
    GenericModelOutputHelper(void* gmoPtr)
    {
        m_data = reinterpret_cast<uint8_t*>(gmoPtr);
        cudaPointerGetAttributes(&m_srcAttrs, gmoPtr);

        // const omni::sensors::GenericModelOutput& ingmo =
        //   *reinterpret_cast<const omni::sensors::GenericModelOutput*>(gmoPtr);
        m_kind = m_srcAttrs.type == cudaMemoryTypeDevice ? cudaMemcpyDeviceToHost : cudaMemcpyHostToHost;
        cudaMemcpyAsync(&mGmo, gmoPtr, sizeof(omni::sensors::GenericModelOutput), m_kind);
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
        if (mGmo.magicNumber != MAGIC_NUMBER_GMO || mGmo.outputType != outType ||
            mGmo.elementsCoordsType != coordType || mGmo.modality != modality)
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
        cudaMemcpyAsync(&returnMe, mAuxlidar.emitterId + sizeof(uint32_t) * i, sizeof(uint32_t), m_kind);
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
        cudaMemcpyAsync(&returnMe, mAuxlidar.tickId + sizeof(uint32_t) * i, sizeof(uint32_t), m_kind);
        return returnMe;
    }

    /**
     * @brief Sets up pointers for the generic model output structure
     * @details Initializes and configures pointers for basic elements and auxiliary data
     */
    inline void setGenericModelOutputPtrs()
    {
        GenericModelOutput* modelOutput{ &mGmo };
        if (mGmo.magicNumber != MAGIC_NUMBER_GMO)
        {
            modelOutput->elements = BasicElements(); // nullptr
            modelOutput->auxiliaryData = nullptr;
            return;
        }
        m_offset = sizeof(GenericModelOutput);
        // Basic elements
        modelOutput->elements.timeOffsetNs = reinterpret_cast<int32_t*>(m_data + m_offset);
        m_offset += sizeof(int32_t) * modelOutput->numElements;
        modelOutput->elements.x = reinterpret_cast<float*>(m_data + m_offset);
        m_offset += sizeof(float) * modelOutput->numElements;
        modelOutput->elements.y = reinterpret_cast<float*>(m_data + m_offset);
        m_offset += sizeof(float) * modelOutput->numElements;
        modelOutput->elements.z = reinterpret_cast<float*>(m_data + m_offset);
        m_offset += sizeof(float) * modelOutput->numElements;
        modelOutput->elements.scalar = reinterpret_cast<float*>(m_data + m_offset);
        m_offset += sizeof(float) * modelOutput->numElements;
        modelOutput->elements.flags = reinterpret_cast<uint8_t*>(m_data + m_offset);
        m_offset += sizeof(uint8_t) * modelOutput->numElements;
        // For the contiguous buffer, additional padding bytes are added after the last flags element (just before the
        // auxiliary data struct) to ensure that the structure is aligned to a multiple of 8 bytes.
        if (m_offset % 8 != 0)
        {
            m_offset += 8 - (m_offset % 8); // This has to be done for reading the auxiliary data from the buffer
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
        cudaMemcpyAsync(&mAuxlidar, m_data + m_offset, sizeof(LidarAuxiliaryData), m_kind);
        LidarAuxiliaryData* auxData = &mAuxlidar;
        GenericModelOutput* modelOutput{ &mGmo };
        modelOutput->auxiliaryData = reinterpret_cast<void*>(auxData);
        m_offset += sizeof(LidarAuxiliaryData);
        if ((auxData->filledAuxMembers & LidarAuxHas::EMITTER_ID) == LidarAuxHas::EMITTER_ID)
        {
            auxData->emitterId = reinterpret_cast<uint32_t*>(m_data + m_offset);
            m_offset += sizeof(uint32_t) * modelOutput->numElements;
        }
        else
        {
            auxData->emitterId = nullptr;
        }

        if ((auxData->filledAuxMembers & LidarAuxHas::CHANNEL_ID) == LidarAuxHas::CHANNEL_ID)
        {
            auxData->channelId = reinterpret_cast<uint32_t*>(m_data + m_offset);
            m_offset += sizeof(uint32_t) * modelOutput->numElements;
        }
        else
        {
            auxData->channelId = nullptr;
        }

        if ((auxData->filledAuxMembers & LidarAuxHas::MAT_ID) == LidarAuxHas::MAT_ID)
        {
            auxData->matId = reinterpret_cast<uint32_t*>(m_data + m_offset);
            m_offset += sizeof(uint32_t) * modelOutput->numElements;
        }
        else
        {
            auxData->matId = nullptr;
        }

        if ((auxData->filledAuxMembers & LidarAuxHas::TICK_ID) == LidarAuxHas::TICK_ID)
        {
            auxData->tickId = reinterpret_cast<uint32_t*>(m_data + m_offset);
            m_offset += sizeof(uint32_t) * modelOutput->numElements;
        }
        else
        {
            auxData->tickId = nullptr;
        }

        if ((auxData->filledAuxMembers & LidarAuxHas::HIT_NORMALS) == LidarAuxHas::HIT_NORMALS)
        {
            auxData->hitNormals = reinterpret_cast<float*>(m_data + m_offset);
            m_offset += sizeof(float) * modelOutput->numElements * 3;
        }
        else
        {
            auxData->hitNormals = nullptr;
        }
        if ((auxData->filledAuxMembers & LidarAuxHas::VELOCITIES) == LidarAuxHas::VELOCITIES)
        {
            auxData->velocities = reinterpret_cast<float*>(m_data + m_offset);
            m_offset += sizeof(float) * modelOutput->numElements * 3;
        }
        else
        {
            auxData->velocities = nullptr;
        }

        if ((auxData->filledAuxMembers & LidarAuxHas::OBJ_ID) == LidarAuxHas::OBJ_ID)
        {
            auxData->objId = reinterpret_cast<uint8_t*>(m_data + m_offset);
            m_offset += sizeof(uint8_t) * modelOutput->numElements;
        }
        else
        {
            auxData->objId = nullptr;
        }

        if ((auxData->filledAuxMembers & LidarAuxHas::ECHO_ID) == LidarAuxHas::ECHO_ID)
        {
            auxData->echoId = reinterpret_cast<uint8_t*>(m_data + m_offset);
            m_offset += sizeof(uint8_t) * modelOutput->numElements;
        }
        else
        {
            auxData->echoId = nullptr;
        }

        if ((auxData->filledAuxMembers & LidarAuxHas::TICK_STATES) == LidarAuxHas::TICK_STATES)
        {
            auxData->tickStates = reinterpret_cast<uint8_t*>(m_data + m_offset);
            m_offset += sizeof(uint8_t) * modelOutput->numElements;
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
        cudaMemcpyAsync(&mAuxUltrasonic, m_data + m_offset, sizeof(USSAuxiliaryData), m_kind);
        USSAuxiliaryData* auxData = &mAuxUltrasonic;
        GenericModelOutput* modelOutput{ &mGmo };
        modelOutput->auxiliaryData = reinterpret_cast<void*>(auxData);
        m_offset += sizeof(USSAuxiliaryData);
    }
    /**
     * @brief Sets up pointers for radar auxiliary data
     * @details Configures pointers for radar-specific auxiliary data fields
     */
    inline void setRadarAuxiliaryDataPtrs()
    {
        cudaMemcpyAsync(&mAuxRadar, m_data + m_offset, sizeof(RadarAuxiliaryData), m_kind);
        RadarAuxiliaryData* auxData = &mAuxRadar;
        GenericModelOutput* modelOutput{ &mGmo };
        modelOutput->auxiliaryData = reinterpret_cast<void*>(auxData);
        m_offset += sizeof(RadarAuxiliaryData);

        auxData->rv_ms = reinterpret_cast<float*>(m_data + m_offset);
        m_offset += sizeof(float) * modelOutput->numElements;
    }
};

}
}
}
