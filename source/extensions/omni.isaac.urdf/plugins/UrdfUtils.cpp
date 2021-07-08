// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "import/ImportHelpers.h"
#include "import/UrdfImporter.h"

#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>

#include <omni/ext/IExt.h>
#include <omni/isaac/urdf/Urdf.h>
#include <omni/kit/IApp.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/usd/UsdContext.h>
#include <pybind11/pybind11/pybind11.h>

#include <fstream>
#include <memory>

#define EXTENSION_NAME "omni.isaac.urdf"

using namespace carb;

const struct carb::PluginImplDesc kPluginImpl = { EXTENSION_NAME, "URDF Utilities", "NVIDIA",
                                                  carb::PluginHotReload::eEnabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::urdf::Urdf)
CARB_PLUGIN_IMPL_DEPS(omni::kit::IApp, carb::logging::ILogging)

namespace
{

carb::Framework* g_framework = nullptr;

omni::isaac::urdf::UrdfRobot parseUrdf(const std::string& assetRoot,
                                       const std::string& assetName,
                                       const omni::isaac::urdf::ImportConfig& importConfig)
{
    omni::isaac::urdf::UrdfRobot robot;

    std::string filename = assetRoot + "/" + assetName;
    pxr::UsdStageWeakPtr stage = omni::usd::UsdContext::getContext()->getStage();
    if (stage)
    {


        CARB_LOG_INFO("Trying to import %s", filename.c_str());

        if (parseUrdf(assetRoot, assetName, robot))
        {
        }
        else
        {
            CARB_LOG_ERROR("Failed to parse URDF file '%s'", assetName.c_str());
            return robot;
        }

        if (importConfig.mergeFixedJoints)
        {
            collapseFixedJoints(robot);
        }

        for (auto& joint : robot.joints)
        {
            joint.second.drive.targetType = importConfig.defaultDriveType;
            if (joint.second.drive.targetType == omni::isaac::urdf::UrdfJointTargetType::POSITION)
            {
                joint.second.dynamics.stiffness = importConfig.defaultDriveStrength;
            }
            else
            {
                joint.second.dynamics.damping = importConfig.defaultDriveStrength;
            }
        }
    }
    return robot;
}
std::string importRobot(const std::string& assetRoot,
                        const std::string& assetName,
                        const omni::isaac::urdf::UrdfRobot& robot,
                        const omni::isaac::urdf::ImportConfig& importConfig)
{

    omni::isaac::urdf::UrdfImporter urdfImporter(assetRoot, assetName, importConfig);
    pxr::UsdStageWeakPtr stage = omni::usd::UsdContext::getContext()->getStage();
    if (stage)
    {
        return urdfImporter.addToStage(stage, robot);
    }
    else
    {
        CARB_LOG_ERROR("Stage pointer not valid, could not import urdf to stage");
    }
    return "";
}
}


pybind11::list addLinksAndJoints(omni::isaac::urdf::KinematicChain::Node* parentNode)
{
    if (parentNode->parentJointName_ == "")
    {
    }
    pybind11::list temp_list;

    if (!parentNode->childNodes_.empty())
    {
        for (const auto& childNode : parentNode->childNodes_)
        {
            pybind11::dict temp;
            temp["A_joint"] = childNode->parentJointName_;
            temp["A_link"] = parentNode->linkName_;
            temp["B_link"] = childNode->linkName_;
            temp["B_node"] = addLinksAndJoints(childNode.get());
            temp_list.append(temp);
        }
    }
    return temp_list;
}

pybind11::dict getKinematicChain(const omni::isaac::urdf::UrdfRobot& robot)
{
    pybind11::dict robotDict;
    omni::isaac::urdf::KinematicChain chain;
    if (chain.computeKinematicChain(robot))
    {
        robotDict["A_joint"] = "";
        robotDict["B_link"] = chain.baseNode->linkName_;
        robotDict["B_node"] = addLinksAndJoints(chain.baseNode.get());
    }
    return robotDict;
}

CARB_EXPORT void carbOnPluginStartup()
{
    CARB_LOG_INFO("Startup URDF Extension");

    // Get app interface using Carbonite Framework
    g_framework = carb::getFramework();
}


CARB_EXPORT void carbOnPluginShutdown()
{
}


void fillInterface(omni::isaac::urdf::Urdf& iface)
{
    memset(&iface, 0, sizeof(iface));
    iface.parseUrdf = parseUrdf;
    iface.importRobot = importRobot;
    iface.getKinematicChain = getKinematicChain;
}
