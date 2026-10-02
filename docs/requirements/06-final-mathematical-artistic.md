# Final Mathematical and Artistic Research Addendum

This addendum completes the planned broad literature/research phase for the Color Rendition OFX Suite.

After completing the investigations defined here, do not continue broad literature expansion merely because additional papers exist.

Further research should become targeted:

- a specific gate fails,
- a mathematical property is unresolved,
- artist validation exposes a specific deficiency,
- or an existing production model demonstrably cannot achieve the desired behaviour.

The purpose of this addendum is to provide the final mathematical foundation required before the project transitions primarily from literature research to implementation, comparison, and artist evaluation.

---

# M1. Perceptual Colour Geometry

The production Volume, Density and Crossover systems must not assume that ordinary RGB, HSV/HSL or a naïve cylindrical colour space provides a perceptually meaningful geometry.

Study and reproduce research implementations of the following.

## IPT

Fritz Ebner and Mark Fairchild:
"Development and Testing of a Color Space (IPT) with Improved Hue Uniformity"
DOI: 10.2352/CIC.1998.6.1.art00003

Purpose:

- constant-hue behaviour,
- opponent-coordinate manipulation,
- baseline against which newer models are tested.

## Hue-linearized CIELAB

Gustav Braun, Fritz Ebner, Mark Fairchild:
"Color Gamut Mapping in a Hue-Linearized CIELAB Color Space"
DOI: 10.2352/CIC.1998.6.1.art00034

Purpose:

Understand the distinction between:

metric hue angle

and

perceived hue.

Use the constant-hue datasets and methodology as validation references.

## Optimized hue-linear colour geometry

Ingmar Lissner and Philipp Urban:
"How Perceptually Uniform Can a Hue Linear Color Space Be?"
DOI: 10.2352/CIC.2010.18.1.art00018

Purpose:

Study explicit optimization of perceptual uniformity and hue linearity.

This is particularly relevant to deciding whether our Volume coordinate system should be:

- a published perceptual space,
- a corrected perceptual space,
- or a purpose-designed transformation.

## CAM16 / CAM16-UCS

Changjun Li et al.:
"Comprehensive color solutions: CAM16, CAT16, and CAM16-UCS"
DOI: 10.1002/col.22131

Purpose:

Research:

- lightness,
- brightness,
- chroma,
- colorfulness,
- saturation,
- viewing-condition-aware appearance coordinates.

Do not assume CAM16-UCS must become the production space.

Use it as one of the reference systems.

## JzAzBz

Muhammad Safdar et al.:
"Perceptually uniform color space for image signals including high dynamic range and wide gamut"
DOI: 10.1364/OE.25.015131

Purpose:

Evaluate:

- HDR/WCG behaviour,
- hue linearity,
- separation of lightness/chroma/hue,
- behaviour over large colour differences.

## Hellwig / Fairchild appearance work

Luke Hellwig and Mark Fairchild:
"Brightness, lightness, colorfulness, and chroma in CIECAM02 and CAM16"
DOI: 10.1002/col.22792

Luke Hellwig, Dale Stolitzka and Mark Fairchild:
"Extending CIECAM02 and CAM16 for the Helmholtz-Kohlrausch effect"
DOI: 10.1002/col.22793

These papers are mandatory Density references.

The implementation must explicitly investigate the fact that perceived brightness is not determined solely by luminance.

Increasing chromatic purity can increase perceived brightness.

This may explain part of the artistically useful distinction between:

"darker"

and

"denser / deeper".

Do not blindly incorporate the full appearance model.

Use the papers to identify and test the perceptual relationships relevant to Density.

---

# M2. Perceptual Geometry Validation

Create a dedicated validation harness for candidate colour coordinates.

Generate:

- constant-exposure hue circles,
- constant-perceived-hue trajectories where reference data exist,
- saturation/chroma sweeps,
- exposure sweeps,
- neutral-axis sweeps,
- highly saturated blue/cyan/magenta regions,
- skin-like colours,
- dark chromatic colours,
- HDR colour values.

Measure:

- hue drift,
- lightness drift,
- chroma monotonicity,
- neutral stability,
- continuity,
- local metric distortion,
- numerical conditioning.

Do not declare a coordinate system superior based on one global mean score.

Report behaviour by hue family and exposure region.

The blue/cyan/magenta regions must receive particular scrutiny because many colour spaces exhibit their largest hue irregularities there.

---

# M3. Colour-Volume Deformation Mathematics

Treat Volume as a deformation of a continuous colour field, not merely six independent qualifiers.

Research mathematical interpolation/deformation families including:

- tetrahedral piecewise-linear interpolation,
- generalized barycentric coordinates,
- radial basis functions,
- polyharmonic splines,
- thin-plate splines,
- bounded weighted vector fields.

Useful references include:

F. L. Bookstein:
"Principal Warps: Thin-Plate Splines and the Decomposition of Deformations"
DOI: 10.1109/34.24792

Academy/ASC Common LUT Format specification:
tetrahedral interpolation.

Jianchao Tan, Jyh-Ming Lien, Yotam Gingold:
"Decomposing Images into Layers via RGB-space Geometry"
DOI: 10.1145/2988229

Jianchao Tan, Jose Echevarria, Yotam Gingold:
"Efficient Palette-Based Decomposition and Recoloring of Images via RGBXY-Space Geometry"
DOI: 10.1145/3272127.3275054

Baptiste Delos et al.:
"RGB Point Cloud Manipulation with Triangular Structures for Artistic Image Recoloring"
arXiv:1912.04583

These papers do NOT dictate the production Volume algorithm.

Use them to study:

- continuous control fields,
- palette geometry,
- simplicial decomposition,
- local interpolation,
- how artist controls can manipulate small but visually important colour regions.

---

# M4. Jacobian Analysis of Volume

This is an engineering requirement even where no single colour paper prescribes it.

For a colour deformation:

F : R^3 → R^3

numerically estimate its Jacobian:

J_F(x)

throughout structured samples of the valid colour domain.

Report:

- determinant,
- singular values,
- local condition number,
- maximum local expansion,
- maximum local compression.

Where Volume is intended to remain locally invertible, investigate whether:

det(J_F) > 0

throughout the supported operating region.

A negative or zero determinant indicates local folding/collapse of colour volume.

Do not automatically forbid all such behaviour if artistic experimentation proves it useful.

However, hidden folds must never occur accidentally.

Inspector should eventually be capable of flagging:

- extreme local stretching,
- compression,
- folding,
- near-singular regions.

This gives the project a rigorous way to distinguish:

"strong creative colour deformation"

from

"numerically broken colour field".

---

# M5. Monotonic Curve Mathematics

Tone and Channel Crossover must not use arbitrary cubic splines that overshoot merely because the UI control points look smooth.

Study:

Fritsch and Carlson:
"Monotone Piecewise Cubic Interpolation"
SIAM Journal on Numerical Analysis, 1980
DOI: 10.1137/0717021

Use monotonic cubic Hermite interpolation as a baseline for:

- tone curves,
- toe/shoulder interpolation,
- density trajectories where monotonicity is intended,
- exposure-conditioned crossover trajectories.

Compare against:

- linear interpolation,
- Catmull-Rom,
- ordinary cubic spline,
- B-spline,
- monotone Hermite / PCHIP.

Whenever an artist-facing curve promises:

brighter input → no unexpected darker inversion

or:

increasing Density → no accidental reversal

the implementation must enforce the promised shape mathematically rather than hoping the control points behave.

---

# M6. Distribution Mapping and Optimal Transport

Study mathematical colour-distribution transfer as a research and Inspector tool.

Do not automatically turn it into an automatic "match reference" production node.

## N-dimensional PDF transfer

François Pitié, Anil Kokaram, Rozenn Dahyot:
"N-Dimensional Probability Density Function Transfer and its Application to Colour Transfer"
DOI: 10.1109/ICCV.2005.166

## Linear Monge-Kantorovich mapping

François Pitié and Anil Kokaram:
"The Linear Monge-Kantorovitch Colour Mapping for Example-Based Colour Transfer"
DOI: 10.1049/CP:20070055

## Automated grading

François Pitié, Anil Kokaram, Rozenn Dahyot:
"Automated Colour Grading Using Colour Distribution Transfer"
DOI: 10.1016/j.cviu.2006.11.011

## Temporal colour-transform interpolation

Nicolas Bonneel et al.:
"Example-Based Video Color Grading"
DOI: 10.1145/2461912.2461939

Research uses:

- quantify how two image palettes differ,
- derive baseline transforms,
- analyze a user's reference images,
- evaluate whether an authored Volume/Strip transform moved the distribution in the intended direction,
- eventually interpolate smoothly between authored looks.

Do not use optimal transport as a replacement for artistic authorship.

Use it as:

analysis,
comparison,
initialization,
or reference assistance.

---

# M7. Gradient and Structure Preservation

Aggressive colour transforms can preserve pointwise colour intentions while damaging spatial relationships.

Study:

Xiao and Ma:
"Gradient-Preserving Color Transfer"
DOI: 10.1111/j.1467-8659.2009.01566.x

The key research question is:

When a strong colour transformation is applied, what image gradients should remain structurally coherent?

Add diagnostics comparing:

- input luminance gradients,
- output luminance gradients,
- chromatic edge direction,
- local contrast.

This does NOT mean Rendition Volume should become a spatial filter.

The purpose is to detect cases where a pointwise transform produces structurally destructive behaviour.

---

# M8. Spatial Tone and Information Hierarchy

The following references should inform Pigment and any future spatial-tone system.

They should NOT silently change the pointwise Rendition Tone node.

## Photographic Tone Reproduction

Reinhard, Stark, Shirley, Ferwerda:
"Photographic Tone Reproduction for Digital Images"
DOI: 10.1145/566654.566575

Study:

- photographic exposure analogy,
- key,
- white point,
- tone compression.

## Gradient-Domain HDR Compression

Fattal, Lischinski, Werman:
"Gradient Domain High Dynamic Range Compression"
DOI: 10.1145/566654.566573

Study:

- separating large-scale gradient compression from fine information,
- preserving local information under strong dynamic-range changes.

## Weighted Least Squares / Multi-scale Decomposition

Farbman, Fattal, Lischinski, Szeliski:
"Edge-Preserving Decompositions for Multi-Scale Tone and Detail Manipulation"
DOI: 10.1145/1360612.1360666

## Local Laplacian Filters

Paris, Hasinoff, Kautz:
"Local Laplacian Filters: Edge-Aware Image Processing with a Laplacian Pyramid"
DOI: 10.1145/2010324.1964963

Use these references for:

- broad information hierarchy,
- selective information loss,
- soft large-scale tonal organization,
- local contrast preservation,
- Pigment research.

Do not merge their spatial logic into the ordinary Color Rendition nodes.

---

# M9. Spectral and Material Mathematics

Maintain the spectral research already defined.

Add these papers explicitly to the mandatory comparison set.

## Spectral upsampling

Wenzel Jakob and Johannes Hanika:
"A Low-Dimensional Function Space for Efficient Spectral Upsampling"
DOI: 10.1111/cgf.13626

Use as a major RGB-to-spectrum reference.

## Pigment-space editing

Jianchao Tan, Stephen DiVerdi, Jingwan Lu, Yotam Gingold:
"Pigmento: Pigment-Based Image Analysis and Editing"
DOI: 10.1109/TVCG.2018.2858238

This is mandatory for Density research.

Study how multispectral absorption/scattering models create editing behaviour that differs from ordinary RGB manipulation.

Do not duplicate Pigmento's implementation.

Use it to ask:

What artistically useful behaviour emerges when colour is manipulated through material parameters rather than RGB?

## Spectral print reproduction

Mathieu Hébert and Roger Hersch:
"Review of Spectral Reflectance Models for Halftone Prints: Principles, Calibration, and Prediction Accuracy"
DOI: 10.1002/col.21907

Study:

- Yule-Nielsen modified Neugebauer,
- cellular Neugebauer,
- optical dot-gain/reproduction interaction,
- colourant mixture modelling.

Use primarily for Strip/separation/recombination research.

---

# M10. Soft Palette and Layer Geometry

Study the mathematical decomposition of image colour into editable overlapping components.

## Soft colour segmentation

Aksoy et al.:
"Unmixing-Based Soft Color Segmentation for Image Manipulation"

Study:

- optimization-based soft layers,
- homogeneous colour components,
- smooth overlapping membership.

## RGB-space layer geometry

Tan, Lien and Gingold:
"Decomposing Images into Layers via RGB-space Geometry"

## RGBXY decomposition

Tan, Echevarria and Gingold:
"Efficient Palette-Based Decomposition and Recoloring of Images via RGBXY-Space Geometry"

Study generalized barycentric weights, convex-hull geometry and spatial coherence.

These approaches are particularly relevant to a future connection between:

Rendition
+
Pigment
+
smart/selective local editing.

Do not expand v1 scope automatically.

Retain these as references for later image-aware colour selection and Look tools.

---

# M11. Density Research Formulation

Density remains original research.

Use the mathematical/perceptual references above to investigate candidate definitions.

A Density operator may depend on:

D = f(J, C, h, E, material model)

where:

J = perceptual lightness/brightness coordinate
C = chroma/colorfulness
h = hue
E = scene exposure / radiometric magnitude

Do not assume density is one scalar transformation.

Investigate separate mechanisms for:

- lightness reduction,
- chroma coupling,
- hue drift,
- spectral/material concentration,
- perceived-brightness compensation.

Explicitly test the Helmholtz-Kohlrausch relationship.

For example:

two colours with equal luminance but different chroma may not have equal perceived brightness.

Therefore a useful Density operation may need to compensate lightness as chroma changes.

Generate controlled experiments before selecting the production model.

---

# M12. Crossover Research Formulation

Treat Crossover as a continuous vector-valued function of hue and exposure.

Conceptually:

Δ(h, E) =
[
    Δh,
    ΔC,
    ΔD
]

Do not implement three hard shadow/midtone/highlight masks.

Use continuous interpolation.

Research:

- monotone Hermite interpolation,
- smooth basis functions,
- compact B-spline representations,
- bounded radial basis functions.

Require at least C1 continuity for normal artist operation.

Prefer C2 where it improves behaviour without sacrificing intuitive control.

Create trajectory plots in the selected perceptual/opponent space.

A user should be able to see:

dark cyan
→ blue-black

mid cyan
→ cyan

bright cyan
→ green-cyan

as one smooth trajectory rather than three independent keyed operations.

---

# M13. Strip Mathematical Formulation

Treat Strip initially as:

1. decomposition into a low-dimensional set of colourant/separation coordinates,
2. nonlinear channel/material response,
3. controlled leakage/crosstalk,
4. recombination.

Compare at minimum:

- pure RGB matrix,
- nonlinear matrix + per-channel curves,
- tetrahedral/LUT deformation,
- Beer-Lambert dye model,
- Neugebauer-style colourant model,
- fitted compact spectral model.

Do not ship the complicated model unless it creates useful behaviour that the simpler candidates cannot reproduce.

This remains a hard gate.

---

# M14. Mathematical Metrics

No single metric decides artistic success.

Use metrics diagnostically.

Possible measurements include:

- Euclidean error in XYZ where appropriate,
- CAM16-UCS distances,
- JzAzBz distances,
- CIEDE2000 for SDR-style reference datasets,
- hue-angle error against constant-hue data,
- neutral-axis error,
- exposure-response error,
- Jacobian determinant / singular values,
- Wasserstein distance for palette distributions,
- spectral reconstruction error,
- held-out Density/Strip trajectory error.

Do not optimize production colour transforms solely against one ΔE metric.

A mathematically lower colour difference does not imply a more useful creative operator.

---

# M15. Artist Target Validation

Create a dedicated target suite based on the actual visual language the user is pursuing.

The suite should contain both structured synthetic images and representative photographic/CG images.

Required artistic behaviours to test include:

## Dark chromatic collapse

Dark colours should be capable of retaining intentional hue identity before progressively collapsing toward:

- blue-black,
- green-black,
- olive-black,
- brown-black,

instead of simply becoming neutral black.

## Dense skin

Skin must be capable of moving toward:

- cream,
- ochre,
- bronze,
- pale cyan/green,

while remaining coherent and avoiding generic orange skin-tone behaviour.

## Palette hierarchy

A small number of colour families should be able to dominate the image.

The system should support deliberate suppression of secondary colour variation.

## Protected accent colours

One family, for example red/orange, should be capable of surviving more strongly while the remainder of the palette becomes compressed or contaminated.

## Contamination

Colour relationships should support controlled:

- olive,
- cyan,
- bronze,
- green,
- dirty warm,

contamination without requiring dozens of local keys.

## Exposure-dependent colour death

Hue/chroma behaviour should evolve gracefully through exposure.

The transformation must not produce abrupt threshold-like changes as image values enter darkness.

These goals are artist acceptance targets.

They are not assumptions about physically correct colour reproduction.

---

# M16. Reference-Reconstruction Challenge

Once Volume, Density, Crossover and Strip reach usable CPU prototypes, create a formal artistic challenge.

Choose several user-approved reference images representing:

- cold spectral/cyan look,
- warm bronze/olive look,
- near-monochrome black look,
- protected red accent,
- dense low-key skin.

Attempt to reproduce the broad colour logic using ONLY:

Scene
Tone
Volume
Density
Crossover
Crosstalk
Strip

plus the user's existing DRT.

Do not initially use:

- SpektraFilm stock colour transforms,
- arbitrary LUT packs,
- dozens of hand-painted masks.

Local exposure/masks may later be introduced where the source image genuinely requires them.

Measure:

- number of controls/nodes required,
- time to reach the result,
- whether transformations remain reusable on another image,
- whether the same look grammar survives different content.

This test matters more than adding another academic model.

---

# M17. Simplicity Challenge

For every proposed new mathematical model, compare it against simpler baselines.

Examples:

Density candidate
vs
Exposure + Saturation

Strip candidate
vs
3×3 Matrix + Curves

Volume candidate
vs
Hue-vs-Hue / Hue-vs-Sat

Crossover candidate
vs
three luminance keys

A sophisticated operator only passes if it provides:

- better control,
- better continuity,
- more coherent colour relationships,
- faster artist interaction,
- or behaviour unavailable from the simple baseline.

Complexity is not a feature by itself.

---

# M18. Final Research Stop Rule

After this addendum is integrated:

Do not add more general colour-science papers, colour spaces, film-emulation references, grading plugins or spectral models by default.

Move into:

implementation,
visual comparison,
artist feedback,
and targeted failure-driven research.

New literature is added only when:

1. a research gate fails,
2. a specific mathematical problem cannot be solved with the current references,
3. artist testing identifies a repeatable deficiency,
4. or a clearly superior published method directly addresses that deficiency.

The project has enough theoretical breadth.

The next major source of information must become:

the images it produces.