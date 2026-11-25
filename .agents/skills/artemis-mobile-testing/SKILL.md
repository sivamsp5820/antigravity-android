---
name: artemis-mobile-testing
description: >-
  Use when testing, exploring, or automating the Antigravity Android app on a
  connected Android device or emulator using ARTEMIS (MCP tools or CLI), ADB,
  and UI verification workflows.
---

# ARTEMIS Mobile Testing for Antigravity Android

Use **ARTEMIS** (installed at `/home/sivamsp/tools/artemis`) to run natural-language UI tests, explore live Android screens, capture traces/screenshots, and verify `dist/antigravity.apk` on physical devices or emulators.

## 1. Pre-Flight & Device Check

1. Check connected devices:
   ```bash
   adb devices -l
   ```
   If multiple devices are connected, **ask the user** which `device_serial` to target before launching tasks.
2. If using the ARTEMIS MCP server and any tool errors or no device is found, call `mobile_diagnose` first (optionally `attempt_fix=true`, `probe_device=true`, or `launch_avd="<name>"`).
3. If `mobile_diagnose` is unavailable in your tool list, run the CLI doctor:
   ```bash
   uv run --project /home/sivamsp/tools/artemis artemis doctor
   ```

## 2. Build & Install the APK Under Test

```bash
# Build standard release APK (outputs dist/antigravity.apk)
bash build.sh

# Or build with region bypass (outputs dist/antigravity-region-bypass.apk)
bash build.sh --region-bypass

# Install onto target device
adb -s <device_serial> install -r dist/antigravity.apk
```

## 3. ARTEMIS Execution Workflows

### Via MCP Tools (Preferred in IDE)

- **`mobile_get_device_state`**: Capture a live `screenshot` or OCR+XML `hierarchy` before planning or asserting UI state.
- **`mobile_run_task`**: Launch an autonomous task:
  - **Flash profile**: Fast reactive observe-and-act loop (~3-5s/step) for straightforward UI flows, smoke tests, and tapping through onboarding/settings.
  - **Pro profile**: Multi-agent Planner + Operator + Checker loop (~15-40s/step) for complex multi-branch journeys, `verify`/`assert` checkpoints, ADB/logcat diagnostics, and written test reports. Tune with `verification_level` (`off` | `final` | `checkpoints` | `strict`) and `explorer_mode` (`flash` | `pro` | `ultra`).
- **`mobile_manage_task`**: Check `status`, `stop`, or `inject_instruction` (pass `release_loop=True` to end continuous monitoring).
- **`mobile_inspect_trace`**: Review step-by-step screenshots, overlays, and agent reasoning after a run.

### Via CLI (Fallback / CI)

```bash
uv run --project /home/sivamsp/tools/artemis artemis run "<natural-language test goal>"
```

## 4. Authoring Deterministic Mobile Tests

1. **Explore First**: Never guess resource IDs, text labels, or screen transitions—verify them live with ARTEMIS first.
2. **Dynamic-First, Coordinate-Fallback**: Prioritize resource IDs, content descriptions, and text/OCR locators; use verified coordinates only as a fallback.
3. **Explicit Waits**: Replace ARTEMIS's LLM step latency with deterministic wait conditions (`sleep`, UIAutomator/Espresso idle waits) in final test scripts.
4. **Diagnostics**: Pull device logs or artifacts with `adb -s <serial> logcat -d -t 200` or `adb -s <serial> pull ...`.
