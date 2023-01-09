// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <plugins/Core/GxfNode.h>

#include <OgnGXFConfigureTCPServerDatabase.h>
using namespace omni::isaac::gxf_bridge;

class OgnGXFConfigureTCPServer : public GxfNode
{
public:
    static bool compute(OgnGXFConfigureTCPServerDatabase& db)
    {
        auto& state = db.internalState<OgnGXFConfigureTCPServer>();
        if (!state.getGxfContext())
        {
            if (state.setGxfContext(db.inputs.context()) != GXF_SUCCESS)
            {
                return false;
            }

            // Try to set TCP server parameters
            auto maybe_tcp_server_uid = state.getComponentCid(db.inputs.tcpEntity(), db.inputs.tcpComponent());
            if (!maybe_tcp_server_uid)
            {
                return false;
            }

            auto result = GxfParameterSetStr(
                state.getGxfContext(), maybe_tcp_server_uid.value(), "address", db.inputs.address().data());
            if (!result)
            {
                CARB_LOG_ERROR(GxfResultStr(result));
                return false;
            }
            result = GxfParameterSetUInt64(state.getGxfContext(), maybe_tcp_server_uid.value(), "port", db.inputs.port());
            if (!result)
            {
                CARB_LOG_ERROR(GxfResultStr(result));
                return false;
            }
        }

        return true;
    }
};

REGISTER_OGN_NODE()
