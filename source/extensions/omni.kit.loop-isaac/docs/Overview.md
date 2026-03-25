# Overview

The omni.kit.loop-isaac extension provides a custom loop runner for Isaac Sim that controls simulation timing and frame stepping. It replaces the default Kit loop runner with one that supports manual stepping mode, fixed timesteps, and multi-tick rendering for deterministic physics simulation.

This extension must be enabled during app startup by adding it as a dependency in your application's `.kit` file.

## Functionality

- **Manual stepping mode**: Enables explicit control over when simulation frames advance, allowing external code to step the simulation at a controlled rate
- **Fixed timestep control**: Configurable step sizes for deterministic simulation behavior independent of wall-clock time
- **Rate limiting**: Configurable rate limits for main, present, and rendering run loops (defaults: main and rendering at 120Hz, present at 60Hz)
- **External simulation time**: Supports setting simulation time from external sources for synchronized multi-system simulations
