import omni.kit.commands
import omni.kit.utils
import carb
from pxr import Sdf
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.utils._isaac_utils import transforms
import asyncio


class IsaacSimSpawnPrim(omni.kit.commands.Command):
    def __init__(
        self, usd_path: str, prim_path: str, translation: carb.Float3 = (0, 0, 0), rotation: carb.Float4 = (0, 0, 0, 1)
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._stage = omni.usd.get_context().get_stage()
        self._context = omni.usd.get_context()
        pass

    def do(self) -> bool:
        async def spawn_task():
            self._prim = self._stage.DefinePrim(self._prim_path, "Xform")
            await omni.kit.app.get_app().next_update_async()
            self._prim.GetReferences().AddReference(self._usd_path)
            await omni.kit.app.get_app().next_update_async()
            transforms.set_transform(
                self._dc,
                self._context.get_stage_id(),
                str(self._prim.GetPath()),
                tuple(self._translation),
                tuple(self._rotation),
            )

        asyncio.ensure_future(spawn_task())
        return True
        pass

    def undo(self):
        pass


class IsaacSimTeleportPrim(omni.kit.commands.Command):
    def __init__(self, prim_path: str, translation: carb.Float3 = (0, 0, 0), rotation: carb.Float4 = (0, 0, 0, 1)):
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._context = omni.usd.get_context()
        pass

    def do(self) -> bool:
        transforms.set_transform(
            self._dc, self._context.get_stage_id(), str(self._prim_path), self._translation, self._rotation
        )
        return True
        pass

    def undo(self):
        pass


class IsaacSimDestroyPrim(omni.kit.commands.Command):
    def __init__(self, prim_path: str):
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self) -> bool:
        stage = omni.usd.get_context().get_stage()
        for layer in stage.GetLayerStack():
            edit = Sdf.BatchNamespaceEdit()
            prim_spec = layer.GetPrimAtPath(self._prim_path)
            if prim_spec is None:
                return False
            parent_spec = prim_spec.realNameParent
            if parent_spec is not None:
                edit.Add(self._prim_path, Sdf.Path.emptyPath)
            layer.Apply(edit)
        pass

    def undo(self):
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
