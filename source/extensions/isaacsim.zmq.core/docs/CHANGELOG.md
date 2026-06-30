# Changelog

## [1.0.1] - 2026-06-29
### Fixed
- Build: suppress spurious `-Wundef` warnings from the generated protobuf sources and stop compiling each `.proto` twice.

## [1.0.0] - 2026-04-01
### Added
- Initial release of the ZeroMQ core library for the Isaac Sim ZMQ bridge.
- Publish (PUSH) and subscribe (SUB) socket wrappers, one socket per node, with two-frame `[topic, payload]` multipart messaging.
- Protobuf message schemas (importable from the package root) and pybind11 Python bindings.
