#include "KinematicChain.h"

#include <carb/logging/Log.h>

#include <algorithm>

namespace omni
{
namespace isaac
{
namespace urdf
{
KinematicChain::~KinematicChain()
{
    baseNode.reset();
}

// Computes the kinematic chain for a Urdf robot
bool KinematicChain::computeKinematicChain(const UrdfRobot& urdfRobot)
{
    bool success = true;

    if (urdfRobot.joints.empty())
    {
        if (urdfRobot.links.empty())
        {
            CARB_LOG_ERROR("*** URDF robot is empty \n");
            success = false;
        }
        else if (urdfRobot.links.size() == 1)
        {
            baseNode = std::make_unique<Node>(urdfRobot.links.begin()->second.name, "");
        }
        else
        {
            CARB_LOG_ERROR("*** URDF has multiple links that are not connected to a joint \n");
            success = false;
        }
    }
    else
    {
        std::vector<std::string> childLinkNames;

        for (auto& joint : urdfRobot.joints)
        {
            childLinkNames.push_back(joint.second.childLinkName);
        }

        // Find the base link
        std::string baseLinkName;
        for (auto& link : urdfRobot.links)
        {
            if (std::find(childLinkNames.begin(), childLinkNames.end(), link.second.name) == childLinkNames.end())
            {
#ifdef VERBOSE_URDF
                CARB_LOG_INFO("Found base link called %s \n", link.second.name.c_str());
#endif
                baseLinkName = link.second.name;
                break;
            }
        }
        if (baseLinkName.empty())
        {
            CARB_LOG_ERROR("*** Could not find base link \n");
            success = false;
        }

        baseNode = std::make_unique<Node>(baseLinkName, "");

        // Recursively add the rest of the kinematic chain
        computeChildNodes(baseNode, urdfRobot);
    }

    return success;
}

void KinematicChain::computeChildNodes(std::unique_ptr<Node>& parentNode, const UrdfRobot& urdfRobot)
{
    for (auto& joint : urdfRobot.joints)
    {
        if (joint.second.parentLinkName == parentNode->linkName_)
        {
            std::unique_ptr<Node> childNode = std::make_unique<Node>(joint.second.childLinkName, joint.second.name);
            parentNode->childNodes_.push_back(std::move(childNode));
#ifdef VERBOSE_URDF
            CARB_LOG_INFO("Link %s has child %s \n", parentNode->linkName_.c_str(), joint.second.childLinkName.c_str());
#endif
        }
    }

    if (parentNode->childNodes_.empty())
    {
        return;
    }
    else
    {
        for (auto& childLink : parentNode->childNodes_)
        {
            computeChildNodes(childLink, urdfRobot);
        }
    }
}
}
}
}
