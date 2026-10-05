# Nuke 17 Output acquisition correction — 2026-10-05

## Result and scope

The installed shared adapter now acquires and validates Output **before** evaluating timed parameters and constructing the immutable render snapshot. All 12 effects use this path. Pixel equations, model generations, defaults, ranges, presentation, interpretation semantics and alpha handling are unchanged. Host frame subdivision and tiles retain their original enabled declarations. No Pigment lifecycle extraction.

This is an evidence-backed acquisition-order correction, not a claim that cancellation explained the reported failure. Cancellation handling remains separately required and tested; non-aborted failures remain fatal.

## Captured failure

The actual installed cancellation-aware binary (`9c285cefe96f6a27fd7aba5be0a0beadfa40c4d46a3d881fd7334d9d7f24aa22`) failed during real native Exposure dragging in the user's connected Read → Base → Viewer graph.

- Suite/function: `OfxImageEffectSuiteV1::clipGetImage(Output)`.
- Action: `OfxImageEffectActionRender`; status `kOfxStatFailed` (1).
- Render 51 succeeded with window `(0,0,1920,199)`.
- Render 52 failed with window `(0,199,1920,398)`.
- Same time 1, scale `(1,1)`, field `OfxFieldNone`; active-render count 1.
- Abort immediately before/after failure: **0 / 0**.
- GPU properties unavailable (status 3); no evidence of GPU rendering.
- Roughly 107 ms elapsed between render entry and Output acquisition.

Evidence: `build/scheduling-proof/baseline-live-failure.log`. The baseline failure check was at `plugin.cpp:206` in that binary; later source insertions move the line. The actual failing function remains the Image constructor's checked `clipGetImage` call.

## Controlled experiments

All controlled runs restarted the same ordinary Nuke 17.0v1 edition, restored the same saved temporary graph, used the same source/OCIO/Viewer settings and applied the same 96 asynchronous parameter updates at a 150 ms timer interval. They exercised Exposure, Contrast, Pivot, Saturation and Black (`blackStops`). These are **background connected-Viewer renders**, not synchronous pixel samples. Error-state samples are supplementary; suite-trace counts are the primary evidence.

The source is the user's `rocklike-init.arnoldrendersettings.0001.exr` (1920×2400). Auto interpretation remains selected. The reproduction graph uses built-in ACES 2.0 SDR viewing; quantitative color/look evaluation was not performed. The first original native-drag capture was NukeX; the controlled comparison uses ordinary Nuke consistently on both sides.

| Run | Host subdivision | Tiles | Acquisition order | Updates | Suite failures |
|---|---:|---:|---|---:|---:|
| Baseline repeat | On | On | Snapshot → Output | 96 | 29 |
| Experiment 1 repeat | Off | On | Snapshot → Output | 96 | 11 |
| Experiment 2 | On | Off | Snapshot → Output | 96 | 27 |
| Experiment 3 | Off | Off | Snapshot → Output | 96 | 26 |
| Output-first candidate | On | On | Output → snapshot | 96 | 0 |
| Restore old order | On | On | Snapshot → Output | 96 | 18 |
| Final installed repeat | On | On | Output → snapshot | 96 | 0 |

The first frame-off trial appeared clean (three native drags plus 80 asynchronous updates). Its repeat failed; it was explicitly rejected. Neither disabling tiles nor disabling both declarations fixed the issue. No scheduling declaration has been permanently changed.

Retained per-run logs, JSON outcomes, exact signed bundles, the unmodified graph backup and the workload script are under `build/scheduling-proof/`. Logs buffer successful neighboring acquisitions and dump only on failure. Timer results do not imply continuous mouse-drag acceptance.

## Confirmed change

Shared [render](../src/ofx/plugin.cpp) now performs:

```text
Render action time / cancellation / GPU-buffer guard
→ render window
→ Output acquisition + RAII ownership / validation
→ timed parameter evaluation / Auto role / immutable snapshot
→ Source / optional Reference or Matte
→ existing processing and abort polling
→ image release
```

Previously snapshot construction preceded Output. No timed evaluation or mathematical operation was removed, retuned or moved into presentation state. A snapshot failure now releases the already-owned Output handle once. Nothing catches or ignores a genuine non-aborted Output failure.

The causal evidence establishes **acquisition-order dependence in this Nuke workload**. It does not prove the internals of Nuke's allocator or that OpenFX forbids snapshot-first ordering. Parameter calls, snapshot computation or time spent before acquisition may contribute; they have not been individually isolated and are not claimed proven root causes.

## Shared-path and interaction checks

On the final installed build:

- Two independent 96-update Output-first runs: zero suite failures.
- Palette Separation, Material Depth and Advanced Scene Exposure: 16 connected-Viewer updates each (48 total), zero observed node errors and zero suite failures.
- Native Properties numeric Exposure edit, node Undo/Redo, frame 1 → 2 → 1: no suite failure.
- Original grading settings and Viewer connection restored; temporary representative nodes removed.

Full final-build continuous mouse dragging remains unverified: the computer-use service repeatedly returned `noWindowsAvailable` for pointer operations despite working AX reads, numeric edits and screenshots. The early native drag reproduction is real; the final asynchronous Viewer comparisons are also real, but neither is presented as a completed final mouse acceptance gate. This tooling limitation is not a captured plugin error.

## Regression/build checks

[ofx_runtime.cpp](../tests/ofx_runtime.cpp) now asserts Output acquisition precedes the first timed read in Render for every effect; IsIdentity retains time-correct evaluation without image acquisition. Snapshot parameter failure must release Output exactly once and report a processing error. Existing tests retain genuine Output failure, unavailable input, pre/post-fetch cancellation, processing cancellation, malformed properties, exact releases, recovery, missing optional diagnostics, correlated concurrent history and trace/no-trace output equality.

Passed:

```text
native_image_contract
ofx_runtime_contract
ofx_suite_trace_contract
```

`git diff --check` and installed deep/strict code-signature verification passed.

Final installed binary SHA-256:
`ae8e9aaa5260d47e4153831527f651acefc4583a49b1139e2fb707f432112d0a`

Installed bundle: `/Users/j7s/Library/OFX/Plugins/Rendition.ofx.bundle`.

## Contract references

- Pinned repository [OpenFX image-effect header](../third_party/openfx/ofxImageEffect.h): host frame threading and image acquisition contracts.
- [OpenFX rendering specification](https://openfx.readthedocs.io/en/main/Reference/ofxRendering.html): render windows, image acquisition and interruption.
- [Official Basic example](https://github.com/AcademySoftwareFoundation/openfx/blob/main/Examples/Basic/basic.cpp): failed image fetch is treated as interruption only when abort is reported.
- [Pigment comparison](RENDITION_VS_PIGMENT_OFX_RENDER_AUDIT.md): independent early Output acquisition; no blanket reuse/refactor.
- [Cancellation correction](OFX_RENDER_CANCELLATION_FIX.md): cancellation is distinct from the now-captured abort-false failure.
