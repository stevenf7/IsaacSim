// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../contact_sensor/ContactManager.h"
#include "../contact_sensor/ContactSensor.h"
#include "../imu_sensor/ImuSensor.h"
#include "BaseSensorComponent.h"
#include "omni/isaac/bridge/BridgeApplication.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/events/EventsUtils.h>
#include <carb/logging/Log.h>

#include <isaacSensorSchema/isaacContactSensor.h>
#include <omni/isaac/isaac_sensor/IsaacSensorTypes.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/usd/UsdContext.h>
#include <physicsSchemaTools/UsdTools.h>
#include <physxSchema/physxContactReportAPI.h>
#include <usdPhysics/scene.h>

#include <PxActor.h>
#include <PxArticulationLink.h>
#include <PxRigidDynamic.h>
#include <PxScene.h>
#include <map>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace omni
{
namespace isaac
{
namespace isaac_sensor
{

class IsaacSensorManager : public utils::BridgeApplicationBase<IsaacBaseSensorComponent>
{
public:
    IsaacSensorManager(omni::physx::IPhysx* physXInterface, omni::renderer::IDebugDraw* debugDrawPtr)
    {
        mPhysXInterface = physXInterface;
        mContactManager = std::make_unique<ContactManager>();
        mDebugDrawPtr = debugDrawPtr;
    }

    ~IsaacSensorManager()
    {
        mComponents.clear();
        mContactManager.reset();
    }

    void onStart()
    {
        mContactManager->resetSensors();
        pxr::UsdPrimRange range = this->mStage->Traverse();
        mPxScene = nullptr;

        for (pxr::UsdPrimRange::iterator iter = range.begin(); iter != range.end(); ++iter)
        {
            pxr::UsdPrim prim = *iter;

            if (prim.IsA<pxr::UsdPhysicsScene>())
            {
                mPxScene = static_cast<::physx::PxScene*>(
                    mPhysXInterface->getPhysXPtr(prim.GetPrimPath(), omni::physx::PhysXType::ePTScene));

                if (mPxScene)
                {
                    break;
                }
            }
        }
    }

    void onStop()
    {
        // PxScene can change after stop is pressed so reset mDoStart bool to force OnStart to run
        for (auto& component : mComponents)
        {
            component.second->mDoStart = true;
            component.second->onStop();
        }
        mContactManager->resetSensors();

        // reset timers whenever stopped
        this->mTimeSeconds = 0;
        this->mTimeNanoSeconds = 0;
    }

    void onComponentAdd(const pxr::UsdPrim& prim)
    {
        std::unique_ptr<IsaacBaseSensorComponent> component;
        if (prim.IsA<pxr::IsaacSensorSchemaIsaacContactSensor>())
        {
            component = std::make_unique<ContactSensor>(mDebugDrawPtr, mPhysXInterface, mContactManager.get());
            component->initialize(pxr::IsaacSensorSchemaIsaacContactSensor(prim), mStage);

            ContactSensor* contactSensor = dynamic_cast<ContactSensor*>(component.get());
            bool validParentFound = contactSensor->findValidParent();

            if (!validParentFound)
            {
                CARB_LOG_ERROR("Failed to create contact sensor, parent prim is not found or invalid");
                return;
            }
        }
        else if (prim.IsA<pxr::IsaacSensorSchemaIsaacImuSensor>())
        {
            component = std::make_unique<ImuSensor>(mDebugDrawPtr, mPhysXInterface);
            component->initialize(pxr::IsaacSensorSchemaIsaacImuSensor(prim), mStage);

            ImuSensor* imuSensor = dynamic_cast<ImuSensor*>(component.get());
            bool validParentFound = imuSensor->findValidParent();

            if (!validParentFound)
            {
                CARB_LOG_ERROR("Failed to create imu sensor, parent prim is not found or invalid");
                return;
            }
        }

        if (component)
        {
            // CARB_LOG_INFO("Create: Isaac Sensor %s with type: %s", prim.GetPath().GetString().c_str(),
            //                 component->getPrim().GetPrim().GetTypeName().GetString().c_str());
            mComponents[prim.GetPath().GetString()] = std::move(component);
        }
    }

    virtual void onComponentChange(const pxr::UsdPrim& prim)
    {
        utils::BridgeApplicationBase<IsaacBaseSensorComponent>::onComponentChange(prim);
        // update properties of this prim (onComponentChange)
        if (mComponents.find(prim.GetPath().GetString()) != mComponents.end())
        {
            mComponents[prim.GetPath().GetString()]->onComponentChange();
        }
    }

    void onPhysicsStep(const double& dt)
    {

        mContactManager->onPhysicsStep(static_cast<float>(mTimeSeconds), static_cast<float>(dt));

        for (auto& component : mComponents)
        {
            if (component.second->mDoStart == true)
            {
                // if the component has not started yet, check to see if its enabled
                // if not enabled, do not start
                if (component.second->getEnabled())
                {
                    component.second->onStart();
                    component.second->mDoStart = false;
                }
            }
            if (component.second->getEnabled())
            {
                component.second.get()->updateTimestamp(this->mTimeSeconds, dt, this->mTimeNanoSeconds);
                component.second->onPhysicsStep();
            }
        }
        this->mTimeSeconds += dt;
        this->mTimeNanoSeconds = static_cast<int64_t>(mTimeSeconds * 1e9);

        // update timestep
    }

    // override tick in bridge application
    virtual void tick(double dt)
    {
        if (mComponents.size() == 0)
        {
            return;
        }
        for (auto& component : mComponents)
        {
            if (component.second->mDoStart == true)
            {
                // if the component has not started yet, check to see if its enabled
                // if not enabled, do not start
                if (component.second->getEnabled())
                {
                    component.second->onStart();
                    component.second->mDoStart = false;
                }
            }
            if (component.second->getEnabled())
            {
                component.second->preTick();
                component.second->tick();
            }
        }
    }

    void drawSensor()
    {
        if (mComponents.size() == 0)
        {
            return;
        }
        for (auto& component : mComponents)
        {
            if (component.second->getEnabled() && component.second->getVisualize())
            {
                component.second.get()->draw();
            }
        }
    }

    ContactSensor* getContactSensor(const pxr::UsdPrim& prim)
    {
        if (prim)
        {
            if (mComponents.find(prim.GetPath().GetString()) != mComponents.end())
            {
                return dynamic_cast<ContactSensor*>(mComponents[prim.GetPath().GetString()].get());
            }
        }
        return nullptr;
    }

    ContactManager* getContactManager()
    {
        return mContactManager.get();
    }

    ImuSensor* getImuSensor(const pxr::UsdPrim& prim)
    {
        if (prim)
        {
            if (mComponents.find(prim.GetPath().GetString()) != mComponents.end())
            {
                return dynamic_cast<ImuSensor*>(mComponents[prim.GetPath().GetString()].get());
            }
        }
        return nullptr;
    }

private:
    ::physx::PxScene* mPxScene = nullptr;
    omni::physx::IPhysx* mPhysXInterface = nullptr;
    std::unique_ptr<ContactManager> mContactManager = nullptr;
    omni::renderer::IDebugDraw* mDebugDrawPtr = nullptr;
};
}
}
}
