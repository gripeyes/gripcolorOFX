# Illuminant restoration — 2026-10-07

Base exposes the source-illuminant estimate previously available only in Advanced Scene. It reuses the shared Scene chromatic-adaptation path before Base tone/colour, preserving historical behaviour through a separately stored illuminant generation. The OFX render lifecycle, Output-first ordering, creative composition generations and thirteen Main controls are unchanged.

## Controls and placement

| Effect / parameter ID | Artist label | Default | Range / units | Presentation |
|---|---|---|---|---|
| Base `temperature` | Illuminant (daylight) | 6504 | 4000…25000 K | Tonal Colour / Ranges |
| Base `illuminantTint` | Illuminant tint | 0 | −0.02…+0.02 CIE 1960 v offset | Tonal Colour / Ranges |
| Base `illuminantAdaptation` | Illuminant adaptation | 0 | Bradford / CAT16 / XYZ scaling | Same page; disabled at neutral temperature/tint |
| Base `illuminantVersion` | Illuminant compatibility | 1 | 0 historical / 1 CIE daylight | Hidden, persisted, nonanimated configuration |
| Scene `temperature`, `tint`, `adaptation` | Existing illuminant controls | 6504 / 0 / Bradford | Historical ranges unchanged | Existing Advanced Scene UI |
| Scene `illuminantVersion` | Illuminant compatibility | 0 | 0 historical / 1 CIE daylight | Appended disabled Expert compatibility metadata |

6504 K/zero tint is exact identity regardless of adaptation/generation. 6500 is not silently treated as 6504. This estimates the **source** illuminant: 6000 produces a cooler correction than 6500. It is not creative Warmth, nor the zero-Y creative Tint. Illuminant correction can change Y and neutral chromaticity. It is exposure-equivariant with fixed settings; combined Base remains exposure-conditioned.

No existing parameter is renamed/reordered. All four Base fields append after its historical inventory. The single Scene compatibility field appends after its historical inventory. Old Base projects receive neutral defaults; old Scene projects retain generation 0. Defaults of existing model/adapter generations are unchanged. Migration of a Scene illuminant to generation 1 is not claimed appearance-preserving.

## Exact daylight generation

For T in Kelvin, generation 1 uses:

```text
x(T) = −4.6070e9/T³ + 2.9678e6/T² + 0.09911e3/T + 0.244063   T ≤ 7000
       −2.0064e9/T³ + 1.9018e6/T² + 0.24748e3/T + 0.23704    T > 7000
y(T) = −3x² + 2.87x − 0.275
```

In generation 1, add `(0.3127,0.3290) − daylight(6504)` to the estimated xy. This explicitly calibrates neutrality at 6504 rather than attributing exact D65 xy to rounded polynomial values. Tint is applied after xy→CIE 1960 uv:

```text
d = −2x + 12y + 3
u = 4x/d
v = 6y/d + illuminantTint
D = 2u − 8v + 4
x' = 3u/D
y' = 2v/D
```

Build the selected CAT from estimated `(x',y')` to D65. Let A map working-white XYZ to D65 using the existing reference adapter and M convert working RGB to XYZ:

```text
WB = M^-1 A^-1 CAT(estimated, D65) A M
```

Thus external primaries do not silently select different creative illuminant trajectories. Matrix setup uses the existing double-precision machinery and shared float pixel kernel. Native negative/HDR RGB remains signed/unbounded; there is no per-pixel clipping. Invalid external parameters/custom input colorimetry still fail explicitly.

Generation 0 retains the former lower polynomial exactly:

```text
x(T) = −0.4e9/T³ + 0.7e6/T² + 0.289e3/T + 0.266    T ≤ 7000
```

It retains the historical upper branch and calibration to working-white xy, not the new common-D65 mapping. The source audit and independent Colour reference exposed a substantial boundary jump at 7000 K and different below-7000 trajectories. These are why generation 1 exists; old Scene grades are not silently repaired. The CIE approximation has a small fitted branch mismatch; no exact C1 claim is made.

The new Base tint range is narrower than Scene's legacy ±0.05 because the latter can generate invalid physical xy at the low-temperature extreme. This avoids advertising that invalid combination on the new control without clipping RGB or rewriting another knob.

## Composition and alpha

```text
Source interpretation → optional illuminant CAT → existing Base tone/colour
→ optional matte-driven local exposure → unchanged alpha
```

Only an active illuminant constructs its child Scene snapshot. With otherwise neutral Base settings the result is exactly that Scene generation's correction, avoiding a redundant tonal round trip. With an active Base grade it is equivalent to the explicit Scene→Base stack. The normal outer alpha policy applies once; zero-alpha RGB is retained under explicit unpremultiply mode. Presentation uses the declarative schema and direct Link_Knob targets; no Python grading values are introduced.

## Evidence and implementation

- [`tests/test_illuminant.py`](../tests/test_illuminant.py): independent Colour CIE daylight/Bradford comparison at 6000/6500; three CAT methods; temperature/tint limits; explicit stack equivalence; legacy equivalence; 7000 K refinement; cross-gamut XYZ; exposure scaling; alpha and neutral/nonfinite identity.
- [`tests/test_presentation.py`](../tests/test_presentation.py): historical parameter definitions remain an exact prefix; only the named new fields append; all 36 accepted render fixtures remain bit-identical; historical presentation parity excludes only the intentionally added editors/group.
- [`src/core/artist_models.cpp`](../src/core/artist_models.cpp), [`operators.cpp`](../src/core/operators.cpp), [`kernel_bridge.cpp`](../src/core/kernel_bridge.cpp): authoritative state, shared Scene-stage composition and generation-specific setup.
- [`presentation/control_system.json`](../presentation/control_system.json): exposure, dependencies and exact page placement; generated metadata remains checked.

## Build and host results

- All seven configured CPU, runtime and presentation CTest suites passed; the signed arm64 bundle built successfully. The focused illuminant/presentation pytest run passed all 36 cases.
- Nuke 17.0v1 terminal smoke passed: real linked OFX controls, neutral bypass, conditional adaptation, 6000/6500 response, timed animation, save/reload and rename, and Scene's historical default. Runner: [`tools/nuke_illuminant_smoke.py`](../tools/nuke_illuminant_smoke.py); output: `build/illuminant/nuke-smoke.json` and `illuminant-smoke.nk`.
- Sampling passes the requested frame explicitly. Nuke terminal `visible()` does not establish GUI visibility without a widget; the smoke verifies editor visibility flags and generated page/link definitions instead. This is not a new continuous mouse-drag acceptance claim.
- The signed bundle is installed at `~/Library/OFX/Plugins/Rendition.ofx.bundle` and the Nuke presentation metadata is updated. The previous installed bundle is retained under `build/install-backups/`. Installation replaces the directory rather than overwriting a binary mapped by an open Nuke process. Restart Nuke to use the new native parameters.

Existing broader artist/Flame/host Metal gates remain unchanged.
