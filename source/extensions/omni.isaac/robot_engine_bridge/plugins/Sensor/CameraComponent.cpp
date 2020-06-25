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
    CARB_PROFILE_ZONE(0, "CameraComponent Tick");

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
        CARB_PROFILE_ZONE(0, "RGB");

        mRgbSensorData = mSyntheticDataInterface->getSensorDeviceData(mRgbSensor);
        const carb::sensors::SensorInfo& rgbInfo = mSensorsInterface->getSensorInfo(mRgbSensor);

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

        rgbaToRgb(mRgbBuffers[0]->data(), (uint8_t*)mRgbSensorData, rgbInfo.tex.width, rgbInfo.tex.height,
                  rgbInfo.tex.rowSize);
        publish(mRgbOutputComponent, mRgbChannelName, imageProto, isaac_message::ImageProtoId, mRgbBuffers);
        publishIntrinsics(
            mRgbOutputComponent, mRgbChannelName, rgbInfo, focalLength, horizontalAperture, verticalAperture);
    }


    if (mDepthSensor)
    {
        CARB_PROFILE_ZONE(0, "Depth");
        const carb::sensors::SensorInfo& depthInfo = mSensorsInterface->getSensorInfo(mDepthSensor);

        // Publish depth image
        IsaacMessage<isaac_message::Image> imageMessage;
        auto imageProto = imageMessage.initProto();
        imageProto.setElementType(ElementType::FLOAT32);
        imageProto.setRows(depthInfo.tex.height);
        imageProto.setCols(depthInfo.tex.width);
        imageProto.setChannels(1);
        imageProto.setDataBufferIndex(0);

        mDepthBuffers[0]->resize(depthInfo.tex.width * depthInfo.tex.height * sizeof(float));
        mDepthSensorData = mSyntheticDataInterface->getSensorDeviceData(mDepthSensor);
        CUDA_CHECK(cudaMemcpy(mDepthBuffers[0]->data(), mDepthSensorData, depthInfo.tex.rowSize * depthInfo.tex.height,
                              cudaMemcpyDeviceToDevice));

        publish(mDepthOutputComponent, mDepthChannelName, imageProto, isaac_message::ImageProtoId, mDepthBuffers);
        publishIntrinsics(
            mDepthOutputComponent, mDepthChannelName, depthInfo, focalLength, horizontalAperture, verticalAperture);
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

            uint32ToUint16((uint16_t*)mSegmentationBuffers[0]->data(), (uint32_t*)mSegmentationSensorData,
                           segmentationInfo.tex.width, segmentationInfo.tex.height, segmentationInfo.tex.rowSize);

            publish(mSegmentationOutputComponent, mSegmentationChannelName + "_instance", instanceImageProto,
                    isaac_message::ImageProtoId, mSegmentationBuffers);
        }

        // Semantic segmentation
        {
            const size_t semanticBufferSize = semanticInfo.tex.width * semanticInfo.tex.height * sizeof(uint8_t);
            std::vector<std::unique_ptr<IsaacBuffer>> buffers(1);
            mSemanticBuffers[0]->resize(semanticBufferSize);


            uint32ToUint8(mSemanticBuffers[0]->data(), (uint32_t*)mSemanticSensorData, semanticInfo.tex.width,
                          semanticInfo.tex.height, semanticInfo.tex.rowSize);


            publish(mSegmentationOutputComponent, mSegmentationChannelName + "_class", semanticImageProto,
                    isaac_message::ImageProtoId, mSemanticBuffers);
        }

        // Class labels
        {
            IsaacMessage<isaac_message::Labels> labelsMessage;
            auto labelsProto = labelsMessage.initProto();
            auto semanticLabelsProto = labelsProto.initLabels(mSegmentationIDLabelMap.size());
            int index = 0;
            for (std::map<uint8_t, std::string>::iterator it = mSegmentationIDLabelMap.begin();
                 it != mSegmentationIDLabelMap.end(); ++it)
            {
                semanticLabelsProto[index].setIndex(it->first);
                semanticLabelsProto[index].setName(it->second);
                index++;
            }
            std::vector<std::unique_ptr<IsaacBuffer>> buffers;
            publish(mSegmentationOutputComponent, mSegmentationChannelName + "_labels", labelsProto,
                    isaac_message::LabelProtoId, buffers);
        }

        // Camera intrinsics
        publishIntrinsics(mSegmentationOutputComponent, mSegmentationChannelName, segmentationInfo, focalLength,
                          horizontalAperture, verticalAperture);
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
            std::vector<std::unique_ptr<IsaacBuffer>> buffers;
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
        mDepthSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eDepthLinear);
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

        mSegmentationSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eInstanceSegmentation);
        mSemanticSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eSemanticSegmentation);
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
        mBoundingBox2DSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eBoundingBox2DTight);
    }
    else
    {
        mBoundingBox2DSensor = nullptr;
        mBoundingBox2DSensorData = nullptr;
    }
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
    focal.setX(info.tex.height * focalLength / verticalAperture);
    focal.setY(info.tex.width * focalLength / horizontalAperture);
    auto center = pinhole.initCenter();
    center.setX(info.tex.height * 0.5f);
    center.setY(info.tex.width * 0.5f);

    std::vector<std::unique_ptr<IsaacBuffer>> dummyBuffers;

    publish(outputComponent, channelName + "_intrinsics", intrinsicsProto, isaac_message::CameraIntrinsicsProtoId,
            dummyBuffers);
}
}
}
}
