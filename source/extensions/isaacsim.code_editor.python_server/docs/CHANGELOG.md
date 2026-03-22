# Changelog

## [1.0.1] - 2026-03-20
### Fixed
- Replace `run_coroutine_threadsafe` with `ensure_future` in `data_received` to avoid `RuntimeError: Cannot enter into task` when other extensions have pending asyncio tasks

## [1.0.0] - 2026-03-09
### Added
- Initial release, extracted from isaacsim.code_editor.vscode
- TCP socket server for remote Python code execution
- Optional UDP-based Carbonite log broadcasting
- Expression evaluation with `result` field in JSON response
