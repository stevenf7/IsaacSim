// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "DRComponentBase.h"

#include <carb/Framework.h>
#include <carb/Types.h>

namespace omni
{
namespace isaac
{
namespace dr
{

DRComponentBase::DRComponentBase()
{
    mRandomizationDurationInterval = -1;
    mIncludeChild = false;
    mDRLayerName = "";
    mCompName = "";
}
DRComponentBase::~DRComponentBase()
{
    // Empty
}

void DRComponentBase::initialize(const pxr::UsdPrim& prim, pxr::UsdStageRefPtr stage)
{
    utils::Component::initialize(prim, stage);
}

}
}
}
