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

Normal eight-node Nuke UI exposure is verified. M15–M17 comparisons and approved ACES photographic/CG fixtures are available in the artist build. Human feedback/time/reuse and meaningful superiority over simple baselines remain pending, particularly for Density/Strip. See `FINAL_ADDENDUM_AUDIT.md` and `ARTIST_ACCEPTANCE.md`. Flame/host Metal do not block this evaluation. M18 stops broad literature expansion; future work is driven by recorded failures.
