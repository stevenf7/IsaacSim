#include "../RangeSensorUtils.h"
#include "../core/RangeSensorComponent.h"
#include "UltrasonicArrayEmissionTimer.h"
#include "plugins/core/UsdUtilities.h"

#include <omni/usd/UtilsIncludes.h>
//
#include <omni/usd/UsdUtils.h>
//
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <pxr/base/gf/vec2i.h>
#include <pxr/usd/usd/inherits.h>
#include <rangeSensorSchema/ultrasonicFiringGroup.h>

#include <vector>

namespace omni
{
namespace isaac
{
namespace range_sensor
{

class UltrasonicFiringGroup : public utils::ComponentBase<pxr::RangeSensorSchemaUltrasonicFiringGroup>
{
public:
    UltrasonicFiringGroup()
    {
    }


    void initialize(const pxr::RangeSensorSchemaUltrasonicFiringGroup& prim, pxr::UsdStageWeakPtr stage)
    {
        utils::ComponentBase<pxr::RangeSensorSchemaUltrasonicFiringGroup>::initialize(prim, stage);

        onComponentChange();
    }


    void onStart()
    {
    }

    void tick()
    {
    }

    void onComponentChange()
    {
        isaac::utils::safeGetAttribute(mPrim.GetEmitterModesAttr(), mEmitterModes);
        isaac::utils::safeGetAttribute(mPrim.GetReceiverModesAttr(), mReceiverModes);
    }

    pxr::VtArray<pxr::GfVec2i> mEmitterModes;
    pxr::VtArray<pxr::GfVec2i> mReceiverModes;

private:
};
}
}
}
