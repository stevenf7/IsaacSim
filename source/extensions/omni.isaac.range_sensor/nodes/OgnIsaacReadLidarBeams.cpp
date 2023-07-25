// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "omni/isaac/utils/UsdUtilities.h"

#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <omni/isaac/utils/BaseResetNode.h>
#include <rangeSensorSchema/lidar.h>
#include <rangeSensorSchema/rangeSensor.h>

#include <OgnIsaacReadLidarBeamsDatabase.h>

namespace omni
{
namespace isaac
{
namespace core_nodes
{

class OgnIsaacReadLidarBeams : public BaseResetNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnIsaacReadLidarBeamsDatabase::sInternalState<OgnIsaacReadLidarBeams>(nodeObj);

        state.mLidarSensorInterface = carb::getCachedInterface<omni::isaac::range_sensor::LidarSensorInterface>();

        if (!state.mLidarSensorInterface)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::range_sensor interface");
            return;
        }
    }

    static bool compute(OgnIsaacReadLidarBeamsDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.internalState<OgnIsaacReadLidarBeams>();

        if (state.mFirstFrame)
        {

            state.mFirstFrame = false;

            const char* primPath = db.inputs.lidarPrim.path();

            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }

            // Verify we have a valid lidar prim
            pxr::UsdPrim targetPrim = stage->GetPrimAtPath(pxr::SdfPath(primPath));
            if (!targetPrim.IsA<pxr::RangeSensorLidar>())
            {
                db.logError("Prim is not a Lidar Prim");
                return false;
            }

            state.mLidarPrim = pxr::RangeSensorLidar(targetPrim);
            state.mRangeSensorPrim = pxr::RangeSensorRangeSensor(targetPrim);

            if (!state.mLidarSensorInterface->isLidarSensor(primPath))
            {
                db.logError("Prim is not registered with Lidar extension");
                return false;
            }

            state.mLidarPrimPath = primPath;

            return true;
        }

        state.readLidar(db);
        return true;
    }


    void readLidar(OgnIsaacReadLidarBeamsDatabase& db)
    {
        if (!mLidarSensorInterface->isLidarSensor(mLidarPrimPath))
        {
            db.logError("Invalid Lidar Reference, Prim is not registered with Lidar extension");
            return;
        }

        auto& numRows = db.outputs.numRows();
        auto& numCols = db.outputs.numCols();

        numRows = mLidarSensorInterface->getNumRows(mLidarPrimPath);
        numCols = mLidarSensorInterface->getNumCols(mLidarPrimPath);

        int numColsTicked = mLidarSensorInterface->getNumColsTicked(mLidarPrimPath);

        size_t numBeams = numColsTicked * numRows;

        float* azimuthData = mLidarSensorInterface->getAzimuthData(mLidarPrimPath);
        // float* zenithData = mLidarSensorInterface->getZenithData(mLidarPrimPath);
        float* beamTimes = mLidarSensorInterface->getBeamTimeData(mLidarPrimPath);
        float* ranges = mLidarSensorInterface->getLinearDepthData(mLidarPrimPath);
        uint8_t* intensities = mLidarSensorInterface->getIntensityData(mLidarPrimPath);

        if (!azimuthData || !beamTimes || !ranges || !intensities)
        {
            return;
        }

        auto& horizontalFov = db.outputs.horizontalFov();
        auto& horizontalResolution = db.outputs.horizontalResolution();
        auto& depthRange = db.outputs.depthRange();
        auto& rotationRate = db.outputs.rotationRate();
        auto& verticalFov = db.outputs.verticalFov();
        auto& verticalResolution = db.outputs.verticalResolution();

        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetHorizontalFovAttr(), horizontalFov);
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetHorizontalResolutionAttr(), horizontalResolution);
        omni::isaac::utils::safeGetAttribute(mRangeSensorPrim.GetMinRangeAttr(), depthRange[0]);
        omni::isaac::utils::safeGetAttribute(mRangeSensorPrim.GetMaxRangeAttr(), depthRange[1]);
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetRotationRateAttr(), rotationRate);
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetVerticalFovAttr(), verticalFov);
        omni::isaac::utils::safeGetAttribute(mLidarPrim.GetVerticalResolutionAttr(), verticalResolution);

        size_t numBeamsTotal = numRows * numCols;

        if (horizontalFov <= 0.0)
        {
            db.logError("Lidar Prim %s: Horizontal FOV must be greater than 0.0", mLidarPrimPath);
            return;
        }
        if (horizontalFov > 360.0)
        {
            db.logError("Lidar Prim %s: Horizontal FOV must be less than or equal to 360.0", mLidarPrimPath);
            return;
        }
        if (horizontalResolution <= 0.0)
        {
            db.logError("Lidar Prim %s: Horizontal Resolution must be greater than 0.0", mLidarPrimPath);
            return;
        }
        if (rotationRate < 0.0)
        {
            db.logError("Lidar Prim %s: Rotation Rate must be equal to or greater than 0.0", mLidarPrimPath);
            return;
        }
        if (verticalFov <= 0.0)
        {
            db.logError("Lidar Prim %s: Vertical FOV must be greater than 0.0", mLidarPrimPath);
            return;
        }
        if (verticalResolution <= 0.0)
        {
            db.logError("Lidar Prim %s: Vertical Resolution must be greater than 0.0", mLidarPrimPath);
            return;
        }

        uint64_t curr_sequence_num = mLidarSensorInterface->getSequenceNumber(mLidarPrimPath);

        if (curr_sequence_num < mPrevSequenceNumber)
        {
            mResetLaserScan = true;
            mPrevSequenceNumber = curr_sequence_num;
        }

        carb::Float2 azimuthRange = mLidarSensorInterface->getAzimuthRange(mLidarPrimPath);
        carb::Float2 zenithRange = mLidarSensorInterface->getZenithRange(mLidarPrimPath);

        auto& azimuthRangeOutput = db.outputs.azimuthRange();
        auto& zenithRangeOutput = db.outputs.zenithRange();

        azimuthRangeOutput[0] = azimuthRange.x;
        azimuthRangeOutput[1] = azimuthRange.y;

        zenithRangeOutput[0] = zenithRange.x;
        zenithRangeOutput[1] = zenithRange.y;

        if (mResetLaserScan)
        {
            mBeamTimeData.clear();
            mIntensitiesData.clear();
            mRangesData.clear();

            mNumBeamsRemaining = numBeamsTotal;

            bool foundStart = false;
            for (mBeamIdx = 0; mBeamIdx < numBeams; mBeamIdx++)
            {
                if (azimuthData[mBeamIdx] == azimuthRange.x)
                {
                    foundStart = true;
                    break;
                }
            }
            if (!foundStart)
            {
                return;
            }
            mResetLaserScan = false;
        }

        if (mNumBeamsRemaining > numBeams)
        {
            for (size_t i = mBeamIdx; i < numBeams; i++)
            {
                mBeamTimeData.push_back(beamTimes[i]);
                mIntensitiesData.push_back(intensities[i]);
                mRangesData.push_back(ranges[i]);
                mNumBeamsRemaining--;
            }
            mBeamIdx = 0;
        }

        else if (mNumBeamsRemaining <= numBeams)
        {

            // Save data up to maximum FOV
            size_t idx;
            for (idx = 0; idx < mNumBeamsRemaining; idx++)
            {
                mBeamTimeData.push_back(beamTimes[idx]);
                mIntensitiesData.push_back(intensities[idx]);
                mRangesData.push_back(ranges[idx]);
            }

            size_t buffSize = mRangesData.size();

            db.outputs.beamTimeData.resize(buffSize);
            db.outputs.linearDepthData.resize(buffSize);
            db.outputs.intensitiesData.resize(buffSize);

            std::memcpy(db.outputs.beamTimeData().data(), &mBeamTimeData[0], mBeamTimeData.size() * sizeof(float));
            std::memcpy(db.outputs.linearDepthData().data(), &mRangesData[0], mRangesData.size() * sizeof(float));
            std::memcpy(
                db.outputs.intensitiesData().data(), &mIntensitiesData[0], mIntensitiesData.size() * sizeof(uint8_t));

            db.outputs.execOut() = kExecutionAttributeStateEnabled;

            mPrevSequenceNumber = curr_sequence_num;

            // Reset fields for new lidar scan
            mBeamTimeData.clear();
            mRangesData.clear();
            mIntensitiesData.clear();

            if (idx < numBeams)
            {
                if (azimuthData[idx] != azimuthRange.x)
                {
                    mResetLaserScan = true;
                    return;
                }
            }

            // Save remaining data
            size_t numBeamsOffset = numBeams - mNumBeamsRemaining;
            for (size_t j = 0; j < numBeamsOffset; j++)
            {
                mBeamTimeData.push_back(beamTimes[idx]);
                mIntensitiesData.push_back(intensities[idx]);
                mRangesData.push_back(ranges[idx]);
                idx++;
            }
            mNumBeamsRemaining = numBeamsTotal - numBeamsOffset;
        }
    }

    virtual void reset()
    {
        mResetLaserScan = true;
        mFirstFrame = true;
    }


private:
    omni::isaac::range_sensor::LidarSensorInterface* mLidarSensorInterface = nullptr;
    pxr::RangeSensorLidar mLidarPrim;
    pxr::RangeSensorRangeSensor mRangeSensorPrim;

    const char* mLidarPrimPath = nullptr;

    std::vector<uint8_t> mIntensitiesData;
    std::vector<float> mRangesData;
    std::vector<float> mBeamTimeData;

    uint64_t mPrevSequenceNumber = 0;

    bool mResetLaserScan = true;
    size_t mNumBeamsRemaining;

    size_t mBeamIdx = 0;

    bool mFirstFrame = true;
};

REGISTER_OGN_NODE()
} // nodes
} // graph
} // omni
