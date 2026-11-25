# Antigravity Android Workspace Rules

## 1. Repository Architecture

This repository builds **Antigravity for Android** (native ARM64 Bionic userspace + Android host app + local web frontend, without Gradle):

- `app/` — Android host app (125+ Java sources, `AndroidManifest.xml`, resources, native splash, WebView, system bridges).
- `modules/` — Decoupled core subsystems:
  - `core/` — Binary unpacking, glibc loader, shims, SHA-256 manifest
  - `patches/` — Binary patch engine (syscall emulation, resolv, SIGILL)
  - `io/` — I/O bus, event broker, FIFO pipes, sockets
  - `env/` — Path resolver, diagnostics, Flight Recorder logs, CLI
  - `builder/` — Gradle-free APK builder (`javac`, `d8`/`r8.jar`, `aapt`, `zipalign`, `apksigner`)
  - `runner/` — Standalone runtime preparation, port probe, E2E tests
- `web/` — Local web frontend (HTML/CSS/JS, workers, Tailwind, self-tests)
- `env/` — Bionic userspace, Termux overlay, `pkg` manager, `liblse_compat`
- `config/` — App constants (`app.env`, `paths.env`, `tools.env`) and **`config/AGENTS.md`** (the in-app runtime agent rules bundled into the Android app—do not confuse with workspace dev rules).

## 2. Build & Verification Commands

- **Build standard APK**: `bash build.sh` (outputs `dist/antigravity.apk`)
- **Build region-bypass APK**: `bash build.sh --region-bypass`
- **Fast iteration build**: `bash build.sh --fast`
- **Run full modular test suite**: `bash test_all_modules.sh`
- **Run individual module tests**: `bash modules/<name>/tests/run_all.sh` or `bash modules/runner/test_e2e.sh`

## 3. Coding & Platform Constraints

- **No Gradle**: Java compilation and DEX packaging are driven by `modules/builder/build_apk.sh` using `tools/android.jar`, `tools/r8.jar`, and `tools/debug.keystore`. Keep `app/` compatible with this pipeline.
- **ARMv8.0-A Baseline**: Native binaries/libraries must target `-march=armv8-a` baseline (with `liblse_compat` for older CPUs without hardware LSE atomics).
- **Android Userspace Reality**: Code running inside the app executes under Android Bionic with `noexec` on `/storage/emulated/0` and no `bwrap` sandboxing; avoid desktop-only Linux assumptions.
- **Shell Scripts**: Follow `bash-defensive-patterns` (`set -euo pipefail`, quoted paths, explicit interpreters).
- **Documentation Sync**: Every module (`modules/*`, `app/`, `web/`, `env/`) maintains its own `README.md`. Update the relevant `README.md` whenever you change interfaces, flags, or module behavior.
- **Clean Working Tree**: Never commit temporary build outputs (`dist/`, `.build/`, `*.apk`).
