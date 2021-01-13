// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "MeshImporter.h"

#include "../core/PathUtils.h"
#include "ImportHelpers.h"
#include "assimp/Importer.hpp"
#include "assimp/postprocess.h"

#include <experimental/filesystem>

#include <cmath>
#include <set>
#include <stack>
#include <unordered_set>


namespace omni
{
namespace isaac
{
namespace urdf
{


const static size_t INVALID_MATERIAL_INDEX = SIZE_MAX;

struct ImportTransform
{
    pxr::GfMatrix4d matrix;
    pxr::GfVec3f translation;
    pxr::GfVec3f eulerAngles; // XYZ order
    pxr::GfVec3f scale;
};


struct MeshGeomSubset
{
    pxr::VtArray<int> faceIndices;
    size_t materialIndex = INVALID_MATERIAL_INDEX;
};


struct Mesh
{
    std::string name;
    pxr::VtArray<pxr::GfVec3f> points;
    pxr::VtArray<int> faceVertexCounts;
    pxr::VtArray<int> faceVertexIndices;
    pxr::VtArray<pxr::GfVec3f> normals; // Face varing normals
    pxr::VtArray<pxr::VtArray<pxr::GfVec2f>> uvs; // Face varing uvs
    pxr::VtArray<pxr::VtArray<pxr::GfVec3f>> colors; // Face varing colors
    std::vector<MeshGeomSubset> meshSubsets;
};

// static pxr::GfMatrix4d AiMatrixToGfMatrix(const aiMatrix4x4& matrix)
// {
//     return pxr::GfMatrix4d(matrix.a1, matrix.b1, matrix.c1, matrix.d1, matrix.a2, matrix.b2, matrix.c2, matrix.d2,
//                            matrix.a3, matrix.b3, matrix.c3, matrix.d3, matrix.a4, matrix.b4, matrix.c4, matrix.d4);
// }

static pxr::GfVec3f AiVector3dToGfVector3f(const aiVector3D& vector)
{
    return pxr::GfVec3f(vector.x, vector.y, vector.z);
}

static pxr::GfVec2f AiVector3dToGfVector2f(const aiVector3D& vector)
{
    return pxr::GfVec2f(vector.x, vector.y);
}

// static pxr::GfVec3h AiVector3dToGfVector3h(const aiVector3D& vector)
// {
//     return pxr::GfVec3h(vector.x, vector.y, vector.z);
// }

// static pxr::GfQuatf AiQuatToGfVector(const aiQuaternion& quat)
// {
//     return pxr::GfQuatf(quat.w, quat.x, quat.y, quat.z);
// }

// static pxr::GfQuath AiQuatToGfVectorh(const aiQuaternion& quat)
// {
//     return pxr::GfQuath(quat.w, quat.x, quat.y, quat.z);
// }

// static pxr::GfVec3f AiColor3DToGfVector3f(const aiColor3D& color)
// {
//     return pxr::GfVec3f(color.r, color.g, color.b);
// }


// static ImportTransform AiMatrixToTransform(const aiMatrix4x4& matrix)
// {
//     ImportTransform transform;
//     transform.matrix =
//         pxr::GfMatrix4d(matrix.a1, matrix.b1, matrix.c1, matrix.d1, matrix.a2, matrix.b2, matrix.c2, matrix.d2,
//                         matrix.a3, matrix.b3, matrix.c3, matrix.d3, matrix.a4, matrix.b4, matrix.c4, matrix.d4);

//     aiVector3D translation, rotation, scale;
//     matrix.Decompose(scale, rotation, translation);
//     transform.translation = AiVector3dToGfVector3f(translation);
//     transform.eulerAngles = AiVector3dToGfVector3f(
//         aiVector3D(AI_RAD_TO_DEG(rotation.x), AI_RAD_TO_DEG(rotation.y), AI_RAD_TO_DEG(rotation.z)));
//     transform.scale = AiVector3dToGfVector3f(scale);

//     return transform;
// }

pxr::GfVec3f AiColor4DToGfVector3f(const aiColor4D& color)
{
    return pxr::GfVec3f(color.r, color.g, color.b);
}


static aiMatrix4x4 GetLocalTransform(const aiNode* node)
{
    aiMatrix4x4 transform = node->mTransformation;
    auto parent = node->mParent;
    while (parent)
    {
        std::string name = parent->mName.data;
        // only take scale from root transform, if the parent has a parent then its not a root node
        if (parent->mParent)
        {
            // parent has a parent, not a root note, use full transform
            transform = parent->mTransformation * transform;
            parent = parent->mParent;
        }
        else
        {
            // this is a root node, only take scale
            aiVector3D pos, scale;
            aiQuaternion rot;
            parent->mTransformation.Decompose(scale, rot, pos);

            aiMatrix4x4 scale_mat;
            transform = aiMatrix4x4::Scaling(scale, scale_mat) * transform;

            break;
        }
    }
    return transform;
}


pxr::SdfPath SimpleImport(pxr::UsdStageRefPtr usdStage, std::string path, const aiScene* mScene, const bool loadMaterials)
{
    std::vector<Mesh> mMeshPrims;
    std::vector<aiNode*> nodesToProcess;
    std::vector<std::pair<int, aiMatrix4x4>> meshTransforms;
    // Traverse tree and get all of the meshes and the full transform for that node
    nodesToProcess.push_back(mScene->mRootNode);
    while (nodesToProcess.size() > 0)
    {
        // remove the node
        aiNode* node = nodesToProcess.back();
        if (!node)
        {
            // printf("INVALID NODE\n");
            continue;
        }
        nodesToProcess.pop_back();
        aiMatrix4x4 transform = GetLocalTransform(node);
        for (size_t i = 0; i < node->mNumMeshes; i++)
        {
            meshTransforms.push_back(std::pair<int, aiMatrix4x4>(node->mMeshes[i], transform));
        }
        // process any meshes in this node:
        for (size_t i = 0; i < node->mNumChildren; i++)
        {
            nodesToProcess.push_back(node->mChildren[i]);
        }
    }
    // printf("%s TOTAL MESHES: %d\n", path.c_str(), meshTransforms.size());
    mMeshPrims.resize(meshTransforms.size());


    // for (size_t i = 0; i < mScene->mNumMaterials; i++)
    // {
    //     auto material = mScene->mMaterials[i];
    //     // printf("AA %d %s \n", i, material->GetName().C_Str());
    // }

    for (size_t i = 0; i < meshTransforms.size(); i++)
    {
        auto transformedMesh = meshTransforms[i];
        auto assimpMesh = mScene->mMeshes[transformedMesh.first];
        // printf("material index: %d \n", assimpMesh->mMaterialIndex);
        // Gather all mesh points information to sort
        std::vector<Mesh> meshImported;

        for (size_t j = 0; j < assimpMesh->mNumVertices; j++)
        {
            auto vertex = assimpMesh->mVertices[j];
            vertex *= transformedMesh.second;
            mMeshPrims[i].points.push_back(AiVector3dToGfVector3f(vertex));
        }
        for (size_t j = 0; j < assimpMesh->mNumFaces; j++)
        {
            const aiFace& face = assimpMesh->mFaces[j];
            if (face.mNumIndices >= 3)
            {
                for (size_t k = 0; k < face.mNumIndices; k++)
                {
                    mMeshPrims[i].faceVertexIndices.push_back(face.mIndices[k]);
                }
            }
        }

        for (size_t j = 0; j < assimpMesh->mNumFaces; j++)
        {
            const aiFace& face = assimpMesh->mFaces[j];
            if (face.mNumIndices >= 3)
            {
                for (size_t k = 0; k < face.mNumIndices; k++)
                {
                    if (assimpMesh->mNormals)
                    {
                        mMeshPrims[i].normals.push_back(AiVector3dToGfVector3f(assimpMesh->mNormals[face.mIndices[k]]));
                    }

                    for (size_t m = 0; m < mMeshPrims[i].uvs.size(); m++)
                    {
                        mMeshPrims[i].uvs[m].push_back(
                            AiVector3dToGfVector2f(assimpMesh->mTextureCoords[m][face.mIndices[k]]));
                    }

                    for (size_t m = 0; m < mMeshPrims[i].colors.size(); m++)
                    {
                        mMeshPrims[i].colors[m].push_back(AiColor4DToGfVector3f(assimpMesh->mColors[m][face.mIndices[k]]));
                    }
                }
                mMeshPrims[i].faceVertexCounts.push_back(face.mNumIndices);
            }
        }
    }

    auto usdMesh =
        pxr::UsdGeomMesh::Define(usdStage, pxr::SdfPath(omni::isaac::urdf::GetNewSdfPathString(usdStage, path)));


    pxr::VtArray<pxr::GfVec3f> allPoints;
    pxr::VtArray<int> allFaceVertexCounts;
    pxr::VtArray<int> allFaceVertexIndices;
    pxr::VtArray<pxr::GfVec3f> allNormals;
    pxr::VtArray<pxr::VtArray<pxr::GfVec2f>> uvs;
    pxr::VtArray<pxr::VtArray<pxr::GfVec3f>> allColors;

    size_t indexOffset = 0;
    size_t vertexOffset = 0;
    std::map<int, pxr::VtArray<int>> materialMap;
    for (size_t m = 0; m < meshTransforms.size(); m++)
    {
        auto transformedMesh = meshTransforms[m];
        auto mesh = mScene->mMeshes[transformedMesh.first];
        auto& meshPrim = mMeshPrims[m];

        for (size_t k = 0; k < meshPrim.uvs.size(); k++)
        {
            uvs.push_back(meshPrim.uvs[k]);
        }

        for (size_t i = 0; i < meshPrim.points.size(); i++)
        {
            allPoints.push_back(meshPrim.points[i]);
        }

        for (size_t i = 0; i < meshPrim.faceVertexCounts.size(); i++)
        {
            allFaceVertexCounts.push_back(meshPrim.faceVertexCounts[i]);
        }

        for (size_t i = 0; i < meshPrim.faceVertexIndices.size(); i++)
        {
            allFaceVertexIndices.push_back(static_cast<int>(meshPrim.faceVertexIndices[i] + indexOffset));
        }
        for (size_t i = vertexOffset; i < vertexOffset + meshPrim.faceVertexCounts.size(); i++)
        {
            materialMap[mesh->mMaterialIndex].push_back(static_cast<int>(i));
        }
        // printf("faceVertexOffset %d %d %d %d\n", indexOffset, points.size(), vertexOffset, faceVertexCounts.size());
        indexOffset = indexOffset + meshPrim.points.size();
        vertexOffset = vertexOffset + meshPrim.faceVertexCounts.size();

        for (size_t i = 0; i < meshPrim.normals.size(); i++)
        {
            allNormals.push_back(meshPrim.normals[i]);
        }
    }

    usdMesh.CreatePointsAttr(pxr::VtValue(allPoints));
    usdMesh.CreateFaceVertexCountsAttr(pxr::VtValue(allFaceVertexCounts));
    usdMesh.CreateFaceVertexIndicesAttr(pxr::VtValue(allFaceVertexIndices));

    pxr::VtArray<pxr::GfVec3f> Extent;
    pxr::UsdGeomPointBased::ComputeExtent(allPoints, &Extent);
    usdMesh.CreateExtentAttr().Set(Extent);

    // Normals
    if (!allNormals.empty())
    {
        usdMesh.CreateNormalsAttr(pxr::VtValue(allNormals));
        usdMesh.SetNormalsInterpolation(pxr::UsdGeomTokens->faceVarying);
    }

    // Texture UV
    for (size_t j = 0; j < uvs.size(); j++)
    {
        pxr::TfToken stName;
        if (j == 0)
        {
            stName = pxr::TfToken("st");
        }
        else
        {
            stName = pxr::TfToken("st_" + std::to_string(j));
        }
        auto Primvar =
            usdMesh.CreatePrimvar(stName, pxr::SdfValueTypeNames->Float2Array, pxr::UsdGeomTokens->faceVarying);
        Primvar.Set(uvs[j]);
    }

    usdMesh.CreateSubdivisionSchemeAttr(pxr::VtValue(pxr::TfToken("none")));
    if (loadMaterials)
    {
        std::string prefix_path = usdStage->GetDefaultPrim().GetPrimPath().GetString();
        // For each material, store the face indices and create GeomSubsets
        for (auto const& mat : materialMap)
        {
            std::string name(mScene->mMaterials[mat.first]->GetName().C_Str());
            // printf("materials: %s\n", name.c_str());

            pxr::UsdPrim prim;
            pxr::UsdShadeMaterial matPrim;
            prim = usdStage->GetPrimAtPath(
                pxr::SdfPath(prefix_path + "/Looks/" + makeValidUSDIdentifier("material_" + name)));
            if (prim)
            {
                matPrim = pxr::UsdShadeMaterial(prim);
            }
            else
            {
                matPrim = pxr::UsdShadeMaterial::Define(
                    usdStage, pxr::SdfPath(prefix_path + "/Looks/" + makeValidUSDIdentifier("material_" + name)));
                pxr::UsdShadeShader pbrShader = pxr::UsdShadeShader::Define(
                    usdStage,
                    pxr::SdfPath(prefix_path + "/Looks/" + makeValidUSDIdentifier("material_" + name) + "/Shader"));
                pbrShader.CreateIdAttr(pxr::VtValue(pxr::UsdImagingTokens->UsdPreviewSurface));

                aiColor3D color;
                if (mScene->mMaterials[mat.first]->Get(AI_MATKEY_COLOR_DIFFUSE, color) == aiReturn_SUCCESS)
                {
                    pbrShader.CreateInput(pxr::TfToken("diffuseColor"), pxr::SdfValueTypeNames->Color3f)
                        .Set(pxr::GfVec3f(color.r, color.g, color.b));
                }
                if (mScene->mMaterials[mat.first]->Get(AI_MATKEY_COLOR_SPECULAR, color) == aiReturn_SUCCESS)
                {
                    pbrShader.CreateInput(pxr::TfToken("specularColor"), pxr::SdfValueTypeNames->Color3f)
                        .Set(pxr::GfVec3f(color.r, color.g, color.b));
                }
                if (mScene->mMaterials[mat.first]->Get(AI_MATKEY_COLOR_EMISSIVE, color) == aiReturn_SUCCESS)
                {
                    pbrShader.CreateInput(pxr::TfToken("emissiveColor"), pxr::SdfValueTypeNames->Color3f)
                        .Set(pxr::GfVec3f(color.r, color.g, color.b));
                }

                auto output = matPrim.CreateSurfaceOutput();
                output.ConnectToSource(pbrShader, pxr::TfToken("surface"));
            }


            auto geomSubset = pxr::UsdGeomSubset::Define(
                usdStage, pxr::SdfPath(usdMesh.GetPath().GetString() + "/material_" + std::to_string(mat.first)));
            geomSubset.CreateElementTypeAttr(pxr::VtValue(pxr::TfToken("face")));
            geomSubset.CreateFamilyNameAttr(pxr::VtValue(pxr::TfToken("materialBind")));
            geomSubset.CreateIndicesAttr(pxr::VtValue(mat.second));
            if (matPrim)
            {
                pxr::UsdShadeMaterialBindingAPI mbi(geomSubset);
                mbi.Bind(matPrim);
            }
        }
    }

    return usdMesh.GetPath();
}

}
}
}
