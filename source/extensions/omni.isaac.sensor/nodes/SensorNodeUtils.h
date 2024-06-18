// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <omni/math/linalg/matrix.h>
#include <omni/sensors/GMOAuxiliaryData.h>
#include <omni/sensors/GenericModelOutputTypes.h>
#include <omni/sensors/lidar/LidarProfileTypes.h>

namespace omni
{
using namespace sensors;
namespace isaac
{
namespace sensor
{

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

class LidarConfigHelper
{
public:
    std::string config;
    LidarScanType scanType{ LidarScanType::kUnknown };
    LidarProfile* profile; // convenient pointer to lidar profile stored in profileBuffer
    std::vector<uint8_t> profileBuffer; // data buffer containing lidar profile

    float getNearRange() const;
    float getFarRange() const;
    uint32_t getNumChannels() const;
    uint32_t getNumEchos() const;
    uint32_t getReturnsPerScan() const;
    uint32_t getTicksPerScan() const;
    bool updateLidarConfig(const char* renderProductPath);
};

// GenericModelOutputHelper is used when you want a host side copy of a
// gmo, and you want pointers in elements and aux to be kept from the input
class GenericModelOutputHelper
{
public:
    omni::sensors::GenericModelOutput m_gmo;
    union
    {
        omni::sensors::LidarAuxiliaryData m_auxlidar;
        omni::sensors::USSAuxiliaryData m_auxUltrasonic;
        omni::sensors::RadarAuxiliaryData m_auxRadar;
    };

private:
    cudaPointerAttributes srcAttrs;
    enum cudaMemcpyKind kind;
    uint8_t* data;
    size_t offset;

public:
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
    bool isValid(const OutputType& outType, const CoordsType& coordType, const AuxType& auxType)
    {
        if (m_gmo.magicNumber != MAGIC_NUMBER_GMO || m_gmo.outputType != outType || m_gmo.coordsType != coordType ||
            m_gmo.auxType != auxType)
        {
            return false;
        }
        return true;
    }
    uint32_t getEmitterId(int i) const
    {
        uint32_t returnMe;
        cudaMemcpyAsync(&returnMe, m_auxlidar.emitterId + sizeof(uint32_t) * i, sizeof(uint32_t), kind);
        return returnMe;
    }
    uint32_t getTickId(int i) const
    {
        uint32_t returnMe;
        cudaMemcpyAsync(&returnMe, m_auxlidar.tickId + sizeof(uint32_t) * i, sizeof(uint32_t), kind);
        return returnMe;
    }

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
        // aux elements
        if (modelOutput->auxType == AuxType::LIDAR)
        {
            setLidarAuxiliaryDataPtrs();
        }
        else if (modelOutput->auxType == AuxType::USS)
        {
            setUSSAuxiliaryDataPtrs();
        }
        else if (modelOutput->auxType == AuxType::RADAR)
        {
            setRadarAuxiliaryDataPtrs();
        }
    }
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
        if ((auxData->filledAuxMembers & LidarAuxHas::ECHO_ID) == LidarAuxHas::ECHO_ID)
        {
            auxData->echoId = reinterpret_cast<uint8_t*>(data + offset);
            offset += sizeof(uint8_t) * modelOutput->numElements;
        }
        else
        {
            auxData->echoId = nullptr;
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
        if ((auxData->filledAuxMembers & LidarAuxHas::OBJ_ID) == LidarAuxHas::OBJ_ID)
        {
            auxData->objId = reinterpret_cast<uint32_t*>(data + offset);
            offset += sizeof(uint32_t) * modelOutput->numElements;
        }
        else
        {
            auxData->objId = nullptr;
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
        if ((auxData->filledAuxMembers & LidarAuxHas::TICK_STATES) == LidarAuxHas::TICK_STATES)
        {
            auxData->tickStates = reinterpret_cast<uint8_t*>(data + offset);
            offset += sizeof(uint8_t) * modelOutput->numElements;
        }
        else
        {
            auxData->tickStates = nullptr;
        }
        if ((auxData->filledAuxMembers & LidarAuxHas::HIT_NORMALS) == LidarAuxHas::HIT_NORMALS)
        {
            auxData->hitNormals = reinterpret_cast<float*>(data + offset);
            offset += sizeof(float) * 3 * modelOutput->numElements;
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
    }
    inline void setUSSAuxiliaryDataPtrs()
    {
        // USSAuxiliaryData auxData;
        cudaMemcpyAsync(&m_auxUltrasonic, data + offset, sizeof(USSAuxiliaryData), kind);
        USSAuxiliaryData* auxData = &m_auxUltrasonic;
        GenericModelOutput* modelOutput{ &m_gmo };
        modelOutput->auxiliaryData = reinterpret_cast<void*>(auxData);
        offset += sizeof(USSAuxiliaryData);
    }
    inline void setRadarAuxiliaryDataPtrs()
    {
        cudaMemcpyAsync(&m_auxRadar, data + offset, sizeof(RadarAuxiliaryData), kind);
        RadarAuxiliaryData* auxData = &m_auxRadar;
        GenericModelOutput* modelOutput{ &m_gmo };
        modelOutput->auxiliaryData = reinterpret_cast<void*>(auxData);
        offset += sizeof(RadarAuxiliaryData);

        auxData->rv_ms = reinterpret_cast<float*>(data + offset);
        offset += sizeof(float) * modelOutput->numElements;

        if ((auxData->filledAuxMembers & RadarAuxHas::SEM_ID) == RadarAuxHas::SEM_ID)
        {
            auxData->semId = reinterpret_cast<uint32_t*>(data + offset);
            offset += sizeof(uint32_t) * modelOutput->numElements;
        }
        else
        {
            auxData->semId = nullptr;
        }

        if ((auxData->filledAuxMembers & RadarAuxHas::MAT_ID) == RadarAuxHas::MAT_ID)
        {
            auxData->matId = reinterpret_cast<uint32_t*>(data + offset);
            offset += sizeof(uint32_t) * modelOutput->numElements;
        }
        else
        {
            auxData->matId = nullptr;
        }

        if ((auxData->filledAuxMembers & RadarAuxHas::OBJ_ID) == RadarAuxHas::OBJ_ID)
        {
            auxData->objId = reinterpret_cast<uint32_t*>(data + offset);
            offset += sizeof(uint32_t) * modelOutput->numElements;
        }
        else
        {
            auxData->objId = nullptr;
        }
    }
};

}
}
}
