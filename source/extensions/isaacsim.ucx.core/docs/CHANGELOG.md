# Changelog

All notable changes to the UCX Core extension will be documented in this file.

## [1.1.0] - 2025-11-24
### Added
- Added `UcxUtils.h`.
### Changed
- Refactored UCXListener's tag messaging functions.

## [1.0.0] - 2025-10-15

### Added
- **UCX Communication Wrappers**
  - **UCXConnection**: High-performance point-to-point communication
    - Tagged send/receive operations for efficient message routing
    - Multi-buffer operations supporting CPU and CUDA memory transfers
    - Thread-safe connection lifecycle management

  - **UCXListener**: Server-side listener for incoming connections
    - Configurable port binding with timeout support
    - Thread-safe client connection tracking

  - **UCXListenerRegistry**: Centralized listener management
    - Singleton pattern ensuring one listener per port
    - Thread-safe listener creation and retrieval

- **Plugin Interface**: Carbonite plugin that publishes simulation clock and physics steps

- **Testing**: Unit tests for core components using doctest framework
