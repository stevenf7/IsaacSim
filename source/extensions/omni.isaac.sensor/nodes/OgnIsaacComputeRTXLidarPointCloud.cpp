// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#ifndef _WIN32

// clang-format off
#include <UsdPCH.h>
// clang-format on

#    include "omni/isaac/utils/UsdUtilities.h"

#    include <carb/InterfaceUtils.h>

#    include <internal/omni/sensors/lidar/LidarSettings.h>
#    include <omni/isaac/utils/BaseResetNode.h>
#    include <omni/math/linalg/matrix.h>
#    include <omni/math/linalg/quat.h>
#    include <omni/sensors/lidar/ILidarProfileReader.h>
#    include <omni/sensors/lidar/ILidarProfileReaderFactory.h>
#    include <omni/sensors/lidar/LidarParameterType.h>
#    include <omni/sensors/lidar/LidarReturnTypes.h>
//#    pragma GCC push_options
//#    pragma GCC optimize("unroll-loops")
#    include <omni/sensors/LidarPointsConvert.h>
//#    pragma GCC pop_options

// #include <tbb/atomic.h>
// #include <tbb/parallel_for.h>

#    include <OgnIsaacComputeRTXLidarPointCloudDatabase.h>
#    include <iostream>
#    include <math.h>
#    define __DEBUG_PRINT_ON 0
namespace omni::isaac::sensor
{

inline void convertReturnToPoint(omni::sensors::lidar::LidarPoint& point,
                                 const LidarReturn& lidarReturn,
                                 const LidarBaseProfile* profile,
                                 const EmitterProfile* emitterProfile)
{
    // const float azimuthDeg = (rightHanded ? (360.f - lidarReturn.azimuthDeg) : lidarReturn.azimuthDeg);
    const float azimuthDeg = 360.f - lidarReturn.azimuthDeg;
    const float elevationDeg{ lidarReturn.elevationDeg };

    const float azimuthRad{ Deg2Rad(azimuthDeg) };
    const float elevationRad{ Deg2Rad(elevationDeg) };

    const float sinAzimuth{ ::sinf(azimuthRad) };
    const float cosAzimuth{ ::cosf(azimuthRad) };
    const float sinElevation{ ::sinf(elevationRad) };
    const float cosElevation{ ::cosf(elevationRad) };

    const float rawDistanceM = lidarReturn.distance;

    // Ray direction in meter
    const float rayDirectionX{ cosElevation * cosAzimuth };
    const float rayDirectionY{ cosElevation * sinAzimuth };
    const float rayDirectionZ{ sinElevation };

    // Ray origin in meter
    float3 rayOrigin{ 0, 0, 0 };

    float distanceCorrectionM = 0.0f;
    float beamOriginMY = 0.0f;
    float beamOriginMZ = 0.0f;
    float beamOriginDistM = 0.0f;
    if (emitterProfile)
    {
        distanceCorrectionM = emitterProfile->distanceCorrectionM;
        beamOriginMY = emitterProfile->horOffsetM;
        beamOriginMZ = emitterProfile->vertOffsetM;
        rayOrigin = { -sinAzimuth * beamOriginMY, cosAzimuth * beamOriginMY, beamOriginMZ };
        beamOriginDistM = beamOriginMY * beamOriginMY + beamOriginMZ * beamOriginMZ;
        beamOriginDistM = beamOriginDistM > FLT_EPSILON ? ::sqrtf(beamOriginDistM) : 0.f;
    }

    const float distanceM = rawDistanceM + distanceCorrectionM;

    point.x = rayOrigin.x + rayDirectionX * distanceM;
    point.y = rayOrigin.y + rayDirectionY * distanceM;
    point.z = rayOrigin.z + rayDirectionZ * distanceM;

    // Add beam origin distance directly? -> see differences in resim
    point.range = distanceM + beamOriginDistM;
    point.intensity =
        profile ?
            static_cast<float>(omni::sensors::lidar::mapIntensity<uint16_t>(*profile, lidarReturn.intensity)) / 100.f :
            lidarReturn.intensity;

    point.azimuth = azimuthRad;
    point.elevation = elevationRad;

    // if (rightHanded)
    point.azimuth = Deg2Rad(360.f) - point.azimuth;
    // fit azimuth into [-PI, PI] ala atan2
    if (point.azimuth > Deg2Rad(180.f))
        point.azimuth -= Deg2Rad(360.f);
}

class OgnIsaacComputeRTXLidarPointCloud : public BaseResetNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state =
            OgnIsaacComputeRTXLidarPointCloudDatabase::sInternalState<OgnIsaacComputeRTXLidarPointCloud>(nodeObj);
        state.mLidarDeleted = false;
        state.mConfig = "";
        state.mScanType = LidarScanType::kUnknown;
    }

    // If the node fails we want to cleanup the output
    static bool returnCleanly(OgnIsaacComputeRTXLidarPointCloudDatabase& db, bool passThroughReturnValue, int dbv)
    {
        auto& matrixOutput = *reinterpret_cast<omni::math::linalg::matrix4d*>(&db.outputs.toWorldMatrix());
        matrixOutput.SetIdentity();
        db.outputs.pointCloudData().resize(0);
        db.outputs.intensity().resize(0);
        db.outputs.range().resize(0);
        db.outputs.azimuth().resize(0);
        db.outputs.elevation().resize(0);

        db.outputs.execOut() =
            passThroughReturnValue ? kExecutionAttributeStateEnabled : kExecutionAttributeStateDisabled;
#    if __DEBUG_PRINT_ON
        std::cout << dbv << "}";
#    endif
        return passThroughReturnValue;
    }

    static bool compute(OgnIsaacComputeRTXLidarPointCloudDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Compute RTX Lidar PointCloud");
#    if __DEBUG_PRINT_ON
        std::cout << "LC[";
#    endif
        const uint8_t* input = reinterpret_cast<const uint8_t*>(db.inputs.cpuPointer());
        if (!input)
        {
            return returnCleanly(db, true, 1);
        }

        const LidarParameterType* parameter{ reinterpret_cast<const LidarParameterType*>(input) };

        if (parameter->async.numTicks == 0 || parameter->async.numChannels * parameter->async.numEchos == 0)
        {
            return returnCleanly(db, true, 2);
        }

        auto& state = db.internalState<OgnIsaacComputeRTXLidarPointCloud>();

        std::string curConfig = "";
        pxr::UsdAttribute configAttr = omni::isaac::utils::getCameraAttributeFromRenderProduct(
            "sensorModelConfig", db.tokenToString(db.inputs.renderProductPath()));
        if (configAttr.IsValid())
        {
            omni::isaac::utils::safeGetAttribute(configAttr, curConfig);
        }

        if (curConfig != state.mConfig)
        {
            state.mConfig = curConfig;
            if (curConfig != "")
            {
                state.mLidarDeleted = false;
                const std::string json = omni::sensors::nv::lidar::getProfileJsonAtPaths(curConfig);
                omni::sensors::lidar::ILidarProfileReaderPtr profileReader =
                    carb::getFramework()
                        ->acquireInterface<omni::sensors::lidar::ILidarProfileReaderFactory>()
                        ->createInstance();
                if (profileReader)
                {
                    profileReader->init(json.c_str());
                    state.mScanType = profileReader->lidarScanType();
                    if (state.mScanType == LidarScanType::kSolidState)
                    {
                        profileReader->update((void*)&state.mSolidStateProfile);
                    }
                    else if (state.mScanType == LidarScanType::kRotary)
                    {
                        profileReader->update((void*)&state.mRotaryProfile);
                    }
                }
            }
            else
            {
                // config switched from valid to ""
                state.mLidarDeleted = true;
                return returnCleanly(db, true, 3);
            }
        }

        if (state.mLidarDeleted)
            return returnCleanly(db, true, 4);
        if (curConfig == "" || state.mScanType == LidarScanType::kUnknown)
        {
            if (curConfig == "")
            {
                CARB_LOG_WARN_ONCE("A Compute RTX Lidar PointCloud node can't get the lidar configuration file.");
            }
            else
            {
                CARB_LOG_WARN_ONCE(
                    "A Compute RTX Lidar PointCloud node tried to read a corrupt or missing profile named %s.",
                    curConfig.c_str());
            }
        }

        // async.pose is [X, Y, Z, W].
        // quatd is i,j,k,w, but constructor is quatd(w, i, j, k)
        omni::math::linalg::vec3d posM{ parameter->async.frameEnd.posM[0], parameter->async.frameEnd.posM[1],
                                        parameter->async.frameEnd.posM[2] };
        omni::math::linalg::quatd pose{ parameter->async.frameEnd.orientation[3],
                                        parameter->async.frameEnd.orientation[0],
                                        parameter->async.frameEnd.orientation[1],
                                        parameter->async.frameEnd.orientation[2] };
        auto& matrixOutput = *reinterpret_cast<omni::math::linalg::matrix4d*>(&db.outputs.toWorldMatrix());
        matrixOutput.SetIdentity();
        matrixOutput.SetRotateOnly(pose);
        matrixOutput.SetTranslateOnly(posM);

        const LidarTick* lidarTicks = reinterpret_cast<const LidarTick*>(input + sizeof(LidarParameterType));
        const LidarReturn* lidarReturns = reinterpret_cast<const LidarReturn*>(
            input + sizeof(LidarParameterType) + sizeof(LidarTick) * parameter->async.numTicks);

        const size_t maxSize = parameter->async.numChannels * parameter->async.numEchos * parameter->async.numTicks;

        bool keepOnlyPositiveDistance = db.inputs.keepOnlyPositiveDistance();
        size_t outSize = 0;
        if (keepOnlyPositiveDistance)
        {
            for (size_t i = 0; i < maxSize; ++i)
            {
                if (lidarReturns[i].distance > 0.f)
                {
                    outSize++;
                }
            }
        }
        else
        {
            outSize = maxSize;
        }

#    define _DEF_OUT_VAR(outName)                                                                                      \
        auto& db_outputs_##outName = db.outputs.outName();                                                             \
        db_outputs_##outName.resize(outSize)
        _DEF_OUT_VAR(pointCloudData);
        _DEF_OUT_VAR(intensity);
        _DEF_OUT_VAR(range);
        _DEF_OUT_VAR(azimuth);
        _DEF_OUT_VAR(elevation);
#    undef _DEF_OUT_VAR

        carb::Float3 accuracyErrorPosition{ db.inputs.accuracyErrorPosition()[0], db.inputs.accuracyErrorPosition()[1],
                                            db.inputs.accuracyErrorPosition()[2] };
        float accuracyErrorAzimuthDeg = db.inputs.accuracyErrorAzimuthDeg();
        float accuracyErrorElevationDeg = db.inputs.accuracyErrorElevationDeg();

        // const bool rightHanded = true; // TODO How should we decide this?
        // Solid state lidar only give out points for one tick at a time. see:
        //     drivesim code base LidarPCConverterHelper.h
        // NOTE: in Drivesim code, Solid State lidar does not use profile or emitterProfile ATM.
        const LidarBaseProfile* profile = state.mScanType == LidarScanType::kRotary ?
                                              reinterpret_cast<const LidarBaseProfile*>(&state.mRotaryProfile) :
                                              nullptr;
        uint32_t numTicks = state.mScanType == LidarScanType::kRotary ? parameter->async.numTicks : 1;
        uint32_t atomicOutIdx = 0;
        for (uint32_t tick = 0; tick < numTicks; tick++)
        {
            const LidarTick& lidarTick = lidarTicks[tick];
            for (uint32_t channelId = 0; channelId < parameter->async.numChannels; ++channelId)
            {
                for (uint32_t echoId = 0; echoId < parameter->async.numEchos; ++echoId)
                {
                    const uint32_t pointIdx{ idxOfReturn(
                        channelId, echoId, parameter->async.numEchos, parameter->async.numChannels, tick) };
                    // If we didn't have accuracy error we could do const LidarReturn& lidarReturn here.
                    LidarReturn lidarReturn = lidarReturns[pointIdx];
                    lidarReturn.azimuthDeg += accuracyErrorAzimuthDeg;
                    lidarReturn.elevationDeg += accuracyErrorElevationDeg;

                    // This is just for runtime efficiency
                    omni::sensors::lidar::LidarPoint p;
                    if (!keepOnlyPositiveDistance || lidarReturn.distance > 0.f)
                    {
                        const uint32_t outIdx = keepOnlyPositiveDistance ? atomicOutIdx++ : pointIdx;
                        // NOTE: in drivesim, emitterProfile is not used for Solid State lidar.
                        const EmitterProfile* emitterProfile =
                            state.mScanType == LidarScanType::kRotary ?
                                &state.mRotaryProfile.emitterStates[lidarTick.state].emitterProfiles[lidarReturn.emitterId] :
                                // state.mScanType == LidarScanType::kSolidState ?
                                // &state.mSolidStateProfile.emitterStates[lidarTick.state].emitterProfiles[lidarReturn.emitterId]
                                // :
                                nullptr;

                        convertReturnToPoint(p, lidarReturn, profile, emitterProfile);
                        p.x += accuracyErrorPosition.x;
                        p.y += accuracyErrorPosition.y;
                        p.z += accuracyErrorPosition.z;

#    define _ASSIGN_OUT(outputName, index, comp, src) db_outputs_##outputName[index] comp = p.src

                        _ASSIGN_OUT(pointCloudData, outIdx, [0], x);
                        _ASSIGN_OUT(pointCloudData, outIdx, [1], y);
                        _ASSIGN_OUT(pointCloudData, outIdx, [2], z);
                        _ASSIGN_OUT(intensity, outIdx, , intensity);
                        _ASSIGN_OUT(range, outIdx, , range);
                        _ASSIGN_OUT(azimuth, outIdx, , azimuth);
                        _ASSIGN_OUT(elevation, outIdx, , azimuth);

#    undef _ASSIGN_OUT
                    }
                }
            }
        }

        db.outputs.execOut() = kExecutionAttributeStateEnabled;

#    if __DEBUG_PRINT_ON
        std::cout << "]";
#    endif
        return true;
    }

    virtual void reset()
    {
        mConfig = "";
        mScanType = LidarScanType::kUnknown;
        mLidarDeleted = false;
    }

private:
    bool mLidarDeleted;
    std::string mConfig;
    LidarScanType mScanType{ LidarScanType::kUnknown };
    LidarSolidStateProfile mSolidStateProfile;
    LidarRotaryProfile mRotaryProfile;
};

REGISTER_OGN_NODE()
} // omni::isaac::sensor
#endif
