// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "gxf/std/tensor.hpp"

#include <extensions/messages/imu_message.hpp>
#include <omni/isaac/gxf_bridge/GxfNode.h>

#include <OgnGXFPublishIMUDatabase.h>
using namespace omni::isaac::gxf_bridge;

class OgnGXFPublishIMU : public GxfNode
{
public:
    static bool compute(OgnGXFPublishIMUDatabase& db)
    {
        auto& state = db.internalState<OgnGXFPublishIMU>();
        if (!state.getGxfContext())
        {
            if (state.setGxfContext(db.inputs.context()) != GXF_SUCCESS)
            {
                return false;
            }

            // nvidia::gxf::Handle<nvidia::isaac::CompositeSchemaServer> schema_server =
            //     state.mAtlas->composite_schema_server();

            // if (!schema_server)
            // {
            //     CARB_LOG_ERROR("Composite schema server not set in ATLAS.");
            //     return false;
            // }
            // schema_server->add(nvidia::isaac::DifferentialBaseStateCompositeSchema()).assign_to(state.schema_uid_);
            return true;
        }

        nvidia::isaac::CreateImuMessage(state.getGxfContext())
            .map(
                [&](nvidia::isaac::ImuMessageParts message)
                {
                    message.timestamp->pubtime = static_cast<int64_t>(db.inputs.timeStamp() * 1e9);
                    message.timestamp->acqtime = static_cast<int64_t>(db.inputs.timeStamp() * 1e9);
                    message.pose_frame_uid->uid =
                        state.mAtlas->pose_tree().findFrame(db.inputs.poseFrame().data()).value();

                    message.imu->linear_acceleration_x = db.inputs.linearAcceleration()[0];
                    message.imu->linear_acceleration_y = db.inputs.linearAcceleration()[1];
                    message.imu->linear_acceleration_z = db.inputs.linearAcceleration()[2];

                    message.imu->angular_velocity_x = db.inputs.angularVelocity()[0];
                    message.imu->angular_velocity_y = db.inputs.angularVelocity()[1];
                    message.imu->angular_velocity_z = db.inputs.angularVelocity()[2];
                    state.publish(db.inputs.outputEntity(), db.inputs.outputComponent(), std::move(message.message));
                });

        return true;
    }

private:
    uint64_t schema_uid_;
};

REGISTER_OGN_NODE()
