// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/InterfaceUtils.h>
#include <carb/Types.h>

#include <boost/make_shared.hpp>
#include <boost/shared_ptr.hpp>
#include <omni/isaac/utils/BaseResetNode.h>
#include <omni/math/linalg/matrix.h>
#include <omni/math/linalg/quat.h>
#include <omni/sensors/radar/IRadarPCConverter.h>
#include <pxr/usd/usdGeom/xformCache.h>

#include <OgnIsaacComputeRTXRadarPointCloudDatabase.h>
#include <iostream>
#include <math.h>

#define __DEBUG_PRINT_ON 0

namespace omni
{
namespace isaac
{
namespace sensor
{

using namespace omni::sensors::radar;

inline void convertDetectionToPoint(const RadarDetection& d, pxr::GfVec3f& p)
{
    const float sinAzimuth{ ::sinf(d.az_ang_rad) };
    const float cosAzimuth{ ::cosf(d.az_ang_rad) };
    const float sinElevation{ ::sinf(d.elev_ang_rad) };
    const float cosElevation{ ::cosf(d.elev_ang_rad) };

    const float rayDirectionX{ cosElevation * cosAzimuth };
    const float rayDirectionY{ cosElevation * sinAzimuth };
    const float rayDirectionZ{ sinElevation };

    p[0] = rayDirectionX * d.r_m;
    p[1] = rayDirectionY * d.r_m;
    p[2] = rayDirectionZ * d.r_m;
}

class OgnIsaacComputeRTXRadarPointCloud : public BaseResetNode
{
public:
    // If the node fails we want to cleanup the output
    static bool returnCleanly(OgnIsaacComputeRTXRadarPointCloudDatabase& db, bool passThroughValue, int dbv)
    {
        pxr::GfMatrix4d T = db.outputs.transform();
        T.SetIdentity();
        db.outputs.dataPtr() = 0;
        db.outputs.bufferSize() = 0;
        db.outputs.cudaDeviceIndex() = -1; // db.inputs.cudaDeviceIndex();
        db.outputs.radialDistance().resize(0);
        db.outputs.radialVelocity().resize(0);
        db.outputs.azimuth().resize(0);
        db.outputs.elevation().resize(0);
        db.outputs.rcs().resize(0);
        db.outputs.semanticId().resize(0);
        db.outputs.materialId().resize(0);
        db.outputs.objectId().resize(0);

        db.outputs.exec() = passThroughValue ? kExecutionAttributeStateEnabled : kExecutionAttributeStateDisabled;
#if __DEBUG_PRINT_ON
        std::cout << dbv << "}";
#endif
        return passThroughValue;
    }

    static bool compute(OgnIsaacComputeRTXRadarPointCloudDatabase& db)
    {
#if __DEBUG_PRINT_ON
        std::cout << "RC[";
#endif
        CARB_PROFILE_ZONE(0, "Compute RTX Radar PointCloud");
        const uint8_t* input = reinterpret_cast<const uint8_t*>(db.inputs.dataPtr());
        if (!input)
        {
            return returnCleanly(db, true, 1);
        }

        const RadarPointCloud* scan{ reinterpret_cast<const RadarPointCloud*>(input) };

        if (scan->numDetections == 0)
        {
            return returnCleanly(db, true, 2);
        }

        // want to point to the detections stored as a static size array in Provider scan.
        const RadarDetection* detections = reinterpret_cast<const RadarDetection*>(
            input + sizeof(RadarPointCloud) - MAX_DETS_PER_SCAN * sizeof(RadarDetection));

        pxr::GfMatrix4d T{ 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1. };

        pxr::UsdPrim prim =
            omni::isaac::utils::getCameraPrimFromRenderProduct(db.tokenToString(db.inputs.renderProductPath()));
        if (prim.IsValid())
        {
            pxr::UsdGeomXformCache xformCache;
            T = xformCache.GetLocalToWorldTransform(prim);
        }
        // take out ISO 8855 to world transform.
        T.SetRotateOnly(pxr::GfMatrix3d(0, 0, -1, -1, 0, 0, 0, 1, 0) *
                        pxr::GfMatrix3d(T[0][0], T[0][1], T[0][2], T[1][0], T[1][1], T[1][2], T[2][0], T[2][1], T[2][2]));
        db.outputs.transform() = T;

        db.outputs.syncData() = reinterpret_cast<uint64_t>(scan->syncData); /**< Sync primitives for syncing with model
                                                                             */
        db.outputs.sensorID() = scan->sensorID; /**< Sensor Id for sensor that generated the scan */
        db.outputs.scanIdx() = scan->scanIdx; /**< Scan index for sensors with multi scan support */
        db.outputs.timeStampNS() = scan->timeStampNS; /**< Scan timestamp in nanoseconds */
        db.outputs.cycleCnt() = scan->cycleCnt; /**< Scan cycle count */
        db.outputs.maxRangeM() = scan->maxRangeM; /**< The max unambiguous range for the scan */
        db.outputs.minVelMps() = scan->minVelMps; /**< The min unambiguous velocity for the scan */
        db.outputs.maxVelMps() = scan->maxVelMps; /**< The max unambiguous velocity for the scan */
        db.outputs.minAzRad() = scan->minAzRad; /**< The min unambiguous azimuth for the scan */
        db.outputs.maxAzRad() = scan->maxAzRad; /**< The max unambiguous azimuth for the scan */
        db.outputs.minElRad() = scan->minElRad; /**< The min unambiguous elevation for the scan */
        db.outputs.maxElRad() = scan->maxElRad; /**< The max unambiguous elevation for the scan */
        db.outputs.numDetections() = scan->numDetections; /**< The number of valid detections in the array */

        size_t numDetects = scan->numDetections;

        auto& state = db.internalState<OgnIsaacComputeRTXRadarPointCloud>();
        state.mDataPtr = boost::make_shared<pxr::GfVec3f[]>(numDetects);
        db.outputs.dataPtr() = reinterpret_cast<uint64_t>(state.mDataPtr.get());
        db.outputs.bufferSize() = numDetects * sizeof(pxr::GfVec3f);
        db.outputs.cudaDeviceIndex() = -1; // TODOMTC

#define _DEF_OUT_VAR(outName)                                                                                          \
    auto& db_outputs_##outName = db.outputs.outName();                                                                 \
    db_outputs_##outName.resize(numDetects)
        _DEF_OUT_VAR(radialDistance);
        _DEF_OUT_VAR(radialVelocity);
        _DEF_OUT_VAR(azimuth);
        _DEF_OUT_VAR(elevation);
        _DEF_OUT_VAR(rcs);
        _DEF_OUT_VAR(semanticId);
        _DEF_OUT_VAR(materialId);
        _DEF_OUT_VAR(objectId);
#undef _DEF_OUT_VAR

        for (uint32_t i = 0; i < numDetects; ++i)
        {
            const RadarDetection& d = detections[i];
            convertDetectionToPoint(d, state.mDataPtr[i]);

#define _ASSIGN_OUT(outputName, src) db_outputs_##outputName[i] = d.src
            _ASSIGN_OUT(radialDistance, r_m);
            _ASSIGN_OUT(radialVelocity, rv_ms);
            _ASSIGN_OUT(azimuth, az_ang_rad);
            _ASSIGN_OUT(elevation, elev_ang_rad);
            _ASSIGN_OUT(rcs, rcs_dbsm);
            _ASSIGN_OUT(semanticId, semId);
            _ASSIGN_OUT(materialId, matId);
            _ASSIGN_OUT(objectId, objId);
#undef _ASSIGN_OUT
        }

        db.outputs.exec() = kExecutionAttributeStateEnabled;

#if __DEBUG_PRINT_ON
        std::cout << "]";
#endif
        return true;
    }

    virtual void reset()
    {
        mDataPtr.reset();
    }

private:
    boost::shared_ptr<pxr::GfVec3f[]> mDataPtr;
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
