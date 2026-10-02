# Artist Primaries / Tonal Colour — dedicated phase

## Decision and interaction study

Implement **B: a new Rendition Primaries node**, as an appended ninth CPU effect. The existing eight remain available with unchanged mathematical behaviour. This is a scene-compatible primary grading prototype, not a replacement for deep colour-volume/material operators or the final authored DRT.

| Placement | Artist workflow | Architectural consequence | Decision |
|---|---|---|---|
| A: expand Tone | One node, but primary colour balance becomes mixed with existing encoding/channel controls | Existing Tone projects require explicit algorithm mode and two sets of semantics | Keep Tone focused |
| B: new Primaries | Named master/blacks/midtones/whites controls, one range model and one saved state | Shared interpretation, CAT, alpha, soft functions and validation; independent versioned primary model | **Selected** |
| C: front-end over nodes | Can hide wiring initially, but multiple selectors, coordinate domains and model versions remain underneath | A panel coordinating several nodes is harder to animate/reload and does not supply one coherent tonal model | May become a future convenience panel, not the processing model |

Only public behavioural/UI descriptions were consulted, not proprietary equations or code. The targeted study is expressly requested by the user and does not reopen general research under M18.

| Reference | Relevant interaction | Adopted principle / boundary |
|---|---|---|
| [Baselight Base Grade](https://www.filmlight.ltd.uk/store/news_articles/lowepost-base-grade-and-the-evolution-of-grading-tools/) | Global controls plus stop-oriented zones, per-zone colour/saturation and adjustable pivot/falloff | Give artists meaningful exposure coordinates and nearby colour controls. Our coordinates, tint plane and tone equations are independently defined. |
| [Baselight X Grade](https://www.filmlight.ltd.uk/pdf/datasheets/FL-BL-DS-1039-Baselight60.pdf) | Multiple smooth corrections in a layer without constructing keys, with visual feedback | A simple primary adjustment should not require a Volume selection setup. No claim to reproduce its proprietary geometry or no-fold guarantees. |
| [Baselight Chromogen](https://www.filmlight.ltd.uk/pdf/datasheets/FL-BL-DS-1039-Baselight60.pdf) | Named colour behaviour including highlight bleaching and brilliance reduction; authored scene looks | Make retention, colour death, bleaching and colourfulness balance explicit. We do not copy its opponent space, stage equations or film behaviour. |
| [Flame MasterGrade](https://help.autodesk.com/cloudhelp/2022/ENU/Flame-EffectsandToolsReference/files/GUID-3A5D8228-E8BC-48CB-8737-B71C6F0934BA.htm) | Scene-linear exposure/contrast/pivot plus black/shadow/midtone/highlight/white controls and range start/width | Separate range edits from grade strength, label photographic units. Do not infer host acceptance from this interaction reference. |
| [Resolve HDR zones](https://documents.blackmagicdesign.com/UserManuals/DaVinci-Resolve-17-Colorist-Guide.pdf) | Zone wheels, exposure/saturation and configurable range/falloff | Compact tonal groups with smoothly overlapping responses; no hard luminance keys. Native wheel custom drawing is deferred; prototype uses hue/amount and balance/tint sliders. |

All five artist groups open initially; Expert and custom colourimetry remain separate. This avoids the initially collapsed group exposure issue observed in Nuke. Portable group identifiers are separate from the visible labels. All requested controls are present. Source interpretation stays explicit/Auto scene_linear. Expert model selection records **Artist Primaries v1 CPU prototype**. Existing effect IDs and indices 0–7 remain unchanged; Primaries is `org.gripcolor.rendition.Primaries`, index 8, effect version 1.0. It is experimental; this does not silently revise an older Tone model.

## One-node tasks

The editable Nuke graph `build/primaries/Rendition-Primaries-artist.nk` has one Source Switch (faces/red jacket/LEGO), seven labelled Primaries nodes, a Target Switch and original/candidate Viewer inputs. The view is the user's **Flawed Emulsion 2 / sRGB**. Raw Reads supply already explicitly converted Linear Rec.2020 fixtures; the OFX adds no input or output display conversion.

| Task | Direct controls |
|---|---|
| Cool the blacks | Shadow hue 240°, tint .35, range −5 stops, softness .7 stops |
| Warm the shadows | Shadow hue 35°, tint .3 |
| Make whites creamier | Highlight hue 50°, tint .2, bleaching .65, range +1.5 stops |
| Hold highlights down | Highlight compression .9, shoulder start +2, softness 1.5, white level −.5 stops |
| Keep colour alive deeper into toe | Shadow compression .55, retention 1.3; colour death .7 starting at −12, softness 1.5 |
| Let colour die smoothly into black | Colour death 1, start −5, softness 1.2 |
| Pale green skin highlights | Highlight hue 120°, tint .35, bleach .8, range −.5, softness 1.2 |

The green recipe was increased after fixed-view comparison of .14/.35/.65 strengths; this is a preset refinement, not an equation change. It affects all colours in the highlight range, not only skin. True zero-energy black stays black unless Black level is explicitly changed. Hue is an ordinary artist RGB hue circle (0 red, 60 yellow, 120 green, 180 cyan, 240 blue, 300 magenta); it is not a perceptually uniform hue measurement or illuminant temperature.

## Mandatory operator statement

1. **Input:** explicitly interpreted scene-linear RGB in Rec.2020/D65, AP1/D60, Rec.709/D65 or custom colourimetry. No guessed gamut.
2. **Representation:** shared RGB→XYZ and CAT to a D65 reference, signed Y plus zero-Y XYZ residual; soft magnitude-stop coordinate for zones. The external gamut remains unchanged.
3. **Relationship changed:** authored luminance relationships, source chroma amplitude and additive zero-Y tonal tint, with separate toe/shoulder, range and chroma-survival controls.
4. **Reference:** scene-compatible, scene-referred creative tone formation with no viewing illuminant, physical print renderer or display white cap. It intentionally changes scene relationships; it is not radiometric reconstruction.
5. **Exposure:** generally exposure-conditioned. Exposure-only scales RGB approximately equivariantly. Zone centres stay relative to 0.18 after Master Exposure, so changing exposure changes participation deliberately.
6. **Negatives:** retained through signed tone gain and signed zero-Y residual, never clamped to zero. Zone selection uses |Y| magnitude; negative values have algebraic rather than physical brightness meaning. Mixed-sign Y≈0 chroma can remain large and must be reviewed.
7. **HDR:** unbounded gain/offset and colour; no output cap or hidden gamut compression. Float overflow is an explicit render error, not pixel repair. Tests cover signed inputs through ±16 EV; this is not a guarantee for arbitrary float extremes.
8. **Inverse:** no global inverse promised for the combined grade. Chroma death/bleaching at extremes and aggressive range-dependent gains may destroy information.
9. **Neutrals:** retained when tint/balance is zero. Neutral magnitude changes with explicit tone/exposure/level controls. Tint, saturation and bleach alone preserve radiometric reference Y within round-trip tolerance, not perceived brightness.
10. **Gamut:** colourimetric D65 operation with fixed Rec.2020-defined artist tint directions. Equivalent XYZ stimuli agree across the three supported gamuts; these directions never change with host metadata.
11. **Failures:** very narrow/strong zonal exposure may reverse tone; offsets can cross zero; large tints/retention can expand gamut; hue direction is continuous but not C1 at RGB hue-sector joins. No perceptual-brightness promise for arbitrary signed/HDR values or for the user's DRT. CPU-only, no new host Metal acceptance.
12. **Separate purpose:** fast basic image formation and tonal colour control, without configuring hue-volume deformations, crossover trajectories or material-depth processing. Density balance here is explicitly nonphysical; spectral Density/Strip remain separate.

## Mathematical contract

Let x be D65 XYZ, W the unit-Y D65 white and r=x−W Y. Apply Master Exposure k=2^E to Y and r. Use epsilon=0.18×2^−20, and e=log2((|kY|+epsilon)/0.18). This smooth magnitude floor is an explicit coordinate adapter, not clipping of RGB or Y. Stop labels are asymptotically photographic stops above the floor; derivative is finite near zero. Negative brightness is not treated as native published appearance-model perception.

Raw shadow/highlight responses are logistic((shadowRange−e)/shadowSoftness) and logistic((e−highlightRange)/highlightSoftness). Raw midtone response is (1−s)(1−h). Normalize all three by their sum to form nonnegative overlapping weights with unit sum. All selections use the same post-Master-Exposure source e, before local deformation. Nonzero softness is enforced; reversed shadow/highlight or toe/shoulder centres fail clearly.

Contrast is the positive signed gain ((|kY|+epsilon)/(0.18×2^pivot+epsilon))^(contrast−1). The toe/shoulder displacement is contrast times the pivot-anchored difference of T(e), where T(z)=0.45 shadowCompression toeSoftness softplus((toeStart−z)/toeSoftness) − 0.45 highlightCompression shoulderSoftness softplus((z−shoulderStart)/shoulderSoftness). This shares the core's stable softplus/logistic primitives. Compression-only asymptotic slope contributions are bounded; multiplying the tail contribution by contrast preserves positive scalar slope at low contrast. Existing Tone's equations/parameters are not replaced.

Additional gain is 2^[midWeight(midExposure−midDensity)+highlightWeight whiteLevel]. Black level is a separate linear Y offset times shadow weight. White level is an exposure adjustment, never an imposed scene white bound. Extremely strong, narrow gain changes can reverse the combined curve; the prototype records this explicitly rather than claiming every configuration is monotonic.

Colourfulness q = ||(rX,rZ)|| / sqrt(||(rX,rZ)||²+(kY)²+epsilon²) is bounded without clipping the colour. Density/colourfulness balance b adds a gain 2^−(b+highlightWeight brillianceReduction)q, and source chroma gain 2^(0.25 bq). It is a documented artistic coupling, not optical density or a spectral model.

Source residual chroma is multiplied by tone gain, saturation, weighted retention and (1−highlightWeight bleaching). Hue directions are fixed-reference RGB rays projected as d=XYZ(ray)−W Y(ray). Midtone cool/warm and magenta/green axes use similarly projected fixed RGB directions. Weighted tint is added with magnitude 0.3|Yout|. The colour-death factor is 1−death sigmoid((deathStart−e)/deathSoftness), applied to source chroma and tonal tint. A final zero-Y projection removes floating leakage. Output is W Yout + residual, transformed back through inverse CAT/RGB conversion.

Bleaching removes source colour before highlight tint is added: it can make green-tinted highlights pale without forcing their endpoint to neutral white. It is not a DRT. Contrast/black offset, brilliance and colourfulness balance intentionally change Y; chroma-only controls do not. All scaling and remapping constants are explicit above and in `src/core/primaries.cpp`.

## Validation and artist gate

Six new tests exercise exact default identity (including preserved nonfinites under bypass), inactive range controls, alpha/zero-alpha workflow, Y preservation, chroma death and direct cool/green tint, curve continuity and positive compression-only slopes, signed/HDR handling, explicit overflow/invalid ranges and equivalent XYZ cross-gamut results. Existing suites also pass. Existing offline Metal parity covers only previous models, not this CPU prototype.

Twenty-one viewed source/candidate comparisons cover seven tasks on three approved frames. They retain unclipped scene EXRs, settings, changed-control counts and unset human interaction/preference fields. About .38 seconds per 640×360 frame was measured in the local headless evaluator; this is a single-run prototype timing, not a full-resolution host benchmark or real-time promise.

The −20 to +20 EV neutral sweep has no reversals for identity, contrast 1.4, full toe/shoulder compression or midtone lift +1 with default softness. A deliberately narrow +4-stop midtone lift shows 66 reversed intervals. That is a concrete range limitation awaiting a targeted monotonic model or explicit protection design; widen softness/reduce zonal displacement for the current artist prototype. Do not grant production status solely because the seven pictures look plausible.

Basic eight-node usability remains accepted. This ninth-node phase needs artist judgement of speed, feel, tint direction, useful black/toe and white/shoulder behaviour, range adjustment and reuse. Complete the observation fields in `build/primaries/artist-review.json` (regeneration preserves this separate review file); solver/render time is not human effort. Flame and host Metal remain pending and do not block this CPU artist evaluation.
