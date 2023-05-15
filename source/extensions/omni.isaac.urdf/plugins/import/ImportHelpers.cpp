// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "ImportHelpers.h"

#include "../core/PathUtils.h"

#include <carb/logging/Log.h>

#include <boost/algorithm/string.hpp>

namespace omni
{
namespace isaac
{
namespace urdf
{


void inertiaToUrdf(const Matrix33& inertia, UrdfInertia& urdfInertia)
{
    urdfInertia.ixx = inertia.cols[0].x;
    urdfInertia.ixy = inertia.cols[0].y;
    urdfInertia.ixz = inertia.cols[0].z;
    urdfInertia.iyy = inertia.cols[1].y;
    urdfInertia.iyz = inertia.cols[1].z;
    urdfInertia.izz = inertia.cols[2].z;
}

void urdfToInertia(const UrdfInertia& urdfInertia, Matrix33& inertia)
{
    inertia.cols[0].x = urdfInertia.ixx;
    inertia.cols[0].y = urdfInertia.ixy;
    inertia.cols[0].z = urdfInertia.ixz;

    inertia.cols[1].x = urdfInertia.ixy;
    inertia.cols[1].y = urdfInertia.iyy;
    inertia.cols[1].z = urdfInertia.iyz;

    inertia.cols[2].x = urdfInertia.ixz;
    inertia.cols[2].y = urdfInertia.iyz;
    inertia.cols[2].z = urdfInertia.izz;
}

void mergeFixedChildLinks(const KinematicChain::Node& parentNode, UrdfRobot& robot)
{
    // Child contribution to inertia
    for (auto& childNode : parentNode.childNodes_)
    {
        // Depth first
        mergeFixedChildLinks(*childNode, robot);

        if (robot.joints.at(childNode->parentJointName_).type == UrdfJointType::FIXED)
        {
            auto& urdfParentLink = robot.links.at(parentNode.linkName_);
            auto& urdfChildLink = robot.links.at(childNode->linkName_);
            // The pose of the child with respect to the parent is defined at the joint connecting them
            Transform poseChildToParent = robot.joints.at(childNode->parentJointName_).origin;

            // At least one of the link masses has to be defined
            if ((urdfParentLink.inertial.hasMass || urdfChildLink.inertial.hasMass) &&
                (urdfParentLink.inertial.mass > 0.0f || urdfParentLink.inertial.mass > 0.0f))
            {
                // Move inertial parameters to parent
                Transform parentInertialInParentFrame = urdfParentLink.inertial.origin;
                Transform childInertialInParentFrame = poseChildToParent * urdfChildLink.inertial.origin;

                float totMass = urdfParentLink.inertial.mass + urdfChildLink.inertial.mass;
                Vec3 com = (urdfParentLink.inertial.mass * parentInertialInParentFrame.p +
                            urdfChildLink.inertial.mass * childInertialInParentFrame.p) /
                           totMass;

                Vec3 deltaParent = parentInertialInParentFrame.p - com;
                Vec3 deltaChild = childInertialInParentFrame.p - com;
                Matrix33 rotParentOrigin(parentInertialInParentFrame.q);
                Matrix33 rotChildOrigin(childInertialInParentFrame.q);

                Matrix33 parentInertia;
                Matrix33 childInertia;
                urdfToInertia(urdfParentLink.inertial.inertia, parentInertia);
                urdfToInertia(urdfChildLink.inertial.inertia, childInertia);

                Matrix33 inertiaParent = rotParentOrigin * parentInertia * Transpose(rotParentOrigin) +
                                         urdfParentLink.inertial.mass * (LengthSq(deltaParent) * Matrix33::Identity() -
                                                                         Outer(deltaParent, deltaParent));

                Matrix33 inertiaChild = rotChildOrigin * childInertia * Transpose(rotChildOrigin) +
                                        urdfChildLink.inertial.mass * (LengthSq(deltaChild) * Matrix33::Identity() -
                                                                       Outer(deltaChild, deltaChild));

                Matrix33 inertia = Transpose(rotParentOrigin) * (inertiaParent + inertiaChild) * rotParentOrigin;

                urdfParentLink.inertial.origin.p.x = com.x;
                urdfParentLink.inertial.origin.p.y = com.y;
                urdfParentLink.inertial.origin.p.z = com.z;
                urdfParentLink.inertial.mass = totMass;
                inertiaToUrdf(inertia, urdfParentLink.inertial.inertia);
            }

            // Move collisions to parent
            for (auto& collision : urdfChildLink.collisions)
            {
                collision.origin = poseChildToParent * collision.origin;
                urdfParentLink.collisions.push_back(collision);
            }
            urdfChildLink.collisions.clear();
            // Move visuals to parent
            for (auto& visual : urdfChildLink.visuals)
            {
                visual.origin = poseChildToParent * visual.origin;
                urdfParentLink.visuals.push_back(visual);
            }
            urdfChildLink.visuals.clear();
            for (auto& joint : robot.joints)
            {
                if (joint.second.parentLinkName == childNode->linkName_)
                {
                    joint.second.parentLinkName = parentNode.linkName_;
                    joint.second.origin = poseChildToParent * joint.second.origin;
                }
            }

            // Remove this link and parent joint
            // if (!urdfChildLink.softs.size())
            // {
            robot.links.erase(childNode->linkName_);
            robot.joints.erase(childNode->parentJointName_);
            // }
        }
    }
}

bool collapseFixedJoints(UrdfRobot& robot)
{
    KinematicChain chain;
    if (!chain.computeKinematicChain(robot))
    {
        return false;
    }

    auto& parentNode = chain.baseNode;
    if (!parentNode->childNodes_.empty())
    {
        mergeFixedChildLinks(*parentNode, robot);
    }

    return true;
}


Vec3 urdfAxisToVec(const UrdfAxis& axis)
{
    return { axis.x, axis.y, axis.z };
}

std::string resolveXrefPath(const std::string& assetRoot, const std::string& urdfPath, const std::string& xrefpath)
{
    // Remove the package prefix if it exists
    std::string xrefPath = xrefpath;
    std::string prefix = "package://";
    std::size_t p = xrefPath.find(prefix);

    if (xrefPath.find("omniverse://") != std::string::npos)
    {
        CARB_LOG_INFO("Path is on nucleus server, will assume that it is fully resolved already");
        return xrefPath;
    }
    if (p != std::string::npos)
    {
        xrefPath.replace(p, prefix.size(), "");
    }

    if (isAbsolutePath(xrefPath.c_str()))
    {
        if (testPath(xrefPath.c_str()) == PathType::eFile)
        {
            return xrefPath;
        }
        else
        {
            // xref not found
            return std::string();
        }
    }

    std::string rootPath;
    if (isAbsolutePath(urdfPath.c_str()))
    {
        rootPath = urdfPath;
    }
    else
    {
        rootPath = pathJoin(assetRoot, urdfPath);
    }

    auto s = rootPath.find_last_of("/\\");
    while (s != std::string::npos && s > 0)
    {
        auto basePath = rootPath.substr(0, s + 1);
        auto path = pathJoin(basePath, xrefPath);
        CARB_LOG_INFO("trying '%s' (%d)\n", path.c_str(), int(testPath(path.c_str())));
        if (testPath(path.c_str()) == PathType::eFile)
        {
            return path;
        }
        // if (strncmp(basePath.c_str(), assetRoot.c_str(), s) == 0)
        // {
        //     // don't search upwards of assetRoot
        //     break;
        // }
        s = rootPath.find_last_of("/\\", s - 1);
    }

    // hmmm, should we accept pure relative paths?
    if (testPath(xrefPath.c_str()) == PathType::eFile)
    {
        return xrefPath;
    }
    // Check if ROS_PACKAGE_PATH is defined and if so go through all searching for the package
    char* exists = getenv("ROS_PACKAGE_PATH");
    if (exists != NULL)
    {
        std::string rosPackagePath = std::string(exists);
        if (rosPackagePath.size())
        {
            std::vector<std::string> results;
            boost::split(results, rosPackagePath, [](char c) { return c == ':'; });
            for (size_t i = 0; i < results.size(); i++)
            {
                std::string path = results[i];
                if (path.size() > 0)
                {
                    auto packagePath = pathJoin(path, xrefPath);
                    CARB_LOG_INFO("Testing ROS Package path '%s' (%d)\n", packagePath.c_str(),
                                  int(testPath(packagePath.c_str())));
                    if (testPath(packagePath.c_str()) == PathType::eFile)
                    {
                        return packagePath;
                    }
                }
            }
        }
    }
    else
    {
        CARB_LOG_WARN("ROS_PACKAGE_PATH not defined, will skip checking ROS packages");
    }
    CARB_LOG_WARN("Path: %s not found", xrefpath.c_str());
    // if we got here, we failed to resolve the path
    return std::string();
}

bool IsUsdFile(const std::string& filename)
{
    std::vector<std::string> types = { ".usd", ".usda" };

    for (auto& t : types)
    {
        if (t.size() > filename.size())
            continue;
        if (std::equal(t.rbegin(), t.rend(), filename.rbegin()))
        {
            return true;
        }
    }
    return false;
}

// Make a path name that is not already used.
std::string GetNewSdfPathString(pxr::UsdStageWeakPtr stage, std::string path, int nameClashNum)
{
    bool appendedNumber = false;
    int numberAppended = std::max<int>(nameClashNum, 0);
    size_t indexOfNumber = 0;
    if (stage->GetPrimAtPath(pxr::SdfPath(path)))
    {
        appendedNumber = true;
        std::string name = pxr::SdfPath(path).GetName();
        size_t last_ = name.find_last_of('_');
        indexOfNumber = path.length() + 1;
        if (last_ == std::string::npos)
        {
            // no '_' found, so just tack on the end.
            path += "_" + std::to_string(numberAppended);
        }
        else
        {
            // There was a _, if the last part of that is a number
            // then replace that number with one higher or nameClashNum,
            // or just tack on the number if it is last character.
            if (last_ == name.length() - 1)
            {
                path += "_" + std::to_string(numberAppended);
            }
            else
            {
                char* p;
                std::string after_ = name.substr(last_ + 1, name.length());
                long converted = strtol(after_.c_str(), &p, 10);
                if (*p)
                {
                    // not a number
                    path += "_" + std::to_string(numberAppended);
                }
                else
                {

                    numberAppended = nameClashNum == -1 ? converted + 1 : nameClashNum;
                    indexOfNumber = path.length() - name.length() + last_ + 1;
                    path = path.substr(0, indexOfNumber);
                    path += std::to_string(numberAppended);
                }
            }
        }
    }
    if (appendedNumber)
    {
        // we just added a number, so we have to make sure the new path is unique.
        while (stage->GetPrimAtPath(pxr::SdfPath(path)))
        {
            path = path.substr(0, indexOfNumber);
            numberAppended += 1;
            path += std::to_string(numberAppended);
        }
    }
#if 0
	else
	{
		while (stage->GetPrimAtPath(pxr::SdfPath(path))) path += ":" + std::to_string(nameClashNum);
	}
#endif
    return path;
}

bool addVisualMeshToCollision(UrdfRobot& robot)
{
    for (auto& link : robot.links)
    {
        if (!link.second.visuals.empty() && link.second.collisions.empty())
        {
            for (auto& visual : link.second.visuals)
            {
                UrdfCollision collision{ visual.name, visual.origin, visual.geometry };

                link.second.collisions.push_back(collision);
            }
        }
    }

    return true;
}
}
}
}
