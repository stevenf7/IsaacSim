#include "omni/isaac/bridge/ViewportManager.h"
#include "omni/isaac/utils/Buffer.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/logging/Log.h>
#include <carb/sensors/SensorTypes.h>

#include <omni/kit/ViewportWindowUtils.h>
#include <omni/kit/syntheticdata/SyntheticData.h>

#include <cuda.h>
#include <string>
#include <vector>


namespace omni
{
namespace isaac
{
namespace utils
{
namespace camera_sensor
{

extern "C" void rgbaToRgb(uint8_t* dest, const uint8_t* src, const int width, const int height, const int srcStride);
extern "C" void depthToPCL(void* dest,
                           const float* src,
                           const int width,
                           const int height,
                           const float fx,
                           const float fy,
                           const float cx,
                           const float cy);
extern "C" void uint32ToUint16(uint16_t* dest, const uint32_t* src, int width, int height, int srcStride);
extern "C" void uint32ToUint8(uint8_t* dest, const uint32_t* src, int width, int height, int srcStride);

class CameraSensor
{


public:
    CameraSensor(utils::ViewportManager* viewportManager)
    {
        mViewportManager = viewportManager;
        mViewportInterface = carb::getCachedInterface<omni::kit::IViewport>();
        if (!mViewportInterface)
        {
            CARB_LOG_ERROR("Failed to acquire omni::kit::IViewport interface");
            return;
        }
        mSyntheticDataInterface = carb::getCachedInterface<omni::syntheticdata::SyntheticData>();
        if (!mSyntheticDataInterface)
        {
            CARB_LOG_ERROR("Failed to acquire omni::syntheticdata::SyntheticData interface");
            return;
        }
        mViewportWindow = nullptr;
    }
    ~CameraSensor()
    {
        if (mViewportWindow == nullptr)
        {
            return;
        }
        if (mRgbSensor)
        {
            mSyntheticDataInterface->destroySensor(carb::sensors::SensorType::eRgb, mViewportWindow);
            mRgbSensor = false;
        }
        if (mDepthSensor)
        {
            mSyntheticDataInterface->destroySensor(carb::sensors::SensorType::eDistanceToImagePlane, mViewportWindow);
            mDepthSensor = false;
        }
        if (mDepthForPCLSensor)
        {
            mSyntheticDataInterface->destroySensor(carb::sensors::SensorType::eDistanceToImagePlane, mViewportWindow);
            mDepthForPCLSensor = false;
        }
        if (mInstanceSensor)
        {
            mSyntheticDataInterface->destroySensor(carb::sensors::SensorType::eInstanceSegmentation, mViewportWindow);
            mInstanceSensor = false;
        }
        if (mSemanticSensor)
        {
            mSyntheticDataInterface->destroySensor(carb::sensors::SensorType::eSemanticSegmentation, mViewportWindow);
            mSemanticSensor = false;
        }
        if (mBoundingBox2DSensor)
        {
            mSyntheticDataInterface->destroySensor(carb::sensors::SensorType::eBoundingBox2DTight, mViewportWindow);
            mBoundingBox2DSensor = false;
        }
        if (mBoundingBox3DSensor)
        {
            mSyntheticDataInterface->destroySensor(carb::sensors::SensorType::eBoundingBox3D, mViewportWindow);
            mBoundingBox3DSensor = false;
        }

        if (mViewportWindow != nullptr)
        {
            mViewportWindow = nullptr;
            mViewportManager->unregisterViewport(mPrimPath);
        }
    }

    void updateViewportSettings(const pxr::SdfPath cameraPath,
                                const pxr::SdfPath primPath,
                                const pxr::GfVec2i resolution,
                                const bool doStart,
                                const bool enableRgb,
                                const bool enableDepth,
                                const bool enablePointCloud,
                                const bool enableSegmentation,
                                const bool enableBoundingBox2D,
                                const bool enableBoundingBox3D)
    {
        mPrimPath = primPath.GetString();
        if (mViewportWindow != nullptr)
        {
            mViewportWindow = nullptr;
            mViewportManager->unregisterViewport(mPrimPath);
        }
        if (mViewportWindow == nullptr)
        {
            std::string viewportWindowName = mViewportManager->getViewport();
            mViewportWindow = mViewportInterface->getViewportWindow(
                mViewportInterface->getViewportWindowInstance(viewportWindowName.c_str()));
            mViewportManager->registerViewport(viewportWindowName, mPrimPath);
        }

        mViewportWindow->setActiveCamera(cameraPath.GetString().c_str());
        if (resolution[0] != 0 && resolution[1] != 0 && resolution != mPrevResolution)
        {
            if (doStart)
            {
                mViewportWindow->setTextureResolution(resolution[0], resolution[1]);
                mPrevResolution = resolution;
            }
            else
            {
                CARB_LOG_WARN("Resolution will change once you stop and start simulation");
            }
        }

        if (enableRgb)
        {
            mRgbSensor = mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eRgb, mViewportWindow);
        }
        else
        {
            mRgbSensor = false;
        }

        if (enableDepth)
        {

            mDepthSensor =
                mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eDistanceToImagePlane, mViewportWindow);
        }
        else
        {
            mDepthSensor = false;
        }

        if (enablePointCloud)
        {
            mDepthForPCLSensor =
                mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eDistanceToImagePlane, mViewportWindow);
        }
        else
        {
            mDepthForPCLSensor = false;
        }

        if (enableSegmentation)
        {
            mSemanticSensor =
                mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eSemanticSegmentation, mViewportWindow);
            mInstanceSensor =
                mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eInstanceSegmentation, mViewportWindow);
        }
        else
        {
            mInstanceSensor = false;
            mSemanticSensor = false;
        }

        if (enableBoundingBox2D)
        {
            mBoundingBox2DSensor =
                mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eBoundingBox2DTight, mViewportWindow);
        }
        else
        {
            mBoundingBox2DSensor = false;
        }

        if (enableBoundingBox3D)
        {
            mBoundingBox3DSensor =
                mSyntheticDataInterface->createSensor(carb::sensors::SensorType::eBoundingBox3D, mViewportWindow);
        }
        else
        {
            mBoundingBox3DSensor = false;
        }
    }

    carb::sensors::SensorInfo getSensorInfo()
    {
        carb::sensors::SensorInfo imgInfo;
        if (mRgbSensor)
        {
            imgInfo = mSyntheticDataInterface->getSensorInfo(carb::sensors::SensorType::eRgb, mViewportWindow);
        }
        else if (mDepthSensor)
        {
            imgInfo = mSyntheticDataInterface->getSensorInfo(
                carb::sensors::SensorType::eDistanceToImagePlane, mViewportWindow);
        }
        else if (mDepthForPCLSensor)
        {
            imgInfo = mSyntheticDataInterface->getSensorInfo(
                carb::sensors::SensorType::eDistanceToImagePlane, mViewportWindow);
        }
        else if (mInstanceSensor)
        {
            imgInfo = mSyntheticDataInterface->getSensorInfo(
                carb::sensors::SensorType::eInstanceSegmentation, mViewportWindow);
        }
        else if (mSemanticSensor)
        {
            imgInfo = mSyntheticDataInterface->getSensorInfo(
                carb::sensors::SensorType::eSemanticSegmentation, mViewportWindow);
        }
        else if (mBoundingBox2DSensor)
        {
            imgInfo =
                mSyntheticDataInterface->getSensorInfo(carb::sensors::SensorType::eBoundingBox2DTight, mViewportWindow);
        }
        else if (mBoundingBox3DSensor)
        {
            imgInfo = mSyntheticDataInterface->getSensorInfo(carb::sensors::SensorType::eBoundingBox3D, mViewportWindow);
        }

        return imgInfo;
    }

    const carb::sensors::SensorInfo getSensorInfo(carb::sensors::SensorType type)
    {
        return mSyntheticDataInterface->getSensorInfo(type, mViewportWindow);
    }

    bool getRGB(void* dst, bool isDstDevice = false)
    {
        // Sensor was not enabled, needs to be enabled before we can get data for it.
        if (!mRgbSensor || mViewportWindow == nullptr)
        {
            return false;
        }

        const carb::sensors::SensorInfo& rgbInfo = getSensorInfo(carb::sensors::SensorType::eRgb);

        const size_t sourceSize = rgbInfo.tex.width * rgbInfo.tex.height * rgbInfo.tex.bpp;
        const size_t dstSize = rgbInfo.tex.width * rgbInfo.tex.height * 3;

        if (sourceSize == 0)
        {

            return false;
        }
        mRgbTmpBuffer.resize(sourceSize);
        // TODO: Remove the extra host -> device copy once the bug is fixed.
        void* rgbSensorData =
            mSyntheticDataInterface->getSensorHostData(carb::sensors::SensorType::eRgb, mViewportWindow);
        if (!rgbSensorData)
        {

            return false;
        }
        CUDA_CHECK(cudaMemcpy(mRgbTmpBuffer.data(), rgbSensorData, sourceSize, cudaMemcpyHostToDevice));

        if (!isDstDevice)
        {
            mRgbDeviceBuffer.resize(dstSize);
            rgbaToRgb(mRgbDeviceBuffer.data(), mRgbTmpBuffer.data(), rgbInfo.tex.width, rgbInfo.tex.height,
                      rgbInfo.tex.rowSize);
            CUDA_CHECK(cudaMemcpy(dst, mRgbDeviceBuffer.data(), dstSize, cudaMemcpyDeviceToHost));
        }
        else
        {
            // write directly to a gpu buffer
            rgbaToRgb((uint8_t*)dst, mRgbTmpBuffer.data(), rgbInfo.tex.width, rgbInfo.tex.height, rgbInfo.tex.rowSize);
        }

        return true;
    }
    bool getDepth(void* dst, bool isDstDevice = false)
    {
        if (!mDepthSensor || mViewportWindow == nullptr)
        {
            return false;
        }
        const carb::sensors::SensorInfo& depthInfo = getSensorInfo(carb::sensors::SensorType::eDistanceToImagePlane);
        void* depthSensorData = mSyntheticDataInterface->getSensorHostData(
            carb::sensors::SensorType::eDistanceToImagePlane, mViewportWindow);
        if (!depthSensorData)
        {
            return false;
        }
        if (!isDstDevice)
        {
            std::memcpy(dst, depthSensorData, depthInfo.tex.rowSize * depthInfo.tex.height);
        }
        else
        {
            // dst is a gpu buffer so we just copy it
            CUDA_CHECK(
                cudaMemcpy(dst, depthSensorData, depthInfo.tex.rowSize * depthInfo.tex.height, cudaMemcpyHostToDevice));
        }
        return true;
    }

    bool getPCL(void* dst, float fx, float fy, float cx, float cy)
    {
        if (!mDepthForPCLSensor || mViewportWindow == nullptr)
        {
            return false;
        }
        // define struct manually here
        typedef struct __align__(16)
        {
            float x;
            float y;
            float z;
        }
        PointXYZ;

        const carb::sensors::SensorInfo& depthInfo = getSensorInfo(carb::sensors::SensorType::eDistanceToImagePlane);
        const size_t srcSize = depthInfo.tex.width * depthInfo.tex.height * sizeof(float);
        const size_t dstSize = depthInfo.tex.width * depthInfo.tex.height * sizeof(PointXYZ);
        mPCLTmpBuffer.resize(depthInfo.tex.width * depthInfo.tex.height);
        mPclDeviceBuffer.resize(dstSize);

        void* depthForPCLSensorData = mSyntheticDataInterface->getSensorHostData(
            carb::sensors::SensorType::eDistanceToImagePlane, mViewportWindow);
        if (!depthForPCLSensorData)
        {
            return false;
        }
        CUDA_CHECK(cudaMemcpy(mPCLTmpBuffer.data(), depthForPCLSensorData, srcSize, cudaMemcpyHostToDevice));
        depthToPCL(
            mPclDeviceBuffer.data(), mPCLTmpBuffer.data(), depthInfo.tex.width, depthInfo.tex.height, fx, fy, cx, cy);
        CUDA_CHECK(cudaMemcpy(dst, mPclDeviceBuffer.data(), dstSize, cudaMemcpyDeviceToHost));
        return true;
    }
    bool getInstance(void* dst, bool isSDKGXF = false, bool isDstDevice = false)
    {
        if (!mInstanceSensor || mViewportWindow == nullptr)
        {
            return false;
        }
        const carb::sensors::SensorInfo& instanceInfo = getSensorInfo(carb::sensors::SensorType::eInstanceSegmentation);

        void* segmentationSensorData = mSyntheticDataInterface->getSensorHostData(
            carb::sensors::SensorType::eInstanceSegmentation, mViewportWindow);
        if (!mInstanceSensor)
        {
            return false;
        }
        if (!isSDKGXF)
        {
            std::memcpy(dst, segmentationSensorData, instanceInfo.tex.rowSize * instanceInfo.tex.height);
        }
        else
        {
            mInstanceTmpBuffer.resize(instanceInfo.tex.width * instanceInfo.tex.height);
            CUDA_CHECK(cudaMemcpy(mInstanceTmpBuffer.data(), segmentationSensorData,
                                  instanceInfo.tex.rowSize * instanceInfo.tex.height, cudaMemcpyHostToDevice));
            // NOTE: this is only ever usd with SDK bridge and dst there is always a gpu buffer
            if (isDstDevice)
            {
                uint32ToUint16((uint16_t*)dst, mInstanceTmpBuffer.data(), instanceInfo.tex.width,
                               instanceInfo.tex.height, instanceInfo.tex.rowSize);
            }
            else
            {
                mInstance16TmpBuffer.resize(instanceInfo.tex.width * instanceInfo.tex.height);
                uint32ToUint16(mInstance16TmpBuffer.data(), mInstanceTmpBuffer.data(), instanceInfo.tex.width,
                               instanceInfo.tex.height, instanceInfo.tex.rowSize);
                CUDA_CHECK(cudaMemcpy(dst, mInstance16TmpBuffer.data(),
                                      instanceInfo.tex.width * instanceInfo.tex.height * sizeof(uint16_t),
                                      cudaMemcpyDeviceToHost));
            }
        }
        return true;
    }
    bool getSemantic(void* dst, bool isSDKGXF = false, bool isDstDevice = false)
    {
        if (!mSemanticSensor || mViewportWindow == nullptr)
        {
            return false;
        }
        const carb::sensors::SensorInfo& semanticInfo = getSensorInfo(carb::sensors::SensorType::eSemanticSegmentation);

        void* semanticSensorData = mSyntheticDataInterface->getSensorHostData(
            carb::sensors::SensorType::eSemanticSegmentation, mViewportWindow);
        if (!semanticSensorData)
        {
            return false;
        }
        if (!isSDKGXF)
        {
            std::memcpy(dst, semanticSensorData, semanticInfo.tex.rowSize * semanticInfo.tex.height);
        }
        else
        {
            mSemanticTmpBuffer.resize(semanticInfo.tex.width * semanticInfo.tex.height);
            CUDA_CHECK(cudaMemcpy(mSemanticTmpBuffer.data(), semanticSensorData,
                                  semanticInfo.tex.rowSize * semanticInfo.tex.height, cudaMemcpyHostToDevice));
            // NOTE: this is only ever usd with SDK bridge and dst there is always a gpu buffer
            if (isDstDevice)
            {
                uint32ToUint8((uint8_t*)dst, mSemanticTmpBuffer.data(), semanticInfo.tex.width, semanticInfo.tex.height,
                              semanticInfo.tex.rowSize);
            }
            else
            {
                mSemantic8TmpBuffer.resize(semanticInfo.tex.width * semanticInfo.tex.height);
                uint32ToUint8(mSemantic8TmpBuffer.data(), mInstanceTmpBuffer.data(), semanticInfo.tex.width,
                              semanticInfo.tex.height, semanticInfo.tex.rowSize);
                CUDA_CHECK(cudaMemcpy(dst, mSemantic8TmpBuffer.data(),
                                      semanticInfo.tex.width * semanticInfo.tex.height * sizeof(uint8_t),
                                      cudaMemcpyDeviceToHost));
            }
        }
        return true;
    }
    bool getLabels(std::map<uint8_t, std::string>& labelMap)
    {
        if (!mSemanticSensor || mViewportWindow == nullptr)
        {
            return false;
        }

        labelMap.clear();
        for (int i = 0; i < 256; ++i)
        {
            std::string semanticLabel(mSyntheticDataInterface->getSemanticDataFromId(i));
            if (!semanticLabel.empty())
            {
                labelMap[i] = semanticLabel;
            }
        }
        return true;
    }

    bool getBBox2D(carb::sensors::BoundingBox2DValues* dst, size_t& numBoundingBoxes)
    {
        if (!mBoundingBox2DSensor || mViewportWindow == nullptr)
        {
            return false;
        }

        void* boundingBox2DSensorData =
            mSyntheticDataInterface->getSensorHostData(carb::sensors::SensorType::eBoundingBox2DTight, mViewportWindow);

        const carb::sensors::SensorInfo& boundingBox2DInfo =
            getSensorInfo(carb::sensors::SensorType::eBoundingBox2DTight);

        dst = reinterpret_cast<carb::sensors::BoundingBox2DValues*>(boundingBox2DSensorData);
        numBoundingBoxes = boundingBox2DInfo.buff.size / sizeof(carb::sensors::BoundingBox2DValues);
        if (numBoundingBoxes == 0)
        {
            return false;
        }
        else
        {
            return true;
        }
    }

    bool getBBox3D(carb::sensors::BoundingBox3DValues* dst, size_t& numBoundingBoxes)
    {
        if (!mBoundingBox3DSensor || mViewportWindow == nullptr)
        {
            return false;
        }

        void* boundingBox3DSensorData =
            mSyntheticDataInterface->getSensorHostData(carb::sensors::SensorType::eBoundingBox3D, mViewportWindow);

        const carb::sensors::SensorInfo& boundingBox3DInfo = getSensorInfo(carb::sensors::SensorType::eBoundingBox3D);

        dst = reinterpret_cast<carb::sensors::BoundingBox3DValues*>(boundingBox3DSensorData);
        numBoundingBoxes = boundingBox3DInfo.buff.size / sizeof(carb::sensors::BoundingBox3DValues);
        if (numBoundingBoxes == 0)
        {
            return false;
        }
        else
        {
            return true;
        }
    }

    pxr::UsdGeomCamera getActiveCamera(pxr::UsdStageWeakPtr stage)
    {
        const char* cameraPath = mViewportWindow->getActiveCamera();
        return pxr::UsdGeomCamera(stage->GetPrimAtPath(pxr::SdfPath(cameraPath)));
    }


private:
    omni::syntheticdata::SyntheticData* mSyntheticDataInterface = nullptr;
    omni::kit::IViewport* mViewportInterface = nullptr;

    utils::ViewportManager* mViewportManager = nullptr;
    omni::kit::IViewportWindow* mViewportWindow = nullptr;

    bool mRgbSensor = false;
    bool mDepthSensor = false;
    bool mDepthForPCLSensor = false;
    bool mInstanceSensor = false;
    bool mSemanticSensor = false;
    bool mBoundingBox2DSensor = false;
    bool mBoundingBox3DSensor = false;

    omni::isaac::buffer::DeviceBuffer mRgbDeviceBuffer;
    omni::isaac::buffer::DeviceBuffer mRgbTmpBuffer;
    omni::isaac::buffer::DeviceBuffer mPclDeviceBuffer;
    omni::isaac::buffer::DeviceBufferBase<float> mPCLTmpBuffer;
    omni::isaac::buffer::DeviceBufferBase<uint32_t> mInstanceTmpBuffer;
    omni::isaac::buffer::DeviceBufferBase<uint32_t> mSemanticTmpBuffer;

    omni::isaac::buffer::DeviceBufferBase<uint16_t> mInstance16TmpBuffer;
    omni::isaac::buffer::DeviceBufferBase<uint8_t> mSemantic8TmpBuffer;
    pxr::GfVec2i mPrevResolution;
    std::string mPrimPath;
};


}
}
}
}
