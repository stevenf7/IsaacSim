# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import gc
import omni.ext
import omni.usd
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
import omni.kit.utils
import omni.kit.commands
from pxr import Usd, UsdGeom, Sdf, UsdShade
import weakref

EXTENSION_NAME = "Mesh Merge Tool"


class Extension(omni.ext.IExt):
    def on_startup(self):
        """Called to load the extension"""

        self._stage = omni.usd.get_context().get_stage()
        self._window = omni.ui.Window(
            EXTENSION_NAME, width=600, height=400, visible=False, dockPreference=ui.DockPreference.LEFT_BOTTOM
        )
        self._menu_items = [
            MenuItemDescription(
                name="Isaac",
                sub_menu=[
                    MenuItemDescription(
                        name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback()
                    )
                ],
            )
        ]
        add_menu_items(self._menu_items, "Window")
        self.models = {}
        with self._window.frame:
            with ui.HStack():
                with ui.VStack(height=0):
                    with ui.HStack():
                        omni.ui.Label("Clear Parent Transform", height=0)
                        self.parent_xform = omni.ui.CheckBox()
                        self.parent_xform.model.set_value(False)
                    ui.Label("Input")
                    ui.Line(height=10)
                    with ui.HStack():
                        # ui.Label("Mesh: ")
                        self.models["input_mesh"] = ui.StringField()
                        self.models["input_mesh"].model.set_value("No Mesh Selected")
                    with ui.HStack():
                        ui.Label("Submeshes:")
                        self.models["submesh"] = ui.IntField()
                    with ui.HStack():
                        ui.Label("Geometry Subsets:")
                        self.models["subset"] = ui.IntField()
                    with ui.HStack():
                        ui.Label("Materials")
                        self.models["materials"] = ui.IntField()
                    ui.Spacer(height=10)
                    ui.Label("Output")
                    ui.Line(height=10)
                    with ui.HStack():
                        ui.Label("Mesh: ")
                        self.models["output_mesh"] = ui.StringField()
                        self.models["output_mesh"].model.set_value("No Mesh Selected")
                    with ui.HStack():
                        ui.Label("Geometry Subsets:")
                        self.models["output_subset"] = ui.IntField()
                with ui.VStack():
                    ui.Button("Merge Selected Prim", clicked_fn=self._merge_mesh)

    def _menu_callback(self):
        self._window.visible = not self._window.visible
        if self._window.visible:
            self._usd_context = omni.usd.get_context()
            if self._usd_context is not None:
                self._selection = self._usd_context.get_selection()
                self._events = self._usd_context.get_stage_event_stream()
                self._stage_event_sub = self._events.create_subscription_to_pop(
                    self._on_stage_event, name="Mesh merge tool stage event"
                )
        else:
            self._stage_event_sub = None

    def _on_stage_event(self, event):
        if self._window.visible:
            if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
                selection = self._selection.get_selected_prim_paths()
                stage = self._usd_context.get_stage()
                if len(selection) == 0:
                    pass
                else:
                    curr_prim = stage.GetPrimAtPath(selection[0])
                    self.models["input_mesh"].model.set_value(selection[0])
                    total_meshes = 0
                    total_subsets = 0
                    materials = {}
                    for child_prim in Usd.PrimRange(curr_prim):
                        imageable = UsdGeom.Imageable(child_prim)
                        visible = imageable.ComputeVisibility(Usd.TimeCode.Default())
                        if child_prim.IsA(UsdGeom.Mesh) and visible != UsdGeom.Tokens.invisible:
                            usdMesh = UsdGeom.Mesh(child_prim)
                            mat, rel = UsdShade.MaterialBindingAPI(usdMesh).ComputeBoundMaterial()
                            if rel:
                                materials[str(mat.GetPath())] = 1
                            subsets = UsdGeom.Subset.GetAllGeomSubsets(UsdGeom.Imageable(child_prim))
                            if len(subsets):
                                total_subsets = total_subsets + len(subsets)
                                for s in subsets:
                                    mat, rel = UsdShade.MaterialBindingAPI(s).ComputeBoundMaterial()
                                    materials[str(mat.GetPath())] = 1
                            else:
                                total_meshes = total_meshes + 1

                    # print(*materials, sep = "\n")

                    self.models["submesh"].model.set_value(total_meshes)
                    self.models["subset"].model.set_value(total_subsets)
                    self.models["materials"].model.set_value(len(materials))
                    merged_path = "/Merged/" + str(curr_prim.GetName())
                    merged_path = omni.kit.utils.get_stage_next_free_path(stage, merged_path, False)
                    self.models["output_mesh"].model.set_value(merged_path)
                    self.models["output_subset"].model.set_value(len(materials))

    def _merge_mesh(self):
        stage = omni.usd.get_context().get_stage()
        selectedPrims = omni.usd.get_context().get_selection().get_selected_prim_paths()
        if len(selectedPrims) > 0:
            curr_prim_path = selectedPrims[-1]
        else:
            curr_prim_path = None
        curr_prim = stage.GetPrimAtPath(curr_prim_path)
        prim_transform = omni.usd.utils.get_world_transform_matrix(curr_prim, Usd.TimeCode.Default())
        count = 0
        meshes = []
        for child_prim in Usd.PrimRange(curr_prim):
            imageable = UsdGeom.Imageable(child_prim)
            visible = imageable.ComputeVisibility(Usd.TimeCode.Default())
            if child_prim.IsA(UsdGeom.Mesh) and visible != UsdGeom.Tokens.invisible:
                usdMesh = UsdGeom.Mesh(child_prim)
                mesh = {}
                mesh["points"] = usdMesh.GetPointsAttr().Get()
                world_mtx = omni.usd.utils.get_world_transform_matrix(child_prim, Usd.TimeCode.Default())
                if self.parent_xform.model.get_value_as_bool():
                    world_mtx = prim_transform * world_mtx * prim_transform.GetInverse()
                else:
                    world_mtx = world_mtx * prim_transform.GetInverse()
                # print(world_mtx)
                mesh["points"][:] = [world_mtx.TransformAffine(x) for x in mesh["points"]]
                mesh["normals"] = usdMesh.GetNormalsAttr().Get()
                mesh["vertex_counts"] = usdMesh.GetFaceVertexCountsAttr().Get()
                mesh["vertex_indices"] = usdMesh.GetFaceVertexIndicesAttr().Get()
                # mesh["st"] = usdMesh.GetPrimvar("st").Get()
                mesh["name"] = child_prim.GetName()
                mat, rel = UsdShade.MaterialBindingAPI(usdMesh).ComputeBoundMaterial()
                if rel:
                    mesh["mat"] = str(mat.GetPath())
                else:
                    mesh["mat"] = "/None"
                subsets = UsdGeom.Subset.GetAllGeomSubsets(UsdGeom.Imageable(child_prim))
                mesh["subset"] = []
                for s in subsets:
                    mat, rel = UsdShade.MaterialBindingAPI(s).ComputeBoundMaterial()
                    mesh["subset"].append((str(mat.GetPath()), s.GetIndicesAttr().Get()))
                # print(mat.GetPath(), rel)
                # print("INDICES", mesh["normals"])
                meshes.append(mesh)
                # print(count)
                # print(len(mesh["points"]), len(mesh["normals"]), len(mesh["vertex_counts"]), len(mesh["vertex_indices"]))
                count = count + 1
        print("Merging: ", count)
        all_points = []
        all_normals = []
        all_vertex_counts = []
        all_vertex_indices = []
        all_mats = {}
        index_offset = 0
        index = 0
        range_offset = 0
        for mesh in meshes:
            all_points.extend(mesh["points"])
            all_normals.extend(mesh["normals"])
            all_vertex_counts.extend(mesh["vertex_counts"])
            mesh["vertex_indices"][:] = [x + index_offset for x in mesh["vertex_indices"]]
            all_vertex_indices.extend(mesh["vertex_indices"])
            # all_st.extend(mesh["st"])
            index_offset = index_offset + len(meshes[index]["points"])
            # print("Offset", index_offset)
            index = index + 1
            # create the material entry
            if len(mesh["subset"]) == 0:
                if mesh["mat"] not in all_mats:
                    all_mats[mesh["mat"]] = []
                all_mats[mesh["mat"]].extend([*range(range_offset, range_offset + len(mesh["vertex_counts"]), 1)])
            else:
                for subset in mesh["subset"]:
                    if subset[0] not in all_mats:
                        all_mats[subset[0]] = []
                    all_mats[subset[0]].extend([*(x + range_offset for x in subset[1])])
            range_offset = range_offset + len(mesh["vertex_counts"])
        merged_path = "/Merged/" + str(curr_prim.GetName())
        merged_path = omni.kit.utils.get_stage_next_free_path(stage, merged_path, False)
        print("merging to path: ", merged_path)
        merged_mesh = UsdGeom.Mesh.Define(stage, merged_path)
        xform = UsdGeom.Xformable(merged_mesh)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
        if not self.parent_xform.model.get_value_as_bool():
            xform_op.Set(prim_transform)
        # merged_mesh.CreateSubdivisionSchemeAttr("none")
        # merged_mesh.CreateTriangleSubdivisionRuleAttr("smooth")
        merged_mesh.CreatePointsAttr(all_points)
        merged_mesh.CreateNormalsAttr(all_normals)
        merged_mesh.CreateFaceVertexCountsAttr(all_vertex_counts)
        merged_mesh.CreateFaceVertexIndicesAttr(all_vertex_indices)
        extent = merged_mesh.ComputeExtent(all_points)
        merged_mesh.CreateExtentAttr().Set(extent)
        # texCoord = merged_mesh.CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.varying)
        # texCoord.Set(all_st)
        # print(all_mats)
        for name, counts in all_mats.items():
            subset_name = merged_path + "/{}".format(name.rsplit("/", 1)[-1])
            # print(subset_name, name)
            geomSubset = UsdGeom.Subset.Define(stage, Sdf.Path(subset_name))
            geomSubset.CreateElementTypeAttr("face")
            geomSubset.CreateFamilyNameAttr("materialBind")
            # print(mesh["vertex_indices"])
            geomSubset.CreateIndicesAttr(counts)
            if name != "/None":
                material = UsdShade.Material.Get(stage, name)
                binding_api = UsdShade.MaterialBindingAPI(geomSubset)
                binding_api.Bind(material)

        # extent = usdMesh.ComputeExtent(Vertex)
        # usdMesh.GetExtentAttr().Set(extent)

    # def _merge_selected(self):
    #     stage = omni.usd.get_context().get_stage()
    #     selectedPrims = omni.usd.get_context().get_selection().get_selected_prim_paths()
    #     if len(selectedPrims) > 0:
    #         curr_prim_path = selectedPrims[-1]
    #     else:
    #         curr_prim_path = None
    #     curr_prim = stage.GetPrimAtPath(curr_prim_path)
    #     meshes_to_process = None
    #     while True:
    #         for child_prim in Usd.PrimRange(curr_prim):
    #             if (
    #                 child_prim.IsA(UsdGeom.Mesh)
    #                 and child_prim.GetParent() != curr_prim
    #                 and child_prim.GetParent().IsA(UsdGeom.Xformable)
    #             ):
    #                 meshes_to_process = child_prim
    #                 break
    #         if meshes_to_process is None:
    #             break
    #         print("Process", meshes_to_process)
    #         omni.kit.commands.execute(
    #             "MovePrimCommand",
    #             path_from=meshes_to_process.GetPrimPath(),
    #             path_to=curr_prim_path + "/" + meshes_to_process.GetName(),
    #             time_code=Usd.TimeCode.Default(),
    #             keep_world_transform=True,
    #             force_fallback=False,
    #         )
    #         meshes_to_process = None
    def on_shutdown(self):
        """Called when the extesion us unloaded"""
        remove_menu_items(self._menu_items, "Window")
        self._window = None
        gc.collect()
