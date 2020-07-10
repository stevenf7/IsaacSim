import omni
import carb
import pxr
from pxr import UsdShade, Sdf, Gf, Vt, UsdGeom
from pxr.Vt import IntArray, Vec3fArray
import random
import os
import shutil
import re
import numpy as np

# class usdMeshExporter:
#     def __init__(self, mesh):


def createInMemoryStage(path):
    stage = pxr.Usd.Stage.CreateNew(path)
    pxr.UsdGeom.SetStageUpAxis(stage, pxr.UsdGeom.Tokens.z)
    return stage


def create_material(stage, _mtl_path, props):
    mat_prim = stage.DefinePrim(_mtl_path, "Material")
    material_prim = UsdShade.Material.Get(stage, mat_prim.GetPath())
    if material_prim:
        shader_path = stage.DefinePrim("{}/Shader".format(_mtl_path), "Shader")
        shader_prim = UsdShade.Shader.Get(stage, shader_path.GetPath())
        if shader_prim:

            shader_out = shader_prim.CreateOutput("out", Sdf.ValueTypeNames.Token)
            material_prim.CreateSurfaceOutput("mdl").ConnectToSource(shader_out)
            material_prim.CreateVolumeOutput("mdl").ConnectToSource(shader_out)
            material_prim.CreateDisplacementOutput("mdl").ConnectToSource(shader_out)
            shader_prim.GetImplementationSourceAttr().Set(UsdShade.Tokens.sourceAsset)
            shader_prim.SetSourceAsset(Sdf.AssetPath("OmniPBR.mdl"), "mdl")
            shader_prim.SetSourceAssetSubIdentifier("OmniPBR", "mdl")

            omni.kit.usd.create_material_input(
                mat_prim,
                "diffuse_color_constant",
                Gf.Vec3f(props.rgba_color.r, props.rgba_color.g, props.rgba_color.b),
                Sdf.ValueTypeNames.Color3f,
            )
            omni.kit.usd.create_material_input(
                mat_prim,
                "emissive_color",
                Gf.Vec3f(props.emmissive.r, props.emmissive.g, props.emmissive.b),
                Sdf.ValueTypeNames.Color3f,
            )
            omni.kit.usd.create_material_input(mat_prim, "metallic_constant", props.metallic, Sdf.ValueTypeNames.Float)
            omni.kit.usd.create_material_input(
                mat_prim, "reflection_roughness_constant", props.roughness, Sdf.ValueTypeNames.Float
            )
            omni.kit.usd.create_material_input(
                mat_prim, "enable_emission", props.emmissive.a > 0, Sdf.ValueTypeNames.Bool
            )
        else:
            carb.log_warn(f"failed to create shader {shader_path}")
    else:
        carb.log_warn(f"failed to create prim {mat_prim.GetPath().pathString}")
    return False


def export_material_list(material_list, path):
    stage = createInMemoryStage(path)
    looks_prim = stage.DefinePrim("/Looks", "Scope")
    stage.SetDefaultPrim(looks_prim)
    out_list = []  # List that contains all materials Path as they are in the stage.
    for i, mat in enumerate(material_list):
        name = "/Looks/Material_{}".format(i)
        create_material(stage, name, mat)
        out_list.append(name[1:])  # Remove first slash from name
    stage.Save()
    return out_list


def make_array(_type, a):
    if _type == "float":
        return Vec3fArray([Gf.Vec3f(float(a[i][0]), float(a[i][1]), float(a[i][2])) for i in range(a.shape[0])])
    elif _type == "int":
        al = a.flatten().tolist()
        return IntArray(al)


class PartExporter:
    def __init__(self, part, path, part_name, tree_model, assemblies_as_usds=True):
        self.part = part
        self.path = path
        self.part_name = part_name
        self._make_assembly_usd = assemblies_as_usds
        self.materials_path = ""
        self.material_list = []
        self.mesh_paths = []
        self.assemblies_prims = []
        self.assemblies_path = [None]
        self.stage = None
        self.tree_model = tree_model

    def reset(self):
        self.part = None

    def __call__(self, a, b):
        part_path = os.path.join(self.path, self.part_name)
        self.path = part_path
        shutil.rmtree(part_path, True)
        materials_path = os.path.join(part_path, "materials")
        os.makedirs(materials_path)
        self.materials_path = os.path.join(materials_path, "colors.usd")
        material_list = export_material_list(self.part.materials, self.materials_path)
        meshes_path = os.path.join(part_path, "meshes")
        os.makedirs(meshes_path)
        self.mesh_paths = export_mesh_list(self.part.meshes, meshes_path, self.materials_path, self.part.materials)
        if self._make_assembly_usd:
            self.assemblies_path = [None for i in range(len(self.part.assemblies))]
        else:
            stage_name = re.sub(r"[\W,_]+", "_", self.part_name)
            stage_path = os.path.join(self.path, stage_name + ".usd")
            self.stage = createInMemoryStage(stage_path)
        self.assemblies_path[0] = self.export_assembly("/Root", 0)
        print(len(self.mesh_paths), len(self.assemblies_path))
        if self._make_assembly_usd:
            stage_path = self.assemblies_path[0]
        self.tree_model.add_part(self.part, self.assemblies_path, self.mesh_paths)
        result = omni.usd.get_context().open_stage(stage_path.strip(), None)

    def get_assembly(self, index):
        if self._make_assembly_usd:
            return self.assemblies_path[index]
        return None

    def export_assembly(self, path, index):
        if self.get_assembly(index) is None:
            assembly = self.part.assemblies[index]
            # print(assembly.name)
            assembly_name = re.sub(r"[\W,_]+", "_", assembly.name)
            if assembly_name[0].isdigit():
                assembly_name = "a_" + assembly_name
            if self._make_assembly_usd:
                count = 0
                assembly_path = os.path.join(self.path, assembly_name + ".usd")
                while os.path.isfile(assembly_path):
                    count += 1
                    assembly_path = os.path.join(self.path, "{}_{:02d}.usd".format(assembly_name, count))
                self.assemblies_path[index] = assembly_path
                stage = createInMemoryStage(assembly_path)
                path = "/Root"
            else:
                stage = self.stage
                count = 0
                root_path = path
                while stage.GetPrimAtPath(root_path):
                    count += 1
                    root_path = "{}_{:02d}".format(path, count)
                path = root_path
            root = UsdGeom.Xform.Define(stage, path).GetPrim()
            if self._make_assembly_usd:
                stage.SetDefaultPrim(root)

            for c in assembly.sub_assemblies:
                sub_assembly = self.part.assemblies[c.id]
                sub_assembly_name = re.sub(r"[\W,_]+", "_", sub_assembly.name)
                sub_assembly_path = self.export_assembly(path + "/" + sub_assembly_name, c.id)
                if sub_assembly_name[0].isdigit():
                    sub_assembly_name = "a_" + sub_assembly_name
                usd_sub_path = "{}/{}".format(path, sub_assembly_name)
                count = 0
                while stage.GetPrimAtPath(usd_sub_path):
                    count += 1
                    usd_sub_path = "{}/{}_{:02d}".format(path, sub_assembly_name, count)
                if self._make_assembly_usd:
                    xform = UsdGeom.Xform.Define(stage, usd_sub_path).GetPrim()
                    xform.GetReferences().AddReference(os.path.relpath(sub_assembly_path, self.path))
                else:
                    xform = stage.GetPrimAtPath(sub_assembly_path)
                set_pose(xform, c.pose)
            for c in assembly.meshes:
                mesh = self.part.meshes[c.id]
                mesh_path = self.mesh_paths[c.id]
                mesh_name = re.sub(r"[\W,_]+", "_", mesh.name)
                if mesh_name[0].isdigit():
                    mesh_name = "m_" + mesh_name
                usd_sub_path = "{}/{}".format(path, mesh_name)
                count = 0
                while stage.GetPrimAtPath(usd_sub_path):
                    count += 1
                    usd_sub_path = "{}/{}_{:02d}".format(path, mesh_name, count)
                xform = UsdGeom.Xform.Define(stage, usd_sub_path).GetPrim()
                xform.GetReferences().AddReference(os.path.relpath(mesh_path, self.path))
                set_pose(xform, c.pose)
            stage.Save()
        if self._make_assembly_usd:
            return self.assemblies_path[index]
        return root.GetPath()


def set_pose(prim, pose):
    xform = UsdGeom.Xformable(prim)
    xform.ClearXformOpOrder()
    xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
    rot_mat = Gf.Matrix3d(Gf.Quatd(pose.r.w, pose.r.x, pose.r.y, pose.r.z))
    pos_vec = Gf.Vec3d(pose.p.x, pose.p.y, pose.p.z)
    xform_op.Set(Gf.Matrix4d().SetRotate(rot_mat).SetTranslateOnly(pos_vec))


def bind_material(stage, prim, mat_path):
    material_prim = stage.GetPrimAtPath(mat_path)
    material = UsdShade.Material(material_prim)
    binding_api = UsdShade.MaterialBindingAPI(prim)
    binding_api.Bind(material)


def export_mesh_list(mesh_list, path, materials_stage, materials_list):
    mesh_names = []
    for mesh in mesh_list:
        name = create_usd_mesh(mesh, path, materials_stage, materials_list)
        mesh_names.append(name)
    return mesh_names


def create_usd_mesh(mesh, path, materials_stage, materials_list):
    count = 0
    mesh_name = re.sub(r"[\W,_]+", "_", mesh.name)
    if mesh_name[0].isdigit():
        mesh_name = "m_" + mesh_name
    # Find next available filename to avoid overwriting meshes that potentially have the same name
    stage_path = os.path.join(path, "{}.usd".format(mesh_name))
    while os.path.isfile(stage_path):
        count += 1
        stage_path = os.path.join(path, "{}_{:02d}.usd".format(mesh_name, count))
    # Create empty stage and create an XForm Root
    stage = createInMemoryStage(stage_path)
    mesh_name = "/Root/{}".format(mesh_name)
    root = UsdGeom.Xform.Define(stage, "/Root").GetPrim()
    stage.SetDefaultPrim(root)
    # add Material list as a reference

    materials = stage.DefinePrim("/Root/Looks", "Scope")
    face_materials = mesh.get_face_materials()

    # materials.GetReferences().AddReference(os.path.relpath(materials_stage, path))
    usdMesh = UsdGeom.Mesh.Define(stage, mesh_name)

    Vertex = make_array("float", mesh.get_vertices())
    VertexNormals = make_array("float", mesh.get_vertex_normals())
    faceVertexCount = IntArray([3 for i in range(int(mesh.get_triangles().shape[0] / 3))])
    facesIndices = make_array("int", mesh.get_triangles())
    # faceNormals = make_array(Vec3fArray, mesh.get_triangles_normals())

    usdMesh.CreatePointsAttr(Vertex)
    usdMesh.CreateNormalsAttr(VertexNormals)
    usdMesh.CreateFaceVertexCountsAttr(faceVertexCount)
    usdMesh.CreateFaceVertexIndicesAttr(facesIndices)
    usdMesh.SetNormalsInterpolation(pxr.UsdGeom.Tokens.faceVarying)

    extent = usdMesh.ComputeExtent(Vertex)
    usdMesh.CreateExtentAttr().Set(extent)

    mat_set = set(face_materials)
    for material in mat_set:
        name = "/Root/Looks/Material_{}".format(material)
        create_material(stage, name, materials_list[material])
        if len(mat_set) > 1:
            face_indices = np.where(face_materials == material)[0]
            subset_name = "{}/Material_{}".format(mesh_name, material)
            geomSubset = UsdGeom.Subset.Define(stage, subset_name)
            geomSubset.CreateElementTypeAttr("face")
            geomSubset.CreateFamilyNameAttr("materialBind")
            geomSubset.CreateIndicesAttr(IntArray(face_indices.tolist()))
            bind_material(stage, geomSubset, name)
        else:
            bind_material(stage, usdMesh, name)

    stage.Save()
    return stage_path
