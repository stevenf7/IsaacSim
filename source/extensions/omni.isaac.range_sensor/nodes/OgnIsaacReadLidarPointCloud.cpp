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

#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/utils/BaseResetNode.h>
#include <rangeSensorSchema/lidar.h>
#include <rangeSensorSchema/rangeSensor.h>

#include <OgnIsaacReadLidarPointCloudDatabase.h>
#include <RangeSensorInterface.h>

namespace omni
{
namespace isaac
{
namespace core_nodes
{

class OgnIsaacReadLidarPointCloud : public BaseResetNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnIsaacReadLidarPointCloudDatabase::sInternalState<OgnIsaacReadLidarPointCloud>(nodeObj);

        state.mLidarSensorInterface = carb::getCachedInterface<omni::isaac::range_sensor::LidarSensorInterface>();

        if (!state.mLidarSensorInterface)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::range_sensor interface");
            return;
        }
    }

    static bool compute(OgnIsaacReadLidarPointCloudDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.internalState<OgnIsaacReadLidarPointCloud>();

        if (state.mFirstFrame)
        {
            const auto& prim = db.inputs.lidarPrim();
            const char* primPath;
            if (prim.size() > 0)
            {
                primPath = omni::fabric::toSdfPath(prim[0]).GetText();
            }
            else
            {
                db.logError("no prim path found for the lidar");
                return false;
            }

            state.mFirstFrame = false;

            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }

            state.mUnitScale = UsdGeomGetStageMetersPerUnit(stage);

            // Verify we have a valid lidar prim
            pxr::UsdPrim targetPrim = stage->GetPrimAtPath(pxr::SdfPath(primPath));
            if (!targetPrim.IsA<pxr::RangeSensorLidar>())
            {
                db.logError("Prim is not a Lidar Prim");
                return false;
            }

            state.mRangeSensorPrim = pxr::RangeSensorRangeSensor(targetPrim);

            if (!state.mLidarSensorInterface->isLidarSensor(primPath))
            {
                db.logError("Prim is not registered with Lidar extension");
                return false;
            }

            state.mLidarPrimPath = primPath;

            return true;
        }

        state.readLidarPointCloud(db);
        return true;
    }


    void readLidarPointCloud(OgnIsaacReadLidarPointCloudDatabase& db)
    {
        float maxRange = 100;

        omni::isaac::utils::safeGetAttribute(mRangeSensorPrim.GetMaxRangeAttr(), maxRange);

        carb::Float3* lidarData = mLidarSensorInterface->getPointCloud(mLidarPrimPath);
        // float* theta = mLidarSensorInterface->getAzimuthData(mLidarPrimPath);
        float* ranges = mLidarSensorInterface->getLinearDepthData(mLidarPrimPath);

        if (!ranges || !lidarData)
        {
            return;
        }

        int numColsTicked = mLidarSensorInterface->getNumColsTicked(mLidarPrimPath);
        int numCols = mLidarSensorInterface->getNumCols(mLidarPrimPath);
        int numRows = mLidarSensorInterface->getNumRows(mLidarPrimPath);

        size_t numBeams = numColsTicked * numRows;
        size_t numBeamsTotal = numRows * numCols;

        uint64_t curr_sequence_num = mLidarSensorInterface->getSequenceNumber(mLidarPrimPath);


        if (curr_sequence_num == mPrevSequenceNumber)
        {
            return;
        }

        if (curr_sequence_num < mPrevSequenceNumber)
        {
            mResetPCL = true;
        }

        mPrevSequenceNumber = curr_sequence_num;

        if (mResetPCL)
        {
            mPointsData.clear();
            mNumBeamsRemainingPCL = numBeamsTotal;
            mResetPCL = false;
        }


        if (mNumBeamsRemainingPCL > numBeams)
        {
            for (size_t i = 0; i < numBeams; i++)
            {

                if (ranges[i] >= maxRange)
                {
                    continue;
                }

                GfVec3f point = { lidarData[i].x, lidarData[i].y, lidarData[i].z };
                mPointsData.push_back(point * mUnitScale);
            }
            mNumBeamsRemainingPCL -= numBeams;
        }
        else if (mNumBeamsRemainingPCL <= numBeams)
        {

            // Save data up to maximum FOV
            size_t i = 0;
            for (i = 0; i < mNumBeamsRemainingPCL; i++)
            {
                if (ranges[i] >= maxRange)
                {
                    continue;
                }

                GfVec3f point = { lidarData[i].x, lidarData[i].y, lidarData[i].z };
                mPointsData.push_back(point * mUnitScale);
            }

            db.outputs.data().resize(mPointsData.size());

            memcpy(db.outputs.data().data(), &mPointsData[0], mPointsData.size() * sizeof(GfVec3f));

            db.outputs.execOut() = kExecutionAttributeStateEnabled;


            mPointsData.clear();

            // Save remaining data
            size_t numBeamsOffset = numBeams - mNumBeamsRemainingPCL;
            for (size_t j = 0; j < numBeamsOffset; j++)
            {
                if (ranges[i] >= maxRange)
                {
                    i++;
                    continue;
                }
                GfVec3f point = { lidarData[i].x, lidarData[i].y, lidarData[i].z };
                mPointsData.push_back(point * mUnitScale);
                i++;
            }
            mNumBeamsRemainingPCL = numBeamsTotal - numBeamsOffset;
        }
    }
    static bool updateNodeVersion(const GraphContextObj& context, const NodeObj& nodeObj, int oldVersion, int newVersion)
    {
        if (oldVersion < newVersion)
        {
            const INode* const iNode = nodeObj.iNode;
            if (oldVersion < 2)
            {
                iNode->removeAttribute(nodeObj, "outputs:pointCloudData");
                CARB_LOG_ERROR(
                    "outputs:pointCloudData renamed to outputs:data, downstream connections will need to be re-connected");
            }
            return true;
        }
        return false;
    }
    virtual void reset()
    {
        mResetPCL = true;
        mFirstFrame = true;
    }


private:
    omni::isaac::range_sensor::LidarSensorInterface* mLidarSensorInterface = nullptr;
    // pxr::RangeSensorLidar mLidarPrim;
    pxr::RangeSensorRangeSensor mRangeSensorPrim;

    const char* mLidarPrimPath = nullptr;

    std::vector<GfVec3f> mPointsData;

    uint64_t mPrevSequenceNumber = 0;

    bool mResetPCL = true;
    size_t mNumBeamsRemainingPCL;

    bool mFirstFrame = true;

    double mUnitScale;
};

REGISTER_OGN_NODE()
} // nodes
} // graph
} // omni
