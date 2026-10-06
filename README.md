# Rendition OFX

**Scene-referred colour authorship, from everyday primaries to deep colour relationships.**

Rendition is a macOS arm64 OpenFX suite built around **Base → Palette → Material**, with Inspector for analysis and the original deep operators available under **Advanced**. One bundle contains twelve distinct effects, sharing a C++ colour core.

The aim is to make authored colour relationships controllable: creamy highlights, bronze/ochre skin, olive contamination, cyan falling into blue-black, surviving colour in deep shadows, or a protected red accent inside a compressed palette. The compact nodes coordinate existing engines; deeper controls remain available when a look needs more precise authorship.

**Current state:** the 0.33 architecture candidate preserves the accepted 0.32 grading equations and control semantics. CPU operation and Nuke 17.0v1 integration have been exercised. The artist feedback is that the current grading behaviour feels very good. This remains a development candidate, not a production-approved or distribution-signed release; broader artist/interaction acceptance, Flame and host Metal remain pending. Presets/recipes are intentionally deferred.

## Guide contents

[Workflow](#the-workflow) · [Input and alpha](#input-interpretation-signed-values-and-alpha) · [Base](#base-everyday-image-formation) · [Palette](#palette-colour-grammar-across-families-and-exposure) · [Material](#material-depth-and-imperfect-reproduction-relationships) · [Linear versus log](#crosstalk-and-the-linearlog-distinction) · [Advanced tools](#the-advanced-engines) · [Composition and compatibility](#main--expert-transparent-composition-and-compatibility) · [Inspector](#inspector-and-reference-assistance) · [Spectral reference](#full-spectral-reference-an-offline-oracle) · [Validation](#what-is-validated-and-what-remains-open) · [Build](#build-install-and-evaluate)

## The workflow

```text
Scene-linear source
    → Rendition Base       tonal formation and tonal colour
    → Rendition Palette    colour-family relationships and exposure trajectories
    → Rendition Material   material-informed depth and record interaction
    → optional Pigment / selected scene-compatible SpektraFilm effects
    → external authored DRT
```

| Tool | Its responsibility | Useful intentions |
|---|---|---|
| **Base** | Exposure, tone, colourfulness and soft tonal colour | Cool blacks; warm shadows; hold highlights; make whites creamier; preserve or extinguish colour through the toe |
| **Palette** | Continuous family deformation, trajectories, channel interaction and tint | Green → olive; dark cyan → blue-black; compress secondaries; protect red; contaminate neutral relationships |
| **Material** | Compact Density/Strip models with channel interaction | Deepen material colour; vary chroma with depth; introduce imperfect separation, leakage and coherent palette bias |
| **Inspector** | Diagnostics and reference assistance | Understand exposure/colour trajectories, local Volume geometry, signed/HDR values, palette distributions and structural preservation |
| **Advanced tools** | Direct access to individual engines | Author matrices, log-domain shaping, detailed selectors and trajectories without replacing the everyday stack |

These responsibilities leave room for bold image direction. Handmade grades can be starting points for substantial changes, including authored spatial cuts, dodge/burn and selective withholding. Grain, diffusion and obscured information may be important to the finished image; technical cleanliness is not the artistic objective. Spatial hierarchy belongs to host mattes/Pigment, photographic texture and reproduction to SpektraFilm, and display rendition to the external DRT.

### A necessary SpektraFilm distinction

Selected, verified scene-compatible optical effects can precede an authored scene DRT. A **full negative/print/reproduction path** may instead produce an appearance or display-encoded result and needs its own appropriate output/display handling. Do not automatically append a second scene DRT. A float buffer—or a conversion back to linear RGB—does not by itself establish scene-referred meaning. The [pipeline contract](docs/PIPELINE_CONTRACT.md) records the tested boundaries and remaining limitations.

## Input interpretation, signed values and alpha

The normal grading contract is **scene-linear RGB in and scene-linear RGB out in the interpreted working gamut**. Inspector diagnostic views are an explicit exception.

- Supported interpretation: Linear Rec.2020, ACEScg/AP1, Linear Rec.709/sRGB primaries, or valid custom primaries/white point.
- **Manual interpretation identifies the incoming numbers; it does not convert them to the selected gamut.** The host or an explicit conversion must perform any actual input conversion.
- In Nuke, Auto resolves the active OCIO `scene_linear` role through the startup bridge. Other hosts can supply recognized scene-linear clip metadata. Unknown, unsupported or ambiguous interpretation fails explicitly; there is no hidden Rec.2020 fallback.
- Correctly tagged Reads with Raw off let Nuke convert source images into the project working space. Rendition then interprets that already converted signal. ACEScct processing does not imply ACEScg input.
- Negative RGB is valid intermediate VFX data. HDR values are not bounded by 1. Rendition introduces no hidden image clipping, gamut compression or DRT. Individual encodings and physical adapters have documented domains.
- With known interpretation, default identity copies original RGB/alpha exactly. RGB as supplied is the default; optional unpremultiply/process/premultiply retains original RGB at zero alpha. Alpha is copied unchanged.
- Active processing reports unsupported domains, nonfinite input or finite-arithmetic overflow explicitly. It does not silently repair pixels. Named diagnostics can display nonfinite data.

**Identity, neutral-axis preservation and neutral-magnitude preservation are separate properties.** A neutral can remain neutral while becoming brighter; a default identity says nothing about the neutrality of an arbitrary creative setting.

### Working-gamut conversions and white points

RGB/XYZ conversion is derived from the selected chromaticities, not an assumed fixed RGB gamut. For primary `(x_i,y_i)`, construct the XYZ column `[x_i/y_i, 1, (1−x_i−y_i)/y_i]`. With these columns in `P` and normalized white `W`, solve `s=P^-1 W`:

```text
RGB_to_XYZ = P diag(s)
XYZ_to_RGB = inverse(RGB_to_XYZ)
```

White-point adaptation uses Bradford, CAT16 or XYZ scaling where exposed. For the selected adaptation matrix `C`, source white `Ws` and destination white `Wd`:

```text
CAT = C^-1 diag((C Wd) / (C Ws)) C
```

Conversion/adaptation setup uses double precision before pixel-kernel evaluation. Invalid or singular custom primaries fail explicitly. Custom chromaticity editors are only applicable under Custom interpretation. These conversions establish colorimetry; they never select a creative look.

## Base: everyday image formation

Base has thirteen Main controls. Advanced pages retain tonal colour/ranges, midtone refinement, bleaching, brilliance, Highlight Burn and matte-driven Dodge/Burn.

| Main control | What it changes |
|---|---|
| Exposure | Master scene exposure in stops: +1 doubles RGB, −1 halves it |
| Contrast | Tonal slope around the pivot |
| Pivot | Contrast pivot in stops relative to scene value 0.18; meaningful when shaping is active |
| Black / White | Soft shadow/highlight stop displacements; **not** literal output floors or caps |
| Toe / Shoulder | Smooth tail compression, with adjustable starts and softness |
| Warmth / Tint | Midtone-weighted warm/cool and magenta/green biases projected into a zero-Y plane |
| Saturation | Scaling of the zero-Y colour residual |
| Density | Everyday colourfulness-dependent tonal attenuation with modest chroma coupling; distinct from Material Density |
| Shadow Colour / Highlight Colour | Signed amounts along independently editable hue directions in soft tonal ranges |

### Restored illuminant / white-balance control

**Base → Tonal Colour / Ranges** exposes **Illuminant (daylight)** in Kelvin, **Illuminant tint**, and **Illuminant adaptation**. The historical **Advanced Scene → Illuminant estimate** remains available too. Base's thirteen Main controls stay compact.

- **6504 K with zero illuminant tint is exact bypass.** 6500 K is close, but deliberately not rounded to neutral.
- This is an estimated **source illuminant**, corrected toward the working reference white. Lowering the estimate from 6500 to 6000 K makes the correction cooler; increasing it makes the correction warmer. It is not the same control as Base's creative Warmth.
- Illuminant tint is a CIE 1960 `v` offset (Base range −0.02…+0.02), distinct from the zero-Y creative Tint. Adaptation offers Bradford, CAT16 or XYZ scaling and is disabled when the illuminant correction is neutral.
- Correction is a global linear chromatic-adaptation matrix before Base's tone, colour and local exposure. It preserves positive exposure scaling and signed/HDR information within finite arithmetic; it may intentionally change Y and neutrals.

The new Base path uses the versioned CIE daylight polynomial over 4000–25000 K, calibrated to exact neutrality at 6504 K in a common D65 reference. Working-gamut transforms surround this correction, so equivalent XYZ colours receive corresponding treatment in Rec.2020, AP1 and Rec.709. It introduces no log encoding or DRT.

The older Scene polynomial has a nonstandard lower branch and a measured discontinuity at 7000 K. Existing Scene instances retain that **historical generation 0**; Base's newly appended illuminant controls use **generation 1**. `illuminantVersion` is hidden persistent compatibility state, not a new everyday model dropdown. Old Base scripts omit the new controls and retain exact default bypass; no previous tonal equations or stored controls are replaced.

See [the illuminant restoration contract](docs/ILLUMINANT_RESTORATION.md) for exact IDs, calibration, mathematics, tests and compatibility.

### Base mathematics

After master exposure, convert to reference-white XYZ and decompose:

```text
XYZ = white × Y + residual
residual = XYZ − white × Y       (residual Y = 0)
e = log2((abs(Y) + ε) / 0.18)
ε = 0.18 × 2^-20
```

This is a **signed-magnitude luminance coordinate**, accurate as exposure stops away from its explicit near-zero floor. Base does not encode the entire RGB image into a camera log space.

Shadow and highlight memberships use logistic transitions; the middle membership is `(1−shadow)(1−highlight)`. All three are normalized to unit sum. Range/softness controls move these overlapping memberships without hard luminance keys. They are evaluated from the source after master exposure.

The desired stop curve combines pivoted contrast, softplus toe/shoulder tails, weighted Black/White and midtone displacements, and colourfulness-dependent Density/brilliance. To contain the historical narrow-midtone reversal, Base integrates a **positive slope** rather than clamping the output:

```text
ρ(d) = d                                      when d ≥ 0.1
ρ(d) = 10^-6 + 0.099999 exp((d−0.1)/0.099999)   otherwise
```

The desired derivative is estimated with a symmetric 0.01-stop stencil. Two maps—neutral and fully colourful—are integrated at 1/128-stop spacing over −64…+64 stops, anchored to the desired pivot value, with positive-slope extrapolation. The maps are blended by scale-independent source colourfulness `q`:

```text
q = length(residual XZ) / sqrt(length(residual XZ)^2 + Y^2)
q = 0 at zero energy
G(e,q) = (1−q)G0(e) + qG1(e)
Yout = Y × 2^(G(e,q)−e)
```

The scalar luminance relationship is monotonic along a fixed chromatic ray. This is **not** a positive full RGB Jacobian, a global inverse, or a claim that the table interpolation is C1. Strong local changes can redistribute tonal response into neighbouring values; very small slopes can flatten under float quantization.

Source colour is scaled by tone/saturation/retention, bleaching attenuates source highlight chroma, and tonal tint is added in the zero-Y plane. Colour Death smoothly attenuates both residual colour and tint toward black. Tint-only controls preserve radiometric Y within numerical precision, which does not guarantee unchanged perceived brightness through a DRT. The fixed projected Rec.2020 artist hue circle is not a colour-managed swatch picker.

### Highlight Burn versus local exposure

Highlight Burn coordinates compression, source-chroma bleaching and brilliance reduction. It does not clip highlights to white and is independent of matte-driven local exposure.

Base's optional Matte input supplies coverage `m`. With local stop amount `E` and range-protection weight `w`:

```text
gain = 2^(E × m × w)
```

Without protection or chroma preservation, full coverage at +1 stop multiplies scene RGB by 2. Optional chroma preservation changes the relative scaling of Y and the zero-Y residual. A missing/unavailable matte contributes zero coverage. Base does not generate segmentation or spatially filter the matte.

Base paired range sliders adjust their display bounds against the opposite endpoint; no other knob is rewritten. This is separate from Palette/Material's evaluated interval sorting. [Exact Base/control contract](docs/RENDITION_CONTROL_SYSTEM_0_32.md).

## Palette: colour grammar across families and exposure

Palette executes **Volume → Crossover → Crosstalk → tonal tint**. Its nine Main controls summarize these stages without making them inaccessible.

| Main control | Existing engine mapping |
|---|---|
| Separation `S` | Family chroma contribution `1 + 0.25S − 0.7C`; Crosstalk rg/bg additions `0.025S` |
| Compression `C` | Reduces the family chroma contribution above |
| Contamination | Final tonal tint: `midTint = 0.2 × Contamination` |
| Protected red accent | Attenuates Main family chroma/hue changes in Red; it is not a universal lock on every later stage |
| Warm / Cool Bias | Final tonal bias: `midBalance = 0.3 × Bias` |
| Shadow Hue Bias / Highlight Hue Bias | Dark/bright Crossover hue control points, multiplied by Trajectory Strength |
| Colour Death | Main dark Crossover chroma multiplier `1 − Colour Death` |
| Trajectory Strength | Modulates eligible Main/Expert hue and channel deflections; it is not a global node opacity |

Additional persistent family-direction amounts feed each family's hue displacement. Main mappings above describe macro bases; the Expert composition contract below determines the effective stage values.

### Volume: continuous regions, not sequential keys

The internal path is working RGB → XYZ → D65 adaptation → Oklab-like opponent coordinates → deformation → inverse transforms → original working RGB. Real signed cube roots are **our algebraic extension**; published perceptual validity is not claimed for arbitrary negative scene values.

Each of Red, Yellow, Green, Cyan, Blue and Magenta has independent persistent state:

- Hue centre/width, relative-chroma and exposure intervals, softness and neutral protection.
- Hue displacement, chroma scale, density displacement and exposure displacement.
- A local 3×3 linear RGB matrix and its mix.

The Nuke UI reuses one selected-family editor linked directly to six stored OFX banks. Switching families does not copy or reset their animation.

Selection weights multiply smooth wrapped-hue, relative-chroma, exposure and neutral memberships. Relative chroma is `sqrt(a²+b²)/max(abs(L),10^-12)`. Exposure selection uses normalized ACEScct Y coordinates, including its signed toe; nonpositive values there are not physical exposure stops.

For opponent point `p`, family deformation `D_i` and original-source weight `w_i`, the default normalized overlap is:

```text
pout = p + Σ[w_i × (D_i(p) − p)] / max(1, Σw_i)
```

Only active deformations contribute to the normalization; local RGB matrix deltas follow the same original-source selection rule. Weighted deltas, bounded vectors and a shared-field mode remain available in Advanced. Internal family ordering never changes later selections.

For hue angle `θ`, chroma multiplier `c`, density `d` and exposure displacement `E`, the existing opponent deformation uses:

```text
Lout = L × 2^((E−d)/3)
[aout, bout] = rotate([a,b], θ) × c × 2^(E/3 + 0.15d)
```

Thus Volume Density changes an opponent lightness/chroma relationship; it is not the spectral-derived Density engine. Strong deformations can fold colour space, including in nonnegative RGB. Normalized overlap prevents unchecked weight addition, not folds or a guaranteed inverse. Inspector geometry exists to make that visible.

### Crossover: trajectories rather than hard tonal masks

Opponent mode defines dark/mid/bright hue, chroma and density relationships along exposure. For ordered centres and positive transition width `t`:

```text
dark   = 1 − sigmoid((EV − darkCentre)/t)
bright = sigmoid((EV − brightCentre)/t)
mid    = 1 − dark − bright
trajectory(EV) = dark × darkValue + mid × midValue + bright × brightValue
```

The interpolated values drive the existing opponent deformation, with original-source selection/protection. This supports a single relationship such as **dark cyan → blue-black, mid cyan → stable cyan, bright cyan → green-cyan**. Family selectors and direct dark/mid/bright controls provide finer authorship than the Main bias macros.

Channel mode is a different, mutually exclusive operation: each original R/G/B channel is encoded into the selected look coordinates, receives its own continuous dark/mid/bright displacement, and is decoded. Opponent selectors do not secretly apply to that path. Channel trajectories are gamut-relative and may tint neutrals.

## Material: depth and imperfect reproduction relationships

Material executes **Density → Strip → Crosstalk**. It is generic material-informed colour authorship, not a film-stock emulator.

| Main control | Existing engine mapping |
|---|---|
| Depth | Strip density interaction; combines with Separation as `1 − (1−Separation)(1−0.5×Depth)` |
| Material Density | Density engine amount |
| Chroma Coupling | Density engine coupling; meaningful when Density is active |
| Separation | Strip separation contribution above |
| Leakage | Strip record leakage; meaningful when separation/depth is active |
| Crosstalk | rg/bg channel additions `0.1 × Crosstalk` |
| Contamination | gr/gb channel additions `0.1 × Contamination` |
| Red / skin anchor | Continuous Strip protection around the existing red-family anchor; not semantic skin detection |

Detailed Density controls retain selection, chroma coupling, shadow weighting and highlight protection. Strip retains three-record, two-record and custom modes; record contributions, weights, leakage, density interaction, palette shaping and anchors remain accessible. Research-only HK or physical reproduction alternatives are not everyday model switches.

### Shared spectral-derived adapter

The compact engines work with a three-spectrum basis, **not a recovered physical spectrum**. Let `x` be D65 XYZ and `B` the integrated basis matrix:

```text
c = B^-1 x
p_i = 0.5 × (c_i + sqrt(c_i² + (0.001 ||c||)²))
r = x − Bp
x = Bp + r
```

`p` supplies a nonnegative physical-component candidate; `r` preserves unsupported signed information. The residual is algebraic and has no assigned physical material meaning. The split is continuous and homogeneous under positive exposure scaling, with explicit zero handling. Negative scene RGB is not discarded.

Six hue families and 129 material-response levels are preintegrated into small interpolated response matrices. The OFX runtime has **no per-pixel wavelength integration loop**.

### Density mathematics

A hue/depth-dependent Kubelka–Munk-derived response `A_KM` attenuates the positive component, with the residual restored:

```text
filtered = A_KM(hue, abs(d)) p + r
candidate = x + sign(d) × (filtered − x)
```

Negative artistic density reverses the attenuation delta; it is not a physical negative concentration. Opponent chroma is then adjusted toward source chroma times `2^(d × coupling)`, before blending with original-source selection/protection weights. This lets depth and chroma vary independently. It does not establish a universal “deeper colour without darkening” property.

The synthetic physical reference uses concentration `1.5d²`. The artistic knob is dimensionless; it is not a measured optical-density control. Exposure selection, shadow weighting and highlight protection deliberately make Density exposure-conditioned.

### Strip mathematics

Strip separates and recombines imperfect spectral-basis records:

1. Blend positive records toward their mean using leakage × separation.
2. Retain three records, redistribute the middle record into two, or transform through a custom record basis.
3. Preserve signed custom-record residuals.
4. Optionally shape normalized record fractions with exponent `2^(separation × palette)`, then renormalize their sum.
5. Apply record contributions, the preintegrated dye response, recombination weights and the custom inverse where applicable.
6. Restore the source signed XYZ residual and blend the deformation through separation, neutral/red anchors and mix.

For fixed settings, this construction aims to preserve positive exposure scaling; finite arithmetic and documented boundaries still apply. Two-record reduction is information-losing, and neither arbitrary palette shaping nor the complete operation has a promised global inverse.

**Custom Strip safety coordinates are not literal Crosstalk coefficients.** In the current bounded generation, raw row entries `u` map to:

```text
gain_r = 2^((u_rr − 1)/4)
total_r = 1 + Σ_(c≠r) abs(u_rc)
M_rr = gain_r
M_rc = 0.75 × gain_r × u_rc / total_r    (c≠r)
```

Positive diagonal dominance keeps the effective custom record basis nonsingular throughout its declared editor range. Historical generations retain their original basis equations.

## Crosstalk and the linear/log distinction

Palette, Material and Advanced Crosstalk expose the actual 3×3 channel interaction:

```text
         M11 M12 M13
M =      M21 M22 M23
         M31 M32 M33
Meffective = (1−mix)I + mix M
```

Off-diagonal macros and constraints contribute to the evaluated matrix; persistent controls remain inspectable. Identity-matrix Mix is disabled when the existing dependency predicate finds no interaction to mix.

| Constraint | Exact invariant in the matrix's operating coordinates |
|---|---|
| Unrestricted | No neutral or luminance constraint |
| Neutral preserving | Each row sums to 1: neutral axis **and** magnitude preserved |
| Common row sum `s` | Neutral axis preserved; neutral magnitude multiplied by `s` |
| Luminance preserving | `lᵀM = lᵀ`, where `l` is the working RGB-to-Y row |

The luminance projection is `M' = M + 1(lᵀ − lᵀM)/(lᵀ1)`. In a **linear RGB** matrix this preserves linear Y. In **encoded coordinates**, a weighted encoded-channel invariant does not imply preserved scene luminance after decoding. Likewise, a common encoded row sum changes neutral magnitude according to the nonlinear encoding. Forward singular matrices are possible in unrestricted modes; invertibility needs a nonsingular effective matrix.

### There is no global “Log Space” switch

External gamut, external encoding and internal operator coordinates are separate concepts:

```text
Linear Rec.2020 → ACEScct scalar encoding → matrix/shaping → inverse encoding → Linear Rec.2020
```

This does not convert to AP1 or add an ACES display transform. Linear Crosstalk mixes scene energy relationships; encoded Crosstalk mixes channel coordinates and generally behaves differently with exposure.

| Operation | Actual internal domain |
|---|---|
| Base | Reference XYZ, zero-Y residual and signed-magnitude stop coordinates; no camera-log selector |
| Advanced Scene | Exposure/CAT/matrix in linear; SOP/saturation in linear or selected look coordinates |
| Advanced Tone | Selected scalar look encoding, normalized around 0.18, shaping, inverse |
| Volume / opponent Crossover | Signed opponent coordinates; exposure-conditioned selection/trajectory where configured |
| Channel Crossover | Selected per-channel look encoding and continuous displacement |
| Crosstalk | Linear RGB or selected encoded RGB |
| Density / Strip | Spectral-derived basis/residual system with opponent selection/coupling; no log runtime switch |

The six existing scalar encodings are distinct options. ACEScct is the accepted default where a scalar encoding is used; a custom representation was not required to win.

| Encoding | Implemented coordinate / signed handling |
|---|---|
| Pure stops | `log2(x/0.18)`; positive input only |
| ACEScct | Linear toe for `x≤0.0078125`: `10.5402377416545x+0.0729055341958355`; otherwise `(log2(x)+9.72)/17.52` |
| LogC4 scalar | Analytical LogC4 branches with a linear lower continuation; no ARRI gamut conversion |
| DaVinci Intermediate scalar | For `x≤0.00262409`: `10.44426855x`; otherwise `(log2(x+0.0075)+7)×0.07329248` |
| Unclamped AgX-style stops | `(log2(x/0.18)+10)/16.5`; positive input only; not the AgX gamut/tone/display transform |
| LookLog candidate | With `b=0.18/64`, below `b`: `−6+(x−b)/(b ln 2)`; otherwise `log2(x/0.18)` |

For completeness, the implemented LogC4 scalar forward branch is:

```text
a = (2^18 − 16) / 117.45
b = 928 / 1023
c = 95 / 1023
t = (2^(6 − 14c/b) − 64) / a
s = 7 ln(2) × 2^(7 − 14c/b) / (a b)
encode(x) = (x−t)/s                                  if x < t
            b × (log2(a x + 64) − 6)/14 + c          otherwise
```

For normalized look shaping, `z = (encode(x)−encode(0.18))/normalStopSlope`. These are approximate exposure coordinates through a linear toe, not physical stops for every signed/near-zero value. Positive-only choices can reject active processing of zero/negative channels; safe parameter composition does not remove that domain restriction. Exact branches/inverses/constants are in the [shared kernel](include/rendition/kernel_math.hpp) and [domain contract](docs/RENDITION_CONTROL_SYSTEM_0_32.md#10-processing-domain-contract).

## The Advanced engines

The original nodes remain available and version-compatible. They are optional direct tools, not prerequisites for everyday grading.

| Effect | Direct capabilities and mathematics |
|---|---|
| **Scene** | Master/RGB exposure, defined daylight temperature/tint and chromatic adaptation, custom matrix/mix, signed SOP and saturation. Execution order: exposure → CAT → matrix → SOP → saturation. SOP is `sign(sx+o) abs(sx+o)^p`; signed power is our extension, not a native physical-light claim. Temperature retains its historical 4000–25000 K approximation; the new Base illuminant uses a separately versioned CIE daylight calculation. |
| **Tone** | Linked/per-channel contrast, pivot, toe/shoulder extents, shadow/highlight density and middle-gray preservation in selected look coordinates. It is a separate curve from Base. Linked mode uses a maximum-absolute-channel magnitude envelope, not a perceptual luminance guide. |
| **Volume** | Direct six-family continuous deformation, local matrices, overlap modes and selection diagnostics described above. |
| **Density** | Direct compact depth/coupling and multidimensional selection/protection. |
| **Crossover** | Direct opponent or independent RGB-channel dark/mid/bright trajectories. |
| **Crosstalk** | Direct matrix, interaction macros, constraints, mix and processing-domain choices. |
| **Strip** | Direct compact record separation/recombination, leakage, palette, contributions/weights and anchors. |
| **Primaries** | Preserved earlier tonal-colour prototype. Its strong narrow-range midtone response can reverse tone; Base contains that issue using its different monotonic model. |

Advanced Tone uses softplus `sp(x)=log(1+exp(x))` and logistic `σ(x)`:

```text
f(z) = pivot + contrast × [(z−pivot)
       + toe × sp(−(z−pivot)−toeExtent)
       − shoulder × sp((z−pivot)−shoulderExtent)]
       − 0.15 × contrast × [shadowDensity × σ(−z−toeExtent)
                           + highlightDensity × σ(z−shoulderExtent)]
```

Middle-gray preservation subtracts `f(0)` from the mapped coordinate; exposure remains separate. Per-channel mode can change channel relationships. Linked encoded displacements are not generally chromaticity-preserving RGB scale. Detailed domains, neutral guarantees, inverses and failure cases live in the [operator design documents](docs/design/).

## Main + Expert: transparent composition and compatibility

Main controls coordinate a macro base; touching Main does not overwrite authored Expert knobs. OFX parameters are the sole persistent grading state. Nuke tabs and self-relative links provide presentation, not a second set of grading values.

Palette/Material retain three stored generations:

| Stored index | Behaviour |
|---|---|
| 0 | Original 0.3 macro behaviour; deeper restored state inactive |
| 1 | Historical 0.31 additive/multiplicative composition; renderable, unsafe ordinary editing contained as read-only |
| 2 | 0.32 bounded/full-controls candidate, preserved by 0.33 |

The descriptor default remains **index 0** because old projects may omit default-valued parameters. Index 2 has not been promoted as the default for newly created nodes. Compatibility is separate from creative model selection; migration is deliberate and may change an Expert-authored grade. Historical saved behaviour must remain reproducible.

For an ordinary index-2 scalar, let macro base be `b`, Expert value `e`, engine default `e0`, and legal engine interval `[lo,hi]`:

```text
delta = e − e0
span = (delta ≥ 0) ? hi−e0 : e0−lo
f = (span > 0) ? delta/span : 0

effective = hi                                  if f =  1
            lo                                  if f = −1
            b + f × ((f ≥ 0) ? hi−b : b−lo)     otherwise
```

Expert deflection uses remaining legal headroom. Neutral Expert retains Main; neutral Main retains ordinary Expert scalar behaviour; endpoints remain valid. No other knob or image RGB is clipped/rewritten. Choices/selectors are explicit state rather than ordinary scalar additions. Eligible hue/channel deflections have the documented trajectory-strength mapping, Strip separation uses complementary composition, crossed effective selector endpoints are sorted, and the custom Strip basis uses the safety mapping above. These exceptions matter; [the canonical control specification](docs/RENDITION_CONTROL_SYSTEM_0_32.md#8-main--expert-composition-contract) gives the exact complete contract.

## Inspector and reference assistance

**Native Inspector** provides exposure/channel/neutral/hue/chroma ramps, chart/cube diagnostics, Reference difference, RGB unit-cube excursion and nonfinite views. Its Volume geometry modes examine determinant, condition number, maximum/minimum stretch and derivative reliability.

For a colour transform `F`, local geometry uses the finite-difference Jacobian `J = ∂F/∂RGB`. Singular values measure stretch; `κ = σmax/σmin` measures conditioning. Reliable negative determinant witnesses reveal local orientation reversal/folds. Near-neutral/near-zero derivatives, deliberate chroma collapse and numerical step sensitivity need separate interpretation. An RGB “outside 0…1” diagnostic is not a universal HDR validity test.

**Offline Inspector Lab** extends this environment with colour/exposure/Density trajectories, Full Spectral comparisons, palette distributions, optimal-transport reference assistance, gradient/structure maps, HK appearance experiments and experimental Pigment soft-membership/residual guides. These are not all native Viewer modes. Transport suggestions do not automatically grade the image; gradient analysis does not introduce spatial filtering into Rendition. HK experiments remain research diagnostics rather than production Density controls.

See [deep-validation findings](docs/DEEP_VALIDATION_0_2.md), [Inspector design](docs/design/inspector.md) and the [experimental Pigment bridge](docs/design/pigment-bridge.md).

## Full Spectral Reference: an offline oracle

The reference path is scene RGB → spectral reconstruction/material operation → CIE integration → XYZ → original linear gamut. It uses **360–830 nm at 1 nm**, the CIE 1931 2° observer, and D65/D60/D50/A reference illuminants where applicable. No DRT is inside the quantitative comparisons.

Reconstruction assumptions include a matched three-basis model, eight-basis NNLS, Smits-derived reconstruction, and a qualified sigmoid/D65 pilot inspired by the Jakob/Hanika function family. The pilot is not the optimized rgb2spec implementation or its gamut/performance guarantees.

**RGB-to-spectrum reconstruction produces plausible metamers; it does not recover the original physical spectrum.** Where a signed residual is needed, only spectrum plus residual reproduces the stimulus. Algebraically exact residual recombination is not proof of accurate physical reconstruction.

Three physical reference classes are kept distinct:

| Class | Reference relationship | Meaning |
|---|---|---|
| Kubelka–Munk | `R∞ = 1/(1+a+sqrt(a²+2a))`, `a=K/S` | Infinite-thickness reflective/scattering pigment reference |
| Beer–Lambert / optical density | `T(λ)=10^(-D(λ))` | Transmissive dye/absorption reference |
| Neugebauer / Yule–Nielsen | `R=(Σ a_i R_i^(1/n))^n` | Multi-colorant coverage/reproduction reference; synthetic illuminated appearances, not scene grading |

Synthetic spectra are not measured film stocks, historical print processes or universal materials. The production compact models use material-informed radiance-relative behaviour; complete illuminated reproduction appearances remain separate.

The focused completion retained 432 baseline comparisons and added 8,000 trajectory rows, reconstruction/conditioning studies, held-out Strip baselines and physical-reference comparisons. The matched full path's reported maximum scale-relative scene-RGB error was `1.93084e-5`; this is a result on the tested domain, not a universal bound. Alternative reconstructions changed trajectories without establishing a useful artistic advantage missing from compact v1. The decision was to **keep current Density and Strip**, not replace them with a slow per-pixel renderer. Broad spectral expansion is closed; further work requires a concrete observed failure. [Full report and limitations](docs/FULL_SPECTRAL_COMPLETION.md).

## What is validated, and what remains open

| Property | Evidence / limitation |
|---|---|
| Default identity and alpha | Exact bypass and separate alpha/neutral invariants; known interpretation remains required |
| Mathematics | Independent Colour/OCIO references, signed/HDR and exposure sweeps, cross-gamut stimuli, overlap permutations, compound stacks and spectral held-out checks |
| Exposure | Linear matrices/exposure are equivariant; Base/Tone/Crossover and selected/protected Density are conditioned; encoded channel operations generally are not equivariant |
| Gamut | Colorimetric operations are tested through equivalent XYZ; raw channel/matrix operations intentionally depend on working primaries |
| 0.33 regression | Seven CPU/runtime/presentation suites passed; all twelve parameter inventories preserved; 36 accepted Base/Palette/Material cases over signed/HDR/neutral samples stayed bit-identical |
| Nuke runtime | The systemic Output-acquisition failure is closed by the accepted shared correction; Output ownership precedes timed snapshot construction. Trace stays opt-in. |
| Nuke presentation | Direct family/matrix links, animation, copy/paste, rename and save/reload smoke passed; full continuous mouse acceptance across every secondary page remains incomplete |
| Artist usefulness | Positive grading feedback; broader predictability, speed, cross-content and Material advantage over simple baselines remain explicit gates |
| GPU / other hosts | Shared-equation offline Metal validation exists; host Metal rendering remains disabled. Flame presentation/production validation remain pending. |

Initial conversion tolerance is `2e-6 + 2e-5 × abs(reference)`; signed cancellation also has a documented vector-scale bound. Offline Metal starts at `5e-6 + 5e-5 × abs(CPU)`, with an explicit cancellation-conditioned amendment and retained strict failure counts. CPU float32 is authoritative, with double setup where appropriate; fast math and multiply/add contraction are disabled. Tolerances do not substitute for artist or semantic acceptance. [Numerical policy](docs/NUMERICS.md).

Known creative limits include Volume folds, strong signed-boundary conditioning, spectral residual dominance, positive-only look domains, forward singular matrices, historical Primaries reversal and finite-float overflow. No claim of universal invertibility, physical reconstruction accuracy, or real-time HD/4K/8K performance is made.

## Build, install and evaluate

Target: macOS arm64, C++17, CMake 3.20+, Apple build tools. The pinned research environment uses Python 3.14; the native OFX pixel runtime has no Python dependency. Nuke uses its own Python for presentation and the OCIO interpretation bridge. ASWF OpenFX headers are pinned in `third_party/openfx`.

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r research/requirements-lock.txt
cmake -S . -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_OSX_ARCHITECTURES=arm64 -DPython_EXECUTABLE="$PWD/.venv/bin/python"
cmake --build build -j 6
ctest --test-dir build --output-on-failure
```

The optional offline Metal validator requires Xcode's Metal compiler/device support. For a CPU-only build, pass `-DRENDITION_BUILD_METAL_VALIDATOR=OFF`. `-DRENDITION_BUILD_PYTHON=OFF` disables the headless research evaluator; native contract tests still build.

The ad-hoc-signed local development bundle is `build/Rendition.ofx.bundle`. Distribution signing is separate. Install the current-user bundle/startup registration, then restart Nuke:

```sh
python3 tools/install_nuke.py
```

The Nuke menu exposes **Rendition → Base, Palette, Material, Inspector**, plus **Rendition → Advanced** for the original tools. The installer preserves existing startup text and adds one named registration block. `--integration-only` refreshes presentation files without replacing the native library. Generated examples/reports under `build/` require local generation and any explicitly selected external OCIO/view configuration; they are not portable bundled DRTs.

For developers and reference evaluation:

```sh
# Export authoritative interfaces and verify/regenerate presentation metadata.
PYTHONPATH=build .venv/bin/python tools/export_schema.py
.venv/bin/python tools/generate_presentation.py --check

# Headless CPU evaluation of JSON samples or float32 RGBA .npy images.
PYTHONPATH=build .venv/bin/python tools/evaluate.py examples/scene.json

# Focused host smoke; run inside licensed Nuke, not ordinary Python.
# OFX_PLUGIN_PATH=build Nuke17.0 -ti tools/nuke_architecture033.py
```

Existing offline investigations can be reproduced from the [research directory](research/README.md). Reproducing a report does not authorize new broad model research or change a saved grade. Benchmark tools measure their stated CPU/GPU scopes, not guaranteed interactive host performance.

## Architecture, documentation and provenance

```text
Rendition Core            equations, operators and evaluated snapshots
Persistent OFX State      real parameters, animation, save/reload and compatibility
Host Presentation         declarative layout/dependencies and direct linked editors
```

Render ordering remains **context → Output acquisition/ownership → timed parameters → immutable snapshot → inputs → processing**. Presentation refresh only changes editor properties/link targets/status text; it never writes grading values or controls rendered mathematics. The schema lives in `presentation/control_system.json`; generated C++ and Nuke artifacts are checked for drift.

| Reference | What it contains |
|---|---|
| [Canonical 0.32 control system](docs/RENDITION_CONTROL_SYSTEM_0_32.md) | Every control ID/default/range, Main–Expert mapping, dependencies, domain and compatibility contract; UX postmortem |
| [0.33 architecture](docs/RENDITION_ARCHITECTURE_0_33.md) | Layer ownership, declarative schema, retained behaviour and regression evidence |
| [Operator designs](docs/design/) | Per-node semantics, exposure, signed/HDR handling, invariants and known failures |
| [0.31 restoration report](docs/ARTIST_CONTROL_RESTORATION_0_31.md) / [0.32 UX report](docs/NUKE_UX_0.32.md) | Control access, mappings, interaction safety and host presentation findings |
| [Runtime correction](docs/OFX_OUTPUT_ACQUISITION_FIX.md) | Accepted Output-first correction and controlled Nuke evidence |
| [Pipeline contract](docs/PIPELINE_CONTRACT.md) | Rendition/Pigment/SpektraFilm/DRT boundaries |
| [Full Spectral completion](docs/FULL_SPECTRAL_COMPLETION.md) | Oracle comparison, retained compact models and limitations |
| [Host behaviour](HOST_BEHAVIOR.md) / [gate history](docs/GATES.md) | Host differences and dated acceptance records; older next-phase notes are superseded by the current presets pause |
| [Third-party references](THIRD_PARTY_REFERENCES.md) / [spectral data sources](SPECTRAL_DATA_SOURCES.md) | Pins, attribution, datasets, reviewed/reused material and provenance |

The project does not currently declare a redistribution license; the licensing decision remains open. Third-party dependencies/data retain their own licenses and attribution obligations. Commercial grading systems are behavioural/UI references, not copied implementations. Sharing this guide does not turn the candidate into a production-certified release.

The guiding requirement is **explicit semantics + validated mathematics + useful artist behaviour**. Future architecture/UI work should preserve the current rendered look unless a specific processing defect is demonstrated, and historical saved grades must remain reproducible.
