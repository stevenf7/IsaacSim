def register_cardboxes_materials_graph_randomizer(
    cardboxes: list[Usd.Prim], cardbox_material_urls: list[str], event_name: str
) -> None:
    """Register graph randomizer to apply random materials to cardbox meshes."""
    cardbox_mesh_paths = []
    for cardbox in cardboxes:
        meshes = [child for child in cardbox.GetChildren() if child.IsA(UsdGeom.Mesh)]
        cardbox_mesh_paths.extend([mesh.GetPrimPath() for mesh in meshes])

    with rep.trigger.on_custom_event(event_name):
        cardbox_mesh_group_node = rep.create.group(cardbox_mesh_paths)
        with cardbox_mesh_group_node:
            rep.randomizer.materials(cardbox_material_urls)


# Register materials randomizer
cardbox_material_urls = [
    f"{assets_root_path}/Isaac/Environments/Simple_Warehouse/Materials/MI_PaperNotes_01.mdl",
    f"{assets_root_path}/Isaac/Environments/Simple_Warehouse/Materials/MI_CardBoxB_05.mdl",
]
register_cardboxes_materials_graph_randomizer(
    cardboxes, cardbox_material_urls, event_name="randomize_cardboxes_materials"
)
