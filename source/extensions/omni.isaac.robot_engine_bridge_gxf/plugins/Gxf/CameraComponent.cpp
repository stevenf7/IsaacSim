// Copyright (c) 2021, NVIDIA CORPORATION. All rights reserved.
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
#include <cstdint>
#include <cuda.h>
namespace omni
{
namespace isaac
{
namespace robot_engine_bridge_gxf
{

extern "C" void rgbaToRgb(uint8_t* dest, const uint8_t* src, int width, int height, int srcStride);
extern "C" void uint32ToUint16(uint16_t* dest, const uint32_t* src, int width, int height, int srcStride);
extern "C" void uint32ToUint8(uint8_t* dest, const uint32_t* src, int width, int height, int srcStride);

CameraComponent::CameraComponent(utils::ViewportManager* viewportManager) : GxfComponent()
{

    mViewportManager = viewportManager;
    mFramework = carb::getFramework();
    if (!mFramework)
    {
        CARB_LOG_ERROR("*** Failed to get Carbonite framework\n");
        return;
    }

    mViewportInterface = mFramework->acquireInterface<omni::kit::IViewport>();
    if (!mViewportInterface)
    {
        CARB_LOG_ERROR("Failed to acquire omni::kit::IViewport interface");
        return;
    }

    mSyntheticDataInterface = mFramework->acquireInterface<omni::syntheticdata::SyntheticData>();
    if (!mSyntheticDataInterface)
    {
        CARB_LOG_ERROR("Failed to acquire carb::sensors::syntheticdata::SyntheticData interface");
        return;
    }

    mSensorsInterface = mFramework->acquireInterface<carb::sensors::Sensors>();
    if (!mSensorsInterface)
    {
        CARB_LOG_ERROR("Failed to acquire carb::sensors::Sensors interface");
        return;
    }
}

CameraComponent::~CameraComponent()
{
    // Destroy all sensors
    onStop();

    mFramework->releaseInterface(mSyntheticDataInterface);
    mFramework->releaseInterface(mSensorsInterface);
}

void CameraComponent::tick()
{
    CARB_PROFILE_ZONE(0, "CameraComponent Tick");

    if (mViewportWindow == nullptr)
        return;

    if (mSkipFirstFrame)
    {
        mSkipFirstFrame = false;
        return;
    }

    if (!mRgbSensor && !mDepthSensor && !mSegmentationSensor && !mSemanticSensor && !mBoundingBox2DSensor)
    {
        // Re-initialize sensors if not initialized yet
        if (mEnableRgb && !mSyntheticDataInterface->isSensorInitialized(mRgbSensor))
            mRgbSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eRgb, mViewportWindow);
        if (mEnableDepth && !mSyntheticDataInterface->isSensorInitialized(mDepthSensor))
            mDepthSensor =
                mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eDepthLinear, mViewportWindow);
        if (mEnableSegmentation && !mSyntheticDataInterface->isSensorInitialized(mSegmentationSensor))
            mSegmentationSensor =
                mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eInstanceSegmentation, mViewportWindow);
        if (mEnableSegmentation && !mSyntheticDataInterface->isSensorInitialized(mSemanticSensor))
            mSemanticSensor =
                mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eSemanticSegmentation, mViewportWindow);
        if (mEnableBoundingBox2D && !mSyntheticDataInterface->isSensorInitialized(mBoundingBox2DSensor))
            mBoundingBox2DSensor =
                mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eBoundingBox2DTight, mViewportWindow);
        if (mEnableBoundingBox3D && !mSyntheticDataInterface->isSensorInitialized(mBoundingBox3DSensor))
            mBoundingBox3DSensor =
                mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eBoundingBox3D, mViewportWindow);
        return;
    }

    const char* cameraPath = mViewportWindow->getActiveCamera();
    if (!cameraPath)
        return;

    pxr::SdfPath path(cameraPath);
    pxr::UsdPrim prim = mStage->GetPrimAtPath(path);
    auto maybePoseUid = mPoseTreeMap->findFrame(cameraPath);
    if (!maybePoseUid)
    {
        CARB_LOG_WARN("Cannot find pose uid for camera %s", cameraPath);
        return;
    }
    const nvidia::isaac::PoseTree::frame_t poseUid = maybePoseUid.value();

    pxr::UsdGeomCamera cameraPrim(prim);

    float focalLength;
    pxr::GfVec2f clipRange;
    float horizontalAperture, verticalAperture;
    float fthetaPolyA, fthetaPolyB, fthetaPolyC, fthetaPolyD, fthetaPolyE;
    pxr::TfToken projectionType = pxr::TfToken("pinhole");

    cameraPrim.GetFocalLengthAttr().Get(&focalLength);
    cameraPrim.GetClippingRangeAttr().Get(&clipRange);
    cameraPrim.GetHorizontalApertureAttr().Get(&horizontalAperture);
    cameraPrim.GetVerticalApertureAttr().Get(&verticalAperture);

    prim.GetAttribute(pxr::TfToken("cameraProjectionType")).Get(&projectionType);
    prim.GetAttribute(pxr::TfToken("fthetaPolyA")).Get(&fthetaPolyA);
    prim.GetAttribute(pxr::TfToken("fthetaPolyB")).Get(&fthetaPolyB);
    prim.GetAttribute(pxr::TfToken("fthetaPolyC")).Get(&fthetaPolyC);
    prim.GetAttribute(pxr::TfToken("fthetaPolyD")).Get(&fthetaPolyD);
    prim.GetAttribute(pxr::TfToken("fthetaPolyE")).Get(&fthetaPolyE);
    const std::array<double, ::isaac::geometry::CameraDistortionInfo::kMaxNumCoefficients> distortionCoefficients{
        fthetaPolyA, fthetaPolyB, fthetaPolyC, fthetaPolyD, fthetaPolyE
    };

    if (mRgbSensor)
    {
        CARB_PROFILE_ZONE(0, "RGB");

        mRgbSensorData = mSyntheticDataInterface->getSensorDeviceData(mRgbSensor);
        const carb::sensors::SensorInfo& rgbInfo = mSensorsInterface->getSensorInfo(mRgbSensor);

        const int rows = rgbInfo.tex.height;
        const int cols = rgbInfo.tex.width;
        if (rows == 0 || cols == 0)
        {
            CARB_LOG_ERROR("Image row/col is zero");
            return;
        }
        // Create the message. TODO: create CUDA tensor message
        auto maybe_message = nvidia::isaac::CreateCameraImageMessage<uint8_t>(mContext, mAllocator, { rows, cols, 3 });
        if (!maybe_message)
        {
            // return maybe_message.error();
            CARB_LOG_ERROR("could not create rgb image message, %d", maybe_message.error());
            return;
        }
        auto message = std::move(maybe_message.value());

        message.timestamp->acqtime = this->mTimeNanoSeconds + mComponentTimeOffsetNanoSeconds;
        message.timestamp->pubtime = ::isaac::NowCount();

        const size_t bufferSize = rows * cols * 3 * sizeof(uint8_t);
        mRgbBuffers[0]->resize(bufferSize);
        // use cuda kernel to reorganize buffer and write to final destination
        rgbaToRgb(mRgbBuffers[0]->data(), (uint8_t*)mRgbSensorData, rgbInfo.tex.width, rgbInfo.tex.height,
                  rgbInfo.tex.rowSize);
        cudaMemcpy(static_cast<byte*>(message.image_tensor_view.element_wise_begin()), mRgbBuffers[0]->data(),
                   bufferSize, cudaMemcpyDeviceToHost);

        // Set camera intrinsics value
        setIntrinsics(message.intrinsics_info, message.distortion_info, rgbInfo, focalLength, horizontalAperture,
                      verticalAperture, distortionCoefficients, projectionType);
        // Set pose frame uid
        message.pose_frame_uid->uid = poseUid;

        publish(mRgbOutputComponent, mRgbChannelName, std::move(message.entity));
    }


    if (mDepthSensor)
    {
        CARB_PROFILE_ZONE(0, "Depth");

        const carb::sensors::SensorInfo& depthInfo = mSensorsInterface->getSensorInfo(mDepthSensor);

        const int rows = depthInfo.tex.height;
        const int cols = depthInfo.tex.width;
        if (rows == 0 || cols == 0)
        {
            CARB_LOG_ERROR("Image row/col is zero");
            return;
        }
        // Create the message. TODO: create CUDA tensor message
        auto maybe_message = nvidia::isaac::CreateCameraImageMessage<float>(mContext, mAllocator, { rows, cols, 1 });
        if (!maybe_message)
        {
            // return maybe_message.error();
            CARB_LOG_ERROR("could not create depth image message, %d", maybe_message.error());
            return;
        }
        auto message = std::move(maybe_message.value());

        message.timestamp->acqtime = this->mTimeNanoSeconds + mComponentTimeOffsetNanoSeconds;
        message.timestamp->pubtime = ::isaac::NowCount();

        const size_t bufferSize = rows * cols * sizeof(float);
        mDepthBuffers[0]->resize(bufferSize);
        mDepthSensorData = mSyntheticDataInterface->getSensorDeviceData(mDepthSensor);
        CUDA_CHECK(cudaMemcpy(mDepthBuffers[0]->data(), mDepthSensorData, bufferSize, cudaMemcpyDeviceToDevice));

        cudaMemcpy(reinterpret_cast<byte*>(message.image_tensor_view.element_wise_begin()), mDepthBuffers[0]->data(),
                   bufferSize, cudaMemcpyDeviceToHost);

        // Set camera intrinsics value
        setIntrinsics(message.intrinsics_info, message.distortion_info, depthInfo, focalLength, horizontalAperture,
                      verticalAperture, distortionCoefficients, projectionType);
        // Set pose frame uid
        message.pose_frame_uid->uid = poseUid;

        publish(mDepthOutputComponent, mDepthChannelName, std::move(message.entity));
    }

    // TODO can we turn on mSegmentationSensor && mSemanticSensor separately
    if (mSegmentationSensor && mSemanticSensor)
    {
        CARB_PROFILE_ZONE(0, "Segmentation");

        mSegmentationSensorData = mSyntheticDataInterface->getSensorDeviceData(mSegmentationSensor);
        mSemanticSensorData = mSyntheticDataInterface->getSensorDeviceData(mSemanticSensor);

        const carb::sensors::SensorInfo& segmentationInfo = mSensorsInterface->getSensorInfo(mSegmentationSensor);
        const carb::sensors::SensorInfo& semanticInfo = mSensorsInterface->getSensorInfo(mSemanticSensor);
        // These images should be of the same resolution
        if (segmentationInfo.tex.height != semanticInfo.tex.height || segmentationInfo.tex.width != semanticInfo.tex.width)
        {
            CARB_LOG_ERROR("The segmentation and semantic textures have different resolutions");
            return;
        }

        const int rows = semanticInfo.tex.height;
        const int cols = semanticInfo.tex.width;
        if (rows == 0 || cols == 0)
        {
            CARB_LOG_ERROR("Image row/col is zero");
            return;
        }

        // TODO : The instance and semantic segmentation should be refactored into one method
        // Instance segmentation
        {
            const size_t bufferSize = rows * cols * sizeof(uint16_t);
            // Create the message. TODO: create CUDA tensor message
            auto maybe_message =
                nvidia::isaac::CreateCameraImageMessage<uint16_t>(mContext, mAllocator, { rows, cols, 1 });
            if (!maybe_message)
            {
                // return maybe_message.error();
                CARB_LOG_ERROR("could not create instance image message, %d", maybe_message.error());
                return;
            }
            auto message = std::move(maybe_message.value());

            message.timestamp->acqtime = this->mTimeNanoSeconds + mComponentTimeOffsetNanoSeconds;
            message.timestamp->pubtime = ::isaac::NowCount();

            mSegmentationBuffers[0]->resize(bufferSize);
            uint32ToUint16((uint16_t*)mSegmentationBuffers[0]->data(), (uint32_t*)mSegmentationSensorData, cols, rows,
                           segmentationInfo.tex.rowSize);
            cudaMemcpy(reinterpret_cast<byte*>(message.image_tensor_view.element_wise_begin()),
                       mSegmentationBuffers[0]->data(), bufferSize, cudaMemcpyDeviceToHost);

            // Set camera intrinsics value
            setIntrinsics(message.intrinsics_info, message.distortion_info, semanticInfo, focalLength,
                          horizontalAperture, verticalAperture, distortionCoefficients, projectionType);
            // Set pose frame uid
            message.pose_frame_uid->uid = poseUid;

            publish(mSegmentationOutputComponent, mSegmentationChannelName + "_instance", std::move(message.entity));
        }

        // Semantic segmentation
        {
            const size_t bufferSize = rows * cols * sizeof(uint8_t);
            // Create the message. TODO: create CUDA tensor message
            auto maybe_message =
                nvidia::isaac::CreateCameraImageMessage<uint8_t>(mContext, mAllocator, { rows, cols, 1 });
            if (!maybe_message)
            {
                // return maybe_message.error();
                CARB_LOG_ERROR("could not create class image message, %d", maybe_message.error());
                return;
            }
            auto message = std::move(maybe_message.value());

            message.timestamp->acqtime = this->mTimeNanoSeconds + mComponentTimeOffsetNanoSeconds;
            message.timestamp->pubtime = ::isaac::NowCount();

            mSemanticBuffers[0]->resize(bufferSize);
            uint32ToUint8(
                mSemanticBuffers[0]->data(), (uint32_t*)mSemanticSensorData, cols, rows, semanticInfo.tex.rowSize);
            cudaMemcpy(static_cast<byte*>(message.image_tensor_view.element_wise_begin()), mSemanticBuffers[0]->data(),
                       bufferSize, cudaMemcpyDeviceToHost);

            // Set camera intrinsics value
            setIntrinsics(message.intrinsics_info, message.distortion_info, semanticInfo, focalLength,
                          horizontalAperture, verticalAperture, distortionCoefficients, projectionType);
            // Set pose frame uid
            message.pose_frame_uid->uid = poseUid;

            publish(mSegmentationOutputComponent, mSegmentationChannelName + "_class", std::move(message.entity));
        }

        // Class labels
        {
            //            // TODO add class label map to message
            //            auto labels_message = nvidia::gxf::Entity::New(mContext);
            //            auto labels_tensor = labels_message.value().add<nvidia::gxf::Tensor>("tensor");
            //            auto labels_timestamp = labels_message.value().add<nvidia::gxf::Timestamp>("timestamp");
            //
            //            labels_timestamp.value()->acqtime = this->mTimeNanoSeconds + mComponentTimeOffsetNanoSeconds;
            //            labels_timestamp.value()->pubtime = ::isaac::NowCount();

            // IsaacMessage<isaac_message::Labels> labelsMessage;
            // auto labelsProto = labelsMessage.initProto();
            // auto semanticLabelsProto = labelsProto.initLabels(mSegmentationIDLabelMap.size());
            // int index = 0;
            // for (std::map<uint8_t, std::string>::iterator it = mSegmentationIDLabelMap.begin();
            //      it != mSegmentationIDLabelMap.end(); ++it)
            // {
            //     semanticLabelsProto[index].setIndex(it->first);
            //     semanticLabelsProto[index].setName(it->second);
            //     index++;
            // }
            // std::vector<std::unique_ptr<IsaacBuffer>> buffers;
            //            publish(
            //                mSegmentationOutputComponent, mSegmentationChannelName + "_labels",
            //                std::move(labels_message.value()));
        }

        // Camera intrinsics
        //        publishIntrinsics(mSegmentationOutputComponent, mSegmentationChannelName, segmentationInfo,
        //        focalLength,
        //                          horizontalAperture, verticalAperture);
    }

    if (mEnableBoundingBox2D)
    {
        CARB_PROFILE_ZONE(0, "BBox");

        mBoundingBox2DSensorData = mSyntheticDataInterface->getSensorHostData(mBoundingBox2DSensor);

        const carb::sensors::SensorInfo& boundingBoxInfo = mSensorsInterface->getSensorInfo(mBoundingBox2DSensor);
        size_t bufferSize = boundingBoxInfo.buff.size;
        int numBoundingBoxes = bufferSize / sizeof(carb::sensors::BoundingBox2DValues);

        if (bufferSize > 0)
        {

            carb::sensors::BoundingBox2DValues* data =
                reinterpret_cast<carb::sensors::BoundingBox2DValues*>(mBoundingBox2DSensorData);
            int numValidBoundingBoxes = 0;
            for (int i = 0; i < numBoundingBoxes; i++)
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

                // TODO need to add checks to gxf calls
                auto detections_message = nvidia::gxf::Entity::New(mContext);
                auto detections_tensor = detections_message.value().add<nvidia::gxf::Tensor>("tensor");
                auto detections_timestamp = detections_message.value().add<nvidia::gxf::Timestamp>("timestamp");

                detections_timestamp.value()->acqtime = this->mTimeNanoSeconds + mComponentTimeOffsetNanoSeconds;
                detections_timestamp.value()->pubtime = ::isaac::NowCount();

                // IsaacMessage<isaac_message::Detections2> detectionMessage;
                // auto detectionMessageProto = detectionMessage.initProto();
                // auto boundingBoxesProto = detectionMessageProto.initBoundingBoxes(numValidBoundingBoxes);
                // auto predictionsProto = detectionMessageProto.initPredictions(numValidBoundingBoxes);

                // data = reinterpret_cast<carb::sensors::BoundingBox2DValues*>(mBoundingBox2DSensorData);
                // int boundingBoxId = 0;
                // for (int i = 0; i < numBoundingBoxes; i++)
                // {
                //     std::string semanticLabel(mSyntheticDataInterface->getSemanticDataFromId(data->semanticId));
                //     // Filter bounding boxes based on semantic data
                //     if (mBoundingBox2DClassList.size() > 0)
                //     {
                //         if (std::find(mBoundingBox2DClassList.begin(), mBoundingBox2DClassList.end(), semanticLabel)
                //         ==
                //             mBoundingBox2DClassList.end())
                //         {
                //             data++;
                //             continue;
                //         }
                //     }
                //     // CARB_LOG_ERROR("Data %d: %s %d, %d, %d, %d, %d, %d", boundingBoxId + 1, semanticLabel.c_str(),
                //     // data->instanceId, data->semanticId, data->x_min, data->y_min, data->x_max, data->y_max);
                //     auto minProto = boundingBoxesProto[boundingBoxId].initMin();
                //     auto maxProto = boundingBoxesProto[boundingBoxId].initMax();
                //     minProto.setX(data->y_min);
                //     minProto.setY(data->x_min);
                //     maxProto.setX(data->y_max);
                //     maxProto.setY(data->x_max);
                //     predictionsProto[boundingBoxId].setLabel(semanticLabel);
                //     predictionsProto[boundingBoxId].setConfidence(1.0);
                //     data++;
                //     boundingBoxId++;
                // }
                // std::vector<std::unique_ptr<IsaacBuffer>> buffers;
                publish(mBoundingBox2DOutputComponent, mBoundingBox2DChannelName, std::move(detections_message.value()));
            }
        }
    }

    if (mEnableBoundingBox3D)
    {
        CARB_PROFILE_ZONE(0, "BBox3D");

        mBoundingBox3DSensorData = mSyntheticDataInterface->getSensorHostData(mBoundingBox3DSensor);

        const carb::sensors::SensorInfo& boundingBoxInfo = mSensorsInterface->getSensorInfo(mBoundingBox3DSensor);
        size_t bufferSize = boundingBoxInfo.buff.size;
        int numBoundingBoxes = bufferSize / sizeof(carb::sensors::BoundingBox3DValues);

        if (bufferSize > 0)
        {
            int numValidBoundingBoxes = 0;

            carb::sensors::BoundingBox3DValues* data =
                reinterpret_cast<carb::sensors::BoundingBox3DValues*>(mBoundingBox3DSensorData);

            for (int i = 0; i < numBoundingBoxes; i++)
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
                // // Create the message

                // TODO need to add checks to gxf calls
                auto detections_message = nvidia::gxf::Entity::New(mContext);
                auto detections_tensor = detections_message.value().add<nvidia::gxf::Tensor>("tensor");
                auto detections_timestamp = detections_message.value().add<nvidia::gxf::Timestamp>("timestamp");

                detections_timestamp.value()->acqtime = this->mTimeNanoSeconds + mComponentTimeOffsetNanoSeconds;
                detections_timestamp.value()->pubtime = ::isaac::NowCount();

                // data = reinterpret_cast<carb::sensors::BoundingBox3DValues*>(mBoundingBox3DSensorData);
                // IsaacMessage<isaac_message::Detections3> detectionMessage;
                // auto detectionMessageProto = detectionMessage.initProto();
                // auto boundingBoxesProto = detectionMessageProto.initBoundingBoxes(numValidBoundingBoxes);
                // auto predictionsProto = detectionMessageProto.initPredictions(numValidBoundingBoxes);
                // auto posesProto = detectionMessageProto.initPoses(numValidBoundingBoxes);

                // int boundingBoxId = 0;
                // for (int i = 0; i < numBoundingBoxes; i++)
                // {
                //     std::string semanticLabel(mSyntheticDataInterface->getSemanticDataFromId(data->semanticId));
                //     // Filter bounding boxes based on semantic data
                //     if (mBoundingBox3DClassList.size() > 0)
                //     {
                //         if (std::find(mBoundingBox3DClassList.begin(), mBoundingBox3DClassList.end(), semanticLabel)
                //         ==
                //             mBoundingBox3DClassList.end())
                //         {
                //             data++;
                //             continue;
                //         }
                //     }

                //     // Get pose in world space
                //     auto floatTransform = data->transform;
                //     std::vector<std::vector<float>> transformMatrix(4, std::vector<float>(4, 0));
                //     for (int row = 0; row < 4; row++)
                //         for (int col = 0; col < 4; col++)
                //             transformMatrix[row][col] = floatTransform[row][col];
                //     pxr::GfTransform gfTransform = pxr::GfTransform(pxr::GfMatrix4d(transformMatrix));
                //     auto isaacTranslationProto = posesProto[boundingBoxId].initTranslation();
                //     auto isaacRotationProto = posesProto[boundingBoxId].initRotation();
                //     pxr::GfVec3d translationValue = gfTransform.GetTranslation();
                //     pxr::GfQuatd rotationValue = gfTransform.GetRotation().GetQuat();
                //     pxr::GfVec3d scaleValue = gfTransform.GetScale() * mUnitScale;
                //     toVector3dProto(translationValue * mUnitScale, isaacTranslationProto);
                //     toSO3dProto(rotationValue, isaacRotationProto);
                //     // Get min and max values of 3D bounding box in local space
                //     auto minProto = boundingBoxesProto[boundingBoxId].initMin();
                //     auto maxProto = boundingBoxesProto[boundingBoxId].initMax();
                //     minProto.setX(data->x_min * scaleValue[0]);
                //     minProto.setY(data->y_min * scaleValue[1]);
                //     minProto.setZ(data->z_min * scaleValue[2]);
                //     maxProto.setX(data->x_max * scaleValue[0]);
                //     maxProto.setY(data->y_max * scaleValue[1]);
                //     maxProto.setZ(data->z_max * scaleValue[2]);
                //     predictionsProto[boundingBoxId].setLabel(semanticLabel);
                //     predictionsProto[boundingBoxId].setConfidence(1.0);
                //     // CARB_LOG_ERROR("Translation: %f, %f, %f", isaacTranslationProto.getX(),
                //     // isaacTranslationProto.getY(),
                //     //                isaacTranslationProto.getZ());
                //     // CARB_LOG_ERROR("Scale: %f, %f, %f", scaleValue[0], scaleValue[1], scaleValue[2]);
                //     // std::string primUri(mSyntheticDataInterface->getUriFromInstanceId(data->instanceId));
                //     // CARB_LOG_ERROR("Data %d: %s, %s, %d, %d, %f, %f, %f, %f, %f, %f", boundingBoxId + 1,
                //     // primUri.c_str(),
                //     //                semanticLabel.c_str(), data->instanceId, data->semanticId, data->x_min,
                //     //                data->y_min, data->z_min, data->x_max, data->y_max, data->z_max);
                //     data++;
                //     boundingBoxId++;
                // }
                // std::vector<std::unique_ptr<IsaacBuffer>> buffers;
                publish(mBoundingBox3DOutputComponent, mBoundingBox3DChannelName, std::move(detections_message.value()));
            }
        }
    }
}
void CameraComponent::onStart()
{
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
    mSkipFirstFrame = true;
    mPrevResolution = pxr::GfVec2i(0, 0);

    onComponentChange();

    // Wait until start is called to configure viewports
    if (mDoStart)
        updateViewportSettings();
}
void CameraComponent::onStop()
{
    if (mRgbSensor)
    {
        mSyntheticDataInterface->destroySensor(mRgbSensor);
        mRgbSensor = nullptr;
        mRgbSensorData = nullptr;
    }
    if (mDepthSensor)
    {
        mSyntheticDataInterface->destroySensor(mDepthSensor);
        mDepthSensor = nullptr;
        mDepthSensorData = nullptr;
    }
    if (mSegmentationSensor)
    {
        mSyntheticDataInterface->destroySensor(mSegmentationSensor);
        mSegmentationSensor = nullptr;
        mSegmentationSensorData = nullptr;
    }
    if (mSemanticSensor)
    {
        mSyntheticDataInterface->destroySensor(mSemanticSensor);
        mSemanticSensor = nullptr;
        mSemanticSensorData = nullptr;
    }
    if (mBoundingBox2DSensor)
    {
        mSyntheticDataInterface->destroySensor(mBoundingBox2DSensor);
        mBoundingBox2DSensor = nullptr;
        mBoundingBox2DSensorData = nullptr;
    }
    if (mBoundingBox3DSensor)
    {
        mSyntheticDataInterface->destroySensor(mBoundingBox3DSensor);
        mBoundingBox3DSensor = nullptr;
        mBoundingBox3DSensorData = nullptr;
    }
}

void CameraComponent::onComponentChange()
{
    // CARB_LOG_ERROR("CameraComponent Update");
    GxfComponent::onComponentChange();

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
    mCameraPrim = mStage->GetPrimAtPath(mCameraPath);

    if (!mDoStart)
        updateViewportSettings();
}

void CameraComponent::updateViewportSettings()
{
    std::string primPath = mPrim.GetPath().GetString();
    if (mViewportWindow == nullptr)
    {
        if (mEnabled)
        {
            std::string viewportWindowName = mViewportManager->getViewport();
            mViewportWindow = mViewportInterface->getViewportWindow(
                mViewportInterface->getViewportWindowInstance(viewportWindowName.c_str()));
            mViewportManager->registerViewport(viewportWindowName, primPath);
        }
    }
    else
    {
        if (!mEnabled)
        {
            mViewportWindow = nullptr;
            mViewportManager->unregisterViewport(primPath);
        }
    }
    if (mViewportWindow == nullptr)
        return;

    mViewportWindow->setActiveCamera(mCameraPath.GetString().c_str());
    if (mResolution[0] != 0 && mResolution[1] != 0 && mResolution != mPrevResolution)
    {
        if (mDoStart)
        {
            mViewportWindow->setTextureResolution(mResolution[0], mResolution[1]);
            mPrevResolution = mResolution;
        }
        else
            CARB_LOG_WARN("Resolution will change once you stop and start simulation");
    }

    if (mEnableRgb)
    {
        mRgbSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eRgb, mViewportWindow);
        mRgbBuffers.resize(1);
        mRgbBuffers[0] = std::make_unique<IsaacDeviceBuffer>();
    }
    else
    {
        mRgbSensor = nullptr;
        mRgbSensorData = nullptr;
        mRgbBuffers.clear();
    }

    if (mEnableDepth)
    {
        mDepthSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eDepthLinear, mViewportWindow);
        mDepthBuffers.resize(1);
        mDepthBuffers[0] = std::make_unique<IsaacDeviceBuffer>();
    }
    else
    {
        mDepthSensor = nullptr;
        mDepthSensorData = nullptr;
        mDepthBuffers.clear();
    }

    if (mEnableSegmentation)
    {

        mSegmentationSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eInstanceSegmentation, mViewportWindow);
        mSemanticSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eSemanticSegmentation, mViewportWindow);
        mSegmentationBuffers.resize(1);
        mSegmentationBuffers[0] = std::make_unique<IsaacDeviceBuffer>();
        mSemanticBuffers.resize(1);
        mSemanticBuffers[0] = std::make_unique<IsaacDeviceBuffer>();
        // build segmentation ID to label map
        mSegmentationIDLabelMap.clear();
        for (int i = 0; i < 256; ++i)
        {
            std::string semanticLabel(mSyntheticDataInterface->getSemanticDataFromId(i));
            if (!semanticLabel.empty())
            {
                mSegmentationIDLabelMap[i] = semanticLabel;
                // CARB_LOG_ERROR("The initial segmentation labels are %i %s", i, mSegmentationIDLabelMap[i].c_str());
            }
        }
    }
    else
    {
        mSegmentationSensor = nullptr;
        mSegmentationSensorData = nullptr;
        mSemanticSensor = nullptr;
        mSemanticSensorData = nullptr;
        mSegmentationBuffers.clear();
        mSemanticBuffers.clear();
    }

    if (mEnableBoundingBox2D)
    {
        mBoundingBox2DSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eBoundingBox2DTight, mViewportWindow);
    }
    else
    {
        mBoundingBox2DSensor = nullptr;
        mBoundingBox2DSensorData = nullptr;
    }

    if (mEnableBoundingBox3D)
    {
        mBoundingBox3DSensor =
            mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eBoundingBox3D, mViewportWindow);
    }
    else
    {
        mBoundingBox3DSensor = nullptr;
        mBoundingBox3DSensorData = nullptr;
    }
}

void CameraComponent::setIntrinsics(
    const nvidia::gxf::Handle<::isaac::geometry::PinholeD>& intrinsics,
    const nvidia::gxf::Handle<::isaac::geometry::CameraDistortionInfo>& distIntrinsics,
    const carb::sensors::SensorInfo& info,
    float focalLength,
    float horizontalAperture,
    float verticalAperture,
    const std::array<double, ::isaac::geometry::CameraDistortionInfo::kMaxNumCoefficients>& distortionCoefficients,
    const pxr::TfToken projectionType)
{
    intrinsics->dimensions[0] = info.tex.height; // rows
    intrinsics->dimensions[1] = info.tex.width; // columns
    // We have to ignore the vertical aperture number because our pixels are square
    // Compute it directly from the image size and horizontal aperture
    verticalAperture = static_cast<float>(info.tex.height) / static_cast<float>(info.tex.width) * horizontalAperture;
    intrinsics->focal[0] = info.tex.height * focalLength / verticalAperture;
    intrinsics->focal[1] = info.tex.width * focalLength / horizontalAperture;
    intrinsics->center[0] = info.tex.height * 0.5;
    intrinsics->center[1] = info.tex.width * 0.5;

    distIntrinsics->distortion_coefficients = distortionCoefficients;
    distIntrinsics->model = (projectionType.GetString().find("fisheye") != std::string::npos ?
                                 ::isaac::geometry::DistortionModel::kFisheye :
                                 ::isaac::geometry::DistortionModel::kPerspective);
    // CARB_LOG_WARN("%s : %f : %f : %f : %f : %f", projectionType.GetString().c_str(), distortionCoefficients[0],
    //               distortionCoefficients[1], distortionCoefficients[2], distortionCoefficients[3],
    //               distortionCoefficients[4]);
}

}
}
}
