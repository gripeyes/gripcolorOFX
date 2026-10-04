# RENDITION CONTROL SYSTEM 0.32

Canonical as-implemented artist-control contract and 0.31/0.32 postmortem. Snapshot: 2026-10-03, current 0.32 UX correction candidate. This document records behavior; it does not accept pending host/artist gates or authorize a refactor. Only this Markdown document was created in this pass.

## How to use this guidance

- Preserve the rendered behavior identified by artist feedback; reorganizing presentation is not permission to redesign the look.
- Read §2 for ownership, §§3–5 for exact control IDs/pages, and §§8–11 before changing any mapping, dependency or compatibility handling.
- Treat the Main mapping equations as macro **bases**; apply the stored-generation composition contract before interpreting effective engine state.
- Use §7 as a do-not-repeat postmortem and §14 to distinguish documented discrepancies from accepted behavior.
- The final invariants are review requirements for a future refactor. Recommendations are explicitly separated from current implementation.

## Contents

[Base](#3-base-control-inventory) · [Palette](#4-palette-control-inventory) · [Material](#5-material-control-inventory) · [Postmortem](#7-what-did-not-work--postmortem) · [Composition](#8-main--expert-composition-contract) · [Dependencies](#9-central-dependency-contract) · [Domains](#10-processing-domain-contract) · [Compatibility](#11-compatibilityversioning-contract) · [Evidence](#15-primary-evidence-and-source-navigation) · [Invariants](#non-negotiable-invariants)

## 1. Executive summary

Base forms scene-compatible tone and tonal colour. Palette authors colour families, exposure trajectories and RGB relationships. Material authors generic material-informed depth, imperfect separation and recombination. Base → Palette → Material remains the everyday architecture; existing deep engines remain available independently under Rendition / Advanced.

**Artist feedback:**

> The current grading behavior feels very good. Future architecture/UI work should preserve the rendered look unless a specific processing defect is demonstrated.

The grading behavior is artistically successful according to this feedback and is the behavior to preserve. The 0.31/0.32 work chiefly restored access, corrected Main/Expert range safety and improved Nuke presentation. This feedback is distinct from formal exhaustive interaction/predictability acceptance, which remains open. Historical grading equations remain preserved. Presets/recipes remain intentionally deferred.

Evidence hierarchy: current source specifies processing and conditional presentation; serialized interface metadata specifies numeric IDs/defaults/ranges; reports record historical observations; tests establish their documented coverage. Earlier prose is not allowed to silently override current equations. “Current model” below means the index-2 candidate, **not** the default for newly created nodes.

## 2. Current artist architecture

```text
scene-linear source
  → Rendition Base → Rendition Palette → Rendition Material
  → optional Pigment / verified scene-compatible SpektraFilm effects
  → external authored DRT
```

| Component | Ownership | Does not own |
|---|---|---|
| Base | Exposure, monotonic stop-coordinate tone formation, soft tonal colour, supplied-matte local exposure | Display transform, automatic masks, film development |
| Palette | Volume → Crossover → Crosstalk → tonal tint; continuous colour-family authorship | Spatial segmentation, film-stock palettes |
| Material | Density → Strip → Crosstalk; compact generic material/reproduction-informed colour behavior | Full physical-film/print rendering or per-pixel spectral oracle |
| Inspector | Analysis/reference assistance: geometry/Jacobian, trajectories, palette/OT, gradients, signed/HDR/nonfinite diagnostics, offline oracle comparisons | Automatic grading or spatial transformation of the rendition |
| Advanced nodes | Historical Scene, Tone, Volume, Density, Crossover, Crosstalk, Strip, Primaries and Inspector, stable IDs and original equations | Required everyday multi-node workaround |
| Pigment | Spatial hierarchy, information survival and planes; explicit supplied memberships/mattes | Rendition’s colour math |
| SpektraFilm | Optional verified photographic/process/optical character | Core Rendition authorship |
| Authored DRT | Final display rendition | Hidden component of any artist node |

Full SpektraFilm reproduction is a separate routing case: use its technically appropriate output/display path rather than blindly appending a scene DRT after a print/display appearance render. See the pipeline contract. Internal working coordinates do not change the external interpreted RGB gamut.

Tables below inventory **51 Base, 216 Palette and 79 Material numeric/choice processing parameters**. UI-only appended selector/button and diagnostic string are documented separately. Nuke `renditionUi_*` names are links/presentation, not alternate persistent grade IDs. Default means serialized factory value; a neutral default can be 1 rather than 0, and selectors/configuration have no independent image identity meaning. Ranges are advertised scalar limits; complete-state/domain constraints are specified later. Base Main is 13 controls, Palette Main 9, Material Main 8.

## 3. Base control inventory

Base effect ID: `org.gripcolor.rendition.Base`, effect version 1.0; Nuke class `OFXorg.gripcolor.rendition.Base_v1`. Main uses native OFX editors; the first Nuke tab carries the effect name and contains the relabelled Main group. Its current Pivot label is **Contrast pivot**.

Base uses explicit-gamut RGB → white-adapted XYZ → neutral Y plus zero-Y chromatic residual → stop-coordinate tone/colour → inverse conversion. Its fixed artist tint axes are derived from Linear Rec.2020, projected into a zero-Y plane; source metadata never selects a different creative model. Equal RGB is neutral in the interpreted white convention. Tint minimizes unintended Y shifts by construction; clipping/display rendering are absent.

### Main

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Exposure | `exposure` | Scale scene energy by 2^exposure before tone/colour formation | 0 | stops | -20…20 | Always; exact stop scale before shaping | Main | Exposure-conditioned subsequent ranges can change response. |
| Contrast | `contrast` | Pivot-anchored stop contrast in the integrated positive-slope tone map | 1 | factor | 0.1…4 | Always | Main | Not a camera-log RGB operation; positive slope is enforced in the tone coordinate. |
| Contrast pivot | `pivot` | Anchor desired/integrated tone curves at this stop coordinate | 0 | stops relative to 0.18 | -12…12 | P in dependency table | Main | At neutral tone settings no visible change is promised. |
| Black | `blackStops` | Shadow-weighted stop displacement a×blackStops in desired tone map | 0 | stops weighted by shadow range; zero stays zero | -4…4 | Shadow membership a | Main | Zero remains zero; not a floor or scene-Y offset. |
| White | `whiteLevel` | Highlight-weighted stop displacement b×whiteLevel | 0 | stops at full highlight weight; no white cap | -4…4 | Highlight membership b | Main | No white cap; not an output limiter. |
| Toe | `shadowCompression` | Toe softplus contribution with coefficient 0.45; integrated slope construction | 0 | fraction; slope contribution 0 to 0.45 | 0…1 | Toe start/softness; tone coordinate | Main | Toe is not a hard shadow key. |
| Shoulder | `highlightCompression` | Shoulder softplus contribution with coefficient −0.45; combined with Highlight Burn | 0 | fraction; slope contribution 0 to 0.45 | 0…1 | Shoulder start/softness; tone coordinate | Main | No clipping to white. |
| Warmth | `midBalance` | Midtone-weighted fixed Rec.2020 warm/cool zero-Y axis | 0 | dimensionless Y-preserving colour amount | -1…1 | Midtone membership m | Main | Not Kelvin or chromatic adaptation; authored axis is independent of input gamut. |
| Tint | `midTint` | Midtone-weighted fixed Rec.2020 magenta/green zero-Y axis | 0 | dimensionless Y-preserving colour amount | -1…1 | Midtone membership m | Main | Signed artist bias, not an illuminant estimate. |
| Saturation | `saturation` | Scale zero-Y residual before tonal retention, bleaching, tint and Colour Death | 1 | factor | 0…4 | Source chromatic residual | Main | Newly generated tint is added after source saturation. |
| Density | `colourBalance` | Colourfulness-dependent tonal attenuation plus source chroma factor 2^(0.25×amount×colourfulness) | 0 | artistic stops; not spectral density | -2…2 | Source colourfulness; tone map | Main | Everyday tonal Density, not Material spectral-derived Density. |
| Shadow Colour | `shadowTint` | Add shadow hue axis × a × amount × 0.3×abs(shapedY) in zero-Y plane | 0 | dimensionless Y-preserving colour amount | -1…1 | Shadow membership; selected shadowHue | Main | Opposite sign moves opposite the hue axis; Colour Death can attenuate tint afterwards. |
| Highlight Colour | `highlightTint` | Add highlight hue axis × b × amount × 0.3×abs(shapedY) in zero-Y plane | 0 | dimensionless Y-preserving colour amount | -1…1 | Highlight membership; selected highlightHue | Main | Tint is added after source bleaching and then receives Colour Death. |

### Tonal Colour / Ranges

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Toe start | `toeStart` | Location of toe softplus | -4 | stops relative to 0.18 | -20…4 | toe operation nonneutral for visible response; editor remains available | Advanced | Start/center pairs use conditional display bounds; softness stays positive. |
| Toe softness | `toeSoftness` | Width of toe softplus | 1 | stops | 0.25…8 | toe operation nonneutral for visible response; editor remains available | Advanced | Exposure-coordinate width; no hard keys. |
| Shadow hue | `shadowHue` | Direction of the projected RGB artist hue-circle shadow tint axis | 240 | degrees; RGB artist hue circle | 0…360 | shadowTint ≠ 0 | Advanced | Degrees on artist RGB hue circle, not the Volume opponent hue circle. |
| Shadow chroma retention | `shadowRetention` | Shadow-weighted source residual retention in a×retention+m×midChroma+b×highlightRetention | 1 | factor | 0…2 | Shadow membership; source chroma | Advanced | Default 1 preserves the factor; does not protect generated tint from Colour Death. |
| Colour death | `colourDeath` | Multiply final chromatic residual, including tint, by 1−amount×sigmoid((deathStart−e)/deathSoftness) | 0 | fraction | 0…1 | Low-exposure membership | Advanced | Does not drive scene Y to zero. |
| Colour-death start | `deathStart` | Center the Colour Death sigmoid | -6 | stops relative to 0.18 | -24…4 | colourDeath ≠ 0 | Advanced | Disabled otherwise; stored value retained. |
| Colour-death softness | `deathSoftness` | Width of Colour Death sigmoid | 2 | stops | 0.25…8 | colourDeath ≠ 0 | Advanced | Continuous transition, not a hard luminance key. |
| Shoulder start | `shoulderStart` | Location of shoulder softplus | 4 | stops relative to 0.18 | -4…20 | shoulder operation nonneutral for visible response; editor remains available | Advanced | Start/center pairs use conditional display bounds; softness stays positive. |
| Shoulder softness | `shoulderSoftness` | Width of shoulder softplus | 1 | stops | 0.25…8 | shoulder operation nonneutral for visible response; editor remains available | Advanced | Exposure-coordinate width; no hard keys. |
| Highlight hue | `highlightHue` | Direction of the projected RGB artist hue-circle highlight tint axis | 60 | degrees; RGB artist hue circle | 0…360 | highlightTint ≠ 0 | Advanced | Same hue convention caveat as Shadow hue. |
| Highlight chroma retention | `highlightRetention` | Highlight-weighted source residual retention | 1 | factor | 0…2 | Highlight membership; source chroma | Advanced | Bleaching additionally attenuates source chroma. |
| Shadow range center | `shadowRange` | Center of soft shadow colour/displacement membership | -3 | stops relative to 0.18 | -20…4 | shadow operation nonneutral for visible response; editor remains available | Advanced | Start/center pairs use conditional display bounds; softness stays positive. |
| Shadow range softness | `shadowSoftness` | Width of soft shadow membership | 1 | stops | 0.25…8 | shadow operation nonneutral for visible response; editor remains available | Advanced | Exposure-coordinate width; no hard keys. |
| Highlight range center | `highlightRange` | Center of soft highlight colour/displacement membership | 3 | stops relative to 0.18 | -4…20 | highlight operation nonneutral for visible response; editor remains available | Advanced | Start/center pairs use conditional display bounds; softness stays positive. |
| Highlight range softness | `highlightSoftness` | Width of soft highlight membership | 1 | stops | 0.25…8 | highlight operation nonneutral for visible response; editor remains available | Advanced | Exposure-coordinate width; no hard keys. |

### Dodge-Burn

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Dodge / Burn | `localExposure` | After Base grade, apply 2^(stops×coverage×protectionWeight) | 0 | stops through optional Matte alpha | -20…20 | Matte alpha or full-frame coverage 1 | Advanced | Range protection/chroma preservation modify pure RGB exposure; see local formula. |
| Range protection | `localProtection` | Reduce local exposure toward the highlight tail | 0 | fraction protecting selected tail | 0…1 | localExposure ≠ 0 | Advanced | Disabled at zero local stops; may reverse local luminance relationships at extreme settings. |
| Protection center | `localCenter` | Center local exposure highlight protection sigmoid | 3 | stops relative to 0.18 | -20…20 | localExposure ≠ 0 and localProtection ≠ 0 | Advanced | Measured on post-Base magnitude Y coordinate. |
| Protection softness | `localSoftness` | Width local exposure highlight protection sigmoid | 1 | stops | 0.25…8 | localExposure ≠ 0 and localProtection ≠ 0 | Advanced | Stops, no spatial filtering. |
| Preserve chroma magnitude | `localChroma` | Blend residual gain from exposure gain k toward 1 while Y receives k | 0 | fraction; 0 scales RGB, 1 scales Y only | 0…1 | localExposure ≠ 0 | Advanced | At 1 preserves zero-Y residual magnitude, not perceptual saturation. |

### Advanced

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Midtone exposure | `midExposure` | Midtone desired-curve displacement m×amount | 0 | stops | -4…4 | Midtone membership | Advanced | Base integrates a positive slope; differs from historical unconstrained Primaries displacement. |
| Midtone density | `midDensity` | Midtone desired-curve attenuation −m×amount | 0 | stops of attenuation | -2…2 | Midtone membership | Advanced | Not material Density. |
| Midtone chroma | `midChroma` | Midtone source chroma multiplier | 1 | factor | 0…3 | Midtone membership; source chroma | Advanced | Not generated tint magnitude. |
| Highlight bleaching | `highlightBleach` | Multiply source chroma by 1−b×bleach before tint; composed with Burn | 0 | fraction; source chroma only, before tint | 0…1 | Highlight membership; source chroma | Advanced | Creamy or tinted highlights need tint separately; does not cap RGB. |
| Brilliance reduction | `brillianceReduction` | Colourfulness-dependent highlight stop attenuation; Burn adds to this internally | 0 | stops weighted by highlight colourfulness | 0…2 | Highlight membership and colourfulness | Advanced | Effective internal amount can exceed this individual knob’s 0…2 range because Burn adds up to 1; documented Base mapping. |
| Highlight Burn | `highlightBurn` | Coordinate shoulder compression, source bleaching and brilliance reduction | 0 | coordinated compression/brilliance/chroma loss | 0…1 | Highlight membership | Advanced | Complement composition for compression/bleach; additive brilliance. Not matte-driven Burn. |

### Input / Compatibility

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Source interpretation | `interpretation` | Interpret input primaries/white only; Auto recognizes scene-linear metadata/OCIO role | 0 | choice / configuration | 0=Auto / scene_linear or metadata; 1=Linear Rec.2020; 2=ACEScg / AP1; 3=Linear Rec.709; 4=Custom xy primaries / white | Always | configuration | Manual does not convert input pixels; unknown Auto fails explicitly. |
| RGB / alpha handling | `alphaMode` | RGB as supplied or explicit unpremultiply/process/premultiply | 0 | choice / configuration | 0=RGB as supplied; 1=Unpremultiply / process / premultiply | Always | configuration | Alpha copied; zero-alpha original RGB retained in unpremultiply mode. |
| rx | `rx` | Custom red primary CIE x coordinate | 0.708 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| ry | `ry` | Custom red primary CIE y coordinate | 0.292 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| gx | `gx` | Custom green primary CIE x coordinate | 0.17 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| gy | `gy` | Custom green primary CIE y coordinate | 0.797 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| bx | `bx` | Custom blue primary CIE x coordinate | 0.131 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| by | `by` | Custom blue primary CIE y coordinate | 0.046 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| wx | `wx` | Custom white point CIE x coordinate | 0.3127 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| wy | `wy` | Custom white point CIE y coordinate | 0.329 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| Mathematical model | `modelVersion` | Persistent compatibility/adapter/stage generation, not a creative option | 0 | choice / configuration | 0=Base v1 CPU | Hidden/disabled in ordinary UI | configuration (hidden compatibility) | Index meanings in §11; stored values drive immutable snapshots. |
| Signed adapter | `adapterVersion` | Persistent compatibility/adapter/stage generation, not a creative option | 0 | choice / configuration | 0=v1 documented per model | Hidden/disabled in ordinary UI | configuration (hidden compatibility) | Index meanings in §11; stored values drive immutable snapshots. |

`semanticReference` is an additional OFX read-only multiline diagnostic string (not in numeric core parameters); hidden in the Nuke artist presentation. `renditionUi_compatibility` is presentation text only, derived from native state, not a second version parameter. Base’s appended `enableFullControls` button is secret/disabled and has no migration action.

### Base tone, chroma and matte contract

For pre-tone exposed Y, `epsilon=0.18×2^−20`, `e=log2((abs(Y)+epsilon)/0.18)`. Let `a0=sigmoid((shadowRange−e)/shadowSoftness)`, `b0=sigmoid((e−highlightRange)/highlightSoftness)`, `m0=(1−a0)(1−b0)`; normalize a,b,m by their sum. These are overlapping soft exposure memberships, not hard luminance keys. Signed values use magnitude coordinates and retain the Y sign; near-zero coordinates are regularized rather than physical exposure measurements.

Base’s desired stop curve includes pivoted contrast/toe/shoulder, `m(midExposure−midDensity)+b whiteLevel+a blackStops`, and colourfulness-weighted Density/brilliance attenuation. It integrates a positive derivative of that desired curve, anchored to its desired value at Pivot. The symmetric derivative stencil is 0.01 stop; for derivative d use `rho(d)=d` if d≥0.1, otherwise `10^−6+0.099999 exp((d−0.1)/0.099999)`. Two maps (neutral/colourful) are integrated over [−64,+64] at 1/128-stop spacing with linear interpolation/extrapolation. This contains old narrow-range reversal without copying historical Primaries equations or clipping output. It is not a blanket monotonic guarantee for arbitrary matte/protection fields or all colour paths.

Highlight Burn computes, exactly:

```text
compression_effective = 1 − (1 − highlightCompression)(1 − highlightBurn)
bleach_effective      = 1 − (1 − highlightBleach)(1 − highlightBurn)
brilliance_effective  = brillianceReduction + highlightBurn
```

Source residual gets tonal gain, Saturation, colourfulness coupling, retention and bleaching. Tint is then added; Colour Death attenuates the final coloured residual; a zero-Y reprojection removes numerical Y leakage. Black is a shadow-weighted **stop displacement**, White a highlight-weighted **stop displacement**. Neither is a literal output floor/cap. Historical Primaries’ `blackLevel` offset was intentionally not inherited by Base.

Matte-driven exposure is applied **after** the authored Base grade. For coverage c, post-grade magnitude exposure e, and local stops L:

```text
w = 1 − localProtection × sigmoid((e − localCenter)/localSoftness)
k = 2^(L × c × w)
chromaGain = k × (1 − localChroma) + localChroma
XYZout = white × (Y × k) + zeroYResidual × chromaGain
```

The optional OFX `Matte` input accepts Alpha or RGBA alpha. Unconnected c=1; outside a connected matte’s bounds c=0. Coverage must be finite in [0,1] or errors explicitly; it is not clamped. +1 stop/full coverage/no protection/chroma mode 0 is ×2; −1 is ×0.5; half coverage/+1 is √2. Alpha is unchanged; unpremultiply zero-alpha RGB remains original. No automatic segmentation, mask blur or other spatial processing occurs.

The exact paired display safety bounds are in §8. Default underlying endpoint ranges in the inventory do not authorize an invalid reversed Base pair.

## 4. Palette control inventory

Palette effect ID: `org.gripcolor.rendition.Palette`, version 1.0. Order is **Volume → Crossover → Crosstalk → historical Primaries tint**; the final tint stage has no restored Primaries Expert bank in Palette. These are stage-source-relative operations: all six Volume selections use that Volume stage’s original source, not a sequentially deformed point.

The following Main mapping notation is the macro base before Expert composition. For every family i let pRed=1−accent, all other pi=1:

```text
Volume vi_chroma    = 1 + pi × (0.25 separation − 0.7 compression)
Volume vi_hueDelta  = familyDirection_i × trajectory × pi
Crossover darkHue   = shadowHue × trajectory
Crossover brightHue = highlightHue × trajectory
Crossover darkChroma = 1 − colourDeath
Crosstalk rg = bg   = 0.025 separation
Primaries midBalance = 0.3 bias
Primaries midTint    = 0.2 contamination
```

Protected red accent limits these **Volume macro bases**, not all later hue/matrix/tint operations or independently authored Expert state. Main Trajectory Strength scales the listed hue macros and eligible Expert displacements, not every control in Palette.

### Main

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Separation | `separation` | Volume family chroma +0.25×S×protection; Crosstalk rg=bg=0.025×S | 0 | fraction | -1…1 | Always; selections and downstream constraints apply | Main | Also channel interaction: not a pure saturation slider. |
| Compression | `compression` | Volume family chroma −0.7×K×protection | 0 | fraction | 0…1 | Family memberships | Main | Compresses chroma relationships; no hard gamut compression. |
| Contamination | `contamination` | Final Primaries midTint=0.2×amount | 0 | fraction | -1…1 | Midtone membership of final Primaries stage | Main | Not a Crosstalk macro; can be subtle on particular content. |
| Protected red accent | `accent` | Red-only macro protection pRed=1−accent for Volume chroma/hue macros | 0 | fraction | 0…1 | Existing Volume macro deformation | Main | Does not protect Crossover/global Crosstalk, or erase authored Expert deltas. |
| Warm / Cool Bias | `bias` | Final Primaries midBalance=0.3×amount | 0 | fraction | -1…1 | Midtone membership | Main | Fixed zero-Y artist axis, not Kelvin. |
| Shadow Hue Bias | `shadowHue` | Crossover darkHue=amount×Trajectory Strength | 0 | degrees | -90…90 | Hue mode; source selection/exposure | Main | Always editable as Main macro; inactive image effect in channel mode. |
| Highlight Hue Bias | `highlightHue` | Crossover brightHue=amount×Trajectory Strength | 0 | degrees | -90…90 | Hue mode; source selection/exposure | Main | Same condition; not Base tint direction. |
| Colour Death | `colourDeath` | Crossover darkChroma=1−amount | 0 | fraction | 0…1 | Hue mode; dark trajectory membership | Main | Dark opponent chroma loss, distinct from Base sigmoid death. |
| Trajectory strength | `trajectory` | Scale Main family directions and Main shadow/highlight hue; modulate eligible Expert hue/channel deflections | 1 | fraction | 0…2 | Nonzero relevant Main or Expert displacements | Main | Not a strength for all chroma/density/matrix changes; exact rule in §8. |

### Families

The single selected editor exposes the rows for the selected family only. All six native families below remain independently persistent and animatable. `editFamily` is a nonanimated, non-render-evaluating OFX Choice: 0 Red, 1 Yellow, 2 Green, 3 Cyan, 4 Blue, 5 Magenta; default 0. It selects presentation, never copies grading values. Its alias is `renditionUi_editFamily`; editor links are `renditionUiFamily_<suffix>`. Each family contains **22** grade/selection/matrix parameters, not 21.

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Red / Hue center | `Volume_v0_hue` | Center wrapped opponent hue membership | 29 | degrees | 0…360 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Hue width | `Volume_v0_width` | Width wrapped opponent hue membership | 90 | degrees | 0.1…360 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Minimum relative chroma | `Volume_v0_chromaMin` | Lower relative-chroma selector boundary | 0 | C / abs(L) | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Maximum relative chroma | `Volume_v0_chromaMax` | Upper relative-chroma selector boundary | 4 | C / abs(L) | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Minimum exposure | `Volume_v0_evMin` | Lower exposure selector boundary | -20 | stops | -30…30 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Maximum exposure | `Volume_v0_evMax` | Upper exposure selector boundary | 20 | stops | -30…30 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Selection softness | `Volume_v0_softness` | Smooth selector edge widths | 0.5 | fraction | 0.01…1 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Neutral protection | `Volume_v0_neutral` | Soft neutral rejection threshold in relative chroma | 0.03 | C / abs(L) | 0…0.5 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Hue shift | `Volume_v0_hueDelta` | Rotate opponent a/b plane | 0 | degrees | -180…180 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Chroma scale | `Volume_v0_chroma` | Scale opponent chroma | 1 | factor | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Density (coordinate trajectory) | `Volume_v0_density` | Scale opponent L by 2^(−density/3) and chroma by 2^(0.15×density) | 0 | artistic units | -2…2 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Exposure shift | `Volume_v0_exposure` | Scale opponent L/chroma by 2^(exposure/3) | 0 | stops | -8…8 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Local M11 | `Volume_v0_m00` | Authored local linear-RGB coefficient m00 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Local M12 | `Volume_v0_m01` | Authored local linear-RGB coefficient m01 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Local M13 | `Volume_v0_m02` | Authored local linear-RGB coefficient m02 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Local M21 | `Volume_v0_m10` | Authored local linear-RGB coefficient m10 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Local M22 | `Volume_v0_m11` | Authored local linear-RGB coefficient m11 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Local M23 | `Volume_v0_m12` | Authored local linear-RGB coefficient m12 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Local M31 | `Volume_v0_m20` | Authored local linear-RGB coefficient m20 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Local M32 | `Volume_v0_m21` | Authored local linear-RGB coefficient m21 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Local M33 | `Volume_v0_m22` | Authored local linear-RGB coefficient m22 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Red / Local matrix mix | `Volume_v0_matrixMix` | Weight linear-RGB local matrix delta | 0 | fraction | 0…1 | Local matrix differs from identity | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Hue center | `Volume_v1_hue` | Center wrapped opponent hue membership | 110 | degrees | 0…360 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Hue width | `Volume_v1_width` | Width wrapped opponent hue membership | 90 | degrees | 0.1…360 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Minimum relative chroma | `Volume_v1_chromaMin` | Lower relative-chroma selector boundary | 0 | C / abs(L) | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Maximum relative chroma | `Volume_v1_chromaMax` | Upper relative-chroma selector boundary | 4 | C / abs(L) | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Minimum exposure | `Volume_v1_evMin` | Lower exposure selector boundary | -20 | stops | -30…30 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Maximum exposure | `Volume_v1_evMax` | Upper exposure selector boundary | 20 | stops | -30…30 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Selection softness | `Volume_v1_softness` | Smooth selector edge widths | 0.5 | fraction | 0.01…1 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Neutral protection | `Volume_v1_neutral` | Soft neutral rejection threshold in relative chroma | 0.03 | C / abs(L) | 0…0.5 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Hue shift | `Volume_v1_hueDelta` | Rotate opponent a/b plane | 0 | degrees | -180…180 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Chroma scale | `Volume_v1_chroma` | Scale opponent chroma | 1 | factor | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Density (coordinate trajectory) | `Volume_v1_density` | Scale opponent L by 2^(−density/3) and chroma by 2^(0.15×density) | 0 | artistic units | -2…2 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Exposure shift | `Volume_v1_exposure` | Scale opponent L/chroma by 2^(exposure/3) | 0 | stops | -8…8 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Local M11 | `Volume_v1_m00` | Authored local linear-RGB coefficient m00 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Local M12 | `Volume_v1_m01` | Authored local linear-RGB coefficient m01 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Local M13 | `Volume_v1_m02` | Authored local linear-RGB coefficient m02 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Local M21 | `Volume_v1_m10` | Authored local linear-RGB coefficient m10 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Local M22 | `Volume_v1_m11` | Authored local linear-RGB coefficient m11 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Local M23 | `Volume_v1_m12` | Authored local linear-RGB coefficient m12 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Local M31 | `Volume_v1_m20` | Authored local linear-RGB coefficient m20 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Local M32 | `Volume_v1_m21` | Authored local linear-RGB coefficient m21 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Local M33 | `Volume_v1_m22` | Authored local linear-RGB coefficient m22 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Yellow / Local matrix mix | `Volume_v1_matrixMix` | Weight linear-RGB local matrix delta | 0 | fraction | 0…1 | Local matrix differs from identity | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Hue center | `Volume_v2_hue` | Center wrapped opponent hue membership | 145 | degrees | 0…360 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Hue width | `Volume_v2_width` | Width wrapped opponent hue membership | 90 | degrees | 0.1…360 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Minimum relative chroma | `Volume_v2_chromaMin` | Lower relative-chroma selector boundary | 0 | C / abs(L) | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Maximum relative chroma | `Volume_v2_chromaMax` | Upper relative-chroma selector boundary | 4 | C / abs(L) | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Minimum exposure | `Volume_v2_evMin` | Lower exposure selector boundary | -20 | stops | -30…30 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Maximum exposure | `Volume_v2_evMax` | Upper exposure selector boundary | 20 | stops | -30…30 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Selection softness | `Volume_v2_softness` | Smooth selector edge widths | 0.5 | fraction | 0.01…1 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Neutral protection | `Volume_v2_neutral` | Soft neutral rejection threshold in relative chroma | 0.03 | C / abs(L) | 0…0.5 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Hue shift | `Volume_v2_hueDelta` | Rotate opponent a/b plane | 0 | degrees | -180…180 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Chroma scale | `Volume_v2_chroma` | Scale opponent chroma | 1 | factor | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Density (coordinate trajectory) | `Volume_v2_density` | Scale opponent L by 2^(−density/3) and chroma by 2^(0.15×density) | 0 | artistic units | -2…2 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Exposure shift | `Volume_v2_exposure` | Scale opponent L/chroma by 2^(exposure/3) | 0 | stops | -8…8 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Local M11 | `Volume_v2_m00` | Authored local linear-RGB coefficient m00 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Local M12 | `Volume_v2_m01` | Authored local linear-RGB coefficient m01 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Local M13 | `Volume_v2_m02` | Authored local linear-RGB coefficient m02 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Local M21 | `Volume_v2_m10` | Authored local linear-RGB coefficient m10 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Local M22 | `Volume_v2_m11` | Authored local linear-RGB coefficient m11 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Local M23 | `Volume_v2_m12` | Authored local linear-RGB coefficient m12 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Local M31 | `Volume_v2_m20` | Authored local linear-RGB coefficient m20 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Local M32 | `Volume_v2_m21` | Authored local linear-RGB coefficient m21 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Local M33 | `Volume_v2_m22` | Authored local linear-RGB coefficient m22 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Green / Local matrix mix | `Volume_v2_matrixMix` | Weight linear-RGB local matrix delta | 0 | fraction | 0…1 | Local matrix differs from identity | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Hue center | `Volume_v3_hue` | Center wrapped opponent hue membership | 195 | degrees | 0…360 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Hue width | `Volume_v3_width` | Width wrapped opponent hue membership | 90 | degrees | 0.1…360 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Minimum relative chroma | `Volume_v3_chromaMin` | Lower relative-chroma selector boundary | 0 | C / abs(L) | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Maximum relative chroma | `Volume_v3_chromaMax` | Upper relative-chroma selector boundary | 4 | C / abs(L) | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Minimum exposure | `Volume_v3_evMin` | Lower exposure selector boundary | -20 | stops | -30…30 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Maximum exposure | `Volume_v3_evMax` | Upper exposure selector boundary | 20 | stops | -30…30 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Selection softness | `Volume_v3_softness` | Smooth selector edge widths | 0.5 | fraction | 0.01…1 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Neutral protection | `Volume_v3_neutral` | Soft neutral rejection threshold in relative chroma | 0.03 | C / abs(L) | 0…0.5 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Hue shift | `Volume_v3_hueDelta` | Rotate opponent a/b plane | 0 | degrees | -180…180 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Chroma scale | `Volume_v3_chroma` | Scale opponent chroma | 1 | factor | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Density (coordinate trajectory) | `Volume_v3_density` | Scale opponent L by 2^(−density/3) and chroma by 2^(0.15×density) | 0 | artistic units | -2…2 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Exposure shift | `Volume_v3_exposure` | Scale opponent L/chroma by 2^(exposure/3) | 0 | stops | -8…8 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Local M11 | `Volume_v3_m00` | Authored local linear-RGB coefficient m00 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Local M12 | `Volume_v3_m01` | Authored local linear-RGB coefficient m01 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Local M13 | `Volume_v3_m02` | Authored local linear-RGB coefficient m02 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Local M21 | `Volume_v3_m10` | Authored local linear-RGB coefficient m10 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Local M22 | `Volume_v3_m11` | Authored local linear-RGB coefficient m11 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Local M23 | `Volume_v3_m12` | Authored local linear-RGB coefficient m12 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Local M31 | `Volume_v3_m20` | Authored local linear-RGB coefficient m20 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Local M32 | `Volume_v3_m21` | Authored local linear-RGB coefficient m21 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Local M33 | `Volume_v3_m22` | Authored local linear-RGB coefficient m22 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Cyan / Local matrix mix | `Volume_v3_matrixMix` | Weight linear-RGB local matrix delta | 0 | fraction | 0…1 | Local matrix differs from identity | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Hue center | `Volume_v4_hue` | Center wrapped opponent hue membership | 265 | degrees | 0…360 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Hue width | `Volume_v4_width` | Width wrapped opponent hue membership | 90 | degrees | 0.1…360 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Minimum relative chroma | `Volume_v4_chromaMin` | Lower relative-chroma selector boundary | 0 | C / abs(L) | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Maximum relative chroma | `Volume_v4_chromaMax` | Upper relative-chroma selector boundary | 4 | C / abs(L) | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Minimum exposure | `Volume_v4_evMin` | Lower exposure selector boundary | -20 | stops | -30…30 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Maximum exposure | `Volume_v4_evMax` | Upper exposure selector boundary | 20 | stops | -30…30 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Selection softness | `Volume_v4_softness` | Smooth selector edge widths | 0.5 | fraction | 0.01…1 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Neutral protection | `Volume_v4_neutral` | Soft neutral rejection threshold in relative chroma | 0.03 | C / abs(L) | 0…0.5 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Hue shift | `Volume_v4_hueDelta` | Rotate opponent a/b plane | 0 | degrees | -180…180 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Chroma scale | `Volume_v4_chroma` | Scale opponent chroma | 1 | factor | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Density (coordinate trajectory) | `Volume_v4_density` | Scale opponent L by 2^(−density/3) and chroma by 2^(0.15×density) | 0 | artistic units | -2…2 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Exposure shift | `Volume_v4_exposure` | Scale opponent L/chroma by 2^(exposure/3) | 0 | stops | -8…8 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Local M11 | `Volume_v4_m00` | Authored local linear-RGB coefficient m00 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Local M12 | `Volume_v4_m01` | Authored local linear-RGB coefficient m01 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Local M13 | `Volume_v4_m02` | Authored local linear-RGB coefficient m02 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Local M21 | `Volume_v4_m10` | Authored local linear-RGB coefficient m10 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Local M22 | `Volume_v4_m11` | Authored local linear-RGB coefficient m11 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Local M23 | `Volume_v4_m12` | Authored local linear-RGB coefficient m12 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Local M31 | `Volume_v4_m20` | Authored local linear-RGB coefficient m20 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Local M32 | `Volume_v4_m21` | Authored local linear-RGB coefficient m21 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Local M33 | `Volume_v4_m22` | Authored local linear-RGB coefficient m22 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Blue / Local matrix mix | `Volume_v4_matrixMix` | Weight linear-RGB local matrix delta | 0 | fraction | 0…1 | Local matrix differs from identity | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Hue center | `Volume_v5_hue` | Center wrapped opponent hue membership | 325 | degrees | 0…360 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Hue width | `Volume_v5_width` | Width wrapped opponent hue membership | 90 | degrees | 0.1…360 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Minimum relative chroma | `Volume_v5_chromaMin` | Lower relative-chroma selector boundary | 0 | C / abs(L) | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Maximum relative chroma | `Volume_v5_chromaMax` | Upper relative-chroma selector boundary | 4 | C / abs(L) | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Minimum exposure | `Volume_v5_evMin` | Lower exposure selector boundary | -20 | stops | -30…30 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Maximum exposure | `Volume_v5_evMax` | Upper exposure selector boundary | 20 | stops | -30…30 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Selection softness | `Volume_v5_softness` | Smooth selector edge widths | 0.5 | fraction | 0.01…1 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Neutral protection | `Volume_v5_neutral` | Soft neutral rejection threshold in relative chroma | 0.03 | C / abs(L) | 0…0.5 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Hue shift | `Volume_v5_hueDelta` | Rotate opponent a/b plane | 0 | degrees | -180…180 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Chroma scale | `Volume_v5_chroma` | Scale opponent chroma | 1 | factor | 0…4 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Density (coordinate trajectory) | `Volume_v5_density` | Scale opponent L by 2^(−density/3) and chroma by 2^(0.15×density) | 0 | artistic units | -2…2 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Exposure shift | `Volume_v5_exposure` | Scale opponent L/chroma by 2^(exposure/3) | 0 | stops | -8…8 | Source membership; nonidentity region deformation for visible selector response | Advanced | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Local M11 | `Volume_v5_m00` | Authored local linear-RGB coefficient m00 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Local M12 | `Volume_v5_m01` | Authored local linear-RGB coefficient m01 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Local M13 | `Volume_v5_m02` | Authored local linear-RGB coefficient m02 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Local M21 | `Volume_v5_m10` | Authored local linear-RGB coefficient m10 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Local M22 | `Volume_v5_m11` | Authored local linear-RGB coefficient m11 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Local M23 | `Volume_v5_m12` | Authored local linear-RGB coefficient m12 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Local M31 | `Volume_v5_m20` | Authored local linear-RGB coefficient m20 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Local M32 | `Volume_v5_m21` | Authored local linear-RGB coefficient m21 | 0 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Local M33 | `Volume_v5_m22` | Authored local linear-RGB coefficient m22 | 1 | coefficient | -4…4 | Source membership; nonidentity region deformation for visible selector response | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |
| Magenta / Local matrix mix | `Volume_v5_matrixMix` | Weight linear-RGB local matrix delta | 0 | fraction | 0…1 | Local matrix differs from identity | Expert | All family selections use original Volume-stage source; local matrix delta uses original linear RGB, not opponent coordinates. |

### Trajectory

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Look coordinate encoding | `Crossover_lookDomain` | Select scalar RGB encoding/inverse for channel trajectories | 1 | choice / configuration | 0=Pure stops (positive only); 1=ACEScct scalar encoding; 2=LogC4 scalar encoding; 3=DaVinci Intermediate scalar encoding; 4=AgX unclamped stops (positive only); 5=LookLog candidate | mode = 1 (Channel) | Expert | Positive-only encodings can error at zero/negative input; irrelevant to hue mode. |
| Crossover mode | `Crossover_mode` | Exclusive hue/opponent or independent RGB-channel path | 0 | choice / configuration | 0=Hue trajectories; 1=Channel trajectories | Always in full-controls model | Expert | No silent simultaneous execution of both paths. |
| Dark transition center | `Crossover_darkPivot` | Set dark transition center | -3 | stops | -20…20 | Both trajectory modes | Advanced | Opponent path uses normalized Y exposure; channel path uses each encoded channel; index 2 sorts centers. |
| Bright transition center | `Crossover_brightPivot` | Set bright transition center | 3 | stops | -20…20 | Both trajectory modes | Advanced | Opponent path uses normalized Y exposure; channel path uses each encoded channel; index 2 sorts centers. |
| Transition width | `Crossover_transition` | Set common sigmoid width | 2 | stops | 0.1…10 | Both trajectory modes | Advanced | Opponent path uses normalized Y exposure; channel path uses each encoded channel; index 2 sorts centers. |
| dark hue displacement | `Crossover_darkHue` | Dark/mid/bright opponent hue/chroma/density relationship | 0 | degrees | -180…180 | Hue mode | Advanced | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| dark chroma scale | `Crossover_darkChroma` | Dark/mid/bright opponent hue/chroma/density relationship | 1 | factor | 0…4 | Hue mode | Advanced | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| dark density | `Crossover_darkDensity` | Dark/mid/bright opponent hue/chroma/density relationship | 0 | artistic units | -2…2 | Hue mode | Advanced | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| dark r displacement | `Crossover_darkr` | Dark/mid/bright channel-coordinate displacement | 0 | normalized look stops | -4…4 | Channel mode | Advanced | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| dark g displacement | `Crossover_darkg` | Dark/mid/bright channel-coordinate displacement | 0 | normalized look stops | -4…4 | Channel mode | Advanced | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| dark b displacement | `Crossover_darkb` | Dark/mid/bright channel-coordinate displacement | 0 | normalized look stops | -4…4 | Channel mode | Advanced | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| mid hue displacement | `Crossover_midHue` | Dark/mid/bright opponent hue/chroma/density relationship | 0 | degrees | -180…180 | Hue mode | Expert | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| mid chroma scale | `Crossover_midChroma` | Dark/mid/bright opponent hue/chroma/density relationship | 1 | factor | 0…4 | Hue mode | Expert | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| mid density | `Crossover_midDensity` | Dark/mid/bright opponent hue/chroma/density relationship | 0 | artistic units | -2…2 | Hue mode | Expert | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| mid r displacement | `Crossover_midr` | Dark/mid/bright channel-coordinate displacement | 0 | normalized look stops | -4…4 | Channel mode | Expert | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| mid g displacement | `Crossover_midg` | Dark/mid/bright channel-coordinate displacement | 0 | normalized look stops | -4…4 | Channel mode | Expert | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| mid b displacement | `Crossover_midb` | Dark/mid/bright channel-coordinate displacement | 0 | normalized look stops | -4…4 | Channel mode | Expert | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| bright hue displacement | `Crossover_brightHue` | Dark/mid/bright opponent hue/chroma/density relationship | 0 | degrees | -180…180 | Hue mode | Advanced | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| bright chroma scale | `Crossover_brightChroma` | Dark/mid/bright opponent hue/chroma/density relationship | 1 | factor | 0…4 | Hue mode | Advanced | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| bright density | `Crossover_brightDensity` | Dark/mid/bright opponent hue/chroma/density relationship | 0 | artistic units | -2…2 | Hue mode | Advanced | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| bright r displacement | `Crossover_brightr` | Dark/mid/bright channel-coordinate displacement | 0 | normalized look stops | -4…4 | Channel mode | Advanced | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| bright g displacement | `Crossover_brightg` | Dark/mid/bright channel-coordinate displacement | 0 | normalized look stops | -4…4 | Channel mode | Advanced | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |
| bright b displacement | `Crossover_brightb` | Dark/mid/bright channel-coordinate displacement | 0 | normalized look stops | -4…4 | Channel mode | Advanced | Smooth sigmoid relationships, not independent hard masks. Hue/eligible channel Expert deltas receive Trajectory Strength. |

### Crosstalk

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Look coordinate encoding | `Crosstalk_lookDomain` | Select encoding/inverse when domain is look | 1 | choice / configuration | 0=Pure stops (positive only); 1=ACEScct scalar encoding; 2=LogC4 scalar encoding; 3=DaVinci Intermediate scalar encoding; 4=AgX unclamped stops (positive only); 5=LookLog candidate | domain = 1 | Expert | Raw-state UI predicate is approximate; effective identity can differ, see §14. Scene-Y preservation does not follow from encoded-coordinate luminance constraints. |
| M11 | `Crosstalk_m00` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 1 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M12 | `Crosstalk_m01` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 0 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M13 | `Crosstalk_m02` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 0 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M21 | `Crosstalk_m10` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 0 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M22 | `Crosstalk_m11` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 1 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M23 | `Crosstalk_m12` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 0 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M31 | `Crosstalk_m20` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 0 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M32 | `Crosstalk_m21` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 0 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M33 | `Crosstalk_m22` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 1 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| Matrix constraints | `Crosstalk_mode` | Constrain matrix after authored entries/interactions | 1 | choice / configuration | 0=Unrestricted; 1=Neutral-preserving (row sums = 1); 2=Row-sum locked; 3=Luminance preserving | Full-controls model | Expert | Raw-state UI predicate is approximate; effective identity can differ, see §14. Scene-Y preservation does not follow from encoded-coordinate luminance constraints. |
| Processing domain | `Crosstalk_domain` | Select linear RGB versus encoded scalar coordinates | 0 | choice / configuration | 0=Scene Linear; 1=Selected look coordinate | Full-controls model | Expert | Raw-state UI predicate is approximate; effective identity can differ, see §14. Scene-Y preservation does not follow from encoded-coordinate luminance constraints. |
| Locked row sum | `Crosstalk_rowSum` | Set common row sum in Row-sum locked mode | 1 | factor | -4…4 | mode = 2 | Expert | Raw-state UI predicate is approximate; effective identity can differ, see §14. Scene-Y preservation does not follow from encoded-coordinate luminance constraints. |
| Mix | `Crosstalk_mix` | Interpolate constrained matrix with identity | 1 | fraction | 0…1 | Authored matrix/interactions or UI macro predicate nonneutral | Expert | Raw-state UI predicate is approximate; effective identity can differ, see §14. Scene-Y preservation does not follow from encoded-coordinate luminance constraints. |
| rg interaction | `Crosstalk_rg` | Add off-diagonal rg interaction and subtract same amount from its row diagonal | 0 | coefficient | -2…2 | Mix > 0 | Advanced | Names are stored interaction labels; matrix row/column relationship is explicit in §4. |
| rb interaction | `Crosstalk_rb` | Add off-diagonal rb interaction and subtract same amount from its row diagonal | 0 | coefficient | -2…2 | Mix > 0 | Advanced | Names are stored interaction labels; matrix row/column relationship is explicit in §4. |
| gr interaction | `Crosstalk_gr` | Add off-diagonal gr interaction and subtract same amount from its row diagonal | 0 | coefficient | -2…2 | Mix > 0 | Advanced | Names are stored interaction labels; matrix row/column relationship is explicit in §4. |
| gb interaction | `Crosstalk_gb` | Add off-diagonal gb interaction and subtract same amount from its row diagonal | 0 | coefficient | -2…2 | Mix > 0 | Advanced | Names are stored interaction labels; matrix row/column relationship is explicit in §4. |
| br interaction | `Crosstalk_br` | Add off-diagonal br interaction and subtract same amount from its row diagonal | 0 | coefficient | -2…2 | Mix > 0 | Advanced | Names are stored interaction labels; matrix row/column relationship is explicit in §4. |
| bg interaction | `Crosstalk_bg` | Add off-diagonal bg interaction and subtract same amount from its row diagonal | 0 | coefficient | -2…2 | Mix > 0 | Advanced | Names are stored interaction labels; matrix row/column relationship is explicit in §4. |

### Advanced

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Red direction | `familyRed` | Volume Red macro hueDelta=direction×trajectory×protection | 0 | degrees | -60…60 | Selected family membership; Trajectory Strength | Advanced | Available on Advanced; Red receives Main accent protection. |
| Yellow direction | `familyYellow` | Volume Yellow macro hueDelta=direction×trajectory×protection | 0 | degrees | -60…60 | Selected family membership; Trajectory Strength | Advanced | Available on Advanced; Red receives Main accent protection. |
| Green direction | `familyGreen` | Volume Green macro hueDelta=direction×trajectory×protection | 0 | degrees | -60…60 | Selected family membership; Trajectory Strength | Advanced | Available on Advanced; Red receives Main accent protection. |
| Cyan direction | `familyCyan` | Volume Cyan macro hueDelta=direction×trajectory×protection | 0 | degrees | -60…60 | Selected family membership; Trajectory Strength | Advanced | Available on Advanced; Red receives Main accent protection. |
| Blue direction | `familyBlue` | Volume Blue macro hueDelta=direction×trajectory×protection | 0 | degrees | -60…60 | Selected family membership; Trajectory Strength | Advanced | Available on Advanced; Red receives Main accent protection. |
| Magenta direction | `familyMagenta` | Volume Magenta macro hueDelta=direction×trajectory×protection | 0 | degrees | -60…60 | Selected family membership; Trajectory Strength | Advanced | Available on Advanced; Red receives Main accent protection. |
| Overlap composition | `Volume_overlap` | Choose shared source-coordinate overlap combination | 1 | choice / configuration | 0=Weighted deltas; 1=Normalized weighted deltas; 2=Bounded vector accumulation; 3=Shared field | Active Volume regions | Expert | Default normalized deltas; other historical strategies remain Expert choices. |
| Selection view | `Volume_debug` | Output combined/per-family selection weight diagnostic | 0 | choice / configuration | 0=Off; 1=Combined weight; 2=Red; 3=Yellow; 4=Green; 5=Cyan; 6=Blue; 7=Magenta | Diagnostic deliberately enabled | diagnostic | Changes output to diagnostic RGB; currently Advanced, not Main. |
| Hue center | `Crossover_hue` | Soft signed-opponent selection: hue center | 195 | degrees | 0…360 | Hue trajectory mode only | Advanced | No selector acts in channel trajectory mode. Exposure coordinate uses ACEScct-normalized Y, not exact low-end log2 stops. |
| Hue width | `Crossover_width` | Soft signed-opponent selection: hue span | 360 | degrees | 0.1…360 | Hue trajectory mode only | Advanced | No selector acts in channel trajectory mode. Exposure coordinate uses ACEScct-normalized Y, not exact low-end log2 stops. |
| Minimum relative chroma | `Crossover_chromaMin` | Soft signed-opponent selection: lower relative chroma | 0 | C / abs(L) | 0…4 | Hue trajectory mode only | Advanced | No selector acts in channel trajectory mode. Exposure coordinate uses ACEScct-normalized Y, not exact low-end log2 stops. |
| Maximum relative chroma | `Crossover_chromaMax` | Soft signed-opponent selection: upper relative chroma | 4 | C / abs(L) | 0…4 | Hue trajectory mode only | Advanced | No selector acts in channel trajectory mode. Exposure coordinate uses ACEScct-normalized Y, not exact low-end log2 stops. |
| Minimum exposure | `Crossover_evMin` | Soft signed-opponent selection: lower exposure | -20 | stops | -30…30 | Hue trajectory mode only | Advanced | No selector acts in channel trajectory mode. Exposure coordinate uses ACEScct-normalized Y, not exact low-end log2 stops. |
| Maximum exposure | `Crossover_evMax` | Soft signed-opponent selection: upper exposure | 20 | stops | -30…30 | Hue trajectory mode only | Advanced | No selector acts in channel trajectory mode. Exposure coordinate uses ACEScct-normalized Y, not exact low-end log2 stops. |
| Selection softness | `Crossover_softness` | Soft signed-opponent selection: edge softness | 0.5 | fraction | 0.01…1 | Hue trajectory mode only | Advanced | No selector acts in channel trajectory mode. Exposure coordinate uses ACEScct-normalized Y, not exact low-end log2 stops. |
| Neutral protection | `Crossover_neutral` | Soft signed-opponent selection: neutral rejection threshold | 0.03 | C / abs(L) | 0…0.5 | Hue trajectory mode only | Advanced | No selector acts in channel trajectory mode. Exposure coordinate uses ACEScct-normalized Y, not exact low-end log2 stops. |

### Input / Compatibility

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Source interpretation | `interpretation` | Interpret input primaries/white only; Auto recognizes scene-linear metadata/OCIO role | 0 | choice / configuration | 0=Auto / scene_linear or metadata; 1=Linear Rec.2020; 2=ACEScg / AP1; 3=Linear Rec.709; 4=Custom xy primaries / white | Always | configuration | Manual does not convert input pixels; unknown Auto fails explicitly. |
| RGB / alpha handling | `alphaMode` | RGB as supplied or explicit unpremultiply/process/premultiply | 0 | choice / configuration | 0=RGB as supplied; 1=Unpremultiply / process / premultiply | Always | configuration | Alpha copied; zero-alpha original RGB retained in unpremultiply mode. |
| rx | `rx` | Custom red primary CIE x coordinate | 0.708 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| ry | `ry` | Custom red primary CIE y coordinate | 0.292 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| gx | `gx` | Custom green primary CIE x coordinate | 0.17 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| gy | `gy` | Custom green primary CIE y coordinate | 0.797 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| bx | `bx` | Custom blue primary CIE x coordinate | 0.131 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| by | `by` | Custom blue primary CIE y coordinate | 0.046 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| wx | `wx` | Custom white point CIE x coordinate | 0.3127 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| wy | `wy` | Custom white point CIE y coordinate | 0.329 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| Mathematical model | `modelVersion` | Persistent compatibility/adapter/stage generation, not a creative option | 0 | choice / configuration | 0=Palette v1 CPU; 1=v2 restored controls (explicit opt-in); 2=Full controls — bounded composition | Hidden/disabled in ordinary UI | configuration (hidden compatibility) | Index meanings in §11; stored values drive immutable snapshots. |
| Signed adapter | `adapterVersion` | Persistent compatibility/adapter/stage generation, not a creative option | 0 | choice / configuration | 0=v1 documented per model | Hidden/disabled in ordinary UI | configuration (hidden compatibility) | Index meanings in §11; stored values drive immutable snapshots. |
| Volume model | `VolumeVersion` | Persistent compatibility/adapter/stage generation, not a creative option | 0 | choice / configuration | 0=v1 historical equations | Hidden/disabled in ordinary UI | configuration (hidden compatibility) | Index meanings in §11; stored values drive immutable snapshots. |
| Crossover model | `CrossoverVersion` | Persistent compatibility/adapter/stage generation, not a creative option | 0 | choice / configuration | 0=v1 historical equations | Hidden/disabled in ordinary UI | configuration (hidden compatibility) | Index meanings in §11; stored values drive immutable snapshots. |
| Crosstalk model | `CrosstalkVersion` | Persistent compatibility/adapter/stage generation, not a creative option | 0 | choice / configuration | 0=v1 historical equations | Hidden/disabled in ordinary UI | configuration (hidden compatibility) | Index meanings in §11; stored values drive immutable snapshots. |
| Primaries model | `PrimariesVersion` | Persistent compatibility/adapter/stage generation, not a creative option | 0 | choice / configuration | 0=v1 historical equations | Hidden/disabled in ordinary UI | configuration (hidden compatibility) | Index meanings in §11; stored values drive immutable snapshots. |

`semanticReference` is an additional OFX read-only multiline diagnostic string (not in numeric core parameters); hidden in the Nuke artist presentation. `renditionUi_compatibility` is presentation text only, derived from native state, not a second version parameter. `enableFullControls` is a non-evaluating native OFX PushButton (no scalar default/range). Visible through `renditionUi_enableFullControls` only for model indices 0/1; deliberately sets native `modelVersion` to 2 inside an undoable edit.

### Family deformation and local versus global matrices

Family indices/default centers are Red v0=29°, Yellow v1=110°, Green v2=145°, Cyan v3=195°, Blue v4=265°, Magenta v5=325°. These are signed-opponent hue centers, not RGB color-picker angles. Family defaults: width 90°, relative chroma [0,4], exposure [−20,20], softness 0.5, neutral protection 0.03; hue/density/exposure displacement 0, chroma 1, local matrix identity and mix 0. All 22 fields per family are independently persistent and animatable.

Selectors multiply smooth wrapped hue, relative-chroma, normalized-Y exposure and neutral-rejection memberships. Relative chroma is `sqrt(a²+b²)/max(abs(L),10^−12)`. Hue width 360 selects all hues. Selections are evaluated from the same original signed-opponent coordinates. The default overlap mode divides summed deltas by `max(1,sum(active weights))`; alternative historical weighted, bounded and shared-field modes remain accessible in Advanced. Region permutation must not become an implicit processing order.

The deformation is:

```text
L' = L × 2^(exposure/3 − density/3)
[a', b'] = rotate(hueDelta)[a,b] × chroma × 2^(exposure/3 + 0.15 density)
```

Each family **local matrix** contributes `weight×matrixMix×(M×sourceRGB−sourceRGB)` in linear input-gamut RGB, accumulated alongside the opponent deformation. It is neither a matrix in signed Oklab nor the later global Crosstalk stage. No local row/luminance constraint mode is present. Local entries `Volume_vN_m00`…`m22` display Local M11…M33. The selected-family editor merely retargets self-relative links; selecting another family does not copy, normalize, reset or merge its native values.

### Continuous trajectories and exclusive modes

For hue mode, using normalized Y exposure e:

```text
d = 1 − sigmoid((e − darkPivot)/transition)
b = sigmoid((e − brightPivot)/transition)
m = 1 − d − b
hue   = d darkHue + m midHue + b brightHue
chroma= d darkChroma + m midChroma + b brightChroma
density= d darkDensity + m midDensity + b brightDensity
```

Deform signed-opponent coordinates with these values, then blend the resulting delta by the opponent selector weight. In channel mode each encoded RGB component independently gets normalized coordinate `z=(encode(channel)−encode(0.18))/slope(domain)` and its own d/m/b weights. The encoded component receives `slope(domain)×(d darkChannel+m midChannel+b brightChannel)` before inverse encoding. **Opponent selectors are not applied in channel mode.** Hue/chroma/density and channel controls are mutually exclusive presentation groups; pivots/transition are shared. Main dark/bright hue and Colour Death affect the hue branch; they are not automatically reinterpreted as channel shaping.

### Global Crosstalk matrix contract (also Material)

```text
                displayed columns
             M11       M12       M13
stored IDs   m00       m01       m02
             M21       M22       M23
             m10       m11       m12
             M31       M32       M33
             m20       m21       m22
```

Artist-node persistent IDs have prefix `Crosstalk_`. The underlying matrix transforms a column vector. Stored interactions `rg,rb,gr,gb,br,bg` modify entries (0,1),(0,2),(1,0),(1,2),(2,0),(2,1) respectively and subtract the same amount from the destination row diagonal. Read IDs literally by row/column rather than inferring directional names.

Constraints apply after authored entries/interactions; Mix applies afterwards as `Mfinal=mix×Mconstrained+(1−mix)I`:

| Mode | Exact invariant / implementation |
|---|---|
| 0 Unrestricted | Authored coefficients/interactions; no neutrality constraint |
| 1 Neutral-preserving | Adjust row diagonals until every row sum =1; neutral axis **and magnitude** preserved in selected coordinates |
| 2 Row-sum locked | Adjust row diagonals to common `rowSum`; neutral axis preserved but magnitude scales by rowSum before Mix |
| 3 Luminance preserving | For each column j compute `delta=(w_j−Σ_i w_i M_ij)/Σ_i w_i`, add delta to every row in that column, where w is interpreted gamut’s XYZ Y row |

Mode 1/2 can cancel isolated diagonal edits. In selected-look coordinates, a luminance constraint preserves the encoded weighted relationship; it does **not** promise scene-Y preservation after decoding. Main and Expert authored state remain inspectable; constraints do not rewrite the nine stored entries. Mix is currently conditionally enabled from raw-state predicates, not a proof the final constrained matrix differs from identity; see §14.

## 5. Material control inventory

Material effect ID: `org.gripcolor.rendition.Material`, version 1.0. Order **Density → Strip → Crosstalk**. Eight Main mappings are the macro bases before Expert composition:

```text
Density density = Main density
Density chromaCoupling = Main coupling
Strip separation = 1 − (1 − Main separation)(1 − 0.5 depth)
Strip density = depth
Strip leakage = Main leakage
Strip redAnchor = Main anchor
Crosstalk rg = bg = 0.1 Main crosstalk
Crosstalk gr = gb = 0.1 Main contamination
```

Depth coordinates Strip, not Density amount. Material Density is the compact spectral-derived material response, unlike Base Density’s stop/colourfulness balance. Palette Contamination is a tonal-tint macro, whereas Material Contamination is an RGB-interaction macro.

### Main

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Depth | `depth` | Strip separation=1−(1−Main separation)(1−0.5×depth); Strip density=depth | 0 | fraction | 0…1 | Strip stage | Main | Does not set Density amount; activates Strip even at Main Separation 0. |
| Material Density | `density` | Density stage density=amount | 0 | fraction | -1…1 | Density selection/protection | Main | Generic compact material response, not physical optical-density units. |
| Chroma Coupling | `coupling` | Density stage chromaCoupling=amount | 0 | fraction | -1…1 | Material Density or Expert Density amount nonzero | Main | Target chroma depends on effective amount; no HK runtime model. |
| Separation | `separation` | Complement-compose with half Depth into Strip separation | 0 | fraction | 0…1 | Strip stage | Main | Also complemented with Expert Strip separation. |
| Leakage | `leakage` | Strip leakage=amount | 0.1 | fraction | 0…1 | Depth/Main or Expert separation nonzero | Main | Leakage inside records is multiplied by effective separation. |
| Crosstalk | `crosstalk` | Crosstalk rg=bg=0.1×amount | 0 | fraction | -1…1 | Global Crosstalk stage | Main | Row constraints and domain still apply. |
| Contamination | `contamination` | Crosstalk gr=gb=0.1×amount | 0 | fraction | -1…1 | Global Crosstalk stage | Main | Different mathematics from Palette Contamination. |
| Red / skin anchor | `anchor` | Strip redAnchor=amount | 0 | fraction | 0…1 | Existing Strip deformation | Main | Protects soft opponent red/skin family; no dedicated yellow anchor. |

### Density

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Hue center | `Density_hue` | Soft signed-opponent selection: hue center | 195 | degrees | 0…360 | Nonzero effective Density | Advanced | Selection/protection can suppress visible response; hue is opponent hue, not Base artist hue. |
| Hue width | `Density_width` | Soft signed-opponent selection: hue span | 360 | degrees | 0.1…360 | Nonzero effective Density | Advanced | Selection/protection can suppress visible response; hue is opponent hue, not Base artist hue. |
| Minimum relative chroma | `Density_chromaMin` | Soft signed-opponent selection: lower relative chroma | 0 | C / abs(L) | 0…4 | Nonzero effective Density | Advanced | Selection/protection can suppress visible response; hue is opponent hue, not Base artist hue. |
| Maximum relative chroma | `Density_chromaMax` | Soft signed-opponent selection: upper relative chroma | 4 | C / abs(L) | 0…4 | Nonzero effective Density | Advanced | Selection/protection can suppress visible response; hue is opponent hue, not Base artist hue. |
| Minimum exposure | `Density_evMin` | Soft signed-opponent selection: lower exposure | -20 | stops | -30…30 | Nonzero effective Density | Advanced | Selection/protection can suppress visible response; hue is opponent hue, not Base artist hue. |
| Maximum exposure | `Density_evMax` | Soft signed-opponent selection: upper exposure | 20 | stops | -30…30 | Nonzero effective Density | Advanced | Selection/protection can suppress visible response; hue is opponent hue, not Base artist hue. |
| Selection softness | `Density_softness` | Soft signed-opponent selection: edge softness | 0.5 | fraction | 0.01…1 | Nonzero effective Density | Advanced | Selection/protection can suppress visible response; hue is opponent hue, not Base artist hue. |
| Neutral protection | `Density_neutral` | Soft signed-opponent selection: neutral rejection threshold | 0.03 | C / abs(L) | 0…0.5 | Nonzero effective Density | Advanced | Selection/protection can suppress visible response; hue is opponent hue, not Base artist hue. |
| Density | `Density_density` | Compact KM-derived response amount; positive attenuates, negative reverses filtered delta | 0 | artistic units | -1…1 | Effective amount nonzero; selectors also apply | Advanced | Positive basis coefficients processed; signed XYZ residual preserved. No HK artist control. |
| Chroma-density coupling | `Density_chromaCoupling` | Set target opponent chroma Csource×2^(density×coupling) | 0 | factor | -1…1 | Effective amount nonzero; selectors also apply | Advanced | Positive basis coefficients processed; signed XYZ residual preserved. No HK artist control. |
| Highlight protection | `Density_highlightProtection` | Multiply selection by 1−protection×sigmoid((e−3)/2) | 0.5 | fraction | 0…1 | Effective amount nonzero; selectors also apply | Advanced | Positive basis coefficients processed; signed XYZ residual preserved. No HK artist control. |
| Shadow weighting | `Density_shadowWeight` | Multiply selection by 1−weight+weight×sigmoid((−e+2)/2) | 0.5 | fraction | 0…1 | Effective amount nonzero; selectors also apply | Advanced | Positive basis coefficients processed; signed XYZ residual preserved. No HK artist control. |
| Density-only view | `Density_debug` | Output selection/protection weight diagnostic | 0 | choice / configuration | 0=Off; 1=Weight | Diagnostic override | diagnostic | Positive basis coefficients processed; signed XYZ residual preserved. No HK artist control. |

### Strip

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Separation system | `Strip_mode` | Three records, two records, or custom basis | 0 | choice / configuration | 0=Three-channel; 1=Two-channel; 2=Custom basis | Available in full-controls model; image response requires effective separation | Expert | Selects record construction, not a full spectral/material-runtime model. |
| Separation | `Strip_separation` | Amount of record separation and final deformation | 0 | fraction | 0…1 | Effective separation and mix nonzero for image response | Advanced | Protection reduces existing delta; spectral-derived compact reference, not full spectral runtime. |
| Leakage | `Strip_leakage` | Mix positive records toward their mean with leak=leakage×separation | 0.1 | fraction | 0…1 | Effective separation and mix nonzero for image response | Advanced | Protection reduces existing delta; spectral-derived compact reference, not full spectral runtime. |
| Dye density coupling | `Strip_density` | Filter depth d=separation×(0.6+0.4×density) | 0 | artistic units | -1…1 | Effective separation and mix nonzero for image response | Advanced | Protection reduces existing delta; spectral-derived compact reference, not full spectral runtime. |
| Palette compression / expansion | `Strip_palette` | Normalize positive record proportions, raise to 2^(separation×palette), preserve record sum | 0 | artistic units | -1…1 | Effective separation and mix nonzero for image response | Advanced | Protection reduces existing delta; spectral-derived compact reference, not full spectral runtime. |
| Neutral anchor | `Strip_neutralAnchor` | Soft protection of zero/low relative chroma | 1 | fraction | 0…1 | Effective separation and mix nonzero for image response | Advanced | Protection reduces existing delta; spectral-derived compact reference, not full spectral runtime. |
| Red / skin anchor | `Strip_redAnchor` | Soft red/skin angular protection around opponent hue 29° | 0 | fraction | 0…1 | Effective separation and mix nonzero for image response | Advanced | Protection reduces existing delta; spectral-derived compact reference, not full spectral runtime. |
| Global mix | `Strip_mix` | Scale final separated/recombined delta | 1 | fraction | 0…1 | Effective separation and mix nonzero for image response | Expert | Protection reduces existing delta; spectral-derived compact reference, not full spectral runtime. |
| r separation contribution | `Strip_rContribution` | Scale corresponding positive basis record before material filtering | 1 | factor | 0…2 | Effective separation and mix nonzero for image response | Advanced | Records are B-basis components: r→z, g→y, b→x; not raw RGB channels. |
| r recombination weight | `Strip_rWeight` | Scale corresponding recombined basis record before inverse custom basis | 1 | factor | 0…2 | Effective separation and mix nonzero for image response | Advanced | Records are B-basis components: r→z, g→y, b→x; not raw RGB channels. |
| g separation contribution | `Strip_gContribution` | Scale corresponding positive basis record before material filtering | 1 | factor | 0…2 | Effective separation and mix nonzero for image response | Advanced | Records are B-basis components: r→z, g→y, b→x; not raw RGB channels. |
| g recombination weight | `Strip_gWeight` | Scale corresponding recombined basis record before inverse custom basis | 1 | factor | 0…2 | Effective separation and mix nonzero for image response | Advanced | Records are B-basis components: r→z, g→y, b→x; not raw RGB channels. |
| b separation contribution | `Strip_bContribution` | Scale corresponding positive basis record before material filtering | 1 | factor | 0…2 | Effective separation and mix nonzero for image response | Advanced | Records are B-basis components: r→z, g→y, b→x; not raw RGB channels. |
| b recombination weight | `Strip_bWeight` | Scale corresponding recombined basis record before inverse custom basis | 1 | factor | 0…2 | Effective separation and mix nonzero for image response | Advanced | Records are B-basis components: r→z, g→y, b→x; not raw RGB channels. |
| Record 1 gain | `Strip_m00` | Custom record gain coordinate | 1 | raw gain/bias coordinate (index 2); coefficient (legacy) | -8…8 | Custom basis mode | Expert | Index 2 basis uses gain/bias safety transform, not literal RGB Crosstalk entries. |
| Record 1 from 2 | `Strip_m01` | Custom signed cross-record bias coordinate | 0 | raw gain/bias coordinate (index 2); coefficient (legacy) | -8…8 | Custom basis mode | Expert | Index 2 basis uses gain/bias safety transform, not literal RGB Crosstalk entries. |
| Record 1 from 3 | `Strip_m02` | Custom signed cross-record bias coordinate | 0 | raw gain/bias coordinate (index 2); coefficient (legacy) | -8…8 | Custom basis mode | Expert | Index 2 basis uses gain/bias safety transform, not literal RGB Crosstalk entries. |
| Record 2 from 1 | `Strip_m10` | Custom signed cross-record bias coordinate | 0 | raw gain/bias coordinate (index 2); coefficient (legacy) | -8…8 | Custom basis mode | Expert | Index 2 basis uses gain/bias safety transform, not literal RGB Crosstalk entries. |
| Record 2 gain | `Strip_m11` | Custom record gain coordinate | 1 | raw gain/bias coordinate (index 2); coefficient (legacy) | -8…8 | Custom basis mode | Expert | Index 2 basis uses gain/bias safety transform, not literal RGB Crosstalk entries. |
| Record 2 from 3 | `Strip_m12` | Custom signed cross-record bias coordinate | 0 | raw gain/bias coordinate (index 2); coefficient (legacy) | -8…8 | Custom basis mode | Expert | Index 2 basis uses gain/bias safety transform, not literal RGB Crosstalk entries. |
| Record 3 from 1 | `Strip_m20` | Custom signed cross-record bias coordinate | 0 | raw gain/bias coordinate (index 2); coefficient (legacy) | -8…8 | Custom basis mode | Expert | Index 2 basis uses gain/bias safety transform, not literal RGB Crosstalk entries. |
| Record 3 from 2 | `Strip_m21` | Custom signed cross-record bias coordinate | 0 | raw gain/bias coordinate (index 2); coefficient (legacy) | -8…8 | Custom basis mode | Expert | Index 2 basis uses gain/bias safety transform, not literal RGB Crosstalk entries. |
| Record 3 gain | `Strip_m22` | Custom record gain coordinate | 1 | raw gain/bias coordinate (index 2); coefficient (legacy) | -8…8 | Custom basis mode | Expert | Index 2 basis uses gain/bias safety transform, not literal RGB Crosstalk entries. |

### Crosstalk

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Look coordinate encoding | `Crosstalk_lookDomain` | Select encoding/inverse when domain is look | 1 | choice / configuration | 0=Pure stops (positive only); 1=ACEScct scalar encoding; 2=LogC4 scalar encoding; 3=DaVinci Intermediate scalar encoding; 4=AgX unclamped stops (positive only); 5=LookLog candidate | domain = 1 | Expert | Raw-state UI predicate is approximate; effective identity can differ, see §14. Scene-Y preservation does not follow from encoded-coordinate luminance constraints. |
| M11 | `Crosstalk_m00` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 1 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M12 | `Crosstalk_m01` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 0 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M13 | `Crosstalk_m02` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 0 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M21 | `Crosstalk_m10` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 0 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M22 | `Crosstalk_m11` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 1 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M23 | `Crosstalk_m12` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 0 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M31 | `Crosstalk_m20` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 0 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M32 | `Crosstalk_m21` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 0 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| M33 | `Crosstalk_m22` | Literal authored 3×3 RGB/encoded-coordinate coefficient | 1 | coefficient | -8…8 | Effective matrix and constraints; Mix > 0 | Expert | Row constraints may override diagonal degrees of freedom; authored matrix is not necessarily effective matrix. |
| Matrix constraints | `Crosstalk_mode` | Constrain matrix after authored entries/interactions | 1 | choice / configuration | 0=Unrestricted; 1=Neutral-preserving (row sums = 1); 2=Row-sum locked; 3=Luminance preserving | Full-controls model | Expert | Raw-state UI predicate is approximate; effective identity can differ, see §14. Scene-Y preservation does not follow from encoded-coordinate luminance constraints. |
| Processing domain | `Crosstalk_domain` | Select linear RGB versus encoded scalar coordinates | 0 | choice / configuration | 0=Scene Linear; 1=Selected look coordinate | Full-controls model | Expert | Raw-state UI predicate is approximate; effective identity can differ, see §14. Scene-Y preservation does not follow from encoded-coordinate luminance constraints. |
| Locked row sum | `Crosstalk_rowSum` | Set common row sum in Row-sum locked mode | 1 | factor | -4…4 | mode = 2 | Expert | Raw-state UI predicate is approximate; effective identity can differ, see §14. Scene-Y preservation does not follow from encoded-coordinate luminance constraints. |
| Mix | `Crosstalk_mix` | Interpolate constrained matrix with identity | 1 | fraction | 0…1 | Authored matrix/interactions or UI macro predicate nonneutral | Expert | Raw-state UI predicate is approximate; effective identity can differ, see §14. Scene-Y preservation does not follow from encoded-coordinate luminance constraints. |
| rg interaction | `Crosstalk_rg` | Add off-diagonal rg interaction and subtract same amount from its row diagonal | 0 | coefficient | -2…2 | Mix > 0 | Advanced | Names are stored interaction labels; matrix row/column relationship is explicit in §4. |
| rb interaction | `Crosstalk_rb` | Add off-diagonal rb interaction and subtract same amount from its row diagonal | 0 | coefficient | -2…2 | Mix > 0 | Advanced | Names are stored interaction labels; matrix row/column relationship is explicit in §4. |
| gr interaction | `Crosstalk_gr` | Add off-diagonal gr interaction and subtract same amount from its row diagonal | 0 | coefficient | -2…2 | Mix > 0 | Advanced | Names are stored interaction labels; matrix row/column relationship is explicit in §4. |
| gb interaction | `Crosstalk_gb` | Add off-diagonal gb interaction and subtract same amount from its row diagonal | 0 | coefficient | -2…2 | Mix > 0 | Advanced | Names are stored interaction labels; matrix row/column relationship is explicit in §4. |
| br interaction | `Crosstalk_br` | Add off-diagonal br interaction and subtract same amount from its row diagonal | 0 | coefficient | -2…2 | Mix > 0 | Advanced | Names are stored interaction labels; matrix row/column relationship is explicit in §4. |
| bg interaction | `Crosstalk_bg` | Add off-diagonal bg interaction and subtract same amount from its row diagonal | 0 | coefficient | -2…2 | Mix > 0 | Advanced | Names are stored interaction labels; matrix row/column relationship is explicit in §4. |

### Input / Compatibility

| Label | Persistent ID | Purpose / underlying operation | Default (not always identity) | Units | Artist range / choices | Dependencies | Layer | Important limitations |
|---|---|---|---|---|---|---|---|---|
| Source interpretation | `interpretation` | Interpret input primaries/white only; Auto recognizes scene-linear metadata/OCIO role | 0 | choice / configuration | 0=Auto / scene_linear or metadata; 1=Linear Rec.2020; 2=ACEScg / AP1; 3=Linear Rec.709; 4=Custom xy primaries / white | Always | configuration | Manual does not convert input pixels; unknown Auto fails explicitly. |
| RGB / alpha handling | `alphaMode` | RGB as supplied or explicit unpremultiply/process/premultiply | 0 | choice / configuration | 0=RGB as supplied; 1=Unpremultiply / process / premultiply | Always | configuration | Alpha copied; zero-alpha original RGB retained in unpremultiply mode. |
| rx | `rx` | Custom red primary CIE x coordinate | 0.708 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| ry | `ry` | Custom red primary CIE y coordinate | 0.292 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| gx | `gx` | Custom green primary CIE x coordinate | 0.17 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| gy | `gy` | Custom green primary CIE y coordinate | 0.797 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| bx | `bx` | Custom blue primary CIE x coordinate | 0.131 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| by | `by` | Custom blue primary CIE y coordinate | 0.046 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| wx | `wx` | Custom white point CIE x coordinate | 0.3127 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| wy | `wy` | Custom white point CIE y coordinate | 0.329 | xy | 0…1 | interpretation = 4 (Custom) | configuration | Configuration hidden/disabled otherwise; [0,1] per-coordinate limits do not guarantee a valid invertible gamut. |
| Mathematical model | `modelVersion` | Persistent compatibility/adapter/stage generation, not a creative option | 0 | choice / configuration | 0=Material v1 CPU; 1=v2 restored controls (explicit opt-in); 2=Full controls — bounded composition | Hidden/disabled in ordinary UI | configuration (hidden compatibility) | Index meanings in §11; stored values drive immutable snapshots. |
| Signed adapter | `adapterVersion` | Persistent compatibility/adapter/stage generation, not a creative option | 0 | choice / configuration | 0=v1 documented per model | Hidden/disabled in ordinary UI | configuration (hidden compatibility) | Index meanings in §11; stored values drive immutable snapshots. |
| Density model | `DensityVersion` | Persistent compatibility/adapter/stage generation, not a creative option | 0 | choice / configuration | 0=v1 historical equations | Hidden/disabled in ordinary UI | configuration (hidden compatibility) | Index meanings in §11; stored values drive immutable snapshots. |
| Strip model | `StripVersion` | Persistent compatibility/adapter/stage generation, not a creative option | 0 | choice / configuration | 0=v1 historical equations | Hidden/disabled in ordinary UI | configuration (hidden compatibility) | Index meanings in §11; stored values drive immutable snapshots. |
| Crosstalk model | `CrosstalkVersion` | Persistent compatibility/adapter/stage generation, not a creative option | 0 | choice / configuration | 0=v1 historical equations | Hidden/disabled in ordinary UI | configuration (hidden compatibility) | Index meanings in §11; stored values drive immutable snapshots. |

`semanticReference` is an additional OFX read-only multiline diagnostic string (not in numeric core parameters); hidden in the Nuke artist presentation. `renditionUi_compatibility` is presentation text only, derived from native state, not a second version parameter. `enableFullControls` is a non-evaluating native OFX PushButton (no scalar default/range). Visible through `renditionUi_enableFullControls` only for model indices 0/1; deliberately sets native `modelVersion` to 2 inside an undoable edit.

### Density physical component, selection and chroma behavior

Convert to reference-white XYZ and signed opponent coordinates. Using the compact three-spectrum basis B, `coeff=B^−1 XYZ`, `positive=max(coeff,0)` and `residual=XYZ−B positive`. This is an explicit basis physical-component adapter, **not** a clamp of scene RGB or a claim the residual is physical energy. The material response acts on the positive basis component; the signed residual is restored continuously.

Selection is multiplied by `1−highlightProtection×sigmoid((e−3)/2)` and `1−shadowWeight+shadowWeight×sigmoid((−e+2)/2)`. Default protection and weighting are both 0.5. `abs(density)` selects the compact KM-derived filter; the signed amount chooses filtered-delta direction. Opponent chroma is then adjusted to `Csource×2^(density×chromaCoupling)`, followed by selection-weighted delta blending. Material depth can change Y and hue; no “deeper without any darkening” guarantee is made. This is not an HK compensation mode.

### Strip records, recombination and anchors

Three-channel keeps three compact basis records; two-channel distributes the middle record equally to the two outer records; custom basis uses the authored transformed record basis and its inverse. Records are not film layers or recovered physical spectra. Stored `bContribution`/`bWeight` act on basis x, `g*` on y, `r*` on z. Thus the r/g/b labels are record conventions, **not** literal working-gamut channel gains.

Leakage blends positive records toward their mean with `leak=leakage×separation`. A custom transform may create signed record coefficients; the positive part receives spectral-derived processing while a signed record residual is retained. Palette shaping raises normalized positive-record proportions to power `2^(separation×palette)` and restores their sum. Contributions apply before material filtering; recombination weights apply after basis inversion of the filtered XYZ and before inverse custom-record transform. Filter concentration is `separation×(0.6+0.4×density)`.

Final blend is `XYZ + (reconstructedXYZ−XYZ)×separation×neutralWeight×redWeight×mix`, where `neutralWeight=1−neutralAnchor+neutralAnchor×smooth(0,0.05,relativeChroma)` and `redWeight=1−redAnchor×(1−smooth(20,70,angularDistance(hue,29)))`. Anchors protect existing deformation; they do not create colour or guarantee exact skin identification. Global Crosstalk is a subsequent separate stage, not an extra Strip runtime switch. Full spectral, Neugebauer, Beer–Lambert and KM research alternatives are not production model choices here.

Index-2 **Record N gain / Record N from M** controls are mapped safety coordinates (equations §8), not literal M11…M33 RGB coefficients. Legacy raw custom-basis equations remain renderable. The Nuke adapter currently uses gain/bias captions for stored legacy and current instances alike; compatibility context must distinguish their actual meaning (§14).

## 6. What worked

| Decision | Concrete evidence | Contract |
|---|---|---|
| Base → Palette → Material everyday architecture | Three shared-core front ends, explicit fixed stage order; 0.3 pipeline tests | Preserve workflow rather than require eight deep nodes |
| Artistically successful grading feel | User feedback quoted in §1 | Preserve rendered look; feedback does not erase outstanding gates |
| Compact Main | Native Artist group first; 13/9/8 controls; restarted screenshots | Secondary depth does not expand Main |
| Deep controls accessible again | 0.31 appended namespaced native banks; direct-linked tab write-through | Engines remain available, no UI-only grade copies |
| Six-family model retained | Original-coordinate overlap tests; six independent persistent banks | Families are not sequential qualifiers |
| One selected-family editor | 0.32 Red/Cyan/Magenta/undo screenshots; independent animation and reload checks | Retarget links, never copy state |
| Full matrix access | Actual 3×3 numeric editors, constraints/domain adjacent; active-Mix checks | Macro slider never replaces literal expert authorship |
| Explicit deep domains | Six encoding/operator response and animation/reload checks; independent round trips | Domain is per connected operator, not global gamut/log switch |
| OFX authoritative state / no duplicated grade | Native parameter IDs, immutable snapshots; self-relative Link_Knob writes; rename/copy/reload tests | Presentation cannot own a second grading value |
| Bounded composition | 160 legal composed configurations per new model, endpoint and signed/HDR tests; reproduced historical failures fixed in index 2 | Prevent invalid engine state by mapping, not error-catching or pixel repair |
| Compatibility separated | Hidden model parameters, explicit undoable migration, exact old-binary float-bit regressions | Saved appearance and current artist workflow are distinct |

## 7. What did not work — postmortem

| Symptom | Root cause | Why the approach was wrong | Current solution | General lesson |
|---|---|---|---|---|
| Six huge family blocks | Technical completeness expressed as repeated UI | Height/scroll made normal editing cumbersome | One selected-family direct-link editor | Inventory completeness is not interaction quality |
| Hidden five blocks still leave blank gaps | Nuke reserves hidden layout/group space | Visibility alone did not produce reusable layout | One actual editor retargeted to native family | Inspect real panel geometry after hiding |
| OFX Pages did not become useful tabs | Observed Nuke 17 host presentation limitation | Spec descriptors do not prove host presentation | Native descriptors retained; narrow Tab_Knob fallback | Probe host behavior before choosing architecture |
| Closed groups did not reveal children reliably | Native OFX group/disclosure behavior in Nuke | Checked-open control still inaccessible | Linked secondary tabs | Enumeration is not reachability |
| Secret source controls removed linked editors | Nuke links need their native targets available | Only link labels survived | Source layout hidden by Nuke presentation, not dynamic Secret | Separate source availability from visible editor |
| OFX/Python visibility callbacks fought | Two owners changed Secret/visibility | Stale/conflicting UI | Nuke-specific Secret updates omitted; adapter owns visible layout | One presentation owner per host |
| Valid Main + Expert sliders caused render errors | Additive/multiplicative effective values exceeded engine ranges | Artist needed another knob reduced before normal dragging | Versioned index-2 headroom mapping; old index-1 editing contained | Entire combined displayed domain must be valid |
| Prominent v1/v2 switching | Implementation chronology shown as creative model | Artist had to reason about compatibility while grading | Hidden stored versions, explicit migration/status | Compatibility is not a look intention |
| Custom xy fields active under Auto | Applicability not reflected in UI | Config looked like inert grading controls | Hidden in Nuke/disabled natively outside Custom | Show relevant configuration only |
| Pivot/protection/coupling/leakage/anchors looked active when ineffective | Missing dependency presentation | Knob implied an independent operation | Conditional native/link Enabled and hints | Distinguish setting an operation from protecting one |
| Identity matrix Mix active | Missing identity dependency | Blend with identity has no effect | Raw matrix/interactions gate Mix; effective-identity caveats remain | Prefer evaluated-operation dependency, not arbitrary knob activity |
| Base tint rule disabled Palette hue biases | Same ID spelling matched unrelated semantics | Cross-node name matching created false dependency | Base-only condition; fresh Palette screenshot/regression | Scope dependencies to effect and operation |
| Selectors treated as additive to 360° macro width (0.31 intermediate) | Generic composition applied to absolute selection | Narrow width remained ineffective | Absolute Expert selectors | Selectors and deformation amounts have different composition contracts |
| Link enabled flag did not disable actual editor | Native target editor still enabled | Presentation appeared applicable despite disabled alias | Set native target Enabled too | Verify editor behavior, not link metadata |
| Main blank after group hiding; matrix sliders not removed by link flags | Native group ordering/end markers and target flags | Cosmetic link changes left underlying layout artifacts | Artist group defined first; target SLIDER flag cleared; numeric row STARTLINE arrangement | Presentation flags often need native-target application |

These are recorded failures, including intermediate unsuccessful fixes. Do not repeat them merely because a new presentation implementation is easier to build.

## 8. Main ↔ Expert composition contract

### Stored index 0 — original 0.3

Compute the Main macro stages exactly as §4/§5. New prefixed Expert fields must equal their neutral stored defaults; any nondefault restored value fails explicit opt-in validation. Crossover width’s neutral stored Expert value is 360°, although the standalone Crossover width factory default is 90°. No stored Expert state is written by a Main control.

### Stored index 1 — 0.31 restored equations

1. Choices, debug and selection fields are absolute Expert values. Family selection includes hue/width/chroma/exposure bounds/softness/neutral protection.
2. Chroma scale fields (`chroma`, dark/mid/bright Chroma, family `_chroma` excluding bounds) use `effective=macro×Expert`.
3. Strip Separation uses `1−(1−macro)(1−Expert)`.
4. Other scalar fields use `effective=macro+Expert−engineDefault`.
5. Expert Crossover hue/channel and Volume family hue-displacement deltas additionally multiply by Main `trajectory`.
6. Matrix entries/interaction deltas compose before the existing matrix constraints and Mix; selectors are not macro-modulated.
7. Child snapshots validate effective ranges. Red chroma 4 plus Separation 0.1 produced 4.1; Density Expert 1 plus Main 0.1 produced 1.1. These remain explicit historical failures, not secretly corrected equations. Unsafe ordinary editing is contained in 0.32 by read-only grade controls for index 1.

### Stored index 2 — exact remaining-headroom formulation

Apply absolute choices/debug/selectors as above. For every remaining scalar let b be its macro stage value (or engine default if no macro supplies it), e its persistent Expert value, e0 its engine default, and [lo,hi] the legal child-engine interval:

```text
delta = e − e0
span  = (delta >= 0) ? (hi − e0) : (e0 − lo)
f     = (span > 0) ? delta / span : 0

if f ==  1: effective = hi
if f == −1: effective = lo
otherwise: effective = b + f × ((f >= 0) ? (hi − b) : (b − lo))
```

This is the actual piecewise mapping, including zero-span and exact endpoint handling. Neutral Expert f=0 preserves Main base b. Neutral Main b=e0 preserves ordinary Expert scalar behavior, subject to the explicit trajectory/custom-basis exceptions below. Legal endpoints remain legal child-engine endpoints. Main and Expert compose at immutable snapshot evaluation; changing Main never rewrites an Expert knob. Image RGB is neither clipped nor repaired by this mapping. Unsupported nonfinite/out-of-range externally supplied parameters still error explicitly.

**Trajectory exception:** before headroom evaluation, for Crossover dark/mid/bright Hue, all channel-displacement fields, and Volume family hueDelta:

```text
T = Main trajectory (0…2; neutral 1)
f = (T == 0) ? 0 : T × f / (1 + (T − 1) × abs(f))
```

T=1 leaves Expert deflection unchanged. T=0 removes eligible Expert deflection. It does not suppress Expert chroma/density/matrix or globally fade the node. Main hue bases already use T in §4. This rational mapping keeps eligible normalized deflections in [−1,1].

**Strip Separation exception:** remains `1−(1−b)(1−e)`, rather than generic headroom evaluation.

**Intervals:** after composition, for each matched chromaMin prefix sort chromaMin/chromaMax and evMin/evMax in the immutable effective stage if reversed; Crossover darkPivot/brightPivot are also sorted when reversed. Values are swapped only in evaluated state. Stored knobs and animation are not rewritten. Endpoints crossing form a continuous interval at equality, not a hard error; this is index-2 behavior only.

**Strip custom basis safety:** after scalar composition, every Strip row r uses its resulting raw entries u:

```text
gain_r  = 2^((u_rr − 1)/4)
total_r = 1 + Σ_(c != r) abs(u_rc)
M_rr    = gain_r
M_rc    = 0.75 × gain_r × u_rc / total_r      (c != r)
```

Applied to the derived Strip stage even when custom mode is not selected; it affects rendering only where the Strip engine uses that custom basis. Each row has positive diagonal and sum of absolute off-diagonal entries <0.75×diagonal, ensuring strict row diagonal dominance/invertibility. Identity raw basis remains identity. The raw editor range [−8,8] is not the effective coefficient range. **Neutral Main does not make these mapped coordinates equal legacy literal matrix coefficients.** Index 0/1 retain their raw historical basis equations.

**Base paired ranges:** existing Base model and validation remain; only display bounds depend on the paired stored knob:

```text
toeStart displayed:       [−20, min(4, shoulderStart)]
shoulderStart displayed:  [max(−4, toeStart), 20]
shadowRange displayed:    [−20, min(4, highlightRange)]
highlightRange displayed: [max(−4, shadowRange), 20]
```

Neither paired knob is rewritten. Native OFX DisplayMin/Max and Nuke target ranges implement this. Numeric/external reversed pairs remain explicit errors. This is different from index-2 Palette/Material interval sorting. Base Highlight Burn composition is given in §3; it is not a generic prefixed Main/Expert merge.

## 9. Central dependency contract

“Disabled” describes the editor, not deletion of stored processing state. All ordinary visibility/Enabled changes below retain stored values and animation. The migration action is the explicit exception: it changes modelVersion on user request. A processing dependency is the mathematical prerequisite for image effect; a presentation dependency is the currently implemented UI predicate, which is sometimes only an approximation.

| Control / IDs | Processing dependency | Current presentation active when | Otherwise | Does presentation change stored grade? |
|---|---|---|---|---|
| Custom rx/ry/gx/gy/bx/by/wx/wy | Custom input interpretation | interpretation=4 | Nuke hidden; native disabled | No |
| Base Pivot | Nonidentity desired tone needs anchor | P: contrast≠1 or any of shadowCompression, highlightCompression, midExposure, midDensity, blackStops, whiteLevel, colourBalance, brillianceReduction, highlightBurn nonzero | Disabled | No |
| Base shadowHue / highlightHue | Nonzero corresponding tint | shadowTint≠0 / highlightTint≠0 | Disabled | No |
| Base deathStart/deathSoftness | Colour Death | colourDeath≠0 | Disabled | No |
| Base localProtection/localChroma | Local exposure | localExposure≠0 | Disabled | No |
| Base localCenter/localSoftness | Protected local exposure | localExposure≠0 and localProtection≠0 | Disabled | No |
| Base toe/shoulder start, softness, range centers/softness, retention | Related tonal/colour operation must affect source for visible response | Generally editable; pair display bounds enforced | Values can be inert at neutral tone/tint; not all are disabled | No |
| Material Main coupling | Effective Density amount nonzero | Main density≠0 or restored Density_density≠0 | Disabled | No |
| Material Main leakage/anchor | Existing Strip separation/deformation | Any Main depth/separation or restored Strip_separation nonzero | Disabled | No |
| Density selectors/coupling/protection/shadowWeight | Nonzero effective amount; selection/content | Same Density activation predicate; Density_density/debug exempt | Disabled when amount macros neutral | No |
| Strip leakage/density/palette/neutralAnchor/redAnchor | Effective Strip separation plus nonzero mix | Any Main depth/separation or restored Strip_separation nonzero | Disabled | No |
| Strip contribution/weight/mix | Effective Strip separation/deformation | Available in full-controls model, not all share a separation gate | May remain editable without immediate effect | No |
| Strip custom m00…m22 | Custom record mode | Strip_mode=2 | Disabled | No |
| Palette opponent trajectory Hue/Chroma/Density | Crossover_mode=0 | mode=0 | Nuke hidden in channel mode; native mode-dependent Enabled | No |
| Palette channel dark/mid/bright r/g/b | Crossover_mode=1 | mode=1 | Nuke hidden in hue mode; native mode-dependent Enabled | No |
| Crossover_lookDomain | Channel encode/decode path | mode=1 | Disabled | No |
| Opponent Crossover selectors | Hue mode only | Current Advanced editors remain available in full-controls model | May look editable in channel mode although engine ignores them | No |
| Palette Main Shadow/Highlight Hue Bias and Colour Death | Hue trajectory mode and membership | Main remains editable; Base tint rule deliberately does not apply | No mode-based hiding implemented for these Main macros | No |
| Global Crosstalk_lookDomain | Encoded-coordinate matrix path | Crosstalk_domain=1 | Disabled | No |
| Crosstalk_rowSum | Row-sum locked constraint | Crosstalk_mode=2 | Disabled | No |
| Crosstalk_mix | Effective nonidentity matrix | Any raw matrix≠I, Expert interaction≠0, or Main crosstalk/contamination≠0 | Disabled by raw predicate | No; predicate exceptions in §14 |
| Volume_vN_matrixMix | Nonidentity family local matrix | Any selected family raw entry≠I | Disabled at identity | No |
| Family selection parameters | Nonidentity family deformation/debug and source membership | Selected family editor; full-controls model | Others hidden through editor retargeting, not erased | No |
| Hidden model/adapter/stage versions | Persisted processing generation | Not ordinary creative editors | Hidden/disabled | No |
| Prefixed restored Expert controls at index 0 | Explicit full-controls generation | Not editable in legacy macro workflow | Disabled (neutral values needed to render) | No |
| Palette/Material grade controls at index 1 | Historical equations render, but editing can exceed composed ranges | Ordinary grade editing disabled | Read-only; Input remains editable | No |
| enableFullControls | Deliberate compatibility migration | Palette/Material index≠2 | Hidden once index 2; Base secret/disabled | **Yes only on deliberate click**, modelVersion→2, undoable |

No claim is made that every current UI predicate perfectly detects effective processing activity. The inventory/dependency table preserves the present implementation, including remaining inert-condition cases, rather than silently specifying a proposed fix.

## 10. Processing-domain contract

External input and normal output remain scene-linear RGB in the interpreted working gamut (Rec.2020, AP1, Rec.709 or valid Custom). Internal conversion/encoding is not a change of external primaries. No global “Log Space” switch exists.

| Operation | Actual internal representation | Domain choice / limitations |
|---|---|---|
| Base | Reference XYZ + zero-Y signed residual + signed-magnitude stop coordinate | No selectable camera-log encoding. Base tint hue uses fixed projected Rec.2020 RGB artist circle |
| Palette Volume | D65 XYZ → signed cube-root Oklab-like opponent extension | Our signed algebraic extension, not claimed native perception of arbitrary negative RGB. Local matrix delta stays linear input-gamut RGB |
| Palette hue Crossover | Signed opponent deformation with exposure-conditioned trajectory | Exposure selector uses ACEScct-normalized Y; no selected look encoding in this mode |
| Palette channel Crossover | Per-channel selected scalar encode → normalized displacement → inverse | Crossover_lookDomain, ACEScct default; opponent selectors not used |
| Palette final Primaries | Historical XYZ/residual tonal tint path | Fixed macro midBalance/midTint; does not use Crossover’s encoding selector |
| Material Density/Strip | Compact spectral-derived three-basis filtering plus signed residual; opponent selection/chroma | No log/domain runtime switch; Full Spectral remains offline oracle |
| Palette/Material Crosstalk | Raw working-gamut linear RGB or selected scalar encoded RGB | Crosstalk_domain + Crosstalk_lookDomain; gamut-relative channel relationships |
| Advanced Scene | Exposure/RGB exposure/illuminant/CAT/custom matrix in linear; SOP/saturation linear or selected scalar coordinates | cdlDomain chooses SOP branch; lookDomain does not globally encode all Scene operations |
| Advanced Tone | Selected scalar look coordinates → normalized shaping → inverse; linked/per-channel | lookDomain, pivot/extents in normalized approximate stops; not Base’s tone model |
| Advanced Crossover | Opponent hue mode or independently encoded RGB channel mode | Exclusive mode; selected look relevant only channel |
| Advanced Crosstalk | Linear or selected encoded matrix | Constraint semantics apply in selected coordinates |
| Inspector / explicit selection diagnostics | Analysis coordinates / diagnostic RGB | Diagnostic output is not necessarily a scene rendition; it must not be treated as the authored grade |

Scalar encoding IDs are unchanged and not aliases:

| ID | Encoding | Exact implemented forward form / signed domain |
|---|---|---|
| 0 | Pure stops | log2(x/0.18), **x>0 only** |
| 1 | ACEScct (default) | x≤0.0078125: 10.5402377416545x+0.0729055341958355; otherwise (log2(x)+9.72)/17.52; linear lower branch includes signed values |
| 2 | LogC4 scalar | Defined analytical LogC4 log branch with linear lower continuation; constants in shared kernel; not an ARRI gamut conversion |
| 3 | DaVinci Intermediate scalar | x≤0.00262409: 10.44426855x; otherwise (log2(x+0.0075)+7)×0.07329248; signed lower branch |
| 4 | Unclamped AgX-style stops | (log2(x/0.18)+10)/16.5, **x>0 only**; not AgX gamut/tone/display transform |
| 5 | LookLog candidate | b=0.18/64; x≤b: −6+(x−b)/(b ln 2); otherwise log2(x/0.18); project-defined lower extension |

Normalized channel coordinate uses slope 1, 1/17.52, (928/1023)/14, 0.07329248, 1/16.5, 1 for IDs 0…5 respectively. The shared kernel implements exact inverse branches. Pure stops and AgX-style stops may yield related normalized behavior by construction; they are not silently mapped to the same choice. They reject zero/negative samples in active paths. This **domain error is not fixed by bounded parameter composition**; default identity bypass can avoid evaluating an otherwise unused encoding.

Round-trip/middle-gray/signed/HDR and operator/domain response tests are documented in the 0.31 report. They do not certify every combined domain/animation state or full derivative/predictability behavior. Density/Strip physical adapters separate unsupported signed information explicitly; `max(positive basis coefficients,0)` is not silent `max(scene RGB,0)`.

## 11. Compatibility/versioning contract

| Stored generation | Meaning | Render / ordinary edit contract |
|---|---|---|
| Base modelVersion=0 | Preserved monotonic Base model | Unchanged equations, normal artist editing |
| Palette/Material modelVersion=0 | Original 0.3 macros | Default restored Expert values only; historical macro appearance; deeper editors inactive |
| Palette/Material modelVersion=1 | 0.31 restored additive/multiplicative composition | Old equations still render; grade UI read-only to contain unsafe editing; Input editable |
| Palette/Material modelVersion=2 | 0.32 bounded candidate | Safe composition plus sorted intervals and mapped custom Strip basis; full-controls editor |

Historical float-bit rendering fixtures compare against independently built pre-0.32 code; real 0.3/0.31 native project state, animation, copy/paste, rename and reload checks pass within documented coverage. Exact historical equations are preserved; exhaustive reproduction of every possible old project is not claimed from finite fixtures.

Model version is persisted compatibility state, not a creative v1/v2/v3 dropdown. Adapter/stage-version choices are fixed metadata in this generation. Old reports call index 0 “v1” and index 1 “v2 restored”; the new index 2 is **not** that old v2. Use stored indices and dates to avoid ambiguous chronology.

Migration through Enable full controls sets modelVersion=2 inside an OFX edit transaction. It is explicit and undoable, can change an existing Expert grade, and must **not** be called appearance-preserving. Loading, showing a panel, selecting a family, or touching Main never migrates or rewrites another grade parameter.

The descriptor default remains historical index **0**, because old scripts may omit parameters saved at their default. New nodes currently remain index 0. Future recommendation, **after acceptance only**: the artist menu factory may explicitly initialize newly created nodes to the current accepted model. Do not change the OFX descriptor default, silently migrate OnCreate/OnScriptLoad, or infer compatibility from metadata. This recommendation is not implemented by this documentation pass.

## 12. OFX versus Nuke presentation findings

| OFX owns | Nuke presentation adapter owns |
|---|---|
| Persistent creative values/IDs, animation, time-evaluated render snapshots, stored model generations | Useful Tab_Knob layout and linked secondary editors |
| Render-time validation and conditional Enabled where portable | Selected-family link retargeting, matrix numeric row layout |
| Native selector/button IDs; explicit undoable model edit | Visibility, native target/link enabled application, host-specific layout flags/workarounds |
| Input interpretation and external colour semantics | Concise compatibility status text, hidden presentation marker/cache |

Standard OFX Pages/PageChild/page order, Group/Parent/order/open state, Choice, Enabled, Hint, Secret, DisplayMin/Max and PushButton were implemented/investigated first. Native Nuke 17 probe without the fallback showed Pages did not give the required tab UI; closed groups checked open without reliably revealing children; Secret native controls lost linked editors; hiding controls/groups could reserve gaps.

Current fallback is **Tab_Knob + self-relative Link_Knob (`this`, real native ID)**, no duplicate Double_Knob creative state. Native Main stays directly visible. Secondary native layout is hidden by the adapter while real parameters remain available for links. Matrix target SLIDER flag is cleared and STARTLINE arranges rows; clearing only alias flags was insufficient. Native Artist group is defined first to avoid blank Main; its persistent identity remains Artist, displayed as Main.

All six family banks exist; `renditionUiFamily_<suffix>` links are retargeted, never synchronized through copied values. Historical per-family aliases remain hidden/addressable for saved expressions. Presentation callbacks are guarded and refresh dependency state on change/showPanel/frame/undo-related UI updates; cached signatures prevent continuous unnecessary refresh. They do not write grading values. Nuke-specific Secret updates are skipped so OFX callbacks do not fight adapter visibility. The explicit migration callback is the sole deliberate processing-version edit in this system.

Observed Nuke limitations are host-specific, not a claim that OFX universally lacks groups/pages. NDK remains an interaction reference only; the processing plugin remains OFX. Flame’s presentation has not been accepted.

## 13. Controls that should NOT return to ordinary artist UI

| Excluded from ordinary Main workflow | Reason / proper home |
|---|---|
| Full spectral reconstruction/basis coefficients, measured-material research parameters | Offline oracle/research; not production runtime switches |
| HK experiments / perceived-brightness research knobs | Did not become accepted production artist parameters |
| Neugebauer/KM/Beer–Lambert alternative runtime choices | Reference classes, not everyday accepted model options |
| Raw Jacobian, nonfinite, distribution/gradient diagnostics | Inspector/reference assistance, not automatic grade. Current Volume_debug and Density_debug remain explicit Advanced diagnostics; do not pretend they are absent |
| Compatibility generation dropdown as creative model | Hidden persisted compatibility; deliberate migration/status only |
| Irrelevant custom-primary xy fields under standard interpretation | Configuration applicable only to Custom |
| Hundreds of selectors/matrices on Main | Advanced/Expert depth remains available through organized pages |
| Literal historical Primaries black offset or its reversal-prone tone equations copied into Base | Historical Advanced nodes preserve them; Base has different permanent semantics |
| Film stocks, negative/print/scanner processes, grain, halation, optical/spatial controls | SpektraFilm/Pigment ownership; not restored colour-control depth |

## 14. Known open issues and documentation discrepancies

Current unresolved acceptance is limited to: full continuous mouse dragging across every secondary page/connected Viewer; new bounded-model default promotion; final artist predictability/usability acceptance; Flame presentation; host Metal. Offline Metal parity is not host GPU acceptance. Presets remain stopped. Artist feedback is positive; these engineering/interaction gates still remain open.

Source inspection also exposes the following concrete ambiguities/mismatches; they are recorded **without implementation changes**:

| Finding | As-implemented interpretation |
|---|---|
| “21” family controls in intermediate descriptions | Actual schema has 22: 7 deformation/neutral fields + 5 range/softness fields + 9 matrix entries + Mix. UI-only selector is additional |
| Blanket “neutral Main preserves Expert behavior” | True for ordinary scalar headroom at default trajectory; custom Strip basis transformation and trajectory modulation are explicit exceptions |
| Blanket “bounded ranges prevent all errors” | Bounds prevent composed-range errors in new model, not invalid interpretation, nonfinite input, positive-only encoding domain failures or corrupt external values |
| Crosstalk Mix UI predicate versus effective matrix | Current predicate includes Main contamination in Palette although that macro is final Primaries tint; it omits Palette Main separation although that macro alters rg/bg. Constraints can also cancel raw diagonal changes. Enabled is therefore not exact effective-identity detection |
| Density/Strip activation predicates use individual amount knobs | Opposed Main and Expert amounts can compose to zero while both appear nonneutral, leaving dependent controls enabled; current predicate is conservative, not exact evaluated-state activity |
| Channel mode and Main/Advanced selectors | Opponent selectors remain editable on Advanced but are unused by channel engine; Main hue biases/Colour Death also remain visible/editable although only hue branch uses them |
| Record gain/bias captions apply to legacy raw bases too | Adapter labels are not version-conditional; indices 0/1 still use raw coefficient semantics. Read compatibility context; do not retroactively describe old matrices as gain coordinates |
| Existing unit suffix “model v2 composed expert state” | Historical 0.31 wording in serialized metadata; not evidence every field uses index 2. Inventory strips this suffix for unit clarity while keeping original parameter meaning |
| Base Black says “zero stays zero” | Base tone/Black alone preserves zero; mixed-sign zero-Y samples with chromatic residual or subsequent local/chromatic operations need full pipeline interpretation, not an RGB output floor claim |

These do not authorize fixes in this pass or a new mathematical research campaign. Future proposals must identify their measured processing/UI scope and preserve output unless explicitly versioned.

## 15. Primary evidence and source navigation

- [src/core/artist_models.cpp](/Users/j7s/coding/gripcolorOFX/src/core/artist_models.cpp) — Artist definitions, exact macro bases, historical/current composition, Base Burn and local exposure.

- [src/core/primaries.cpp](/Users/j7s/coding/gripcolorOFX/src/core/primaries.cpp) — Base/Primaries defaults, tone construction and chromatic residual/tint semantics.

- [src/core/operators.cpp](/Users/j7s/coding/gripcolorOFX/src/core/operators.cpp) — Parameter choices/ranges, snapshot validation, matrix constraints and artist execution.

- [include/rendition/kernel_math.hpp](/Users/j7s/coding/gripcolorOFX/include/rendition/kernel_math.hpp) — Actual encoding/inverse, signed opponent, selector, Volume, Crossover, Density and Strip equations.

- [src/ofx/plugin.cpp](/Users/j7s/coding/gripcolorOFX/src/ofx/plugin.cpp) — Native OFX descriptors, source/Matte handling, conditional enabled/display bounds and migration.

- [include/rendition/ui_layout.hpp](/Users/j7s/coding/gripcolorOFX/include/rendition/ui_layout.hpp) — Native OFX page categorization.

- [integrations/nuke/rendition_ui.py](/Users/j7s/coding/gripcolorOFX/integrations/nuke/rendition_ui.py) — Actual Nuke page ordering, one-family links, conditional presentation and compatibility.

- [integrations/nuke/artist-groups.json](/Users/j7s/coding/gripcolorOFX/integrations/nuke/artist-groups.json) — Native parameter grouping inventory, including all six banks.

- [integrations/nuke/rendition_legacy_ui.py](/Users/j7s/coding/gripcolorOFX/integrations/nuke/rendition_legacy_ui.py) — Preserved historical deep-node presentation.

- [docs/interfaces.json](/Users/j7s/coding/gripcolorOFX/docs/interfaces.json) — Serialized parameter IDs, defaults, units, ranges and choices.

- [docs/ARTIST_ARCHITECTURE_0_3.md](/Users/j7s/coding/gripcolorOFX/docs/ARTIST_ARCHITECTURE_0_3.md) — Original artist front-end and monotonic/matte contract.

- [docs/ARTIST_CONTROL_RESTORATION_0_31.md](/Users/j7s/coding/gripcolorOFX/docs/ARTIST_CONTROL_RESTORATION_0_31.md) — Restoration mapping, historical additive behavior, response evidence and limitations.

- [docs/NUKE_UX_0.32.md](/Users/j7s/coding/gripcolorOFX/docs/NUKE_UX_0.32.md) — Reproduced UX failures, failed intermediate fixes and corrected candidate status.

- [docs/PIPELINE_CONTRACT.md](/Users/j7s/coding/gripcolorOFX/docs/PIPELINE_CONTRACT.md) — Pigment, SpektraFilm and display ownership/routing.

- [docs/design/base.md](/Users/j7s/coding/gripcolorOFX/docs/design/base.md) — Base design-document pointer.

- [docs/design/palette.md](/Users/j7s/coding/gripcolorOFX/docs/design/palette.md) — Palette design-document pointer.

- [docs/design/material.md](/Users/j7s/coding/gripcolorOFX/docs/design/material.md) — Material design-document pointer.

- [tests/test_ux_safety.py](/Users/j7s/coding/gripcolorOFX/tests/test_ux_safety.py) — Composition/endpoints, reproduced failures and historical exact-bit tests.

- [tests/fixtures/legacy-0.31.json](/Users/j7s/coding/gripcolorOFX/tests/fixtures/legacy-0.31.json) — Pre-0.32 historical render fixture.

- [tests/test_restored_controls.py](/Users/j7s/coding/gripcolorOFX/tests/test_restored_controls.py) — Opt-in, deterministic non-destructive composition, domains/selectors.

- [tests/test_artist_architecture.py](/Users/j7s/coding/gripcolorOFX/tests/test_artist_architecture.py) — Base monotonicity, matte, alpha, signed/HDR and artist stack contracts.

- [tests/test_core.py](/Users/j7s/coding/gripcolorOFX/tests/test_core.py) — Interpretation, conversion and encoding references.

- [tools/nuke_ux32.py](/Users/j7s/coding/gripcolorOFX/tools/nuke_ux32.py) — Ten host persistence/render/dependency checks and approved tagged-sample fixture.

- [build/ux-0.32/host-checks.json](/Users/j7s/coding/gripcolorOFX/build/ux-0.32/host-checks.json) — Existing host results; read, not rerun in this documentation pass.

- [build/ux-0.32/index.html](/Users/j7s/coding/gripcolorOFX/build/ux-0.32/index.html) — Existing actual screenshots and report.

- [build/control-audit-0.31/index.html](/Users/j7s/coding/gripcolorOFX/build/control-audit-0.31/index.html) — Existing parameter-response sheets/domain/restoration evidence.

## NON-NEGOTIABLE INVARIANTS

1. Preserve current grading behavior unless a specific processing defect is demonstrated.
2. Historical saved grades must remain reproducible.
3. OFX state is authoritative.
4. Host presentation must not duplicate grading state.
5. Normal visible control ranges must not create invalid render states; configuration/domain limitations must remain explicit.
6. Main controls must remain compact.
7. Expert depth must remain available.
8. Compatibility/versioning is not an everyday creative control.
9. Internal log/opponent/spectral domains remain explicit per operator and distinct from the external working gamut.
10. Pigment, SpektraFilm and the authored DRT retain their existing ownership boundaries.
11. Do not reopen broad spectral/color-model research without a concrete observed failure.
12. UI refactors must be output-identical unless explicitly versioned otherwise.
