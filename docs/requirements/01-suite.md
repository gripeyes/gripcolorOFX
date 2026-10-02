# Color Rendition OFX Suite

Build a production-quality OpenFX color-rendition suite intended primarily for Autodesk Flame and Foundry Nuke on macOS Apple Silicon.

The suite is not a film-emulation preset collection and must not duplicate the existing Pigment project, SpektraFilm, or the user's authored DRTs.

Its purpose is to provide explicit, controllable color-rendition primitives for authoring how color relationships behave before spatial treatment, optical treatment and display rendering.

## Core philosophy

Do not treat either linear or log as universally correct.

Each operation must execute in the mathematical domain appropriate to its intended behavior.

The external contract of the suite is scene-referred image data. The normal workflow is:

Scene-linear RGB
→ operator-specific internal representation
→ operation
→ inverse internal representation
→ scene-linear RGB

Never silently apply a display transform, DRT, output transform or viewing transform.

Do not clamp RGB unless explicitly required by an enabled user control.

Preserve floating-point values above 1.0 and below 0.0 wherever mathematically possible.

Alpha must pass through unchanged unless a future masking feature explicitly requires otherwise.

## Color-management architecture

Use the host's color-space information when reliably available, including OpenFX 1.5 native color-management metadata, but never make correct processing dependent on it.

Provide an explicit manual override for source RGB primaries/white point.

Initial supported scene-linear RGB spaces:

Linear Rec.2020
ACEScg / AP1
Linear Rec.709 / sRGB primaries

Linear Rec.2020 is the primary validation target.

Auto mode must never introduce a hidden transform. It may only determine the colorimetric interpretation of the incoming RGB values.

All nodes output the same external scene-linear color space they received unless an explicit diagnostic mode states otherwise.

## Internal LookLog

Implement an internal scene-referred logarithmic coordinate system named `LookLog`.

LookLog is NOT a file format and NOT an interchange space.

It exists exclusively as an internal mathematical domain for operators whose behavior benefits from approximately equal spacing per exposure stop.

Requirements:

Middle gray is explicitly anchored at scene-linear 0.18.

Equal exposure-stop changes should produce equal numerical displacement throughout the normal log region.

Use a linear toe around zero so black, very small positive values and reasonable negative scene-linear values can be processed without undefined logarithms.

The encoding and inverse must be continuous.

Prefer first-derivative continuity at the toe boundary.

Do not clamp LookLog to 0–1.

32-bit float behavior is authoritative.

Keep RGB primaries unchanged when entering LookLog. Linear Rec.2020 becomes LookLog-encoded Rec.2020, not AP1.

Implement this using explicit documented math compatible in spirit with OCIO `LogCameraTransform` / `LogAffineTransform`.

Add development-only comparison modes for ACEScct and pure log2 so behavior can be validated.

Do not call the custom encoding ACEScct, LogC or DaVinci Intermediate.

Document all constants.

## Shared core library

Create one reusable C++ color library used by all OFX effects.

The library owns:

RGB ↔ XYZ conversion

chromatic adaptation

RGB-matrix operations

LookLog encoding/decoding

opponent-space conversion

hue/chroma coordinates

exposure-value calculation

smooth region-selection functions

neutral-axis protection

gamut diagnostics

NaN/Inf handling

CPU scalar/reference implementations

GPU-compatible math functions

The image-processing mathematics must not be duplicated separately inside individual plug-ins.

CPU is the correctness reference.

Metal acceleration comes only after CPU validation.

## OFX package architecture

Ship one OFX bundle containing multiple separately instantiable effects.

The graph must remain readable. Do not implement one giant node containing every possible operation.

Expose these effects:

### Rendition Scene

Purpose: technically understandable scene-referred adjustments.

Controls:

Exposure in stops

RGB exposure offsets

temperature

tint

chromatic adaptation

optional custom 3x3 matrix

matrix mix

ASC-CDL-style slope / offset / power / saturation

CDL domain selector:
Scene Linear
LookLog

Default to Scene Linear.

Do not call SOP mathematically linear merely because the node is processing a linear image. Clearly distinguish the processing domain.

### Rendition Tone

Purpose: broad tonal shaping independent of the final DRT.

Operate primarily in LookLog.

Controls:

Exposure

Contrast

Pivot, expressed meaningfully relative to middle gray / stops

Toe strength

Toe extent

Shoulder strength

Shoulder extent

Shadow density

Highlight density

RGB-linked / per-channel modes

Preserve middle gray option

The node must remain invertible or approximately monotonic under sensible parameter ranges.

It must not attempt to become the display-rendering transform.

### Rendition Volume

This is the centerpiece of the suite.

Purpose: select a continuous region of color volume and deform it with controlled falloff.

Selection coordinates:

Hue center

Hue width

Chroma center/range

Exposure or luminance center/range

Softness

Optional neutral-distance condition

Deformation controls:

Hue displacement

Chroma scale

Density

Exposure/luminance displacement

Optional local RGB matrix/crosstalk

Coordinate-model options:

Opponent

Cone-like

Tetrahedral-like, if a rigorous independently developed implementation is achieved

Do not copy proprietary Yedlin, MonoNodes or other commercial implementations.

The design should be inspired only by the general principle of controlled color-volume deformation.

Provide visual matte/debug modes showing selection weight.

Changes must fall off continuously in all selected dimensions.

### Rendition Density

Purpose: separate perceived color depth from ordinary saturation.

Controls:

Density

Chroma-density coupling

Highlight protection

Shadow weighting

Hue range

Chroma range

Neutral protection

Density-only debug

Allow these broad behaviors:

denser + more chromatic

denser + less chromatic

denser with approximately constant chroma

Do not implement Density as merely multiplying RGB or lowering luminance.

The operator should be developed and validated perceptually using exposure sweeps and color ramps.

### Rendition Crossover

Purpose: allow color rendition to evolve continuously as scene exposure changes.

Provide two related modes.

Hue Crossover:

For a selected hue family, allow dark, middle and bright regions to follow different hue/chroma/density trajectories.

Examples of intended behavior:

dark cyan → blue-black
mid cyan → stable cyan
bright cyan → green-cyan

dark bronze → olive
mid bronze → bronze
bright bronze → warm yellow

Transitions must be continuous, not three hard luminance keys.

Channel Crossover:

Allow independent RGB toe/mid/shoulder shaping in LookLog so that channel relationships change with exposure.

This is analogous conceptually to photographic crossover or sophisticated split toning but must not claim physical film-stock simulation.

### Rendition Crosstalk

Purpose: explicit channel interaction.

Implement a full 3×3 RGB mixing matrix plus useful constrained modes.

Modes:

Unrestricted

Neutral-preserving

Row-sum locked

Optional luminance-preserving approximation

Processing domain:

Scene Linear

LookLog

Neutral-preserving mode must keep equal RGB input values on the neutral axis within numerical tolerance.

Provide intuitive controls in addition to expert matrix coefficients.

Do not hide the underlying matrix.

### Rendition Strip

Purpose: broad palette shaping inspired by historical multi-strip separation/recombination principles, without claiming to reproduce Technicolor or any proprietary commercial product.

Modes:

Three-channel separation

Two-channel separation

Custom basis

Controls:

basis/channel contribution

separation amount

cross-channel leakage

recombination weights

density coupling

palette compression/separation

neutral anchor

red/skin anchor

global mix

The module should feel like changing the reproduction logic of the image rather than selectively hue-shifting individual colors.

Internally investigate alternative color bases, but preserve explicit, inspectable mathematics.

Do not copy PixelTools Three/Strip algorithms.

### Rendition Inspector

Purpose: understand transforms rather than judge them only on hero images.

Modes:

Input image

Exposure ramp

Neutral ramp

RGB ramps

Hue sweep

Chroma sweep

Macbeth-style reference chart generated from known reference values

Color cube slices

Before/after difference

Out-of-gamut diagnostic

NaN/Inf diagnostic

For pointwise nodes, provide before/after trajectory visualizations where practical.

If host overlay APIs allow it, eventually provide graphical plots, but image-based diagnostics are sufficient for the first version.

## Processing order philosophy

Do not enforce a mandatory node order, but design and document this recommended conceptual order:

Scene
→ Tone
→ Volume
→ Density
→ Crossover
→ Crosstalk / Strip
→ Pigment
→ optical / film effects
→ authored DRT

The user must remain free to reorder nodes deliberately.

Different orderings are part of the creative system.

## GPU architecture

CPU reference implementation comes first.

Every operation must have deterministic CPU validation tests.

After CPU correctness is established, implement Metal acceleration for Apple Silicon.

Use OpenFX GPU rendering where supported.

Maintain CPU fallback for hosts that do not provide Metal buffers.

CPU and Metal outputs must match within an explicitly defined numerical tolerance.

Do not redesign algorithms merely to make the GPU version easier.

## Validation

Do not validate using only photographic hero images.

Every operator must be tested on:

neutral ramps

RGB ramps

exposure sweeps

hue sweeps

chroma sweeps

extreme scene-linear values

negative values

values above 1.0

known neutral values

Macbeth-style reference colors

real CG renders

real photographic material

Test invariants appropriate to each node.

Examples:

zero/default parameters produce identity

neutral-preserving crosstalk preserves neutrals

LookLog round-trip reproduces source values within tolerance

CPU and Metal agree

no unrequested clipping occurs

no NaNs are created from valid finite inputs

parameter changes are continuous

hue wrapping is continuous around 0/360 degrees

## Development phases

Phase 1: infrastructure

Build OFX host skeleton, shared color core, image I/O, CPU reference pipeline, color-space metadata handling and automated tests.

Implement and validate LookLog first.

Do not proceed until linear → LookLog → linear round-trip behavior is understood and tested.

Phase 2: fundamental nodes

Implement Scene, Tone and Crosstalk.

These establish the basic math and host integration.

Phase 3: color-rendition nodes

Implement Volume and Density.

Volume is the highest-priority creative operator.

Validate it extensively before implementing more elaborate features.

Phase 4: crossover/palette system

Implement Crossover and Strip.

Do not attempt literal film-stock or Technicolor matching.

Focus on controllable color relationships.

Phase 5: Inspector

Add diagnostic/reference generation and transform-inspection capabilities.

Use Inspector to evaluate all previous nodes.

Phase 6: GPU

Implement Metal parity only after CPU behavior is accepted.

Phase 7: host validation

Validate at minimum in Flame and Nuke.

Confirm:

correct float range

correct alpha behavior

timeline and node-graph operation

parameter animation

render consistency

project reload consistency

OFX packaging/signing on macOS

correct behavior under the user's custom OCIO-managed project

## Non-goals

Do not build another DRT.

Do not build grain.

Do not build halation.

Do not build lens simulation.

Do not merge Pigment into this suite.

Do not copy proprietary DCTL/OFX implementations.

Do not make a collection of film-look presets.

Do not assume ACES, LogC, DWG or any other vendor ecosystem is authoritative.

The goal is an authored set of transparent color-rendition primitives.

## Primary design criterion

At any point, the user should be able to answer:

"What mathematical relationship is this control changing, and in what domain is it changing it?"

If that cannot be answered clearly, the design is too opaque.