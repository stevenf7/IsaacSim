# Changelog

## [0.1.0] - 2026-06-05
### Added
- Initial NuRec rendering utilities and standalone example for rendering neural reconstruction
  NuRec USDs from `source/standalone_examples/nurec/nurec_render.py`.
- Rendering setup helpers that detect NuRec USD types (`ParticleField` gaussian splats, NuRec
  volumes, and SPG/PPISP render graphs), enforce launch prerequisites (`omni.rtx.spg` and
  single-GPU rendering), and apply the matching runtime carb overrides for PPISP and plain NuRec
  NuRec USDs.
- Render-product and capture utilities that use authored SPG RenderProducts for PPISP NuRec USDs or
  create camera RenderProducts for plain NuRec USDs, then render frames from sensor-rig keyframes or
  explicit TUM camera poses.
- Pass-through camera exposure handling for PPISP NuRec USDs so the SPG/PPISP graph remains the sole
  photometric authority during capture.
- Manifest, image I/O, timestamp, sensor-rig keyframe matching, camera pose extraction, TUM
  trajectory read/write, and frame-selection helpers used by the renderer and tests.
- PSNR, SSIM, mean-absolute-difference, image-diff, plotting, and GT-evaluation helpers for
  comparing rendered frames against ground-truth image trees.
- NuRec regression test assets, including original and extended `endeavor_lr1` GT timestamp sets,
  and tests covering Kit-free helper behavior, torch-backed metrics, SPG detection and launch
  gating, render-vs-GT scoring, and keyframe-vs-explicit-pose rendering consistency.
- User documentation for rendering NuRec USDs from explicit poses or sensor-rig keyframes, plus
  GT scoring guidance, in the NuRec USD assets page.
- Native Python test registration for the Kit-free NuRec helper unit suite.
