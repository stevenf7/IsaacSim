// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
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

#include "omni/isaac/utils/UsdUtilities.h"

#include <omni/fabric/FabricUSD.h>

#include <IsaacSensor.h>
#include <OgnIsaacReadContactSensorDatabase.h>


namespace omni
{
namespace isaac
{
namespace sensor
{

class OgnIsaacReadContactSensor
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnIsaacReadContactSensorDatabase::sPerInstanceState<OgnIsaacReadContactSensor>(nodeObj, instanceId);

        state.mContactSensorInterface = carb::getCachedInterface<ContactSensorInterface>();

        if (!state.mContactSensorInterface)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::sensor interface");
            return;
        }
    }

    static bool compute(OgnIsaacReadContactSensorDatabase& db)
    {
        auto& state = db.perInstanceState<OgnIsaacReadContactSensor>();

        const auto& prim = db.inputs.csPrim();
        const char* primPath;

        auto& inContact = db.outputs.inContact();
        auto& value = db.outputs.value();
        auto& sensorTime = db.outputs.sensorTime();

        if (prim.size() > 0)
        {
            primPath = omni::fabric::toSdfPath(prim[0]).GetText();
        }
        else
        {
            inContact = false;
            value = 0;
            sensorTime = 0.0f;
            db.logError("Invalid contact sensor prim");
            return false;
        }

        CsReading sensorReading = state.mContactSensorInterface->getSensorReading(primPath, db.inputs.useLatestData());

        if (sensorReading.is_valid)
        {
            inContact = sensorReading.inContact;
            value = sensorReading.value;
            sensorTime = sensorReading.time;
        }
        else
        {
            inContact = false;
            value = 0;
            sensorTime = 0.0f;
            db.logWarning("no valid sensor reading, is the sensor enabled?");
            db.outputs.execOut() = kExecutionAttributeStateDisabled;
            return false;
        }
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

private:
    ContactSensorInterface* mContactSensorInterface = nullptr;
};


REGISTER_OGN_NODE()
} // sensor
} // graph
} // omni
