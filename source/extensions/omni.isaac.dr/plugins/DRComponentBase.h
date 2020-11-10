#pragma once

#include "plugins/core/Component.h"

#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

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

    float mRandomizationDurationInterval;
    float mLastTickTime = 0.0f;
    bool mIncludeChild;
    std::vector<std::string> mIgnoreClassList;
    std::string mDRLayerName, mCompName;
    int mSeed, mCurrentSeed;
    std::default_random_engine mRandomGenerator;

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
};
}
}
}
