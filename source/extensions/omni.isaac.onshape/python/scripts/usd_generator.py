from numpy.core.einsumfunc import _greedy_path
from numpy.lib import ufunclike
import omni
import carb
from carb._carb import Float3, Float4
import pxr
from pxr import UsdShade, Sdf, Gf, Vt, UsdGeom, UsdLux, Usd, Kind, UsdPhysics, PhysxSchema
from pxr.Vt import IntArray, Vec3fArray, Vec2fArray, DoubleArray
import random
import os
import shutil
import re
import tempfile
import numpy as np
import time
import glob
import copy
import ctypes
import sys
import asyncio

import base64
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading

from omni.isaac.onshape.widgets.color_name import ColorName
from omni.isaac.onshape.widgets.visual_materials_widget import VisualMaterial
from omni.isaac.onshape.widgets.assembly_widget import Mate


import unicodedata
import re


def make_valid_filename(value):
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value)
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def TraversePrim(prim, filterfn=None):
    """
    Extract all sub-childrens from a given prim, on a breadth-first search, cutting the search if a sub-prim does not
    match the filter function criteria
    """
    childrenStack = [prim]
    out = prim.GetChildren()
    while len(childrenStack) > 0:
        prim = childrenStack.pop(0)
        if not filterfn or (filterfn and filterfn(prim)):
            children = prim.GetChildren()
            childrenStack = childrenStack + children
            out = out + children
    return out


def get_next_available(paths_list, path):
    extension = ""
    i = 0
    while path + extension in paths_list:
        i += 1
        extension = "_{:02d}".format(i)
    return path + extension


def terminate_thread(thread):
    """Terminates a python thread from another thread.

    :param thread: a threading.Thread instance
    """
    if not thread.isAlive():
        return

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def bind_material(stage, prims, mat_path):
    material_prim = stage.GetPrimAtPath(mat_path)
    material = UsdShade.Material(material_prim)
    if type(prims) is not list:
        prims = [prims]
    for prim in prims:
        binding_api = UsdShade.MaterialBindingAPI(prim)
        binding_api.Bind(material)


def make_array(_type, a):
    if _type == "float":
        if a.shape[1] == 3:
            return Vec3fArray([Gf.Vec3f(float(a[i][0]), float(a[i][1]), float(a[i][2])) for i in range(a.shape[0])])
        if a.shape[1] == 2:
            return Vec2fArray([Gf.Vec2f(float(a[i][0]), float(a[i][1])) for i in range(a.shape[0])])
    elif _type == "int":
        al = a.flatten().tolist()
        return IntArray(al)


def createInMemoryStage(path):
    if os.path.isfile(path):
        stage = pxr.Usd.Stage.Open(path)
    else:
        stage = pxr.Usd.Stage.CreateNew(path)
        pxr.UsdGeom.SetStageUpAxis(stage, pxr.UsdGeom.Tokens.z)
    return stage


class Transform:
    def __init__(self, p: Float3 = Float3(), r: Float4 = Float4()):
        self.p = p
        self.r = r


def convertColor(color_str):
    return bytearray(base64.b64decode(color_str))


def set_pose(prim, pose):
    xform = UsdGeom.Xformable(prim)
    # xform.ClearXformOpOrder()
    ops = xform.GetOrderedXformOps()
    if ops:
        xform_op = ops[0]
    else:
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
    rot_mat = Gf.Matrix3d(Gf.Quatd(pose.r.w, pose.r.x, pose.r.y, pose.r.z))
    pos_vec = Gf.Vec3d(pose.p.x, pose.p.y, pose.p.z)
    xform_op.Set(Gf.Matrix4d().SetRotate(rot_mat).SetTranslateOnly(pos_vec))


def create_material(stage, _mtl_path, props):
    mat_prim = stage.GetPrimAtPath(Sdf.Path(_mtl_path))
    if not mat_prim:
        mat_prim = stage.DefinePrim(Sdf.Path(_mtl_path), "Material")
    material_prim = UsdShade.Material.Get(stage, mat_prim.GetPath())
    if material_prim:
        shader_path = stage.GetPrimAtPath(Sdf.Path("{}/Shader".format(_mtl_path)))
        if not shader_path:
            shader_path = stage.DefinePrim(Sdf.Path("{}/Shader".format(_mtl_path)), "Shader")
        shader_prim = UsdShade.Shader.Get(stage, shader_path.GetPath())
        if shader_prim:

            shader_out = shader_prim.CreateOutput("out", Sdf.ValueTypeNames.Token)
            material_prim.CreateSurfaceOutput("mdl").ConnectToSource(shader_out)
            material_prim.CreateVolumeOutput("mdl").ConnectToSource(shader_out)
            material_prim.CreateDisplacementOutput("mdl").ConnectToSource(shader_out)
            shader_prim.GetImplementationSourceAttr().Set(UsdShade.Tokens.sourceAsset)
            shader_prim.SetSourceAsset(Sdf.AssetPath("OmniPBR.mdl"), "mdl")
            shader_prim.SetSourceAssetSubIdentifier("OmniPBR", "mdl")

            omni.usd.create_material_input(
                mat_prim,
                "diffuse_color_constant",
                Gf.Vec3f(props.color.r, props.color.g, props.color.b),
                Sdf.ValueTypeNames.Color3f,
            )
            omni.usd.create_material_input(
                mat_prim,
                "emissive_color",
                Gf.Vec3f(props.emissive.r, props.emissive.g, props.emissive.b),
                Sdf.ValueTypeNames.Color3f,
            )
            omni.usd.create_material_input(mat_prim, "metallic_constant", props.metallic, Sdf.ValueTypeNames.Float)
            omni.usd.create_material_input(
                mat_prim, "reflection_roughness_constant", props.roughness, Sdf.ValueTypeNames.Float
            )
            omni.usd.create_material_input(mat_prim, "enable_emission", props.emissive.a > 0, Sdf.ValueTypeNames.Bool)
            omni.usd.create_material_input(mat_prim, "emissive_intensity", props.emissive.a, Sdf.ValueTypeNames.Float)
            # mat_prim.SetInstanceable(True)
        else:
            carb.log_warn(f"failed to create shader {shader_path}")
        stage.Save()
        return mat_prim.GetPath().pathString
    else:
        carb.log_error(f"failed to create prim {mat_prim.GetPath().pathString}")
        return False


def get_material_path(prim):
    result = prim.GetRelationship("material:binding").GetTargets()
    return str(result[0]) if len(result) > 0 else ""


def get_all_prims_with_material(stage, material_name):
    return [x for x in stage.Traverse() if material_name == os.path.basename(get_material_path(x))]


DEFAULT_TEMP_FOLDER_SETTING = "/ext/omni.isaac.onshape_importer/default_temp"


class PartItem:
    def __init__(self, base_path, part):
        name = make_valid_filename(part.get_name())
        self.path = os.path.join(base_path, "{}.usd".format(name))
        # print(self.path)
        self.part = part
        if os.path.exists(self.path):
            i = 1
            while os.path.exists(self.path):
                self.path = os.path.join(base_path, "{}_{}.usd".format(name, i))
                i = i + 1
        # print(self.path)
        self.stage = createInMemoryStage(self.path)
        self.imported = False
        # print(self.path)


class UsdGenerator:
    tmp_prefix = "tmp_isaac_onshape_importer_"

    def __init__(self, document, assembly):
        self.document = document
        self.assembly = assembly
        # define the work directory for the document usds
        self.tempdir = tempfile.TemporaryDirectory(
            prefix=self.tmp_prefix, dir=carb.settings.get_settings().get(DEFAULT_TEMP_FOLDER_SETTING)
        ).name
        self.tempdir = os.path.join(self.tempdir, document.get_name())
        os.makedirs(self.tempdir)
        # print(self.tempdir)
        # Materials USD, where all materials for the assembly will be stored.
        self._materials_path = os.path.join(self.tempdir, "materials")
        self.assemblies_path = {}
        self.groupMates = {}
        self.group_map = {}
        self.instance_group_map = {}
        self.override_parent = {}
        self.rigid_bodies = set()
        self.rig_physics = True
        os.makedirs(self._materials_path)
        # print(self._materials_path)
        self._materials_path = os.path.join(self._materials_path, "materials.usd")
        self._material_stage = None

        self._stages_dir = os.path.join(self.tempdir, "parts")
        os.makedirs(self._stages_dir)
        self.parts_building_pool = ThreadPoolExecutor(max_workers=40)
        # Assemblies need parts stage to be fully built

        self.assembly_stage = None
        self.stage_path = None
        self.assembly_building_pool = ThreadPoolExecutor(max_workers=40)

        # Dictionary of materials key: color string from the source, value: usd path in the material stage
        self._materials_dict = {}
        # Dictionary of parts and stage; key: part.get_key(), stage: stage that
        self._parts_stage_dict = {}
        # self.manager = multiprocessing.Manager()
        self.materials_update_lock = threading.Lock()
        self.part_stage_lock = threading.Lock()
        self.stage_lock = threading.Lock()
        # self.main_thread = threading.currentThread()

        # print(self.main_thread.getName())
        self.shutdown = False
        self.delayed_make_assembly = False
        self._app_update_sub = (
            omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._on_update_ui)
        )

        self._selection = omni.usd.get_context().get_selection()
        self._events = omni.usd.get_context().get_stage_event_stream()
        self._stage_event_subscription = self._events.create_subscription_to_pop(
            self._on_stage_event, name="Onshape Usd Exporter stage Watch"
        )
        omni.usd.get_context().disable_save_to_recent_files()
        self.parts_to_process = []

    def get_abs_and_rel_paths(self):
        directory = self.tempdir.replace("\\", "/")
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

    def get_abs_and_rel_paths(self):
        directory = self.tempdir.replace("\\", "/")
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

    def _on_stage_event(self, event):
        """Called with omni.usd.context when stage event"""

        if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            self._on_kit_selection_changed()
        if event.type == int(omni.usd.StageEventType.OPENED):
            try:
                self.set_materials_to_color_layer()
            except Exception as e:
                carb.log_error("Onshape USD Generator:" + str(e))

    def _on_kit_selection_changed(self):
        """The selection in kit is changed"""
        selection = []
        for sel in self._selection.get_selected_prim_paths():
            if sel.startswith("/Looks"):
                self.set_material_authoring_layer()
                return
        self.set_root_authoring_layer()

    def set_material_authoring_layer(self):
        if self.is_temp_stage_open():
            context = omni.usd.get_context()
            stage = context.get_stage()
            if stage:
                edit_target = Usd.EditTarget([a for a in stage.GetUsedLayers() if "materials/materials" in str(a)][0])
                stage.SetEditTarget(edit_target)

    def set_root_authoring_layer(self):
        if self.is_temp_stage_open():
            context = omni.usd.get_context()
            stage = context.get_stage()
            if stage:
                edit_target = Usd.EditTarget(stage.GetRootLayer())
                stage.SetEditTarget(edit_target)

    def is_temp_stage_open(self):
        return os.path.split(self.tempdir)[1].replace("\\", "/") in omni.usd.get_context().get_stage_url()

    def delayed_delete(self):

        tempdir = os.path.split(self.tempdir)[0]

        def delete_folder():
            try:
                if os.path.exists(tempdir):
                    shutil.rmtree(tempdir)
            except Exception as e:
                carb.log_error("Error trying to clean temp folder: " + str(e))

        omni.usd.get_context().new_stage_with_callback(on_finish_fn=lambda a, b: delete_folder())

    def is_temp_stage_open(self):
        return os.path.split(self.tempdir)[1].replace("\\", "/") in omni.usd.get_context().get_stage_url()

    def delayed_delete(self):

        tempdir = os.path.split(self.tempdir)[0]

        def delete_folder():
            try:
                if os.path.exists(tempdir):
                    shutil.rmtree(tempdir)
            except Exception as e:
                carb.log_error("Error trying to clean temp folder: " + str(e))

        omni.usd.get_context().new_stage_with_callback(on_finish_fn=lambda a, b: delete_folder())

    def __del__(self):
        # print("del")
        self._stage_event_subscription = None
        self._app_update_sub = None
        if not self.shutdown:
            self.shutdown = True
            self.parts_building_pool.shutdown(wait=True)
            for t in self.parts_building_pool._threads:
                terminate_thread(t)
            # if self.materials_update_lock.locked():
            #     self.materials_update_lock.release()
            self.materials_update_lock = None
            # if self.part_stage_lock.locked():
            #     self.part_stage_lock.release()
            self.part_stage_lock = None
            tempdir = os.path.split(self.tempdir)[0]
            # print(tempdir)
            omni.usd.get_context().enable_save_to_recent_files()
            if self.is_temp_stage_open():
                self.delayed_delete()

            else:
                try:
                    if os.path.exists(tempdir):
                        shutil.rmtree(tempdir)
                except Exception as e:
                    carb.log_error("Error trying to clean temp folder: " + str(e))

    def on_shutdown(self):
        # print("shutting down")
        self._stage_event_subscription = None
        self._app_update_sub = None
        if not self.shutdown:
            self.shutdown = True
            self.parts_building_pool.shutdown(wait=True)
            for t in self.parts_building_pool._threads:
                terminate_thread(t)
            # if self.materials_update_lock.locked():
            #     self.materials_update_lock.release()
            self.materials_update_lock = None
            # if self.part_stage_lock.locked():
            #     self.part_stage_lock.release()
            self.part_stage_lock = None
            tempdir = os.path.split(self.tempdir)[0]
            # print(tempdir)
            omni.usd.get_context().enable_save_to_recent_files()
            if self.is_temp_stage_open():
                self.delayed_delete()

            else:
                try:
                    if os.path.exists(tempdir):
                        shutil.rmtree(tempdir)
                except Exception as e:
                    carb.log_error("Error trying to clean temp folder: " + str(e))

    def get_material(self, material_key):
        """
        Get material reference according to the key
        """

        if material_key not in self._materials_dict:
            mat = VisualMaterial(convertColor(material_key))
            name = "/Looks/" + pxr.Tf.MakeValidIdentifier("{}".format(mat.name))
            # print ("getting material", self._materials_path, name)
            # with self.materials_update_lock:
            usd_mat = create_material(self.material_stage, name, mat)
            if usd_mat:
                self._materials_dict[material_key] = {"usd": usd_mat, "name": name}
            ###
        return self._materials_dict[material_key]

    def update_material(self, material_key, new_mat: VisualMaterial):
        name = self.get_material(material_key)
        new_name = "/Looks/" + pxr.Tf.MakeValidIdentifier("{}".format(new_mat.name))
        # with self.materials_update_lock:
        if new_name != name:
            move_dict = {name: new_name}
            omni.kit.commands.execute("MovePrimsCommand", paths_to_move=move_dict, on_move_fn=None)

        usd_mat = create_material(self.material_stage, name, new_mat)
        if usd_mat:
            self._materials_dict[material_key] = {"usd": usd_mat, "name": new_name}
        return self._materials_dict[material_key]

    def create_part_stage(self, part, done_importing):
        # print(part.get_name(), "Done importing, starting USD conversion")
        if part.get_key() in self._parts_stage_dict:
            done_importing = False
        task = self.parts_building_pool.submit(self.set_part_mesh, part)
        # self.set_part_mesh(part)
        if done_importing:
            task.add_done_callback(self._build_assemblies)

    @property
    def material_stage(self):
        if not self._material_stage:
            # print (self._materials_path)
            self._material_stage = createInMemoryStage(self._materials_path)
            looks_prim = self._material_stage.DefinePrim(Sdf.Path("/Looks"), "Scope")
            self._material_stage.SetDefaultPrim(looks_prim)
        return self._material_stage

    def set_part_mesh(self, part, sync=False):
        # print("set part")
        if self.shutdown:
            return
        # if part.get_key() in self._parts_stage_dict and self.is_temp_stage_open():
        #     # print("stage open")
        #     if omni.usd.get_context().can_close_stage():
        #         omni.usd.get_context().close_stage_with_callback(
        #             # on_finish_fn=lambda a, b, part=part: omni.usd.get_context().new_stage_with_callback(
        #             on_finish_fn=lambda a, b, part=part:self.set_part_mesh(part)
        #         )
        #         # )
        #         return
        # print("Next")
        # carb.log_warn(part.get_name() + " part start")
        if part.get_key() not in self._parts_stage_dict:
            # print(part.get_name(), " part doesn't exist, creating Item")
            with self.part_stage_lock:
                # print(part.get_name(), " part Lock")
                self._parts_stage_dict[part.get_key()] = PartItem(self._stages_dir, part)
        # #     self.set_root_authoring_layer()
        if self.is_temp_stage_open():
            if not sync:
                with self.part_stage_lock:
                    self.parts_to_process.append(part)
                    return

        # with Sdf.ChangeBlock():
        stage = self._parts_stage_dict[part.get_key()].stage
        path = self._parts_stage_dict[part.get_key()].path
        self._parts_stage_dict[part.get_key()].imported = False

        mesh_name = pxr.Tf.MakeValidIdentifier(make_valid_filename(part.get_name().strip()))
        # print(part.get_name(), "creating part")
        mesh_name = "/Root/{}".format(mesh_name)
        root = UsdGeom.Xform.Define(stage, "/Root").GetPrim()
        stage.SetDefaultPrim(root)
        rootLayer = stage.GetRootLayer()
        rootLayer.SetPermissionToEdit(True)
        # print("waiting")
        with Usd.EditContext(stage, rootLayer):
            # print(part.get_name(), "creating mesh", mesh_name)
            usdMesh = UsdGeom.Mesh.Define(stage, Sdf.Path(mesh_name))
            mesh_prim = stage.GetPrimAtPath(Sdf.Path(mesh_name))
            model_api = Usd.ModelAPI(mesh_prim)
            model_api.SetKind(Kind.Tokens.model)
            # with self.materials_update_lock:
            # print(mesh_name, "setting COM")
            mass_props = part.get_mass_properties(wait=True)

            com = [0.0, 0.0, 0.0]
            # print(mass_props, type(mass_props))

            if mass_props:
                if "centroid" in mass_props:
                    com = [float(mass_props["centroid"][i]) * 100.0 for i in [0, 1, 2]]

            # print(com)
            pose = Transform(Float3(com[0], com[1], com[2]))
            set_pose(usdMesh, pose)
            massAPI = None
            # print(mesh_name, "setting mass props")
            massAPI = UsdPhysics.MassAPI.Apply(mesh_prim)
            if mass_props and "mass" in mass_props:
                massAPI.CreateMassAttr(mass_props["mass"][0])
                # TODO: Use PhysicsAPI to set mass and inertia to ensure forward compatibility
                # mesh_prim.CreateAttribute("Mass", Sdf.ValueTypeNames.Double, False).Set(
                #     mass_props["mass"][0]
                # )  # density is in g/cm3
                # print( "mass done")
                if mass_props and "inertia" in mass_props:
                    inertia_matrix = mass_props["inertia"]
                    mesh_prim.CreateAttribute("inertiaMatrix", Sdf.ValueTypeNames.DoubleArray, False).Set(
                        DoubleArray([float(i) * 10000 for i in inertia_matrix[0:9]])
                    )
                # print( "inertia")
                if mass_props and "principalInertia" in mass_props:
                    diag_inertia = mass_props["principalInertia"]
                    if not massAPI:
                        massAPI = UsdPhysics.MassAPI.Apply(mesh_prim)
                    massAPI.CreateDiagonalInertiaAttr(Gf.Vec3d([float(i) * 10000 for i in diag_inertia]))
                    # mesh_prim.CreateAttribute("DiagonalInertia", Sdf.ValueTypeNames.Double3, False).Set(
                    #     Gf.Vec3d([float(i)*10000 for i in diag_inertia])
                    # )
            # TODO: Add Density based on selected material

            # print(part.get_name(), "setting mesh vertices", mesh_name)
            # with self.materials_update_lock:
            Vertex = make_array("float", 100 * part.get_mesh().vertices - np.array(com))
            face_vertex_count = make_array("int", part.get_mesh().face_vertex_count)
            face_indices = make_array("int", part.get_mesh().face_indices)
            face_indices_uvs = make_array("float", part.get_mesh().vertices_UVs)
            face_indices_normals = make_array("float", part.get_mesh().vertices_normals)

            usdMesh.CreatePointsAttr(Vertex)
            usdMesh.CreateNormalsAttr(face_indices_normals)
            usdMesh.CreateFaceVertexCountsAttr(face_vertex_count)
            usdMesh.CreateFaceVertexIndicesAttr(face_indices)

            usdMesh.SetNormalsInterpolation(pxr.UsdGeom.Tokens.faceVarying)
            texCoord = usdMesh.CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.faceVarying)
            texCoord.Set(face_indices_uvs)
            usdMesh.CreateSubdivisionSchemeAttr("none")

            materials = stage.GetPrimAtPath("/Root/Looks")
            # if not materials:
            # print(part.get_name(), "- Pre-Lock")
            distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
            distantLight.CreateIntensityAttr(300)
            light_pose = Transform(r=Float4(-0.383, 0, 0, 0.924))
            set_pose(distantLight, light_pose)
            with self.materials_update_lock:
                if self.shutdown:
                    return
                # carb.log_error(part.get_name()+ " - Materials Lock")
                try:
                    for i, material in enumerate(
                        part.get_mesh().colors
                    ):  # Ensure the Materials usd is created before setting reference
                        mat = self.get_material(material)
                    # materials = stage.GetPrimAtPath("/Root/Looks")

                    materials = stage.OverridePrim("/Root/Looks")
                    materials.GetReferences().AddReference(
                        os.path.relpath(self._materials_path, self._stages_dir).replace("\\", "/")
                    )
                    root_layer = stage.GetRootLayer()
                    if path not in root_layer.subLayerPaths:
                        mat_layer = os.path.relpath(self._materials_path, self._stages_dir).replace("\\", "/")
                        if mat_layer not in root_layer.subLayerPaths:
                            root_layer.subLayerPaths.append(mat_layer)

                    for i, material in enumerate(part.get_mesh().colors):
                        mat = self.get_material(material)
                        if len(part.get_mesh().colors) > 1:
                            face_indices = part.get_mesh().facets_per_color[i]
                            subset_name = "{}/{}".format(mesh_name, os.path.basename(mat["name"]))
                            # print(subset_name)
                            geomSubset = UsdGeom.Subset.Define(stage, subset_name)
                            geomSubset.CreateElementTypeAttr("face")
                            geomSubset.CreateFamilyNameAttr("materialBind")
                            geomSubset.CreateIndicesAttr(IntArray(face_indices))
                            bind_material(stage, geomSubset, "/Root{}".format(mat["usd"]))
                        else:
                            bind_material(stage, usdMesh, "/Root{}".format(mat["usd"]))

                        materials.SetInstanceable(True)
                except Exception as e:
                    carb.log_error("Mesh USD Generation error: " + str(e))

        stage.Save()
        # print("Done")
        self._parts_stage_dict[part.get_key()].imported = True

    def reset_assembly(self):
        # if self.is_temp_stage_open():
        #     omni.usd.get_context().close_stage_with_callback(lambda a,b: omni.usd.get_context().new_stage_with_callback(lambda a,b: self.reset_assembly()))
        # else:
        #     if self.stage_path:
        self.stage_path = None

        # self._build_assemblies()

    def _build_assemblies(self, task=None):
        self.delayed_make_assembly = True

    def get_assembly_paths(self, assembly, parent_path, parent_id):
        name = assembly.get_item("name").split(" <")[0].strip()
        a_id = parent_id + assembly.get_item("id")
        path = parent_path + "/{}".format(pxr.Tf.MakeValidIdentifier(make_valid_filename(name.strip())))
        path = get_next_available(self.assemblies_path.values(), path)
        self.assemblies_path[a_id] = path
        # print(assembly.get_item("name"),name, path)
        for a in assembly.get_children():
            self.get_assembly_paths(a, path, a_id)

    def write_assembly_xform(
        self, assembly, parent, parent_id, parent_global_pose, level=0, in_group=None, make_collision=False
    ):
        # print(level, assembly   )
        # print(assembly.transform)
        name = assembly.get_item("name").strip()[:-4]
        a_id = parent_id + assembly.get_item("id")
        path = self.assemblies_path[a_id]
        # print(assembly.get_item("id"), path)
        parent_prim = self.assembly_stage.GetPrimAtPath(os.path.dirname(path))
        if parent_prim:
            parent_global_pose = omni.usd.utils.get_world_transform_matrix(parent_prim)
        else:
            carb.log_error("Parent Prim Not defined: " + os.path.dirname(path))

        t = np.array(assembly.transform[a_id]).reshape((4, 4))
        t = np.transpose(t)
        gf_m = Gf.Matrix4d(*t.reshape(16).tolist())
        gf_m.SetTranslateOnly(gf_m.ExtractTranslation() * 100.0)
        local_t = gf_m * parent_global_pose.GetInverse()
        prim = self.assembly_stage.GetPrimAtPath(path)
        if assembly.get_item("suppressed") and prim:
            self.assembly_stage.RemovePrim(path)
            return

        try:
            if prim and assembly.get_item("type") == "Part":
                if prim.GetChildren():
                    # print("{} moved to {}".format(path, path + "/{}".format(make_valid_filename(name))))
                    path = omni.usd.get_stage_next_free_path(
                        self.assembly_stage, path + "/{}".format(make_valid_filename(name)), False
                    )
                    self.assemblies_path[a_id] = path
                    prim = self.assembly_stage.GetPrimAtPath(path)
            if not prim:
                if assembly.get_item("type") == "Part":
                    part_id = assembly.get_item("hashId")
                    if part_id in self._parts_stage_dict:
                        prim = self.assembly_stage.OverridePrim(path)
                        timeout = 10
                        if len(prim.GetChildren()) == 0:
                            if self._parts_stage_dict[part_id].imported:
                                # carb.log_info(
                                #     "waiting" + name + "(This usually means there is an uncaptured exception)"
                                # )
                                # time.sleep(1.0)
                                # timeout -= 1
                                # if self.shutdown or timeout == 0:
                                #     if timeout == 0:
                                #         carb.log_error(name + "Exceeded wait time. aborting")
                                #     return
                                prim.GetReferences().AddReference(
                                    os.path.relpath(self._parts_stage_dict[part_id].path, self.tempdir).replace(
                                        "\\", "/"
                                    )
                                )
                            # if make_collision:
                            #     for c in [c for c in prim.GetChildren() if UsdGeom.Mesh(c)]:
                            #         UsdPhysics.CollisionAPI.Apply(c)
                            #         collisionAPI = UsdPhysics.MeshCollisionAPI.Apply(c)
                            #         collisionAPI.CreateApproximationAttr().Set("convexHull")
                            self._parts_stage_dict[part_id].part.add_usd_path(path)
                            # print(self._parts_stage_dict[part_id].part.parts_usds)
                    else:
                        carb.log_error(
                            "Part Not Found, Please re-import the assembly to load it: {} ({})".format(name, path)
                        )
                        return
                else:
                    prim = UsdGeom.Xform.Define(self.assembly_stage, path).GetPrim()

            # print(prim)
            # print(level*" ",prim.GetPath())
            child_prims = TraversePrim(prim)
            child_transforms = [omni.usd.utils.get_world_transform_matrix(c) for c in child_prims]

            xform = UsdGeom.Xformable(prim)
            xform.ClearXformOpOrder()
            xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
            xform_op.Set(local_t)

            for i, c in enumerate(child_prims):
                xform = UsdGeom.Xformable(c)
                xform.ClearXformOpOrder()
                xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
                parent_global = omni.usd.utils.get_world_transform_matrix(prim.GetParent())
                xform_op = child_transforms[i] * parent_global.GetInverse()

            # print(level*" ",local_t)
            if assembly.get_item("hidden"):
                UsdGeom.Imageable(prim).MakeInvisible()
        except Exception as e:
            carb.log_error("{}: {}".format(str(e), path))

        # print(assembly.get_item("name"), path)
        # for a in assembly.get_children():
        # print ("   ", a.get_item("name"))
        if self.rig_physics:
            self.make_groups_xform(assembly, path, a_id)

        for a in assembly.get_children():
            if not a.get_item("suppressed"):
                c_id = a.get_item("id")
                p_path = path
                p_in_group = in_group
                if a_id + c_id in self.group_map:
                    p_in_group = self.group_map[a_id + c_id]
                    p_path = self.groupMates[p_in_group]["prim"]
                self.write_assembly_xform(a, p_path, a_id, gf_m, in_group=p_in_group)

    def make_groups_xform(self, assembly, path, a_id=""):
        if self.rig_physics and not assembly.get_item("suppressed") and assembly.uid in self.assembly.features_map:
            # a_id = a_id + (assembly.get_item("id") or '')
            for f_id in self.assembly.features_map[assembly.uid]:
                feature = self.assembly.assembly_features[f_id]
                f_id = feature["id"]
                if feature["featureType"] == "mateGroup" and not feature["suppressed"]:
                    if (a_id, f_id) in self.groupMates:
                        # Create Prim for group
                        group = self.groupMates[(a_id, f_id)]
                        group_path = group["prim"]
                        # print("Before", group_path)
                        if not group_path:
                            group_path = path + "/{}".format(
                                pxr.Tf.MakeValidIdentifier(make_valid_filename(feature["featureData"]["name"].strip()))
                            )
                            group_path = omni.usd.get_stage_next_free_path(self.assembly_stage, group_path, False)
                            # print(group_path)
                            self.groupMates[(a_id, f_id)]["prim"] = group_path
                        g_prim = self.assembly_stage.GetPrimAtPath(group_path)
                        if not g_prim:
                            g_prim = UsdGeom.Xform.Define(self.assembly_stage, group_path).GetPrim()
                            xform = UsdGeom.Xformable(g_prim)
                            xform.ClearXformOpOrder()
                            xform_op = xform.AddXformOp(
                                UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, ""
                            )
                            xform_op.Set(Gf.Matrix4d())
                            # UsdPhysics.RigidBodyAPI.Apply(g_prim)
                    else:
                        carb.log_error("group mate not found {}".format((a_id, f_id)))

    def get_sub_joints(self, assembly):
        features = []
        if assembly.uid in self.assembly.features_map:
            features = [
                f
                for f in self.assembly.features_map[assembly.uid]
                if self.assembly.assembly_features[f]["featureType"] == "mate"
                and self.assembly.assembly_features[f]["suppressed"] == False
                and self.assembly.assembly_features[f]["featureData"]["mateType"] in ["REVOLUTE", "SLIDER"]
            ]
        for a in assembly.get_children():
            features += self.get_sub_joints(a)
        return features

    def create_group_mates(self, assembly, a_id="", in_group=None):
        if self.rig_physics:
            a_id = a_id + str(assembly.get_item("id") or "")
            self.instance_group_map[a_id] = in_group
            if (
                not assembly.get_item("suppressed")
                and assembly.get_item("type").lower() == "assembly"
                and assembly.uid in self.assembly.features_map
            ):
                gms = [
                    f
                    for f in self.assembly.features_map[assembly.uid]
                    if self.assembly.assembly_features[f]["featureType"] == "mateGroup"
                    and not self.assembly.assembly_features[f]["suppressed"]
                ]
                # if gms and a_id in self.assemblies_path:
                # print(assembly.get_item("id"), assembly.get_item("name"), self.assemblies_path[a_id])
                for f_id in gms:
                    feature = self.assembly.assembly_features[f_id]
                    f_id = feature["id"]

                    instances = [o["occurrence"][0] for o in feature["featureData"]["occurrences"]]
                    if (a_id, f_id) not in self.groupMates:
                        prim = self.assemblies_path[a_id] + "/{}".format(
                            pxr.Tf.MakeValidIdentifier(make_valid_filename(feature["featureData"]["name"].strip()))
                        )
                        prim = get_next_available(self.assemblies_path.values(), prim)
                        groupMate = {"name": feature["featureData"]["name"], "instances": instances, "prim": prim}
                        # print((a_id, f_id), feature["featureData"]["name"])
                        # print("  ", groupMate["prim"])
                        for i in instances:
                            self.group_map[a_id + i] = (a_id, f_id)
                        # print("   ", assembly.get_item("name"), groupMate["name"], groupMate["prim"])
                        self.groupMates[(a_id, f_id)] = groupMate
            # Find Instances of assembly that are part of each mate
            for a in assembly.get_children():
                p_in_group = in_group
                if a_id + a.get_item("id") in self.group_map and not p_in_group:
                    p_in_group = self.group_map[a_id + a.get_item("id")]
                    self.get_assembly_paths(a, self.groupMates[p_in_group]["prim"], a_id)
                self.create_group_mates(a, a_id, p_in_group)

    def process_fastened_mates(self, assembly, a_id="", in_group=None):
        if self.rig_physics:
            _a_id = a_id
            a_id = a_id + str(assembly.get_item("id") or "")
            # self.instance_group_map[a_id] = in_group
            if (
                not assembly.get_item("suppressed")
                and assembly.get_item("type").lower() == "assembly"
                and assembly.uid in self.assembly.features_map
            ):
                # print("Group Mate assembly ID", a_id)
                # print("  Features:", self.assembly.features_map[assembly.uid])
                # print(self.assemblies_path[a_id])
                for f_id in [
                    f
                    for f in self.assembly.features_map[assembly.uid]
                    if self.assembly.assembly_features[f]["featureType"] == "mate"
                    and self.assembly.assembly_features[f]["suppressed"] == False
                    and self.assembly.assembly_features[f]["featureData"]["mateType"] == "FASTENED"
                ]:

                    # print("  ",f_id)
                    feature = self.assembly.assembly_features[f_id]
                    # print(assembly.get_item("name"), feature["featureData"]["name"], feature["suppressed"])
                    f_id = feature["id"]
                    # f = Mate(self.assembly.assembly_features[f_id], self.assembly.features_details[f_id])
                    mateds = [m["matedOccurrence"] for m in feature["featureData"]["matedEntities"]]
                    base = None
                    p = None
                    if len(mateds) >= 2:
                        base, p = mateds
                    if base and p:
                        if self.instance_group_map[a_id + "".join(base)]:
                            base_path = self.groupMates[self.instance_group_map[a_id + "".join(base)]]["prim"]
                        else:
                            base_id = max(0, len(base) - 2)  # start one before last
                            # print("    Find base parent assembly")
                            inst = self.assembly._instances_flat[base[base_id]]
                            while not self.get_sub_joints(
                                inst
                            ):  # inst.uid not in self.assembly.features_map or not self.assembly.features_map[inst.uid]:
                                # print("    ", self.assemblies_path[a_id+''.join(base[:base_id])])
                                base_id -= 1
                                if base_id < 0:
                                    break
                                inst = self.assembly._instances_flat[base[base_id]]
                            # print(base_id)
                            base_id = min(len(base) - 1, base_id + 1)
                            b_id = "".join(base[: base_id + 1])
                            # print(f.name, base_id, a_id, b_id)
                            base_path = self.assemblies_path[a_id + b_id]
                        # print("  ", feature["featureData"]["name"], base_path)

                        if self.instance_group_map[a_id + "".join(p)]:

                            prim_path = self.groupMates[self.instance_group_map[a_id + "".join(p)]]["prim"]
                            if (
                                self.instance_group_map[a_id + "".join(base)]
                                != self.instance_group_map[a_id + "".join(p)]
                            ):
                                prim_path = get_next_available(
                                    self.assemblies_path.values(), base_path + "/{}".format(os.path.basename(prim_path))
                                )
                                self.groupMates[self.instance_group_map[a_id + "".join(p)]]["prim"] = prim_path
                            else:
                                prim_path = base_path
                            # for a in assembly.get_children():
                            #     if self.instance_group_map[a_id + a.get_item("id")] == self.instance_group_map[a_id+''.join(p)]:
                            #         self.get_assembly_paths(a,prim_path,a_id)

                        else:

                            p_id = max(0, len(p) - 2)  # start one before last

                            # print("    Find child parent assembly")
                            inst = self.assembly._instances_flat[p[p_id]]
                            while not self.get_sub_joints(
                                inst
                            ):  # inst.uid not in self.assembly.features_map or not self.assembly.features_map[inst.uid]:
                                # print("    ", self.assemblies_path[a_id+''.join(p[:p_id])])
                                p_id -= 1
                                if p_id < 0:
                                    break
                                inst = self.assembly._instances_flat[p[p_id]]
                            # print(p_id)
                            p_id = min(len(p) - 1, p_id + 1)
                            _p_id = "".join(p[: p_id + 1])
                            # print("   ", p_id, a_id, _p_id)
                            prim_path = get_next_available(
                                self.assemblies_path.values(),
                                base_path + "/{}".format(os.path.basename(self.assemblies_path[a_id + _p_id])),
                            )
                            self.assemblies_path[a_id + _p_id] = prim_path
                            for a in self.assembly._instances_flat[p[p_id]].get_children():
                                self.get_assembly_paths(a, prim_path, a_id + _p_id)
                        if not [i for i in self.rigid_bodies if Sdf.Path(base_path).HasPrefix(i)]:
                            self.rigid_bodies.add(
                                base_path
                            )  # Add this body to a set to later add the RBAPI, and set the collisions for the underlying meshes
                        # print("  ", feature["featureData"]["name"], prim_path)
            ## Regenerate all assemblies paths if any group mate was created
            # Find Instances of assembly that are part of each mate
            # print("Done", a_id)
            for a in assembly.get_children():
                p_in_group = in_group
                if a_id + a.get_item("id") in self.group_map:
                    p_in_group = self.group_map[a_id + a.get_item("id")]

                self.process_fastened_mates(a, a_id, p_in_group)
            self.create_group_mates(assembly, _a_id, in_group)

    def get_rigid_body_path(self, a_id, occurence):
        if self.instance_group_map[a_id + "".join(occurence)]:
            path = self.groupMates[self.instance_group_map[a_id + "".join(occurence)]]["prim"]
            # print("in group:", path)
            # print(self.rigid_bodies)
        else:
            _id = max(0, len(occurence) - 1)
            inst = self.assembly._instances_flat[occurence[_id - 1]]
            while not self.get_sub_joints(
                inst
            ):  # inst.uid not in self.assembly.features_map or not self.assembly.features_map[inst.uid]:
                _id -= 1
                if _id < 0:
                    break
                inst = self.assembly._instances_flat[occurence[_id - 1]]

            _id += 2
            _id = min(_id, len(occurence) + 1)
            o_id = "".join(occurence[:_id])
            # print(occurence)
            # print("assembly group:",o_id, len(occurence), _id)
            path = self.assemblies_path[a_id + o_id]
            # print(path)
        if not [i for i in self.rigid_bodies if Sdf.Path(path).HasPrefix(i)]:
            self.rigid_bodies.add(path)
        else:
            path = [i for i in self.rigid_bodies if Sdf.Path(path).HasPrefix(i)][0]  # There should be only one
            # print(path)
        return path

    def process_joints(self, assembly, parent_id, in_group=None):
        a_id = parent_id + str(assembly.get_item("id") or "")
        if (
            not assembly.get_item("suppressed")
            and assembly.get_item("type").lower() == "assembly"
            and assembly.uid in self.assembly.features_map
        ):
            for f_id in [
                f
                for f in self.assembly.features_map[assembly.uid]
                if self.assembly.assembly_features[f]["featureType"] == "mate"
                and self.assembly.assembly_features[f]["suppressed"] == False
                and self.assembly.assembly_features[f]["featureData"]["mateType"] in ["REVOLUTE", "SLIDER"]
            ]:

                feature = self.assembly.assembly_features[f_id]
                f_id = feature["id"]
                # print(assembly.get_item("name"), feature["featureData"]["name"])
                # print("feature", feature['featureData']["name"])
                # f = Mate(self.assembly.assembly_features[f_id], self.assembly.features_details[f_id])
                base, p = [m["matedOccurrence"] for m in feature["featureData"]["matedEntities"]]
                base_path = self.get_rigid_body_path(a_id, base)
                prim_path = self.get_rigid_body_path(a_id, p)

                if base_path == prim_path:
                    # Skip this joint as it connects the body to itself
                    continue
                # print(" ",self.assembly._instances_flat[base[-1]].get_item("name"))
                # print(" ",self.assembly._instances_flat[p[-1]].get_item("name"))
                # print(" ",prim_path)

                body_0 = UsdGeom.Xform.Define(self.assembly_stage, base_path).GetPrim()
                body_1 = UsdGeom.Xform.Define(self.assembly_stage, prim_path).GetPrim()
                # body_1 = UsdGeom.Xformable(self.assembly_stage.GetPrimAtPath(prim_path)).GetPrim()

                UsdPhysics.RigidBodyAPI.Apply(body_0)
                UsdPhysics.RigidBodyAPI.Apply(body_1)

                for p in [a for a in TraversePrim(body_0) + TraversePrim(body_1) if UsdGeom.Mesh(a)]:
                    UsdPhysics.CollisionAPI.Apply(p)
                    collisionAPI = UsdPhysics.MeshCollisionAPI.Apply(p)
                    collisionAPI.CreateApproximationAttr().Set("convexHull")

                body_0_global = omni.usd.utils.get_world_transform_matrix(body_0)
                body_1_global = omni.usd.utils.get_world_transform_matrix(body_1)

                mate = Mate(self.assembly.assembly_features[f_id], self.assembly.features_details[f_id])

                joint_parent_assembly = mate.positions[0]
                a0 = self.assembly_stage.GetPrimAtPath(self.assemblies_path[a_id + "".join(base)])
                p_a = omni.usd.utils.get_world_transform_matrix(a0)
                joint_global_pose = joint_parent_assembly * p_a  #
                # t0.SetTranslateOnly(t0.ExtractTranslation() + t0.ExtractRotation().TransformDir(joint_parent_assembly.ExtractTranslation()))
                # t0.SetRotateOnly(joint_parent_assembly.ExtractRotation()*t0.ExtractRotation())
                # * joint_parent_assembly#.GetInverse()
                root = self.assemblies_path[""]
                p = "{}/{}".format(root, pxr.Tf.MakeValidIdentifier(make_valid_filename(mate.name)))
                p = omni.usd.get_stage_next_free_path(self.assembly_stage, p, False)
                # print(p)

                if mate.type == "SLIDER":
                    joint = UsdPhysics.PrismaticJoint.Define(self.assembly_stage, p)
                if mate.type == "REVOLUTE":
                    joint = UsdPhysics.RevoluteJoint.Define(self.assembly_stage, p)

                joint.CreateAxisAttr(mate.axis)
                # print(f.limits)
                if mate.limits[0] is not None:
                    joint.CreateLowerLimitAttr(mate.limits[0])
                if mate.limits[1] is not None:
                    joint.CreateUpperLimitAttr(mate.limits[1])

                joint.CreateBody0Rel().SetTargets([base_path])
                joint.CreateBody1Rel().SetTargets([prim_path])

                joint.CreateLocalPos0Attr().Set((joint_global_pose * body_0_global.GetInverse()).ExtractTranslation())
                joint.CreateLocalRot0Attr().Set(
                    Gf.Quatf((joint_global_pose * body_0_global.GetInverse()).ExtractRotation().GetQuat())
                )

                joint.CreateLocalPos1Attr().Set((joint_global_pose * body_1_global.GetInverse()).ExtractTranslation())
                joint.CreateLocalRot1Attr().Set(
                    Gf.Quatf((joint_global_pose * body_1_global.GetInverse()).ExtractRotation().GetQuat())
                )

        for a in assembly.get_children():
            if not a.get_item("suppressed"):
                p_in_group = in_group
                if a_id + a.get_item("id") in self.group_map:
                    p_in_group = self.group_map[a_id + a.get_item("id")]

                self.process_joints(a, a_id, p_in_group)
        # self.create_group_mates(assembly, a_id, in_group)

    def _on_update_ui(self, time):
        # if self.delayed_root_layer:
        # self._selection.clear_selected_prim_paths()
        # self.set_root_authoring_layer()
        # asyncio.ensure_future(omni.kit.app.get_app().next_update_async())
        # self.delayed_root_layer = False
        if self.parts_to_process:
            with self.part_stage_lock:
                while self.parts_to_process:
                    part = self.parts_to_process.pop()
                    self.set_part_mesh(part, sync=True)
                    for path in part.parts_usds:
                        part_prim = self.assembly_stage.GetPrimAtPath(path)
                        stack = part_prim.GetPrimStack()
                        if not [True for i in stack if i.HasInfo(Sdf.PrimSpec.ReferencesKey)]:
                            part_prim.GetReferences().AddReference(self._parts_stage_dict[part.get_key()].path)
                try:
                    self.set_materials_to_color_layer()
                except Exception as e:
                    carb.log_error("Onshape USD Generator:" + str(e))

        # print("Build assembly", threading.currentThread().getName())
        if self.delayed_make_assembly:
            self.delayed_make_assembly = False

            # self.main_thread.join()
            # def do_task():
            # print("Building assembly")

            # print("creating new Assembly")
            self.stage_path = os.path.join(self.tempdir, "{}.usd".format(make_valid_filename(self.assembly.get_name())))
            # print(self.stage_path)
            if not self.assembly_stage:
                self.assembly_stage = createInMemoryStage(self.stage_path)
            rootLayer = self.assembly_stage.GetRootLayer()
            rootLayer.SetPermissionToEdit(True)
            # print("waiting")
            # with Usd.EditContext(self.assembly_stage, rootLayer):
            # with self.stage_lock:
            # asyncio.wait(omni.kit.app.get_app().next_update_async())
            # print("resuming")

            # print(self.assembly_stage)
            # print(self.assembly._root._item)
            for p in self.assembly_stage.GetPrimAtPath("/").GetChildren():
                self.assembly_stage.RemovePrim(p.GetPath())
            path = "/{}".format(pxr.Tf.MakeValidIdentifier(make_valid_filename(self.assembly.get_name())))
            self.root = path
            root = UsdGeom.Xform.Define(self.assembly_stage, path).GetPrim()
            if self.rig_physics:
                UsdPhysics.ArticulationRootAPI.Apply(self.assembly_stage.GetPrimAtPath(path))
                root_api = PhysxSchema.PhysxArticulationAPI.Apply(self.assembly_stage.GetPrimAtPath(path))
                root_api.CreateEnabledSelfCollisionsAttr().Set(False)
            self.assembly_stage.SetDefaultPrim(root)
            self.groupMates = {}
            self.group_map = {}
            self.assemblies_path = {}
            self.assemblies_path[""] = path
            self.rigid_bodies = set()
            for a in self.assembly._root.get_children():
                self.get_assembly_paths(a, path, "")
            if self.rig_physics:
                self.create_group_mates(self.assembly._root)
                self.process_fastened_mates(self.assembly._root)
                self.make_groups_xform(self.assembly._root, path)
            for a in self.assembly._root.get_children():
                if not a.get_item("suppressed"):
                    c_id = a.get_item("id")
                    p_path = path
                    in_group = None
                    if c_id in self.group_map:
                        in_group = self.group_map[c_id]
                        p_path = self.groupMates[in_group]["prim"]
                    self.write_assembly_xform(a, p_path, "", Gf.Matrix4d().SetIdentity(), in_group=in_group)
            if self.rig_physics:
                self.process_joints(self.assembly._root, "")
                bodies = sorted(self.rigid_bodies)
            # for b in bodies:
            #     print(b)
            root_layer = self.assembly_stage.GetRootLayer()
            if path not in root_layer.subLayerPaths:
                mat_layer = os.path.relpath(self._materials_path, self.tempdir).replace("\\", "/")
                if mat_layer not in root_layer.subLayerPaths:
                    with self.materials_update_lock:
                        root_layer.subLayerPaths.append(mat_layer)

            distantLight = UsdLux.DistantLight.Define(self.assembly_stage, Sdf.Path("/DistantLight"))
            distantLight.CreateIntensityAttr(300)
            light_pose = Transform(r=Float4(-0.383, 0, 0, 0.924))
            set_pose(distantLight, light_pose)
            if self.rig_physics:
                UsdPhysics.Scene.Define(self.assembly_stage, Sdf.Path("/physicsScene"))
            # print("saving")
            self.assembly_stage.Save()
            if not self.is_temp_stage_open():
                omni.usd.get_context().close_stage_with_callback(
                    lambda a, b: omni.usd.get_context().open_stage(self.stage_path)
                )

            # do_task()
            # asyncio.run(do_task())

        # self.parts_building_pool.submit(do_task)

    def set_materials_to_color_layer(self):
        # print("set_materials")
        if self.is_temp_stage_open():
            context = omni.usd.get_context()
            stage = context.get_stage()
            session_layer = stage.GetSessionLayer()
            # session_layer.subLayerPaths.append(os.path.relpath(self._materials_path, self.stage_path).replace("\\", "/"))
            # Makes the session layer the authoring layer to make a non-permanent change on material binding
            materials_list = [m["name"] for m in self._materials_dict.values()]
            # print(materials_list)
            with Usd.EditContext(stage, session_layer):
                # layers.set_authoring_layer_by_identifier(session_layer_id)
                with Sdf.ChangeBlock():
                    for mat in materials_list:
                        if stage.GetPrimAtPath(mat):
                            mat_name = os.path.basename(mat)
                            prims = get_all_prims_with_material(stage, mat_name)
                            bind_material(stage, prims, mat)
            # return to root layer

    def save_flattened(self, path, on_finish_fn=None):
        self.material_stage.Save()
        self.assembly_stage.Save()

        path = "{}/{}.usd".format(path, make_valid_filename(self.assembly.get_name()))
        omni.usd.get_context().export_as_stage_with_callback(
            path,
            lambda a, b, path=path, finish_fn=on_finish_fn: omni.usd.get_context().open_stage_with_callback(
                path, lambda a, b, path=path, finish_fn=finish_fn: self._open_flattened(a, b, path, finish_fn)
            ),
        )
        # omni.usd.get_context().open_stage(
        #     self.stage_path, lambda a, b, c=path, d=on_finish_fn: self._saved_flattened(c, d)
        # )

    def _saved_flattened(self, path, on_finish_fn):
        if self.is_temp_stage_open():
            # self.set_materials_to_color_layer()
            # move_dict = {}
            # move_dict["/Looks"] = "{}/Looks".format(self.root)
            # omni.kit.commands.execute("MovePrimsCommand", paths_to_move=move_dict)
            omni.usd.get_context().export_as_stage_with_callback(
                path, lambda a, b, c=path, d=on_finish_fn: self._open_flattened(c, d)
            )

    def _open_flattened(self, a, b, path, on_finish_fn):
        # print("saved flattened")
        move_dict = {}
        move_dict["/Looks"] = "{}/Looks".format(self.root)
        omni.kit.commands.execute("MovePrimsCommand", paths_to_move=move_dict)
        stage = omni.usd.get_context().get_stage()
        stage.RemovePrim("/Flattened_Master_1")
        stage.Save()
        # stage = pxr.Usd.Stage.Open(path)
        # materials = [i.GetPath().pathString for i in stage.GetPrimAtPath("{}/Looks".format(self.root)).GetChildren()]
        # for material in materials:
        #     mat_name = os.path.basename(material)
        #     prims = get_all_prims_with_material(stage, mat_name)
        #     bind_material(stage, prims, material)

        prims = [
            i.GetChild("Looks").GetPath()
            for i in stage.Traverse()
            if i.GetChild("Looks") and i.GetPath().pathString != "{}".format(self.root)
        ]
        for prim in prims:
            stage.RemovePrim(prim)
        stage.Save()
        if on_finish_fn:
            on_finish_fn()
        # omni.usd.get_context().open_stage_with_callback(path, on_finish_fn)

    def open_stage(self):
        if self.stage_path:
            omni.usd.get_context().open_stage(self.stage_path)
