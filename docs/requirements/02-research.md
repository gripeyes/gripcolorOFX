# Research and Open-Source Reference Requirements

Before inventing color mathematics, study the following references.

The implementation must distinguish between:

1. normative/reference mathematics that may be reused subject to its license,
2. scientific papers used to understand or validate behavior,
3. creative open-source implementations used only as architectural inspiration.

Do not blindly copy algorithms merely because an implementation exists.

Every significant mathematical component introduced into the suite must document its origin, derivation, or independent design rationale.

## Tier A: Normative / Foundational Open-Source References

### OpenColorIO

Repository:
`AcademySoftwareFoundation/OpenColorIO`

Use as the primary reference for:

- logarithmic transfer functions,
- LogAffineTransform,
- LogCameraTransform,
- matrix transforms,
- ranges,
- 1D/3D LUT evaluation,
- color-space processor architecture,
- CPU/GPU consistency expectations.

In particular, study `LogCameraTransform` before designing LookLog.

LookLog should not be invented from arbitrary constants if an established generalized mathematical formulation can provide the required behavior.

OpenColorIO is BSD-3-Clause.

### Colour Science for Python

Repository:
`colour-science/colour`

Use as the independent numerical reference implementation for:

- RGB ↔ XYZ,
- RGB colourspace definitions,
- chromatic adaptation,
- Von Kries / Bradford / CAT16,
- IPT,
- CAM16 and CAM16-UCS,
- JzAzBz,
- Hellwig colour appearance models where available,
- colour-volume analysis,
- log functions,
- colour-difference calculations.

Do not ship Python as part of the OFX runtime.

Instead, use Colour in offline Python validation scripts to generate golden/reference values against which the C++ implementation is tested.

Colour is BSD-3-Clause.

### ACES 2.0 Core

Repository:
`aces-aswf/aces-core`

Study the current ACES 2.x implementation, particularly:

- tonescale,
- chroma compression,
- gamut compression,
- colour-space matrices,
- chromatic adaptation,
- perceptual JMh processing,
- forward/inverse design,
- numerical robustness.

Do not reproduce ACES as the application's look.

The goal is to learn how a modern production rendering transform separates:

- lightness,
- chroma/colorfulness,
- hue,
- gamut boundary handling,
- tone compression.

ACES Core is Apache-2.0.

### ASWF OpenFX

Repository:
`AcademySoftwareFoundation/openfx`

Use as the authoritative OFX API and build reference.

Study:

- support library,
- example plugins,
- filter context,
- parameter declaration,
- multithreaded CPU render paths,
- host capability detection,
- OpenFX GPU render extensions,
- Metal support,
- image and color metadata.

Do not base production architecture on undocumented host-specific behavior when an OFX-standard mechanism exists.

## Tier B: Scientific References for Colour Coordinates

### IPT

Study:

Ebner & Fairchild:
“Development and Testing of a Color Space (IPT) with Improved Hue Uniformity”

and Ebner's thesis:

“Derivation and Modelling Hue Uniformity and Development of the IPT Color Space”

Purpose:

IPT must be treated as a serious candidate internal coordinate system for `Rendition Volume`.

Its value is specifically its improved constant-hue behavior relative to simpler spaces.

Implement IPT in the research harness even if it is not ultimately selected for production.

### Hue-linearized gamut mapping

Study:

Braun, Fairchild & Ebner:
“Color Gamut Mapping in a Hue-Linearized CIELAB Color Space”

Purpose:

Understand why constant mathematical hue angle does not necessarily imply constant perceived hue.

Use this as a warning against naïvely implementing a cylindrical Lab, HSV, HSL, or arbitrary opponent-space hue control.

### JzAzBz

Study:

Safdar et al.:
“Perceptually uniform color space for image signals including high dynamic range and wide gamut”

Purpose:

Implement JzAzBz in the research/validation harness as another candidate coordinate system for:

- hue trajectories,
- chroma/density manipulation,
- HDR/WCG behavior,
- perceptual distances.

Do not assume it is automatically superior to IPT or CAM-based spaces.

Evaluate it.

### CAM16 / Hellwig-style JMh

Study the current literature and the open implementations in Colour and ACES 2.0.

Purpose:

Evaluate JMh-style coordinates for operations where explicit lightness, colorfulness and hue separation is beneficial.

This is especially important for:

- Density,
- Color Volume,
- gamut handling,
- perceptually meaningful chroma compression.

## Tier C: Open Creative Implementations

### OpenDRT

Repository:
`jedypod/open-display-transform`

Use OpenDRT as an architectural and behavioral reference for:

- picture formation,
- tonescale design,
- chroma treatment,
- gamut handling,
- creative look modules,
- RGB-ratio versus per-channel processing,
- robustness across large scene-linear ranges.

IMPORTANT:

OpenDRT is GPLv3.

Do not copy OpenDRT source code into this project unless the project intentionally adopts a GPL-compatible licensing strategy.

Study concepts, diagrams, behavior and openly discussed techniques.

For foundational implementation math, prefer permissively licensed references such as OpenColorIO, Colour and ACES Core.

### gamut-compress

Repository:
`jedypod/gamut-compress`

Study as a reference for:

- gamut compression geometry,
- threshold/limit behavior,
- hue/chromaticity consequences,
- invertibility considerations,
- scene-referred gamut compression.

Again inspect the repository license before incorporating any implementation.

Use it primarily to understand failure modes and design alternatives.

### OpenDRT OFX ports

Study existing community OFX ports of OpenDRT as architectural references for:

- macOS ARM64 packaging,
- CPU fallback,
- Metal execution,
- shared colour-core design,
- CMake structure,
- host testing.

Do not copy GPL-derived processing code into an incompatibly licensed project.

The value here is understanding the practical host/build architecture.

## Research Requirement for LookLog

Before finalizing LookLog, implement offline comparisons against:

- pure log2,
- ACEScct,
- ARRI LogC4,
- DaVinci Intermediate,
- the proposed custom LookLog.

Compare:

- code value versus exposure stops,
- middle-gray location,
- negative-value behavior,
- behavior around zero,
- first derivative,
- highlight range,
- invertibility,
- floating-point round-trip error,
- behavior of Tone and Crossover operators in each domain.

The custom LookLog must only survive if it demonstrates a useful reason to exist.

Do not create a proprietary encoding merely for the sake of having one.

If an existing generalized encoding provides equivalent behavior without importing inappropriate gamut or camera assumptions, prefer the simpler solution.

## Research Requirement for Rendition Volume

Do not choose the production colour coordinate system in advance.

Prototype and compare at least:

- IPT,
- JzAzBz,
- CAM16-UCS or a suitable JMh representation,
- a simpler custom opponent space,
- optionally Oklab for comparison.

Generate structured tests containing:

- full hue circles at multiple exposures,
- chroma ramps,
- exposure ramps,
- Rec.2020 primaries and secondaries,
- Macbeth/reference colors,
- highly saturated blues, cyans, magentas and reds,
- skin-tone trajectories.

For each candidate system, evaluate:

- hue stability,
- neutral stability,
- smoothness,
- reversibility,
- behavior outside display gamut,
- behavior on negative scene-linear values,
- computational cost,
- artistic controllability.

Do not select a space solely because it is described as perceptually uniform.

## Research Requirement for Density

There is no assumed canonical Density algorithm.

Density must be treated as original research.

Investigate whether useful behavior can be expressed using combinations of:

- lightness/intensity,
- chroma or colorfulness,
- hue,
- RGB ratios,
- logarithmic exposure,
- subtractive-style relationships.

The operator must be validated against explicit intended behaviors.

Examples:

A saturated dark cyan should be capable of becoming a deep blue-black without merely becoming grey.

A warm brown should be capable of becoming dense bronze.

A dark green should be capable of becoming olive while retaining controlled chromatic identity.

Develop several candidate formulations and compare them visually and numerically.

Do not use vague labels such as “film density” to justify unexplained math.

## Research Requirement for Crosstalk

Start from explicit linear algebra.

Implement:

`RGB_out = M × RGB_in`

and derive constrained versions mathematically.

At minimum test:

- unrestricted matrix,
- row-sum constrained neutral preservation,
- scene-linear processing,
- LookLog processing.

Prove the neutral-preservation invariant numerically.

Do not infer channel crosstalk behavior from proprietary commercial plug-ins.

## Research Requirement for Strip

Treat historical multi-strip processes as conceptual inspiration, not a claim of physical simulation.

Research:

- additive versus subtractive color reproduction,
- dye-density relationships,
- separation matrices,
- channel leakage/crosstalk,
- recombination.

The first production implementation may be an abstract separation/recombination model rather than a physical Technicolor model.

Do not advertise it as a Technicolor simulation unless future work is based on measured historical material and a validated physical model.

## Inspector / Validation Harness

Before polishing creative UI, build an external Python research harness using Colour Science.

It must be capable of:

- evaluating the C++ reference math against Python references,
- generating exposure sweeps,
- generating hue/chroma sweeps,
- plotting neutral axes,
- plotting trajectories through candidate opponent spaces,
- measuring round-trip errors,
- detecting clipping,
- detecting NaN/Inf,
- comparing candidate internal domains.

Use generated structured tests before evaluating photographic hero images.

The rule is:

Do not accept an operator merely because it makes three photographs look attractive.

Understand what it does to the colour volume.

## Licensing

Maintain `THIRD_PARTY_REFERENCES.md`.

For every external implementation consulted, record:

- project,
- repository,
- license,
- files or concepts studied,
- whether implementation code was reused,
- resulting attribution obligations.

Prefer permissively licensed foundational implementations.

Do not accidentally introduce GPL-derived code into an otherwise permissively licensed core.

## Final Research Principle

The suite should not be designed by imitating the controls of existing commercial grading products.

Commercial tools may identify useful artistic problems.

Scientific literature and transparent reference implementations should inform the mathematics.

Our implementation should then solve those problems independently, explicitly, and testably.