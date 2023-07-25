// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "gxf/core/entity.hpp"
#include "gxf/std/timestamp.hpp"

#include <plugins/Core/GxfNode.h>

#include <OgnGXFPublishTimestampDatabase.h>
using namespace omni::isaac::gxf_bridge;

class OgnGXFPublishTimestamp : public GxfNode
{
public:
    static bool compute(OgnGXFPublishTimestampDatabase& db)
    {
        auto& state = db.internalState<OgnGXFPublishTimestamp>();
        if (!state.getGxfContext())
        {
            if (state.setGxfContext(db.inputs.context()) != GXF_SUCCESS)
            {
                return false;
            }

            return true;
        }

        // Test for duplicate timestamps
        if (db.inputs.timeStamp() == state.timeStampPrev)
        {
            CARB_LOG_WARN("Encountered duplicate timestamp: %f. Skipping node execution.", state.timeStampPrev);
            return true;
        }
        state.timeStampPrev = db.inputs.timeStamp();

        // Immediately advance the context's SyntheticClock so downstream publishing nodes can access the correct time.
        state.mClock->advanceTo(db.inputs.timeStamp() * 1e9);

        // Then, publish the timestamp so any components which need it explicitly can use it
        nvidia::gxf::Expected<nvidia::gxf::Entity> maybe_entity = nvidia::gxf::Entity::New(state.getGxfContext());
        if (!maybe_entity)
        {
            CARB_LOG_ERROR("Could not create new entity.");
            return false;
        }
        nvidia::gxf::Entity& entity = maybe_entity.value();

        // Add timestamp to entity
        nvidia::gxf::Expected<nvidia::gxf::Handle<nvidia::gxf::Timestamp>> maybe_timestamp =
            entity.add<nvidia::gxf::Timestamp>("timestamp");
        if (!maybe_timestamp)
        {
            CARB_LOG_ERROR("Could not add timestamp to entity.");
            return false;
        }
        nvidia::gxf::Timestamp& timestamp = *maybe_timestamp.value();

        // Set timestamp acqtime to latest sim time, and pubtime to
        // sim system wall-clock at time of message generation.
        timestamp.acqtime = db.inputs.timeStamp() * 1e9;
        auto now = std::chrono::system_clock::now();
        timestamp.pubtime = std::chrono::time_point_cast<std::chrono::nanoseconds>(now).time_since_epoch().count();

        state.publish(db.inputs.outputEntity(), db.inputs.outputComponent(), std::move(entity));
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

private:
    double timeStampPrev = -1;
};

REGISTER_OGN_NODE()
