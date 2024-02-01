// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
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

#include <omni/fabric/FabricUSD.h>
#include <pxr/base/gf/quatd.h>
#include <pxr/base/gf/vec3d.h>

#include <IsaacSensor.h>
#include <OgnIsaacReadIMUDatabase.h>


namespace omni
{
namespace isaac
{
namespace sensor
{

class OgnIsaacReadIMU
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnIsaacReadIMUDatabase::sInternalState<OgnIsaacReadIMU>(nodeObj);

        state.mImuSensorInterface = carb::getCachedInterface<ImuSensorInterface>();

        if (!state.mImuSensorInterface)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::sensor interface");
            return;
        }
    }

    static bool compute(OgnIsaacReadIMUDatabase& db)
    {
        auto& state = db.internalState<OgnIsaacReadIMU>();

        const auto& prim = db.inputs.imuPrim();
        const char* primPath;

        auto& linAcc = db.outputs.linAcc();
        auto& angVel = db.outputs.angVel();
        auto& orientation = db.outputs.orientation();
        auto& sensorTime = db.outputs.sensorTime();

        if (prim.size() > 0)
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

        IsReading sensorReading = state.mImuSensorInterface->getSensorReading(
            primPath, nullptr, db.inputs.useLatestData(), db.inputs.readGravity());

        if (sensorReading.is_valid)
        {
            linAcc = GfVec3d(sensorReading.lin_acc_x, sensorReading.lin_acc_y, sensorReading.lin_acc_z);
            angVel = GfVec3d(sensorReading.ang_vel_x, sensorReading.ang_vel_y, sensorReading.ang_vel_z);
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
            return false;
        }
        return true;
    }

private:
    ImuSensorInterface* mImuSensorInterface = nullptr;
};


REGISTER_OGN_NODE()
} // sensor
} // graph
} // omni
