// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <omni/isaac/lidar/LidarInterface.h>
#include <carb/Framework.h>
#include <carb/Types.h>
#include <vector>
#include <string>

#include "../Core/IsaacComponent.h"
#include "LidarComponent.h"
#include <carb/logging/Log.h>
#include <carb/profiler/Profile.h>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

LidarComponent::LidarComponent() : IsaacComponent()
{

    framework = carb::getFramework();
    if (!framework)
    {
        CARB_LOG_ERROR("*** Failed to get Carbonite framework\n");
        return;
    }

    mLidarInterface = framework->acquireInterface<omni::isaac::lidar::LidarInterface>();
    if (!mLidarInterface)
    {
        CARB_LOG_ERROR("Failed to acquire omni::isaac::lidar interface");
        return;
    }

    onComponentChange();
}

LidarComponent::~LidarComponent()
{
    framework->releaseInterface(mLidarInterface);
}

void LidarComponent::onStart()
{
    onComponentChange();
}
void LidarComponent::tick()
{
    CARB_PROFILE_ZONE(0, "REB LidarComponent Tick");

    mLidarHandle = mLidarInterface->getLidarHandle(mLidarPath.c_str());

    if (mLidarHandle == omni::isaac::lidar::kLidarInvalidHandle)
    {
        CARB_LOG_ERROR("Prim is not a LIDAR");
        return;
    }

    // Create the message
    IsaacMessage<isaac_message::RangeScan> scanMessage;

    auto scanMessageProto = scanMessage.initProto();

    int numColsTicked = mLidarInterface->getNumColsTicked(mLidarHandle);
    int numRows = mLidarInterface->getNumRows(mLidarHandle);
    int numBeams = numColsTicked * numRows;

    // Initialize the ranges tensor
    auto rangesTensor = scanMessageProto.initRanges();
    rangesTensor.setElementType(ElementType::UINT16);
    rangesTensor.initSizes(2);
    rangesTensor.setSizes({ numColsTicked, numRows });
    rangesTensor.setScanlineStride(0);
    rangesTensor.setDataBufferIndex(0);

    // Initialize the intensities tensor
    auto intensities = scanMessageProto.initIntensities();
    intensities.setElementType(ElementType::UINT8);
    intensities.initSizes(1);
    intensities.setSizes({ 0 });
    intensities.setScanlineStride(0);
    intensities.setDataBufferIndex(1);

    float* theta = mLidarInterface->getAzimuthData(mLidarHandle);
    float* phi = mLidarInterface->getZenithData(mLidarHandle);
    uint16_t* ranges = mLidarInterface->getDepthData(mLidarHandle);

    float maxRange = mLidarInterface->getMaxRange(mLidarHandle);

    scanMessageProto.setTheta(kj::ArrayPtr<const float>(theta, theta + numColsTicked));
    scanMessageProto.setPhi(kj::ArrayPtr<const float>(phi, phi + numRows));

    scanMessageProto.setRangeDenormalizer(maxRange);
    scanMessageProto.setIntensityDenormalizer(1.0f);
    scanMessageProto.setDeltaTime(0);
    scanMessageProto.setInvalidRangeThreshold(0.0);
    scanMessageProto.setOutOfRangeThreshold(maxRange);

    std::vector<std::vector<uint8_t>> buffers(1);
    buffers[0] = std::vector<uint8_t>(numBeams * sizeof(uint16_t));
    std::memcpy(buffers[0].data(), ranges, numBeams * sizeof(uint16_t));
    publish(mOutputComponent, mScanChannelName, scanMessageProto, isaac_message::RangeScanProtoId, buffers);
}
void LidarComponent::onComponentChange()
{
    // CARB_LOG_ERROR("LidarComponent Update");
    IsaacComponent::onComponentChange();

    if (auto attr = mPrim.GetAttribute(pxr::TfToken("outputComponent")))
    {
        attr.Get(&mOutputComponent);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("scanChannelName")))
    {
        attr.Get(&mScanChannelName);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("lidarPath")))
    {
        attr.Get(&mLidarPath);
    }
}
}
}
}
