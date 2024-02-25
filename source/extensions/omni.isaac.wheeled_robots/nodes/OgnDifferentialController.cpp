// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include <omni/isaac/utils/BaseResetNode.h>

#include <OgnDifferentialControllerDatabase.h>
#include <cmath>

namespace omni
{
namespace isaac
{
namespace wheeled_robot
{

class OgnDifferentialController : public BaseResetNode
{

public:
    static bool compute(OgnDifferentialControllerDatabase& db)
    {
        auto& state = db.perInstanceState<OgnDifferentialController>();
        state.nodeObj = db.abi_node();

        if (!state.mInitialized)
        {
            if (db.inputs.wheelRadius() <= 0 || db.inputs.wheelDistance() <= 0)
            {
                db.logWarning("invalid wheel radius and distance");
                return false;
            }
            else
            {
                state.mWheelRadius = db.inputs.wheelRadius();
                state.mWheelDistance = db.inputs.wheelDistance();
            }


            if (std::fabs(db.inputs.maxLinearSpeed()) > 0)
            {
                state.mMaxLinearSpeed = std::fabs(db.inputs.maxLinearSpeed());
            }

            if (std::fabs(db.inputs.maxAngularSpeed()) > 0)
            {
                state.mMaxAngularSpeed = std::fabs(db.inputs.maxAngularSpeed());
            }

            if (std::fabs(db.inputs.maxWheelSpeed()) > 0)
            {
                state.mMaxWheelSpeed = std::fabs(db.inputs.maxWheelSpeed());
            }

            state.mInitialized = true;
        }

        double linearVelocity =
            std::max(-state.mMaxLinearSpeed, std::min(state.mMaxLinearSpeed, db.inputs.linearVelocity()));
        double angularVelocity =
            std::max(-state.mMaxAngularSpeed, std::min(state.mMaxAngularSpeed, db.inputs.angularVelocity()));

        // calculate wheel speed
        auto& jointVelocities = db.outputs.velocityCommand();
        jointVelocities.resize(2);
        jointVelocities[0] = ((2 * linearVelocity) - (angularVelocity * state.mWheelDistance)) / (2 * state.mWheelRadius);
        jointVelocities[1] = ((2 * linearVelocity) + (angularVelocity * state.mWheelDistance)) / (2 * state.mWheelRadius);

        jointVelocities[0] = std::max(-state.mMaxWheelSpeed, std::min(state.mMaxWheelSpeed, jointVelocities[0]));
        jointVelocities[1] = std::max(-state.mMaxWheelSpeed, std::min(state.mMaxWheelSpeed, jointVelocities[1]));

        return true;
    }

    virtual void reset()
    {
        GraphObj graphObj{ nodeObj.iNode->getGraph(nodeObj) };
        GraphContextObj context{ graphObj.iGraph->getDefaultGraphContext(graphObj) };

        // set the node's input and output
        AttributeObj linearAttr = nodeObj.iNode->getAttribute(nodeObj, "inputs:linearVelocity");
        auto linearHandle = linearAttr.iAttribute->getAttributeDataHandle(linearAttr, kAccordingToContextIndex);
        double* linearVelocity = getDataW<double>(context, linearHandle);
        *linearVelocity = 0;

        // set the node's input and output
        AttributeObj angularAttr = nodeObj.iNode->getAttribute(nodeObj, "inputs:angularVelocity");
        auto angularHandle = angularAttr.iAttribute->getAttributeDataHandle(angularAttr, kAccordingToContextIndex);
        double* angularVelocity = getDataW<double>(context, angularHandle);
        *angularVelocity = 0;

        // set the node's input and output
        // TODO: Disabled because this causes a crash on reset when next compute is called
        // AttributeObj velocityAttr = nodeObj.iNode->getAttribute(nodeObj, "outputs:velocityCommand");
        // auto velocityHandle = velocityAttr.iAttribute->getAttributeDataHandle(velocityAttr,
        // kAccordingToContextIndex); double* velocityCommand = getDataW<double>(context, velocityHandle);
        // velocityCommand[0] = 0.0;
        // velocityCommand[1] = 0.0;
    }

private:
    bool mInitialized = false;
    double mMaxAngularSpeed = 1.0e7;
    double mMaxWheelSpeed = 1.0e7;
    double mMaxLinearSpeed = 1.0e7;
    double mWheelDistance = 0;
    double mWheelRadius = 0;
    NodeObj nodeObj;
};

REGISTER_OGN_NODE()
}
}
}
