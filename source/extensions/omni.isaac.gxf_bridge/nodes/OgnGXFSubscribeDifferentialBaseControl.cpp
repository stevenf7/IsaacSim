// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "gxf/std/tensor.hpp"

#include <gems/control_types/differential_drive.hpp>
#include <omni/isaac/gxf_bridge/GxfNode.h>

#include <OgnGXFSubscribeDifferentialBaseControlDatabase.h>
using namespace omni::isaac::gxf_bridge;

class OgnGXFSubscribeDifferentialBaseControl : public GxfNode
{
public:
    static bool compute(OgnGXFSubscribeDifferentialBaseControlDatabase& db)
    {
        auto& state = db.internalState<OgnGXFSubscribeDifferentialBaseControl>();
        if (!state.getGxfContext())
        {
            if (state.setGxfContext(db.inputs.context()) != GXF_SUCCESS)
            {
                return false;
            }

            nvidia::gxf::Handle<nvidia::isaac::CompositeSchemaServer> schema_server =
                state.mAtlas->composite_schema_server();

            if (!schema_server)
            {
                CARB_LOG_ERROR("Composite schema server not set in ATLAS.");
                return false;
            }
            schema_server->add(nvidia::isaac::DifferentialBaseCommandCompositeSchema()).assign_to(state.schema_uid_);
            return true;
        }
        auto maybe_input_message = nvidia::gxf::Entity::New(state.getGxfContext());
        std::string entity = db.inputs.inputEntity();
        std::string component = db.inputs.inputComponent();
        if (state.receive(entity, component, maybe_input_message) == gxf_result_t::GXF_SUCCESS)
        {
            // CARB_LOG_ERROR("receive");
            auto maybe_message_parts = nvidia::isaac::ParseCompositeMessage(std::move(maybe_input_message.value()));
            if (maybe_message_parts)
            {
                nvidia::isaac::DifferentialBaseCommandConstView<double> command;
                command.pointer = maybe_message_parts.value().view.element_wise_begin();

                db.outputs.angularVelocity() = command.angular_speed();
                db.outputs.linearVelocity() = command.linear_speed();
                db.outputs.execOut() = kExecutionAttributeStateEnabled;
                // CARB_LOG_ERROR("Linear speed, angular speed: %f, %f", command.linear_speed(),
                // command.angular_speed());
            }

            // maybe_input_message
            //     .map(
            //         [state](nvidia::gxf::Entity message)
            //         {
            //             // CARB_LOG_ERROR("MESSAGE RECEIVED");
            //             return nvidia::isaac::ExtractComposite<nvidia::isaac::DifferentialBaseCommand<double>>(
            //                 std::move(message), state.mAtlas->composite_schema_server(),
            //                 nvidia::isaac::DifferentialBaseCommandCompositeSchema());
            //         })
            //     .map(
            //         [&db](nvidia::isaac::DifferentialBaseCommand<double> dbc)
            //         {
            //             db.outputs.angularVelocity() = dbc.angular_speed();
            //             db.outputs.linearVelocity() = dbc.linear_speed();
            //             db.outputs.execOut() = kExecutionAttributeStateEnabled;
            //             // CARB_LOG_ERROR("Linear speed, angular speed: %f, %f", dbc.linear_speed(),
            //             // dbc.angular_speed());
            //         });
        }
        return true;
    }

private:
    uint64_t schema_uid_;
};

REGISTER_OGN_NODE()
