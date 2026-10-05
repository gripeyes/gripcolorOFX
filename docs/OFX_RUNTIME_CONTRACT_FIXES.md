# P0 — Shared OFX runtime contract fixes and captured remaining failure

2026-10-04. **Outcome: stop condition B. Connected-Viewer Exposure dragging remains broken.** This report does not claim interactive acceptance.

## Implemented shared fixes

- Every plugin current-value `paramGetValue` call was removed. Creative/configuration values use `paramGetValueAtTime`; the separate `hostSceneLinear` role now uses the action time, is evaluated once, and is reused for Source/Reference interpretation within that render. Render and IsIdentity use their supplied time. The UI-only family selector also uses a timed read so Create does not use a restricted current-value API. No untimed equivalent is used elsewhere in the native implementation.
- The pinned output-colour query has no time argument. Its disconnected configuration remains evaluated at time 0, using the timed API, preserving its previous time-zero policy.
- The shared Image helper explicitly distinguishes Input and Output. Input `kOfxStatFailed` creates an absent image with no property access or release. Connected unavailable Source is processed as transparent-black data through the existing operator; unavailable Reference is zero, and unavailable Matte has zero coverage. Disconnected required Source retains its explicit validation error. Actual signed/HDR pixels are not repaired or clipped.
- Failed Output fetch, invalid input handle, memory failure and malformed image data remain fatal. No blanket suppression of status 1 was added. Failure-only suite tracing remains available through `RENDITION_SUITE_TRACE=1`.
- No Base/Palette/Material/core equations, parameter ranges, composition, domain options, compatibility versions or Nuke UI source were changed.

## Regression evidence

[tests/ofx_runtime.cpp](../tests/ofx_runtime.cpp) exercises the actual shared action dispatcher against a strict mock host for all 12 effects. Untimed reads fail the mock; requested-time reads, Render, IsIdentity, animated role/interpretation/configuration, unchanged alpha, unavailable Source, unavailable Matte and fatal input/output/image errors are tested. The mock is not evidence of interactive Nuke acceptance.

`ofx_runtime_contract` and `native_image_contract` passed (2/2). The existing [trace harness](../tests/ofx_suite_trace.cpp) was updated for the new timed-role helper and explicit Output access. Build and signing succeeded; the previous installed bundle was backed up under `build/ofx-runtime-fix/previous-installed-bundle`. Only the native bundle was installed; Python presentation files were not rewritten.

## Actual Nuke outcome

A fresh Nuke 17.0v1 arm64 process was launched with `RENDITION_SUITE_TRACE=1`, using `build/ofx-runtime-fix/connected-base.nk`: approved ACES photographic Read (tagged ACES2065-1), custom OCIO project `scene_linear`, Auto Rendition Base, connected Viewer. The initial default image displayed; an identity bypass is not proof of successful nonidentity rendering. The user then continuously dragged Exposure and reported it still broken. The process log captured six Output-fetch failures on three thread identifiers.

| Field | Captured value |
|---|---|
| Suite | `OfxImageEffectSuiteV1` |
| Function | `clipGetImage` |
| Status | `1` / `kOfxStatFailed` |
| Action | `OfxImageEffectActionRender` |
| Effect | `9` / Base |
| Clip | **Output**, not Source/Reference/Matte |
| Time | `1` |
| Source | `src/ofx/plugin.cpp:179` status check; fetch at line 172 |
| Instance | `0xc44d51400` |
| Thread IDs (C++ thread hashes) | `12545305448868200853`, `2095735758851356314`, `9333092811827952160` |
| Same-thread action nesting | `1` |

Evidence: `build/ofx-runtime-fix/nuke-diagnostic.log`, `captured-failure.json`, and `installation.json`. Installed binary SHA-256:

`00884d21b82b5b974545f01e770b771b56b3745cf37871b7fd443bb632050386`

This trace confirms the remaining failing **call**, not why Nuke refuses the output image. It does not establish cancellation, an invalid output request, or a presentation-callback race. Required Output failure was deliberately not swallowed. The original hypothesis about untimed Auto reads is a corrected contract defect but is not the captured remaining failure.

## Gate and stop boundary

Base is not clean. Contrast/Pivot/Saturation/Black, idle/frame/Viewer toggle/undo tests and the subsequent Palette/Material/Advanced continuous-drag checks are not accepted and were not continued after the captured Output failure. UI automation also encountered `AXError.notImplemented`; the user’s Exposure drag supplied the decisive live reproduction.

Stop at the requested **B** boundary with exact shared-call evidence. No Exposure-specific patch, broad re-audit, cancellation fallback or speculative image-fetch recovery was implemented. A subsequent correction must address this confirmed shared Output acquisition path while keeping true output/image corruption fatal. A failure-only abort-state/render-window/scale record would distinguish a cancelled render from a genuinely invalid output request; that further instrumentation is not silently treated as a diagnosis here.
