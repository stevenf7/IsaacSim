// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
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
#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/InterfaceUtils.h>
#include <carb/Types.h>

#include <omni/isaac/utils/Buffer.h>
#include <omni/math/linalg/matrix.h>
#include <omni/sensors/GenericModelOutput.h>

#include <OgnIsaacComputeRTXRadarPointCloudDatabase.h>
#include <math.h>

namespace omni
{
using namespace sensors;
namespace isaac
{
namespace sensor
{

inline void convertDetectionToPoint(const GenericModelOutput& gmo, uint32_t idx, float3& p)
{
    const float* az_ang_deg = gmo.elements.x;
    const float* elev_ang_deg = gmo.elements.y;
    const float* r_m = gmo.elements.z;

    const float sinAzimuth{ ::sinf(Deg2Rad(az_ang_deg[idx])) };
    const float cosAzimuth{ ::cosf(Deg2Rad(az_ang_deg[idx])) };
    const float sinElevation{ ::sinf(Deg2Rad(elev_ang_deg[idx])) };
    const float cosElevation{ ::cosf(Deg2Rad(elev_ang_deg[idx])) };

    const float rayDirectionX{ cosElevation * cosAzimuth };
    const float rayDirectionY{ cosElevation * sinAzimuth };
    const float rayDirectionZ{ sinElevation };

    p.x = rayDirectionX * r_m[idx];
    p.y = rayDirectionY * r_m[idx];
    p.z = rayDirectionZ * r_m[idx];
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
        if (!helper.isValid(OutputType::POINTCLOUD, CoordsType::SPHERICAL, AuxType::RADAR))
        {
            CARB_LOG_WARN(
                "Input to IsaacComputeRTXRadarPointCloud is not a valid RADAR POINTCLOUD type. Buffer will not be parsed.");
            return true;
        }
        if (helper.m_gmo.numElements == 0)
        {
            return true;
        }
        omni::sensors::FrameAtTime frameEnd;
#define RADAR_HAS_NO_TRANSFORM
        // When the GMO output for the radar starts outputing the correct transform, you can
        // undefine this.
#ifndef RADAR_HAS_NO_TRANSFORM
        frameEnd = helper.m_gmo.frameEnd;
#else
        pxr::GfVec3d translate{ 0, 0, 0 };
        pxr::GfQuatd rotate{ 1, 0, 0, 0 };
        pxr::UsdAttribute transAttr = omni::isaac::utils::getCameraAttributeFromRenderProduct(
            "xformOp:translate", db.tokenToString(db.inputs.renderProductPath()));
        pxr::UsdAttribute rotAttr = omni::isaac::utils::getCameraAttributeFromRenderProduct(
            "xformOp:orient", db.tokenToString(db.inputs.renderProductPath()));
        if (transAttr.IsValid() && rotAttr.IsValid())
        {
            omni::isaac::utils::safeGetAttribute(transAttr, translate);
            omni::isaac::utils::safeGetAttribute(rotAttr, rotate);
        }
        frameEnd.orientation.w = (float)rotate.GetReal();
        frameEnd.orientation.x = (float)rotate.GetImaginary()[0];
        frameEnd.orientation.y = (float)rotate.GetImaginary()[1];
        frameEnd.orientation.z = (float)rotate.GetImaginary()[2];
        frameEnd.posM.x = (float)translate[0];
        frameEnd.posM.y = (float)translate[1];
        frameEnd.posM.z = (float)translate[2];
#endif
        getTransformFromSensorPose(frameEnd, matrixOutput);
        RadarAuxiliaryData* aux = reinterpret_cast<RadarAuxiliaryData*>(helper.m_gmo.auxiliaryData);

        // for the radar data:
        // x = az_ang_rad
        // y = elev_ang_rad
        // z = r_m
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
        db.outputs.numDetections() = aux->numDetections; /**< The number of valid detections in the array */

        size_t outSize = helper.m_gmo.numElements; // aux->numDetections;

        state.hostPcBuffer.resize(outSize, make_float3(0.0f, 0.0f, 0.0f));
        float3* dataPtr = state.hostPcBuffer.data();
        db.outputs.dataPtr() = reinterpret_cast<uint64_t>(dataPtr);

        db.outputs.bufferSize() = outSize * sizeof(pxr::GfVec3f);
        db.outputs.cudaDeviceIndex() = -1; // TODO
        db.outputs.width() = static_cast<uint32_t>(outSize);
        db.outputs.height() = 1;

#define _DEF_OUT_VAR(outName)                                                                                          \
    auto& db_outputs_##outName = db.outputs.outName();                                                                 \
    db_outputs_##outName.resize(outSize)
        _DEF_OUT_VAR(radialDistance);
        _DEF_OUT_VAR(radialVelocity);
        _DEF_OUT_VAR(azimuth);
        _DEF_OUT_VAR(elevation);
        _DEF_OUT_VAR(rcs);
        _DEF_OUT_VAR(semanticId);
        _DEF_OUT_VAR(materialId);
        _DEF_OUT_VAR(objectId);
#undef _DEF_OUT_VAR
        bool hasSemId = ((aux->filledAuxMembers & RadarAuxHas::SEM_ID) == RadarAuxHas::SEM_ID);
        bool hasMatId = ((aux->filledAuxMembers & RadarAuxHas::MAT_ID) == RadarAuxHas::MAT_ID);
        bool hasObjId = ((aux->filledAuxMembers & RadarAuxHas::OBJ_ID) == RadarAuxHas::OBJ_ID);

        for (uint32_t i = 0; i < outSize; ++i)
        {
            convertDetectionToPoint(helper.m_gmo, i, dataPtr[i]);

            // x = az_ang_deg
            // y = elev_ang_deg
            // z = r_m
            // scalar = rcs_dbsm
            // aux->rv_ms = rv_ms
#define _IF_ASSIGN_OUT(has, outputName, src) db_outputs_##outputName[i] = (has) ? src[i] : 0
            _IF_ASSIGN_OUT(true, radialDistance, helper.m_gmo.elements.z);
            _IF_ASSIGN_OUT(true, radialVelocity, aux->rv_ms);
            _IF_ASSIGN_OUT(true, azimuth, helper.m_gmo.elements.x);
            _IF_ASSIGN_OUT(true, elevation, helper.m_gmo.elements.y);
            _IF_ASSIGN_OUT(true, rcs, helper.m_gmo.elements.scalar);
            _IF_ASSIGN_OUT(hasSemId, semanticId, aux->semId);
            _IF_ASSIGN_OUT(hasMatId, materialId, aux->matId);
            _IF_ASSIGN_OUT(hasObjId, objectId, aux->objId);
#undef _IF_ASSIGN_OUT
        }

        return true;
    }

private:
    isaac::utils::HostBufferBase<float3> hostPcBuffer;
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
