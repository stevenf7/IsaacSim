// Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "gxf/std/tensor.hpp"

#include <extensions/messages/accelerometer_message.hpp>
#include <plugins/Core/GxfNode.h>

#include <OgnGXFPublishAccelerometerDatabase.h>
using namespace omni::isaac::gxf_bridge;

class OgnGXFPublishAccelerometer : public GxfNode
{
public:
    static bool compute(OgnGXFPublishAccelerometerDatabase& db)
    {
        auto& state = db.internalState<OgnGXFPublishAccelerometer>();
        if (!state.getGxfContext())
        {
            if (state.setGxfContext(db.inputs.context()) != GXF_SUCCESS)
            {
                return false;
            }
            return true;
        }
        nvidia::gxf::Expected<nvidia::isaac::AccelerometerMessageParts> maybe_message =
            nvidia::isaac::CreateAccelerometerMessage(state.getGxfContext());
        if (!maybe_message)
        {
            db.logError("Cannot create Accelerometer message");
            return false;
        }
        nvidia::isaac::AccelerometerMessageParts message = maybe_message.value();
        message.timestamp->pubtime = state.mClock->timestamp();
        message.timestamp->acqtime = message.timestamp->pubtime;
        const std::string frame_name = db.inputs.poseFrame();
        auto maybe_frame = state.mAtlas->pose_tree().findFrame(frame_name.c_str());
        if (!maybe_frame)
        {
            db.logError("Cannot find frame %s", frame_name.c_str());
            return false;
        }
        message.pose_frame_uid->uid = maybe_frame.value();

        message.accelerometer->linear_acceleration_x = db.inputs.linearAcceleration()[0];
        message.accelerometer->linear_acceleration_y = db.inputs.linearAcceleration()[1];
        message.accelerometer->linear_acceleration_z = db.inputs.linearAcceleration()[2];

        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return state.publish(db.inputs.outputEntity(), db.inputs.outputComponent(), message.message);
    }

private:
    uint64_t schema_uid_;
};

REGISTER_OGN_NODE()
