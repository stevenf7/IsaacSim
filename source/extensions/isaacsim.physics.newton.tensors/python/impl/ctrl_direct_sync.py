# SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""CTRL_DIRECT synchronization helpers for the C++ Newton tensor backend.

These functions mirror the logic in ``NewtonArticulationView`` (Python)
for syncing PD gains and position targets to the MuJoCo solver. The C++
backend calls them via pybind11 after set_dof_stiffnesses / set_dof_dampings
/ set_dof_position_targets.
"""

from __future__ import annotations

from typing import Any

import warp as wp

_dof_map_cache: wp.array | None = None
_dof_map_initialized: bool = False
_biastype_set: bool = False


def reset() -> None:
    """Reset cached state (call when simulation is destroyed)."""
    global _dof_map_cache, _dof_map_initialized, _biastype_set
    _dof_map_cache = None
    _dof_map_initialized = False
    _biastype_set = False


def _get_dof_map(model: Any) -> wp.array | None:
    """Return the cached CTRL_DIRECT DOF mapping array, building it on first call.

    Args:
        model: The Newton model object.

    Returns:
        Warp array mapping DOF indices to actuator indices, or None if unavailable.
    """
    global _dof_map_cache, _dof_map_initialized
    if not _dof_map_initialized:
        _dof_map_initialized = True
        try:
            from isaacsim.physics.newton.impl.tensors.kernels import build_ctrl_direct_dof_mapping

            _dof_map_cache = build_ctrl_direct_dof_mapping(model)
        except Exception:
            _dof_map_cache = None
    return _dof_map_cache


def sync_actuator_gains(newton_stage: Any, model: Any) -> None:
    """Sync joint_target_ke/kd to MuJoCo actuator gainprm/biasprm.

    Args:
        newton_stage: The Newton stage object.
        model: The Newton model object.
    """
    dof_map = _get_dof_map(model)
    if dof_map is None:
        return
    mujoco_attrs = getattr(model, "mujoco", None)
    if mujoco_attrs is None:
        return
    gainprm = getattr(mujoco_attrs, "actuator_gainprm", None)
    biasprm = getattr(mujoco_attrs, "actuator_biasprm", None)
    if gainprm is None or biasprm is None:
        return
    nworlds = model.world_count if hasattr(model, "world_count") else 1
    dofs_per_world = model.joint_dof_count // max(nworlds, 1)

    from isaacsim.physics.newton.impl.tensors.kernels import sync_ctrl_direct_gains

    wp.launch(
        sync_ctrl_direct_gains,
        dim=(dofs_per_world,),
        inputs=[dof_map, model.joint_target_ke, model.joint_target_kd],
        outputs=[gainprm, biasprm],
        device=model.device,
    )

    try:
        import newton.solvers

        solver = getattr(newton_stage, "solver", None)
        if solver is not None:
            solver.notify_model_changed(newton.solvers.SolverNotifyFlags.ACTUATOR_PROPERTIES)
    except (AttributeError, ImportError):
        pass


def sync_position_targets(newton_stage: Any, model: Any) -> None:
    """Sync joint_target_pos to control.mujoco.ctrl for CTRL_DIRECT actuators.

    Args:
        newton_stage: The Newton stage object.
        model: The Newton model object.
    """
    global _biastype_set
    dof_map = _get_dof_map(model)
    if dof_map is None:
        return
    control = getattr(newton_stage, "control", None)
    if control is None:
        return
    mujoco_ctrl = getattr(getattr(control, "mujoco", None), "ctrl", None)
    if mujoco_ctrl is None:
        return
    nworlds = model.world_count if hasattr(model, "world_count") else 1
    dofs_per_world = model.joint_dof_count // max(nworlds, 1)
    ctrls_per_world = mujoco_ctrl.shape[0] // max(nworlds, 1)

    from isaacsim.physics.newton.impl.tensors.kernels import sync_ctrl_direct_targets

    wp.launch(
        sync_ctrl_direct_targets,
        dim=(nworlds, dofs_per_world),
        inputs=[dof_map, control.joint_target_pos, dofs_per_world, ctrls_per_world],
        outputs=[mujoco_ctrl],
        device=model.device,
    )

    if not _biastype_set:
        _biastype_set = True
        _set_ctrl_direct_biastype_affine(newton_stage, model, dof_map)


def _set_ctrl_direct_biastype_affine(newton_stage: Any, model: Any, dof_map: wp.array) -> None:
    """Set biastype=AFFINE for CTRL_DIRECT actuators.

    Args:
        newton_stage: The Newton stage object.
        model: The Newton model object.
        dof_map: Warp array mapping DOF indices to actuator indices.
    """
    BIAS_AFFINE = 1
    dof_map_np = dof_map.numpy()
    newton_act_indices = sorted({int(a) for a in dof_map_np if a >= 0})
    mujoco_attrs = getattr(model, "mujoco", None)
    if mujoco_attrs is not None:
        bt = getattr(mujoco_attrs, "actuator_biastype", None)
        if bt is not None:
            bt_np = bt.numpy()
            for act_idx in newton_act_indices:
                if act_idx < len(bt_np):
                    bt_np[act_idx] = BIAS_AFFINE
            wp.copy(bt, wp.array(bt_np, dtype=bt.dtype, device=bt.device))

    solver = getattr(newton_stage, "solver", None)
    if solver is None:
        return
    ctrl_source = getattr(solver, "mjc_actuator_ctrl_source", None)
    if ctrl_source is None:
        return
    ctrl_np = ctrl_source.numpy()
    mjc_act_indices = [i for i in range(len(ctrl_np)) if int(ctrl_np[i]) == 1]
    if not mjc_act_indices:
        return

    mj_model = getattr(solver, "mj_model", None)
    if mj_model is not None and hasattr(mj_model, "actuator_biastype"):
        for act_idx in mjc_act_indices:
            if act_idx < len(mj_model.actuator_biastype):
                mj_model.actuator_biastype[act_idx] = BIAS_AFFINE

    mjw_model = getattr(solver, "mjw_model", None)
    if mjw_model is not None:
        bt_warp = getattr(mjw_model, "actuator_biastype", None)
        if bt_warp is not None:
            bt_np = bt_warp.numpy()
            if bt_np.ndim == 2:
                for act_idx in mjc_act_indices:
                    if act_idx < bt_np.shape[1]:
                        bt_np[:, act_idx] = BIAS_AFFINE
            elif bt_np.ndim == 1:
                for act_idx in mjc_act_indices:
                    if act_idx < len(bt_np):
                        bt_np[act_idx] = BIAS_AFFINE
            wp.copy(bt_warp, wp.array(bt_np, dtype=bt_warp.dtype, device=bt_warp.device))
