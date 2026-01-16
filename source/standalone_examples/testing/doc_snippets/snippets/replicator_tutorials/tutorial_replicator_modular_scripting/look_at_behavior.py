def _setup(self):
    target_prim_path = self._get_exposed_variable("targetPrimPath")
    if target_prim_path:
        self._target_prim = self.stage.GetPrimAtPath(target_prim_path)
        if not self._target_prim or not self._target_prim.IsValid() or not self._target_prim.IsA(UsdGeom.Xformable):
            self._target_prim = None
            carb.log_warn(f"[{self.prim_path}] Invalid target prim path: {target_prim_path}")
