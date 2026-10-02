# Spectral Research Extension

This document extends the main Color Rendition OFX Suite brief.

The purpose of spectral processing in this project is NOT to convert the entire grading pipeline into a spectral pipeline.

Spectral methods are to be researched and used selectively where wavelength-dependent material/reproduction behaviour provides capabilities that RGB or perceptual-coordinate manipulation cannot express cleanly.

Primary targets:

1. Density / subtractive colour behaviour
2. Dye and pigment interaction
3. Strip / separation / recombination
4. Film-layer-inspired colour reproduction
5. Development of physically informed RGB approximations

Spectral processing must remain compatible with the project's primary external contract:

`scene-linear RGB in → scene-linear RGB out`

unless an explicitly named research mode states otherwise.

---

# 1. Fundamental semantic rule

Do not confuse:

- spectral representation,
- scene-referred RGB,
- linear numerical encoding,
- display-referred RGB,
- rendered appearance,
- display encoding.

These are separate concepts.

A spectral operator does not inherently constitute a display transform.

The default processing architecture is:

```text
Scene-linear RGB
        ↓
spectral reconstruction / spectral basis
        ↓
spectral operation
        ↓
CIE XYZ integration
        ↓
original scene-linear RGB working space
        ↓
continue image processing
```

No DRT, ODT, EOTF, OETF, display gamma, gamut mapping or output encoding is applied.

For the primary workflow:

```text
IN  = Linear Rec.2020
OUT = Linear Rec.2020
```

Values may remain:

- negative,
- above 1.0,
- HDR,
- unclamped.

Do not normalize to 0–1 merely because spectral reflectance or transmittance calculations contain bounded quantities internally.

---

# 2. Linear encoding is not automatically scene-referred

The implementation must explicitly track semantic meaning.

For example:

```text
physical print simulation
→ reflected spectrum
→ XYZ
→ Linear Rec.2020
```

produces linear RGB numbers.

However, these numbers describe a rendered print appearance, not the original scene radiance.

Therefore:

`linear numerical representation ≠ scene-referred semantics`

The software and documentation must distinguish at minimum:

### Scene-referred linear

Represents quantities proportional to scene light or a scene-referred working representation.

### Appearance/rendered linear

Linear XYZ/RGB representation of a rendered or viewed appearance.

### Display-encoded

Values encoded for a specific display signal such as sRGB, Rec.709, PQ, HLG, etc.

Never relabel appearance-referred values as scene-referred merely because they were converted back into linear RGB.

---

# 3. Two spectral operating modes

Research two conceptually different modes.

## Mode A: Spectral Rendition

This is the production-oriented mode.

Goal:

Use physical/spectral models to derive useful colour relationships while preserving the surrounding scene-referred pipeline.

Architecture:

```text
Scene-linear RGB
        ↓
spectral reconstruction or parameterization
        ↓
material / dye / pigment model
        ↓
spectral result
        ↓
XYZ
        ↓
derive rendition transformation
        ↓
scene-linear RGB
```

The result must behave as a creative scene-referred look operator suitable for continued processing.

Use cases:

- Density
- subtractive chroma behaviour
- dye interaction
- three-strip-inspired palette formation
- controlled colourant crosstalk

This is the default research priority.

## Mode B: Physical Reproduction

This is an experimental/reference mode.

Goal:

Model a complete physical reproduction or viewing process.

Examples:

```text
scene
→ negative film
→ developed dyes
→ print stock
→ projection/viewing illuminant
→ observer
→ XYZ
```

or:

```text
scene
→ pigment surface
→ illuminant
→ reflected spectrum
→ observer
→ XYZ
```

Such outputs are rendered/appearance-referred.

They may be stored numerically as linear XYZ or linear RGB, but they must NOT be described as scene-referred.

This mode is primarily for:

- research,
- validation,
- generating targets,
- fitting faster production models,
- possible future DRT/print-emulation work.

Do not silently insert Mode B behaviour into the Color Rendition suite.

---

# 4. Spectral reconstruction from RGB

RGB does not uniquely define a physical spectrum.

Many spectra can produce the same tristimulus values.

Therefore spectral reconstruction from RGB must always be described as constructing:

`a plausible representative spectrum`

not:

`recovering the original spectrum`.

Never claim that an RGB input contains enough information to uniquely reconstruct the physical spectrum that generated it.

Research several reconstruction methods.

At minimum study:

- Jakob & Hanika smooth RGB-to-spectrum reconstruction
- methods used in PBRT
- methods used in Mitsuba
- Colour Science spectral recovery implementations
- low-dimensional spectral basis methods

Evaluate:

- accuracy of RGB round-trip,
- smoothness,
- behaviour outside standard gamut,
- negative RGB handling,
- computational cost,
- suitability for reflectance,
- suitability for emission,
- suitability for transmission/dyes.

Do not use the same spectral reconstruction blindly for:

- reflective pigments,
- transmissive dyes,
- emissive sources.

These have different physical constraints.

---

# 5. Reflectance vs transmittance vs emission

Represent these separately.

## Reflectance spectra

Typical range:

`0 ≤ R(λ) ≤ 1`

Used for:

- pigments,
- paint,
- paper,
- reflective surfaces.

## Transmittance spectra

Typical range:

`0 ≤ T(λ) ≤ 1`

Used for:

- photographic dyes,
- filters,
- transparent layers.

## Spectral density / absorbance

Represent photographic dye density where appropriate using:

```text
D(λ) = -log10(T(λ))
```

or an equivalent explicitly documented convention.

## Emission / radiance spectra

Not intrinsically bounded to 1.

Used for:

- lights,
- emissive displays,
- scene illumination.

Never treat an arbitrary RGB triplet as reflectance without an explicit conversion model and stated assumption.

---

# 6. Beer–Lambert research

Use Beer–Lambert-style absorption as the primary starting model for transparent dye layers.

Relevant applications:

- film dyes,
- transparent filters,
- three-layer colour systems,
- print dyes where scattering is negligible or intentionally ignored.

Conceptual model:

```text
T(λ) = exp(-α(λ) · c · l)
```

or, in density form:

```text
D(λ) = Σ ci · Di(λ)
T(λ) = 10^(-D(λ))
```

Research:

- cyan-like dye spectral density,
- magenta-like dye spectral density,
- yellow-like dye spectral density,
- imperfect dye isolation,
- broad absorption tails,
- cross-channel contamination,
- concentration nonlinearity,
- layer-order effects where relevant.

Use this as the primary physical basis for `Rendition Strip`.

Do not assume ideal CMY dyes.

Perfect complementary dyes are unlikely to generate the interesting palette behaviour desired.

Imperfect dye overlap and leakage may be artistically more important.

---

# 7. Kubelka–Munk research

Use Kubelka–Munk for reflective/scattering material behaviour.

Research:

- absorption coefficient K(λ),
- scattering coefficient S(λ),
- K/S relationships,
- pigment concentration,
- mixtures,
- finite vs effectively infinite layer thickness,
- substrate influence.

Primary target:

`Rendition Density`

Questions:

- How do real pigment trajectories move through hue/chroma/lightness as concentration increases?
- Which behaviours can be approximated cheaply in RGB/opponent coordinates?
- What gives the perceptual impression of "deeper" colour rather than merely "darker" colour?

Do not automatically run Kubelka–Munk per pixel in the final OFX.

First use it as a reference model.

---

# 8. Spectral Density research

Density is currently an intentionally open research problem.

Build spectral experiments for at least:

- cyan/blue pigment families,
- green/olive families,
- red/brown/bronze families,
- yellow/orange families,
- magenta/purple families.

For each family, sweep:

- concentration,
- scattering,
- absorption,
- mixture ratio,
- illuminant where relevant.

Convert resulting spectra to XYZ and then to working RGB.

Measure trajectories in:

- linear RGB,
- LookLog,
- IPT,
- Oklab,
- JzAzBz,
- suitable JMh representation.

Extract:

- hue trajectory,
- chroma trajectory,
- luminance/lightness trajectory,
- perceived brightness trajectory where practical.

The aim is to determine whether a fast analytic operator can reproduce characteristic spectral trajectories.

Potential production architecture:

```text
spectral reference model
        ↓
large generated dataset
        ↓
fit analytic RGB/opponent model
        ↓
Rendition Density production node
```

Possible approximation families:

- low-order polynomials,
- rational functions,
- splines,
- compact basis transforms,
- small LUTs,
- hybrid analytic + LUT approaches.

Prefer explicit and inspectable fits over opaque ML unless ML demonstrates a substantial advantage.

---

# 9. Rendition Strip spectral research

Treat `Strip` as a broad colour reproduction system rather than a literal Technicolor simulation.

Initial physical research model:

```text
Scene-linear RGB
        ↓
spectral reconstruction
        ↓
virtual separation records
        ↓
three colourant/dye channels
        ↓
spectral density / transmittance interaction
        ↓
recombination
        ↓
XYZ
        ↓
working RGB
```

Research controls corresponding conceptually to:

- separation purity,
- channel overlap,
- cyan density,
- magenta density,
- yellow density,
- cross-channel leakage,
- layer bias,
- colourant concentration,
- recombination weighting,
- neutral anchor,
- red/skin anchor,
- overall density.

Do not call these historical Technicolor parameters unless historically validated.

The production tool may expose more abstract controls such as:

- Separation
- Crosstalk
- Dye Density
- Palette Compression
- Leakage
- Warm/Cool Bias
- Neutral Anchor

while the physical research model remains underneath.

---

# 10. Historical three-strip research

Study actual historical multi-strip and dye-transfer systems where reliable public documentation is available.

Research:

- spectral sensitivities of separation records,
- filter behaviour,
- dye transfer,
- imperfect spectral selectivity,
- print/recombination characteristics,
- density curves,
- channel contamination.

Do not assume a modern RGB → CMY conversion reproduces historical three-strip colour.

Treat PixelTools Three/Strip as a behavioural reference only.

Do not copy or reverse engineer proprietary algorithms.

The aim is to independently understand why separation/recombination systems create distinct palette behaviour.

---

# 11. Neugebauer / Yule–Nielsen research

Research classical multi-colorant reproduction models:

- Neugebauer equations,
- Demichel equations,
- Yule–Nielsen modified Neugebauer,
- cellular Neugebauer variants.

These are not automatically production algorithms for this project.

Use them to study:

- colourant-area combinations,
- nonlinear mixture behaviour,
- interaction between multiple subtractive primaries,
- decomposition and recombination,
- why simple linear RGB mixing cannot reproduce some subtractive behaviours.

Compare their colour trajectories against:

- Beer–Lambert,
- Kubelka–Munk,
- simple matrix mixing,
- opponent-space approximations.

---

# 12. Illuminants and observers

The research harness must support known standard illuminants.

At minimum:

- D65
- D60
- D50
- Illuminant A

Support custom spectral power distributions later.

Use standard CIE colour matching functions.

At minimum test:

- CIE 1931 2° Standard Observer.

Optionally investigate modern observer functions where useful, but do not complicate the first implementation unnecessarily.

For creative scene-referred modes, illuminant changes should not accidentally become hidden white-balance transforms.

White-point handling must be explicit.

---

# 13. Spectral integration

Implement high-quality numerical spectral integration.

Research suitable wavelength intervals.

Initial reference implementation may use approximately:

- 360–830 nm,
- 1–5 nm reference spacing.

Production GPU experimentation may use substantially fewer samples if validated.

Potential optimization paths:

- fixed wavelength quadrature,
- basis spectra,
- low-dimensional parameterizations,
- importance-selected wavelength samples,
- Jakob–Hanika-style parametric spectra.

Do not reduce wavelength count until error is measured.

Compare resulting XYZ values against a high-resolution reference.

---

# 14. Scene-linear return transform

The default spectral operator must return to the same scene-linear working gamut as its input.

Example:

```text
Linear Rec.2020
      ↓
spectral operation
      ↓
XYZ
      ↓
Linear Rec.2020
```

Do not apply:

- tone mapping,
- display rendering,
- gamut clipping,
- output encoding,
- display gamma.

Out-of-gamut scene-linear RGB results are permitted.

Do not automatically compress them unless the user enables an explicit gamut operation.

Negative RGB values resulting from XYZ → RGB conversion must remain available unless mathematically unsafe for a following stage.

---

# 15. Scene-referred rendition fitting

Physical spectral simulation frequently produces appearance-referred behaviour.

When converting this into a production `Rendition` operator, do not simply relabel those values as scene-referred.

Instead derive a scene-referred colour transformation whose trajectories reproduce the desired relationship.

Research methods such as:

```text
Input scene RGB
→ spectral reference result
→ compare relative colour relationships
→ fit scene-referred transformation
```

The fitted operator should preserve useful properties such as:

- exposure scalability where desired,
- HDR headroom,
- neutral behaviour,
- smooth trajectories,
- no hidden clipping,
- continuous hue relationships.

Document clearly which physical properties survive the fitting process and which do not.

---

# 16. Spectral Lab

Add an offline `Spectral Lab` research application or Python harness.

This does not need to ship as the initial OFX.

Capabilities:

## Spectrum display

Plot:

- reflectance,
- transmittance,
- absorbance/density,
- illuminant SPD,
- resulting stimulus spectrum.

## RGB reconstruction comparison

Compare spectral reconstruction algorithms for the same RGB input.

## Material models

Support:

- Beer–Lambert dyes,
- Kubelka–Munk pigments,
- simple reflective spectra,
- arbitrary measured spectra.

## Colourant mixing

Interactive or scripted sweeps over:

- concentration,
- layer density,
- mixture proportions,
- channel leakage,
- separation weights.

## Colour-space trajectories

Plot generated results in:

- xyY,
- u'v',
- IPT,
- Oklab,
- JzAzBz,
- JMh where available.

## Dataset generation

Export structured datasets suitable for fitting fast production operators.

## Validation

Compare low-resolution production spectral calculations with high-resolution reference integration.

---

# 17. Measured spectral data

Where legally available, prefer real measured spectra over arbitrary synthetic curves.

Potential useful datasets:

- colour checker reflectances,
- Munsell reflectance spectra,
- pigment reflectances,
- filter transmission spectra,
- photographic dye density curves,
- illuminant SPDs.

Record source and license for every dataset.

Do not package proprietary spectral measurements without permission.

Maintain:

`SPECTRAL_DATA_SOURCES.md`

containing:

- dataset name,
- source,
- license,
- spectral range,
- sampling interval,
- intended use.

---

# 18. Open-source references

Study open implementations including:

### Colour Science for Python

Use for:

- spectral distributions,
- spectral interpolation,
- CMFs,
- illuminants,
- RGB ↔ XYZ,
- spectral → XYZ,
- colour appearance analysis.

Use Colour as the primary independent Python reference implementation.

### PBRT

Study its spectral rendering architecture and RGB-to-spectrum handling.

Focus on:

- compact spectral representations,
- RGB spectrum reconstruction,
- wavelength sampling,
- numerical integration.

### Mitsuba

Study current spectral-mode architecture and RGB-to-spectrum parameterization.

### Jakob & Hanika

Study:

“A Low-Dimensional Function Space for Efficient Spectral Upsampling”

Use as a major reference for compact RGB-to-spectrum reconstruction.

### Open spectral / pigment implementations

Study available Kubelka–Munk and pigment-mixing projects subject to license review.

Do not import unknown code directly into production.

---

# 19. Commercial behavioural references

Use the following only to identify useful artist-facing problems:

- PixelTools Three/Strip
- MonoNodes density / colour-shift tools
- FilmLight Chromogen
- FilmLight X Grade
- FilmLight Base Grade
- commercial film-emulation products where spectral claims are publicly documented

Do not reverse engineer protected implementations.

Our mathematics must be independently derived from open literature, open implementations and our own research.

---

# 20. Fast production approximation

The preferred long-term architecture is:

```text
HIGH-FIDELITY RESEARCH

Spectral model
      ↓
generated dataset
      ↓
analysis / fitting

FAST PRODUCTION

RGB/opponent analytic approximation
or
compact LUT/basis representation
```

The spectral reference model remains available for:

- comparison,
- validation,
- regeneration,
- future refinement.

Do not force real-time spectral calculation where a validated approximation is perceptually indistinguishable.

---

# 21. Optional true spectral production mode

Only after fast models are successful, investigate actual GPU spectral processing.

Potential Metal architecture:

```text
RGB
↓
compact spectral coefficients
↓
evaluate N wavelength samples
↓
spectral operation
↓
XYZ accumulation
↓
RGB
```

Research 8, 12, 16, 24 and higher wavelength counts.

Always compare against the high-resolution CPU reference.

The minimum acceptable wavelength count is determined by measured error, not performance preference.

CPU remains authoritative.

---

# 22. Spectral validation tests

Create test cases for:

### Identity

RGB → spectrum → XYZ → RGB should reproduce target RGB within defined tolerances where reconstruction is designed to do so.

### Neutral axis

Neutral inputs should remain neutral under neutral configurations.

### Concentration monotonicity

Increasing pigment/dye concentration should produce predictable continuous trajectories.

### Layer continuity

No discontinuities when dye density or mixture weights are animated.

### Illuminant sensitivity

Physical reproduction mode should respond plausibly to illuminant changes.

Scene-referred rendition mode should not accidentally introduce unwanted viewing-condition dependence.

### Extreme colour

Test:

- saturated Rec.2020 primaries,
- bright HDR values,
- dark saturated colours,
- near-black values,
- values above 1,
- negative RGB input.

### CPU / Metal parity

If GPU spectral processing is implemented, validate against CPU reference.

---

# 23. Handling negative RGB

Spectral reconstruction of negative scene-linear RGB values is physically undefined in the direct sense.

Do not clamp them silently.

Research strategies including:

- separate signed residual representation,
- base-positive-spectrum + linear residual,
- process positive spectral component while preserving negative residual,
- bypass spectral contribution smoothly near problematic regions.

Document chosen behaviour.

Negative RGB preservation is required for compositing-grade robustness.

This is a research problem and must not be hidden behind `max(rgb, 0)` without justification.

---

# 24. HDR scale behaviour

Spectral reconstruction algorithms often assume normalized reflectance-like RGB inputs.

Our inputs may contain HDR scene values well above 1.

Separate:

```text
chromatic shape
×
radiometric / exposure scale
```

where possible.

For example:

```text
RGB = scale × normalized_chromatic_component
```

Reconstruct the chromatic spectrum independently from the scene exposure scale, then reapply radiometric scaling where physically/mathematically appropriate.

This avoids rebuilding a different spectral shape solely because exposure changed.

Verify exposure scalability explicitly.

---

# 25. Spectral Density design goal

The production Density operator should ultimately answer:

> How does colour gain or lose perceived material depth while preserving intentional hue identity?

Do not equate Density with:

- saturation,
- gamma,
- RGB multiplication,
- subtractive preset,
- simple luminance reduction.

Use spectral models to discover useful trajectories and then expose artist-friendly controls.

Target examples:

```text
cyan
→ dense cyan
→ blue-cyan
→ blue-black
```

```text
green
→ dense forest green
→ olive
```

```text
orange/brown
→ bronze
→ deep warm brown
```

with continuous controllable behaviour.

---

# 26. Spectral Strip design goal

The Strip operator should answer:

> What happens when the image is reproduced through a deliberately imperfect multi-channel colourant system?

Target behaviours:

- broad palette separation,
- coherent channel interaction,
- controlled cyan/magenta/yellow contamination,
- red/skin anchoring,
- colourant leakage,
- density-driven hue evolution,
- palette compression or expansion,
- reproduction-like colour relationships.

Do not reduce Strip to:

```text
3×3 matrix + saturation
```

unless research demonstrates that a matrix approximation genuinely captures the desired result.

---

# 27. Relationship to the DRT

The DRT remains downstream and separate.

Recommended production pipeline:

```text
Scene-linear CG / photography
        ↓
Rendition Scene
        ↓
Tone
        ↓
Volume
        ↓
Density
        ↓
Crossover
        ↓
Crosstalk / Strip
        ↓
Pigment
        ↓
Optical / film characteristics
        ↓
Authored DRT
        ↓
Display
```

A spectral rendition node must not silently perform DRT responsibilities.

Conversely, a future spectral physical-print DRT may be researched separately.

Do not merge the two projects prematurely.

---

# 28. Inspector spectral additions

Extend `Rendition Inspector` with optional spectral diagnostics.

Potential modes:

- source representative spectrum,
- modified spectrum,
- spectral difference,
- dye density curves,
- reflectance/transmittance graph,
- XYZ result,
- metamer comparison,
- illuminant comparison,
- spectral reconstruction comparison.

This is primarily a development/advanced-user feature.

---

# 29. Phase plan

## Spectral Phase S0: Infrastructure

Implement:

- spectral distribution class,
- wavelength grid,
- CMFs,
- standard illuminants,
- XYZ integration,
- spectral interpolation,
- Python reference tests.

## Spectral Phase S1: RGB reconstruction

Implement and compare multiple RGB-to-spectrum strategies.

Establish:

- SDR behaviour,
- HDR scale handling,
- negative-value strategy,
- round-trip behaviour.

## Spectral Phase S2: Beer–Lambert

Build transparent dye model.

Generate synthetic CMY systems.

Visualize palette trajectories.

## Spectral Phase S3: Kubelka–Munk

Build reflective pigment model.

Generate concentration/mixing trajectories.

Use results to inform Density.

## Spectral Phase S4: Density fitting

Fit fast scene-referred RGB/opponent models to selected spectral trajectories.

Compare visually and numerically.

## Spectral Phase S5: Strip reference model

Create multi-dye separation/recombination model.

Experiment with imperfect dyes, leakage and density.

## Spectral Phase S6: Strip fitting

Produce a fast production approximation.

## Spectral Phase S7: optional Metal spectral mode

Only begin after the visual value of actual runtime spectral calculation is demonstrated.

---

# 30. Non-goals

Do not:

- convert the entire project to spectral processing,
- claim RGB spectra are uniquely recoverable,
- claim spectral automatically means physically accurate,
- silently clamp negative values,
- bake display transforms into spectral rendition nodes,
- reproduce proprietary film stocks without measurements,
- claim Technicolor accuracy without historical measurement data,
- run expensive spectral math purely because it sounds sophisticated,
- replace useful RGB/opponent processing where spectral adds no benefit.

---

# 31. Primary decision criterion

For every proposed spectral component, answer:

> Does spectral modelling provide a meaningful behaviour that cannot be represented as clearly, controllably or robustly using ordinary RGB/opponent-space processing?

If the answer is no, use RGB.

If the answer is yes:

1. build a high-quality spectral reference,
2. understand its behaviour,
3. attempt to fit a simpler production model,
4. retain actual spectral runtime only if the approximation materially loses desirable behaviour.

---

# 32. Core philosophy

Spectral processing is a source of physically meaningful behaviour and research data.

It is not a badge of sophistication.

The final system should use the simplest representation that faithfully produces the intended image behaviour.

The preferred pattern is:

```text
physics informs model
        ↓
model informs colour trajectories
        ↓
colour trajectories inform artist controls
        ↓
fast transparent production operator
```

The artist should never need to understand wavelengths merely to make a useful colour adjustment.

But the implementation should be able to explain why the adjustment behaves the way it does.