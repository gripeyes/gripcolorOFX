# Gate status — development candidate, 2026-10-02

| Gate | Current evidence | Status / remaining acceptance |
|---|---|---|
| A: Interpretation/core | Explicit Auto failure, manual authority, Colour matrix/CAT checks, float reference tests | Numerical core implemented; broader metadata/host edge cases remain |
| B: Look domains | Six scalar comparisons, float round trips, OCIO tangent-toe reference, plots | ACEScct scalar selected for initial candidates; expanded Tone/Channel Crossover controllability study remains |
| C: Scene/Tone/Crosstalk | Working CPU nodes; Nuke discovery/render/animation/reload reports | **Pending Flame smoke test** and full host acceptance |
| D: Volume | Six-model coordinate comparison, signed Oklab candidate, four overlap models, permutation/cross-gamut tests | Working candidate; wider adapter/overlap benchmark and artist/media acceptance remain |
| E: Spectral infrastructure | 1 nm integration, four illuminants, two reconstructions/three scales, KM/dye/Neugebauer experiments, signed residual tests | Working oracle; measured materials, wider chromatic/native reconstruction comparisons and real compositing acceptance remain |
| F: Density | Compact KM-basis radiance-relative candidate; held-out response errors, continuity/exposure/non-matrix tests | **Research candidate**, not production accepted; validate desired material families and real imagery |
| G: Strip | Compact dye-basis candidate with record/leakage/palette/anchors; comparison and stability tests | **Research candidate**, not production accepted; historical/reference and real-image validation remain |
| H: Production | Local signed CPU bundle, shared-equation offline Metal kernels, tests and benchmark tools | **Pending** Flame, OFX Metal host integration, final model/artist/media acceptance and distribution signing |

No production gate is inferred solely from passing unit tests. The entire bundle is labeled Research. Optional runtime spectral processing, tetra/cone models, overlays and CLF/CTF export are not implemented or implied by the candidate.

## First-class artist gate

Normal eight-node Nuke UI exposure is verified. M15–M17 comparisons and approved ACES photographic/CG fixtures are available in the artist build. The user accepts current eight-node basic usability. Aggressive-range feedback/time/reuse and meaningful superiority over simple baselines remain pending, particularly for Density/Strip. See `FINAL_ADDENDUM_AUDIT.md` and `ARTIST_ACCEPTANCE.md`. Flame/host Metal do not block this evaluation. M18 stops broad literature expansion; future work is driven by recorded failures.

The targeted 0.2 phase implements differential Inspector modes, HK appearance experiments, fairer aggressive baselines, offline palette/structure analysis and experimental soft guide exports. Nuke CPU mode/animation/reload/render smoke checks pass; creative equations are unchanged. See `DEEP_VALIDATION_0_2.md`. This is ongoing development, not an acceptance freeze.

## Dedicated Artist Primaries / Tonal Colour phase

Option B adds a versioned ninth CPU prototype with shared core interpretation/CAT/alpha infrastructure and unchanged original operator equations. All requested master/toe/mid/shoulder/range controls are present. Six focused independent tests and 10 native Nuke checks pass; interactive menu creation/control exposure/edit/save passes. Seven task recipes on three approved frames are prepared for human review. See `ARTIST_PRIMARIES.md` and retained `0.2.1-*` reports.

**Artist/prototype gate pending:** useful speed/feel, human preferences, reliable group collapse/Expert/custom expansion, wider real-media behavior and a targeted remedy for aggressive narrow zonal tone reversal. No full monotonicity, production or Metal parity claim applies to this new model. Flame and host Metal remain pending while Nuke artist evaluation continues.

## Rendition 0.3 architecture consolidation

Base scalar/ray tone reversal is constrained by positive-slope construction, with original Primaries v1 untouched. Palette/Material compact front ends reuse existing engines; full 1 nm spectral reference and matte-driven exposure are implemented on CPU. Native Nuke sample translation, alpha/animation/reload/render checks pass. Artist control contracts and version selectors are explicit.

**Architecture freeze pending** human predictability/time/reuse, Material M17 advantage and complete Pigment/SpektraFilm workflow evidence. No invented artist acceptance. Signed/HDR adaptations, numerical conditioning and wider image/host edges remain documented. Active SpektraFilm, host Metal and Flame do not block CPU evaluation. See `ARTIST_ARCHITECTURE_0_3.md` and `PIPELINE_CONTRACT.md`.

## Focused Full Spectral completion

The existing 0.3 baseline remains intact. The completion audit, 8,000 sweep comparisons, reconstruction conditioning/shape metrics, Strip held-out baselines, full-integrated record-control comparisons, signed-boundary refinements, runtime ratios and reduced approved-sample examples are delivered in `docs/FULL_SPECTRAL_COMPLETION.md` and `build/spectral-completion/index.html`. Numerical completion is not physical material truth or artist acceptance. Keep current production Density and Strip; no v2 or runtime spectral replacement justified. Artist acceptance and deliberately deferred expert configurations remain explicit. Broad spectral expansion is stopped; reopen only for a concrete numerical or artist-observed failure. Next phase: Base → Palette → Material Artist Presets / Recipes.

## Rendition 0.31 control restoration

Base remains v1. Palette/Material preserve model choice index 0 and append explicit model index 1 for restored Expert state. All original effect/parameter IDs, ordering and defaults are retained; new controls append. Families, continuous hue/channel trajectories, constrained matrices and detailed compact Density/Strip controls are reachable through native OFX parameters and Nuke links. Numerical response audit covers all 30 Main controls and the full artist parameter inventory; native animation/reload and exact neutral-expert compatibility tests pass.

**Recipe/control freeze remains pending** comprehensive perceptual direction/redundancy/continuity judgments, target-language artist acceptance and packaged UI screenshot evidence. The observed subtle Main palette mappings and locally uneven selected Material-depth example are recorded; no arbitrary gain or production-model replacement was made. See `ARTIST_CONTROL_RESTORATION_0_31.md`. Broad spectral research remains closed. Flame/host Metal remain separate pending host gates.
