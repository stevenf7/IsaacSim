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
        const GraphContextObj& context = db.abi_context();

        auto& state = db.perInstanceState<OgnDifferentialController>();

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
            else if (db.inputs.maxLinearSpeed() == 0)
            {
                state.mMaxLinearSpeed = 10000000;
            }

            if (std::fabs(db.inputs.maxAngularSpeed()) > 0)
            {
                state.mMaxAngularSpeed = std::fabs(db.inputs.maxAngularSpeed());
            }
            else if (db.inputs.maxAngularSpeed() == 0)
            {
                state.mMaxAngularSpeed = 10000000;
            }

            if (std::fabs(db.inputs.maxWheelSpeed()) > 0)
            {
                state.mMaxWheelSpeed = std::fabs(db.inputs.maxWheelSpeed());
            }
            else if (db.inputs.maxWheelSpeed() == 0)
            {
                state.mMaxWheelSpeed = 10000000;
            }
            state.mInitialized = true;
        }

        double linearVelocity =
            std::max(-state.mMaxLinearSpeed, std::min(state.mMaxLinearSpeed, db.inputs.linearVelocity()));
        double angularVelocity =
            std::max(-state.mMaxAngularSpeed, std::min(state.mMaxAngularSpeed, db.inputs.angularVelocity()));

        // calculate wheel speed
        auto& jointVelocities = db.outputs.velocityCommand();
        jointVelocities[0] = ((2 * linearVelocity) - (angularVelocity * state.mWheelDistance)) / (2 * state.mWheelRadius);
        jointVelocities[1] = ((2 * linearVelocity) + (angularVelocity * state.mWheelDistance)) / (2 * state.mWheelRadius);

        jointVelocities[0] = std::max(-state.mMaxWheelSpeed, std::min(state.mMaxWheelSpeed, jointVelocities[0]));
        jointVelocities[1] = std::max(-state.mMaxWheelSpeed, std::min(state.mMaxWheelSpeed, jointVelocities[1]));

        return true;
    }


    virtual void reset()
    {
        mInitialized = false;
    }


private:
    bool mInitialized = false;
    double mMaxAngularSpeed = 0;
    double mMaxWheelSpeed = 0;
    double mMaxLinearSpeed = 0;
    double mWheelDistance = 0;
    double mWheelRadius = 0;
};

REGISTER_OGN_NODE()
}
}
}
