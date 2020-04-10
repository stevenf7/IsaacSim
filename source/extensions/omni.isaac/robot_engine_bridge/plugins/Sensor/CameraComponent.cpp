#include "CameraComponent.h"

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

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
        mRgbSensorData = mSyntheticDataInterface->getSensorHostData(mRgbSensor);
        const carb::sensors::SensorInfo& rgbInfo = mSensorsInterface->getSensorInfo(mRgbSensor);

        // Create the message
        IsaacMessage<isaac_message::ColorCamera> cameraMessage;
        auto cameraMessageProto = cameraMessage.initProto();
        cameraMessageProto.setColorSpace(ColorCameraProto::ColorSpace::RGBA);

        // Create the image
        auto imageProto = cameraMessageProto.initImage();
        imageProto.setElementType(ElementType::UINT8);
        imageProto.setRows(rgbInfo.height);
        imageProto.setCols(rgbInfo.width);
        imageProto.setChannels(4);
        imageProto.setDataBufferIndex(0);

        // Pinhole info
        auto pinhole = cameraMessageProto.initPinhole();
        pinhole.setRows(rgbInfo.height);
        pinhole.setCols(rgbInfo.width);
        auto focal = pinhole.initFocal();
        focal.setX(rgbInfo.width * focalLength / horizontalAperture);
        focal.setY(rgbInfo.height * focalLength / verticalAperture);
        auto center = pinhole.initCenter();
        center.setX(rgbInfo.width * 0.5f);
        center.setY(rgbInfo.height * 0.5f);

        // Distortion info
        auto distortion = cameraMessageProto.initDistortion();
        distortion.setModel(DistortionProto::DistortionModel::BROWN);
        auto distortionCoeff = distortion.initCoefficients();
        auto coeff = distortionCoeff.initCoefficients(5);
        for (int i = 0; i < 5; i++)
            coeff.set(i, 0.0f);


        std::vector<std::vector<uint8_t>> buffers(1);
        buffers[0] = std::vector<uint8_t>(rgbInfo.width * rgbInfo.height * 4);
        if (rgbInfo.rowSize == rgbInfo.width * 4)
        {
            std::memcpy(buffers[0].data(), mRgbSensorData, rgbInfo.rowSize * rgbInfo.height);
        }
        else
        {
            for (int i = 0; i < rgbInfo.height; i++)
            {
                std::memcpy(buffers[0].data() + i * rgbInfo.width * 4, (uint8_t*)mRgbSensorData + i * rgbInfo.rowSize,
                            rgbInfo.width * 4);
            }
        }

        publish(mOutputComponent, mChannelName, cameraMessageProto, isaac_message::ColorCameraProtoId, buffers);
    }


    if (mDepthSensor && mDepthSensorData)
    {
        mDepthSensorData = mSyntheticDataInterface->getSensorHostData(mDepthSensor);

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
        if (depthInfo.rowSize == depthInfo.width * sizeof(float))
        {
            std::memcpy(buffers[0].data(), mDepthSensorData, depthInfo.rowSize * depthInfo.height);
        }
        else
        {
            for (int i = 0; i < depthInfo.height; i++)
            {
                std::memcpy(buffers[0].data() + i * depthInfo.width * sizeof(float),
                            (uint8_t*)mDepthSensorData + i * depthInfo.rowSize, depthInfo.width * sizeof(float));
            }
        }

        // Compute depth from inverse depth and scale
        float* depth = reinterpret_cast<float*>(buffers[0].data());
        for (size_t depthIndex = 0; depthIndex < depthInfo.width * depthInfo.height; depthIndex++)
        {
            float transformedDepth = (1.0f / depth[depthIndex]) * mUnitScale;
            depth[depthIndex] = transformedDepth;
        }

        publish(mDepthOutputComponent, mDepthChannelName, cameraMessageProto, isaac_message::DepthCameraProtoId, buffers);
    }

    if (mSegmentationSensor && mSegmentationSensorData)
    {
        mSegmentationSensorData = mSyntheticDataInterface->getSensorHostData(mSegmentationSensor);

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

        std::vector<std::vector<uint8_t>> buffers(1);
        buffers[0] = std::vector<uint8_t>(segmentationInfo.width * segmentationInfo.height * sizeof(uint16_t));

        uint16_t* dest = reinterpret_cast<uint16_t*>(buffers[0].data());
        uint8_t* src = reinterpret_cast<uint8_t*>(mSegmentationSensorData);
        for (int i = 0; i < segmentationInfo.height; i++)
        {
            for (int j = 0; j < segmentationInfo.width; j++)
                dest[i * segmentationInfo.width + j] =
                    (uint16_t) * ((uint32_t*)(src + i * segmentationInfo.rowSize + j * 4));
        }

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
    // RGB attributes
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("outputComponent")))
    {
        attr.Get(&mOutputComponent);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("channelName")))
    {
        attr.Get(&mChannelName);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("enableRgb")))
    {
        attr.Get(&mEnableRgb);
    }

    // Depth attributes
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("depthOutputComponent")))
    {
        attr.Get(&mDepthOutputComponent);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("depthChannelName")))
    {
        attr.Get(&mDepthChannelName);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("enableDepth")))
    {
        attr.Get(&mEnableDepth);
    }

    // Segmentation attributes
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("segmentationOutputComponent")))
    {
        attr.Get(&mSegmentationOutputComponent);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("segmentationChannelName")))
    {
        attr.Get(&mSegmentationChannelName);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("enableSegmentation")))
    {
        attr.Get(&mEnableSegmentation);
    }

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

        mDepthSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eDepth);
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
