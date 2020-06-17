#include "CameraComponent.h"

#include "plugins/core/UsdUtilities.h"

#include <carb/cuda/CudaRuntime.h>

#include <boost/algorithm/string.hpp>

#include <algorithm>
#include <cuda.h>
namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

extern "C" void rgbaToRgb(uint8_t* dest, const uint8_t* src, int width, int height, int srcStride);
extern "C" void uint32ToUint16(uint16_t* dest, const uint32_t* src, int width, int height, int srcStride);
extern "C" void uint32ToUint8(uint8_t* dest, const uint32_t* src, int width, int height, int srcStride);

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
        mSyntheticDataInterface->destroySensor(carb::sensors::SensorType::eRgb);
        mRgbSensor = nullptr;
        mRgbSensorData = nullptr;
    }
    if (mDepthSensor)
    {
        mSyntheticDataInterface->destroySensor(carb::sensors::SensorType::eDepthLinear);
        mDepthSensor = nullptr;
        mDepthSensorData = nullptr;
    }
    if (mSegmentationSensor)
    {
        mSyntheticDataInterface->destroySensor(carb::sensors::SensorType::eInstanceSegmentation);
        mSegmentationSensor = nullptr;
        mSegmentationSensorData = nullptr;
    }
    if (mSemanticSensor)
    {
        mSyntheticDataInterface->destroySensor(carb::sensors::SensorType::eSemanticSegmentation);
        mSemanticSensor = nullptr;
        mSemanticSensorData = nullptr;
    }
    if (mBoundingBox2DSensor)
    {
        mSyntheticDataInterface->destroySensor(carb::sensors::SensorType::eBoundingBox2DTight);
        mBoundingBox2DSensor = nullptr;
        mBoundingBox2DSensorData = nullptr;
    }

    mFramework->releaseInterface(mEditorInterface);
    mFramework->releaseInterface(mSyntheticDataInterface);
    mFramework->releaseInterface(mSensorsInterface);
}

void CameraComponent::tick()
{
    CARB_PROFILE_ZONE(0, "REB CameraComponent Tick");

    if (!mRgbSensor && !mDepthSensor && !mSegmentationSensor && !mSemanticSensor && !mBoundingBox2DSensor)
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
        imageProto.setRows(rgbInfo.tex.height);
        imageProto.setCols(rgbInfo.tex.width);
        imageProto.setChannels(3);
        imageProto.setDataBufferIndex(0);

        // Pinhole info
        auto pinhole = cameraMessageProto.initPinhole();
        pinhole.setRows(rgbInfo.tex.height);
        pinhole.setCols(rgbInfo.tex.width);
        auto focal = pinhole.initFocal();
        focal.setX(rgbInfo.tex.height * focalLength / verticalAperture);
        focal.setY(rgbInfo.tex.width * focalLength / horizontalAperture);
        auto center = pinhole.initCenter();
        center.setX(rgbInfo.tex.height * 0.5f);
        center.setY(rgbInfo.tex.width * 0.5f);

        // Distortion info
        auto distortion = cameraMessageProto.initDistortion();
        distortion.setModel(DistortionProto::DistortionModel::BROWN);
        auto distortionCoeff = distortion.initCoefficients();
        auto coeff = distortionCoeff.initCoefficients(5);
        for (int i = 0; i < 5; i++)
            coeff.set(i, 0.0f);


        const size_t bufferSize = rgbInfo.tex.width * rgbInfo.tex.height * 3;
        std::vector<std::vector<uint8_t>> buffers(1);
        buffers[0] = std::vector<uint8_t>(bufferSize);

        uint8_t* rgbDevice;
        CUDA_CHECK(cudaMalloc(&rgbDevice, bufferSize));

        rgbaToRgb(rgbDevice, (uint8_t*)mRgbSensorData, rgbInfo.tex.width, rgbInfo.tex.height, rgbInfo.tex.rowSize);
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
        imageProto.setRows(depthInfo.tex.height);
        imageProto.setCols(depthInfo.tex.width);
        imageProto.setChannels(1);
        imageProto.setDataBufferIndex(0);

        // TODO : remove duplication with RGB camera
        // Pinhole info
        auto pinhole = cameraMessageProto.initPinhole();
        pinhole.setRows(depthInfo.tex.height);
        pinhole.setCols(depthInfo.tex.width);
        auto focal = pinhole.initFocal();
        focal.setX(depthInfo.tex.height * focalLength / verticalAperture);
        focal.setY(depthInfo.tex.width * focalLength / horizontalAperture);
        auto center = pinhole.initCenter();
        center.setX(depthInfo.tex.height * 0.5f);
        center.setY(depthInfo.tex.width * 0.5f);

        std::vector<std::vector<uint8_t>> buffers(1);
        buffers[0] = std::vector<uint8_t>(depthInfo.tex.width * depthInfo.tex.height * sizeof(float));
        mDepthSensorData = mSyntheticDataInterface->getSensorDeviceData(mDepthSensor);
        CUDA_CHECK(cudaMemcpy(
            buffers[0].data(), mDepthSensorData, depthInfo.tex.rowSize * depthInfo.tex.height, cudaMemcpyDeviceToHost));

        publish(mDepthOutputComponent, mDepthChannelName, cameraMessageProto, isaac_message::DepthCameraProtoId, buffers);
    }

    // TODO can we turn on mSegmentationSensor && mSemanticSensor separately
    if (mSegmentationSensor && mSemanticSensor)
    {
        mSegmentationSensorData = mSyntheticDataInterface->getSensorDeviceData(mSegmentationSensor);
        mSemanticSensorData = mSyntheticDataInterface->getSensorDeviceData(mSemanticSensor);

        const carb::sensors::SensorInfo& segmentationInfo = mSensorsInterface->getSensorInfo(mSegmentationSensor);
        const carb::sensors::SensorInfo& semanticInfo = mSensorsInterface->getSensorInfo(mSemanticSensor);

        // Create the message
        IsaacMessage<isaac_message::SegmentationCamera> cameraMessage;
        auto cameraMessageProto = cameraMessage.initProto();

        // Create the instance image
        auto instanceImageProto = cameraMessageProto.initInstanceImage();
        instanceImageProto.setElementType(ElementType::UINT16);
        instanceImageProto.setRows(segmentationInfo.tex.height);
        instanceImageProto.setCols(segmentationInfo.tex.width);
        instanceImageProto.setChannels(1);
        instanceImageProto.setDataBufferIndex(0);

        // Create the semantic image
        auto semanticImageProto = cameraMessageProto.initLabelImage();
        semanticImageProto.setElementType(ElementType::UINT8);
        semanticImageProto.setRows(semanticInfo.tex.height);
        semanticImageProto.setCols(semanticInfo.tex.width);
        semanticImageProto.setChannels(1);
        semanticImageProto.setDataBufferIndex(1);

        auto semanticLabelsProto = cameraMessageProto.initLabels(mSegmentationIDLabelMap.size());
        int index = 0;
        for (std::map<uint8_t, std::string>::iterator it = mSegmentationIDLabelMap.begin();
             it != mSegmentationIDLabelMap.end(); ++it)
        {
            semanticLabelsProto[index].setIndex(it->first);
            semanticLabelsProto[index].setName(it->second);
            index++;
        }

        // These images should be of the same resolution
        if (segmentationInfo.tex.height != semanticInfo.tex.height || segmentationInfo.tex.width != semanticInfo.tex.width)
        {
            CARB_LOG_ERROR("The segmentation and semantic textures have different resolutions");
            return;
        }

        // TODO : remove duplication with RGB camera
        // Pinhole info
        auto pinhole = cameraMessageProto.initPinhole();
        pinhole.setRows(segmentationInfo.tex.height);
        pinhole.setCols(segmentationInfo.tex.width);
        auto focal = pinhole.initFocal();
        focal.setX(segmentationInfo.tex.height * focalLength / verticalAperture);
        focal.setY(segmentationInfo.tex.width * focalLength / horizontalAperture);
        auto center = pinhole.initCenter();
        center.setX(segmentationInfo.tex.height * 0.5f);
        center.setY(segmentationInfo.tex.width * 0.5f);

        // Message buffers
        std::vector<std::vector<uint8_t>> buffers(2);

        // TODO : The instance and semantic segmentation should be refactored into one method
        // TODO : Have persistent device buffers for the CUDA conversion
        // Instance segmentation
        const size_t bufferSize = segmentationInfo.tex.width * segmentationInfo.tex.height * sizeof(uint16_t);
        buffers[0] = std::vector<uint8_t>(bufferSize);

        uint16_t* segmentationDevice;
        CUDA_CHECK(cudaMalloc(&segmentationDevice, bufferSize));

        uint32ToUint16(segmentationDevice, (uint32_t*)mSegmentationSensorData, segmentationInfo.tex.width,
                       segmentationInfo.tex.height, segmentationInfo.tex.rowSize);
        CUDA_CHECK(cudaMemcpy(buffers[0].data(), segmentationDevice, bufferSize, cudaMemcpyDeviceToHost));

        CUDA_CHECK(cudaFree(segmentationDevice));


        // Semantic segmentation
        const size_t semanticBufferSize = semanticInfo.tex.width * semanticInfo.tex.height * sizeof(uint8_t);
        buffers[1] = std::vector<uint8_t>(semanticBufferSize);

        uint8_t* semanticDevice;
        CUDA_CHECK(cudaMalloc(&semanticDevice, semanticBufferSize));

        uint32ToUint8(semanticDevice, (uint32_t*)mSemanticSensorData, semanticInfo.tex.width, semanticInfo.tex.height,
                      semanticInfo.tex.rowSize);
        CUDA_CHECK(cudaMemcpy(buffers[1].data(), semanticDevice, semanticBufferSize, cudaMemcpyDeviceToHost));

        CUDA_CHECK(cudaFree(semanticDevice));


        publish(mSegmentationOutputComponent, mSegmentationChannelName, cameraMessageProto,
                isaac_message::SegmentationCameraProtoId, buffers);
    }

    if (mEnableBoundingBox2D)
    {
        mBoundingBox2DSensorData = mSyntheticDataInterface->getSensorHostData(mBoundingBox2DSensor);

        const carb::sensors::SensorInfo& boundingBoxInfo = mSensorsInterface->getSensorInfo(mBoundingBox2DSensor);
        size_t bufferSize = boundingBoxInfo.buff.size;
        int numBoundingBoxes = bufferSize / sizeof(carb::sensors::BoundingBox2DValues);

        if (bufferSize > 0)
        {
            // Create the message
            IsaacMessage<isaac_message::Detections2> detectionMessage;
            auto detectionMessageProto = detectionMessage.initProto();
            auto boundingBoxesProto = detectionMessageProto.initBoundingBoxes(numBoundingBoxes);
            auto predictionsProto = detectionMessageProto.initPredictions(numBoundingBoxes);

            carb::sensors::BoundingBox2DValues* data =
                reinterpret_cast<carb::sensors::BoundingBox2DValues*>(mBoundingBox2DSensorData);
            for (int boundingBoxId = 0; boundingBoxId < numBoundingBoxes; boundingBoxId++)
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
            }
            std::vector<std::vector<uint8_t>> buffers;
            publish(mBoundingBox2DOutputComponent, mBoundingBox2DChannelName, detectionMessageProto,
                    isaac_message::Detections2ProtoId, buffers);
        }
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

    // Bounding Box attributes
    std::string filterClassList;
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DOutputComponentAttr(), mBoundingBox2DOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DOutputChannelAttr(), mBoundingBox2DChannelName);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DClassListAttr(), filterClassList);
    isaac::utils::safeGetAttribute(typedPrim.GetBoundingBox2DEnabledAttr(), mEnableBoundingBox2D);
    mBoundingBox2DClassList.clear();
    if (filterClassList != "")
        boost::split(mBoundingBox2DClassList, filterClassList, [](char c) { return c == ','; });


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

        mSegmentationSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eInstanceSegmentation);
        mSemanticSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eSemanticSegmentation);

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
}
}
}
}
