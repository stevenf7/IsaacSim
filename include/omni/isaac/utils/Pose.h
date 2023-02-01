#pragma once

#include "Conversions.h"
#include "UsdUtilities.h"

#include <foundation/PxTransform.h>
#include <omni/usd/UsdUtils.h>
#include <physx/include/foundation/PxTransform.h>
#include <usdrt/scenegraph/usd/rt/xformable.h>


using namespace omni::isaac::utils::conversions;
using namespace omni::isaac::utils;
namespace omni
{
namespace isaac
{

namespace utils
{

namespace pose
{

static usdrt::GfMatrix4d computeWorldXformNoCache(pxr::UsdStageRefPtr usdStage,
                                                  usdrt::UsdStageRefPtr usdrtStage,
                                                  const pxr::SdfPath& path,
                                                  pxr::UsdTimeCode timecode = pxr::UsdTimeCode::Default())
{
    if (path.IsRootPrimPath())
    {
        return usdrt::GfMatrix4d(1.0);
    }
    if (usdrtStage->HasPrimAtPath(path.GetString()))
    {
        usdrt::UsdPrim usdrtPrim = usdrtStage->GetPrimAtPath(path.GetString());
        usdrt::RtXformable usdrtXformable = usdrt::RtXformable(usdrtPrim);

        if (usdrtXformable.HasWorldXform())
        {
            usdrt::GfVec3d worldPos;
            usdrt::GfQuatf worldOrient;
            usdrt::GfVec3f worldScale;
            usdrtXformable.GetWorldPositionAttr().Get(&worldPos, usdrt::UsdTimeCode(timecode.GetValue()));
            usdrtXformable.GetWorldOrientationAttr().Get(&worldOrient, usdrt::UsdTimeCode(timecode.GetValue()));
            usdrtXformable.GetWorldScaleAttr().Get(&worldScale, usdrt::UsdTimeCode(timecode.GetValue()));

            usdrt::GfMatrix4d rot, scale, result;
            scale.SetScale(usdrt::GfVec3d(worldScale));
            rot.SetRotate(usdrt::GfQuatd(worldOrient));
            result = scale * rot;
            result.SetTranslateOnly(worldPos);
            return result;
        }
        else if (usdrtXformable.HasLocalXform())
        {
            usdrt::GfMatrix4d localMat(1);
            usdrtXformable.GetLocalMatrixAttr().Get(&localMat, usdrt::UsdTimeCode(timecode.GetValue()));
            const pxr::SdfPath parentPath = usdStage->GetPrimAtPath(path).GetParent().GetPath();
            usdrt::GfMatrix4d parentXform = computeWorldXformNoCache(usdStage, usdrtStage, parentPath, timecode);

            return localMat * parentXform;
        }
    }
    {
        pxr::UsdPrim prim = usdStage->GetPrimAtPath(path);

        usdrt::GfMatrix4d localMat(1.0);
        if (PXR_NS::UsdGeomXformable xformable = PXR_NS::UsdGeomXformable(prim))
        {
            bool dontCare;
            xformable.GetLocalTransformation(reinterpret_cast<PXR_NS::GfMatrix4d*>(&localMat), &dontCare, timecode);
        }
        usdrt::GfMatrix4d parentXform =
            computeWorldXformNoCache(usdStage, usdrtStage, prim.GetParent().GetPath(), timecode);

        return localMat * parentXform;
    }
}

}
}
}
}
