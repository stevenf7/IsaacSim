// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "omni/isaac/bridge/Component.h"

#include <carb/InterfaceUtils.h>
#include <carb/dictionary/IDictionary.h>
#include <carb/dictionary/ISerializer.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <omni/renderer/IDebugDraw.h>

#include <functional>
#include <random>


namespace omni
{
namespace isaac
{
namespace dr
{

template <class PrimType>
class DRComponentBase : public utils::ComponentBase<PrimType>
{
public:
    DRComponentBase()
    {
        mRandomizationDurationInterval = -1;
        mIncludeChild = false;
        mDRLayerName = "";
        mCompName = "";
        mSeed = 12345;
        mCurrentSeed = 0;
        mDictionary = carb::getCachedInterface<carb::dictionary::IDictionary>();
        mSerializer = carb::getCachedInterface<carb::dictionary::ISerializer>();
    }
    virtual ~DRComponentBase()
    {
        // Empty
    }
    virtual void initialize(const PrimType& prim, pxr::UsdStageWeakPtr stage)
    {
        utils::ComponentBase<PrimType>::initialize(prim, stage);
    }
    virtual void onStart() = 0;
    virtual void tick() = 0;
    virtual void onComponentChange() = 0;

    double mRandomizationDurationInterval;
    double mLastTickTime = 0.0;
    bool mIncludeChild;
    std::vector<std::string> mIgnoreClassList;
    std::string mDRLayerName, mCompName;
    int mSeed, mCurrentSeed;
    std::default_random_engine mRandomGenerator;
    omni::renderer::SimplexBuffer mShapeDebugLineBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
    omni::renderer::RenderInstanceBuffer mShapeDebugRenderInstanceBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
    carb::dictionary::IDictionary* mDictionary = nullptr;
    carb::dictionary::ISerializer* mSerializer = nullptr;
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> mAllAttributeParamsMap;
    std::vector<std::string> distributionParamNames{ "mean", "stddev", "min", "max" };

protected:
    float randomRangeFloat(float low, float high)
    {
        std::uniform_real_distribution<float> p(low, high);
        return p(mRandomGenerator);
    }

    int randomRangeInt(int low, int high)
    {
        std::uniform_int_distribution<int> p(low, high);
        return p(mRandomGenerator);
    }

    float randomNormalFloat(float mean, float stddev, float low, float high)
    {
        std::normal_distribution<float> p(mean, stddev);
        return std::max(low, std::min(p(mRandomGenerator), high));
    }
    float randomFloat(std::string distribution, std::map<std::string, float>& distributionParams)
    {
        if (distribution == "uniform")
            return randomRangeFloat(distributionParams["min"], distributionParams["max"]);
        else if (distribution == "normal")
        {
            float minVal = distributionParams["mean"] - (2 * distributionParams["stddev"]);
            float maxVal = distributionParams["mean"] + (2 * distributionParams["stddev"]);
            if (distributionParams.find("min") != distributionParams.end())
                minVal = distributionParams["min"];
            if (distributionParams.find("max") != distributionParams.end())
                maxVal = distributionParams["max"];
            return randomNormalFloat(distributionParams["mean"], distributionParams["stddev"], minVal, maxVal);
        }
        return randomRangeFloat(distributionParams["min"], distributionParams["max"]);
    }

    bool ignoreClass(std::string prim, std::vector<std::string>& groupClassList)
    {
        for (std::string& ignoreClass : mIgnoreClassList)
        {
            if (prim.find(ignoreClass) != std::string::npos)
                return true;
        }
        if (mIgnoreClassList[0] == "all_except_group_classes")
        {
            for (std::string& groupClass : groupClassList)
            {
                if (prim.find(groupClass) != std::string::npos)
                    return false;
            }
            return true;
        }
        return false;
    }

    void createDebugLineList(size_t size, omni::renderer::IDebugDraw* mDebugDrawPtr)
    {
        if (mShapeDebugLineBuffer == omni::renderer::IDebugDraw::eInvalidBuffer)
        {
            mShapeDebugLineBuffer = mDebugDrawPtr->allocateLineBuffer(size);
            mShapeDebugRenderInstanceBuffer = mDebugDrawPtr->allocateRenderInstanceBuffer(mShapeDebugLineBuffer, 1);
            float transform[16] = {};
            transform[0] = 1.f;
            transform[1 + 4] = 1.f;
            transform[2 + 8] = 1.f;
            transform[3 + 12] = 1.f;

            mDebugDrawPtr->setRenderInstance(mShapeDebugRenderInstanceBuffer, 0, &transform[0], 0);
        }
    }

    void releaseDebugLineList(omni::renderer::IDebugDraw* mDebugDrawPtr)
    {
        if (mShapeDebugLineBuffer != omni::renderer::IDebugDraw::eInvalidBuffer)
        {
            mDebugDrawPtr->deallocateLineBuffer(mShapeDebugLineBuffer);
            mDebugDrawPtr->deallocateRenderInstanceBuffer(mShapeDebugRenderInstanceBuffer);
            mShapeDebugLineBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
            mShapeDebugRenderInstanceBuffer = omni::renderer::IDebugDraw::eInvalidBuffer;
        }
    }

    void setCustomDataFromJson(pxr::UsdStageWeakPtr stage, pxr::SdfPath primPath, std::string perAttributeJson)
    {
        pxr::VtDictionary userCustomData;
        const carb::dictionary::Item* jsonBase = mSerializer->createDictionaryFromStringBuffer(perAttributeJson.c_str());
        for (size_t child_idx = 0; child_idx < mDictionary->getItemChildCount(jsonBase); child_idx++)
        {
            pxr::VtDictionary userCustomDataL1;
            const carb::dictionary::Item* jsonLevel1 = mDictionary->getItemChildByIndex(jsonBase, child_idx);
            for (size_t child_l1_idx = 0; child_l1_idx < mDictionary->getItemChildCount(jsonLevel1); child_l1_idx++)
            {
                const carb::dictionary::Item* jsonLevel2 = mDictionary->getItemChildByIndex(jsonLevel1, child_l1_idx);
                const char* key = mDictionary->getItemName(jsonLevel2);
                const char* val = mDictionary->getStringBuffer(jsonLevel2);
                // CARB_LOG_WARN("%s : %s : %s", mDictionary->getItemName(jsonLevel1), key, val);
                userCustomDataL1[key] = val;
            }
            userCustomData[mDictionary->getItemName(jsonLevel1)] = userCustomDataL1;
        }
        pxr::UsdPrim mAttributeUsdPrim = stage->GetPrimAtPath(primPath);
        mAttributeUsdPrim.SetCustomData(userCustomData);
    }

    void getCustomDataAsDictionary(pxr::UsdStageWeakPtr stage, pxr::SdfPath primPath)
    {
        pxr::UsdPrim mAttributeUsdPrim = stage->GetPrimAtPath(primPath);
        pxr::VtDictionary customData = mAttributeUsdPrim.GetCustomData();
        auto dictionaryRoot = mDictionary->createItem(nullptr, "root", carb::dictionary::ItemType::eDictionary);
        for (auto iter = customData.begin(); iter != customData.end(); iter++)
        {
            std::unordered_map<std::string, std::string> attributeParamsMap;
            auto dictionaryNextLevel =
                mDictionary->createItem(dictionaryRoot, iter->first.c_str(), carb::dictionary::ItemType::eDictionary);
            pxr::VtDictionary customDataNextLevel = (iter->second).Get<pxr::VtDictionary>();
            std::string attrName = "";
            for (auto iterNextLevel = customDataNextLevel.begin(); iterNextLevel != customDataNextLevel.end();
                 iterNextLevel++)
            {
                auto nextLevelItem = mDictionary->createItem(
                    dictionaryNextLevel, iterNextLevel->first.c_str(), carb::dictionary::ItemType::eDictionary);
                std::string nextLevelValue = iterNextLevel->second.Get<std::string>();
                mDictionary->setString(nextLevelItem, nextLevelValue.c_str());
                attributeParamsMap[iterNextLevel->first] = nextLevelValue;
                if (iterNextLevel->first == "name")
                    attrName = nextLevelValue;
            }
            mAllAttributeParamsMap[attrName] = attributeParamsMap;
        }
        const char* serializedMessage =
            mSerializer->createStringBufferFromDictionary(dictionaryRoot, carb::dictionary::kSerializerOptionMakePretty);
        CARB_LOG_INFO("%s", serializedMessage);
        mSerializer->destroyStringBuffer(serializedMessage);
        mDictionary->destroyItem(dictionaryRoot);
    }

    void getDistributionParams(std::unordered_map<std::string, std::string>& attributeParamMap,
                               std::map<std::string, float>& distributionParams)
    {
        for (std::string paramName : distributionParamNames)
        {
            if (attributeParamMap.find(paramName) != attributeParamMap.end())
            {
                distributionParams[paramName] = std::stof(attributeParamMap[paramName]);
            }
        }
    }
};
}
}
}
