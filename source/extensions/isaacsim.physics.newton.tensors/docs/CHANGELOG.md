# Changelog

## [0.1.1] - 2026-04-22
### Fixed
- Fix contact point positions for MuJoCo backend: detect world-space contact positions from `mjw_data.contact.pos` and skip body-local-to-world rotation in CPU and GPU contact data kernels

- Fix contact force dt scaling in `BaseRigidContactView` to apply `sim_dt / user_dt` matching the Python tensor implementation


## [0.1.0] - 2026-04-14
### Added
- C++ tensor backend implementing `omni.physics.tensors` interfaces for Newton physics, with CPU and GPU (Warp/CUDA) implementations of `SimulationView`, `ArticulationView`, `RigidBodyView`, and `RigidContactView`. Supports three device configurations (CPU sim + CPU view, GPU sim + CPU view, GPU sim + GPU view) for articulation and rigid body state, force/torque application, and contact queries.
