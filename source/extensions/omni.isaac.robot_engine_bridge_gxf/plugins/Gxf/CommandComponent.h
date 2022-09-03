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

// #include <omni/kit/IApp.h>
// #include <robotEngineBridgeSchema/robotEngineCommand.h>

// #include <string>

// namespace omni
// {
// namespace isaac
// {
// namespace robot_engine_bridge_gxf
// {

// class CommandComponent : public GxfComponent
// {
// public:
//     /**
//      * @brief Construct a new Component object
//      *
//      */
//     CommandComponent();

//     /**
//      * @brief Destroy the Component object
//      *
//      */
//     ~CommandComponent();


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
//     virtual void onComponentChange();

// private:
//     omni::kit::IAppScripting* mScripting = nullptr;
//     carb::dictionary::ISerializer* mJsonSerializer = nullptr;
//     carb::dictionary::IDictionary* mIDict = nullptr;

//     /// The name of the channel on which commands are received from
//     std::string mInputComponent = "command";
//     std::string mInputChannel = "input";

//     bool mSkipFirstFrame = true;
//     double mUnitScale = 1.0;
// };
// }
// }
// }
