# Full Spectral Reference completion — Density and Strip

Decision: **keep the current production Density and Strip models**. Existing equations, IDs, parameters and saved-project meanings are unchanged. The matched full integration does not expose an important approximation deficit. Alternative reconstructions change the grade, but no useful behavior missing from compact v1 has been established. No v2 or per-pixel spectral production runtime is justified by this pass.

Broad spectral development stops here. Further spectral work requires a concrete artist-observed or numerical failure. The next phase is Artist Presets / Recipes using Base → Palette → Material and the approved visual direction.

## Scope and audit

The existing 360–830 nm/1 nm path and 432 baseline comparisons were retained. New completion coverage contains **8000** sweep rows, 160 reconstruction comparisons, eight Strip interaction configurations on held-out data and 200 physical-reference records. Run `PYTHONPATH=build:. .venv/bin/python -m research.spectral_completion` followed by `-m research.spectral_completion_report`. The pinned existing Colour/SciPy environment and shared CPU evaluator are required. Reports are generated from scene-linear pre-DRT values, never viewed pixels.

| Requirement | Baseline | Final | Evidence / boundary |
|---|---|---|---|
| 1 nm integration, observer and original-gamut return | satisfied | satisfied | Existing Lab/FullReference retained; CIE integration tests retained. Completion numerical sweeps are Rec.2020; AP1/709 use the baseline path. |
| Materially different RGB reconstruction assumptions | satisfied | satisfied | Three existing methods retained; nonlinear sigmoid/D65 pilot adds a distinct bounded-reflectance assumption, no optimized rgb2spec implementation claimed. |
| Reconstruction reproduction, shape, saturation, boundary, exposure and conditioning comparisons | partially satisfied | satisfied | 160 family/chroma/method reconstruction records, shape plots, matrix/fit conditioning and signed-boundary refinement. |
| Jakob/Hanika-style investigation | missing | satisfied | Targeted paper-family pilot only; retained offline because bounded D65 spectral shapes provide a distinct metamer sensitivity reference. Poorly conditioned extreme fits are explicitly qualified. |
| Production use of Jakob/Hanika optimized tables | intentionally deferred | intentionally deferred | No measured production need; no table/code import or runtime plugin change. |
| KM versus Beer-Lambert versus Neugebauer/Yule-Nielsen semantics | partially satisfied | satisfied | 200 synthetic physical-reference records, distinct classes and appearance semantics below. |
| Density ten-family exposure/chroma/depth trajectories | partially satisfied | satisfied | 4000 Density rows; RGB, hue, chroma, XYZ/Y and exposure plots. |
| Strip full separation, interaction, leakage, recombination and anchors | partially satisfied | satisfied | 4000 Strip rows plus eight control configurations; independent 1 nm integration matches compact record contract. |
| Strip versus matrix and matrix-plus-curves baselines | missing | satisfied | 180 training / 90 held-out colours, unrestricted matrix followed by independent cubic channel curves; image examples included. |
| Signed physical component, residual and HDR decomposition | partially satisfied | satisfied | Extraction formulas, zero/mixed-sign/HDR probes, 2x exposure and boundary refinement recorded; residual is algebraic, not physical. |
| Runtime ratio and reconstruction-method variation | missing | satisfied | Same-machine 64-pixel batches, cold/warm timings; Python/C++ implementation overhead explicitly included. |
| Consolidated scene-linear report and viewed examples | missing | satisfied | This report + HTML environment + EXRs; PNGs alone use external Flawed Emulsion 2. |
| Useful artist behavior missing from compact verified by artist | missing | partially satisfied | Targeted visual inspection and model differences recorded; small examples do not establish artist superiority or user acceptance. |
| Full-resolution authored-shot/general artist acceptance | intentionally deferred | intentionally deferred | Approved sample previews are deliberately small; next artist recipe phase uses Base/Palette/Material, with failure-driven follow-up only. |
| Density v2 / Strip v2 fitting or per-pixel runtime replacement | intentionally deferred | intentionally deferred | No established useful missing behavior; retaining production v1 equations/IDs/parameters is the recommendation. |
| All expert selectors, custom gamuts and arbitrary production parameters matched by oracle | partially satisfied | partially satisfied | Record mode/custom matrix/palette/contributions/weights added; custom selector/domain/config combinations not exhaustively matched. |
| Measured pigments/dyes, fluorescence, finite-layer scattering or film stocks | intentionally deferred | intentionally deferred | Outside completion scope; synthetic curves and reference classes are not universal or film identities. |
| Explicit final recommendations, reproducibility and stop | missing | satisfied | Keep current Density and Strip; no production source changes. Broad spectral expansion stops here. |

## Reconstruction and the sigmoid pilot

**RGB-to-spectrum reconstruction produces plausible metamers. It does not recover the original physical spectrum.** A nonzero residual means the spectrum alone is not a metamer; only spectrum plus algebraic residual reproduces the stimulus. This distinction also applies to the three-basis method.

Matched three-Gaussian, eight-basis nonnegative least squares and Smits-derived assumptions remain. The new pilot independently implements the [Jakob/Hanika sigmoid-quadratic function family](https://rgl.epfl.ch/publications/Jakob2019Spectral): `f = (1 + z/sqrt(1+z²))/2`, `z = c0 t² + c1 t + c2`, `t = (λ−595)/235`. It fits three coefficients directly with SciPy least squares using three fixed starts. It does **not** import optimized tables/code, reproduce canonical rgb2spec performance, or inherit its gamut guarantees.

Our scene adapter uses D65 `I` normalized to unit integrated Y and `scale = 2 max(abs(XYZ / whiteXYZ))`. Fit the bounded reflectance-like shape to `XYZ/scale`, construct nonnegative radiance `scale I f`, then define the signed residual exactly. This normalized target is invariant to positive exposure scale. Arbitrary signed/wide-gamut stimuli may not be representable by bounded D65 reflectance; that limitation is visible in the residual and Jacobian diagnostics. Multiple fit minima, rank-deficient/saturated solutions and finite iteration limits prevent treating the pilot as an authoritative reconstruction for every input. 1 fitted cases had deficient Jacobian rank. Cache stores solutions only; cold timings include solving.

The pilot is retained as an **offline, qualified metamer-sensitivity reference**, because its bounded nonlinear illuminated shape differs materially from additive emission bases. It is not generally smoother by the discrete curvature metric and is not a replacement for existing methods. Extreme signed cases yielding smaller residuals do not establish physical validity.

| Reconstruction | Median spectrum-only relative XYZ error | Max | Median normalized second-difference norm |
|---|---|---|---|
| compact_basis | 0.0471 | 1.69 | 0.000353 |
| nnls_residual | 9.98e-16 | 0.698 | 0.000846 |
| smits_residual | 0.0564 | 0.73 | 0.00109 |
| sigmoid_d65_pilot | 3.17e-14 | 0.519 | 0.00399 |

All residual-recombined XYZ errors are recorded independently. The residual makes exact reconstruction largely an algebraic identity; it must not be presented as proof of accurate physical reconstruction. Shape curvature is a descriptive metric, not artist quality. The eight-basis mapping has five unconstrained null-space dimensions before nonnegative constraints; its rectangular condition number does not imply unique coefficients. Matrix condition numbers and solver Jacobian ranks/conditions are in `summary.json`; singular conditions are `null` with rank, not nonfinite JSON.

## Physical reference classes

**A. Kubelka–Munk:** synthetic infinite-thickness reflective/scattering pigment reference. `a=K/S`, `R∞=1/(1+a+sqrt(a²+2a))`. Concentration changes K; S is positive. No finite-layer/substrate, fluorescence or measured pigment identity claim.

**B. Beer–Lambert / optical density:** synthetic transmissive dye reference, `T=10^(−D(λ))`. Nonnegative optical density and explicitly mixed absorption/leakage spectra; not the same physics as scattering pigment. Production's artistic Density units are not physical optical-density units.

**C. Neugebauer / Yule–Nielsen:** eight synthetic overprint primaries with independent coverage weights `a_i`, `R=(Σ a_i R_i^(1/n))^n`; n=1 is Neugebauer, n=2 is the illustrative Yule–Nielsen variant. Synthetic overprint primaries use our dye attenuation as a reflectance surrogate over a white substrate. These D65-lit outputs are **appearance-referred**. They are separate reproduction references, not hidden scene grading or film simulation.

Full scene-reference Density multiplies a reconstructed nonnegative radiance component by KM attenuation and restores its residual. That is an authored, material-informed **scene-compatible attenuation operator**, not a complete physical object/print appearance. Strip likewise uses dye attenuation, separation/leakage and recombination. The appearance-reference Neugebauer values cannot be subtracted from arbitrary source scene RGB and called production error; they are shown separately to identify conceptual differences.

## Density and Strip results

Ten families: red, yellow, green, cyan, blue, magenta, skin, olive, bronze/ochre and deep chromatic shadows. Chroma factors 0/.5/1/1.5, exposure −10/−5/0/+5/+10 stops, amounts 0/.25/.5/.75/1. Source, reference and production scene RGB, XYZ, Y, signed-Oklab chroma and hue are in each sweep record. Hue is undefined at exact neutral; neutral diagnostics use axis/magnitude rather than interpreting neutral hue.

The matched 1 nm path's maximum scale-relative scene-RGB error is **1.93084e-05**. Eight Strip control cases have maximum absolute RGB error **1.46355e-05** on the tested unit-scale held-out colours. The latter tests three/two/custom records, leakage, palette shaping, contributions, weights, density coupling and red anchoring. Full integration followed by projection/recombination is intentional: it reproduces the existing record contract, rather than inventing an incompatible recombination model. Alternative spectra use three overlapping broad spectral records with Y-calibrated coefficients and retained residuals; they are not claimed identical physical records.

Simple baselines use 180 deterministic training and 90 held-out colours: unrestricted RGB matrix, then independently fitted cubic channel curves. Curves are unconstrained and may overshoot outside training coverage; no clipping hides this. Some alternative oracles are closer to these simple baselines than to compact v1. That shows different authored relationships, not superiority. Nonzero matrix residual does not prove that additional spectral complexity deserves an artist control.

## Signed, zero and HDR semantics

Three-basis extraction: `u=B⁻¹ XYZ`, `positive_i=.5*(u_i+sqrt(u_i²+(.001||u||)²))`, physical base `S(λ)=Σ positive_i basis_i(λ)`, residual `r=XYZ−∫S CMF`. Eight-basis NNLS uses max-absolute-channel scale with explicit zero handling and solves normalized XYZ. Smits uses an explicitly nonnegative Rec.709 **physical component**, radiometric calibration and an exact XYZ residual; removed signed data are retained, not discarded. The sigmoid adapter is defined above.

After material operation, output is `∫S_processed CMF + r`; residual is signed algebraic VFX information and has **no assigned physical meaning**. Positive radiance components can be physical energy; arbitrary synthetic reconstructions do not establish an actual material/spectrum. Negative Density reverses an attenuation displacement algebraically and is not physical gain from negative concentration. Signed Oklab calculations are our algebraic coordinate continuation, not a claim of perceptual validity for negative light.

Exact-zero spectra/residuals remain zero. Mixed-sign and signed-ray transitions are finite. Max/norm scale is homogeneous for positive exposure; twofold exposure doubles reconstructed spectrum and residual. Strip's measured scale error is near machine precision; Density is deliberately exposure-conditioned by its protection weighting. Default neutrality shows small leakage from published white/model constants; magnitude and axis drift are reported separately and not claimed exact.

The saturated signed boundary has large local gains in **both production and full reference**. `targets-and-boundaries.png` and `boundary_convergence` refine the same −.05…+.05 R path at G=.001, B=1, using 81/161/321 samples. This does not certify differentiability or compositing robustness everywhere. Strong conditioning is a documented limitation; it is not silently repaired, nor evidence that a larger spectral runtime solves it.

## Runtime

Same-machine macOS-26.5.2-arm64-arm-64bit-Mach-O; 64-pixel batches, median seven compact calls / three warm reference calls. Cold first pass includes reconstruction solves. Ratios include Python loops/Colour/SciPy versus compiled batched C++ and are **not** a hardware-normalized cost of spectral arithmetic alone. They justify keeping the oracle offline; no HD/4K/8K real-time inference.

| Effect | Method | Compact ms | Cold oracle ms | Warm oracle ms | Cold / warm ratio |
|---|---|---|---|---|---|
| Density | compact_basis | 0.036 | 12.40 | 12.26 | 341× / 337× |
| Density | nnls_residual | 0.036 | 13.68 | 13.68 | 377× / 377× |
| Density | smits_residual | 0.036 | 53.89 | 53.82 | 1483× / 1481× |
| Density | sigmoid_d65_pilot | 0.036 | 271.48 | 11.64 | 7472× / 320× |
| Strip | compact_basis | 0.040 | 13.04 | 13.10 | 328× / 330× |
| Strip | nnls_residual | 0.040 | 15.87 | 15.83 | 399× / 398× |
| Strip | smits_residual | 0.040 | 57.68 | 56.72 | 1451× / 1427× |
| Strip | sigmoid_d65_pilot | 0.040 | 274.32 | 13.89 | 6901× / 349× |

## Artist targets and visual inspection

Four comparison sheets use approved ACES portrait and interior samples, explicit Linear Rec.2020 reduced fixtures, and external Flawed Emulsion 2/sRGB. Every fifteenth fixture pixel is evaluated; nearest enlargement makes sampling visible. EXRs contain pre-DRT float results. These are colour-behavior previews, not full-resolution skin/structure acceptance. Matrix-plus-curves overshoot is visible in the saturated interior, limiting that baseline outside its fitted distribution.

| Target | Missing useful compact behavior established? | Observation / decision |
|---|---|---|
| Bronze / ochre skin | No, not established | Alternative reconstructions shift attenuation/hue and brightness; the matched oracle is visually coincident with compact. No demonstrated controllability/skin advantage. |
| Olive contamination | No, not established | Different metamer shapes alter olive trajectories. Coherent olive authorship remains available through Palette/Material; spectral difference alone does not establish a missing control. |
| Cyan → blue-black | No, not established | Existing trajectories deepen cyan; alternative curves change depth but also darken. No evidence for a better exposure grammar. |
| Dense low-key skin | No, not established | All material paths attenuate the physical component. Default Density keeps chroma magnitude while changing Y; this is not proof of deeper colour without ordinary darkening. |
| Protected red/yellow accents | No, not established | Red/skin anchor tested; yellow-specific anchor not introduced. No artist-observed yellow failure justifies adding a new algorithm. |
| Dirty warm relationships | No, not established | Existing front ends plus chosen spectral basis already produce this direction. Differences require artist evaluation, not automatic preference. |
| Deep chromatic blacks | No, not established | Signed residual fraction and high conditioning can dominate. No tested alternative consistently resolves these limits. |

These are conservative engineering/visual-review conclusions, **not user artist acceptance** and not proof that no future useful difference exists. No target has a validated YES, so no speculative analytic/LUT v2 was fitted. If an artist later identifies a precise desirable trajectory that compact cannot reproduce, fit that behavior under an explicit new model version and compare held-out error/speed; otherwise retain v1.

## Plots and viewed examples

![Reconstruction shapes](../build/spectral-completion/reconstruction-shapes.png)

![Density hue/XYZ depth trajectories](../build/spectral-completion/density-hue-xyz.png)

![Strip hue/XYZ depth trajectories](../build/spectral-completion/strip-hue-xyz.png)

![Artist-target trajectories and signed-boundary refinement](../build/spectral-completion/targets-and-boundaries.png)

![Density, approved portrait sample](../build/spectral-completion/density-0005.png)

![Strip, approved portrait sample](../build/spectral-completion/strip-0005.png)

![Density, approved saturated interior](../build/spectral-completion/density-0060.png)

![Strip, approved saturated interior](../build/spectral-completion/strip-0060.png)

## Final boundary

Density: **keep current production model**. Strip: **keep current production model**. Artist/material superiority remains unresolved; this does not justify changing saved projects. Full Spectral remains an offline oracle. General spectral expansion, extra reconstruction catalogues and film-process development stop. Remaining explicitly deferred work is opened only by a concrete observed failure.
