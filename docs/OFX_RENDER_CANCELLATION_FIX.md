# Shared OFX render cancellation correction

2026-10-05. This implements the cancellation correction following the request to build an actual fix. It supersedes the diagnostic-only behavior described in [OFX_RENDER_LIFECYCLE_DIAGNOSTICS.md](OFX_RENDER_LIFECYCLE_DIAGNOSTICS.md). The cause of the earlier Nuke failure is still not proven; this build corrects the documented interrupted-render case without hiding non-aborted failures.

## Behavior changed

Shared [plugin.cpp](../src/ofx/plugin.cpp) now uses an internal `RenderCancelled` outcome caught separately at the OFX action boundary. It returns `kOfxStatOK` without posting or clearing persistent processing messages.

- Abort is checked at render entry, before each image acquisition, immediately after any failed acquisition, and after successful acquisition before image-property processing.
- `clipGetImage` status 1 with abort true terminates the interrupted render cleanly. This covers Output, Source, Reference and Matte. Status 1 with abort false remains fatal for Output and retains existing absent-input semantics for inputs.
- Bad-handle, memory and other suite errors remain fatal even if the host concurrently reports abort. No blanket suite-exception catch was added.
- Processing polls once per row and at 256-pixel intervals within rows. A shared atomic cancellation flag stops fellow workers. After workers return, real processing exceptions take precedence; cancellation exits before persistent-message handling.
- Successful image acquisitions are owned before cancellation checks. Constructor cleanup releases handles on cancellation or validation failure; RAII releases images already acquired by the enclosing render. Failed fetches have no owned image to release. A success status with a null handle remains an explicit error.
- The trace uses the same abort samples as the lifecycle decision and records cancelled exits distinctly. Genuine failure dumps still include correlated neighboring renders.

Before this correction, status 1 from Output became a suite exception even during an aborted render. Cancellation was polled only in the pixel loop, which returned normally and continued to message handling. The new policy follows the official OpenFX Basic example's interrupted-render distinction.

## Preserved

No change to colour mathematics, artist controls/ranges, domains, composition, IDs, models, UI, acquisition order or scheduling declarations. Default host subdivision and tiles remain enabled. Historical and artist nodes use the same corrected adapter. No Pigment refactor, spectral work, recipes or artistic retuning.

## Regression results

All three selected contracts passed on the final build:

- `native_image_contract`
- `ofx_runtime_contract`
- `ofx_suite_trace_contract`

The runtime tests cover every registered effect for already-aborted renders (zero fetches), failed Output acquisition followed by abort, fatal non-aborted Output failure, repeated cancellation and recovery, successful acquisition followed by abort, and cancellation during processing. Cancelled renders post/clear no persistent messages. Exact release tests also cover malformed images and interrupted input acquisition. Bad-handle/memory failures remain visible even when abort becomes true. Existing timed-parameter, absent-input, concurrency, bounded-history and signed/HDR output checks remain passing.

The concurrency test filters correlation events by sequence as well as instance address; stack-address reuse must not be mistaken for the same live render instance. Mock tests establish contract behavior, not connected-Viewer Nuke acceptance.

## Build and installation

Built and ad-hoc signed arm64 `build/Rendition.ofx.bundle`. Installed into:

`/Users/j7s/Library/OFX/Plugins/Rendition.ofx.bundle`

Installed binary SHA-256:

`9c285cefe96f6a27fd7aba5be0a0beadfa40c4d46a3d881fd7334d9d7f24aa22`

Previous bundle preserved at:

`build/render-cancellation-fix/a4f12e8b-ad7a-4686-8ac9-cf3ae0cadd55/previous-installed-bundle`

Installation metadata: `build/render-cancellation-fix/latest.json`. Installed and built binaries were verified identical; signature verified before replacement. `git diff --check` passed.

Nuke was not launched, restarted or otherwise controlled. An already-running Nuke process retains the previous loaded binary: a full restart is required. Actual connected-Viewer acceptance remains pending.

## Remaining runtime gate

After restart, test connected Base Exposure dragging first. If the error remains, the installed build retains `RENDITION_SUITE_TRACE=1` support and will identify genuine non-aborted failures with correlation/window/scale/field/GPU/concurrency context. Only then run the agreed scheduling experiments one variable at a time; none has been applied permanently or run here.
