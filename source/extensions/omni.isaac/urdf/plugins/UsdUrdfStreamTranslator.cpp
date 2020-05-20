// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "UsdUrdfStream.h"

#include <PhysicsSchema/articulationAPI.h>
#include <PhysicsSchema/articulationJointAPI.h>
#include <PhysicsSchema/collisionAPI.h>
#include <PhysicsSchema/driveAPI.h>
#include <PhysicsSchema/physicsJoint.h>
#include <PhysicsSchema/limitAPI.h>
#include <PhysicsSchema/massAPI.h>
#include <PhysicsSchema/physicsScene.h>
#include <PhysicsSchema/fixedPhysicsJoint.h>
#include <PhysicsSchema/prismaticPhysicsJoint.h>
#include <PhysicsSchema/revolutePhysicsJoint.h>
#include <PhysicsSchema/sphericalPhysicsJoint.h>
#include <PhysicsSchemaTools/UsdTools.h>

#include <PhysxSchema/physxMeshCollisionAPI.h>

// #include <PxPhysicsAPI.h>

#include <NvIsaacRobotModel.h>
#include <cmath>

using namespace pxr;

#define MY_DEBUG_CRAP 1
#if MY_DEBUG_CRAP
#    include <fstream>
#endif

#define COLLISION_MESH_NAME "/collisionMesh"
#define VISUAL_MESH_NAME "/visualMesh"
#define PHYSICS_BODY_NAME "/physicsBody"

namespace omni
{
namespace isaac
{
namespace urdf
{

typedef void (*addJointFunction)(const UsdStagePtr& stage,
                                 const std::string& jointName,
                                 const std::string& actor0,
                                 const std::string& actor1,
                                 const pxr::GfVec3f& localPos0,
                                 const pxr::GfQuatf& localRot0,
                                 const pxr::GfVec3f& localPos1,
                                 const pxr::GfQuatf& localRot1,
                                 float breakForce,
                                 float breakTorque);

// Make a path name that is not already used.
std::string GetNewSdfPathString(UsdStageWeakPtr stage, std::string path, int nameClashNum = -1)
{
    bool appendedNumber = false;
    int numberAppended = std::max<int>(nameClashNum, 0);
    size_t indexOfNumber = 0;
    if (stage->GetPrimAtPath(SdfPath(path)))
    {
        appendedNumber = true;
        std::string name = SdfPath(path).GetName();
        size_t last_ = name.find_last_of('_');
        indexOfNumber = path.length() + 1;
        if (last_ == std::string::npos)
        {
            // no '_' found, so just tack on the end.
            path += "_" + std::to_string(numberAppended);
        }
        else
        {
            // There was a _, if the last part of that is a number
            // then replace that number with one higher or nameClashNum,
            // or just tack on the number if it is last character.
            if (last_ == name.length() - 1)
            {
                path += "_" + std::to_string(numberAppended);
            }
            else
            {
                char* p;
                std::string after_ = name.substr(last_ + 1, name.length());
                long converted = strtol(after_.c_str(), &p, 10);
                if (*p)
                {
                    // not a number
                    path += "_" + std::to_string(numberAppended);
                }
                else
                {

                    numberAppended = nameClashNum == -1 ? converted + 1 : nameClashNum;
                    indexOfNumber = path.length() - name.length() + last_ + 1;
                    path = path.substr(0, indexOfNumber);
                    path += std::to_string(numberAppended);
                }
            }
        }
    }
    if (appendedNumber)
    {
        // we just added a number, so we have to make sure the new path is unique.
        while (stage->GetPrimAtPath(SdfPath(path)))
        {
            path = path.substr(0, indexOfNumber);
            numberAppended += 1;
            path += std::to_string(numberAppended);
        }
    }
#if 0
	else
	{
		while (stage->GetPrimAtPath(SdfPath(path))) path += ":" + std::to_string(nameClashNum);
	}
#endif
    return path;
}
TfToken getAxis(NvIsaac::IRobotSkeleton::DOFAxis inAxis)
{
    switch (inAxis)
    {
    case NvIsaac::IRobotSkeleton::DOFAxis::kLinearX:
        return TfToken("transX");
    case NvIsaac::IRobotSkeleton::DOFAxis::kLinearY:
        return TfToken("transY");
    case NvIsaac::IRobotSkeleton::DOFAxis::kLinearZ:
        return TfToken("transZ");
    case NvIsaac::IRobotSkeleton::DOFAxis::kAngularX:
        return TfToken("rotX");
    case NvIsaac::IRobotSkeleton::DOFAxis::kAngularY:
        return TfToken("rotY");
    case NvIsaac::IRobotSkeleton::DOFAxis::kAngularZ:
        return TfToken("rotZ");
    }
}
TfToken getAxisXYZ(NvIsaac::IRobotSkeleton::DOFAxis inAxis)
{
    switch (inAxis)
    {
    case NvIsaac::IRobotSkeleton::DOFAxis::kLinearX:
    case NvIsaac::IRobotSkeleton::DOFAxis::kAngularX:
        return TfToken("X");
    case NvIsaac::IRobotSkeleton::DOFAxis::kLinearY:
    case NvIsaac::IRobotSkeleton::DOFAxis::kAngularY:
        return TfToken("Y");
    case NvIsaac::IRobotSkeleton::DOFAxis::kLinearZ:
    case NvIsaac::IRobotSkeleton::DOFAxis::kAngularZ:
        return TfToken("Z");
    }
}
GfQuatf getQ(const NvIsaac::Transform& pose)
{
    return GfQuatf(pose.q.w, GfVec3f(pose.q.x, pose.q.y, pose.q.z));
}
GfVec3f getP(const NvIsaac::Transform& pose)
{
    return GfVec3f(pose.p.x, pose.p.y, pose.p.z);
}

bool SetToPose(UsdGeomXformable const& gprim, const NvIsaac::Transform& pose, float distanceScale)
{
    // For insurance, we will make sure there aren't any ordered ops
    // before we start
    gprim.ClearXformOpOrder();

    UsdGeomXformOp trans;


    if (!(trans = gprim.AddTransformOp()))
    {
        return false;
    }
    pxr::GfMatrix4d mat;
    mat.SetTranslateOnly(distanceScale * GfVec3d(pose.p.x, pose.p.y, pose.p.z));
    mat.SetRotateOnly(GfQuatf(pose.q.w, GfVec3f(pose.q.x, pose.q.y, pose.q.z)));
    bool retVal = (trans.Set(mat, UsdTimeCode::Default()));
    return retVal;
}


template <class SubMesh>
const NvIsaac::IRobotGraphics::Material* GetMaterial(const SubMesh*)
{
    return nullptr;
}
template <>
const NvIsaac::IRobotGraphics::Material* GetMaterial(const NvIsaac::IRobotGraphics::SubMesh* sm)
{
    return sm ? &sm->getMaterial() : nullptr;
}

void CreateMaterial(UsdGeomGprim& gprim, const NvIsaac::IRobotGraphics::Material* smMat, SdfPath path, UsdStageWeakPtr stage)
{
    VtVec3fArray color(1);
    if (!smMat || (smMat && !stage))
    {
        color[0] = GfVec3f(1, 0, 0);
        gprim.CreateDisplayColorPrimvar().Set(color);
        VtFloatArray opacity(1);
        opacity[0] = 0.25f;
        gprim.CreateDisplayOpacityPrimvar().Set(opacity);
        return;
    }
    /*
    The interface to Nv's Material here is:
      virtual const char* getName() const = 0;
      virtual const Color& getAmbientColor() const = 0;
      virtual const Color& getDiffuseColor() const = 0;
      virtual const Color& getEmissiveColor() const = 0;
      virtual const Color& getSpecularColor() const = 0;
      virtual float getShininess() const = 0;
      virtual const char* getTextureName() const = 0;
    Which does not have a direct translation to "UsdPreviewSurface", but lets do our best
    or learn the usd shading pipeline better in order to make urdf shading parameters
    more readily presentable.
      */
    NvIsaac::IRobotGraphics::Color cd = smMat->getDiffuseColor();
    color[0] = GfVec3f(cd.r, cd.g, cd.b);
    gprim.CreateDisplayColorPrimvar().Set(color);
    // TODO, Once we start using material in graphene, then set these correctly.
#if 1
    // create the material as a container in which to put the shaders
    SdfPath matPath = SdfPath(path.GetString() + "Mat");
    UsdShadeMaterial meshMat = UsdShadeMaterial::Define(stage, matPath);

    // create a surface shader and attach it to the material.
    UsdShadeShader pbrShader = UsdShadeShader::Define(
        stage, SdfPath(path.GetString() + TfMakeValidIdentifier(std::string(smMat->getName()) + "Shader")));
    pbrShader.CreateIdAttr(VtValue(UsdImagingTokens->UsdPreviewSurface));

    // UsdPreviewSurface is defined here:
    // https://graphics.pixar.com/usd/docs/UsdPreviewSurface-Proposal.html#UsdPreviewSurfaceProposal-PreviewSurface
    pbrShader.CreateInput(TfToken("diffuseColor"), SdfValueTypeNames->Color3f).Set(GfVec3f(cd.r, cd.g, cd.b));

    // note: not in UsdPreviewSurface Specs
    NvIsaac::IRobotGraphics::Color ca = smMat->getAmbientColor();
    pbrShader.CreateInput(TfToken("ambientColor"), SdfValueTypeNames->Color3f).Set(GfVec3f(ca.r, ca.g, ca.b));

    NvIsaac::IRobotGraphics::Color ce = smMat->getEmissiveColor();
    pbrShader.CreateInput(TfToken("emissiveColor"), SdfValueTypeNames->Color3f).Set(GfVec3f(ce.r, ce.g, ce.b));

    NvIsaac::IRobotGraphics::Color cs = smMat->getSpecularColor();
    pbrShader.CreateInput(TfToken("useSpecularWorkflow"), SdfValueTypeNames->Int).Set(1);
    pbrShader.CreateInput(TfToken("specularColor"), SdfValueTypeNames->Color3f).Set(GfVec3f(cs.r, cs.g, cs.b));

    // note: not in UsdPreviewSurface Specs
    float shininess = smMat->getShininess();
    pbrShader.CreateInput(TfToken("shininess"), SdfValueTypeNames->Float).Set(shininess);

    auto output = meshMat.CreateSurfaceOutput();
    output.ConnectToSource(pbrShader, TfToken("surface"));

    UsdShadeMaterialBindingAPI mbi(gprim);
    mbi.Bind(meshMat);
#endif
}


std::string FindSubstringName(const char* param1)
{
    int begin = 0;
    int length = 0;
    if (!param1)
    {
        return "";
    }
    // is this an implicit?
    if (param1[0] == '@')
    {
        begin = 1;
        length = 0;
        while (param1[length + 1] != 0 && param1[length + 1] != '(')
            length++;
        return std::string(param1).substr(begin, length);
    }
    // assume this is a file
    // then begin is the last known / or \ and length is the distance from that to the end of the file name (keep
    // extension?)
    int lastDot = -1;
    while (param1[length])
    {
        if (param1[length] == '\\' || param1[length] == '/')
            begin = length + 1;
        if (param1[length] == '.')
            lastDot = length;
        length += 1;
    }
    std::string retMe = std::string(param1).substr(begin, length - begin);
    if (lastDot >= 0)
        retMe[lastDot - begin] = '_';
    return retMe;
}


template <class Mesh>
int GetSubMeshCount(const Mesh*);
template <>
int GetSubMeshCount(const NvIsaac::IRobotPhysics::Mesh* mesh)
{
    return mesh->getConvexHullCount();
}
template <>
int GetSubMeshCount(const NvIsaac::IRobotGraphics::Mesh* mesh)
{
    return mesh->getSubMeshCount();
}

template <class Mesh, class SubMesh>
const SubMesh* GetSubMesh(const Mesh*, int);
template <>
const NvIsaac::IRobotPhysics::TriangleMesh* GetSubMesh(const NvIsaac::IRobotPhysics::Mesh* mesh, int i)
{
    return mesh->getConvexHull(i);
}
template <>
const NvIsaac::IRobotGraphics::SubMesh* GetSubMesh(const NvIsaac::IRobotGraphics::Mesh* mesh, int i)
{
    return mesh->getSubMesh(i);
}

template <class SubMesh>
const NvIsaac::Vec3& GetVertex(const SubMesh*, int);
template <>
const NvIsaac::Vec3& GetVertex(const NvIsaac::IRobotPhysics::TriangleMesh* sm, int i)
{
    return sm->getVertex(i);
}
template <>
const NvIsaac::Vec3& GetVertex(const NvIsaac::IRobotGraphics::SubMesh* sm, int i)
{
    return sm->getVertex(i)->position;
}

template <class SubMesh, class Tri>
const Tri* GetTri(const SubMesh*, int);
template <>
const NvIsaac::IRobotPhysics::Tri* GetTri(const NvIsaac::IRobotPhysics::TriangleMesh* sm, int i)
{
    return &sm->getTriangle(i);
}
template <>
const NvIsaac::IRobotGraphics::Tri* GetTri(const NvIsaac::IRobotGraphics::SubMesh* sm, int i)
{
    return sm->getTriangle(i);
}

void AddCollisionMeshesToStage(UsdStageWeakPtr stage,
                               float distanceScale,
                               const SdfPath& robotPath,
                               const SdfPath& path,
                               const char* meshName,
                               const NvIsaac::Transform& pose,
                               int meshIndex,
                               int i,
                               int subMeshCount,
                               bool useGuide = false)
{
    std::string subStringName = FindSubstringName(meshName);
    SdfPath meshPath = SdfPath(GetNewSdfPathString(stage,
                                                   path.GetString() + "/" + TfMakeValidIdentifier(subStringName) //, i
                                                   ));
    for (int sm = 0; sm < subMeshCount; sm++)
    {
        pxr::UsdGeomMesh convexMesh = pxr::UsdGeomMesh::Define(stage, SdfPath(meshPath.GetString() //+ "_" +
                                                                                                   // std::to_string(sm)
                                                                              ));

        convexMesh.GetPrim().GetReferences().AddInternalReference(SdfPath(
            robotPath.GetString() + COLLISION_MESH_NAME + std::to_string(meshIndex) + "/_" + std::to_string(sm)));
        SetToPose(convexMesh, pose, distanceScale);
        if (useGuide)
            convexMesh.CreatePurposeAttr().Set(UsdGeomTokens->guide);
    }
}
UsdPrim AddVisualMeshesToStage(UsdStageWeakPtr stage,
                               float distanceScale,
                               const SdfPath& robotPath,
                               const SdfPath& path,
                               const char* meshName,
                               const NvIsaac::Transform& pose,
                               int meshIndex,
                               int i)
{
    std::string subStringName = FindSubstringName(meshName);
    SdfPath meshPath = SdfPath(GetNewSdfPathString(stage,
                                                   path.GetString() + "/" + TfMakeValidIdentifier(subStringName) //, i
                                                   ));
    UsdGeomXform xform = UsdGeomXform::Define(stage, meshPath);
    xform.GetPrim().GetReferences().AddInternalReference(
        SdfPath(robotPath.GetString() + VISUAL_MESH_NAME + std::to_string(meshIndex)));
    SetToPose(xform, pose, distanceScale);

    return xform.GetPrim();
}


template <class Mesh, class SubMesh, class Tri>
int AddInstanceMeshesToStage(
    UsdStageWeakPtr stage, float distanceScale, const SdfPath& path, const Mesh* mesh, int i, bool isCollision = false)
{
    SdfPath meshPath = SdfPath(path.GetString() + std::to_string(i));
    UsdPrim prim = stage->OverridePrim(meshPath);

    prim.CreateAttribute(TfToken("name"), SdfValueTypeNames->String).Set(std::string(mesh->getName()));

    int nm = GetSubMeshCount<Mesh>(mesh);
    for (int k = 0; k < nm; ++k)
    {
        const SubMesh* sm = GetSubMesh<Mesh, SubMesh>(mesh, k);
        int nv = sm->getVertexCount();
        if (!nv)
            continue;

        GfRange3f extent;
        std::vector<GfVec3f> verts(nv);
        for (int l = 0; l < nv; ++l)
        {
            const NvIsaac::Vec3& v = GetVertex<SubMesh>(sm, l);
            verts[l] = distanceScale * GfVec3f(v.x, v.y, v.z);
            extent.UnionWith(verts[l]);
        }
        VtVec3fArray extentArray(2);
        extentArray[0] = extent.GetMin();
        extentArray[1] = extent.GetMax();
        // Copy verts into VtVec3fArray for Usd.
        VtVec3fArray usdPoints;
        usdPoints.assign(verts.begin(), verts.end());

        SdfPath smPath = SdfPath(meshPath.GetString() + "/_" + std::to_string(k));
        if (isCollision)
        {
            pxr::UsdGeomMesh convexMesh = pxr::UsdGeomMesh::Define(stage, smPath);
            convexMesh.CreatePointsAttr().Set(usdPoints);
            convexMesh.CreateExtentAttr().Set(extentArray);
            PhysicsSchemaCollisionAPI::Apply(convexMesh.GetPrim());
            PhysxSchemaPhysxMeshCollisionAPI physxMeshAPI = PhysxSchemaPhysxMeshCollisionAPI::Apply(convexMesh.GetPrim());
            physxMeshAPI.CreatePhysxMeshCollisionApproximationAttr().Set(PhysxSchemaTokens.Get()->convexHull);
        }
        else
        {
            UsdGeomMesh usdMesh = UsdGeomMesh::Define(stage, smPath);

            CreateMaterial(usdMesh, GetMaterial<SubMesh>(sm), smPath, stage);

            usdMesh.GetPointsAttr().Set(usdPoints);


            VtArray<int> faceVertexCounts, faceVertexIndices;
            int triCount = sm->getTriangleCount();
            for (int l = 0; l < triCount; ++l)
            {
                const Tri* t = GetTri<SubMesh, Tri>(sm, l);
                faceVertexCounts.push_back(3);
                faceVertexIndices.push_back(t->i1);
                faceVertexIndices.push_back(t->i2);
                faceVertexIndices.push_back(t->i3);
            }

            // Now set the attributes.
            usdMesh.GetFaceVertexCountsAttr().Set(faceVertexCounts);
            usdMesh.GetFaceVertexIndicesAttr().Set(faceVertexIndices);

            // Set extent.
            usdMesh.GetExtentAttr().Set(extentArray);
        }
    }
    // Apparently Doing a mesh define within the over parent sets the parent to defined as well.. we
    // don't want these meshes, which we only want to use for referencing instances here, to be de-
    // fined in the scene or we will have a bunch of parts sitting at the origin.
    prim.SetSpecifier(SdfSpecifierOver);
    return nm;
}


UsdPrim AddBoxToStage(UsdStageWeakPtr stage,
                      float distanceScale,
                      const SdfPath& path,
                      const NvIsaac::Vec3& size,
                      const NvIsaac::Transform& pose,
                      int i,
                      bool isGuide = false)
{
    std::string name = "box";
    // USD has cube, which maybe we can scale to get a box.
    UsdGeomCube gprim = UsdGeomCube::Define(stage, SdfPath(GetNewSdfPathString(stage, path.GetString() + "/" + name //,
                                                                                                                    // i
                                                                               )));
    VtVec3fArray extentArray(2);
    extentArray[1] = distanceScale * GfVec3f(size.x * 0.5, size.y * 0.5, size.z * 0.5);
    extentArray[0] = -extentArray[1];
    gprim.GetExtentAttr().Set(extentArray);
    gprim.GetSizeAttr().Set(1.0);
    SetToPose(gprim, pose, distanceScale);
    UsdGeomXformOp s = gprim.AddScaleOp();
    s.Set(distanceScale * GfVec3f(size.x, size.y, size.z));

    VtVec3fArray color(1);
    color[0] = GfVec3f(1, .341, .20);
    gprim.CreateDisplayColorPrimvar().Set(color);
    VtFloatArray opacity(1);
    opacity[0] = 0.25f;
    gprim.CreateDisplayOpacityPrimvar().Set(opacity);
    if (isGuide)
    {
        gprim.CreatePurposeAttr().Set(UsdGeomTokens->guide);
        PhysicsSchemaCollisionAPI::Apply(gprim.GetPrim());
    }

    gprim.GetPrim().CreateAttribute(TfToken("name"), SdfValueTypeNames->String).Set(name);
    return gprim.GetPrim();
}

UsdPrim AddSphereToStage(UsdStageWeakPtr stage,
                         float distanceScale,
                         const SdfPath& path,
                         float radius,
                         const NvIsaac::Transform& pose,
                         int i,
                         bool isGuide = false)
{
    std::string name = "sphere";
    UsdGeomSphere gprim =
        UsdGeomSphere::Define(stage, SdfPath(GetNewSdfPathString(stage, path.GetString() + "/" + name //, i
                                                                 )));
    VtVec3fArray extentArray(2);
    gprim.ComputeExtent(distanceScale * radius, &extentArray);
    gprim.GetExtentAttr().Set(extentArray);
    gprim.GetRadiusAttr().Set(double(distanceScale * radius));
    SetToPose(gprim, pose, distanceScale);

    VtVec3fArray color(1);
    color[0] = GfVec3f(0, 1, 0);
    gprim.CreateDisplayColorPrimvar().Set(color);
    VtFloatArray opacity(1);
    opacity[0] = 0.25f;
    gprim.CreateDisplayOpacityPrimvar().Set(opacity);
    if (isGuide)
    {
        gprim.CreatePurposeAttr().Set(UsdGeomTokens->guide);
        PhysicsSchemaCollisionAPI::Apply(gprim.GetPrim());
    }

    gprim.GetPrim().CreateAttribute(TfToken("name"), SdfValueTypeNames->String).Set(name);

    return gprim.GetPrim();
}

template <class UsdGeomCapsinder>
UsdPrim AddCapsinderAttrs(UsdStageWeakPtr stage,
                          UsdGeomCapsinder gprim,
                          float distanceScale,
                          float radius,
                          float height,
                          std::string name,
                          const SdfPath& originalPath,
                          const NvIsaac::Transform& pose,
                          bool isGuide = false)
{
    VtVec3fArray extentArray(2);
    // PhysicsDOM assumes the long axis is x (so does PhysX).
    // URDF assumes the long axis is z.
    gprim.ComputeExtent(distanceScale * height, distanceScale * radius, UsdGeomTokens->x, &extentArray);
    gprim.GetAxisAttr().Set(UsdGeomTokens->x);
    gprim.GetExtentAttr().Set(extentArray);
    gprim.GetHeightAttr().Set(double(distanceScale * height));
    gprim.GetRadiusAttr().Set(double(distanceScale * radius));
    NvIsaac::Transform rotatedPose = pose;
    rotatedPose.q *= NvIsaac::Quat(M_PI * 0.5, NvIsaac::Vec3(0.0, 1.0, 0.0));
    SetToPose(gprim, rotatedPose, distanceScale);

    // Have to rotate graphics cylinder too
    pxr::UsdGeomXformable graphicsXform(stage->GetPrimAtPath(originalPath));
    SetToPose(graphicsXform, rotatedPose, distanceScale);

    VtVec3fArray color(1);
    color[0] = GfVec3f(1, 0, 1);
    gprim.CreateDisplayColorPrimvar().Set(color);
    VtFloatArray opacity(1);
    opacity[0] = 0.25f;
    gprim.CreateDisplayOpacityPrimvar().Set(opacity);
    if (isGuide)
    {
        gprim.CreatePurposeAttr().Set(UsdGeomTokens->guide);
        PhysicsSchemaCollisionAPI::Apply(gprim.GetPrim());
    }

    // add the name
    gprim.GetPrim().CreateAttribute(TfToken("name"), SdfValueTypeNames->String).Set(name);
    return gprim.GetPrim();
}

UsdPrim AddCylinderToStage(UsdStageWeakPtr stage,
                           float distanceScale,
                           const SdfPath& path,
                           float radius,
                           float height,
                           const NvIsaac::Transform& pose,
                           int i,
                           bool isGuide = false)
{
    std::string name = "cylinder";
    std::string originalPathString = path.GetString() + "/" + name;
    SdfPath addPath = SdfPath(GetNewSdfPathString(stage, originalPathString));

    UsdGeomCylinder gprim = UsdGeomCylinder::Define(stage, addPath);
    return AddCapsinderAttrs<UsdGeomCylinder>(
        stage, gprim, distanceScale, radius, height, name, SdfPath(originalPathString), pose, isGuide);
}

UsdPrim AddCapsuleToStage(UsdStageWeakPtr stage,
                          float distanceScale,
                          const SdfPath& path,
                          float radius,
                          float height,
                          const NvIsaac::Transform& pose,
                          int i,
                          bool isGuide = false)
{
    std::string name = "capsule";
    std::string originalPathString = path.GetString() + "/" + name;
    std::string addPath = GetNewSdfPathString(stage, originalPathString);
    UsdGeomCapsule gprim = UsdGeomCapsule::Define(stage, SdfPath(addPath));

    return AddCapsinderAttrs<UsdGeomCapsule>(
        stage, gprim, distanceScale, radius, height, name, SdfPath(originalPathString), pose, isGuide);
}

void AddRawDOFToStage(UsdStageWeakPtr stage, const SdfPath& path, const NvIsaac::IRobotSkeleton* skel)
{
    SdfPath mpath = SdfPath(GetNewSdfPathString(stage, path.GetString() + "/DebugInfo/DOF"));
    UsdPrim prim = stage->DefinePrim(mpath);

    int numDOF = skel->getDOFCount();
    VtIntArray axes(numDOF);
    VtBoolArray limitsEnablers(numDOF);
    VtFloatArray limitLows(numDOF);
    VtFloatArray limitHighs(numDOF);
    VtIntArray jointIndices(numDOF);
    for (int i = 0; i < numDOF; ++i)
    {
        axes[i] = int(skel->getDOF(i)->axis);
        limitsEnablers[i] = skel->getDOF(i)->limitsEnabled;
        limitLows[i] = skel->getDOF(i)->limitLow;
        limitHighs[i] = skel->getDOF(i)->limitHigh;
        jointIndices[i] = skel->getDOF(i)->jointIndex;
    }
    prim.CreateAttribute(TfToken("axis"), SdfValueTypeNames->IntArray).Set(axes);
    prim.CreateAttribute(TfToken("limitEnabled"), SdfValueTypeNames->BoolArray).Set(limitsEnablers);
    prim.CreateAttribute(TfToken("limitLow"), SdfValueTypeNames->FloatArray).Set(limitLows);
    prim.CreateAttribute(TfToken("limitHigh"), SdfValueTypeNames->FloatArray).Set(limitHighs);
    prim.CreateAttribute(TfToken("jointIndex"), SdfValueTypeNames->IntArray).Set(jointIndices);
}

void AddRawJointsToStage(UsdStageWeakPtr stage, const SdfPath& path, const NvIsaac::IRobotSkeleton* skel)
{
    SdfPath newPath = SdfPath(GetNewSdfPathString(stage, path.GetString() + "/DebugInfo/Joints"));
    UsdGeomXform gprim = UsdGeomXform::Define(stage, newPath);

    UsdGeomPrimvarsAPI primvars(gprim);

    int16_t num = skel->getJointCount();

    VtStringArray name(num);
    VtIntArray index(num);
    VtIntArray type(num);
    VtIntArray body0(num);
    VtIntArray body1(num);
    VtQuatfArray localPose0_q(num);
    VtVec3fArray localPose0_p(num);
    VtQuatfArray localPose1_q(num);
    VtVec3fArray localPose1_p(num);
    VtBoolArray limitsEnabled(num);
    VtFloatArray limitLow(num);
    VtFloatArray limitHigh(num);
    VtFloatArray limitY(num);
    VtFloatArray limitZ(num);
    VtFloatArray maxEffort(num);
    VtFloatArray maxVelocity(num);
    VtFloatArray damping(num);
    VtFloatArray friction(num);
    VtIntArray DOFIndex(num);
    VtIntArray DOFIndexCount(num);
    for (int16_t i = 0; i < num; ++i)
    {
        const NvIsaac::IRobotSkeleton::JointNode* j = skel->getJoint(i);

        name[i] = std::string(j->getName());
        index[i] = j->getIndex();
        type[i] = int(j->getType());
        body0[i] = j->getBody0();
        body1[i] = j->getBody1();
        const NvIsaac::Transform& t0 = j->getLocalPose0();
        const NvIsaac::Transform& t1 = j->getLocalPose1();
        localPose0_q[i] = GfQuatf(t0.q.w, GfVec3f(t0.q.x, t0.q.y, t0.q.z));
        localPose0_p[i] = GfVec3f(t0.p.x, t0.p.y, t0.p.z);
        localPose1_q[i] = GfQuatf(t1.q.w, GfVec3f(t1.q.x, t1.q.y, t1.q.z));
        localPose1_p[i] = GfVec3f(t1.p.x, t1.p.y, t1.p.z);
        limitsEnabled[i] = j->getLimitsEnabled();
        limitLow[i] = j->getLimitLow();
        limitHigh[i] = j->getLimitHigh();
        limitY[i] = j->getLimitY();
        limitZ[i] = j->getLimitZ();
        maxEffort[i] = j->getMaxEffort();
        maxVelocity[i] = j->getMaxVelocity();
        damping[i] = j->getDamping();
        friction[i] = j->getFriction();
        DOFIndex[i] = j->getDOFIndex();
        DOFIndexCount[i] = j->getDOFIndexCount();
    }
    primvars.CreatePrimvar(TfToken("name"), SdfValueTypeNames->StringArray).Set(name);
    primvars.CreatePrimvar(TfToken("index"), SdfValueTypeNames->IntArray).Set(index);
    primvars.CreatePrimvar(TfToken("type"), SdfValueTypeNames->IntArray).Set(type);
    primvars.CreatePrimvar(TfToken("body0"), SdfValueTypeNames->IntArray).Set(body0);
    primvars.CreatePrimvar(TfToken("body1"), SdfValueTypeNames->IntArray).Set(body1);
    primvars.CreatePrimvar(TfToken("localPose0_q"), SdfValueTypeNames->QuatfArray).Set(localPose0_q);
    primvars.CreatePrimvar(TfToken("localPose0_p"), SdfValueTypeNames->Vector3fArray).Set(localPose0_p);
    primvars.CreatePrimvar(TfToken("localPose1_q"), SdfValueTypeNames->QuatfArray).Set(localPose1_q);
    primvars.CreatePrimvar(TfToken("localPose1_p"), SdfValueTypeNames->Vector3fArray).Set(localPose1_p);
    primvars.CreatePrimvar(TfToken("limitsEnabled"), SdfValueTypeNames->BoolArray).Set(limitsEnabled);
    primvars.CreatePrimvar(TfToken("limitLow"), SdfValueTypeNames->FloatArray).Set(limitLow);
    primvars.CreatePrimvar(TfToken("limitHigh"), SdfValueTypeNames->FloatArray).Set(limitHigh);
    primvars.CreatePrimvar(TfToken("limitY"), SdfValueTypeNames->FloatArray).Set(limitY);
    primvars.CreatePrimvar(TfToken("limitZ"), SdfValueTypeNames->FloatArray).Set(limitZ);
    primvars.CreatePrimvar(TfToken("maxEffort"), SdfValueTypeNames->FloatArray).Set(maxEffort);
    primvars.CreatePrimvar(TfToken("maxVelocity"), SdfValueTypeNames->FloatArray).Set(maxVelocity);
    primvars.CreatePrimvar(TfToken("damping"), SdfValueTypeNames->FloatArray).Set(damping);
    primvars.CreatePrimvar(TfToken("friction"), SdfValueTypeNames->FloatArray).Set(friction);
    primvars.CreatePrimvar(TfToken("DOFIndex"), SdfValueTypeNames->IntArray).Set(DOFIndex);
    primvars.CreatePrimvar(TfToken("DOFIndexCount"), SdfValueTypeNames->IntArray).Set(DOFIndexCount);
}

void AddRawJointFramesToStage(UsdStageWeakPtr stage,
                              const SdfPath& path,
                              const std::vector<std::string>& bodyNames,
                              const NvIsaac::IRobotSkeleton* skel)
{
    SdfPath mpath = SdfPath(GetNewSdfPathString(stage, path.GetString() + "/DebugInfo/JointFrames"));
    UsdPrim prim = stage->DefinePrim(mpath);

    int num = skel->getJointReferenceFrameCount();
    std::vector<std::string> nameVec(num);
    std::vector<int> indexVec(num);
    std::vector<GfQuatf> lpVec(num);
    VtStringArray name(num);
    VtIntArray index(num);
    VtIntArray parentComponentIndex(num);
    VtQuatfArray localPose_q(num);
    VtVec3fArray localPose_p(num);
    for (int i = 0; i < num; ++i)
    {
        const NvIsaac::IRobotSkeleton::ReferenceFrame* f = skel->getJointReferenceFrame(i);

        name[i] = std::string(f->getName());
        nameVec[i] = name[i];
        index[i] = f->getIndex();
        indexVec[i] = index[i];
        const NvIsaac::Transform& t = f->getLocalPose();
        localPose_q[i] = GfQuatf(t.q.w, GfVec3f(t.q.x, t.q.y, t.q.z));
        lpVec[i] = localPose_q[i];
        localPose_p[i] = GfVec3f(t.p.x, t.p.y, t.p.z);
    }

    int jointCount = skel->getJointCount();

    VtStringArray jointNames(jointCount);

    for (int ji = 0; ji < jointCount; ++ji)
    {
        const NvIsaac::IRobotSkeleton::JointNode* jn = skel->getJoint(ji);
        std::string actor0 = bodyNames[jn->getBody0()];
        std::string actor1 = bodyNames[jn->getBody1()];
        // Make path relative to the prefix
        std::string jointPath = pxr::SdfPath(actor0).MakeRelativePath(path).GetString() + "/" + jn->getName();

        parentComponentIndex[ji] = int(jn->getBody0());

        if (!SdfPath::IsValidPathString(jointPath))
        {
            // jn->getName starts with a number which is not valid for usd path, so prefix it with "joint"
            jointPath = pxr::SdfPath(actor0).MakeRelativePath(path).GetString() + "/joint" + jn->getName();
        }

        jointNames[ji] = jointPath;
    }
    prim.CreateAttribute(TfToken("name"), SdfValueTypeNames->StringArray).Set(name);
    prim.CreateAttribute(TfToken("index"), SdfValueTypeNames->IntArray).Set(index);
    prim.CreateAttribute(TfToken("parentComponentIndex"), SdfValueTypeNames->IntArray).Set(parentComponentIndex);
    prim.CreateAttribute(TfToken("path"), SdfValueTypeNames->StringArray).Set(jointNames);
    prim.CreateAttribute(TfToken("localPose_q"), SdfValueTypeNames->QuatfArray).Set(localPose_q);
    prim.CreateAttribute(TfToken("localPose_p"), SdfValueTypeNames->Vector3fArray).Set(localPose_p);
}

template <class T>
void SetLimit(T& jointAPI, const NvIsaac::IRobotSkeleton::DOF* dn, float distanceScale)
{
    jointAPI.CreateLowerLimitAttr().Set(dn->limitLow);
    jointAPI.CreateUpperLimitAttr().Set(dn->limitHigh);
}
template <>
void SetLimit(PhysicsSchemaSphericalPhysicsJoint& sphericalJointAPI,
              const NvIsaac::IRobotSkeleton::DOF* dn,
              float distanceScale)
{
    sphericalJointAPI.CreateConeAngle0LimitAttr().Set(dn->limitLow);
    sphericalJointAPI.CreateConeAngle1LimitAttr().Set(dn->limitHigh);
}

template <>
void SetLimit(PhysicsSchemaPrismaticPhysicsJoint& prismaticJointAPI,
              const NvIsaac::IRobotSkeleton::DOF* dn,
              float distanceScale)
{

    prismaticJointAPI.CreateLowerLimitAttr().Set(dn->limitLow * distanceScale);
    prismaticJointAPI.CreateUpperLimitAttr().Set(dn->limitHigh * distanceScale);
}

template <class T>
void AddSingleJoint(const NvIsaac::IRobotSkeleton::JointNode* jn,
                    UsdStageWeakPtr stage,
                    const SdfPath& jointPath,
                    PhysicsSchemaPhysicsJoint& jointPrimBase,
                    const NvIsaac::IRobotSkeleton* skel,
                    float distanceScale)
{
    T jointPrim = T::Define(stage, SdfPath(jointPath));
    jointPrimBase = jointPrim;
    const int DOFIndex = jn->getDOFIndex();
    const int DOFCount = jn->getDOFIndexCount();
    for (int di = DOFIndex; di < DOFIndex + DOFCount; ++di)
    {
        const NvIsaac::IRobotSkeleton::DOF* dn = skel->getDOF(di);
        jointPrim.CreateAxisAttr().Set(getAxisXYZ(dn->axis));

        if (dn->limitsEnabled)
        {
            SetLimit(jointPrim, dn, distanceScale);
        }

        if (jn->getType() == NvIsaac::RobotJointType::kPrismatic)
        {
            PhysicsSchemaDriveAPI driveAPI = PhysicsSchemaDriveAPI::Apply(jointPrim.GetPrim(), TfToken("linear"));
            driveAPI.CreateMaxForceAttr().Set(FLT_MAX);
            driveAPI.CreateTargetAttr().Set(0.0f);
            driveAPI.CreateTypeAttr().Set(TfToken("acceleration"));
            driveAPI.CreateTargetTypeAttr().Set(TfToken("position"));
            driveAPI.CreateDampingAttr().Set(1.0f);
            driveAPI.CreateStiffnessAttr().Set(100000.0f);
        }
        else if (jn->getType() == NvIsaac::RobotJointType::kRevolute)
        {
            PhysicsSchemaDriveAPI driveAPI = PhysicsSchemaDriveAPI::Apply(jointPrim.GetPrim(), TfToken("angular"));
            driveAPI.CreateMaxForceAttr().Set(FLT_MAX);
            driveAPI.CreateTargetAttr().Set(0.0f);
            driveAPI.CreateTypeAttr().Set(TfToken("acceleration"));
            driveAPI.CreateTargetTypeAttr().Set(TfToken("position"));
            driveAPI.CreateDampingAttr().Set(1.0f);
            driveAPI.CreateStiffnessAttr().Set(100000.0f);
        }
    }
}
void AddJointsToStage(UsdStageWeakPtr stage,
                      const SdfPath& path,
                      float distanceScale,
                      const std::vector<std::string>& bodyNames,
                      const NvIsaac::IRobotSkeleton* skel)
{

    // Create the root joint
    std::string rootJointPath = path.GetString() + "/rootJoint";
    PhysicsSchemaPhysicsJoint rootJoint = PhysicsSchemaPhysicsJoint::Define(stage, SdfPath(rootJointPath));
    auto linkAPI = PhysicsSchemaArticulationJointAPI::Apply(stage->GetPrimAtPath(SdfPath(rootJointPath)));
    linkAPI.CreateArticulationTypeAttr().Set(TfToken("articulatedRoot"));
    const NvIsaac::IRobotSkeleton::JointNode* jn = skel->getJoint(int16_t(0));
    std::string actor0 = bodyNames[jn->getBody0()];
    SdfPathVector val0{ SdfPath(actor0) };
    rootJoint.CreateBody0Rel().SetTargets(val0);

    int jointCount = skel->getJointCount();
    std::vector<std::string> jointNames(jointCount);
    for (int ji = 0; ji < jointCount; ++ji)
    {
        const NvIsaac::IRobotSkeleton::JointNode* jn = skel->getJoint(ji);
        std::string actor0 = bodyNames[jn->getBody0()];
        std::string actor1 = bodyNames[jn->getBody1()];
        std::string jointPath = actor0 + "/" + jn->getName();

        if (!SdfPath::IsValidPathString(jointPath))
        {
            // jn->getName starts with a number which is not valid for usd path, so prefix it with "joint"
            jointPath = actor0 + "/joint" + jn->getName();
        }

        jointNames[ji] = jointPath;
        PhysicsSchemaPhysicsJoint jointPrim;
        // defining the joint type
        if (jn->getType() == NvIsaac::RobotJointType::kFixed)
        {
            jointPrim = PhysicsSchemaFixedPhysicsJoint::Define(stage, SdfPath(jointPath));
        }
        else if (jn->getType() == NvIsaac::RobotJointType::kPrismatic)
        {
            AddSingleJoint<PhysicsSchemaPrismaticPhysicsJoint>(
                jn, stage, SdfPath(jointPath), jointPrim, skel, distanceScale);
        }
        else if (jn->getType() == NvIsaac::RobotJointType::kSpherical)
        {
            AddSingleJoint<PhysicsSchemaSphericalPhysicsJoint>(
                jn, stage, SdfPath(jointPath), jointPrim, skel, distanceScale);
        }
        else // default if (jn->getType() == NvIsaac::RobotJointType::kRevolute)
        {
            AddSingleJoint<PhysicsSchemaRevolutePhysicsJoint>(
                jn, stage, SdfPath(jointPath), jointPrim, skel, distanceScale);
        }

        SdfPathVector val0{ SdfPath(actor0) };
        SdfPathVector val1{ SdfPath(actor1) };

        if (actor0 != "")
        {
            jointPrim.CreateBody0Rel().SetTargets(val0);
        }
        GfVec3f localPos0 = distanceScale * getP(jn->getLocalPose0());
        GfQuatf localRot0 = getQ(jn->getLocalPose0());
        GfVec3f localPos1 = distanceScale * getP(jn->getLocalPose1());
        GfQuatf localRot1 = getQ(jn->getLocalPose1());
        // addPosition(jointPrim, localPos0);
        // addOrientation(jointPrim, localRot0);
        jointPrim.CreateLocalPos0Attr().Set(localPos0);
        jointPrim.CreateLocalRot0Attr().Set(localRot0);

        if (actor1 != "")
        {
            jointPrim.CreateBody1Rel().SetTargets(val1);
        }
        jointPrim.CreateLocalPos1Attr().Set(localPos1);
        jointPrim.CreateLocalRot1Attr().Set(localRot1);
#if 0 // Do we need this from Graphene\source\plugins\carb.physics-usd\BackwardCompatibility.cpp
      // We may not have a local frame.  In that case, calculate them from the joint-body relative transform
		const bool hasFrame0 = q0.Normalize() > 0;
		const bool hasFrame1 = q1.Normalize() > 0;
		if (!hasFrame0 || !hasFrame0)
		{
			GfMatrix4d jointFrameInWorld;
			jointFrameInWorld.SetTranslate(GfVec3d(translate));
			jointFrameInWorld.SetRotateOnly(GfQuatd(orient));

			if (usdPrim.GetParent())
			{
				const GfMatrix4d parentMatrix = getWorldTransformMatrix(usdPrim.GetParent());
				jointFrameInWorld = jointFrameInWorld * parentMatrix;
			}

			if (!hasFrame0)
			{
				const GfMatrix4d body0ToWorld = getWorldTransformMatrix(stage->GetPrimAtPath(SdfPath(body0)));
				const GfMatrix4d jointFrameInBody0 = jointFrameInWorld * body0ToWorld.GetInverse();
				t0 = GfVec3f(jointFrameInBody0.ExtractTranslation());
				q0 = GfQuatf(jointFrameInBody0.ExtractRotation().GetQuat());

				UsdGeomXformCache xfCache;

				GfMatrix4d mat = xfCache.GetLocalToWorldTransform(stage->GetPrimAtPath(SdfPath(body0)));

				const GfTransform tr(mat);
				const GfVec3f sc = GfVec3f(tr.GetScale());

				for (int i = 0; i < 3; i++)
				{
					t0[i] /= sc[i];
				}

				jointPrim.GetLocalPos0Attr().Set(t0);
				jointPrim.GetLocalRot0Attr().Set(q0);
			}

			if (!hasFrame1)
			{
				const GfMatrix4d body1ToWorld = getWorldTransformMatrix(stage->GetPrimAtPath(SdfPath(body1)));
				const GfMatrix4d jointFrameInBody1 = jointFrameInWorld * body1ToWorld.GetInverse();
				t1 = GfVec3f(jointFrameInBody1.ExtractTranslation());
				q1 = GfQuatf(jointFrameInBody1.ExtractRotation().GetQuat());

				UsdGeomXformCache xfCache;

				GfMatrix4d mat = xfCache.GetLocalToWorldTransform(stage->GetPrimAtPath(SdfPath(body1)));

				const GfTransform tr(mat);
				const GfVec3f sc = GfVec3f(tr.GetScale());

				for (int i = 0; i < 3; i++)
				{
					t1[i] /= sc[i];
				}

				jointPrim.GetLocalPos1Attr().Set(t1);
				jointPrim.GetLocalRot1Attr().Set(q1);
			}
		}
#endif

        jointPrim.CreateJointFrictionAttr().Set(jn->getFriction());

        jointPrim.CreateBreakForceAttr().Set(FLT_MAX); // TODO?
        jointPrim.CreateBreakTorqueAttr().Set(FLT_MAX);

        // Apply articulations for these joints
        auto linkAPI = PhysicsSchemaArticulationJointAPI::Apply(stage->GetPrimAtPath(SdfPath(jointPath)));
        linkAPI.CreateArticulationTypeAttr().Set(TfToken("articulatedJoint"));
    }
}

void UsdUrdfStream::UsdUrdfTranslateUrdfToUsd(UsdStageWeakPtr stage)
{
    float distanceScale = mImportConfig.distanceScale;
    // To create an SdfLayer holding Usd data representing \p urdfStream, we
    // would like to use the Usd and UsdGeom APIs.  To do so, we first create an
    // anonymous in-memory layer, then create a UsdStage with that layer as its
    // root layer.  Then we use the Usd/UsdGeom API to create UsdGeomMeshes on
    // that stage, populating them with the URDF mesh data.  Finally we return
    // the generated layer to the caller, discarding the UsdStage we created for
    // authoring purposes.

    if (mImportConfig.forceZUp)
    {
        UsdGeomSetStageUpAxis(stage, UsdGeomTokens->z);
    }

    PhysicsSchemaPhysicsScene scene = PhysicsSchemaPhysicsScene::Define(stage, SdfPath("/physicsScene"));
    scene.CreateGravityAttr().Set(GfVec3f(0.0f, 0.0f, -9.80f * distanceScale));

    // addGroundPlane(stage, "/plane", TfToken("Z"), distanceScale);

    NvIsaac::IRobotModel* model = GetRobotModel();
    SdfPath mpath = SdfPath(GetNewSdfPathString(stage, "/" + TfMakeValidIdentifier(std::string(model->getName()))));

    // Remove the prim we are about to add in case it exists
    if (stage->GetPrimAtPath(mpath))
    {
        stage->RemovePrim(mpath);
    }

    UsdGeomXform robot = UsdGeomXform::Define(stage, mpath);
    PhysicsSchemaArticulationAPI physicsSchema = PhysicsSchemaArticulationAPI::Apply(robot.GetPrim());
    // By default fix the robot in place
    physicsSchema.CreateFixBaseAttr().Set(true);
    // robot.GetPrim().CreateAttribute(TfToken("fileName"), SdfValueTypeNames->String).Set(GetFileName());
    // robot.GetPrim().CreateAttribute(TfToken("assetPath"),
    // SdfValueTypeNames->String).Set(std::string(model->getAssetPath())); fprintf(stderr, "\nmpath: %s\n",
    // mpath.GetText());


    stage->SetDefaultPrim(robot.GetPrim());

    // put graphics meshes into the usd
    const NvIsaac::IRobotSkeleton* skel = model->getSkeleton();
    const NvIsaac::IRobotGraphics* graph = model->getGraphics();
    const NvIsaac::IRobotPhysics* phys = model->getPhysics();

    if (mImportConfig.addDebugInfo)
    {
        AddRawDOFToStage(stage, mpath, skel);
        AddRawJointsToStage(stage, mpath, skel);
    }
    const bool setAsGuide = true;
    // Collect the collision and visual meshes for instancing.
    for (int bi = 0; bi < phys->getMeshCount(); ++bi)
    {
        auto pmesh = phys->getMesh(bi);
        if (!pmesh)
            continue;

        AddInstanceMeshesToStage<NvIsaac::IRobotPhysics::Mesh, NvIsaac::IRobotPhysics::TriangleMesh,
                                 NvIsaac::IRobotPhysics::Tri>(
            stage, distanceScale, SdfPath(mpath.GetString() + COLLISION_MESH_NAME), pmesh, bi, setAsGuide);
    }
    for (int i = 0; i < graph->getMeshCount(); ++i)
    {
        auto vmesh = graph->getMesh(i);
        if (!vmesh)
            continue;
        AddInstanceMeshesToStage<NvIsaac::IRobotGraphics::Mesh, NvIsaac::IRobotGraphics::SubMesh, NvIsaac::IRobotGraphics::Tri>(
            stage, distanceScale, SdfPath(mpath.GetString() + VISUAL_MESH_NAME), vmesh, i);
    }

    int bodyCount = skel->getBodyCount();
    std::vector<std::string> bodyNames(bodyCount);
    for (int bi = 0; bi < bodyCount; ++bi)
    {
        auto sbody = skel->getBody(bi);
        auto pbody = phys->getBody(bi);
        auto gbody = graph->getBody(bi);
        if (!sbody || !pbody || !gbody)
            continue;
        bodyNames[bi] =
            GetNewSdfPathString(stage, mpath.GetString() + "/" + TfMakeValidIdentifier(std::string(sbody->getName())));
        SdfPath bodyPath = SdfPath(bodyNames[bi]);
        UsdGeomXform bodyXform = UsdGeomXform::Define(stage, bodyPath);
        auto pose = sbody->getPose();

        bodyXform.GetPrim().SetInstanceable(true);
        SetToPose(bodyXform, pose, distanceScale);
        addRigidBody(stage, bodyNames[bi]);
        addVelocity(stage, bodyNames[bi], GfVec3f(0.0f), GfVec3f(0.0f));
        // NvIsaac::Vec3 com = distanceScale*pbody->getCenterOfMass();
        // NvIsaac::Quat inertialOrientation;
        // NvIsaac::Vec3 inertialFrame = PxDiagonalize(pbody->getMassSpaceInertiaTensor(), inertialOrientation);
        // PhysicsSchemaInertiaAPI inertiaAPI = PhysicsSchemaInertiaAPI::Apply(bodyXform.GetPrim());
        // GfVec3f p = GfVec3f(inertialFrame.x, inertialFrame.y, inertialFrame.z);
        // GfVec4f q = GfVec4f(inertialOrientation.x, inertialOrientation.y, inertialOrientation.z,
        // inertialOrientation.w); GfVec3f c = GfVec3f(com.x, com.y, com.z);
        // inertiaAPI.CreateInertiaMassSpaceInertiaTensorAttr().Set(p);
        // inertiaAPI.CreateInertiaCMassLocalOrientationAttr().Set(q);
        // inertiaAPI.CreateInertiaCMassLocalPositionAttr().Set(c);

        // get the graphics
        int visualCount = gbody->getVisualCount();
        for (int vi = 0; vi < visualCount; ++vi)
        {
            auto vis = gbody->getVisual(vi);
            auto vmesh = graph->getMesh(vis->meshIndex);
            if (!vis || !vmesh)
                continue;

            AddVisualMeshesToStage(
                stage, distanceScale, mpath, bodyPath, vmesh->getName(), vis->localPose, vis->meshIndex, vi);
        }
        // get the physics
        int colliderCount = pbody->getColliderCount();
        for (int ci = 0; ci < colliderCount; ci++)
        {
            auto c = pbody->getCollider(ci);
            if (!c)
                continue;
            switch (c->geometry.type)
            {
            case NvIsaac::IRobotPhysics::GeometryType::kMesh:
            {
                auto pmesh = phys->getMesh(c->geometry.mesh.index);
                if (!pmesh)
                    continue;

                AddCollisionMeshesToStage(stage, distanceScale, mpath, bodyPath, pmesh->getName(), c->localPose,
                                          c->geometry.mesh.index, ci, pmesh->getConvexHullCount(), setAsGuide);
            }
            break;
            case NvIsaac::IRobotPhysics::GeometryType::kCylinder:
            {
                float radius = c->geometry.cylinder.radius;
                float height = c->geometry.cylinder.height;
                AddCylinderToStage(stage, distanceScale, bodyPath, radius, height, c->localPose, ci, setAsGuide);
            }
            break;
            case NvIsaac::IRobotPhysics::GeometryType::kCapsule:
            {
                float radius = c->geometry.cylinder.radius;
                float height = c->geometry.cylinder.height;
                AddCapsuleToStage(stage, distanceScale, bodyPath, radius, height, c->localPose, ci, setAsGuide);
            }
            break;
            case NvIsaac::IRobotPhysics::GeometryType::kSphere:
            {
                float radius = c->geometry.sphere.radius;
                AddSphereToStage(stage, distanceScale, bodyPath, radius, c->localPose, ci, setAsGuide);
            }
            break;
            case NvIsaac::IRobotPhysics::GeometryType::kBox:
            {
                NvIsaac::Vec3 size = c->geometry.box.size;
                AddBoxToStage(stage, distanceScale, bodyPath, size, c->localPose, ci, setAsGuide);
            }
            break;
            default:
                fprintf(stderr, "Collider of type %i NOT loaded!\n", c->geometry.type);
            }

            // add physics properties
            // TODO: Make this match the physx scheme?
            /* TODO WHAT DO I DO WITH THIS?
            auto pmat = phys->getMaterial(c->materialIndex);
            if (prim && pmat)
            {
                prim.CreateAttribute(TfToken("physicsMaterialName"),
            SdfValueTypeNames->String).Set(std::string(pmat->getName())); prim.CreateAttribute(TfToken("restitution"),
            SdfValueTypeNames->Float).Set(pmat->getRestitution()); prim.CreateAttribute(TfToken("dynamicFriction"),
            SdfValueTypeNames->Float).Set(pmat->getDynamicFriction()); prim.CreateAttribute(TfToken("staticFriction"),
            SdfValueTypeNames->Float).Set(pmat->getStaticFriction());
            }
            PhysicsSchemaCollisionAPI::Apply(prim);
            */
        }
        // Use mass from URDF instead of density
        PhysicsSchemaMassAPI massAPI = PhysicsSchemaMassAPI::Apply(bodyXform.GetPrim());
        double udrfMass = pbody->getMass();
        if (udrfMass > 0)
        {
            massAPI.CreateMassAttr().Set(udrfMass);
        }
        else
        {
            // mass was not valid so fallback with density
            massAPI.CreateDensityAttr().Set(1.0f);
        }
        // addDensity(stage, bodyNames[bi], urdfMass);// TODO correct density, should just be able to set inertial
        // proerties, but getting 0 mass crash.
    }
    if (mImportConfig.addDebugInfo)
    {
        AddRawJointFramesToStage(stage, mpath, bodyNames, skel);
    }
    AddJointsToStage(stage, mpath, distanceScale, bodyNames, skel);
#if MY_DEBUG_CRAP
    std::string s;
    if (stage->GetRootLayer()->ExportToString(&s))
    {
        std::ofstream out("d:\\usrdFileFormat.usda");
        out << s;
        out.close();
    }
#endif
}

}
}
}
