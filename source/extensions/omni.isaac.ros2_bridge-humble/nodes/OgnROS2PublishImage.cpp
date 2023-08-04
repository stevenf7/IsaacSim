// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "sensor_msgs/image_encodings.hpp"
#include "sensor_msgs/msg/image.hpp"

#include <carb/graphics/GraphicsTypes.h>

#include <omni/isaac/ros/Ros2Node.h>
#include <omni/isaac/utils/Buffer.h>
#include <omni/isaac/utils/ScopedCudaDevice.h>

#include <OgnROS2PublishImageDatabase.h>

extern "C" void textureFloatCopyToRawBuffer(cudaTextureObject_t, uint8_t*, uint32_t, uint32_t, cudaStream_t);

class OgnROS2PublishImage : public Ros2Node
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS2PublishImageDatabase::sInternalState<OgnROS2PublishImage>(nodeObj);
    // }

    static bool compute(OgnROS2PublishImageDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishImage>();
        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            return false;
        }

        // Publisher was not valid, create a new one
        if (!state.mPublisher)
        {
            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();

            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);

            if (!validateTopic(fullTopicName))
            {
                return false;
            }

            state.mPublisher =
                state.mNodeHandle->create_publisher<sensor_msgs::msg::Image>(fullTopicName, db.inputs.queueSize());

            state.mFrameId = db.inputs.frameId();

            return true;
        }

        // Setup ROS Image Message
        sensor_msgs::msg::Image& msg = state.msg;
        msg.header.frame_id = state.mFrameId;

        if (db.inputs.timeStamp() >= 0.0)
        {
            msg.header.stamp = rclcpp::Time(int64_t(db.inputs.timeStamp() * 1e9));
        }
        else
        {
            db.logWarning("Timestamp is invalid. Timestamp will be neglected for all published ROS Image messages");
            return false;
        }

        msg.width = db.inputs.width();
        msg.height = db.inputs.height();
        if (msg.width == 0 || msg.height == 0)
        {
            db.logError("Width %d or height %d is not valid", msg.width, msg.height);
            return false;
        }

        msg.encoding = db.tokenToString(db.inputs.encoding());

        int channels = 0;
        int bitDepth = 0;
        try
        {
            channels = sensor_msgs::image_encodings::numChannels(msg.encoding);
            bitDepth = sensor_msgs::image_encodings::bitDepth(msg.encoding);
        }
        catch (std::exception& e)
        {
            db.logError("%s", e.what());
            return false;
        }
        int byteDepth = bitDepth / 8;

        msg.step = msg.width * channels * byteDepth;

        size_t totalBytes = msg.step * msg.height;
        msg.data.resize(totalBytes);

        if (db.inputs.cudaDeviceIndex() == -1)
        {
            if (db.inputs.dataPtr() != 0 && totalBytes == db.inputs.bufferSize())
            {
                // Data is on host as ptr, buffer size matches
                memcpy(&msg.data[0], reinterpret_cast<void*>(db.inputs.dataPtr()), totalBytes);
            }
            else if (db.inputs.dataPtr() == 0 && totalBytes == db.inputs.data.size())
            {
                // data is on host as ogn data, copy from cpu
                memcpy(&msg.data[0], reinterpret_cast<const uint8_t*>(db.inputs.data.cpu().data()), totalBytes);
            }
            else
            {
                db.logError(
                    "image format with bit depth %d and expected size %d bytes does not match input buffer Size of %d bytes",
                    bitDepth, totalBytes, db.inputs.bufferSize());
                db.logError("dataPtr null and expected size %d bytes does not match input data Size of %d bytes",
                            totalBytes, db.inputs.data.size());
                return false;
            }
        }
        else
        {
            omni::isaac::utils::ScopedDevice(db.inputs.cudaDeviceIndex());

            if (db.inputs.bufferSize() == 0)
            {
                omni::isaac::utils::ScopedCudaTextureObject srcTexObj(
                    reinterpret_cast<cudaMipmappedArray_t>(db.inputs.dataPtr()), 0);
                switch (static_cast<carb::graphics::Format>(db.inputs.format()))
                {
                case carb::graphics::Format::eR32_SFLOAT:
                    if (db.inputs.width() * db.inputs.height() * sizeof(float) != totalBytes)
                    {
                        CARB_LOG_ERROR("totalBytes doesn't match eR32_SFLOAT %d %d",
                                       db.inputs.width() * db.inputs.height() * sizeof(float), totalBytes);
                    }
                    else
                    {
                        state.mBuffer.setDevice(db.inputs.cudaDeviceIndex());
                        state.mBuffer.resize(db.inputs.width() * db.inputs.height() * sizeof(float));
                        textureFloatCopyToRawBuffer(srcTexObj, state.mBuffer.data(), msg.width, msg.height, 0);
                        CUDA_CHECK(cudaGetLastError());
                        auto src = reinterpret_cast<void*>(state.mBuffer.data());
                        CUDA_CHECK(cudaMemcpy(&msg.data[0], src, totalBytes, cudaMemcpyDeviceToHost));
                    }
                    break;

                default:
                    CARB_LOG_ERROR("SdRenderVarToRawArray : input texture format (%d) is not supported.",
                                   static_cast<int>(db.inputs.format()));
                    return false;
                }
            }
            else
            {
                CUDA_CHECK(cudaMemcpy(&msg.data[0], reinterpret_cast<void*>(db.inputs.dataPtr()),
                                      db.inputs.bufferSize(), cudaMemcpyDeviceToHost));
            }
        }

        state.mPublisher->publish(msg);

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishImageDatabase::sInternalState<OgnROS2PublishImage>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<rclcpp::Publisher<sensor_msgs::msg::Image>> mPublisher = nullptr;

    std::string mFrameId = "sim_camera";
    sensor_msgs::msg::Image msg;
    omni::isaac::utils::DeviceBuffer mBuffer;
};

REGISTER_OGN_NODE()
