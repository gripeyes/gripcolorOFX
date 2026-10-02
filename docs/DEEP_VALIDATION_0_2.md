# 0.2 targeted deep validation — 2026-10-02

The user accepts the current eight nodes as artistically usable. That is a starting point for creative-range development, not a development freeze or a waiver of production gates. This phase addresses recorded M4, M6–M8, M10–M12 and M15–M17 properties. It does not replace the existing models or restart literature discovery. The production creative equation header is unchanged.

Open `build/validation-0.2/index.html` for **Inspector Lab**, also linked from the installed Nuke Rendition menu. The local report brings together Volume geometry, Density HK experiments, colour trajectories, candidate/baseline pictures, palette transport, structural maps and experimental guide layers. All image comparisons use the approved ACES sample frames, explicit Linear Rec.2020 conversion, and the user's existing sRGB / Flawed Emulsion 2 view. Scene EXRs are unclipped; only display previews are bounded. The external user OCIO configuration remains required and is not redistributed.

## Volume geometry (M4)

The shared CPU core now exposes a finite-difference Jacobian of the actual operator, with determinant, descending singular values, condition number and step disagreement. Each column uses central differences at h and h/2, with h = 0.002 × max(|R|, |G|, |B|, 0.18). The denominator is the actual float32 perturbation distance. Relative Frobenius disagreement above 5% marks the estimate unreliable. The identity Jacobian is exactly I. Independent NumPy determinant/SVD checks and a known fourfold exposure scaling validate the diagnostic implementation.

The structured sweep covers 6,552 hue/chroma/exposure samples plus 1,024 signed samples per configuration, five configurations, saved Jacobians, family/exposure statistics and finer-step witnesses. These are external RGB-to-RGB derivatives in Linear Rec.2020, not perceptual metric tensors. Singular values and conditioning depend on the chosen RGB basis. Finite sampling is not a proof of global injectivity or absence of folds.

| Configuration | Reliable / uncertain samples | Reliable det ≤ 0 | Reliable near-singular |
|---|---:|---:|---:|
| Identity | 7,576 / 0 | 0 | 0 |
| Overlapping artist-range example | 5,867 / 1,709 | 209 | 0 |
| Aggressive normalized overlap | 5,294 / 2,282 | 711 | 3 |
| Aggressive bounded accumulation | 5,305 / 2,271 | 1,064 | 5 |
| Intentional chroma-collapse probe | 6,344 / 1,232 | 3,018 | 5,907 |

The overlapping artist-range example includes 111 nonnegative-RGB negative-determinant samples; twelve selected positive witnesses remain negative and reliable at relative step 0.00025. Aggressive normalized and bounded configurations also have stable positive-RGB witnesses. Bounded accumulation does not guarantee an injective deformation. Chroma-collapse samples must be distinguished from orientation reversal; tiny determinant signs near collapse may be numerical. Near-zero signed cube-root geometry and the normalization boundary can make estimates step-sensitive. Magenta in the maps means uncertainty, not a proven fold.

Native Inspector appends modes 11–15: determinant, conditioning, maximum stretch, minimum stretch, step convergence. The collapsed **Volume probe** group configures one family (hue/width/displacement/chroma/density/step). Connect the source entering the Volume being investigated. This is an explicitly configured probe, not automatic inspection of an upstream node; the offline sweep handles multiple regions. Red indicates reliable det ≤ 0; magenta indicates unreliable differentiation. Grayscale remappings are documented in the Inspector design. Alpha is copied with RGB-as-supplied processing. These diagnostic views are CPU-only and expensive (12 Volume evaluations per pixel); no real-time or host Metal claim is made.

Keep the creative Volume model. The measurements justify a documented fold warning, finer-step investigation and visual testing of specific settings. They do not justify silently limiting controls or asserting a global inverse.

## Aggressive creative ranges and simplicity (M12, M15–M17)

Nine configurations use 400 training and 1,100 held-out positive samples, exposure trajectories from −14 to +14 stops, and 1,705 signed/HDR/axis/near-zero stress samples. Baselines have bounded multistart fits selected by training loss, then frozen for held-out samples and three new photographic/CG frames. Reports retain parameters, convergence, control counts and solver times. Human interaction time is unset. Fits are local searches, not proofs of irreducibility or optimal artist tuning.

| Candidate setting | Simple baseline | Held-out relative RGB RMS |
|---|---|---:|
| Density depth / thin | Matched-selection exposure + saturation | 0.1363 / 0.1403 |
| Density skin depth | Matched-selection exposure + saturation | 0.0173 |
| Crossover cyan death / global trajectory | Movable smooth luminance keys with matched selector | 0.0168 / 0.0203 |
| Crossover narrow transition | Movable smooth keys with matched selector | 0.0437 |
| Strip three records / two records / contamination | 3×3 matrix | 0.1574 / 0.1470 / 0.1306 |

Crossover baselines now share the actual continuous selector and ACEScct exposure coordinate. This removes misleading qualifier/near-zero coordinate advantages. The movable-key baseline is much closer to the narrow transition than fixed keys. The skin Density setting is also closely approximated by its simple baseline. Strip's bounded matrix+monotone-curve fit did not improve held-out errors over its matrix fit in these runs. Its additional flexibility does not automatically confer useful behaviour.

All nine candidate settings remain finite on the defined stress set. All eight individually stressed nodes and six reordered Scene/Volume/Density/Crossover/Strip stacks remain finite and preserve alpha bit-for-bit. Finite does not mean tame: the extreme Scene example reaches about 4.6×10^8 RGB. Reports retain magnitude growth, neutral-axis/magnitude changes and order sensitivity instead of repairing pixels.

The contact sheets are an artist test, not an automated verdict. Compare depth versus ordinary darkness, cyan colour death versus keyed hue/chroma change, coherent contamination versus matrix mixing, and neutral/red/skin anchors. Record preferred behaviour, reusable settings, control effort, seams and failure cases. Density and Strip retain research status until useful superiority over simple alternatives is demonstrated. Basic usability is accepted; these stronger claims remain open.

## Helmholtz–Kohlrausch Density experiments (M11)

The existing pinned Colour Hellwig 2022 implementation is a separate appearance oracle. Equal-Y purity sweeps cover red, yellow, green, cyan, blue, magenta and skin, plus neutral controls. Current Density is evaluated at three chroma couplings. The report records Y, J, Q, J_HK, Q_HK, invalid oracle outputs and adaptation-luminance sensitivity (16/64/256 cd/m²).

Conditions are explicit: D65 Yw=100, background Yb=20, Average surround, nominal adaptation luminance 64 cd/m². Scene Y=0.18 maps to oracle XYZ Y=18. Only finite nonnegative XYZ enters the oracle; invalid samples are excluded and counted, never clipped. This setup is an appearance-reference experiment, not a claim of scene perceptual brightness for arbitrary signed/HDR RGB. The published neutral has a small numerical HK term; zero correction is not assumed.

The experiments reveal chroma-dependent model brightness at equal radiometric Y and show how current depth/chroma coupling changes the correlate. They do not establish psychophysical or artist acceptance. No compensation or viewing-condition dependency was added to production Density. Review under the fixed user view before proposing an equation change.

## Palette and structure assistance (M6–M7)

Inspector Lab extracts deterministic compact palettes in signed algebraic Oklab, compares them with the approved independent neon reference, computes balanced entropic transport in a stable log solver and 64 fixed-direction sliced 1D Wasserstein distances. Transport minimizes squared Euclidean coordinate cost plus entropy under palette-mass marginals. The regularization is explicit, derived from median pair cost. Coupling cost is self-biased and regularization-dependent, not a perceptual distance or a look-quality score. Different image content remains a confound. There is no transform-application or automatic-grading API.

Solver residual, iteration count and convergence are retained. Eight of nine image couplings meet the strict 1e−9 marginal target; Strip/frame 5 remains above it after 12,000 iterations and is explicitly unaccepted as a converged solve. Do not silently relax the target. Sliced self-comparison uses matching sampling so sampling noise cannot create a nonzero self distance.

Structure diagnostics compare forward spatial derivatives of Rec.2020 luminance and signed Oklab opponent coordinates. Maps record gradient magnitude ratios, direction cosines, reversals, lost edges and new edges in previously flat regions. Borders are excluded; low source gradients use an explicit threshold. Opponent direction is a four-dimensional spatial/chromatic vector, not a hue-angle or perceptual local-contrast score. Aggressive Density and Strip produce many luminance reversals on faces/red-jacket content; these are review locations, not automatic defects. Opponent-map validity has its own threshold. No spatial filter or neighbourhood operation enters a Rendition node.

## Experimental Rendition–Pigment bridge (M8/M10)

See [bridge contract](design/pigment-bridge.md). Eight soft overlapping palette memberships and a parallel signed RGB residual are exported as data-only EXR weights plus an NPZ with palette, residual and alpha. Partition and reconstruction tests include signed/HDR samples, frozen-palette reuse and exposure changes. Absolute-coordinate memberships are intentionally exposure-conditioned. No physical pigment interpretation or spatial processing is claimed; a future Pigment consumer remains unimplemented.

## Reproduction and pending checks

With the existing repository Python environment/build: `PYTHONPATH=build .venv/bin/python -m diagnostics.run`. `--modules volume,hk,range,stacks,images` selects only these recorded properties. Full Jacobians/layer arrays and plots live in the local package; compact JSON evidence is retained in `docs/reports/0.2-*.json`. The package includes the offline diagnostic source, but its evaluator/environment is built from the repository; Python is outside the OFX runtime.

CTest passes the independent reference suite, native image contract, operator/spectral contract and existing offline Metal parity. New Inspector differential modes are not in the Metal validator and are not host-Metal accepted. The targeted Nuke smoke script is `tools/nuke_inspector_geometry.py`. Historical interactive discovery covers all eight nodes. New 0.2 Nuke execution passes 22 checks: the five mode identity readings, active signed/HDR/zero samples and alpha, animated probe save/reload and native float rendering, plus Auto using the user Rec.2020 scene_linear role. See `reports/0.2-nuke-inspector-geometry.json`. The saved diagnostic graph is `build/artist-tests/Inspector-geometry-0.2.nk`. Flame and host Metal remain pending without blocking this artist phase.

Next work is bounded: inspect the recorded fold witnesses and structure reversals; compare matched baselines on the same viewed frames; try frozen palette guide data in a separate experimental Pigment consumer; record actual artist observations before changing creative math. Unimplemented full multiscale/temporal/perceptual diagnostics are still gaps. M18 remains in force.
