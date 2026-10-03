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

## 0.3 artist architecture

Native CPU Nuke tests cover twelve IDs, reference samples, original/new model choices and animation reload, Base optional alpha Matte (half coverage -> half stop), two-frame float rendering, tagged AP0 source Read with Raw disabled, Nuke OCIO-to-scene_linear and downstream Auto identity. See `docs/reports/0.3-nuke-architecture.json`. Old equations/IDs remain, with new artist IDs appended and deep effects grouped Advanced. GUI menu acceptance is separately recorded, not inferred from scripts.

Two installed SpektraFilm v0.2 plugins and Pigment effects were discovered through their native interfaces. Narrow constant probes show full Print simulation defaults produce display output; diffuse defaults approximately preserve tested signed/HDR values. Active/spatial/temporal semantics and appearance comparisons remain pending; see `docs/PIPELINE_CONTRACT.md`.


### Nuke 0.3 presentation verification

Fresh Nuke 17.0v1 interactive tests pass normal creation of Base, Palette, Material and Inspector from Rendition; the nine historical entries remain in Advanced. Base's 13 main controls, Advanced tonal controls (edited shadow hue) and five Dodge/Burn controls are accessible. Palette's nine controls and six family directions and Material's eight controls are visible. The native expandable-group issue persists; the Nuke adapter presents standard tabs with self-relative links to the original parameters instead. Native write-through, node rename and saved reload pass without duplicate processing state. See `docs/reports/0.3-nuke-ui.json` and the 21 native checks in `docs/reports/0.3-nuke-architecture.json`.

The interactively created test was saved as `UI-created-artist.nk`. Opening the sample graph did not visibly replace that window, so interactive sample graph loading is not claimed accepted. Its native Read conversion and Auto identity tests pass. This is an artist candidate; human predictability, speed and cross-content acceptance remain open.

## 0.31 Nuke control restoration, 2026-10-03

Interactive Rendition menu creation verified Base, Palette and Material. Restored tabs link to their real OFX knobs; they do not store separate grading values. Palette has qualified six-family controls, continuous Trajectory and explicit Channel Trajectory, and M11–M33 Crosstalk Matrix. Material exposes Density selectors and compact Strip records/contributions/recombination. Base Advanced retains tonal colour/ranges and Dodge/Burn. New Palette/Material expert processing requires explicit v2 opt-in; old graphs remain v1.

The native restoration script covers rename/copy/paste, all creative-parameter animation/save/reload, linked knob writes, six look domains on four historical operators and choice animation. Serialization of deliberately mixed extreme settings is not artist/render acceptance. UI screenshots were inspected in the conversation; exported screenshot files and comprehensive human response acceptance remain pending. Host Metal/Flame status is unchanged.

A subsequent interactive check found the same native OFX disclosure limitation on historical Tone: Expert checked open, but its encoding remained invisible. The Nuke adapter now adds real-knob Expert/Advanced links for Scene, Tone, Crossover and Crosstalk as well. This restores domain/channel/matrix access without changing effect IDs, parameter IDs, persisted native values or historical processing.
