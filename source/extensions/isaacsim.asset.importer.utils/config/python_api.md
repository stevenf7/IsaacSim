# Public API for module isaacsim.asset.importer.utils:

# Public API for module isaacsim.asset.importer.utils.impl.importer_utils:

## Classes

- class PhysxAttr(Enum)
  - JOINT_ARMATURE: Tuple
  - JOINT_FRICTION: Tuple
  - JOINT_MAX_VELOCITY: Tuple
  - ARTICULATION_SELF_COLLISION: Tuple
  - [property] def name(self) -> str
  - [property] def type(self) -> Sdf.ValueTypeName

- class PhysxMimicAttr(Enum)
  - GEARING: Tuple
  - OFFSET: Tuple
  - REFERENCE_JOINT_AXIS: Tuple
  - [property] def type(self) -> Sdf.ValueTypeName
  - def format(self, axis: str) -> str

- class PhysxMimicRel(Enum)
  - REFERENCE_JOINT: str
  - def format(self, axis: str) -> str

- class PhysxSchema(str, Enum)
  - JOINT_API: str
  - ARTICULATION_API: str
  - MIMIC_JOINT_API: str
  - JOINT_STATE_API: str

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
