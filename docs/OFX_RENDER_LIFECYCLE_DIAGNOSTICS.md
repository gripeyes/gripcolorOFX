# Shared OFX render lifecycle: correlated diagnostic candidate

2026-10-05. Implementation of the **source-only diagnostic stage** of the shared render-lifecycle plan. This is not a claim that the Nuke failure is fixed.

Subsequent correction: [OFX_RENDER_CANCELLATION_FIX.md](OFX_RENDER_CANCELLATION_FIX.md). The diagnostic-only outcomes below describe the earlier candidate, not the newly installed cancellation-aware build.

## Implemented

- [render_trace.hpp](../src/ofx/render_trace.hpp) contains a fixed 128-event chronological history shared across render threads. Each render gets a monotonically increasing correlation ID; each event gets a sequence and steady-clock timestamp.
- Context includes instance, effect, thread, active renders on that instance, action time, window, scale, field, interactive flag, Metal/CUDA/OpenCL enabled state, and property-read statuses.
- Shared [plugin.cpp](../src/ofx/plugin.cpp) records before/result events for Output, Source, Reference and Matte acquisitions inside Render. It samples abort immediately before the fetch and again after any failed fetch.
- Existing suite-error records now include render ID. Failed checked calls dump adjacent history, including successful acquisitions/renders. Successful events are buffered silently.
- Enabled only with `RENDITION_SUITE_TRACE=1`. When disabled there are no new context or abort host calls. Optional diagnostic-property failures are recorded, never routed through `checkedStatus`.
- Diagnostic locking protects counters/ring copies only. No lock is held while acquiring host images, evaluating parameters, processing pixels, or formatting/writing the history dump. Active-instance entries are erased when the last traced render exits. No image/parameter handles are retained by diagnostics; recorded addresses are opaque identifiers.

`property_status` order: window, scale, field, interactive, Metal, CUDA, OpenCL. `-1` means not queried/unknown; failed getter status identifies unavailable context. A window/scale value must not be treated as known unless its getter succeeded. `abort_after_fetch=-1` on successful fetches is intentional. `active_renders` is sampled at event recording, not a guarantee that pixel processing overlapped. IDs distinguish attempts even when time/window match.

A suite failure occurs before the failing render's exit record; its dump includes that acquisition result but not the subsequent unwind event. Future failure dumps may include the unwind. Monotonic timestamps permit entry-to-fetch comparison; they are not a profiling campaign. The history is global/bounded, so heavy activity may evict older events; use instance and correlation ID to select relevant neighbors.

## Deliberately unchanged pending host evidence

The captured Nuke failure still lacks an observed abort result. Accordingly this candidate preserves all acquisition/error behavior:

| Case | Current outcome |
|---|---|
| Output status 1, abort false | Fatal and traced |
| Output status 1, abort true | Fatal and traced; diagnostic-only phase does not introduce cancellation recovery |
| Unavailable input | Existing black-transparent / zero-matte semantics |
| Successful images followed by abort | Existing row polling stops processing; acquired images release |
| Already-aborted render | Still acquires images before existing worker polling; now observable |
| Malformed image / genuine suite failure | Existing failure remains visible; successful acquisitions unwind |

No change to scheduling flags (subdivision on, tiles on), acquisition order, grading equations, controls, UI, colour interpretation, model versions or compatibility. No Pigment refactor. The existing timed-read/unavailable-input changes predate this pass and remain intact.

## Tests and build

[ofx_runtime.cpp](../tests/ofx_runtime.cpp) exercises the real shared action dispatcher with a strict mock host:

- Timed Render/IsIdentity and animated interpretation, existing absent-input cases.
- All 12 registered effects: failed Output with abort false and true is correctly observed and remains fatal.
- A fetch race changes abort false → true; both samples are retained without swallowing the failure.
- Already-aborted and successfully-acquired-then-aborted renders release their images; a subsequent successful render recovers normally.
- Malformed Source construction releases Source and Output exactly once.
- Missing optional diagnostic fields do not fail rendering.
- Base, Palette, Material and Scene outputs are bit-identical with tracing on/off for the finite signed/HDR fixture.
- Two dispatcher invocations with the same instance identity overlap at Output acquisition; IDs/threads differ, active count reaches two, and counters clear after exit. Thread-local mock fixtures provide isolated pixel storage; this tests trace concurrency, not Nuke's allocator.
- More than 128 events evict oldest history; retained sequences stay ordered. Disabled tracing adds no history.

[ofx_suite_trace.cpp](../tests/ofx_suite_trace.cpp) remains the focused exception/context-restoration test and is now registered in CTest. The native image-contract test is also run.

Build/check commands:

```sh
cmake --build build --target rendition_bundle_sign rendition_ofx_runtime_tests rendition_ofx_suite_trace_tests rendition_native_tests -j 4
ctest --test-dir build -R 'native_image_contract|ofx_(runtime|suite_trace)_contract' --output-on-failure
```

All three selected CTest contracts passed on the final build. `git diff --check` passed.

The arm64 local bundle is `build/Rendition.ofx.bundle`; its native binary SHA-256 is `1feb820137ff95947221b0916423230b79cc2a969fa8689558823f2c056890f2`. Build signing is local ad-hoc signing, not installation. No Nuke was launched and no installed bundle was changed.

## Runtime decision gate — pending authorization

Use the diagnostic bundle in a restarted Nuke with `RENDITION_SUITE_TRACE=1`, retaining stderr. Begin with connected `Read → Base → Viewer` and one continuous Exposure drag. This runtime step has not been performed.

If Output failure reports abort true, implement centralized clean cancellation at the Render boundary and corresponding early-exit/release tests. Never suppress bad handles, malformed images or genuine non-aborted failures.

If abort is false, compare adjacent successes by ID/time/window/scale/field/GPU/concurrency. If apparently valid, run temporary candidates one variable at a time:

1. Subdivision off, tiles on.
2. Subdivision restored on, tiles off.
3. Both off only if necessary.
4. Acquisition-order experiment only after scheduling is isolated.

Keep the same script/settings/Viewer/interaction; restart between builds. A candidate difference must survive baseline restoration and candidate repetition before permanent declarations or ordering change. Those experimental variants are **not** implemented or run in this pass.

## Actual result

Correlated diagnostic candidate built; source/mock contracts checked. Nuke cause and interactive acceptance remain unresolved. Cancellation handling and scheduling changes remain evidence-gated, not speculatively applied. Next work is a narrow failure capture, not broader research or presets.
