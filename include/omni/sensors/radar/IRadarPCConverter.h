// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
//
// This code contains NVIDIA Confidential Information and is disclosed
// under the Mutual Non-Disclosure Agreement.
//
// Notice
// ALL NVIDIA DESIGN SPECIFICATIONS AND CODE ("MATERIALS") ARE PROVIDED "AS IS" NVIDIA MAKES
// NO REPRESENTATIONS, WARRANTIES, EXPRESSED, IMPLIED, STATUTORY, OR OTHERWISE WITH RESPECT TO
// THE MATERIALS, AND EXPRESSLY DISCLAIMS ANY IMPLIED WARRANTIES OF NONINFRINGEMENT,
// MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
//
// NVIDIA Corporation assumes no responsibility for the consequences of use of such
// information or for any infringement of patents or other rights of third parties that may
// result from its use. No license is granted by implication or otherwise under any patent
// or patent rights of NVIDIA Corporation. No third party distribution is allowed unless
// expressly authorized by NVIDIA.  Details are subject to change without notice.
// This code supersedes and replaces all information previously supplied.
// NVIDIA Corporation products are not authorized for use as critical
// components in life support devices or systems without express written approval of
// NVIDIA Corporation.
//

#pragma once

#include <carb/Interface.h>

#include <cstdint>

namespace omni
{
namespace sensors
{
namespace radar
{

static constexpr uint16_t MAX_DETS_PER_SCAN = 2500;

#pragma pack(push, 1)

/**
  \brief Defines the structure for a raw radar detection
 */
struct RadarDetection
{
    float r_m; /**< Radial distance (m) */
    float rv_ms; /**< Radial velocity (m/s) */
    float az_ang_rad; /**< Azimuth angle (radians) */
    float elev_ang_rad; /**< Angle of elevation (radians) */
    float rcs_dbsm; /**< radar cross section*/
    uint32_t semId;
    uint32_t matId;
    uint32_t objId;
};

/**
  \brief Represents a full radar stream for a major cycle
 */
struct RadarPointCloud
{
    void* syncData; /**< contains Sync primitives for syncing with model */
    void* taskingCounter; /**< a tasking counter for async cpu work */
    uint8_t sensorID; /**< Sensor Id for sensor that generated the scan */
    uint8_t scanIdx; /**< Scan index for sensors with multi scan support */
    uint64_t timeStampNS; /**< Scan timestamp in nanoseconds */
    uint64_t cycleCnt; /**< Scan cycle count (unique per scan idx) */
    float maxRangeM; /**< The max unambiguous range for the scan */
    float minVelMps; /**< The min unambiguous velocity for the scan */
    float maxVelMps; /**< The max unambiguous velocity for the scan */
    float minAzRad; /**< The min unambiguous azimuth for the scan */
    float maxAzRad; /**< The max unambiguous azimuth for the scan */
    float minElRad; /**< The min unambiguous elevation for the scan */
    float maxElRad; /**< The max unambiguous elevation for the scan */
    uint16_t numDetections; /**< The number of valid detections in the array */
    RadarDetection detections[MAX_DETS_PER_SCAN]; /**< Array of valid detections */
};

/**
  \brief Represents debug data the optionally trails the pointcloud
 */
struct DebugData
{
    uint16_t numRBins;
    uint16_t numVBins;
    uint32_t cfarSize;
    float* cfar;
};

#pragma pack(pop)

/**
 * @brief an interface for radar point cloud converter
 *
 */
class IRadarPCConverter
{
public:
    CARB_PLUGIN_INTERFACE("omni::sensors::radar::IRadarPCConverter", 0, 1)

    /**
     * @brief converts radar output raw buffer (raw AOV) to a point cloud
     *
     * @param buffer raw radar output buffer (AOV)
     * @return RadarPointCloudPtr radar point cloud object pointer
     */
    RadarPointCloud*(CARB_ABI* convertBuffer)(void* buffer);

    /**
     * @brief gets debug data struct from a radar raw buffer
     *
     * @param buffer raw radar output buffer (AOV)
     * @return RadarPointCloudPtr radar point cloud object pointer
     */
    DebugData*(CARB_ABI* getDebugData)(void* buffer);
};

} // namespace radar
} // namespace sensors
} // namespace omni
