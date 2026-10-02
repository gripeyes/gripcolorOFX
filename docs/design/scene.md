# Rendition Scene — v1 research candidate
1. Input: explicitly interpreted scene-linear RGB, including signed/HDR values.
2. Internal representation: scene linear, with optional scalar look encoding for SOP.
3. Relationship changed: exposure, illuminant adaptation, RGB matrix, signed SOP, saturation.
4. Output: scene-compatible authored rendition; no display transform.
5. Exposure: pure exposure/adaptation/matrix/slope/saturation are equivariant; offsets/powers and look-domain SOP are non-equivariant.
6. Negatives: matrix/exposure native; sign-preserving power is our extension of SOP, not normative ASC CDL on negatives.
7. HDR: unbounded except finite-float arithmetic limits.
8. Inverse: available analytically for nonsingular matrices and nonzero slopes/saturation with positive powers; mixed matrix can be singular.
9. Neutrals: exposure preserves them; RGB offsets, adaptation, matrix, and SOP may deliberately change them.
10. Gamut: CAT/exposure colorimetric; raw RGB matrix and SOP are gamut-relative.
11. Failures: singular custom primaries, invalid powers, unsupported pure-stop input, overflow; report errors.
12. Separate purpose: technically explicit scene corrections preceding rendition shaping.
References: Colour RGB/CAT, ASWF OFX, OCIO scalar log formulations, ASC CDL control concept. Original execution order: exposure → CAT → matrix mix → SOP → saturation. Temperature uses CIE daylight xy from 4000–25000 K; tint offsets CIE 1960 v. Default 6504 K/zero tint is exact bypass; nondefault illuminant is adapted to working white. Parameters are not color-managed swatches.
Structured tests: signed neutrals, RGB/exposure ramps, matrix invariants, corresponding XYZ stimuli, animated daylight/tint.
