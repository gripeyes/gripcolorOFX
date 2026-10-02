# Rendition 0.3 — Artist Architecture Consolidation

Status: CPU artist candidates, not production acceptance or final artist freeze. The everyday architecture is **Base → Palette → Material**, with Inspector as the diagnostic/reference environment. Original Scene, Tone, Volume, Density, Crossover, Crosstalk, Strip, Inspector and Primaries remain native, version-compatible tools in **Rendition / Advanced**; Inspector also appears at the top level.

## Permanent ownership

Rendition authors scene colour relationships and look formation. Pigment owns spatial information hierarchy, planes and selective information loss. SpektraFilm owns optional photographic/process/optical character. The authored DRT owns final display rendition. No film stocks, negative development, print/scanner simulation, grain, halation, diffusion, weave or physical film-plane effects are added to Rendition. Negative RGB means signed VFX data, never photographic negative film.

## Base v1 artist API

Thirteen main controls: Exposure, Contrast, Pivot, Black, White, Toe, Shoulder, Warmth, Tint, Saturation, Density, Shadow Colour, Highlight Colour. The common Input group adds interpretation/alpha controls, not additional creative mathematics. Advanced tonal colour retains hue directions, soft range centers/widths, chroma retention/death, local midtone displacement, bleaching and brilliance. Local exposure is a separate optional-matte group. These are parameter sliders; custom colour wheels are not implemented.

Exposure remains stops: +1 doubles RGB. Pivot is stops relative to 0.18. Black/White are weighted stop displacements of the shadow/highlight ranges, **not output floors or caps**: zero-energy black stays zero. Toe and Shoulder coordinate smooth tail compression. Warmth/Tint are midtone-weighted zero-Y biases. Shadow/Highlight Colour are signed amounts along independently editable hue directions. Density changes colourfulness-weighted scene magnitude with modest chroma coupling; it is dimensionless artistic depth, not physical optical density. Saturation scales the zero-Y residual. Tint-only settings preserve radiometric Y, not necessarily perceived brightness through a DRT.

Highlight Burn coordinates shoulder compression, brilliance reduction and source-chroma bleaching while allowing independent tint/retention. It never clips to white. Colour Death suppresses source chroma and tint smoothly as stop coordinates descend; its start/softness remain editable. Main controls are fixed intent contracts; future algorithms require new model selections, never silent replacement.

### Monotonic local tonal displacement

Primaries v1 is preserved unchanged, including its known extreme reversal; it remains Advanced. Base has a distinct effect ID and model, not a migration of Primaries. The targeted comparison uses the same +4-stop narrow midtone intention:

- PCHIP on the original, already reversing knots retains reversals. PCHIP preserves input-data monotonicity; it cannot make arbitrarily ordered knots monotone without a separate constraint. [SciPy's primary documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.PchipInterpolator.html).
- Merely bounding displacement amplitude also retains negative slopes. A bound on amplitude is not a derivative bound.
- **Selected:** integrate a positive slope of the desired stop curve, preserving artist parameter ranges and avoiding output clipping. Alternative constrained knots are deferred because they need another artist-to-knot mapping, with no measured workflow advantage.

Let e = log2((|Y| + ε)/0.18), ε = 0.18 × 2^-20. The existing smooth shadow/highlight memberships s,h and m=(1-s)(1-h) are normalized to unit sum, all evaluated from source coordinates after master exposure. Let T be the existing soft toe/shoulder tail. For q=0 and q=1 construct:

Dq(e) = pivot + contrast × [e − pivot + T(e) − T(pivot)] + m(midExposure−midDensity) + h whiteStops + s blackStops − q(density + h brillianceReduction).

Numerically differentiate D with a symmetric 0.01-stop stencil. Apply the C1 positive slope function ρ(d)=d when d≥0.1; otherwise ρ(d)=10^-6 + 0.099999 exp((d−0.1)/0.099999). Integrate using positive midpoint increments on [-64,+64] EV at 1/128-stop spacing; anchor each integral to **Dq(pivot)**, so midtone exposure is not accidentally canceled by pivot anchoring. Use positive endpoint slopes for extrapolation, never an endpoint clamp.

For a sample use scale-independent q = |zero-Y residual XZ| / sqrt(|residual XZ|²+Y²), with q=0 for zero energy. Interpolate the two increasing stop maps: G(e,q)=(1−q)G0(e)+qG1(e). Output luminance is Y × 2^[G(e,q)−e]. Along each fixed chromatic ray q is constant; both maps have positive slopes and so does their convex combination. With the signed near-zero adapter, d log |Yout| / d log |Y| = 1 + (G′−1)|Y|/(|Y|+ε) > 0. This is a scalar/ray luminance guarantee, **not** a positive full RGB Jacobian or global colour inverse. Float quantization may flatten extremely small slopes. The table is value-continuous; piecewise-linear interpolation has small derivative jumps. No C1 table interpolation claim is made.

The original colourfulness/tint/retention helpers are reused. The extra map ensures colour-dependent Density and Burn do not reintroduce the tested ray reversals. Full combined invertibility, extreme chromatic conditioning and broader artist feel remain unaccepted. Tail settings/contrast/pivot retain their declared meanings; slope constraints redistribute strong zonal changes across neighbouring values rather than arbitrarily reducing the control range.

## Palette v1 mappings

Fixed stage order: **Volume → Crossover → Crosstalk → shared zero-Y tonal tint** (historical Primaries helper). No new deformation engine. Six optional family directions are degrees in the existing Volume coordinates; the main UI hides raw coordinate displacement/matrices.

Separation increases family chroma by 0.25×amount and adds small neutral-preserving channel interactions. Compression reduces family chroma by 0.7×amount. Optional red protection first reduces red-family deformation; final blending uses the **original source** red membership, a smooth circular hue weight and relative-chroma protection across the complete stage stack. It is a soft red accent, not a hard isolating key or guarantee that arbitrary red pixels are untouched. Warm/Cool and neutral contamination coordinate zero-Y midtone tint. Shadow/Highlight Hue Bias feed existing exposure trajectories, multiplied by Trajectory strength. Colour Death reduces the dark trajectory chroma. Family directions plus these range controls provide the olive/cyan/secondary/accent examples; artist usefulness is pending.

Strong compression (>0.7), separation magnitude (>0.7), or family direction × trajectory magnitude (>30°) issues a nonblocking OFX warning. This is explicitly a **heuristic**, not a measured fold diagnosis. Nothing is silently restricted. Inspector Lab evaluates actual combined Palette determinants, stretch, condition and derivative reliability; prior multi-region Volume analyses remain available.

## Material v1 mappings / complexity gate

Fixed order: **Density → Strip → Crosstalk**. Material Density and Chroma Coupling invoke existing radiance-relative density behavior. Depth activates Strip with separation 1−(1−separation)(1−0.5 depth), and its density interaction; Depth therefore works independently at default separation. Leakage coordinates existing separation leakage. Crosstalk and Contamination expose small inspectable channel interactions; Red/skin anchor invokes the existing soft Strip anchor.

These eight controls are a provisional compact panel, not evidence that every research control deserves permanence. Density/Strip's M17 advantage gate remains open: some 0.2 responses closely match simple exposure/saturation/matrix baselines. The 0.3 review form explicitly asks for faster interaction, continuity/coherence, predictable depth and usefulness beyond those baselines. Controls failing that challenge move to Advanced or gain a new explicit model version; complexity is not accepted because a model is spectral-derived. No film or print stock is implied.

## Matte-driven local exposure

Base's optional **Matte** clip accepts float alpha coverage or RGBA alpha. No segmentation/filtering is introduced. Unconnected means full-frame coverage 1; outside a connected matte's bounds means 0. Invalid/nonfinite coverage or coverage outside [0,1] produces an explicit error. It is never silently clamped.

After the authored Base grade, local exposure applies k=2^[localStops × matteAlpha × (1−protection×sigmoid((e−center)/softness))]. Protection is optional highlight-tail protection, center/softness in stops. At protection=0: +1 stop/full coverage means ×2, −1 means ×0.5, half coverage/+1 means √2. Chroma preservation blends the zero-Y residual gain from k toward 1 while Y still receives k. Alpha is copied; zero-alpha unpremultiply mode retains original RGB. Local range protection is exposure-conditioned and may redistribute/reverse luminance relationships at extreme strengths: the Base scalar monotonic guarantee does not cover arbitrary matte/protection fields. No clipping or spatial image processing repairs this.

## Full Spectral Reference Lab

`research/full_reference.py`: slow 360–830 nm / 1 nm CIE 1931 2° emission integration, original synthetic KM/dye attenuation, signed XYZ residual recombination and return to the original linear gamut. No DRT, display encoding, viewing-illuminant print render, or unique spectrum recovery. Supports Rec.2020, AP1/D60 with explicit CAT, and Rec.709.

Three distinct reconstructions: matched compact three-Gaussian smooth-positive basis; eight-basis NNLS; Smits-derived spectral shape with nonnegative physical component and preserved signed residual. Max-absolute-channel normalization separates radiometric scale; residuals retain unsupported signed/nonphysical components. Twofold exposure doubles spectral magnitude without changing shape. NNLS/Smits residual/participation transitions still need wide image/compositing acceptance; exact no-op reconstruction and active finiteness alone do not pass that gate.

The matched path reproduces Density's default selection/protection/chroma coupling and Strip's default record/recombination/anchor behavior by full integration rather than interpolated response matrices. Alternative Strip references use explicit overlapping broad spectral records; they are materially different references, **not** identical low-level parameterizations. The current 432 comparisons cover six skin/cyan/blue/olive/red/ochre families × four chroma levels × three exposure levels × two operators × three reconstructions. Matched errors measure approximation; alternative differences measure underdetermination. Arbitrary custom matrices, record weights, all selector/domain settings and measured real materials are not yet matched by this reference runner. Do not replace production implementations with per-pixel spectra based on these numerical results.

## Operator explanations / acceptance

| Required property | Base v1 | Palette v1 | Material v1 |
|---|---|---|---|
| Input | Explicit/Auto scene-linear known gamut; unknown fails | Same | Same |
| Internal representation | D65 XYZ, signed residual, two monotone stop maps | Existing signed Oklab Volume/Crossover, linear channel matrix, XYZ tint | Existing positive spectral coefficients + signed XYZ residual, linear channel matrix |
| Relationship changed | Tone, chroma survival and tonal chromaticity | Family separation, trajectory and palette diversity | Radiance-relative attenuation/separation/recombination |
| Scene vs appearance | Scene-compatible authorship, no DRT | Same | Synthetic material-informed scene-compatible candidate, not print appearance |
| Exposure | Conditioned; master pure exposure equivariant alone | Conditioned trajectories | Density-conditioned; Strip alone equivariant; channel matrix equivariant |
| Negative handling | Signed-magnitude gain + unchanged-sign residual construction | Historical signed-coordinate extension | Historical smooth physical component + explicit signed residual |
| HDR | Unbounded scene scale; explicit float overflow | Unbounded; actual geometry may fold | Unbounded radiometric component; representability limitations explicit |
| Invertibility | Combined inverse unclaimed | Unclaimed; folds possible | Unclaimed; separation may lose information |
| Neutrals | Axis preserved except explicit tint; magnitude only identity/tint-only Y | Core protections; explicit contamination can tint | Neutral anchors; unrestricted front-end interactions can alter magnitude |
| Gamut dependence | Colorimetric fixed D65 XYZ/tint directions | Colorimetric Volume/Crossover/tint, explicit gamut-relative Crosstalk | Colorimetric spectral stages; explicit gamut-relative Crosstalk |
| Failures remaining | Quantized near-flat slopes, conditioning, matte protection extremes, artist feel | Folds, partial soft accent isolation, family-control prediction | M17 advantage, residual domination, artist depth usefulness |
| Why separate | Everyday image formation | Coherent colour grammar | Generic depth/reproduction-informed relationships, independent of film |

The Inspector 0.3 landing page organizes previous Volume geometry, HK, trajectories, palette/OT, gradients, signed/nonfinite diagnostics and the Pigment bridge alongside new full-spectral comparisons and artist examples. It never changes a grade automatically. Native Inspector's existing image modes remain available; the central offline page is not claimed to embed all plots inside the OFX UI.

## Evidence / remaining gates

Retained reports and image artifacts are under `build/architecture-0.3` with snapshots in `docs/reports/0.3-*`. Four suites include new monotonic ray, exposure, tint-Y, signed/HDR/alpha, matte, original Primaries recipe and full-reference tests. Native Nuke validates all twelve native IDs, model/animation reload, matte coverage, float rendering, **tagged AP0 Read with Raw disabled**, OCIO-to-scene_linear conversion and downstream Auto identity. GUI evidence is recorded separately; scripted creation never substitutes for interactive menu acceptance.

68 one-node examples cover seven Base tasks, six Palette tasks and four Material tasks on four approved sample frames, under the external Flawed Emulsion 2 / sRGB view. Nuke graph sources use all six approved originals tagged ACES2065-1, or local Rec.2020 fixtures tagged Linear Rec.2020; Raw is OFF so Nuke converts to the project's scene_linear role. Rendition Auto interprets the already converted signal. Local fixture headers include Rec.2020 chromaticities and an OCIO colour-space label. Original ACES files remain untouched. Labels are explicit; metadata alone is not assumed to make every host infer the correct space.

The user requested continued sample use rather than additional authored CG assets. Human time/predictability/reuse and reference-direction judgment remain unset in a **preserved** artist review file. Do not invent acceptance or claim the approved samples are the user's authored CG. Architecture freeze follows coherent artist acceptance; these versioned candidates establish the target but do not satisfy that stop condition. Metal and Flame remain pending and do not block this phase.


### Nuke 0.3 presentation verification

Fresh Nuke 17.0v1 interactive tests pass normal creation of Base, Palette, Material and Inspector from Rendition; the nine historical entries remain in Advanced. Base's 13 main controls, Advanced tonal controls (edited shadow hue) and five Dodge/Burn controls are accessible. Palette's nine controls and six family directions and Material's eight controls are visible. The native expandable-group issue persists; the Nuke adapter presents standard tabs with self-relative links to the original parameters instead. Native write-through, node rename and saved reload pass without duplicate processing state. See `docs/reports/0.3-nuke-ui.json` and the 21 native checks in `docs/reports/0.3-nuke-architecture.json`.

The interactively created test was saved as `UI-created-artist.nk`. Opening the sample graph did not visibly replace that window, so interactive sample graph loading is not claimed accepted. Its native Read conversion and Auto identity tests pass. This is an artist candidate; human predictability, speed and cross-content acceptance remain open.
