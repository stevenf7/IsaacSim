import omni.ext
from isaacsim.asset.conveyor.bindings._isaacsim_asset_conveyor import acquire_interface as _acquire
from isaacsim.asset.conveyor.bindings._isaacsim_asset_conveyor import release_interface as _release


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self.__interface = _acquire()

    def on_shutdown(self):
        _release(self.__interface)
        self.__interface = None
