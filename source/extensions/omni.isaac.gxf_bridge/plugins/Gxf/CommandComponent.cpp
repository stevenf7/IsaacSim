// // Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// // clang-format off
// #include <UsdPCH.h>
// // clang-format on

// #include "CommandComponent.h"

// #include "../Core/GxfComponent.h"
// #include "extensions/messages/simulation_command_message.hpp"

// #include <carb/Framework.h>
// #include <carb/Types.h>
// #include <carb/logging/Log.h>
// #include <carb/profiler/Profile.h>

// #include <string>
// #include <vector>


// namespace omni
// {
// namespace isaac
// {
// namespace gxf_bridge
// {

// CommandComponent::CommandComponent() : GxfComponent()
// {


//     mJsonSerializer = carb::getCachedInterface<carb::dictionary::ISerializer>();
//     if (!mJsonSerializer)
//     {
//         CARB_LOG_ERROR("Failed to acquire carb::dictionary::ISerializer interface");
//         return;
//     }

//     mIDict = carb::getCachedInterface<carb::dictionary::IDictionary>();

//     if (!mIDict)
//     {
//         CARB_LOG_ERROR("Failed to acquire carb::dictionary::IDictionary interface");
//         return;
//     }

//     mScripting = carb::getCachedInterface<omni::kit::IApp>()->getPythonScripting();
// }

// CommandComponent::~CommandComponent()
// {
// }

// void CommandComponent::onStart()
// {
//     onComponentChange();
//     mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
//     mSkipFirstFrame = true;
// }
// void CommandComponent::tick()
// {
//     if (mSkipFirstFrame)
//     {
//         mSkipFirstFrame = false;
//         return;
//     }
//     CARB_PROFILE_ZONE(0, "REB CommandComponent Tick");
//     auto message = nvidia::gxf::Entity::New(mContext);

//     if (receive(mInputComponent, mInputChannel, message) != gxf_result_t::GXF_SUCCESS)
//     {
//         return;
//     }
//     auto maybe_message = nvidia::isaac::GetSimulationCommandMessage(message.value());


//     if (!maybe_message)
//     {

//         // return maybe_message.error();
//         CARB_LOG_WARN("Simulation Command Message Could Not Be Parsed");
//         return;
//     }

//     nvidia::isaac::SimulationCommandMessageParts commandMessage = std::move(maybe_message.value());

//     for (auto& command : commandMessage.commands)
//     {

//         // execute command
//         std::string commandName = command->command_name;
//         // std::string debug = command->attributes.dump();
//         // CARB_LOG_ERROR("received command with name %s and data %s", commandName.c_str(), debug.c_str());
//         std::string arguments;

//         for (auto& attr : command->attributes.items())
//         {
//             //     // const carb::dictionary::Item* attributeItem = mIDict->getItemChildByIndex(jsonBase, i);
//             //     // TODO Convert this item into its name and value
//             //     //(is there a simpler way to do this if we already have json?)

//             arguments += attr.key() + "=" + attr.value().dump() + ", ";
//         }
//         std::string imports = "import omni.kit.commands\n";
//         std::string fullCommand = imports + "omni.kit.commands.execute('" + commandName + "', " + arguments + ")";
//         CARB_LOG_WARN("Executing Command: %s", fullCommand.c_str());
//         mScripting->executeString(fullCommand.c_str());
//     }
// }

// void CommandComponent::onComponentChange()
// {
//     // CARB_LOG_ERROR("CommandComponent Update");
//     GxfComponent::onComponentChange();
//     const pxr::RobotEngineBridgeSchemaRobotEngineCommand& typedPrim =
//         (pxr::RobotEngineBridgeSchemaRobotEngineCommand)mPrim;
//     isaac::utils::safeGetAttribute(typedPrim.GetInputComponentAttr(), mInputComponent);
//     isaac::utils::safeGetAttribute(typedPrim.GetInputChannelAttr(), mInputChannel);
// }
// }
// }
// }
