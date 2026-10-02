# Additional Research Targets and Behavioural References

The following systems should be studied in addition to the foundational scientific/open-source references already listed.

These references fall into two categories:

- **Open/reference implementations**: mathematics and architecture may be studied and, where licensing permits, reused with attribution.
- **Commercial/closed behavioural references**: study the problem definition, control model, UI, examples and qualitative behaviour only. Do not reverse engineer or reproduce proprietary algorithms.

---

## A. FilmLight Baselight

FilmLight should be treated as one of the most important behavioural references for the project.

### Base Grade

Study Baselight Base Grade as a reference for a modern scene-referred primary grading operator.

Relevant ideas:

- exposure-centric rather than legacy Lift/Gamma/Gain-centric design,
- operation across scene-referred dynamic range,
- perceptually meaningful dark / balance / light relationships,
- colour-space-independent artist controls,
- preserving useful scene relationships while still giving intuitive image manipulation.

FilmLight explicitly designed Base Grade to move away from traditional Lift/Gamma/Gain assumptions and toward perception-oriented controls suitable for modern scene-referred imagery.

Our `Rendition Scene` and `Rendition Tone` nodes should be compared against this philosophy.

Do not copy Baselight parameterization.

Questions to investigate:

- Which controls belong in scene-linear math?
- Which controls require a perceptual mapping internally?
- Can one exposure-based control model remain useful across HDR ranges?
- How should pivot and tonal region width behave in stops rather than encoded values?

### X Grade

Study Baselight X Grade closely.

X Grade is particularly relevant to `Rendition Volume`.

Its important conceptual property is the ability to make multiple localized and complex colour modifications without building traditional keys or mattes.

Treat this as a behavioural target for:

- continuous colour-volume selection,
- multiple overlapping colour regions,
- soft multidimensional falloff,
- direct manipulation rather than procedural qualifier construction,
- avoiding hard boundaries between “primary” and “secondary” grading.

Our Volume node should eventually make it possible to sculpt colour regions with similar immediacy while retaining explicit mathematical semantics.

Do not attempt to reproduce FilmLight's proprietary X Grade algorithm.

### Hue Shift

Study Baselight Hue Shift.

Relevant concepts:

- moving colour families toward adjacent hues,
- controlling hue relationships broadly rather than picking exact RGB values,
- separating hue deformation from ordinary saturation,
- maintaining smooth transitions between colour regions.

MonoNodes Color Shift explicitly identifies Baselight Hue Shift as an inspiration, making this useful as the upstream behavioural reference.

### Six Vector

Study Baselight Six Vector as a reference for reduced, intelligible control over principal colour families.

The concept of controlling:

- red,
- yellow,
- green,
- cyan,
- blue,
- magenta

remains useful even if the underlying transformation is continuous.

Consider providing a simplified six-family artist UI over a more general continuous colour-volume engine.

The UI representation and processing model should remain separate.

### Curve Grade in Baselight 6+

Baselight 6 Curve Grade is especially important.

FilmLight describes:

- an extended-range perceptual RGB space for scene-referred RGB curves,
- an Exposure-only curve mode with chromaticity stability,
- Hue / Saturation / Exposure curves derived from a new opponent colour space,
- the same opponent system driving X Grade and Chromogen.

This is extremely close to the architecture desired for this suite.

Research question:

Can our tool use one carefully selected opponent representation across Volume, Density and Crossover, rather than inventing unrelated coordinate systems for every node?

Compare:

- IPT,
- Oklab,
- Hellwig/CAM-derived coordinates,
- ACES 2 JMh,
- a custom opponent representation.

### Chromogen

Study FilmLight Chromogen as a high-level behavioural reference for look development.

Do not assume Chromogen's internal model is known.

Focus on:

- look development as a system rather than a stack of arbitrary grading nodes,
- correlated colour changes,
- palette-level manipulation,
- controlled colour reproduction characteristics,
- separation of look development from display rendering.

Our Color Rendition suite should aspire to the same level of system-level colour authorship while remaining transparent and inspectable.

---

## B. Steve Yedlin Public Work

Study Steve Yedlin's publicly available Display Prep demonstrations and technical writing.

Specific topics:

### Tetra

Study the publicly reconstructed Tetra transformation and its geometry.

Open references include:

- `npeason/Tetra-DCTLOFX`
- `calvinsilly/Tetrahedral-Interpolation`
- related Fusion implementations

These community implementations were independently reconstructed from Yedlin's public demonstrations.

Use them to understand:

- tetrahedral partitioning of RGB/XYZ colour volume,
- primary and secondary anchor manipulation,
- continuous interpolation between anchors,
- constraints that preserve useful geometric relationships.

Do not describe these reconstructions as Yedlin's exact proprietary implementation.

### Cone Coordinates

Yedlin's Cone Coordinates should remain a conceptual reference for:

- manipulating colour regions using purpose-designed coordinates,
- avoiding unintended deformation elsewhere in colour volume,
- evaluating an operation by its global deformation field rather than by a handful of sampled colours.

No exact implementation should be claimed unless publicly documented.

### Transform inspection methodology

Study Yedlin's methodology as seriously as his colour operators.

Important principles:

- inspect the entire transform,
- sample dense colour volumes,
- extract tone behaviour,
- test colour trajectories,
- measure target/source relationships,
- derive transforms from structured data,
- separate spatial film characteristics from per-pixel colour transforms.

This philosophy should strongly influence `Rendition Inspector`.

---

## C. MonoNodes Behavioural Reference Set

Study the following MonoNodes tools as examples of useful artist problems.

Do not copy proprietary implementations.

### Color Shift

Use as a behavioural reference for:

- broad colour-family manipulation,
- spherical versus tetra-like models,
- density and saturation changes tied to colour families.

### Color Shaper

Use as reference for:

`Hue × luminance region → colour deformation`

This maps closely to our multidimensional Volume design.

### Hue Twist / Hue Bend

High-priority behavioural reference.

Study the concept:

`Hue deformation = f(hue, brightness)`

rather than hue as a one-dimensional coordinate.

Our Crossover node should generalize this concept into:

`ΔHue / ΔChroma / ΔDensity = f(Hue, Exposure)`

with smooth continuous trajectories.

### RGB Crosstalk

Study as a compact artist UI for neutral-preserving matrix manipulation.

Underlying processing should remain explicit matrix math in our implementation.

### RGB Split Tone

Study the concept of changing channel relationships differently through toe, midrange and shoulder.

Use this as behavioural inspiration for `Channel Crossover`.

Do not reduce the idea to ordinary shadow/highlight tinting.

### Utility / analysis tools

Study MonoNodes' ramps, clipping diagnostics, isolators and palette tools.

These reinforce the need for `Rendition Inspector`.

---

## D. PixelTools Three/Strip

Study PixelTools Three/Strip as a major behavioural reference for `Rendition Strip`.

Relevant concepts:

- colour separation,
- controlled recombination,
- crosstalk,
- hue rotation,
- density interaction,
- broad palette transformation,
- skin/red anchoring,
- changing the apparent reproduction process rather than grading individual colours.

Do not attempt to reconstruct or reproduce the commercial algorithm.

The key research question is:

Can similar broad palette behaviours emerge from independently designed separation matrices, nonlinear channel-density mappings and controlled recombination?

Our Strip node should remain an abstract colour-reproduction operator unless historical measurements justify a specific physical process claim.

---

## E. Open Tetrahedral Colour Transform References

Study the following open implementations:

### `npeason/Tetra-DCTLOFX`

MIT-licensed community implementation of a tetrahedral transformation inspired by Yedlin's public demonstrations.

### `calvinsilly/Tetrahedral-Interpolation`

Open Nuke implementation and associated research notes.

Particularly useful because the author documents reconstruction assumptions and cites interpolation literature.

### `bobtronic73/free-DCTL`

Includes:

- Tetra Simple,
- normalized colour matrices,
- test ramps,
- basic technical colour utilities.

The simplified Tetra implementation is useful for studying how constraints can reduce parameter count while retaining useful colour-volume deformation.

Do not assume that “Tetra” should automatically become our production Volume model.

Use these implementations as experimental baselines.

---

## F. Oklab / OkLCh / Okhsl / Okhsv

Study Björn Ottosson's Oklab work.

Oklab is explicitly designed for image-processing operations involving:

- perceived lightness,
- chroma,
- hue,
- smooth colour interpolation,
- numerical simplicity,
- scale-independent behaviour.

The original implementation is openly available and intentionally straightforward.

Oklab should be added to the Volume research gate alongside:

- IPT,
- JzAzBz,
- CAM16/JMh,
- Hellwig,
- ACES 2 perceptual coordinates.

Pay particular attention to Ottosson's comparisons.

He notes:

- IPT has excellent hue behaviour but weaker lightness/chroma prediction,
- CAM16-UCS has strong perceptual uniformity but less desirable interpolation/compression behaviour,
- JzAzBz introduces exposure/scale dependencies,
- Oklab is designed specifically as a practical image-processing coordinate system.

Also study Okhsl / Okhsv for artist-facing parameterization.

Do not necessarily use Okhsl/Okhsv internally, but their mapping from perceptual colour geometry into understandable artist controls may inform our UI.

---

## G. HCT / Material Color Utilities

Study Google's open Material Color Utilities and HCT model.

HCT combines:

- CAM16 hue,
- CAM16 chroma,
- perceptual tone based on L*.

It is not intended as a cinematic grading system, but it is useful research for independently controlling:

- hue,
- chroma,
- tone.

The library is open source under Apache 2.0.

Use HCT as another reference when designing artist-facing colour-volume coordinates.

Do not assume UI-design colour requirements directly transfer to scene-referred HDR imagery.

---

## H. Hellwig & Fairchild 2022

Add the Hellwig/Fairchild revisions to colour appearance modelling.

Study:

“Brightness, lightness, colorfulness, and chroma in CIECAM02 and CAM16”

and:

“Extending CIECAM02 and CAM16 for the Helmholtz–Kohlrausch effect”

These papers are valuable for our Density research because perceived brightness is not determined solely by luminance.

Highly chromatic colours can appear brighter through the Helmholtz–Kohlrausch effect.

This matters when designing:

- density,
- chroma-density coupling,
- highlight colour behaviour,
- perceptually stable colour darkening.

The `colour-science/colour` project includes an open implementation of the Hellwig 2022 model.

Add Hellwig to the research harness.

---

## I. Subtractive / Material Colour Research

Our Density and Strip operators should not rely solely on RGB grading intuition.

Research actual subtractive colour systems.

### Kubelka–Munk

Study Kubelka–Munk theory as a model of absorption and scattering in coloured materials.

Relevant concepts:

- absorption,
- scattering,
- concentration,
- nonlinear mixture response,
- spectral colour mixing.

Do NOT run a full Kubelka–Munk spectral simulation per pixel in the initial OFX merely because it is physically interesting.

Instead investigate whether its behavioural relationships suggest better low-dimensional density/chroma models.

Useful references:

- the Colour Science archived `MunsellAndKubelkaMunkToolbox`,
- modern Kubelka–Munk colour-mixing papers.

Potential research experiment:

Generate synthetic mixtures using Kubelka–Munk offline, convert them to RGB / opponent coordinates, and fit simpler RGB-domain approximations to the resulting trajectories.

This could provide a scientifically grounded starting point for “subtractive density” behaviour.

---

## J. Neugebauer / Demichel / Yule–Nielsen

For `Rendition Strip`, research classical colour reproduction models:

- Neugebauer equations,
- Demichel equations,
- Yule–Nielsen modified Neugebauer models,
- cellular Neugebauer variants.

These describe colour reproduction through combinations of subtractive colorants and are especially relevant to our separation/recombination ideas.

We are not reproducing a halftone printer.

The useful conceptual material is:

- decomposition into colourant primaries,
- nonlinear contribution of overlapping primaries,
- recombination behaviour,
- interaction between physical components,
- departure from simple additive RGB mixing.

Use these as inspiration for independently deriving an abstract separation/recombination model.

---

## K. Filmic Blender and AgX

Study Filmic Blender and AgX as historical/open picture-formation references.

### Filmic Blender

Relevant ideas:

- scene-linear input,
- high-dynamic-range tone mapping,
- intensity gamut handling,
- relationship between overexposure and saturation,
- separating a base rendering transform from optional looks.

Do not reproduce Filmic.

### AgX

Study AgX's open OCIO configuration and implementation.

Relevant concepts:

- scene-referred input,
- inset / colour-volume management,
- log-domain working representation,
- tone mapping,
- appearance transforms,
- explicit OCIO architecture.

AgX is useful particularly as a reference for:

`linear → controlled intermediate representation → appearance shaping → display`

It also provides another real example of a deliberately designed internal log representation.

The project should compare its LookLog design philosophy against AgX's log encoding.

---

## L. CLF and CTF

Add support research for:

- Academy/ASC Common LUT Format (CLF),
- Autodesk Color Transform Format (CTF).

CLF supports ordered transform chains including:

- matrices,
- ASC CDL,
- log transforms,
- exponentials,
- ranges,
- 1D LUTs,
- 3D LUTs.

CTF is a superset capable of serializing arbitrary OCIO transform chains.

Long-term, consider allowing pointwise Rendition operators to be baked/exported to CLF/CTF where mathematically possible.

Potential uses:

- regression tests,
- transform interchange,
- baking approved looks,
- inspecting OFX transforms outside the host,
- reproducing an authored transform in another OCIO-aware environment.

Not all operators will be representable exactly.

Spatial nodes such as Pigment are explicitly outside this category.

---

# Behavioural Benchmark Matrix

Build a benchmark document comparing our suite against concepts found in existing tools.

The goal is NOT feature parity.

The purpose is to ensure we have solved the useful artistic problem.

## Rendition Scene

Look at:

- Baselight Base Grade
- ASC CDL
- exposure / white-balance behaviour in camera pipelines

Question:

Can an artist make broad scene corrections while still understanding what happens mathematically?

## Rendition Tone

Look at:

- Baselight Base Grade
- Baselight Curve Grade
- AgX
- OpenDRT
- Filmic

Question:

Can we shape scene tone deliberately without accidentally creating another DRT?

## Rendition Volume

Look at:

- Baselight X Grade
- Baselight Hue Shift
- MonoNodes Color Shift
- MonoNodes Color Shaper
- Yedlin Cone Coordinates
- Tetra reconstructions

Question:

Can we manipulate a region of colour volume smoothly without constructing keys?

## Rendition Density

Look at:

- MonoNodes density controls
- FilmLight Chromogen
- subtractive paint / dye behaviour
- Kubelka–Munk trajectories
- Hellwig brightness/colorfulness relationships

Question:

Can “density” become a well-defined useful image attribute rather than a renamed saturation slider?

## Rendition Crossover

Look at:

- MonoNodes Hue Twist / Bend
- MonoNodes RGB Split Tone
- photographic crossover behaviour
- channel characteristic curves

Question:

Can colour rendition evolve continuously with exposure?

## Rendition Crosstalk

Look at:

- MonoNodes RGB Crosstalk
- RGB mixer mathematics
- Yedlin-style explicit transform authoring

Question:

Can channel interaction remain explicit and analytically understandable?

## Rendition Strip

Look at:

- PixelTools Three/Strip
- historical three-strip / dye-transfer processes
- Neugebauer/Demichel colourant models
- Kubelka–Munk
- channel separation/recombination mathematics

Question:

Can broad palette behaviour emerge from an independently designed reproduction model?

## Inspector

Look at:

- Yedlin LUT/data-analysis methodology
- MonoNodes utility DCTLs
- OCIO command-line tools
- Colour Science plots and test datasets

Question:

Can we understand the transform without relying on a hero image?

---

# Mandatory Research Rule

For each production node, create a one-page design document before implementation.

It must answer:

1. What artistic problem does this node solve?
2. What existing tools solve a similar problem?
3. What scientific/open references are relevant?
4. What mathematical domain is appropriate?
5. What invariants should hold?
6. What undesirable behaviours must be avoided?
7. Why does this node need to exist separately from the other nodes?
8. What structured test images reveal its behaviour?
9. Is the proposed implementation original, permissively licensed, or derived?
10. Can the transformation be explained clearly enough that a user knows what it is doing?

Do not implement a node until these questions have satisfactory answers.