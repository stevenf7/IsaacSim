# Public API for module isaacsim.asset.importer.mjcf:

## Classes

- class MJCFImporterConfig
  - mjcf_path: str | None
  - usd_path: str | None
  - import_scene: bool
  - merge_mesh: bool
  - debug_mode: bool
  - collision_from_visuals: bool
  - collision_type: str
  - allow_self_collision: bool

- class MJCFImporter
  - def __init__(self, config: MJCFImporterConfig | None = None)
  - [property] def config(self) -> MJCFImporterConfig
  - [config.setter] def config(self, config: MJCFImporterConfig)
  - def import_mjcf(self, config: MJCFImporterConfig | None = None) -> str

- class Extension(omni.ext.IExt)
  - def on_startup(self, ext_id: str)
  - def on_shutdown(self)

## Other

- gc: builtin module
- omni.ext: unknown module
