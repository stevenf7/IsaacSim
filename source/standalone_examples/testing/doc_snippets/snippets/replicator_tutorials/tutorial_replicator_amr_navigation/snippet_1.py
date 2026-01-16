def _run_sdg(self) -> None:
    if self._use_temp_rp:
        self._enable_render_products()
    rep.orchestrator.step(rt_subframes=16)
    if self._use_temp_rp:
        self._disable_render_products()
