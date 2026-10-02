# Rendition Inspector — v1 research candidate
1. Input: explicitly interpreted scene-linear source and optional matching Reference clip.
2. Internal: procedural RGB/XYZ/opponent coordinates and metadata.
3. Change: diagnostic image generation, differences, failure visualization.
4. Output: input mode scene-linear; diagnostics are explicitly diagnostic, not image rendition.
5. Exposure: mode-dependent/non-equivariant diagnostics.
6. Negatives: input/difference preserve; diagnostics reveal them.
7. HDR: procedural exposure ramp includes HDR, no clamp.
8. Inverse: input identity only.
9. Neutrals: ramps explicitly neutral; other modes not constrained.
10. Gamut: cube/RGB ramps are gamut-relative; chart derives known XYZ reference with stated illuminant adaptation.
11. Failures: Reference encoding/gamut mismatch must fail; comparison without Reference must fail; procedural generation bounds must be stable across render tiles.
12. Purpose: inspect structured transforms without relying only on attractive photographs.
References: Colour reference chart and generated data provenance, original procedural geometry. OFX uses filter/general plus generator contexts for procedural modes; diagnostics retain source alpha, generator alpha is explicitly 1.

## 0.2 CPU differential views

Modes 11–15 analyze a configured single-family Volume probe, using the source RGB before that deformation. Expert probe controls never infer upstream parameters. Offline Inspector Lab handles multiregion sweeps. Determinant is mapped as .5 + log2(det)/8, condition as log2(max(condition,1))/12, stretch as .5 + log2(sigma)/8 and step disagreement as error/.05. These display values are bounded to [0,1]. Reliable det ≤ 0 is red (fold or collapse); unreliable >5% coarse/fine disagreement is magenta and overrides the value. Infinite condition is white. No diagnostic clipping alters the source or creative operator.

External RGB is interpreted explicitly; differential coordinates are RGB→RGB in that gamut, not perceptual geometry. Processing is non-equivariant diagnostic output, non-invertible, with unchanged source alpha under RGB-as-supplied processing. Signed/HDR values are probed through the actual Volume adapter; near-zero/nonsmooth regions can remain uncertain. No inverse/global-injectivity guarantee follows from a finite difference. Twelve Volume evaluations per pixel make these inspection modes expensive. New modes are CPU-only; native Nuke checks pass; Metal implementation/parity remains pending separately. Default input mode remains exact identity.

Inspector Lab is offline reference assistance: colour trajectories, HK appearance oracle, palettes/transport, gradient/structure maps and experimental soft Pigment guides. It does not apply a distribution grade or spatial filter. See [phase and limits](../DEEP_VALIDATION_0_2.md).
