// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "gxf/std/tensor.hpp"

#include <gems/control_types/ackermann_drive.hpp>
#include <plugins/Core/GxfNode.h>

#include <OgnGXFSubscribeAckermannControlDatabase.h>
using namespace omni::isaac::gxf_bridge;

class OgnGXFSubscribeAckermannControl : public GxfNode
{
public:
    static bool compute(OgnGXFSubscribeAckermannControlDatabase& db)
    {
        auto& state = db.internalState<OgnGXFSubscribeAckermannControl>();
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
                db.logError("Composite schema server not set in Atlas.");
                return false;
            }
            schema_server->add(nvidia::isaac::AckermannControlCompositeSchema()).assign_to(state.schema_uid_);
            return true;
        }
        auto maybe_input_message = nvidia::gxf::Entity::New(state.getGxfContext());
        std::string entity = db.inputs.inputEntity();
        std::string component = db.inputs.inputComponent();
        if (state.receive(entity, component, maybe_input_message) == gxf_result_t::GXF_SUCCESS)
        {
            auto maybe_message_parts = nvidia::isaac::ParseCompositeMessage(std::move(maybe_input_message.value()));
            if (maybe_message_parts)
            {
                nvidia::isaac::AckermannControlConstView<double> command;
                command.pointer = maybe_message_parts.value().view.element_wise_begin();

                db.outputs.acceleration() = command.acceleration();
                db.outputs.curvature() = command.curvature();
                db.outputs.execOut() = kExecutionAttributeStateEnabled;
            }
        }
        return true;
    }

private:
    uint64_t schema_uid_;
};

REGISTER_OGN_NODE()
