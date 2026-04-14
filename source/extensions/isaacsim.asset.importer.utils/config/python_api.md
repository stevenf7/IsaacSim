# Public API for module isaacsim.asset.importer.utils:

# Public API for module isaacsim.asset.importer.utils.impl.importer_utils:

## Classes

- class AssetTransformerManager
  - def __init__(self, registry: RuleRegistry | None = None)
  - [property] def registry(self) -> RuleRegistry
  - def run(self, input_stage_path: str, profile: RuleProfile, package_root: str | None = None) -> ExecutionReport

- class RuleProfile
  - profile_name: str
  - version: str | None
  - rules: list[RuleSpec]
  - interface_asset_name: str | None
  - output_package_root: str | None
  - flatten_source: bool
  - base_name: str | None
  - def to_dict(self) -> dict[str, Any]
  - def to_json(self) -> str
  - static def from_dict(data: dict[str, Any]) -> RuleProfile
  - static def from_json(json_str: str) -> RuleProfile

## Functions

- def collision_from_visuals(stage: Usd.Stage, collision_type: str) -> int
- def enable_self_collision(usd_stage: Usd.Stage, enabled: bool = True) -> int
- def run_asset_transformer_profile(input_stage_path: str, output_package_root: str, profile_json_path: str)
- def delete_scope(stage: Usd.Stage, prim_path: str)
- def add_joint_schemas(stage: Usd.Stage)
- def add_rigid_body_schemas(stage: Usd.Stage)
- def remove_custom_scopes(stage: Usd.Stage)
- def create_physx_mimic_joint(prim: Usd.Prim)

## Variables

- USD_GEOMETRY_TYPES: Set
- MESH_APPROXIMATION_MAP: Dict
- PHYSICS_AXIS_MAP: Dict

# Public API for module isaacsim.asset.importer.utils.impl.merge_mesh_utils:

## Functions

- def clean_mesh_operation(stage: Usd.Stage)
- def generate_mesh_uv_normals_operation(stage: Usd.Stage)
- def merge_meshes_operation(stage: Usd.Stage) -> int
- def merge_mesh(stage: Usd.Stage, meshes: list[str])

# Public API for module isaacsim.asset.importer.utils.impl.stage_utils:

## Functions

- def save_stage(stage: Usd.Stage, usd_path: str) -> bool
- def open_stage(usd_path: str) -> Usd.Stage
- def get_stage_id(stage: Usd.Stage) -> int