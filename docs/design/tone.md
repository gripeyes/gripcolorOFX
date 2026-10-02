# Rendition Tone — v1 research candidate
1. Input: scene-linear working-gamut RGB.
2. Internal: selected scalar look encoding normalized around 0.18 into approximate stop coordinates.
3. Changes: contrast about stop-relative pivot, continuous softplus toe/shoulder, smooth shadow/highlight displacement.
4. Output: scene-compatible exposure-conditioned rendition, not a DRT.
5. Exposure: conditioned except exposure-only configuration.
6. Negatives: encoding's stated toe; pure stops explicitly reject nonpositive input.
7. HDR: no clipping/output encoding; parameter-dependent scene values can grow.
8. Inverse: monotonic candidate curve for stated strengths; linked mode has no claimed global inverse.
9. Neutrals: equal channels remain equal; brightness deliberately changes.
10. Gamut: per-channel and linked-coordinate operations are gamut-relative.
11. Failures: extreme overflow; unsupported selected domain; linked coordinate displacement is not chromaticity-preserving scaling.
12. Separate purpose: tone authorship independent from downstream display rendering.
Math: z=(encode(x)-encode(0.18))/normal-stop-slope. f(z)=pivot+c[(z-pivot)+toe*softplus(-(z-pivot+toeExtent))-shoulder*softplus(z-pivot-shoulderExtent)]-0.15*c*[shadowDensity*sigmoid(-z-toeExtent)+highlightDensity*sigmoid(z-shoulderExtent)]. Strengths ≤0.8, extents >0, densities ±1, c>0 ensure positive derivative. Gray preservation subtracts f(0). Exposure is applied in linear RGB before shaping. Linked mode uses the displacement computed from the maximum absolute RGB channel (a magnitude envelope that remains defined for signed HDR colors) and adds the same coordinate displacement to each channel; it does not claim exposure-only chromaticity stability.
References: OCIO/Colour scalar encodings; original softplus curve design, Base Grade behavior only.
Tests: monotonic signed neutral sweep, pivot/gray, derivatives, domains, exposure and channel ramps.
