// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "MotionPolicySuppressionToken.h"

MotionPolicySuppressionToken::MotionPolicySuppressionToken()
{
}
void MotionPolicySuppressionToken::Add(const std::string& obstacleName, const double state)
{
    mActivations[obstacleName] = state;
    mTargetActivations[obstacleName] = state;
}
bool MotionPolicySuppressionToken::Remove(const std::string& obstacleName)
{
    if (mActivations.erase(obstacleName) && mTargetActivations.erase(obstacleName))
    {
        return true;
    }
    return false;
}
bool MotionPolicySuppressionToken::Disable(const std::string& obstacleName)
{
    if (mTargetActivations.find(obstacleName) == mTargetActivations.end())
    {
        return false;
    }
    mTargetActivations[obstacleName] = 0.0;
    return true;
}
bool MotionPolicySuppressionToken::Enable(const std::string& obstacleName)
{
    if (mTargetActivations.find(obstacleName) == mTargetActivations.end())
    {
        return false;
    }
    mTargetActivations[obstacleName] = 1.0;
    return true;
}
void MotionPolicySuppressionToken::Update(const double step)
{
    for (auto& activation : mActivations)
    {
        const double target = mTargetActivations[activation.first];
        if (activation.second < target)
        {
            activation.second += step;
        }
        else if (activation.second > target)
        {
            activation.second -= step;
        }

        if (activation.second < 0.0)
        {
            activation.second = 0.0;
        }

        if (activation.second > 1.0)
        {
            activation.second = 1.0;
        }
    }
}
double MotionPolicySuppressionToken::Activation(const std::string& obstacleName) const
{
    const auto& access = mActivations.find(obstacleName);
    if (access == mActivations.end())
    {
        return 0.0;
    }
    return access->second;
}
