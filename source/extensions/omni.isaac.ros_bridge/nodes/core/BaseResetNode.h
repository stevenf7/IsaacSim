// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once


#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>

#include <omni/usd/UsdContextIncludes.h>
//
#include <omni/usd/UsdContext.h>

/**
 * @brief Base class for nodes that automatically reset when stop is pressed.
 *
 */
class BaseResetNode
{

public:
    /**
     * @brief Construct a new object
     *
     */
    BaseResetNode()
    {
        // When the node is created, we create a stage event subscription
        auto context = omni::usd::UsdContext::getContext();
        // The idea is that node is reset whenever stop/play are pressed
        mStageEventSub = carb::events::createSubscriptionToPop(
            context->getStageEventStream().get(),
            [this](carb::events::IEvent* e)
            {
                // TODO change this to eSimulatonStopPlay when that works
                if (static_cast<omni::usd::StageEventType>(e->type) == omni::usd::StageEventType::eAnimationStopPlay)
                {
                    reset();
                }
            },
            0, "IsaacSimOGNStageEventHandler");
    }
    /**
     * @brief Destroy the object, clear the stage event subscription
     *
     */
    ~BaseResetNode()
    {
        mStageEventSub = nullptr;
    }

    /**
     * @brief This reset function is pure virtual and must be defined by the derived class;
     *
     */
    virtual void reset() = 0;

private:
    carb::events::ISubscriptionPtr mStageEventSub;
};
