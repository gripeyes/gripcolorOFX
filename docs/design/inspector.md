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
