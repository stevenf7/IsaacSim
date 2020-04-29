#include "CameraComponent.h"

#include "plugins/core/UsdUtilities.h"

#include <carb/cuda/CudaRuntime.h>

#include <cuda.h>
namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

extern "C" void rgbaToRgb(uint8_t* dest, const uint8_t* src, int width, int height, int srcStride);
extern "C" void uint32ToUint16(uint16_t* dest, const uint32_t* src, int width, int height, int srcStride);

CameraComponent::CameraComponent() : IsaacComponent()
{

    mFramework = carb::getFramework();
    if (!mFramework)
    {
        CARB_LOG_ERROR("*** Failed to get Carbonite framework\n");
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

    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
}

CameraComponent::~CameraComponent()
{
    if (mRgbSensor)
    {
        // mSyntheticDataInterface->destroySensor(mRgbSensor);
        mRgbSensor = nullptr;
        mRgbSensorData = nullptr;
    }
    if (mDepthSensor)
    {
        // mSyntheticDataInterface->destroySensor(mDepthSensor);
        mDepthSensor = nullptr;
        mDepthSensorData = nullptr;
    }
    if (mSegmentationSensor)
    {
        // mSyntheticDataInterface->destroySensor(mSegmentationSensor);
        mSegmentationSensor = nullptr;
        mSegmentationSensorData = nullptr;
    }

    mFramework->releaseInterface(mEditorInterface);
    mFramework->releaseInterface(mSyntheticDataInterface);
    mFramework->releaseInterface(mSensorsInterface);
}

void CameraComponent::tick()
{
    CARB_PROFILE_ZONE(0, "REB CameraComponent Tick");

    if (!mRgbSensor && !mDepthSensor && !mSegmentationSensor)
        return;

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


    if (mRgbSensor)
    {
        mRgbSensorData = mSyntheticDataInterface->getSensorDeviceData(mRgbSensor);
        const carb::sensors::SensorInfo& rgbInfo = mSensorsInterface->getSensorInfo(mRgbSensor);

        // Create the message
        IsaacMessage<isaac_message::ColorCamera> cameraMessage;
        auto cameraMessageProto = cameraMessage.initProto();
        cameraMessageProto.setColorSpace(ColorCameraProto::ColorSpace::RGB);

        // Create the image
        auto imageProto = cameraMessageProto.initImage();
        imageProto.setElementType(ElementType::UINT8);
        imageProto.setRows(rgbInfo.height);
        imageProto.setCols(rgbInfo.width);
        imageProto.setChannels(3);
        imageProto.setDataBufferIndex(0);

        // Pinhole info
        auto pinhole = cameraMessageProto.initPinhole();
        pinhole.setRows(rgbInfo.height);
        pinhole.setCols(rgbInfo.width);
        auto focal = pinhole.initFocal();
        focal.setX(rgbInfo.height * focalLength / verticalAperture);
        focal.setY(rgbInfo.width * focalLength / horizontalAperture);
        auto center = pinhole.initCenter();
        center.setX(rgbInfo.height * 0.5f);
        center.setY(rgbInfo.width * 0.5f);

        // Distortion info
        auto distortion = cameraMessageProto.initDistortion();
        distortion.setModel(DistortionProto::DistortionModel::BROWN);
        auto distortionCoeff = distortion.initCoefficients();
        auto coeff = distortionCoeff.initCoefficients(5);
        for (int i = 0; i < 5; i++)
            coeff.set(i, 0.0f);


        const size_t bufferSize = rgbInfo.width * rgbInfo.height * 3;
        std::vector<std::vector<uint8_t>> buffers(1);
        buffers[0] = std::vector<uint8_t>(bufferSize);

        uint8_t* rgbDevice;
        CUDA_CHECK(cudaMalloc(&rgbDevice, bufferSize));

        rgbaToRgb(rgbDevice, (uint8_t*)mRgbSensorData, rgbInfo.width, rgbInfo.height, rgbInfo.rowSize);
        CUDA_CHECK(cudaMemcpy(buffers[0].data(), rgbDevice, bufferSize, cudaMemcpyDeviceToHost));

        CUDA_CHECK(cudaFree(rgbDevice));

        publish(mRgbOutputComponent, mRgbChannelName, cameraMessageProto, isaac_message::ColorCameraProtoId, buffers);
    }


    if (mDepthSensor)
    {

        const carb::sensors::SensorInfo& depthInfo = mSensorsInterface->getSensorInfo(mDepthSensor);

        // Create the message
        IsaacMessage<isaac_message::DepthCamera> cameraMessage;
        auto cameraMessageProto = cameraMessage.initProto();

        // Create the image
        auto imageProto = cameraMessageProto.initDepthImage();
        imageProto.setElementType(ElementType::FLOAT32);
        imageProto.setRows(depthInfo.height);
        imageProto.setCols(depthInfo.width);
        imageProto.setChannels(1);
        imageProto.setDataBufferIndex(0);

        // TODO : remove duplication with RGB camera
        // Pinhole info
        auto pinhole = cameraMessageProto.initPinhole();
        pinhole.setRows(depthInfo.height);
        pinhole.setCols(depthInfo.width);
        auto focal = pinhole.initFocal();
        focal.setX(depthInfo.width * focalLength / horizontalAperture);
        focal.setY(depthInfo.height * focalLength / verticalAperture);
        auto center = pinhole.initCenter();
        center.setX(depthInfo.width * 0.5f);
        center.setY(depthInfo.height * 0.5f);

        std::vector<std::vector<uint8_t>> buffers(1);
        buffers[0] = std::vector<uint8_t>(depthInfo.width * depthInfo.height * sizeof(float));
        mDepthSensorData = mSyntheticDataInterface->getSensorDeviceData(mDepthSensor);
        CUDA_CHECK(cudaMemcpy(
            buffers[0].data(), mDepthSensorData, depthInfo.rowSize * depthInfo.height, cudaMemcpyDeviceToHost));

        publish(mDepthOutputComponent, mDepthChannelName, cameraMessageProto, isaac_message::DepthCameraProtoId, buffers);
    }

    if (mSegmentationSensor)
    {
        mSegmentationSensorData = mSyntheticDataInterface->getSensorDeviceData(mSegmentationSensor);

        const carb::sensors::SensorInfo& segmentationInfo = mSensorsInterface->getSensorInfo(mSegmentationSensor);

        // Create the message
        IsaacMessage<isaac_message::SegmentationCamera> cameraMessage;
        auto cameraMessageProto = cameraMessage.initProto();

        // Create the instance image
        auto instanceImageProto = cameraMessageProto.initInstanceImage();
        instanceImageProto.setElementType(ElementType::UINT16);
        instanceImageProto.setRows(segmentationInfo.height);
        instanceImageProto.setCols(segmentationInfo.width);
        instanceImageProto.setChannels(1);
        instanceImageProto.setDataBufferIndex(0);

        // TODO : remove duplication with RGB camera
        // Pinhole info
        auto pinhole = cameraMessageProto.initPinhole();
        pinhole.setRows(segmentationInfo.height);
        pinhole.setCols(segmentationInfo.width);
        auto focal = pinhole.initFocal();
        focal.setX(segmentationInfo.width * focalLength / horizontalAperture);
        focal.setY(segmentationInfo.height * focalLength / verticalAperture);
        auto center = pinhole.initCenter();
        center.setX(segmentationInfo.width * 0.5f);
        center.setY(segmentationInfo.height * 0.5f);


        const size_t bufferSize = segmentationInfo.width * segmentationInfo.height * sizeof(uint16_t);
        std::vector<std::vector<uint8_t>> buffers(1);
        buffers[0] = std::vector<uint8_t>(bufferSize);

        uint16_t* segmentationDevice;
        CUDA_CHECK(cudaMalloc(&segmentationDevice, bufferSize));

        uint32ToUint16(segmentationDevice, (uint32_t*)mSegmentationSensorData, segmentationInfo.width,
                       segmentationInfo.height, segmentationInfo.rowSize);
        CUDA_CHECK(cudaMemcpy(buffers[0].data(), segmentationDevice, bufferSize, cudaMemcpyDeviceToHost));

        CUDA_CHECK(cudaFree(segmentationDevice));

        publish(mSegmentationOutputComponent, mSegmentationChannelName, cameraMessageProto,
                isaac_message::SegmentationCameraProtoId, buffers);
    }
}
void CameraComponent::onStart()
{
    onComponentChange();
}

void CameraComponent::onComponentChange()
{
    // CARB_LOG_ERROR("CameraComponent Update");
    IsaacComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEngineCamera& typedPrim = (pxr::RobotEngineBridgeSchemaRobotEngineCamera)mPrim;

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

        mSegmentationSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eSegmentation);
    }
    else
    {
        mSegmentationSensor = nullptr;
        mSegmentationSensorData = nullptr;
    }
}
}
}
}
