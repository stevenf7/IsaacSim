import omni.kit.commands

omni.kit.commands.execute(
    "CreateAndBindMdlMaterialFromLibrary",
    mdl_name="OmniSurface.mdl",
    mtl_name="OmniSurface",
    mtl_created_list=["/Looks/OmniSurface"],
)

new_material = UsdShade.Material.Get(stage, "/Looks/OmniSurface")

binding_api = UsdShade.MaterialBindingAPI.Apply(sphere)
binding_api.Bind(new_material)
