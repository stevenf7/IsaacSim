// SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "isaacsim/core/includes/UsdUtilities.h"

#include <omni/fabric/FabricUSD.h>
#include <pxr/base/gf/quatd.h>
#include <pxr/base/gf/vec3d.h>

#include <IPhysicsSensor.h>
#include <OgnIsaacReadIMUDatabase.h>


namespace isaacsim
{
namespace sensors
{
namespace physics
{

class OgnIsaacReadIMU
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnIsaacReadIMUDatabase::sPerInstanceState<OgnIsaacReadIMU>(nodeObj, instanceId);

        state.m_imuSensorInterface = carb::getCachedInterface<ImuSensorInterface>();

        if (!state.m_imuSensorInterface)
        {
            CARB_LOG_ERROR("Failed to acquire isaacsim::sensors::physics interface");
            return;
        }
    }

    static bool compute(OgnIsaacReadIMUDatabase& db)
    {
        auto& state = db.perInstanceState<OgnIsaacReadIMU>();

        const auto& prim = db.inputs.imuPrim();
        const char* primPath;

        auto& linAcc = db.outputs.linAcc();
        auto& angVel = db.outputs.angVel();
        auto& orientation = db.outputs.orientation();
        auto& sensorTime = db.outputs.sensorTime();

        if (!prim.empty())
        {
            primPath = omni::fabric::toSdfPath(prim[0]).GetText();
        }
        else
        {
            linAcc = GfVec3d(0.0, 0.0, 0.0);
            angVel = GfVec3d(0.0, 0.0, 0.0);
            orientation = GfQuatd(1.0, 0.0, 0.0, 0.0);
            sensorTime = 0.0f;
            db.logError("Invalid Imu sensor prim");
            return false;
        }

        IsReading sensorReading = state.m_imuSensorInterface->getSensorReading(
            primPath, nullptr, db.inputs.useLatestData(), db.inputs.readGravity());

        if (sensorReading.isValid)
        {
            linAcc = GfVec3d(sensorReading.linAccX, sensorReading.linAccY, sensorReading.linAccZ);
            angVel = GfVec3d(sensorReading.angVelX, sensorReading.angVelY, sensorReading.angVelZ);
            orientation = GfQuatd(sensorReading.orientation.w, sensorReading.orientation.x, sensorReading.orientation.y,
                                  sensorReading.orientation.z);
            sensorTime = sensorReading.time;
        }
        else
        {
            linAcc = GfVec3d(0.0, 0.0, 0.0);
            angVel = GfVec3d(0.0, 0.0, 0.0);
            orientation = GfQuatd(1.0, 0.0, 0.0, 0.0);
            sensorTime = 0.0f;
            db.logWarning("no valid sensor reading, is the sensor enabled?");
            db.outputs.execOut() = kExecutionAttributeStateDisabled;
            return false;
        }
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

private:
    ImuSensorInterface* m_imuSensorInterface = nullptr;
};


REGISTER_OGN_NODE()
} // sensor
} // graph
} // omni
