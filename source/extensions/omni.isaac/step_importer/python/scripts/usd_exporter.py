import omni
import carb
import pxr
from pxr import UsdShade, Sdf, Gf, Vt, UsdGeom, UsdLux, Usd, Kind
from pxr.Vt import IntArray, Vec3fArray, Vec2fArray, DoubleArray
import random
import os
import shutil
import re
import tempfile
import numpy as np
import time
import glob

from omni.isaac.step_importer import _step_importer

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
        if a.shape[1] == 3:
            return Vec3fArray([Gf.Vec3f(float(a[i][0]), float(a[i][1]), float(a[i][2])) for i in range(a.shape[0])])
        if a.shape[1] == 2:
            return Vec2fArray([Gf.Vec2f(float(a[i][0]), float(a[i][1])) for i in range(a.shape[0])])
    elif _type == "int":
        al = a.flatten().tolist()
        return IntArray(al)


class PartExporter:

    tmp_prefix = "tmp_isaac_step_importer_"

    def __init__(self, si_interface, step_file, part, path, part_name, assemblies_as_usds=True, temp_dir_to_clean=None):
        self._si = si_interface
        self.step_file = step_file
        self.part = part
        self.base_folder = path
        self.part_name = part_name.strip()
        self._make_assembly_usd = assemblies_as_usds
        self.materials_path = ""
        self.material_list = []
        self.mesh_map = {}
        self.mesh_replacement_map = {}
        self.mesh_usd_paths = {}
        self.assemblies_prims = []
        self.assemblies_path = [None]
        self.stage = None
        self.preview = True
        self.tempdir = tempfile.TemporaryDirectory(prefix=self.tmp_prefix).name
        self._temp_dir_to_clean = temp_dir_to_clean

    def get_temp_dir(self):
        return self.tempdir

    def is_temp_stage_open(self):
        return os.path.split(self.tempdir)[1].replace("\\", "/").lower() in omni.usd.get_context().get_stage_url()

    def __del__(self):
        # Cleans after itself, deletes the temp folder
        temp_path_name = os.path.split(self.tempdir)[1]
        self._si.release_step_file(self.step_file)
        if self.is_temp_stage_open():
            tempdir = self.tempdir

            def delete_folder():
                shutil.rmtree(tempdir)

            omni.usd.get_context().new_stage(on_finish_fn=lambda a, b: delete_folder())
        else:
            shutil.rmtree(self.tempdir)

    def get_mesh_id(self, mesh_id):
        if mesh_id in self.mesh_replacement_map:
            return self.mesh_replacement_map[mesh_id]
        return mesh_id

    def get_mesh_path(self, mesh_id):
        mesh_id = self.get_mesh_id(mesh_id)
        if mesh_id in self.mesh_usd_paths:
            return self.mesh_usd_paths[mesh_id]
        return None

    def get_abs_and_rel_paths(self):
        directory = self.path.replace("\\", "/")
        glob_dir = os.path.join(directory, "**", "*")
        absolute_paths = []
        relative_paths = []

        def _remove_prefix(filename, base):
            if base in filename:
                return os.path.relpath(filename, base).replace("\\", "/")
            return filename

        for filename in glob.iglob(glob_dir, recursive=True):
            filename = filename.replace("\\", "/")
            if os.path.isfile(filename):
                relative_path = _remove_prefix(filename, os.path.dirname(directory))
                if relative_path != "/" and relative_path.startswith("/"):
                    relative_path = relative_path[1:]
                if len(relative_path) > 0:
                    absolute_paths.append(filename)
                    relative_paths.append(relative_path)

        return absolute_paths, relative_paths

    def export(self):
        """
        Exports a preview version of the assembly with low quality meshes, to allow tweaking per mesh,
        removing duplicates, and reorg the assembly structure.
        """
        base_folder = self.tempdir
        part_path = os.path.join(base_folder, self.part_name)
        self.path = part_path.replace("\\", "/")
        print("Creating assembly usd at", self.path)
        shutil.rmtree(part_path, True)
        materials_path = os.path.join(part_path, "materials").replace("\\", "/")
        os.makedirs(materials_path)
        self.materials_path = os.path.join(materials_path, "colors.usd")
        material_list = export_material_list(self.part.materials, self.materials_path)
        meshes_path = os.path.join(part_path, "meshes")
        os.makedirs(meshes_path)
        self.export_mesh_list(meshes_path, self.materials_path, self.part.materials)
        # for i, path in enumerate(self.mesh_paths):
        #     self.part.mesh_usd_paths[i] = path
        if self._make_assembly_usd:
            self.assemblies_path = [None for i in range(len(self.part.assemblies))]
        else:
            stage_name = re.sub(
                r"[\W,_]+", "_", self.part_name
            ).lower()  # Ensures use of lowercase path name because USD library always return lowercase name.
            stage_path = os.path.join(self.path, stage_name + ".usd")
            self.stage = createInMemoryStage(stage_path)
        self.assemblies_path[0] = self.export_assembly("/Root", 0)
        if self._make_assembly_usd:
            stage_path = self.assemblies_path[0]

        omni.usd.get_context().open_stage(stage_path.strip(), None)

    def get_assembly(self, index):
        if self._make_assembly_usd:
            return self.assemblies_path[index]
        return None

    def replace_duplicate_meshes(self, duplicate_indexes):
        base_idx = duplicate_indexes[0]
        for i in duplicate_indexes:
            self.part.mesh_replacement_map[i] = base_idx

    def export_assembly(self, path, index):
        if self.get_assembly(index) is None:
            assembly = self.part.assemblies[index]
            # print(assembly.name)
            assembly_name = re.sub(r"[\W,_]+", "_", assembly.name).lower()
            if assembly_name[0].isdigit():
                assembly_name = ("a_" + assembly_name).lower()
            if self._make_assembly_usd:
                count = 0
                assembly_path = os.path.join(self.path, assembly_name + ".usd").lower()
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
                sub_assembly_name = re.sub(r"[\W,_]+", "_", sub_assembly.name).lower()
                sub_assembly_path = self.export_assembly(path + "/" + sub_assembly_name, c.id)
                if sub_assembly_name[0].isdigit():
                    sub_assembly_name = "a_" + sub_assembly_name
                usd_sub_path = "{}/{}".format(path, sub_assembly_name.lower())
                count = 0
                while stage.GetPrimAtPath(usd_sub_path):
                    count += 1
                    usd_sub_path = "{}/{}_{:02d}".format(path, sub_assembly_name, count)
                if self._make_assembly_usd:
                    xform = stage.DefinePrim(usd_sub_path, "")
                    xform.GetReferences().AddReference(os.path.relpath(sub_assembly_path, self.path).replace("\\", "/"))
                else:
                    xform = stage.GetPrimAtPath(sub_assembly_path)
                set_pose(xform, c.pose)
            for c in assembly.meshes:
                mesh_id = self.get_mesh_id(c.id)
                mesh_props = self.part.meshes_properties[c.id]
                mesh_path = self.get_mesh_path(c.id)
                mesh_name = re.sub(r"[\W,_]+", "_", mesh_props.name).lower()
                if mesh_name[0].isdigit():
                    mesh_name = "m_" + mesh_name
                usd_sub_path = "{}/{}".format(path, mesh_name)
                count = 0
                while stage.GetPrimAtPath(usd_sub_path):
                    count += 1
                    usd_sub_path = "{}/{}_{:02d}".format(path, mesh_name, count)
                xform = stage.DefinePrim(usd_sub_path, "")
                xform.GetReferences().AddReference(os.path.relpath(mesh_path, self.path).replace("\\", "/"))
                # for child in xform.GetChildren():
                #     if "Looks" not in child.GetPath().pathString:
                #         pose = _step_importer.Transform()
                #         pose.p = mesh_props.com
                #         set_pose(child, pose)
                set_pose(xform, c.pose)

            distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
            distantLight.CreateIntensityAttr(3000)
            light_pose = _step_importer.Transform()
            light_pose.r.x = -0.383
            light_pose.r.y = 0
            light_pose.r.z = 0
            light_pose.r.w = 0.924
            set_pose(distantLight, light_pose)
            stage.Save()
        if self._make_assembly_usd:
            return self.assemblies_path[index]
        return root.GetPath()

    def export_mesh_list(self, path, materials_stage, materials_list):
        mesh_names = []
        props = _step_importer.Tesselation_Properties()
        props.max_linear_offset = 0.1
        props.max_angular_offset = 1.0
        props.min_surface = 1.0
        props.use_relative_offset = False
        props.use_internal_vertices = True
        props.volumetric_center_meshes = True
        for idx, meshprops in enumerate(self.part.meshes_properties):
            if idx not in self.mesh_map:
                mesh = _step_importer.Mesh()
                if self._si.get_mesh(self.step_file, idx, props, mesh):
                    name = create_usd_mesh(
                        mesh, meshprops, path, materials_stage, materials_list, props.volumetric_center_meshes
                    )
                    self.mesh_usd_paths[idx] = name
                    self.mesh_map[idx] = mesh
                else:
                    raise ("Unable to import mesh " + meshprops.name)
            else:
                mesh = self.mesh_map[idx]
                name = create_usd_mesh(
                    mesh, meshprops, path, materials_stage, materials_list, props.volumetric_center_meshes
                )
                self.mesh_usd_paths[idx] = name

    def export_mesh(self, mesh_index, props, open_stage=True):
        # TODO add multi-LOD
        if mesh_index in self.mesh_map:
            mesh = self.mesh_map[mesh_index]
        else:
            mesh = _step_importer.Mesh()
        path = os.path.join(self.path, "meshes")
        mesh_name = re.sub(r"[\W,_]+", "_", self.part.meshes_properties[mesh_index].name).lower()
        print("Converting", self.mesh_usd_paths[mesh_index])
        if mesh_name[0].isdigit():
            mesh_name = "m_" + mesh_name
        if self._si.get_mesh(self.step_file, mesh_index, props[0], mesh):
            name = create_usd_mesh_at_path(
                mesh,
                mesh_name,
                self.part.meshes_properties[mesh_index],
                path,
                self.mesh_usd_paths[mesh_index],
                self.materials_path,
                self.part.materials,
                props[0].volumetric_center_meshes,
            )
            del mesh
            mesh = None
            if open_stage:
                print("Opening", self.mesh_usd_paths[mesh_index])
                omni.usd.get_context().open_stage(self.mesh_usd_paths[mesh_index], None)


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


def create_usd_mesh(mesh, mesh_props, path, materials_stage, materials_list, move_to_com):
    count = 0
    mesh_name = re.sub(r"[\W,_]+", "_", mesh_props.name).lower()
    if mesh_name[0].isdigit():
        mesh_name = "m_" + mesh_name
    # Find next available filename to avoid overwriting meshes that potentially have the same name
    stage_path = os.path.join(path, "{}.usd".format(mesh_name))
    while os.path.isfile(stage_path):
        count += 1
        stage_path = os.path.join(path, "{}_{:02d}.usd".format(mesh_name, count))
    return create_usd_mesh_at_path(
        mesh, mesh_name, mesh_props, path, stage_path, materials_stage, materials_list, move_to_com
    )


def create_usd_mesh_at_path(
    mesh, mesh_name, mesh_props, path, stage_path, materials_stage, materials_list, move_to_com
):

    # Create empty stage and create an XForm Root
    stage = createInMemoryStage(stage_path)
    mesh_name = "/Root/{}".format(mesh_name)
    root = UsdGeom.Xform.Define(stage, "/Root").GetPrim()
    stage.SetDefaultPrim(root)

    # materials.GetReferences().AddReference(os.path.relpath(materials_stage, path).replace("\\", "/"))
    usdMesh = UsdGeom.Mesh.Define(stage, mesh_name)
    mesh_prim = stage.GetPrimAtPath(mesh_name)
    model_api = Usd.ModelAPI(mesh_prim)
    model_api.SetKind(Kind.Tokens.model)

    pose = _step_importer.Transform()
    pose.p = mesh_props.com
    set_pose(usdMesh, pose)
    Vertex = make_array("float", mesh.get_vertices())
    VertexNormals = make_array("float", mesh.get_vertex_normals())
    VertexUVs = make_array("float", mesh.get_vertex_UVs())
    faceVertexCount = IntArray([3 for i in range(int(mesh.get_triangles().shape[0] / 3))])
    facesIndices = make_array("int", mesh.get_triangles())
    # faceNormals = make_array(Vec3fArray, mesh.get_triangles_normals())

    usdMesh.CreatePointsAttr(Vertex)
    usdMesh.CreateNormalsAttr(VertexNormals)
    usdMesh.CreateFaceVertexCountsAttr(faceVertexCount)
    usdMesh.CreateFaceVertexIndicesAttr(facesIndices)

    # TODO: Use PhysicsAPI to set mass and inertia to ensure forward compatibility
    mesh_prim.CreateAttribute("mass", Sdf.ValueTypeNames.Double, False).Set(
        mesh_props.volume * mesh_props.density / 1000.0
    )  # density is in g/cm3
    inertia_Diag_Matrix = mesh_props.get_inertia_diag_matrix()
    mesh_prim.CreateAttribute("diagonalInertia", Sdf.ValueTypeNames.Double3, False).Set(
        Gf.Vec3d(
            float(inertia_Diag_Matrix[0] / 1000.0),
            float(inertia_Diag_Matrix[2] / 1000.0),
            float(inertia_Diag_Matrix[5] / 1000.0),
        )
    )

    # Store full inertia tensor diagonal matrix (Ixx Ixy Iyy Ixz Izy Izz) for eventual computations
    mesh_prim.CreateAttribute("inertiaDiagonalMatrix", Sdf.ValueTypeNames.DoubleArray, False).Set(
        DoubleArray([float(i) / 1000.0 for i in inertia_Diag_Matrix])
    )

    # usdMesh.SetNormalsInterpolation(pxr.UsdGeom.Tokens.faceVarying)
    texCoord = usdMesh.CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.varying)
    texCoord.Set(VertexUVs)
    usdMesh.CreateSubdivisionSchemeAttr("none")
    usdMesh.CreateTriangleSubdivisionRuleAttr("smooth")
    extent = usdMesh.ComputeExtent(Vertex)
    usdMesh.CreateExtentAttr().Set(extent)

    distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
    distantLight.CreateIntensityAttr(3000)
    light_pose = _step_importer.Transform()
    light_pose.r.x = -0.383
    light_pose.r.y = 0
    light_pose.r.z = 0
    light_pose.r.w = 0.924
    set_pose(distantLight, light_pose)

    # Face materials
    face_materials = mesh.get_face_materials()
    mat_set = set(face_materials)
    stage.DefinePrim("/Root/Looks", "Scope")
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
