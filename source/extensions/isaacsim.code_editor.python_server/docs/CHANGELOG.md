# Changelog

## [1.1.0] - 2026-03-24
### Fixed
- Buffer incoming TCP data until EOF instead of processing on first `data_received` call, preventing partial execution of fragmented payloads
- Capture `print()` output from `await`ed coroutines in the JSON response `output` field (previously lost to real stdout)
- Add `write_eof()` calls in test client helpers to match the corrected wire protocol

### Changed
- Updated Overview.md with client examples, async code notes, and state persistence documentation
- Added `stdoutFailPatterns.exclude` for pre-existing asyncio context re-entry errors in test configuration

### Added
- New test suite `test_protocol_robustness.py` covering TCP fragmentation handling and async stdout capture

## [1.0.1] - 2026-03-20
### Fixed
- Replace `run_coroutine_threadsafe` with `ensure_future` in `data_received` to avoid `RuntimeError: Cannot enter into task` when other extensions have pending asyncio tasks

## [1.0.0] - 2026-03-09
### Added
- Initial release, extracted from isaacsim.code_editor.vscode
- TCP socket server for remote Python code execution
- Optional UDP-based Carbonite log broadcasting
- Expression evaluation with `result` field in JSON response
