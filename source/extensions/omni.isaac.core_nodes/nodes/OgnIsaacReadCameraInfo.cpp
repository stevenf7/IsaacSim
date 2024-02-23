// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
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


#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/utils/UsdUtilities.h>

#include <CoreNodes.h>
#include <OgnIsaacReadCameraInfoDatabase.h>


namespace omni
{
namespace isaac
{
namespace core_nodes
{

class OgnIsaacReadCameraInfo
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnIsaacReadCameraInfoDatabase::sPerInstanceState<OgnIsaacReadCameraInfo>(nodeObj, instanceId);
        state.mStage = omni::usd::UsdContext::getContext()->getStage();
    }

    static bool compute(OgnIsaacReadCameraInfoDatabase& db)
    {
        auto& state = db.perInstanceState<OgnIsaacReadCameraInfo>();
        const std::string renderProductPath = std::string(db.tokenToString(db.inputs.renderProductPath()));
        pxr::UsdPrim camera = omni::isaac::utils::getCameraPrimFromRenderProduct(renderProductPath);

        if (!camera.IsValid())
        {
            CARB_LOG_ERROR("Render product path is invalid or outdated");
            return false;
        }

        pxr::UsdPrim renderProduct = state.mStage->GetPrimAtPath(pxr::SdfPath(renderProductPath));

        pxr::GfVec2i resolution;
        renderProduct.GetAttribute(pxr::TfToken("resolution")).Get(&resolution);

        auto value = resolution.GetArray();
        db.outputs.width() = value[0];
        db.outputs.height() = value[1];


        // width height
        if (db.outputs.height() == 0 || db.outputs.width() == 0)
        {
            CARB_LOG_ERROR("Camera width or height cannot be 0");
            return false;
        }


        camera.GetAttribute(pxr::TfToken("focalLength")).Get(&db.outputs.focalLength());
        camera.GetAttribute(pxr::TfToken("horizontalAperture")).Get(&db.outputs.horizontalAperture());

        float verticalAperture;
        camera.GetAttribute(pxr::TfToken("horizontalAperture")).Get(&verticalAperture);
        db.outputs.verticalAperture() = verticalAperture * (float(db.outputs.height()) / db.outputs.width());

        camera.GetAttribute(pxr::TfToken("horizontalApertureOffset")).Get(&db.outputs.horizontalOffset());
        camera.GetAttribute(pxr::TfToken("verticalApertureOffset")).Get(&db.outputs.verticalOffset());

        pxr::TfToken projection_type;
        camera.GetAttribute(pxr::TfToken("cameraProjectionType")).Get(&projection_type);
        if (projection_type.IsEmpty())
        {
            projection_type = pxr::TfToken("pinhole");
        }

        db.outputs.projectionType() = db.stringToToken(projection_type.GetText());


        omni::graph::core::ogn::array<float>& cameraFisheyeParams = db.outputs.cameraFisheyeParams();
        cameraFisheyeParams.resize(19);
        if (projection_type.GetString() != "pinhole")
        {
            camera.GetAttribute(pxr::TfToken("fthetaWidth")).Get(&cameraFisheyeParams[0]);
            camera.GetAttribute(pxr::TfToken("fthetaHeight")).Get(&cameraFisheyeParams[1]);
            camera.GetAttribute(pxr::TfToken("fthetaCx")).Get(&cameraFisheyeParams[2]);
            camera.GetAttribute(pxr::TfToken("fthetaCy")).Get(&cameraFisheyeParams[3]);
            camera.GetAttribute(pxr::TfToken("fthetaMaxFov")).Get(&cameraFisheyeParams[4]);
            camera.GetAttribute(pxr::TfToken("fthetaPolyA")).Get(&cameraFisheyeParams[5]);
            camera.GetAttribute(pxr::TfToken("fthetaPolyB")).Get(&cameraFisheyeParams[6]);
            camera.GetAttribute(pxr::TfToken("fthetaPolyC")).Get(&cameraFisheyeParams[7]);
            camera.GetAttribute(pxr::TfToken("fthetaPolyD")).Get(&cameraFisheyeParams[8]);
            camera.GetAttribute(pxr::TfToken("fthetaPolyE")).Get(&cameraFisheyeParams[9]);
            camera.GetAttribute(pxr::TfToken("fthetaPolyF")).Get(&cameraFisheyeParams[10]);
            camera.GetAttribute(pxr::TfToken("p0")).Get(&cameraFisheyeParams[11]);
            camera.GetAttribute(pxr::TfToken("p1")).Get(&cameraFisheyeParams[12]);
            camera.GetAttribute(pxr::TfToken("s0")).Get(&cameraFisheyeParams[13]);
            camera.GetAttribute(pxr::TfToken("s1")).Get(&cameraFisheyeParams[14]);
            camera.GetAttribute(pxr::TfToken("s2")).Get(&cameraFisheyeParams[15]);
            camera.GetAttribute(pxr::TfToken("s3")).Get(&cameraFisheyeParams[16]);
            camera.GetAttribute(pxr::TfToken("fisheyeResolutionBudget")).Get(&cameraFisheyeParams[17]);
            camera.GetAttribute(pxr::TfToken("fisheyeFrontFaceResolutionScale")).Get(&cameraFisheyeParams[18]);
        }

        db.outputs.cameraFisheyeParams() = cameraFisheyeParams;


        std::string physical_distortion;
        camera.GetAttribute(pxr::TfToken("physicalDistortionModel")).Get(&physical_distortion);
        if (!physical_distortion.empty())
        {
            db.outputs.physicalDistortionModel() = db.stringToToken(physical_distortion.c_str());
        }

        pxr::VtArray<float> physical_distortion_coefs;
        camera.GetAttribute(pxr::TfToken("physicalDistortionCoefficients")).Get(&physical_distortion_coefs);


        if (!physical_distortion_coefs.empty())
        {
            omni::graph::core::ogn::array<float>& physicalDistortionCoefficients =
                db.outputs.physicalDistortionCoefficients();
            physicalDistortionCoefficients.resize(physical_distortion_coefs.size());
            for (size_t i = 0; i < physicalDistortionCoefficients.size(); i++)
            {
                physicalDistortionCoefficients[i] = physical_distortion_coefs.data()[i];
            }
        }

        return true;
    }

private:
    pxr::UsdStageRefPtr mStage = nullptr;
};
REGISTER_OGN_NODE()
}
}
}
