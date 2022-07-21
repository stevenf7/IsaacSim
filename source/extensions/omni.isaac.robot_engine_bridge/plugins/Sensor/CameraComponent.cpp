// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "CameraComponent.h"

#include "../Utils/IsaacConversions.h"
#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/cuda/CudaRuntime.h>

#include <boost/algorithm/string.hpp>
#include <omni/kit/KitUtils.h>
#include <omni/kit/ViewportWindowUtils.h>

#include <algorithm>
#include <cuda.h>
namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

CameraComponent::CameraComponent(utils::ViewportManager* viewportManager) : IsaacComponent()
{

    mViewportManager = viewportManager;

    mSyntheticDataInterface = mcarb::getCachedInterface<omni::syntheticdata::SyntheticData>();
    if (!mSyntheticDataInterface)
    {
        CARB_LOG_ERROR("Failed to acquire carb::sensors::syntheticdata::SyntheticData interface");
        return;
    }
}

CameraComponent::~CameraComponent()
{
    // Destroy all sensors
    onStop();
}

void CameraComponent::tick()
{
    CARB_PROFILE_ZONE(0, "CameraComponent Tick");

    if (!mCameraSensor)
    {
        return;
    }

    if (mSkipFirstFrame)
    {
        mSkipFirstFrame = false;
        return;
    }

    float focalLength;
    pxr::GfVec2f clipRange;
    float horizontalAperture, verticalAperture;

    mCameraPrim.GetFocalLengthAttr().Get(&focalLength);
    mCameraPrim.GetClippingRangeAttr().Get(&clipRange);
    mCameraPrim.GetHorizontalApertureAttr().Get(&horizontalAperture);
    mCameraPrim.GetVerticalApertureAttr().Get(&verticalAperture);

    if (mEnableRgb)
    {
        CARB_PROFILE_ZONE(0, "RGB");


        const carb::sensors::SensorInfo& rgbInfo = mCameraSensor->getSensorInfo(carb::sensors::SensorType::eRgb);

        // Publish rgb image
        IsaacMessage<isaac_message::Image> imageMessage;
        auto imageProto = imageMessage.initProto();
        imageProto.setElementType(ElementType::UINT8);
        imageProto.setRows(rgbInfo.tex.height);
        imageProto.setCols(rgbInfo.tex.width);
        imageProto.setChannels(3);
        imageProto.setDataBufferIndex(0);

        const size_t bufferSize = rgbInfo.tex.width * rgbInfo.tex.height * 3;
        mRgbBuffers[0]->resize(bufferSize);

        if (mCameraSensor->getRGB(mRgbBuffers[0]->data(), true))
        {
            publish(mRgbOutputComponent, mRgbChannelName, imageMessage, mRgbBuffers);
            publishIntrinsics(
                mRgbOutputComponent, mRgbChannelName, rgbInfo, focalLength, horizontalAperture, verticalAperture);
        }
    }


    if (mEnableDepth)
    {
        CARB_PROFILE_ZONE(0, "Depth");


        const carb::sensors::SensorInfo& depthInfo =
            mCameraSensor->getSensorInfo(carb::sensors::SensorType::eDistanceToImagePlane);

        // Publish depth image
        IsaacMessage<isaac_message::Image> imageMessage;
        auto imageProto = imageMessage.initProto();
        imageProto.setElementType(ElementType::FLOAT32);
        imageProto.setRows(depthInfo.tex.height);
        imageProto.setCols(depthInfo.tex.width);
        imageProto.setChannels(1);
        imageProto.setDataBufferIndex(0);

        mDepthBuffers[0]->resize(depthInfo.tex.width * depthInfo.tex.height * sizeof(float));
        if (mCameraSensor->getDepth(mDepthBuffers[0]->data(), true))
        {
            publish(mDepthOutputComponent, mDepthChannelName, imageMessage, mDepthBuffers);
            publishIntrinsics(
                mDepthOutputComponent, mDepthChannelName, depthInfo, focalLength, horizontalAperture, verticalAperture);
        }
    }

    // TODO can we turn on mSegmentationSensor && mSemanticSensor separately
    if (mEnableSegmentation)
    {
        CARB_PROFILE_ZONE(0, "Segmentation");

        const carb::sensors::SensorInfo& segmentationInfo =
            mCameraSensor->getSensorInfo(carb::sensors::SensorType::eInstanceSegmentation);
        const carb::sensors::SensorInfo& semanticInfo =
            mCameraSensor->getSensorInfo(carb::sensors::SensorType::eSemanticSegmentation);
        // These images should be of the same resolution
        if (segmentationInfo.tex.height != semanticInfo.tex.height || segmentationInfo.tex.width != semanticInfo.tex.width)
        {
            CARB_LOG_ERROR("The segmentation and semantic textures have different resolutions");
            return;
        }

        // Create the instance image
        IsaacMessage<isaac_message::Image> instanceMessage;
        auto instanceImageProto = instanceMessage.initProto();
        instanceImageProto.setElementType(ElementType::UINT16);
        instanceImageProto.setRows(segmentationInfo.tex.height);
        instanceImageProto.setCols(segmentationInfo.tex.width);
        instanceImageProto.setChannels(1);
        instanceImageProto.setDataBufferIndex(0);

        // Create the semantic image
        IsaacMessage<isaac_message::Image> semanticMessage;
        auto semanticImageProto = semanticMessage.initProto();
        semanticImageProto.setElementType(ElementType::UINT8);
        semanticImageProto.setRows(semanticInfo.tex.height);
        semanticImageProto.setCols(semanticInfo.tex.width);
        semanticImageProto.setChannels(1);
        semanticImageProto.setDataBufferIndex(0);


        // TODO : The instance and semantic segmentation should be refactored into one method
        // Instance segmentation
        {
            // Message buffers
            const size_t bufferSize = segmentationInfo.tex.width * segmentationInfo.tex.height * sizeof(uint16_t);
            mSegmentationBuffers[0]->resize(bufferSize);


            if (mCameraSensor->getInstance(mSegmentationBuffers[0]->data(), true, true))
            {
                publish(mSegmentationOutputComponent, mSegmentationChannelName + "_instance", instanceMessage,
                        mSegmentationBuffers);
            }
        }

        // Semantic segmentation
        {
            const size_t semanticBufferSize = semanticInfo.tex.width * semanticInfo.tex.height * sizeof(uint8_t);
            std::vector<std::unique_ptr<IsaacBuffer>> buffers(1);
            mSemanticBuffers[0]->resize(semanticBufferSize);

            if (mCameraSensor->getSemantic(mSemanticBuffers[0]->data(), true, true))
            {
                publish(mSegmentationOutputComponent, mSegmentationChannelName + "_class", semanticMessage,
                        mSemanticBuffers);
            }
        }

        // Class labels
        {
            std::map<uint8_t, std::string> labelMap;
            if (!mCameraSensor->getLabels(labelMap))
            {
                return;
            }

            IsaacMessage<isaac_message::Labels> labelsMessage;
            auto labelsProto = labelsMessage.initProto();
            auto semanticLabelsProto = labelsProto.initLabels(labelMap.size());
            int index = 0;
            for (std::map<uint8_t, std::string>::iterator it = labelMap.begin(); it != labelMap.end(); ++it)
            {
                semanticLabelsProto[index].setIndex(it->first);
                semanticLabelsProto[index].setName(it->second);
                index++;
            }
            std::vector<std::unique_ptr<IsaacBuffer>> buffers;
            publish(mSegmentationOutputComponent, mSegmentationChannelName + "_labels", labelsMessage, buffers);
        }

        // Camera intrinsics
        publishIntrinsics(mSegmentationOutputComponent, mSegmentationChannelName, segmentationInfo, focalLength,
                          horizontalAperture, verticalAperture);
    }

    if (mEnableBoundingBox2D)
    {
        CARB_PROFILE_ZONE(0, "BBox");

        size_t numBoundingBoxes = 0;
        carb::sensors::BoundingBox2DValues* bboxData = nullptr;
        if (!mCameraSensor->getBBox2D(bboxData, numBoundingBoxes))
        {
            return;
        }


        carb::sensors::BoundingBox2DValues* data = bboxData;
        int numValidBoundingBoxes = 0;
        for (size_t i = 0; i < numBoundingBoxes; i++)
        {
            std::string semanticLabel(mSyntheticDataInterface->getSemanticDataFromId(data->semanticId));
            // Filter bounding boxes based on semantic data
            if (mBoundingBox2DClassList.size() > 0)
            {
                if (std::find(mBoundingBox2DClassList.begin(), mBoundingBox2DClassList.end(), semanticLabel) ==
                    mBoundingBox2DClassList.end())
                {
                    data++;
                    continue;
                }
            }
            data++;
            numValidBoundingBoxes++;
        }
        if (numValidBoundingBoxes > 0)
        {
            // Create the message
            carb::sensors::BoundingBox2DValues* data = bboxData;
            IsaacMessage<isaac_message::Detections2> detectionMessage;
            auto detectionMessageProto = detectionMessage.initProto();
            auto boundingBoxesProto = detectionMessageProto.initBoundingBoxes(numValidBoundingBoxes);
            auto predictionsProto = detectionMessageProto.initPredictions(numValidBoundingBoxes);

            int boundingBoxId = 0;
            for (size_t i = 0; i < numBoundingBoxes; i++)
            {
                std::string semanticLabel(mSyntheticDataInterface->getSemanticDataFromId(data->semanticId));
                // Filter bounding boxes based on semantic data
                if (mBoundingBox2DClassList.size() > 0)
                {
                    if (std::find(mBoundingBox2DClassList.begin(), mBoundingBox2DClassList.end(), semanticLabel) ==
                        mBoundingBox2DClassList.end())
                    {
                        data++;
                        continue;
                    }
                }
                // CARB_LOG_ERROR("Data %d: %s %d, %d, %d, %d, %d, %d", boundingBoxId + 1, semanticLabel.c_str(),
                // data->instanceId, data->semanticId, data->x_min, data->y_min, data->x_max, data->y_max);
                auto minProto = boundingBoxesProto[boundingBoxId].initMin();
                auto maxProto = boundingBoxesProto[boundingBoxId].initMax();
                minProto.setX(data->y_min);
                minProto.setY(data->x_min);
                maxProto.setX(data->y_max);
                maxProto.setY(data->x_max);
                predictionsProto[boundingBoxId].setLabel(semanticLabel);
                predictionsProto[boundingBoxId].setConfidence(1.0);
                data++;
                boundingBoxId++;
            }
            std::vector<std::unique_ptr<IsaacBuffer>> buffers;
            publish(mBoundingBox2DOutputComponent, mBoundingBox2DChannelName, detectionMessage, buffers);
        }
    }

    if (mEnableBoundingBox3D)
    {
        CARB_PROFILE_ZONE(0, "BBox3D");
        size_t numBoundingBoxes = 0;
        carb::sensors::BoundingBox3DValues* bboxData = nullptr;

        if (!mCameraSensor->getBBox3D(bboxData, numBoundingBoxes))
        {
            return;
        }


        int numValidBoundingBoxes = 0;

        carb::sensors::BoundingBox3DValues* data = bboxData;

        for (size_t i = 0; i < numBoundingBoxes; i++)
        {
            std::string semanticLabel(mSyntheticDataInterface->getSemanticDataFromId(data->semanticId));
            // Filter bounding boxes based on semantic data
            if (mBoundingBox3DClassList.size() > 0)
            {
                if (std::find(mBoundingBox3DClassList.begin(), mBoundingBox3DClassList.end(), semanticLabel) ==
                    mBoundingBox3DClassList.end())
                {
                    data++;
                    continue;
                }
            }
            data++;
            numValidBoundingBoxes++;
        }
        if (numValidBoundingBoxes > 0)
        {
            // Create the message
            carb::sensors::BoundingBox3DValues* data = bboxData;
            IsaacMessage<isaac_message::Detections3> detectionMessage;
            auto detectionMessageProto = detectionMessage.initProto();
            auto boundingBoxesProto = detectionMessageProto.initBoundingBoxes(numValidBoundingBoxes);
            auto predictionsProto = detectionMessageProto.initPredictions(numValidBoundingBoxes);
            auto posesProto = detectionMessageProto.initPoses(numValidBoundingBoxes);

            int boundingBoxId = 0;
            for (size_t i = 0; i < numBoundingBoxes; i++)
            {
                std::string semanticLabel(mSyntheticDataInterface->getSemanticDataFromId(data->semanticId));
                // Filter bounding boxes based on semantic data
                if (mBoundingBox3DClassList.size() > 0)
                {
                    if (std::find(mBoundingBox3DClassList.begin(), mBoundingBox3DClassList.end(), semanticLabel) ==
                        mBoundingBox3DClassList.end())
                    {
                        data++;
                        continue;
                    }
                }

                // Get pose in world space
                auto floatTransform = data->transform;
                std::vector<std::vector<float>> transformMatrix(4, std::vector<float>(4, 0));
                for (int row = 0; row < 4; row++)
                    for (int col = 0; col < 4; col++)
                        transformMatrix[row][col] = floatTransform[row][col];
                pxr::GfTransform gfTransform = pxr::GfTransform(pxr::GfMatrix4d(transformMatrix));
                auto isaacTranslationProto = posesProto[boundingBoxId].initTranslation();
                auto isaacRotationProto = posesProto[boundingBoxId].initRotation();
                pxr::GfVec3d translationValue = gfTransform.GetTranslation();
                pxr::GfQuatd rotationValue = gfTransform.GetRotation().GetQuat();
                pxr::GfVec3d scaleValue = gfTransform.GetScale() * mUnitScale;
                toVector3dProto(translationValue * mUnitScale, isaacTranslationProto);
                toSO3dProto(rotationValue, isaacRotationProto);
                // Get min and max values of 3D bounding box in local space
                auto minProto = boundingBoxesProto[boundingBoxId].initMin();
                auto maxProto = boundingBoxesProto[boundingBoxId].initMax();
                minProto.setX(data->x_min * scaleValue[0]);
                minProto.setY(data->y_min * scaleValue[1]);
                minProto.setZ(data->z_min * scaleValue[2]);
                maxProto.setX(data->x_max * scaleValue[0]);
                maxProto.setY(data->y_max * scaleValue[1]);
                maxProto.setZ(data->z_max * scaleValue[2]);
                predictionsProto[boundingBoxId].setLabel(semanticLabel);
                predictionsProto[boundingBoxId].setConfidence(1.0);
                // CARB_LOG_ERROR("Translation: %f, %f, %f", isaacTranslationProto.getX(),
                // isaacTranslationProto.getY(),
                //                isaacTranslationProto.getZ());
                // CARB_LOG_ERROR("Scale: %f, %f, %f", scaleValue[0], scaleValue[1], scaleValue[2]);
                // std::string primUri(mSyntheticDataInterface->getUriFromInstanceId(data->instanceId));
                // CARB_LOG_ERROR("Data %d: %s, %s, %d, %d, %f, %f, %f, %f, %f, %f", boundingBoxId + 1,
                // primUri.c_str(),
                //                semanticLabel.c_str(), data->instanceId, data->semanticId, data->x_min,
                //                data->y_min, data->z_min, data->x_max, data->y_max, data->z_max);
                data++;
                boundingBoxId++;
            }
            std::vector<std::unique_ptr<IsaacBuffer>> buffers;
            publish(mBoundingBox3DOutputComponent, mBoundingBox3DChannelName, detectionMessage, buffers);
        }
    }
}
void CameraComponent::onStart()
{
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
    mSkipFirstFrame = true;
    mCameraSensor = std::make_unique<utils::camera_sensor::CameraSensor>(mViewportManager);
    onComponentChange();
}

void CameraComponent::onStop()
{
    mCameraSensor.reset();
}

void CameraComponent::onComponentChange()
{
    IsaacComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEngineCamera& typedPrim = (pxr::RobotEngineBridgeSchemaRobotEngineCamera)mPrim;

    isaac::utils::safeGetAttribute(typedPrim.GetResolutionAttr(), mResolution);

    // RGB attributes
    isaac::utils::safeGetAttribute(typedPrim.GetRgbOutputComponentAttr(), mRgbOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetRgbOutputChannelAttr(), mRgbChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetRgbEnabledAttr(), mEnableRgb);

    // Depth attributes
    isaac::utils::safeGetAttribute(typedPrim.GetDepthOutputComponentAttr(), mDepthOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetDepthOutputChannelAttr(), mDepthChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetDepthEnabledAttr(), mEnableDepth);

    // Segmentation attributes
    isaac::utils::safeGetAttribute(typedPrim.GetSegmentationOutputComponentAttr(), mSegmentationOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetSegmentationOutputChannelAttr(), mSegmentationChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetSegmentationEnabledAttr(), mEnableSegmentation);

    // Bounding Box attributes
    std::string filterClassList;
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DOutputComponentAttr(), mBoundingBox2DOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DOutputChannelAttr(), mBoundingBox2DChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DClassListAttr(), filterClassList);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DEnabledAttr(), mEnableBoundingBox2D);

    // Bounding Box 3D attributes
    std::string filterClassList3D;
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox3DOutputComponentAttr(), mBoundingBox3DOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox3DOutputChannelAttr(), mBoundingBox3DChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox3DClassListAttr(), filterClassList3D);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox3DEnabledAttr(), mEnableBoundingBox3D);

    mBoundingBox2DClassList.clear();
    if (filterClassList != "")
        boost::split(mBoundingBox2DClassList, filterClassList, [](char c) { return c == ','; });

    mBoundingBox3DClassList.clear();
    if (filterClassList3D != "")
        boost::split(mBoundingBox3DClassList, filterClassList3D, [](char c) { return c == ','; });

    mCameraPath = pxr::SdfPath("/OmniverseKit_Persp");
    pxr::SdfPathVector targets;
    typedPrim.GetCameraPrimRel().GetTargets(&targets);
    if (targets.size() > 0)
    {
        mCameraPath = targets[0];
    }
    mCameraPrim = pxr::UsdGeomCamera(mStage->GetPrimAtPath(mCameraPath));

    if (!mCameraPrim)
    {
        CARB_LOG_ERROR("%s is not a USD Camera", mCameraPath.GetString().c_str());
        mCameraSensor.reset();
        return;
    }
    mCameraSensor->updateViewportSettings(mCameraPath, mPrim.GetPath(), mResolution, mDoStart, mEnableRgb, mEnableDepth,
                                          false, mEnableSegmentation, mEnableBoundingBox2D, mEnableBoundingBox3D);

    mRgbBuffers.resize(1);
    mRgbBuffers[0] = std::make_unique<IsaacDeviceBuffer>();
    mDepthBuffers.resize(1);
    mDepthBuffers[0] = std::make_unique<IsaacDeviceBuffer>();
    mSegmentationBuffers.resize(1);
    mSegmentationBuffers[0] = std::make_unique<IsaacDeviceBuffer>();
    mSemanticBuffers.resize(1);
    mSemanticBuffers[0] = std::make_unique<IsaacDeviceBuffer>();
}

void CameraComponent::publishIntrinsics(std::string outputComponent,
                                        std::string channelName,
                                        const carb::sensors::SensorInfo& info,
                                        float focalLength,
                                        float horizontalAperture,
                                        float verticalAperture)
{
    IsaacMessage<isaac_message::CameraIntrinsics> intrinsicsMessage;
    auto intrinsicsProto = intrinsicsMessage.initProto();

    auto pinhole = intrinsicsProto.initPinhole();
    pinhole.setRows(info.tex.height);
    pinhole.setCols(info.tex.width);
    auto focal = pinhole.initFocal();
    // We have to ignore the vertical aperture number because our pixels are square
    // Compute it directly from the image size and horizontal aperture
    verticalAperture = static_cast<float>(info.tex.height) / static_cast<float>(info.tex.width) * horizontalAperture;
    focal.setX(info.tex.height * focalLength / verticalAperture);
    focal.setY(info.tex.width * focalLength / horizontalAperture);
    auto center = pinhole.initCenter();
    center.setX(info.tex.height * 0.5f);
    center.setY(info.tex.width * 0.5f);

    std::vector<std::unique_ptr<IsaacBuffer>> dummyBuffers;

    publish(outputComponent, channelName + "_intrinsics", intrinsicsMessage, dummyBuffers);
}
}
}
}
