#pragma once

#include <string>
#include <vector>
namespace omni
{
namespace isaac
{
namespace utils
{

/**
 * @brief Base class which defines a component in an Application that is attached to a USD prim
 */
template <class PrimType>
class ComponentBase
{
public:
    /**
     * @brief Set the USD prim and stage for this application
     *
     * @param prim
     * @param stage
     */
    virtual void initialize(const PrimType& prim, pxr::UsdStageRefPtr stage)
    {
        mPrim = prim;
        mStage = stage;
    }

    /**
     * @brief Function that runs after start is pressed
     *
     */
    virtual void onStart() = 0;

    /**
     * @brief Called every frame
     *
     */
    virtual void tick() = 0;

    /**
     * @brief Called every time the Prim is changed
     *
     */
    virtual void onComponentChange() = 0;

protected:
    // USD reference to prim that stores settings for this component
    PrimType mPrim;
    // USD stage that the prim is in
    pxr::UsdStageRefPtr mStage = nullptr;

    double mTimeSeconds = 0; // current time in seconds
    int64_t mTimeNanoSeconds = 0; // current time in nano seconds
    double mTimeDelta = 0; // delta time for current tick
};

typedef ComponentBase<pxr::UsdPrim> Component;


}
}
}
