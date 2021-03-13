// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once
#include "../Core/GxfComponent.h"

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxVehicle.h>
#include <physx/include/PxPhysicsAPI.h>
#include <robotEngineBridgeSchema/robotEngineVehicle.h>

#include <deque>
#include <string>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{
namespace gxf_bridge
{
struct WheelFlag
{
    enum Enum
    {
        eHAS_WHEEL_CONTROLLER = (1 << 0),
        eHAS_DRIVE = (1 << 1), // only valid for DriveType::eBASIC
        eHAS_STEER = (1 << 2), // only valid for DriveType::eBASIC
        eHAS_BRAKE = (1 << 3) // only valid for DriveType::eBASIC
    };
};
struct WheelCache
{
    pxr::SdfPath usdPath;
    int32_t index;
    uint32_t wheelFlags;
    float maxSteerAngle;
    float maxBrakeTorque;
    float maxHandBrakeTorque;
    float mass;
    float radius;

    static const uint32_t sInitialWheelCapacity = 4;
};


struct DriveType
{
    enum Enum
    {
        eNONE = 0, // user wants to control wheels directly
        eBASIC, // simple steering support and max brake/drive torque
        eSTANDARD // full engine, gears etc. setup
    };
};

struct CacheStateFlag
{
    enum Enum
    {
        eUSD = (1 << 0), // USD properties have been cached
        eINTERNAL = (1 << 1), // internal object handles etc. have been cached
        eVALID = eUSD | eINTERNAL
    };
};

struct Cache
{
    Cache() : state(0)
    {
    }

    size_t vehicleId;
    ::physx::PxVehicleWheels* mVehiclePtr = nullptr;
    union
    {
        std::vector<WheelCache>* wheels;
    };
    float peakDriveTorque; // only used for DriveType::eBASIC
    DriveType::Enum driveType;
    uint8_t state;
    bool hasController; // whether the vehicle has any sort of controller (VehicleControllerAPI or
                        // WheelControllerAPI). Ideally, we would rather not create a VehicleController instance to
                        // begin with if there is no controller API though.
    float rearWidth = 0.0f;
    float axleSeparation = 0.0f;
    int numDrivenWheels = 0; // Lets us divide torque evenly between all driven wheels
    int numBrakedWheels = 0; // Lets us divide torque evenly between all braked wheels
    float chassisMass = 0;
    float totalMass = 0;

    ::physx::PxVec3 forward = ::physx::PxVec3(1, 0, 0);
};


/**
 * @brief A simulated differential-base driver based on speed commands.
 *
 */
class VehicleSimulator : public GxfComponent
{
public:
    VehicleSimulator();
    /**
     * @brief The articulation for the robot might not be valid, so force update on start
     *
     */
    virtual void onStart();

    virtual void onStop();

    /**
     * @brief Get latest command message and publish ground truth data
     *
     */
    virtual void tick();
    /**
     * @brief Update the properties of this component based on any USD changes
     *
     */
    virtual void onComponentChange();


private:
    void fillCache();
    void setAckermannSteering(const float steeringAngle, const int leftWheel, const int rightWheel);
    pxr::SdfPath mVehiclePath;
    pxr::UsdPrim mVehiclePrim;
    double mUnitScale;

    /// The name of the channel on which commands are received
    std::string mInputComponent = "input";
    std::string mCommandChannelName = "vehicle_command";

    /// The name of the channel on which state informations is published
    std::string mOutputComponent = "output";
    std::string mStateChannelName = "vehicle_state";

    omni::physx::IPhysx* mPhysxPtr = nullptr;
    // omni::physx::IPhysxVehicle* mPhysxVehiclePtr = nullptr;
    Cache mCache;

    const float mReverseTime = 0.5f;
    const float mReverseSpeed = 1.0f;
    bool mInReverse = false;
    float mBrakeTimer = 0.0f;
    float mCurrentSteeringAngle = 0.0f;

    float mPrevForwardSpeed = 0;
    float mForwardAcceleration = 0;
    std::deque<float> mAveragedAcceleration;
    const size_t mMovingAverageSize = 200;
};
}
}
}
}
