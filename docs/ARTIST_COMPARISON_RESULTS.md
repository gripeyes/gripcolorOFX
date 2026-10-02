# M15–M17 comparison results

User-approved sources/references: ACES_ODT_SampleFrames-main, frames 4/5/7/14/23/60. Source AP0/D60 is verified and converted explicitly through the user configuration to Linear Rec.2020. Every comparison uses sRGB / Flawed Emulsion 2. Scene EXRs retain signed/HDR values and alpha; PNGs clip only after the view.

Six M15 editable starting recipes were reused on eight contents (two synthetic plus six photographic/CG), with finite RGB and unchanged alpha. This demonstrates executable/reusable settings, not successful visual grammar. Desired variants and human scores remain pending.

## M16: five reference attempts

Only existing Scene/Volume/Density/Crossover/Strip parameters were used; no added LUT, stock transform or masks. Five bounded controls are fitted per case, with other authored settings explicit. Palette quantiles/covariance after the fixed DRT are diagnostic objectives, not spatial/image-reconstruction scores. Human time is deliberately null.

| Target | Reference / source / second content (frame) | Nodes | Changed controls | Solver seconds | Converged |
|---|---|---|---|---|---|
| cold_cyan | 4 / 60 / 7 | 2 | 6 | 0.083 | True |
| bronze_olive | 14 / 7 / 60 | 3 | 9 | 0.210 | True |
| near_black | 23 / 60 / 4 | 2 | 7 | 0.158 | True |
| red_accent | 7 / 60 / 14 | 3 | 7 | 0.199 | True |
| low_key_skin | 5 / 7 / 60 | 3 | 9 | 0.162 | True |

Visual inspection of the cold/cyan attempt shows a darker image but does not reconstruct the neon reference’s cyan distribution or hierarchy. This is a concrete limitation of the current short recipe/descriptor fit; it does not justify rejecting the coordinate model. Content/lighting differs substantially (LEGO café versus neon street), and additional artist-authored parameters may be needed. No reference case is marked artist-successful automatically. Inspect all reference/candidate/second-content panels before identifying model changes.

## M17: held-out simple-baseline fits

Seed 1717, 600 training and 1,200 held-out samples across -8 to +8 EV; reports break errors down by hue family and exposure. Errors below are relative scene RGB RMS, not perceptual scores or usefulness thresholds. Parameters fitted on synthetic samples were also reused unchanged on faces, red jacket and LEGO content.

| Candidate | Baseline | Held-out relative RGB RMS | Parameters |
|---|---|---|---|
| Density | Exposure + Saturation | 0.12921 | 2 |
| Density | Exposure + Saturation with identical selection | 0.12243 | 2 |
| Strip | 3x3 Matrix | 0.06126 | 9 |
| Strip | 3x3 Matrix + monotone per-channel curves | 0.06170 | 30 |
| Volume | Hue-vs-Hue / Hue-vs-Chroma curves | 0.02429 | 24 |
| Crossover | Three smooth luminance keys | 0.00965 | 9 |
| Crossover | Three hard luminance keys diagnostic | 0.03077 | 9 |

Density differs numerically from exposure+saturation, including with matched selection. Strip differs from the tested matrix/curves; its curves fit has slightly worse held-out error than the matrix alone, so extra parameters have not improved this challenge. The smooth luminance-key baseline closely approximates this Crossover configuration; convenience, continuity and broader trajectories must justify the node. Fits are limited local optimizations/settings, not proofs that baselines cannot reproduce a candidate.

Density and Strip remain research candidates. Artist comparisons must establish better control, continuity, coherence, speed or unavailable useful behaviour; numerical non-equivalence alone passes none of these. Signed/HDR/compositing baseline stress, artist-tuned alternatives and human timing remain gaps.

All existing CTest suites pass; artist verification additionally checks signed/HDR EXR round trips, monotone baseline identity, finite scene outputs, saved eight-node UI evidence and Nuke/CPU fixture samples. Full report files and editable graph are included in the local artist package. Broad literature expansion is stopped; next work is feedback and repeatable targeted deficiencies.
