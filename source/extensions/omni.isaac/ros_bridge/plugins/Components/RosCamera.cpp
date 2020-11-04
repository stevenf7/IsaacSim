// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "RosCamera.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include "rosgraph_msgs/Clock.h"
#include "std_msgs/Int64.h"
#include "std_msgs/UInt8.h"
#include "std_msgs/String.h"
#include "std_srvs/Empty.h"
#include "sensor_msgs/CameraInfo.h"
#include "sensor_msgs/Image.h"
#include "sensor_msgs/image_encodings.h"
#include "../../msgs/melodic/IsaacBoundingBox.h"
#include "../../msgs/melodic/IsaacBoundingBoxArray.h"
#include "../../msgs/melodic/BoundingBox3D.h"
#include "../../msgs/melodic/BoundingBox3DArray.h"

#include <boost/algorithm/string.hpp>

#include <time.h>
#include <carb/cuda/CudaRuntime.h>

#include <cuda.h>
namespace omni
{
namespace isaac
{
namespace ros_bridge
{
extern "C" void rgbaToRgb(uint8_t* dest, const uint8_t* src, int width, int height, int srcStride);

RosCamera::RosCamera()
{

    mFramework = carb::getFramework();
    if (!mFramework)
    {
        CARB_LOG_ERROR("Failed to get Carbonite framework");
        return;
    }

    mEditorInterface = mFramework->acquireInterface<omni::kit::IEditor>();
    if (!mEditorInterface)
    {
        CARB_LOG_ERROR("Failed to acquire omni::kit::IEditor interface");
        return;
    }

    mSyntheticDataInterface = mFramework->acquireInterface<carb::syntheticdata::SyntheticData>();
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
RosCamera::~RosCamera()
{
    CARB_LOG_INFO("RosCamera Destroyed");
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mCameraInfoPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mRgbPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mDepthPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mInstancePubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mSemanticPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mLabelPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mBoundingBox2DPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mBoundingBox3DPubTopic);
}

void RosCamera::initialize(RosNode* rosNode, const pxr::RosBridgeSchemaRosBridgeComponent& prim, pxr::UsdStageWeakPtr stage)
{
    IsaacComponent::initialize(rosNode, prim, stage);
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);

    onComponentChange();
}

void RosCamera::onComponentChange()
{

    IsaacComponent::onComponentChange();

    const pxr::RosBridgeSchemaRosCamera& typedPrim = (pxr::RosBridgeSchemaRosCamera)mPrim;

    // Destroy the old message, in case the topic changes
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mCameraInfoPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mRgbPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mDepthPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mInstancePubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mSemanticPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mLabelPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mBoundingBox2DPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mBoundingBox3DPubTopic);

    isaac::utils::safeGetAttribute(typedPrim.GetCameraInfoPubTopicAttr(), mCameraInfoPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetRgbPubTopicAttr(), mRgbPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetDepthPubTopicAttr(), mDepthPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetInstancePubTopicAttr(), mInstancePubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetSemanticPubTopicAttr(), mSemanticPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetLabelPubTopicAttr(), mLabelPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DPubTopicAttr(), mBoundingBox2DPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox3DPubTopicAttr(), mBoundingBox3DPubTopic);

    isaac::utils::safeGetAttribute(typedPrim.GetQueueSizeAttr(), mQueueSize);
    isaac::utils::safeGetAttribute(typedPrim.GetFrameIdAttr(), mFrameId);

    isaac::utils::safeGetAttribute(typedPrim.GetRgbEnabledAttr(), mEnableRgb);
    isaac::utils::safeGetAttribute(typedPrim.GetDepthEnabledAttr(), mEnableDepth);
    isaac::utils::safeGetAttribute(typedPrim.GetSegmentationEnabledAttr(), mEnableSegmentation);
    std::string filterClassList2D;
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DEnabledAttr(), mEnableBoundingBox2D);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DClassListAttr(), filterClassList2D);
    std::string filterClassList3D;
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox3DEnabledAttr(), mEnableBoundingBox3D);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox3DClassListAttr(), filterClassList3D);


    mRosNode->createPublisher<sensor_msgs::CameraInfo>(
        mPrim.GetPath().GetString(), mCameraInfoPubTopic, mQueueSize, &RosCamera::cameraInfoPubCallback, this);
    mRosNode->createPublisher<sensor_msgs::Image>(
        mPrim.GetPath().GetString(), mRgbPubTopic, mQueueSize, &RosCamera::rgbPubCallback, this);
    mRosNode->createPublisher<sensor_msgs::Image>(
        mPrim.GetPath().GetString(), mDepthPubTopic, mQueueSize, &RosCamera::depthPubCallback, this);
    mRosNode->createPublisher<sensor_msgs::Image>(
        mPrim.GetPath().GetString(), mInstancePubTopic, mQueueSize, &RosCamera::instancePubCallback, this);
    mRosNode->createPublisher<sensor_msgs::Image>(
        mPrim.GetPath().GetString(), mSemanticPubTopic, mQueueSize, &RosCamera::semanticPubCallback, this);
    mRosNode->createPublisher<std_msgs::String>(
        mPrim.GetPath().GetString(), mLabelPubTopic, mQueueSize, &RosCamera::labelPubCallback, this);
    mRosNode->createPublisher<isaac_bridge::IsaacBoundingBoxArray>(
        mPrim.GetPath().GetString(), mBoundingBox2DPubTopic, mQueueSize, &RosCamera::boundingbox2dPubCallback, this);
    mRosNode->createPublisher<isaac_bridge::BoundingBox3DArray>(
        mPrim.GetPath().GetString(), mBoundingBox3DPubTopic, mQueueSize, &RosCamera::boundingbox3dPubCallback, this);


    mBoundingBox2DClassList.clear();
    if (filterClassList2D != "")
        boost::split(mBoundingBox2DClassList, filterClassList2D, [](char c) { return c == ','; });

    mBoundingBox3DClassList.clear();
    if (filterClassList3D != "")
        boost::split(mBoundingBox3DClassList, filterClassList3D, [](char c) { return c == ','; });


    if (mEnableRgb)
    {
        mRgbSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eRgb);
    }
    else
    {
        mRgbSensor = nullptr;
        mRgbSensorData = nullptr;
    }

    if (mEnableDepth)
    {

        mDepthSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eDepthLinear);
    }
    else
    {
        mDepthSensor = nullptr;
        mDepthSensorData = nullptr;
    }

    if (mEnableSegmentation)
    {
        mSemanticSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eSemanticSegmentation);
        mSegmentationSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eInstanceSegmentation);
    }
    else
    {
        mSegmentationSensor = nullptr;
        mSegmentationSensorData = nullptr;
        mSemanticSensor = nullptr;
        mSemanticSensorData = nullptr;
    }

    if (mEnableBoundingBox2D)
    {
        mBoundingBox2DSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eBoundingBox2DTight);
    }
    else
    {
        mBoundingBox2DSensor = nullptr;
        mBoundingBox2DSensorData = nullptr;
    }

    if (mEnableBoundingBox3D)
    {
        mBoundingBox3DSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eBoundingBox3D);
    }
    else
    {
        mBoundingBox3DSensor = nullptr;
        mBoundingBox3DSensorData = nullptr;
    }
}

void RosCamera::cameraInfoPubCallback(ros::Publisher* pub)
{
    const char* cameraPath = mEditorInterface->getActiveCamera();
    if (!cameraPath)
        return;

    pxr::SdfPath path(cameraPath);
    pxr::UsdPrim prim = mStage->GetPrimAtPath(path);

    pxr::UsdGeomCamera cameraPrim(prim);

    float focalLength;
    pxr::GfVec2f clipRange;
    float horizontalAperture, verticalAperture;

    cameraPrim.GetFocalLengthAttr().Get(&focalLength);
    cameraPrim.GetClippingRangeAttr().Get(&clipRange);
    cameraPrim.GetHorizontalApertureAttr().Get(&horizontalAperture);
    cameraPrim.GetVerticalApertureAttr().Get(&verticalAperture);
    carb::sensors::SensorInfo imgInfo;
    if (mEnableRgb)
    {
        imgInfo = mSensorsInterface->getSensorInfo(mRgbSensor);
    }
    else if (mEnableDepth)
    {
        imgInfo = mSensorsInterface->getSensorInfo(mDepthSensor);
    }
    else
    {
        return;
    }

    sensor_msgs::CameraInfo cam_info_msg;
    cam_info_msg.header.seq = 0;
    cam_info_msg.header.frame_id = mFrameId;
    cam_info_msg.header.stamp.fromSec(mTimeSeconds);
    cam_info_msg.height = imgInfo.tex.height;
    cam_info_msg.width = imgInfo.tex.width;
    cam_info_msg.distortion_model = "plumb_bob";

    cam_info_msg.K = { imgInfo.tex.height * focalLength / verticalAperture,
                       0,
                       imgInfo.tex.height * 0.5f,
                       0,
                       imgInfo.tex.width * focalLength / horizontalAperture,
                       imgInfo.tex.width * 0.5f,
                       0,
                       0,
                       1 };
    cam_info_msg.P = { imgInfo.tex.height * focalLength / verticalAperture,
                       0,
                       imgInfo.tex.height * 0.5f,
                       0,
                       0,
                       imgInfo.tex.width * focalLength / horizontalAperture,
                       imgInfo.tex.width * 0.5f,
                       0,
                       0,
                       0,
                       1,
                       0 };
    cam_info_msg.D = { 0, 0, 0, 0, 0 };
    pub->publish(cam_info_msg);
}

void RosCamera::rgbPubCallback(ros::Publisher* pub)
{
    if (!mEnableRgb || !mRgbSensor)
    {
        return;
    }
    const carb::sensors::SensorInfo& rgbInfo = mSensorsInterface->getSensorInfo(mRgbSensor);

    const int color_channels = 3;
    const size_t color_step = rgbInfo.tex.width * color_channels * sizeof(uint8_t);

    sensor_msgs::Image color_msg;
    color_msg.header.seq = 0;
    color_msg.header.frame_id = mFrameId;
    color_msg.header.stamp.fromSec(mTimeSeconds);
    color_msg.width = rgbInfo.tex.width;
    color_msg.height = rgbInfo.tex.height;
    color_msg.step = color_step;
    color_msg.encoding = sensor_msgs::image_encodings::RGB8;
    color_msg.data.resize(rgbInfo.tex.height * color_step);
    uint8_t* rgb = &color_msg.data[0];
    uint8_t* rgbDevice;
    const size_t bufferSize = rgbInfo.tex.width * rgbInfo.tex.height * 3;
    CUDA_CHECK(cudaMalloc(&rgbDevice, bufferSize));
    mRgbSensorData = mSyntheticDataInterface->getSensorDeviceData(mRgbSensor);

    rgbaToRgb(rgbDevice, (uint8_t*)mRgbSensorData, rgbInfo.tex.width, rgbInfo.tex.height, rgbInfo.tex.rowSize);
    CUDA_CHECK(cudaMemcpy(rgb, rgbDevice, bufferSize, cudaMemcpyDeviceToHost));

    CUDA_CHECK(cudaFree(rgbDevice));
    pub->publish(color_msg);
}
void RosCamera::depthPubCallback(ros::Publisher* pub)
{

    if (!mEnableDepth || !mDepthSensor)
    {
        return;
    }
    const carb::sensors::SensorInfo& depthInfo = mSensorsInterface->getSensorInfo(mDepthSensor);

    const int depth_channels = 1;
    const size_t depth_step = depthInfo.tex.width * depth_channels * sizeof(float);


    sensor_msgs::Image depth_msg;
    depth_msg.header.seq = 0;
    depth_msg.header.frame_id = mFrameId;
    depth_msg.header.stamp.fromSec(mTimeSeconds);
    depth_msg.width = depthInfo.tex.width;
    depth_msg.height = depthInfo.tex.height;
    depth_msg.step = depth_step;
    depth_msg.encoding = sensor_msgs::image_encodings::TYPE_32FC1;
    depth_msg.data.resize(depthInfo.tex.height * depth_step);

    uint8_t* depth = &depth_msg.data[0];
    mDepthSensorData = mSyntheticDataInterface->getSensorDeviceData(mDepthSensor);
    CUDA_CHECK(cudaMemcpy(depth, mDepthSensorData, depthInfo.tex.rowSize * depthInfo.tex.height, cudaMemcpyDeviceToHost));
    pub->publish(depth_msg);
}

void RosCamera::instancePubCallback(ros::Publisher* pub)
{
    if (!mEnableSegmentation || !mSegmentationSensor)
    {
        return;
    }
    mSegmentationSensorData = mSyntheticDataInterface->getSensorDeviceData(mSegmentationSensor);
    const carb::sensors::SensorInfo& instanceInfo = mSensorsInterface->getSensorInfo(mSegmentationSensor);


    // instance (output is an image with integer labels)
    const int instance_channels = 1;
    const size_t instance_step = instanceInfo.tex.width * instance_channels * sizeof(float);

    sensor_msgs::Image instance_msg;
    instance_msg.header.seq = 0;
    instance_msg.header.frame_id = mFrameId;
    instance_msg.header.stamp.fromSec(mTimeSeconds);
    instance_msg.width = instanceInfo.tex.width;
    instance_msg.height = instanceInfo.tex.height;
    instance_msg.step = instance_step;
    instance_msg.encoding = sensor_msgs::image_encodings::TYPE_32FC1;
    instance_msg.data.resize(instanceInfo.tex.height * instance_step);

    uint8_t* instance = &instance_msg.data[0];
    CUDA_CHECK(cudaMemcpy(
        instance, mSegmentationSensorData, instanceInfo.tex.rowSize * instanceInfo.tex.height, cudaMemcpyDeviceToHost));
    pub->publish(instance_msg);
}

void RosCamera::semanticPubCallback(ros::Publisher* pub)
{
    if (!mEnableSegmentation || !mSemanticSensor)
    {
        return;
    }
    mSemanticSensorData = mSyntheticDataInterface->getSensorDeviceData(mSemanticSensor);
    const carb::sensors::SensorInfo& semanticInfo = mSensorsInterface->getSensorInfo(mSemanticSensor);

    // segmentation (output is an image with integer labels)
    const int semantic_channels = 1;
    const size_t semantic_step = semanticInfo.tex.width * semantic_channels * sizeof(float);

    sensor_msgs::Image semantic_msg;
    semantic_msg.header.seq = 0;
    semantic_msg.header.frame_id = mFrameId;
    semantic_msg.header.stamp.fromSec(mTimeSeconds);
    semantic_msg.width = semanticInfo.tex.width;
    semantic_msg.height = semanticInfo.tex.height;
    semantic_msg.step = semantic_step;
    semantic_msg.encoding = sensor_msgs::image_encodings::TYPE_32FC1;
    semantic_msg.data.resize(semanticInfo.tex.height * semantic_step);

    uint8_t* semantic = &semantic_msg.data[0];
    CUDA_CHECK(cudaMemcpy(
        semantic, mSemanticSensorData, semanticInfo.tex.rowSize * semanticInfo.tex.height, cudaMemcpyDeviceToHost));
    pub->publish(semantic_msg);
}

void RosCamera::labelPubCallback(ros::Publisher* pub)
{
    if (!mEnableSegmentation || !mSemanticSensor)
    {
        return;
    }

    std::string labels;
    labels.append("{");
    for (int i = 0; i < 256; ++i)
    {
        std::string semanticLabel(mSyntheticDataInterface->getSemanticDataFromId(i));
        if (!semanticLabel.empty())
        {
            labels.append(std::to_string(i));
            labels.append(": '");
            labels.append(semanticLabel.c_str());
            labels.append("'; ");
        }
    }
    labels.append("}");
    std_msgs::String label_msg;
    label_msg.data = labels;
    pub->publish(label_msg);
}


void RosCamera::boundingbox2dPubCallback(ros::Publisher* pub)
{

    if (!mEnableBoundingBox2D || !mBoundingBox2DSensor)
    {
        return;
    }

    mBoundingBox2DSensorData = mSyntheticDataInterface->getSensorHostData(mBoundingBox2DSensor);

    const carb::sensors::SensorInfo& boundingBox2DInfo = mSensorsInterface->getSensorInfo(mBoundingBox2DSensor);
    size_t bufferSize = boundingBox2DInfo.buff.size;
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

        isaac_bridge::IsaacBoundingBoxArray bbox_msg;
        if (numValidBoundingBoxes > 0)
        {
            data = reinterpret_cast<carb::sensors::BoundingBox2DValues*>(mBoundingBox2DSensorData);
            int boundingBoxId = 0;
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
                isaac_bridge::IsaacBoundingBox bbox_single;
                bbox_single.name = semanticLabel;
                bbox_single.confidence = 1.0;
                bbox_single.xmin = data->x_min;
                bbox_single.ymin = data->y_min;
                bbox_single.xmax = data->x_max;
                bbox_single.ymax = data->y_max;

                bbox_msg.bboxes.push_back(bbox_single);

                data++;
                boundingBoxId++;
            }
        }
        pub->publish(bbox_msg);
    }
}

void RosCamera::boundingbox3dPubCallback(ros::Publisher* pub)
{
    if (!mEnableBoundingBox3D || !mBoundingBox3DSensor)
    {
        return;
    }


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

        isaac_bridge::BoundingBox3DArray bbox_msg;
        if (numValidBoundingBoxes > 0)
        {
            data = reinterpret_cast<carb::sensors::BoundingBox3DValues*>(mBoundingBox3DSensorData);

            int boundingBoxId = 0;
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

                // Get pose in world space
                auto floatTransform = data->transform;
                std::vector<std::vector<float>> transformMatrix(4, std::vector<float>(4, 0));
                for (int row = 0; row < 4; row++)
                    for (int col = 0; col < 4; col++)
                        transformMatrix[row][col] = floatTransform[row][col];
                pxr::GfTransform gfTransform = pxr::GfTransform(pxr::GfMatrix4d(transformMatrix));
                pxr::GfVec3d translationValue = gfTransform.GetTranslation();
                pxr::GfQuatd rotationValue = gfTransform.GetRotation().GetQuat();
                pxr::GfVec3d scaleValue = gfTransform.GetScale() * mUnitScale;

                // Get min and max values of 3D bounding box in local space
                isaac_bridge::BoundingBox3D bbox_single;
                bbox_single.name = semanticLabel;
                bbox_single.confidence = 1.0;
                bbox_single.center.position.x = translationValue[0] * mUnitScale;
                bbox_single.center.position.y = translationValue[1] * mUnitScale;
                bbox_single.center.position.z = translationValue[2] * mUnitScale;

                bbox_single.center.orientation.x = rotationValue.GetImaginary()[0];
                bbox_single.center.orientation.y = rotationValue.GetImaginary()[1];
                bbox_single.center.orientation.z = rotationValue.GetImaginary()[2];
                bbox_single.center.orientation.w = rotationValue.GetReal();

                bbox_single.size.x = (data->x_max - data->x_min) * scaleValue[0];
                bbox_single.size.y = (data->y_max - data->y_min) * scaleValue[1];
                bbox_single.size.z = (data->z_max - data->z_min) * scaleValue[2];

                bbox_msg.bboxes.push_back(bbox_single);

                data++;
                boundingBoxId++;
            }
        }
        pub->publish(bbox_msg);
    }
}


}
}
}
