// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
// clang-format off
#ifndef _WIN32
#include <UsdPCH.h>
// clang-format on

#    include "omni/isaac/utils/UsdUtilities.h"

#    include <carb/InterfaceUtils.h>
#    include <carb/Types.h>

#    include <omni/drivesim/sensors/radar/RadarProvider_Types.h>
#    include <omni/isaac/utils/BaseResetNode.h>
#    include <omni/math/linalg/matrix.h>
#    include <omni/math/linalg/quat.h>

#    include <OgnIsaacComputeRTXRadarPointCloudDatabase.h>
#    include <iostream>
#    include <math.h>

#    define __DEBUG_PRINT_ON 0
namespace omni
{
namespace isaac
{
namespace sensor
{

inline void convertDetectionToPoint(const ProviderDetection& d, pxr::GfVec3f& p)
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
    inline static bool needOutput(const NodeObj& nodeObj, NameToken attrName)
    {
        const AttributeObj attr = nodeObj.iNode->getAttributeByToken(nodeObj, attrName);
        return attr.iAttribute->getDownstreamConnectionCount(attr);
    }

public:
    static bool compute(OgnIsaacComputeRTXRadarPointCloudDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Compute RTX Radar PointCloud");
        const uint8_t* input = reinterpret_cast<const uint8_t*>(db.inputs.cpuPointer());
        if (!input)
        {
            return true;
        }

        const ProviderScan* scan{ reinterpret_cast<const ProviderScan*>(input) };

        if (scan->numDetections == 0)
        {
            return true;
        }

        // want to point to the detections stored as a static size array in Provider scan.
        const ProviderDetection* detections = reinterpret_cast<const ProviderDetection*>(
            input + sizeof(ProviderScan) - MAX_DETS_PER_SCAN * sizeof(ProviderDetection));

        // take out ISO 8855 to world transform.
        pxr::GfMatrix4d T = db.inputs.transform();
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

        auto& nodeObj = db.abi_node();
        bool outputNeeded = false;

#    define _DEFINE_OUTPUT_VARS(outputName)                                                                            \
        auto& db_outputs_##outputName = db.outputs.outputName();                                                       \
        bool needed_##outputName = needOutput(nodeObj, outputs::outputName.m_token);                                   \
        outputNeeded |= needed_##outputName

        _DEFINE_OUTPUT_VARS(pointCloudData);
        _DEFINE_OUTPUT_VARS(radialDistance);
        _DEFINE_OUTPUT_VARS(radialVelocity);
        _DEFINE_OUTPUT_VARS(azimuth);
        _DEFINE_OUTPUT_VARS(elevation);
        _DEFINE_OUTPUT_VARS(rcs);
        _DEFINE_OUTPUT_VARS(semanticId);
        _DEFINE_OUTPUT_VARS(materialId);
        _DEFINE_OUTPUT_VARS(objectId);
#    undef _DEFINE_OUTPUT_VARS

        if (!outputNeeded)
        {
            db.outputs.execOut() = kExecutionAttributeStateEnabled;
            return true;
        }
        size_t numDetects = scan->numDetections;
        // allocate mem for the output#define
#    define _RESIZE_IF_NEEDED(outputName, size)                                                                        \
        if (needed_##outputName)                                                                                       \
        db_outputs_##outputName.resize(size)
        _RESIZE_IF_NEEDED(pointCloudData, numDetects);
        _RESIZE_IF_NEEDED(radialDistance, numDetects);
        _RESIZE_IF_NEEDED(radialVelocity, numDetects);
        _RESIZE_IF_NEEDED(azimuth, numDetects);
        _RESIZE_IF_NEEDED(elevation, numDetects);
        _RESIZE_IF_NEEDED(rcs, numDetects);
        _RESIZE_IF_NEEDED(semanticId, numDetects);
        _RESIZE_IF_NEEDED(materialId, numDetects);
        _RESIZE_IF_NEEDED(objectId, numDetects);
#    undef _RESIZE_IF_NEEDED

#    if __DEBUG_PRINT_ON
        float min_el = 10000000;
        float max_el = -10000000;
        float min_az = 10000000;
        float max_az = -10000000;
        float min_dm = 10000000;
        float max_dm = -10000000;
#    endif
        for (uint32_t i = 0; i < numDetects; ++i)
        {
            const ProviderDetection& d = detections[i];

            if (needed_pointCloudData)
            {
#    if __DEBUG_PRINT_ON
                if (d.elev_ang_rad > max_el)
                    max_el = d.elev_ang_rad;
                if (d.elev_ang_rad < min_el)
                    min_el = d.elev_ang_rad;
                if (d.az_ang_rad > max_az)
                    max_az = d.az_ang_rad;
                if (d.az_ang_rad < min_az)
                    min_az = d.az_ang_rad;
                if (d.r_m > max_dm)
                    max_dm = d.r_m;
                if (d.r_m < min_dm)
                    min_dm = d.r_m;
#    endif
                convertDetectionToPoint(d, db_outputs_pointCloudData[i]);
            }
#    define _ASSIGN_IF_NEEDED(outputName, src)                                                                         \
        if (needed_##outputName)                                                                                       \
        db_outputs_##outputName[i] = d.src
            _ASSIGN_IF_NEEDED(radialDistance, r_m);
            _ASSIGN_IF_NEEDED(radialVelocity, rv_ms);
            _ASSIGN_IF_NEEDED(azimuth, az_ang_rad);
            _ASSIGN_IF_NEEDED(elevation, elev_ang_rad);
            _ASSIGN_IF_NEEDED(rcs, rcs_dbsm);
            _ASSIGN_IF_NEEDED(semanticId, semId);
            _ASSIGN_IF_NEEDED(materialId, matId);
            _ASSIGN_IF_NEEDED(objectId, objId);
#    undef _ASSIGN_IF_NEEDED
        }

        db.outputs.execOut() = kExecutionAttributeStateEnabled;

#    if __DEBUG_PRINT_ON
        std::cout << numDetects << " detects\n";
        std::cout << "rm = [" << min_dm << ", " << max_dm << "]\n";
        std::cout << "el = [" << min_el << ", " << max_el << "]\n";
        std::cout << "az = [" << min_az << ", " << max_az << "]\n";
#    endif

        return true;
    }

    virtual void reset()
    {
    }
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
// clang-format off
#endif
// clang-format on
