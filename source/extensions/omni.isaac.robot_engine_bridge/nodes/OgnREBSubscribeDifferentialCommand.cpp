// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// #include "ros/ros.h"

#include <omni/isaac/robot_engine_bridge/RebNode.h>

#include <OgnREBSubscribeDifferentialCommandDatabase.h>
using namespace omni::isaac::robot_engine_bridge;

class OgnREBSubscribeDifferentialCommand : public RebNode
{
public:
    static bool compute(OgnREBSubscribeDifferentialCommandDatabase& db)
    {
        auto& state = db.internalState<OgnREBSubscribeDifferentialCommand>();
        if (!state.initializeHandles())
        {
            return false;
        }

        std::vector<IsaacHostBuffer> buffers;
        IsaacMessage<isaac_message::State> commandComposite;
        MessageHeader header;
        if (checkErrorCode(
                state.receive(db.inputs.inputComponent(), db.inputs.inputChannel(), header, commandComposite, buffers)))
        {
            // State need buffer for data
            if (buffers.size() == 0)
            {
                return false;
            }
            std::vector<double> elements(buffers[0].size() / sizeof(double));
            std::memcpy(elements.data(), buffers[0].data(), elements.size() * sizeof(double));
            if (elements.size() != 2)
            {
                CARB_LOG_ERROR("Wrong number of elements: %zu", elements.size());
                return false;
            }


            db.outputs.linearVelocity() = elements[0];
            db.outputs.angularVelocity() = elements[1];
            db.outputs.execOut() = kExecutionAttributeStateEnabled;
        }

        return true;
    }

private:
};

REGISTER_OGN_NODE()
