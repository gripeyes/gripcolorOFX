# Spectral/data sources

| Dataset | Source | License/attribution status | Range / interval | Intended use |
|---|---|---|---|---|
| CIE 1931 2° CMFs | Colour 0.4.7, standard observer tables; original references in Colour data module | Colour distribution BSD-3-Clause; normative CIE data origins retained in installed source | Resampled 360–830 nm, 1 nm | Offline XYZ integration/oracle |
| D65, D60, D50, Illuminant A | Colour 0.4.7 standard illuminant tables | Software BSD-3-Clause; per-table reference origins retained; resampling is explicit | Resampled 360–830 nm, 1 nm | Reflectance/transmittance appearance experiments |
| Synthetic K/S and optical-density curves | Original Gaussian curves in `research/spectral_lab.py` | Project-authored | 360–830 nm, 1 nm | KM/dye trajectory research, preintegrated response tables |
| Synthetic emitted spectral basis | Original 450/545/625 nm Gaussians, widths 38/42/48 nm | Project-authored | 360–830 nm, 1 nm | Radiance base, signed residual, fast model fitting |
| ColorChecker 2005 xyY | Colour `CCS_COLOURCHECKERS`, original BabelColor/ColorChecker references in Colour | Reference values, not measured spectra; source-specific obligations remain for user's licensing reconciliation | 24 tristimulus values, D50 white | Inspector known-reference chart; generated XYZ include |
| Smits 1999 reconstruction basis | Colour recovery implementation/data | Colour BSD-3-Clause, Smits paper attribution | Colour resampled grid | Offline alternative nonunique emitted-base reconstruction |

The runtime bundles derived basis response matrices and chart XYZ values only. It does not bundle Python, CMFs, illuminant tables, or proprietary spectral measurements. All synthetic curves are deliberately nonhistorical and must not be marketed as measured dyes, pigment identities, film stocks, or Technicolor records.

Measured Munsell, pigment, filter, or dye datasets are not yet integrated. Their access rights and spectral ranges must be recorded before packaging. Every generated physical reference dataset records appearance-referred semantics; no RGB reconstruction is claimed unique.
