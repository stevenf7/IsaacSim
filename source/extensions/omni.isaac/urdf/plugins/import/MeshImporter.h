#pragma once
// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "assimp/Importer.hpp"
#include "assimp/postprocess.h"
#include "assimp/scene.h"
#include <unordered_set>
#include <stack>
#include <set>
#include <experimental/filesystem>
#include <cmath>


struct MeshPoint
{
    size_t index;
    std::vector<float> values;

    bool operator==(const MeshPoint& other) const
    {
        if (values.size() != other.values.size())
        {
            return false;
        }

        for (size_t i = 0; i < values.size(); i++)
        {
            if (values[i] != other.values[i])
            {
                return false;
            }
        }

        return true;
    }

    bool operator<(const MeshPoint& other) const
    {
        for (size_t i = 0; i < values.size(); i++)
        {
            if (values[i] < other.values[i])
            {
                return true;
            }
            else if (values[i] > other.values[i])
            {
                return false;
            }
        }

        return false;
    }
};

struct Mesh
{
    // Assimp will split meshes into several pieces if it has multiple materials attached.
    // Importer will group them under the same xform node.
    std::string groupName;

    // Group Prim path
    pxr::SdfPath groupPrimPath;

    // This is the unique name across stage
    std::string uniqueName;

    // This is only useful for separate mesh export.
    // For single file export, all meshes will share the same layer.
    std::string layerAbsolutePath;

    // Prim path of this mesh.
    pxr::SdfPath primPath;

    // Remapping information of mesh points
    size_t remappingVertexCount;
    std::vector<bool> keepPoints;
    std::vector<size_t> indexRemapping;

    // If exportPointerInstancer is true, it will export pointer instancer for this mesh.
    // pointerInstances hosts the indexes of mMeshInstances
    bool exportPointerInstancer;
    pxr::SdfPath pointInstancerPath;
    std::vector<size_t> pointerInstances;

    // It will hosts the indexes of mMeshInstances that will not be exported as pointer instancer.
    std::vector<size_t> instances;
};

const static std::string ASSIMP_INSERTED_NODE_PATTERN = "$Assimp";

static pxr::GfMatrix4d AiMatrixToGfMatrix(const aiMatrix4x4& matrix)
{
    return pxr::GfMatrix4d(matrix.a1, matrix.b1, matrix.c1, matrix.d1, matrix.a2, matrix.b2, matrix.c2, matrix.d2,
                           matrix.a3, matrix.b3, matrix.c3, matrix.d3, matrix.a4, matrix.b4, matrix.c4, matrix.d4);
}

static aiMatrix4x4 GetLocalTransform(const aiNode* node)
{
    aiMatrix4x4 transform = node->mTransformation;
    auto parent = node->mParent;
    while (parent)
    {
        std::string name = parent->mName.data;
        if (name.find(ASSIMP_INSERTED_NODE_PATTERN) != std::string::npos)
        {
            transform = parent->mTransformation * transform;
            parent = parent->mParent;
        }
        else
        {
            break;
        }
    }

    return transform;
}
static std::string MakeValidUSDIdentifier(const std::string& name)
{
    auto validName = pxr::TfMakeValidIdentifier(name);
    if (validName[0] == '_')
    {
        validName = "a" + validName;
    }

    return validName;
}
static pxr::SdfPath SimpleImport(pxr::UsdStageRefPtr usdStage,
                                 std::string path,
                                 const aiScene* mScene,
                                 const bool loadMaterials = true)
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
        nodesToProcess.pop_back();
        // process any meshes in this node:
        aiMatrix4x4 transform = GetLocalTransform(node);
        for (size_t i = 0; i < node->mNumMeshes; i++)
        {
            meshTransforms.push_back(std::pair<int, aiMatrix4x4>(node->mMeshes[i], transform));
        }

        for (size_t i = 0; i < node->mNumChildren; i++)
        {
            nodesToProcess.push_back(node->mChildren[i]);
        }
    }

    mMeshPrims.resize(meshTransforms.size());

    for (size_t i = 0; i < meshTransforms.size(); i++)
    {
        auto transformedMesh = meshTransforms[i];
        auto mesh = mScene->mMeshes[transformedMesh.first];
        // pxr::GfMatrix4d nodeMat = AiMatrixToGfMatrix(transformedMesh.second);
        // pxr::GfVec3d temp = nodeMat.ExtractTranslation();
        // printf("%d %d  TRANS: %f %f %f\n", i, transformedMesh.first, temp[0], temp[1], temp[2]);
        // Assimp will unweld all meshes by default. For FBX,
        // it will keep original control points to avoid use
        // unweld geometry.
        if (!mesh->HasControlPoints())
        {
            // Gather all mesh points information to sort
            std::vector<MeshPoint> meshPoints;
            size_t numUVChannels = mesh->GetNumUVChannels();
            size_t numColorChannels = mesh->GetNumColorChannels();
            for (size_t j = 0; j < mesh->mNumVertices; j++)
            {
                MeshPoint point;
                point.index = j;
                point.values.push_back(mesh->mVertices[j].x);
                point.values.push_back(mesh->mVertices[j].y);
                point.values.push_back(mesh->mVertices[j].z);
                if (mesh->mNormals)
                {
                    point.values.push_back(mesh->mNormals[j].x);
                    point.values.push_back(mesh->mNormals[j].y);
                    point.values.push_back(mesh->mNormals[j].z);
                }
                for (size_t k = 0; k < numUVChannels; k++)
                {
                    point.values.push_back(mesh->mTextureCoords[k][j].x);
                    point.values.push_back(mesh->mTextureCoords[k][j].y);
                }
                for (size_t k = 0; k < numColorChannels; k++)
                {
                    point.values.push_back(mesh->mColors[k][j].r);
                    point.values.push_back(mesh->mColors[k][j].g);
                    point.values.push_back(mesh->mColors[k][j].b);
                }
                meshPoints.push_back(point);
            }

            // Sort points to remove redudant one
            std::sort(meshPoints.begin(), meshPoints.end());

            std::vector<bool> keepPoints(mesh->mNumVertices, false);
            std::vector<size_t> referenceIndex(mesh->mNumVertices);

            // Find and mark all redundant points
            auto meshPoint = meshPoints[0];
            size_t currentIndex = meshPoint.index;
            referenceIndex[currentIndex] = currentIndex;
            keepPoints[currentIndex] = true;
            for (size_t j = 1; j < meshPoints.size(); j++)
            {
                if (meshPoints[j] == meshPoint)
                {
                    keepPoints[meshPoints[j].index] = false;
                    referenceIndex[meshPoints[j].index] = currentIndex;
                }
                else
                {
                    meshPoint = meshPoints[j];
                    currentIndex = meshPoint.index;
                    referenceIndex[currentIndex] = currentIndex;
                    keepPoints[currentIndex] = true;
                }
            }
            meshPoints.clear();

            // Keep only unique points
            size_t keepPointsSize = 0;
            std::vector<size_t> indexRemapping(mesh->mNumVertices);
            for (size_t j = 0; j < mesh->mNumVertices; j++)
            {
                if (keepPoints[j])
                {
                    indexRemapping[j] = keepPointsSize;
                    keepPointsSize++;
                }
            }

            // Remapping indexes for redundant points
            for (size_t j = 0; j < mesh->mNumVertices; j++)
            {
                if (!keepPoints[j])
                {
                    indexRemapping[j] = indexRemapping[referenceIndex[j]];
                }
            }

            mMeshPrims[i].keepPoints = keepPoints;
            mMeshPrims[i].remappingVertexCount = keepPointsSize;
            mMeshPrims[i].indexRemapping = indexRemapping;
        }

        // const std::string& meshName = Utils::MakeValidUSDIdentifier(mesh->mName.C_Str());
        // mMeshPrims[transformedMesh.first].uniqueName = meshName;
    }
    auto usdMesh = pxr::UsdGeomMesh::Define(usdStage, pxr::SdfPath(path));


    pxr::VtArray<pxr::GfVec3f> allPoints;
    pxr::VtArray<size_t> allFaceVertexCounts;
    pxr::VtArray<size_t> allFaceVertexIndices;
    pxr::VtArray<pxr::GfVec3f> allNormals;
    pxr::VtArray<pxr::VtArray<pxr::GfVec2f>> uvs;
    pxr::VtArray<pxr::VtArray<pxr::GfVec3f>> allColors;

    size_t indexOffset = 0;
    size_t vertexOffset = 0;
    std::map<int, pxr::VtArray<size_t>> materialMap;
    for (size_t m = 0; m < meshTransforms.size(); m++)
    {
        auto transformedMesh = meshTransforms[m];
        auto mesh = mScene->mMeshes[transformedMesh.first];
        auto& meshPrim = mMeshPrims[m];

        pxr::VtArray<pxr::GfVec3f> points;
        pxr::VtArray<size_t> faceVertexCounts;
        pxr::VtArray<size_t> faceVertexIndices;
        pxr::VtArray<pxr::VtArray<pxr::GfVec3f>> colors;
        pxr::VtArray<pxr::GfVec3f> normals;
        pxr::VtArray<pxr::GfVec3f> tangentX;
        pxr::VtArray<pxr::GfVec2f> uv[AI_MAX_NUMBER_OF_TEXTURECOORDS];
        pxr::VtArray<pxr::GfVec3f> color[AI_MAX_NUMBER_OF_COLOR_SETS];


        // Gather all mesh points information to sort
        std::vector<MeshPoint> meshPoints;
        size_t numUVChannels = mesh->GetNumUVChannels();
        size_t numColorChannels = mesh->GetNumColorChannels();

        if (mesh->HasControlPoints())
        {
            for (size_t j = 0; j < mesh->mNumControlPoints; j++)
            {
                auto vertex = mesh->mControlPoints[j];
                vertex *= transformedMesh.second;
                points.push_back(pxr::GfVec3f(vertex.x, vertex.y, vertex.z));
            }

            // Face varying data
            for (size_t j = 0; j < mesh->mNumVertices; j++)
            {
                if (mesh->mNormals)
                {
                    normals.push_back(pxr::GfVec3f(mesh->mNormals[j].x, mesh->mNormals[j].y, mesh->mNormals[j].z));
                }

                for (size_t k = 0; k < numUVChannels; k++)
                {
                    uv[k].push_back(pxr::GfVec2f(mesh->mTextureCoords[k][j].x, mesh->mTextureCoords[k][j].y));
                }

                for (size_t k = 0; k < numColorChannels; k++)
                {
                    color[k].push_back(pxr::GfVec3f(mesh->mColors[k][j].r, mesh->mColors[k][j].g, mesh->mColors[k][j].b));
                }
            }

            for (size_t j = 0; j < mesh->mNumFaces; j++)
            {
                aiFace face = mesh->mFaces[j];

                size_t facePointsCounts = 3;
                if (face.mNumIndices == 1)
                {
                    int v0 = mesh->mVertexIndices[face.mIndices[0]];
                    faceVertexIndices.push_back(v0);
                    faceVertexIndices.push_back(v0);
                    faceVertexIndices.push_back(v0);
                }
                else if (face.mNumIndices == 2)
                {
                    int v0 = mesh->mVertexIndices[face.mIndices[0]];
                    int v1 = mesh->mVertexIndices[face.mIndices[1]];
                    faceVertexIndices.push_back(v0);
                    faceVertexIndices.push_back(v1);
                    faceVertexIndices.push_back(v1);
                }
                else
                {
                    for (size_t i = 0; i < face.mNumIndices; i++)
                    {
                        int v = mesh->mVertexIndices[face.mIndices[i]];
                        faceVertexIndices.push_back(v);
                    }
                    facePointsCounts = face.mNumIndices;
                }
                faceVertexCounts.push_back(facePointsCounts);
            }
        }
        else
        {
            for (size_t j = 0; j < mesh->mNumFaces; j++)
            {
                aiFace face = mesh->mFaces[j];

                size_t facePointsCounts = 3;
                if (face.mNumIndices == 1)
                {
                    size_t v0 = meshPrim.indexRemapping[face.mIndices[0]];
                    faceVertexIndices.push_back(v0);
                    faceVertexIndices.push_back(v0);
                    faceVertexIndices.push_back(v0);
                }
                else if (face.mNumIndices == 2)
                {
                    size_t v0 = meshPrim.indexRemapping[face.mIndices[0]];
                    size_t v1 = meshPrim.indexRemapping[face.mIndices[1]];
                    faceVertexIndices.push_back(v0);
                    faceVertexIndices.push_back(v1);
                    faceVertexIndices.push_back(v1);
                }
                else
                {
                    for (size_t i = 0; i < face.mNumIndices; i++)
                    {
                        size_t v = meshPrim.indexRemapping[face.mIndices[i]];
                        faceVertexIndices.push_back(v);
                    }
                    facePointsCounts = face.mNumIndices;
                }
                faceVertexCounts.push_back(facePointsCounts);
            }

            pxr::VtArray<pxr::GfVec3f> vertexNormals;
            pxr::VtArray<pxr::GfVec2f> vertexUv[AI_MAX_NUMBER_OF_TEXTURECOORDS];
            pxr::VtArray<pxr::GfVec3f> vertexColor[AI_MAX_NUMBER_OF_COLOR_SETS];

            // Keep only unique points
            for (size_t j = 0; j < mesh->mNumVertices; j++)
            {
                if (meshPrim.keepPoints[j])
                {
                    auto vertex = mesh->mVertices[j];
                    vertex *= transformedMesh.second;
                    points.push_back(pxr::GfVec3f(vertex.x, vertex.y, vertex.z));
                    if (mesh->mNormals)
                    {
                        vertexNormals.push_back(
                            pxr::GfVec3f(mesh->mNormals[j].x, mesh->mNormals[j].y, mesh->mNormals[j].z));
                    }

                    for (size_t k = 0; k < numUVChannels; k++)
                    {
                        vertexUv[k].push_back(pxr::GfVec2f(mesh->mTextureCoords[k][j].x, mesh->mTextureCoords[k][j].y));
                    }

                    for (size_t k = 0; k < numColorChannels; k++)
                    {
                        vertexColor[k].push_back(
                            pxr::GfVec3f(mesh->mColors[k][j].r, mesh->mColors[k][j].g, mesh->mColors[k][j].b));
                    }
                }
            }

            // Convert to face varying data
            if (!vertexNormals.empty())
            {
                for (size_t j = 0; j < faceVertexIndices.size(); j++)
                {
                    auto vertexIndex = faceVertexIndices[j];
                    normals.push_back(vertexNormals[vertexIndex]);
                }
            }

            for (size_t k = 0; k < numUVChannels; k++)
            {
                for (size_t j = 0; j < faceVertexIndices.size(); j++)
                {
                    auto vertexIndex = faceVertexIndices[j];
                    uv[k].push_back(vertexUv[k][vertexIndex]);
                }
            }

            for (size_t k = 0; k < numColorChannels; k++)
            {
                for (size_t j = 0; j < faceVertexIndices.size(); j++)
                {
                    auto vertexIndex = faceVertexIndices[j];
                    color[k].push_back(vertexColor[k][vertexIndex]);
                }
            }
        }


        for (size_t k = 0; k < numUVChannels; k++)
        {
            uvs.push_back(uv[k]);
        }

        for (size_t k = 0; k < numColorChannels; k++)
        {
            allColors.push_back(color[k]);
        }


        for (size_t i = 0; i < points.size(); i++)
        {
            allPoints.push_back(points[i]);
        }

        for (size_t i = 0; i < faceVertexCounts.size(); i++)
        {
            allFaceVertexCounts.push_back(faceVertexCounts[i]);
        }

        for (size_t i = 0; i < faceVertexIndices.size(); i++)
        {
            allFaceVertexIndices.push_back(faceVertexIndices[i] + indexOffset);
        }
        for (size_t i = vertexOffset; i < vertexOffset + faceVertexCounts.size(); i++)
        {
            materialMap[mesh->mMaterialIndex].push_back(i);
        }
        // printf("faceVertexOffset %d %d %d %d\n", indexOffset, points.size(), vertexOffset, faceVertexCounts.size());
        indexOffset = indexOffset + points.size();
        vertexOffset = vertexOffset + faceVertexCounts.size();

        for (size_t i = 0; i < normals.size(); i++)
        {
            allNormals.push_back(normals[i]);
        }
    }

    usdMesh.CreatePointsAttr(pxr::VtValue(allPoints));
    usdMesh.CreateFaceVertexCountsAttr(pxr::VtValue(allFaceVertexCounts));
    usdMesh.CreateFaceVertexIndicesAttr(pxr::VtValue(allFaceVertexIndices));

    pxr::VtArray<pxr::GfVec3f> Extent;
    pxr::UsdGeomPointBased::ComputeExtent(allPoints, &Extent);
    usdMesh.CreateExtentAttr().Set(Extent);

    // // Vertex color
    // if (!allColors.empty())
    // {
    //     auto Primvar = usdMesh.CreateDisplayColorPrimvar(pxr::UsdGeomTokens->faceVarying);
    //     Primvar.Set(allColors[0]);
    //     // TODO : set multi colors
    // }

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


            pxr::UsdPrim prim;
            pxr::UsdShadeMaterial matPrim;
            prim = usdStage->GetPrimAtPath(
                pxr::SdfPath(prefix_path + "/Looks/" + MakeValidUSDIdentifier("material_" + name)));
            if (prim)
            {
                matPrim = pxr::UsdShadeMaterial(prim);
            }
            else
            {
                matPrim = pxr::UsdShadeMaterial::Define(
                    usdStage, pxr::SdfPath(prefix_path + "/Looks/" + MakeValidUSDIdentifier("material_" + name)));
                pxr::UsdShadeShader pbrShader = pxr::UsdShadeShader::Define(
                    usdStage,
                    pxr::SdfPath(prefix_path + "/Looks/" + MakeValidUSDIdentifier("material_" + name) + "/Shader"));
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
