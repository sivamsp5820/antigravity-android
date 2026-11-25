# Mobile Testing Mindset (ARTEMIS Integration)

Write executable tests based on device behavior verified with **ARTEMIS**. Before authoring a test, explore the target application and confirm its screens, transitions, and interactions. Use ARTEMIS device actions or ADB commands to investigate software and hardware behavior instead of assuming how an interaction works.

## 1. The Runnable Code Principle & ARTEMIS Exploration

- **Explore before authoring**: Before writing any test code, use ARTEMIS MCP tools (`mobile_run_task`, `mobile_get_device_state`) to interactively run and explore the target application and discover exact UI states, transitions, and interactions.
- **Timing & Latency Management**:
  - Use ARTEMIS to discover and verify the interaction path, then implement exact, deterministic timing and wait conditions in final authored test scripts.
  - When delegating timed waits to ARTEMIS during exploration, account for model step latency (Flash ~5s/step, Pro ~30s/turn).

## 2. Flash vs. Pro Routing Strategy

- **ARTEMIS Flash**: Fast reactive single-model observe-and-act loop. Use for simple, deterministic UI operations, smoke checks, and direct navigation.
- **ARTEMIS Pro**: Multi-agent Planner + Operator + read-only Checker closed loop. Use for long-range multi-branch tasks, verified `checkpoints`/`strict` assertions, continuous monitoring loops, ADB/log/video diagnostics, or detailed reports.

## 3. Device & Environment Management

- **Multi-Device Priority**: Run `adb devices -l` to inspect connected hardware/emulators. When multiple devices are connected or selection is ambiguous, **ask the user** which `device_serial` to target before launching a task.
- **Per-Device Mutex**: Different devices run in parallel; a single device executes one task at a time.
- **Host Extraction**: Use `adb -s <serial> pull ...` and `adb -s <serial> logcat` to extract logs or artifacts to the host.

## 4. Robust Test Code ("Dynamic-First, Coordinate-Fallback")

- Prioritize dynamic locators (resource IDs, text, OCR, accessibility semantics) so tests survive layout and resolution changes.
- Use verified absolute coordinates only as a fallback (`try` dynamic locator -> `catch` coordinate fallback) when dynamic locators are unavailable.

## 5. Environment Self-Diagnosis (`mobile_diagnose`)

- Whenever an ARTEMIS tool errors, a task fails to start, or no device is found, call `mobile_diagnose` first (use `attempt_fix=true` for safe self-heals, `verify_credentials=true` for auth checks, `probe_device=true` for end-to-end UIAutomator checks, `launch_avd="<name>"` to boot an AVD).
- Never pass API keys through chat; direct the user to update `.env` and reload the MCP server.
- If `mobile_diagnose` is not in your tool list, run `uv run --project /home/sivamsp/tools/artemis artemis doctor`.
