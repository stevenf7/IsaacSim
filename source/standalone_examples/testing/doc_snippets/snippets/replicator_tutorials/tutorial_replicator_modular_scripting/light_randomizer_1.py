def _setup(self):
    include_children = self._get_exposed_variable("includeChildren")
    if include_children:
        self._valid_prims = [prim for prim in Usd.PrimRange(self.prim) if prim.HasAPI(UsdLux.LightAPI)]
    elif self.prim.HasAPI(UsdLux.LightAPI):
        self._valid_prims = [self.prim]
    else:
        self._valid_prims = []
        carb.log_warn(f"[{self.prim_path}] No valid light prims found.")
