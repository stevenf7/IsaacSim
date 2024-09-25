// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <include/Ros2Node.h>

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
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            db.logError("Unable to create ROS2 node, please check that namespace is valid");
            return false;
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
            if (qosProfile == "")
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
        float* rangeData = (float*)malloc(sizeof(float) * buffSize);
        memcpy(rangeData, rangePoints, sizeof(float) * buffSize);

        const uint8_t* intensityPointsCpu = static_cast<const uint8_t*>(db.inputs.intensitiesData().data());
        float* intensityData = (float*)malloc(sizeof(float) * buffSize);

        for (size_t i = 0; i < buffSize; i++)
        {
            intensityData[i] = static_cast<float>(intensityPointsCpu[i]);
        }

        state.m_message->writeData(db.inputs.timeStamp(), state.m_frameId, db.inputs.azimuthRange(), rotationRate,
                                   db.inputs.depthRange(), buffSize, rangeData, intensityData,
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

    std::string m_frameId = "sim_lidar";
};

REGISTER_OGN_NODE()
