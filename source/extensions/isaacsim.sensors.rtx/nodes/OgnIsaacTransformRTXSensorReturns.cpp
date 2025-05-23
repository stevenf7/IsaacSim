// SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "OgnIsaacTransformRTXSensorReturnsDatabase.h"
#include "isaacsim/core/includes/ScopedCudaDevice.h"

#include <carb/Defines.h>
#include <carb/InterfaceUtils.h>
#include <carb/logging/Log.h>

#include <usdrt/gf/quat.h>

#include <GenericModelOutput.h>
#include <GenericModelOutputTypes.h>

namespace isaacsim
{
namespace sensors
{
namespace rtx
{

/**
 * @class OgnIsaacTransformRTXSensorReturns
 * @brief Node that transforms sensor returns by interpolating between start and end frames.
 * @details
 * This node takes a GenericModelOutput buffer containing sensor data points and applies
 * orientation transforms to each element. The transformation is calculated by spherical
 * linear interpolation (SLERP) between the start and end frame orientations, with the
 * interpolation factor derived from each element's timestamp.
 */
class OgnIsaacTransformRTXSensorReturns
{
public:
    /**
     * @brief Compute method that performs the transformation of sensor returns.
     * @details
     * The method performs the following operations:
     * 1. Validates the input GenericModelOutput buffer
     * 2. Extracts quaternion orientations from start and end frames
     * 3. For each element, calculates an interpolation factor based on its timestamp
     * 4. Performs SLERP between the start and end orientations
     * 5. Applies the interpolated rotation to each point
     *
     * @param db The node database containing inputs and outputs
     * @return True if transformation was successful, false otherwise
     */
    static bool compute(OgnIsaacTransformRTXSensorReturnsDatabase& db)
    {
        // Disable downstream execution by default
        db.outputs.exec() = kExecutionAttributeStateDisabled;

        // Get input data and check if it's valid
        void* gmoBufferPointer = reinterpret_cast<void*>(db.inputs.gmoBufferPointer());
        if (!gmoBufferPointer)
        {
            // Expected if scan is being accumulated before being passed to this node.
            CARB_LOG_INFO("IsaacTransformRTXSensorReturns: gmoBufferPointer input is empty.");
            return false;
        }

        // Get the CUDA device index
        int32_t gmoDeviceIndex = db.inputs.gmoDeviceIndex();
        cudaDeviceProp cudaDeviceProperties;
        if (gmoDeviceIndex != -1 &&
            cudaGetDeviceProperties(&cudaDeviceProperties, gmoDeviceIndex) != cudaError::cudaSuccess)
        {
            CARB_LOG_ERROR("IsaacTransformRTXSensorReturns can't find CUDA device %d.", gmoDeviceIndex);
            return false;
        }

        // Get the GenericModelOutput from the buffer
        omni::sensors::GenericModelOutput* gmo = omni::sensors::getModelOutputPtrFromBuffer(gmoBufferPointer);
        if (gmo->numElements == 0)
        {
            CARB_LOG_WARN("IsaacTransformRTXSensorReturns: gmo->numElements is 0. Skipping execution.");
            return false;
        }

        // Verify that we have a supported modality (currently LIDAR or RADAR)
        if (gmo->modality != omni::sensors::Modality::LIDAR && gmo->modality != omni::sensors::Modality::RADAR)
        {
            CARB_LOG_WARN(
                "IsaacTransformRTXSensorReturns: Unsupported sensor modality: %d. Only LIDAR and RADAR are supported.",
                static_cast<int>(gmo->modality));
            return false;
        }

        // Verify output type is valid (must be POINTCLOUD)
        if (gmo->outputType != omni::sensors::OutputType::POINTCLOUD)
        {
            CARB_LOG_WARN("IsaacTransformRTXSensorReturns: Expected POINTCLOUD output type, got: %d",
                          static_cast<int>(gmo->outputType));
            return false;
        }

        // Get references to frame poses
        const omni::sensors::FrameAtTime& frameAtStart = gmo->frameStart;
        // CARB_LOG_WARN("IsaacTransformRTXSensorReturns: frameAtStart.orientation = %f %f %f %f",
        // frameAtStart.orientation[0], frameAtStart.orientation[1], frameAtStart.orientation[2],
        // frameAtStart.orientation[3]);
        const omni::sensors::FrameAtTime& frameAtEnd = gmo->frameEnd;
        // CARB_LOG_WARN("IsaacTransformRTXSensorReturns: frameAtEnd.orientation = %f %f %f %f",
        // frameAtEnd.orientation[0], frameAtEnd.orientation[1], frameAtEnd.orientation[2], frameAtEnd.orientation[3]);

        // Create a ScopedDevice object to handle CUDA device context
        isaacsim::core::includes::ScopedDevice scopedDevice(gmoDeviceIndex);

        // Get total number of elements to process
        const size_t numElements = gmo->numElements;

        // Create quaternion objects from frame orientations
        // Note: GfQuatf constructor takes (w, x, y, z) while orientation is stored as (x, y, z, w)
        usdrt::GfQuatf start(frameAtStart.orientation[3], // w
                             frameAtStart.orientation[0], // x
                             frameAtStart.orientation[1], // y
                             frameAtStart.orientation[2] // z
        );

        usdrt::GfQuatf end(frameAtEnd.orientation[3], // w
                           frameAtEnd.orientation[0], // x
                           frameAtEnd.orientation[1], // y
                           frameAtEnd.orientation[2] // z
        );

        // Process all elements - transform their positions
        // CARB_LOG_WARN("IsaacTransformRTXSensorReturns: processing %lu elements", numElements);
        // CARB_LOG_WARN("IsaacTransformRTXSensorReturns: gmo->timestampNs = %lu, frameAtStart.timestampNs = %lu,
        // frameAtEnd.timestampNs = %lu", gmo->timestampNs, frameAtStart.timestampNs, frameAtEnd.timestampNs); int32_t*
        // max_element_ptr = std::max_element(gmo->elements.timeOffsetNs, gmo->elements.timeOffsetNs +
        // numElements*sizeof(int32_t)); int32_t* min_element_ptr = std::min_element(gmo->elements.timeOffsetNs,
        // gmo->elements.timeOffsetNs + numElements*sizeof(int32_t)); CARB_LOG_WARN("IsaacTransformRTXSensorReturns:
        // gmo->elements.timeOffsetNs min, max = %d, %d", *min_element_ptr, *max_element_ptr);
        for (size_t i = 0; i < numElements; i++)
        {
            // test validity

            if ((gmo->elements.flags[i] & omni::sensors::ElementFlags::VALID) != omni::sensors::ElementFlags::VALID)
            {
                continue;
            }
            // Calculate interpolation factor (t) based on element's timeOffset
            // t = 0.0 corresponds to frameAtStart, t = 1.0 corresponds to frameAtEnd
            float timeRange = static_cast<float>(frameAtEnd.timestampNs - frameAtStart.timestampNs);
            float t = static_cast<float>(gmo->timestampNs + gmo->elements.timeOffsetNs[i] - frameAtStart.timestampNs) /
                      timeRange;

            // Clamp t to [0, 1] to handle elements with timestamps outside the frame range
            t = std::max(0.0f, std::min(1.0f, t));

            // Perform spherical linear interpolation (SLERP) between start and end quaternions
            usdrt::GfQuatf result = omni::math::linalg::GfSlerp(start, end, t);

            if (gmo->elementsCoordsType == omni::sensors::CoordsType::CARTESIAN)
            {
                // CARB_LOG_WARN("IsaacTransformRTXSensorReturns: Cartesian - x/y/z: %f/%f/%f", gmo->elements.x[i],
                // gmo->elements.y[i], gmo->elements.z[i]); Create point as vec3f for transformation
                omni::math::linalg::vec3f originalPoint(gmo->elements.x[i], gmo->elements.y[i], gmo->elements.z[i]);
                if (originalPoint.GetLength() < 1e-6)
                {
                    // skip zero elements
                    continue;
                }

                // Apply rotation transform using quaternion's Transform method
                omni::math::linalg::vec3f transformedPoint = result.Transform(originalPoint);

                // Store transformed point coordinates back to the buffer
                gmo->elements.x[i] = transformedPoint[0];
                gmo->elements.y[i] = transformedPoint[1];
                gmo->elements.z[i] = transformedPoint[2];
            }
            else
            {
                // Transform spherical coordinates to Cartesian, converting from degrees to radians
                const float az = static_cast<float>(M_PI) / 180.0f * gmo->elements.x[i];
                const float el = static_cast<float>(M_PI) / 180.0f * gmo->elements.y[i];
                const float r = gmo->elements.z[i];
                if (r < 1e-6)
                {
                    // skip zero elements
                    continue;
                }

                // Convert to Cartesian coordinates
                const float x = std::cos(az) * std::cos(el);
                const float y = std::sin(az) * std::cos(el);
                const float z = std::sin(el);

                // Create point as vec3f for transformation
                const omni::math::linalg::vec3f originalPoint(x, y, z);

                // Apply rotation transform using quaternion's Transform method
                const omni::math::linalg::vec3f transformedPoint = result.Transform(originalPoint);

                // Convert back to spherical coordinates
                const float transformedAz = std::atan2(transformedPoint[1], transformedPoint[0]);
                const float transformedEl = std::asin(transformedPoint[2]);
                // if (i % 100000 == 0) {
                //     CARB_LOG_WARN("IsaacTransformRTXSensorReturns, gmo time %lu, start time %lu, end time %lu,
                //     timeOffsetNs %d, t = %f", gmo->timestampNs, frameAtStart.timestampNs, frameAtEnd.timestampNs,
                //     gmo->elements.timeOffsetNs[i], t); CARB_LOG_WARN("IsaacTransformRTXSensorReturns, Spherical -
                //     az/el - %f/%f transformed az/el/r: %f/%f", az, el, transformedAz, transformedEl);
                // }

                // Store transformed point coordinates back to the buffer, converting from radians to degrees
                gmo->elements.x[i] = transformedAz * 180.0f / static_cast<float>(M_PI);
                gmo->elements.y[i] = transformedEl * 180.0f / static_cast<float>(M_PI);
            }
        }

        // Set outputs (data pointer and device index remain the same)
        db.outputs.gmoBufferPointer() = db.inputs.gmoBufferPointer();
        db.outputs.gmoDeviceIndex() = gmoDeviceIndex;

        // Return success and enable downstream execution
        db.outputs.exec() = kExecutionAttributeStateEnabled;
        return true;
    }
};

REGISTER_OGN_NODE()

} // namespace rtx
} // namespace sensors
} // namespace isaacsim
