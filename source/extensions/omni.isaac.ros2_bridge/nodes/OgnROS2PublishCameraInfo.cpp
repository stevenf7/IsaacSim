// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on


#include <include/Ros2Node.h>

#include <OgnROS2PublishCameraInfoDatabase.h>


class OgnROS2PublishCameraInfo : public Ros2Node
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        // auto& state = OgnROS2PublishCameraInfoDatabase::sInternalState<OgnROS2PublishCameraInfo>(nodeObj);
    }

    static bool compute(OgnROS2PublishCameraInfoDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishCameraInfo>();
        // std::cout << "Call publish method..." << std::endl;

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
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);
            if (!state.mFactory->validateTopic(fullTopicName))
            {
                return false;
            }
            state.mMessage = state.mFactory->CreateCameraInfoMessage();
            state.mPublisher =
                state.mFactory->CreatePublisher(state.mNodeHandle.get(), fullTopicName.c_str(),
                                                state.mMessage->getTypeSupportHandle(), db.inputs.queueSize());

            return true;
        }

        state.mFrameId = db.inputs.frameId();

        state.publishCameraInfo(db);

        return true;
    }

    void publishCameraInfo(OgnROS2PublishCameraInfoDatabase& db)
    {
        auto& state = db.internalState<OgnROS2PublishCameraInfo>();

        state.mMessage->fillHeader(db.inputs.timeStamp(), state.mFrameId);

        auto& height = db.inputs.height();
        auto& width = db.inputs.width();
        state.mMessage->fillHeightWidth(height, width);
        // ROS image: conventions
        // origin of frame should be optical center of camera
        // +x should point to the right in the image
        // +y should point down in the image
        // +z should point into the plane of the image

        float fx, fy, cy, cx;

        fx = width * db.inputs.focalLength() / db.inputs.horizontalAperture();
        fy = height * db.inputs.focalLength() / db.inputs.verticalAperture();
        cx = width * 0.5f;
        cy = height * 0.5f;
        double k_arr[] = { fx, 0, cx, 0, fy, cy, 0, 0, 1 };
        state.mMessage->fillIntrisicArray(k_arr, 9);

        double p_arr[] = { fx, 0, cx, db.inputs.stereoOffset()[0], 0, fy, cy, db.inputs.stereoOffset()[1], 0, 0, 1, 0 };
        state.mMessage->fillProjectionArray(p_arr, 12);
        std::string physicalDistortion = db.tokenToString(db.inputs.physicalDistortionModel());

        if (physicalDistortion.length() > 0)
        {
            std::vector<double> coeff;
            for (size_t i = 0; i < db.inputs.physicalDistortionCoefficients().size(); i++)
            {
                coeff.push_back(db.inputs.physicalDistortionCoefficients()[i]);
            }
            state.mMessage->fillDistortionModel(coeff, physicalDistortion);
        }
        else
        {
            // TODO: Handle fisheye coeffieicents?
            std::vector<double> empty;
            state.mMessage->fillDistortionModel(empty, db.tokenToString(db.inputs.projectionType()));
        }
        state.mPublisher.get()->publish(state.mMessage->ptr());
    }

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2PublishCameraInfoDatabase::sInternalState<OgnROS2PublishCameraInfo>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }


private:
    std::shared_ptr<Ros2Publisher> mPublisher = nullptr;
    std::shared_ptr<Ros2CameraInfoMessage> mMessage = nullptr;

    std::string mFrameId = "sim_camera";
};

REGISTER_OGN_NODE()
