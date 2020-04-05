#pragma once


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

class DRComponentBase
{
public:
    DRComponentBase();
    virtual ~DRComponentBase() = 0;
    void initialize(const pxr::UsdPrim& prim, pxr::UsdStageRefPtr stage);
    virtual void onStart() = 0;
    virtual void tick(const float dt = 0.0f) = 0;
    virtual void onComponentChange() = 0;

    float mRandomizationDurationInterval;
    float mLastTickTime = 0.0f;
    bool mIncludeChild;
    std::vector<std::string> mIgnoreClassList;
    std::string mDRLayerName, mCompName;

protected:
    static float randomRange(float low, float high)
    {
        static std::default_random_engine rng(0xBEEF);
        std::uniform_real_distribution<float> p(low, high);
        return p(rng);
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

    // USD reference to prim that stores settings for this component
    pxr::UsdPrim mPrim;
    pxr::UsdStageWeakPtr mStage;
};
}
}
}
