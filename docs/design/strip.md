# Rendition Strip — v1 spectral-derived research candidate

1. Input: explicitly interpreted scene-linear RGB.
2. Internal: D65 XYZ → emitted spectral basis records plus signed residual; optional inspectable custom record basis and inverse.
3. Change: imperfect record separation, leakage, nonlinear palette shaping and dye-derived recombination response.
4. Output: scene-compatible radiance rendition candidate. Physical transmission/reflection/print appearances stay in Spectral Lab; no historical Technicolor accuracy is claimed.
5. Exposure: equivariant within finite float range for fixed controls. Record shape, hue families and relative neutral protection are scale-independent.
6. Negatives: smooth positive records with signed auxiliary/residual restoration. Custom-basis negative records remain explicit.
7. HDR: homogeneous coefficient processing separates spectral shape from scene-radiance magnitude; no reflectance clamp.
8. Inverse: no global inverse; two-record mode loses information, nonlinear palette shaping and creative anchors can fold relationships.
9. Neutrals/red: independently weighted continuous anchors; their brightness behavior is tested separately from default identity.
10. Gamut: colorimetric spectral basis. Custom matrices operate on documented spectral records, not automatically on working RGB channels.
11. Failures: residual dominance, singular custom bases, extreme contribution/weight controls, synthetic dye limitations and anchor-region transition behavior need real imagery/artist acceptance.
12. Purpose: reproduction-inspired whole-palette relationships, separate from local Volume deformations and linear Crosstalk.

Use x=Bp+r with the same smooth split as Density. Leakage blends positive records toward their mean. Two-record mode redistributes the middle record; custom mode applies an explicit nonsingular matrix. Palette shaping normalizes positive records, raises each fraction to 2^(separation*palette), then renormalizes their sum. Contributions multiply the shaped records. A_BeerLambert(h,d) applies preintegrated dye attenuation with d=separation*(0.6+0.4*density (density-coupling control)). Recombination weights and the inverse custom basis reconstruct XYZ; signed record and source residuals remain explicit. Final displacement is multiplied by separation, neutral/red anchor weights and global mix.

The 129-level compact response table is compared with held-out 1 nm oracle trajectories. This enabled Research candidate is not production accepted and does not reproduce a measured stock or commercial implementation. Physical optical density belongs to the offline dye oracle, not this node's dimensionless artist parameter.
