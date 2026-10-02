# Rendition Density — v1 spectral-derived research candidate

1. Input: explicitly interpreted scene-linear RGB with known primaries/white point.
2. Internal: D65 XYZ, three emitted Gaussian basis coefficients plus signed XYZ residual; signed Oklab coordinates guide artistic selection/coupling.
3. Change: wavelength-dependent KM attenuation trajectories followed by independent chroma coupling. Density is dimensionless artistic input, not physical optical density.
4. Output: deliberately scene-compatible radiance rendition candidate. Physical reflected material/print appearances are separate research outputs; production semantic/artist acceptance remains pending.
5. Exposure: conditioned by EV range, shadow and highlight weights. Fixed selection and coupling have homogeneous scale behavior; no viewing luminance is introduced.
6. Negatives: smooth positive basis split plus explicit signed XYZ residual. Negative artistic density mirrors the attenuation delta, not negative physical concentration.
7. HDR: basis coefficients and residual scale with scene radiance. The native coefficient-norm split separates shape from scale without bounding scene RGB to reflectance values.
8. Inverse: no global inverse promised.
9. Neutrals: continuous chroma-distance protection, independently tested from default identity and magnitude preservation.
10. Gamut: colorimetric D65 XYZ basis; equivalent-gamut tests are required. RGB gamut is retained on output.
11. Failures: synthetic basis is nonunique; residual dominance, extreme chromatic attenuation and gamut expansion require real compositing/media evaluation. Held-out table accuracy does not establish perceptual equivalence.
12. Purpose: material-informed color depth with independent chroma behavior, beyond ordinary saturation or RGB scaling.

Let x be D65 XYZ, c=B^-1 x, p=0.5(c+sqrt(c²+(0.001||c||)²)), and r=x-Bp. B contains integrated original emitted Gaussian spectra. A_KM(h,|d|) is a preintegrated response matrix, interpolated over six hue families and 129 density levels. The provisional result is x+sign(d)(A_KM p+r-x). Its opponent chroma is scaled to the original chroma times 2^(d*coupling), then blended using original-source selection/protection weights. The physical oracle uses nonnegative pigment concentration 1.5 d²; negative d is an explicit artistic delta reversal.

This candidate is enabled in the Research bundle. It is not an accepted physical material simulator or production Density model. No per-pixel wavelength integration runs in OFX. See the spectral basis fit, approximation comparison and signed/HDR reports for evidence and limitations.
