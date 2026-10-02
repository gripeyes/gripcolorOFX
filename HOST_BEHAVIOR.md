# Host behavior and acceptance

## Nuke 17.0v1 / macOS arm64

Development tests use an isolated terminal process and `OFX_PLUGIN_PATH=build`, not system installation. Exact plugin classes are `OFXorg.gripcolor.rendition.<Effect>_v1`. Nuke plugin enumeration did not list unloaded OFX effects; creating the exact class successfully loaded the bundle.

Verified by the retained smoke report: eight-effect discovery/default float identity, signed/HDR exposure, parameter animation, matrix/neutral invariants, save/reload of model/domain settings, multiframe CPU rendering to 32-bit float EXR.

Nuke point sampling must pass the frame explicitly (`Node.sample(..., frame=nuke.frame())`); changing the root frame alone did not sample the animated plugin at the new time in this headless test.

The extended host test passes interpretation-required errors and recovery, explicit premultiplication, active creative candidates, Inspector, and user-authored Rec.2020/ACEScg OCIO environments. Its retained report, rather than this checklist alone, is the authority for which cases have passed. Color metadata is not inferred from a filename or the project working-space label.

Inspector uses General context with optional Source in Nuke; disconnected procedural modes use a fixed 1920×1080 canonical domain and alpha 1. Input/difference/gamut/nonfinite modes require Source. Procedural sampling uses pixel centers (`100.5` rather than `100`).

Recoverable interpretation errors are cleared after successful semantic revalidation in IsIdentity: Nuke can query identity before its deferred parameter-change notification. No cache flush is required to recover.

GPU rendering is not advertised. The offline Metal validator can synchronize its own command buffers; that does not validate an OFX asynchronous host path. The plugin rejects unexpected GPU-buffer render requests instead of treating GPU pointers as CPU memory.

Normal user installation and main-menu creation of all eight effects were verified interactively; see `docs/reports/nuke-ui-discovery.json`. Native artist panels are visible; independent Tab-search automation remains unverified. The artist graph uses the custom user view Flawed Emulsion 2 (sRGB).

Pending: artist ergonomics/acceptance, complex real-media workloads, full animation/model compatibility matrix, host tile/PAR/proxy edge cases, and actual OFX Metal buffers/queue/error behavior.

## Flame — early Gate C pending

Flame was not found in standard local installation locations. No Flame behavior is claimed verified. Gate C and production Gate H remain pending, even though independent Nuke/research work proceeds.

Run the CPU candidate immediately when access is available:

1. Discover Scene/Tone/Crosstalk under OFX; select explicit working primaries.
2. Exercise Segment FX, Source FX where applicable, Batch and Batch FX; record unsupported contexts explicitly.
3. Render the structured signed/HDR/neutral/reference fixtures as float, checking RGB range and exact alpha behavior.
4. Animate parameters; compare timeline and Batch renders; save/reload and rerender.
5. Test the user's custom OCIO project without implicit input or output conversion.
6. Record actual clip metadata and capabilities; test Auto with known and unknown tags.
7. Verify CPU operation, concurrent/multiframe behavior, image layout, cancellation, and packaging/signing.
8. Keep Metal disabled until actual buffer/queue support and error propagation are verified.

Record Flame version/build, macOS, hardware, project color management, applicable contexts, test results and numerical differences. Host limitations belong here, not in undocumented alternate creative math.

## Nuke Auto / scene_linear role

Auto now uses the current OCIO `scene_linear` role, resolved by `integrations/nuke/rendition_host.py` using Nuke's bundled PyOpenColorIO. A hidden, nonanimated, nonpersistent OFX bridge parameter communicates the supported gamut (Rec.2020/AP1/Rec.709) or explicit unresolved state. Config changes, node creation, project reload and before-render callbacks refresh it. Manual interpretation overrides it; model/domain controls and pixels are never changed by this bridge. Missing/non-OCIO/unsupported/ambiguous roles fail instead of using stale metadata or a default gamut. Other hosts retain recognized clip-metadata Auto behavior.

Role resolution/callback tests pass with real OCIO configs and simulated Nuke callbacks. The rebuilt CPU bundle and existing numerical suites pass. Retesting the new bridge in Nuke itself is currently **pending**: both render-license (`-t`) and interactive-license (`-ti`) terminal attempts failed with Foundry license-server communication / missing token errors. Earlier eight-node UI and host reports remain historical evidence for the previous build, not proof of this new Auto bridge. Frameserver/background-render and live project-change acceptance remain pending host access.

## Targeted 0.2 Inspector retest

License access became available on 2026-10-02. The rebuilt/installed arm64 CPU bundle passes the targeted native Nuke geometry smoke test: modes 11–15 identity remappings, active signed/HDR/zero sources with preserved alpha, animated probe save/reload and float EXR render. Auto also resolves the user's custom Rec.2020 scene_linear role and applies expected Scene exposure. See `docs/reports/0.2-nuke-inspector-geometry.json` (22 checks). This supersedes the license blocker for these cases, not every pending host workload. Background frameserver and all unknown-role/error/config-change paths remain separately unaccepted in the real host.

A detached-node shutdown notification exposed a startup callback exception; the callback now returns only for that detached-node ValueError, with a regression test. New Inspector modes are CPU-only and analyze a configured single family, not upstream node internals. The menu links the local Inspector Lab report. Existing Nuke sessions must reload the bundle/menu to access new controls; no running session was forcibly restarted.

## Artist Primaries / Tonal Colour 0.2.1

Primaries appends a ninth native effect without changing the original eight IDs/models. Interactive main-menu creation, visibility of 33 controls in all five artist groups, shadow-tint editing and Save Comp As pass; see `docs/reports/0.2.1-primaries-ui.json`. Initially collapsed artist groups did not reliably expose children (MIDTONES as well as slash-containing labels). New group identifiers are normalized and artist groups open initially; this is an exposure workaround, not proof of the host root cause or correct collapse/Expert/custom expansion. Those UI paths remain pending.

Native Nuke CPU smoke tests pass 10 checks: exact default identity, seven reference sample comparisons, animated saved-state reload and two-frame float EXR rendering (`docs/reports/0.2.1-nuke-primaries.json`). These are numerical tests, not artist acceptance. The generated seven-recipe graph uses explicit Rec.2020 fixtures and the external user view; an interactive Open attempt did not visibly replace the current test window, so its GUI loading is not claimed verified. Primaries has no Metal implementation or Flame validation.
