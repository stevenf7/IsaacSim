// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "RosCamera.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include "rosgraph_msgs/Clock.h"
#include "std_msgs/Int64.h"
#include "std_msgs/UInt8.h"
#include "std_srvs/Empty.h"
#include "sensor_msgs/CameraInfo.h"
#include "sensor_msgs/Image.h"
#include "sensor_msgs/image_encodings.h"
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
}

void RosCamera::initialize(RosNode* rosNode, const pxr::RosBridgeSchemaRosBridgeComponent& prim, pxr::UsdStageWeakPtr stage)
{
    IsaacComponent::initialize(rosNode, prim, stage);
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


    isaac::utils::safeGetAttribute(typedPrim.GetCameraInfoPubTopicAttr(), mCameraInfoPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetRgbPubTopicAttr(), mRgbPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetDepthPubTopicAttr(), mDepthPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetQueueSizeAttr(), mQueueSize);
    isaac::utils::safeGetAttribute(typedPrim.GetFrameIdAttr(), mFrameId);

    isaac::utils::safeGetAttribute(typedPrim.GetRgbEnabledAttr(), mEnableRgb);
    isaac::utils::safeGetAttribute(typedPrim.GetDepthEnabledAttr(), mEnableDepth);


    mRosNode->createPublisher<sensor_msgs::CameraInfo>(
        mPrim.GetPath().GetString(), mCameraInfoPubTopic, mQueueSize, &RosCamera::cameraInfoPubCallback, this);
    mRosNode->createPublisher<sensor_msgs::Image>(
        mPrim.GetPath().GetString(), mRgbPubTopic, mQueueSize, &RosCamera::rgbPubCallback, this);
    mRosNode->createPublisher<sensor_msgs::Image>(
        mPrim.GetPath().GetString(), mDepthPubTopic, mQueueSize, &RosCamera::depthPubCallback, this);


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

    cam_info_msg.K = { imgInfo.tex.width * focalLength / horizontalAperture,
                       0,
                       imgInfo.tex.height * 0.5f,
                       0,
                       imgInfo.tex.height * focalLength / verticalAperture,
                       imgInfo.tex.width * 0.5f,
                       0,
                       0,
                       1 };
    cam_info_msg.P = { imgInfo.tex.width * focalLength / horizontalAperture,
                       0,
                       imgInfo.tex.height * 0.5f,
                       0,
                       0,
                       imgInfo.tex.height * focalLength / verticalAperture,
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
}
}
}
