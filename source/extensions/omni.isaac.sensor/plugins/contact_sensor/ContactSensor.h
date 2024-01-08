// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../core/BaseSensorComponent.h"
#include "ContactManager.h"
#include "IsaacSensor.h"

#include <isaacSensorSchema/isaacContactSensor.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>
#include <pxr/base/gf/vec4d.h>
#include <pxr/usd/usd/inherits.h>
#include <usdrt/gf/matrix.h>
#include <usdrt/gf/vec.h>

#include <cmath>
#include <vector>

#define PI 3.14159265

namespace omni
{
namespace isaac
{
namespace sensor
{
class ContactSensor : public IsaacBaseSensorComponent
{
public:
    ContactSensor(omni::renderer::IDebugDraw* debugDraw, omni::physx::IPhysx* PhysXInterface, ContactManager* contactManager)
        : IsaacBaseSensorComponent(debugDraw)
    {
        mPhysXInterfacePtr = PhysXInterface;
        mContactManagerPtr = contactManager;
        mDebugDrawPtr = debugDraw;
    }

    virtual ~ContactSensor();

    void reset();

    // this function will draw a sphere based on the radius and location of the contact sensor
    void drawCircle(const omni::math::linalg::vec3d& _pose, const int& nsegment);

    virtual void draw();

    CsRawData* getRawData(size_t& size);

    CsReading getSimSensorReading();

    CsReading getSensorReadings(size_t& numReadings);

    CsReading getSensorReading(const bool& getLatestValue = false);

    // use the index to indicate the recency of the data
    // 0 for old data, 1 for new data for the reading pair
    void processRawContacts(CsRawData* rawContact, const size_t& size, const size_t& index, const double& time);

    virtual void onPhysicsStep();

    virtual void tick()
    {
    }

    void setContactReportApi();

    bool findValidParent();

    void onComponentChange();

    // the virtual onstop will clear everything on stop, the overloaded onstop will redraw the sensor after stop
    virtual void onStop();

    // functions for internal debugging
    void printRawData(CsRawData* data);

    // functions for internal debugging
    void printReadingPair();

private:
    pxr::GfVec4f mColor = pxr::GfVec4f(1.0f, 1.0f, 1.0f, 1.0f);
    CsProperties mProps;

    size_t mSize;
    CsReading mReadingPair[2]; // Data obtained on simulation timestamp
    CsReading mSensorReading;
    CsRawData* mContactsRawData = nullptr;
    ContactManager* mContactManagerPtr = nullptr;
    omni::renderer::IDebugDraw* mDebugDrawPtr = nullptr;
    omni::physx::IPhysx* mPhysXInterfacePtr = nullptr;
    bool mCurrent{ 0 };
    bool mPreviousEnabled{ true };
    float mCurrentTime{ 0 };
    float mSensorTime{ 0 };
};
}
}
}
