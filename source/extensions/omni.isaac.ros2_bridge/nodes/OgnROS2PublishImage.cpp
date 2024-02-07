// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/graphics/GraphicsTypes.h>
#include <carb/profiler/Profile.h>

#include <include/Ros2Node.h>
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
            CARB_PROFILE_ZONE(0, "setup publisher");
            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();

            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);

            if (!state.mFactory->validateTopic(fullTopicName))
            {
                return false;
            }

            state.mMessage = state.mFactory->CreateImageMessage();
            state.mPublisher =
                state.mFactory->CreatePublisher(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());
            state.mFrameId = db.inputs.frameId();

            return true;
        }

        return state.publishImage(db);
    }


    bool publishImage(OgnROS2PublishImageDatabase& db)
    {
        CARB_PROFILE_ZONE(1, "publish image function");
        auto& state = db.internalState<OgnROS2PublishImage>();
        // Check if subscription count is 0
        if (!state.mPublisher.get()->get_subscription_count())
        {
            return false;
        }

        auto zoneID = CARB_PROFILE_BEGIN(5, "Generate message header and buffer");
        state.mMessage = state.mFactory->CreateImageMessage();

        state.mMessage->fillHeader(db.inputs.timeStamp(), state.mFrameId);

        if (db.inputs.width() == 0 || db.inputs.height() == 0)
        {
            db.logError("Width %d or height %d is not valid", db.inputs.width(), db.inputs.height());
            return false;
        }

        std::string encoding = db.tokenToString(db.inputs.encoding());
        state.mMessage->generateBuffer(db.inputs.height(), db.inputs.width(), encoding);
        size_t totalBytes = state.mMessage->getTotalBytes();
        void* dataPtr = state.mMessage->getDataPtr();
        CARB_PROFILE_END(zoneID);

        if (db.inputs.cudaDeviceIndex() == -1)
        {
            CARB_PROFILE_ZONE(2, "Data on host");
            if (db.inputs.dataPtr() != 0 && totalBytes == db.inputs.bufferSize())
            {
                // Data is on host as ptr, buffer size matches
                memcpy(dataPtr, reinterpret_cast<void*>(db.inputs.dataPtr()), totalBytes);
            }
            else if (db.inputs.dataPtr() == 0 && totalBytes == db.inputs.data.size())
            {
                // data is on host as ogn data, copy from cpu
                memcpy(dataPtr, reinterpret_cast<const uint8_t*>(db.inputs.data.cpu().data()), totalBytes);
            }
            else
            {
                db.logError("image format and expected size %d bytes does not match input buffer Size of %d bytes",
                            totalBytes, db.inputs.bufferSize());
                db.logError("dataPtr null and expected size %d bytes does not match input data Size of %d bytes",
                            totalBytes, db.inputs.data.size());
                return false;
            }
        }
        else
        {
            CARB_PROFILE_ZONE(3, "data on Cuda device");
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
                        CARB_LOG_ERROR("totalBytes doesn't match eR32_SFLOAT %zu %zu",
                                       db.inputs.width() * db.inputs.height() * sizeof(float), totalBytes);
                    }
                    else
                    {
                        state.mBuffer.setDevice(db.inputs.cudaDeviceIndex());
                        state.mBuffer.resize(db.inputs.width() * db.inputs.height() * sizeof(float));
                        textureFloatCopyToRawBuffer(
                            srcTexObj, state.mBuffer.data(), db.inputs.width(), db.inputs.height(), 0);
                        CUDA_CHECK(cudaGetLastError());
                        auto src = reinterpret_cast<void*>(state.mBuffer.data());
                        CUDA_CHECK(cudaMemcpy(dataPtr, src, totalBytes, cudaMemcpyDeviceToHost));
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
                CUDA_CHECK(cudaMemcpy(dataPtr, reinterpret_cast<void*>(db.inputs.dataPtr()), db.inputs.bufferSize(),
                                      cudaMemcpyDeviceToHost));
            }
        }
        CARB_PROFILE_ZONE(4, "image publisher publish");
        state.mPublisher.get()->publish(state.mMessage->ptr());

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
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2ImageMessage> mMessage = nullptr;

    std::string mFrameId = "sim_camera";
    omni::isaac::utils::DeviceBuffer mBuffer;
};

REGISTER_OGN_NODE()
