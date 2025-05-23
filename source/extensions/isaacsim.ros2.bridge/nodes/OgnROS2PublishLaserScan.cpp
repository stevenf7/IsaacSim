// SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <isaacsim/ros2/bridge/Ros2Node.h>

#include <OgnROS2PublishLaserScanDatabase.h>

using namespace isaacsim::ros2::bridge;

class OgnROS2PublishLaserScan : public Ros2Node
{
public:
    static bool compute(OgnROS2PublishLaserScanDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2PublishLaserScan>();

        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.isInitialized())
        {
            const GraphContextObj& context = db.abi_context();
            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            if (!state.initializeNodeHandle(
                    std::string(nodeObj.iNode->getPrimPath(nodeObj)),
                    collectNamespace(db.inputs.nodeNamespace(),
                                     stage->GetPrimAtPath(pxr::SdfPath(nodeObj.iNode->getPrimPath(nodeObj)))),
                    db.inputs.context()))
            {
                db.logError("Unable to create ROS2 node, please check that namespace is valid");
                return false;
            }
        }

        // Publisher was not valid, create a new one
        if (!state.m_publisher)
        {
            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(state.m_namespaceName, topicName);
            if (!state.m_factory->validateTopicName(fullTopicName))
            {
                db.logError("Unable to create ROS2 publisher, invalid topic name");
                return false;
            }

            state.m_message = state.m_factory->createLaserScanMessage();

            Ros2QoSProfile qos;
            const std::string& qosProfile = db.inputs.qosProfile();
            if (qosProfile.empty())
            {
                qos.depth = db.inputs.queueSize();
            }
            else
            {
                if (!jsonToRos2QoSProfile(qos, qosProfile))
                {
                    return false;
                }
            }

            state.m_publisher = state.m_factory->createPublisher(
                state.m_nodeHandle.get(), fullTopicName.c_str(), state.m_message->getTypeSupportHandle(), qos);
            state.m_frameId = db.inputs.frameId();
            return true;
        }

        return state.publishLidar(db);
    }

    bool publishLidar(OgnROS2PublishLaserScanDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Lidar 2D Pub");
        auto& state = db.perInstanceState<OgnROS2PublishLaserScan>();

        // Check if subscription count is 0
        if (!m_publishWithoutVerification && !state.m_publisher.get()->getSubscriptionCount())
        {
            return false;
        }

        size_t buffSize = db.inputs.numCols() * db.inputs.numRows();
        if (buffSize == 0)
        {
            return false;
        }
        if (db.inputs.numRows() != 1)
        {
            db.logError(
                "Number of rows must be equal to 1. High LOD not supported for LaserScan, only 2D Lidar Supported for LaserScan. Please disable Lidar High LOD setting");
            return false;
        }

        float rotationRate = db.inputs.rotationRate();

        if (!db.inputs.linearDepthData.isValid() || !db.inputs.intensitiesData.isValid())
        {
            db.logError("Buffers are invalid");
            return false;
        }

        if (db.inputs.linearDepthData.size() != db.inputs.intensitiesData.size())
        {
            db.logError("Linear Depth data and Intensities data sizes do not match");
            return false;
        }

        if (buffSize != db.inputs.linearDepthData.size())
        {
            db.logError("Lidar data with %d rows and %d columns does not match input buffer array size of %d",
                        db.inputs.numRows(), db.inputs.numCols(), db.inputs.linearDepthData.size());
            return false;
        }

        const float* rangePoints = static_cast<const float*>(db.inputs.linearDepthData().data());
        m_rangeData.resize(buffSize);
        memcpy(m_rangeData.data(), rangePoints, sizeof(float) * buffSize);

        const uint8_t* intensityPointsCpu = static_cast<const uint8_t*>(db.inputs.intensitiesData().data());
        m_intensityData.resize(buffSize);

        std::transform(intensityPointsCpu, intensityPointsCpu + buffSize, m_intensityData.begin(),
                       [](uint8_t val) { return static_cast<float>(val); });

        state.m_message->writeData(db.inputs.timeStamp(), state.m_frameId, db.inputs.azimuthRange(), rotationRate,
                                   db.inputs.depthRange(), buffSize, m_rangeData.data(), m_intensityData.data(),
                                   db.inputs.horizontalResolution(), db.inputs.horizontalFov());

        state.m_publisher.get()->publish(state.m_message->getPtr());

        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2PublishLaserScanDatabase::sPerInstanceState<OgnROS2PublishLaserScan>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        m_publisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }


private:
    std::shared_ptr<Ros2Publisher> m_publisher = nullptr;
    std::shared_ptr<Ros2LaserScanMessage> m_message = nullptr;
    std::vector<float> m_rangeData;
    std::vector<float> m_intensityData;


    std::string m_frameId = "sim_lidar";
};

REGISTER_OGN_NODE()
