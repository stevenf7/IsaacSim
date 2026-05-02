# Changelog

## [1.7.1] - 2026-04-24
### Added
- `JointStateAPIRule` applies `PhysxSchema.JointStateAPI` (`linear` on prismatic, `angular` on revolute) to non-fixed joints missing it. Wired into the Isaac Sim profile between `Fix Physics Joint Poses` and `Route Materials`.
- `MakeListsNonExplicitRule` now normalizes the `isaac:physics:robotLinks` and `isaac:physics:robotJoints` relationships to `prepend` list ops, walking each prim's `GetPrimStack()` so sublayered PrimSpecs are also rewritten. A second profile entry is added to `isaacsim_structure.json` targeting these relationships.

## [1.7.0] - 2026-04-22
### Added
- MergeMeshRule to merge visual mesh prims grouped under rigid bodies via Scene Optimizer
- MjcToPhysxConversionRule to convert MJCF actuator/joint attributes to PhysX drive and joint schemas
- UrdfToMjcPhysxConversionRule to convert URDF joint attributes to MJCF actuators and PhysX schemas

## [1.6.0] - 2026-04-20
### Added
- `GeometriesRoutingRule` now quantizes hashed geometry values to a physical 1 mm grid derived from the stage's `metersPerUnit` (and the mesh's extent magnitude), so meshes authored in m, cm, or mm deduplicate against the same resolution instead of relying on raw float string comparison. Large arrays (points, normals, UVs) are quantized via NumPy in C.
- `GeometriesRoutingRule` now tracks a global `used_geometry_names` set so newly emitted geometry names cannot collide with pre-existing entries when deduplication is enabled.
- `visibility` added to `_INSTANCE_SPECIFIC_PROPERTIES` so it is no longer baked into the geometry hash.

### Changed
- `GeometriesRoutingRule._compute_geometry_hash` now ignores xform properties and replaces the previous `str(value)` hashing with a unit-aware quantization via the new `_quantize_value` helper.

### Fixed
- `MaterialsRoutingRule` no longer duplicates local texture files when the target path already exists with identical content; a `files_are_identical` check short-circuits the rename loop before appending a counter.

## [1.5.0] - 2026-04-14
### Added
- `DEFAULT_PROFILE_PATH` module-level constant exposing the path to the bundled `isaacsim_structure.json` profile
- `register_all_rules()` standalone function for registering all built-in rules without Kit's extension lifecycle

## [1.4.0] - 2026-04-09
### Added
- Test verifying multiple sibling meshes under a parent Xform are preserved as separate instanceable references

### Fixed
- GeometriesRoutingRule `_is_subtree_empty` not checking composition arcs, causing premature merging of sibling meshes that carry references but no authored properties
- GeometriesRoutingRule setting empty `typeName` on prim specs, which triggers a USD error
- GeometriesRoutingRule not propagating `purpose=guide` from parent Xform to child mesh prim in the instances layer
- `is_builtin_mdl` not recognizing `omnisurfacepresets.mdl`, `core_definitions.mdl`, and path-suffix forms like `nvidia/core_definitions.mdl`

## [1.3.0] - 2026-04-08
### Changed
- Improve Python API documentation (`config/python_api.md` and/or module docstrings).

## [1.2.0] - 2026-03-09
### Added
- PhysicsJointPoseFixRule to correct joint local poses after body world transforms change
- Idempotency test that runs the Isaac Sim profile twice and asserts stable output

### Fixed
- VariantRoutingRule leaving self-referencing payload arcs on extracted variant layers
- GeometriesRoutingRule non-idempotent merge decisions when VisualMaterials scopes or empty siblings remain after geometry extraction
- GeometriesRoutingRule floating-point precision drift in xformOp values across consecutive serialization round-trips
- GeometriesRoutingRule retaining root-level prims outside the defaultPrim hierarchy after flattening
- GeometriesRoutingRule quaternion sign ambiguity (q vs -q) causing idempotency test failure on double-transform
- SchemaRoutingRule, PropertyRoutingRule, and PrimRoutingRule using root layer defaultPrim instead of composed stage defaultPrim
- RobotSchemaRule not setting defaultPrim when no matching Isaac Robot schemas are found

## [1.1.2] - 2026-03-02
### Fixed
- Ensure all generated relative paths (references, payloads, sublayers) use explicit `./` or `../` prefixes

## [1.1.1] - 2026-02-26
### Changed
- Updated isaacsim_structure.json to delete Newton Mimic api in physx to avoid conflict

## [1.1.0] - 2026-02-17
### Added
- Overwrite schema rule

## [1.0.2] - 2026-02-16
### Fixed
- Fix geometry rule for negative scale and proper deduplicate

## [1.0.1] - 2026-02-13
### Fixed
- Tests failing due to misconfiguration of tests

## [1.0.0] - 2026-02-12
### Added
- First version of Asset Transformer core rules
