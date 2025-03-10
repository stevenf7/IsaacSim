// Copyright (c) 2022-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "SensorNodeUtils.h"
#include "isaacsim/core/includes/UsdUtilities.h"

#include <carb/InterfaceUtils.h>
#include <carb/Types.h>

#include <isaacsim/core/includes/Buffer.h>
#include <omni/math/linalg/matrix.h>

#include <GenericModelOutput.h>
#include <OgnIsaacComputeRTXRadarPointCloudDatabase.h>
#include <math.h>

namespace isaacsim
{
namespace sensors
{
namespace rtx
{
using namespace omni::sensors;

inline void convertDetectionToPoint(const GenericModelOutput& gmo, uint32_t idx, float3& p)
{
    const float* azAngDeg = gmo.elements.x;
    const float* elevAngDeg = gmo.elements.y;
    const float* rM = gmo.elements.z;

    const float sinAzimuth{ ::sinf(deg2Rad(azAngDeg[idx])) };
    const float cosAzimuth{ ::cosf(deg2Rad(azAngDeg[idx])) };
    const float sinElevation{ ::sinf(deg2Rad(elevAngDeg[idx])) };
    const float cosElevation{ ::cosf(deg2Rad(elevAngDeg[idx])) };

    const float rayDirectionX{ cosElevation * cosAzimuth };
    const float rayDirectionY{ cosElevation * sinAzimuth };
    const float rayDirectionZ{ sinElevation };

    p.x = rayDirectionX * rM[idx];
    p.y = rayDirectionY * rM[idx];
    p.z = rayDirectionZ * rM[idx];
}

class OgnIsaacComputeRTXRadarPointCloud
{
public:
    static bool compute(OgnIsaacComputeRTXRadarPointCloudDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Compute RTX Radar PointCloud");

        db.outputs.exec() = db.inputs.exec();
        db.outputs.dataPtr() = 0;
        db.outputs.cudaDeviceIndex() = -1; // db.inputs.cudaDeviceIndex();
        db.outputs.bufferSize() = 0;
        db.outputs.width() = 0;
        db.outputs.height() = 1;
        auto& matrixOutput = *reinterpret_cast<omni::math::linalg::matrix4d*>(&db.outputs.transform());
        matrixOutput.SetIdentity();

        uint8_t* input = reinterpret_cast<uint8_t*>(db.inputs.dataPtr());
        if (!input)
        {
            return true;
        }
        auto& state = db.perInstanceState<OgnIsaacComputeRTXRadarPointCloud>();

        GenericModelOutputHelper helper(input);
        if (!helper.isValid(OutputType::POINTCLOUD, CoordsType::SPHERICAL, Modality::RADAR))
        {
            CARB_LOG_WARN(
                "Input to IsaacComputeRTXRadarPointCloud is not a valid RADAR POINTCLOUD type. Buffer will not be parsed.");
            return true;
        }
        if (helper.mGmo.numElements == 0)
        {
            return true;
        }
        omni::sensors::FrameAtTime frameEnd;
#define RADAR_HAS_NO_TRANSFORM
        // When the GMO output for the radar starts outputing the correct transform, you can
        // undefine this.
#ifndef RADAR_HAS_NO_TRANSFORM
        frameEnd = helper.mGmo.frameEnd;
#else
        pxr::GfVec3d translate{ 0, 0, 0 };
        pxr::GfQuatd rotate{ 1, 0, 0, 0 };
        pxr::UsdAttribute transAttr = isaacsim::core::includes::getCameraAttributeFromRenderProduct(
            "xformOp:translate", db.tokenToString(db.inputs.renderProductPath()));
        pxr::UsdAttribute rotAttr = isaacsim::core::includes::getCameraAttributeFromRenderProduct(
            "xformOp:orient", db.tokenToString(db.inputs.renderProductPath()));
        if (transAttr.IsValid() && rotAttr.IsValid())
        {
            isaacsim::core::includes::safeGetAttribute(transAttr, translate);
            isaacsim::core::includes::safeGetAttribute(rotAttr, rotate);
        }
        frameEnd.orientation[3] = (float)rotate.GetReal();
        frameEnd.orientation[0] = (float)rotate.GetImaginary()[0];
        frameEnd.orientation[1] = (float)rotate.GetImaginary()[1];
        frameEnd.orientation[2] = (float)rotate.GetImaginary()[2];
        frameEnd.posM[0] = (float)translate[0];
        frameEnd.posM[1] = (float)translate[1];
        frameEnd.posM[2] = (float)translate[2];
#endif
        getTransformFromSensorPose(frameEnd, matrixOutput);
        RadarAuxiliaryData* aux = reinterpret_cast<RadarAuxiliaryData*>(helper.mGmo.auxiliaryData);

        // for the radar data:
        // x = az_ang_rad
        // y = elev_ang_rad
        // z = rM
        // scalar = rcs_dbsm
        // aux->rv_ms = rv_ms
        db.outputs.sensorID() = aux->sensorID; /**< Sensor Id for sensor that generated the aux */
        db.outputs.scanIdx() = aux->scanIdx; /**< Scan index for sensors with multi aux support */
        db.outputs.cycleCnt() = aux->cycleCnt; /**< Scan cycle count */
        db.outputs.maxRangeM() = aux->maxRangeM; /**< The max unambiguous range for the aux */
        db.outputs.minVelMps() = aux->minVelMps; /**< The min unambiguous velocity for the aux */
        db.outputs.maxVelMps() = aux->maxVelMps; /**< The max unambiguous velocity for the aux */
        db.outputs.minAzRad() = aux->minAzRad; /**< The min unambiguous azimuth for the aux */
        db.outputs.maxAzRad() = aux->maxAzRad; /**< The max unambiguous azimuth for the aux */
        db.outputs.minElRad() = aux->minElRad; /**< The min unambiguous elevation for the aux */
        db.outputs.maxElRad() = aux->maxElRad; /**< The max unambiguous elevation for the aux */

        size_t outSize = helper.mGmo.numElements; // aux->numDetections;

        state.m_hostPcBuffer.resize(outSize, make_float3(0.0f, 0.0f, 0.0f));
        float3* dataPtr = state.m_hostPcBuffer.data();
        db.outputs.dataPtr() = reinterpret_cast<uint64_t>(dataPtr);

        db.outputs.bufferSize() = outSize * sizeof(pxr::GfVec3f);
        db.outputs.cudaDeviceIndex() = -1; // TODO
        db.outputs.width() = static_cast<uint32_t>(outSize);
        db.outputs.height() = 1;

#define DEF_OUT_VAR(outName)                                                                                           \
    auto& db_outputs_##outName = db.outputs.outName();                                                                 \
    db_outputs_##outName.resize(outSize)
        DEF_OUT_VAR(radialDistance);
        DEF_OUT_VAR(radialVelocity);
        DEF_OUT_VAR(azimuth);
        DEF_OUT_VAR(elevation);
        DEF_OUT_VAR(rcs);
#undef DEF_OUT_VAR

        for (uint32_t i = 0; i < outSize; ++i)
        {
            // Test for point validiy
            if ((helper.mGmo.elements.flags[i] & ElementFlags::VALID) != ElementFlags::VALID)
            {
                continue;
            }
            convertDetectionToPoint(helper.mGmo, i, dataPtr[i]);

            // x = azAngDeg
            // y = elevAngDeg
            // z = rM
            // scalar = rcs_dbsm
            // aux->rv_ms = rv_ms
#define IF_ASSIGN_OUT(has, outputName, src) db_outputs_##outputName[i] = (has) ? src[i] : 0
            IF_ASSIGN_OUT(true, radialDistance, helper.mGmo.elements.z);
            IF_ASSIGN_OUT(true, radialVelocity, aux->rv_ms);
            IF_ASSIGN_OUT(true, azimuth, helper.mGmo.elements.x);
            IF_ASSIGN_OUT(true, elevation, helper.mGmo.elements.y);
            IF_ASSIGN_OUT(true, rcs, helper.mGmo.elements.scalar);
#undef IF_ASSIGN_OUT
        }

        return true;
    }

private:
    isaacsim::core::includes::HostBufferBase<float3> m_hostPcBuffer;
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
