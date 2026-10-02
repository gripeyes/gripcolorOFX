# Offline research system

Python is not linked into OFX. Use the pinned environment in requirements-lock.txt and the shared-core evaluator built by CMake. The reference scripts use Colour and OCIO independently of the C++ implementation. Output artifacts are regenerated under output/; reference evidence snapshots are retained in ../docs/reports/.

- domains.py compares six scalar encodings, float32 round trips, stop sensitivity, centered contrast and an independent OCIO tangent-toe implementation. Nonpositive tonal outputs have no physical stop coordinate and are omitted from the stop plot, not repaired.
- coordinates.py compares IPT, Oklab, JzAzBz, CAM16-UCS, Hellwig JMh and an original XYZ opponent baseline. It separates viewing-condition/absolute-luminance models from scale-homogeneous algebra.
- adapters.py evaluates five complete coordinate adapters and four spectral signed strategies, with boundary steps, identity, scale and output-growth measurements. Our positive/signed adapters are not claims about published models' native negative domain.
- overlap.py compares all four implemented original-source composition rules and records growth, seams, neutral behavior and region permutation differences.
- exposure.py records 34 configurations across every node and all selectable scalar look domains. Conditioned/non-equivariant results are characterized, not incorrectly rejected as equivariance failures.
- spectral_lab.py integrates the 1 nm oracle, compares four illuminants, reconstructs emitted bases plus signed residuals, and exports versioned appearance-reference material trajectories. Physical reflectances/transmittances stay bounded by their actual semantics; scene-radiance magnitude is separate.
- fit_basis.py generates a validated compact 129-level response table atomically. fit_comparison.py compares polynomial, linear-table and PCHIP candidates on held-out response matrices. The simple convex table evaluator is shared by CPU/Metal; this is not yet a perceptual error criterion.
- benchmarks.py measures single-thread scalar CPU throughput with output allocation. The separate Metal benchmark measures offline command GPU time. Neither establishes host real-time performance.

Initial choices are ACEScct scalar coordinates, our signed Oklab algebra, normalized Volume deltas, and spectral-response basis tables. Choices are documented candidates, not automatic production acceptance. Measured materials, deeper scientific/behavioral comparisons, complete reconstruction-native strategies and real compositing/artist validation remain in the gate ledger.
