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

#include <OgnREBPublishDifferentialStateDatabase.h>
using namespace omni::isaac::robot_engine_bridge;

class OgnREBPublishDifferentialState : public RebNode
{
public:
    static bool compute(OgnREBPublishDifferentialStateDatabase& db)
    {
        auto& state = db.internalState<OgnREBPublishDifferentialState>();
        if (!state.initializeHandles())
        {
            return false;
        }
        state.updateTimestamp(db.inputs.timeStamp(), db.inputs.timeOffset());

        IsaacMessage<isaac_message::State> stateMessage;
        auto stateMessageProto = stateMessage.initProto();
        stateMessageProto.setSchema("");

        auto tensorProto = stateMessageProto.initPack();
        tensorProto.setElementType(ElementType::FLOAT64);
        tensorProto.initSizes(3);
        tensorProto.setSizes({ 1, 1, 4 });
        tensorProto.setScanlineStride(0);
        tensorProto.setDataBufferIndex(0);

        const GraphContextObj& context = db.abi_context();
        long stageId = context.iContext->getStageId(context);
        auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

        pxr::GfVec2d measuredSpeed = pxr::GfVec2d(
            pxr::GfDot(db.inputs.linearVelocity(), db.inputs.robotFront()) * UsdGeomGetStageMetersPerUnit(stage),
            db.inputs.angularVelocity()[2]);
        pxr::GfVec2d measuredAcceleration = (measuredSpeed - state.mLastSpeed) / state.mTimeDelta;
        state.mLastAcceleration +=
            state.timedSmoothingFactor(state.mTimeDelta, 1.0) * (measuredAcceleration - state.mLastAcceleration);

        std::vector<double> real_data = {
            state.mLastSpeed[0],
            state.mLastSpeed[1],
            state.mLastAcceleration[0],
            state.mLastAcceleration[1],
        };

        std::vector<std::unique_ptr<IsaacBuffer>> buffers(1);
        buffers[0] = std::make_unique<IsaacHostBuffer>(real_data.size() * sizeof(double));
        std::memcpy(buffers[0]->data(), real_data.data(), real_data.size() * sizeof(double));
        state.publish(db.inputs.outputComponent(), db.inputs.outputChannel(), stateMessage, buffers);
        state.mLastSpeed = measuredSpeed;

        return true;
    }

private:
    float timedSmoothingFactor(float dt, float lambda)
    {
        if (lambda <= dt * 0.01f)
        {
            return 0.0;
        }
        else
        {
            return 1.0f - std::exp(-dt / lambda);
        }
    }


    pxr::GfVec2d mLastSpeed;
    pxr::GfVec2d mLastAcceleration;
};

REGISTER_OGN_NODE()
