// // Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// #pragma once

// #include "../Core/GxfComponent.h"

// #include <carb/Types.h>

// #include <omni/isaac/range_sensor/RangeSensorInterface.h>
// #include <robotEngineBridgeSchema/robotEngineUltrasonic.h>

// #include <string>

// namespace omni
// {
// namespace isaac
// {
// namespace gxf_bridge
// {

// class UltrasonicComponent : public GxfComponent
// {
// public:
//     /**
//      * @brief Construct a new Component object
//      *
//      * @param appHandle
//      * @param prim
//      * @param stage
//      */
//     UltrasonicComponent();

//     /**
//      * @brief Destroy the Component object
//      *
//      */
//     ~UltrasonicComponent();


//     /**
//      * @brief The sensor pointer might not be valid, so force update on start
//      *
//      */
//     virtual void onStart();

//     /**
//      * @brief
//      *
//      */
//     virtual void tick();

//     /**
//      * @brief
//      *
//      */
//     virtual void publishAllMessages();

//     /**
//      * @brief
//      *
//      */
//     virtual void onComponentChange();

// private:
//     omni::isaac::range_sensor::UltrasonicSensorInterface* mUltrasonicSensorInterface = nullptr;


//     /// The name of the channel on which state informations is published
//     std::string mOutputComponent = "output";
//     std::string mScanChannelName = "uss_envelopes";
//     pxr::SdfPath mUltrasonicPath = pxr::SdfPath("/");

//     omni::isaac::range_sensor::RangeSensorHandle mUltrasonicSensorHandle = omni::isaac::range_sensor::kInvalidHandle;
//     bool mSkipFirstFrame = true;
//     double mUnitScale = 1.0;
// };
// }
// }
// }
