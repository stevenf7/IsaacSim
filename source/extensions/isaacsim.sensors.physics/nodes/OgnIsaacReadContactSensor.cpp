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

#include <isaacsim/sensors/physics/IPhysicsSensor.h>
#include <omni/fabric/FabricUSD.h>

#include <OgnIsaacReadContactSensorDatabase.h>


namespace isaacsim
{
namespace sensors
{
namespace physics
{

class OgnIsaacReadContactSensor
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnIsaacReadContactSensorDatabase::sPerInstanceState<OgnIsaacReadContactSensor>(nodeObj, instanceId);

        state.m_contactSensorInterface = carb::getCachedInterface<ContactSensorInterface>();

        if (!state.m_contactSensorInterface)
        {
            CARB_LOG_ERROR("Failed to acquire isaacsim::sensors::physics interface");
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

        if (!prim.empty())
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

        CsReading sensorReading = state.m_contactSensorInterface->getSensorReading(primPath, db.inputs.useLatestData());

        if (sensorReading.isValid)
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
    ContactSensorInterface* m_contactSensorInterface = nullptr;
};


REGISTER_OGN_NODE()
} // sensor
} // graph
} // omni
