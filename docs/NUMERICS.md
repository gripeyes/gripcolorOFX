# Numerical policy and measured amendments

CPU float32 processing is authoritative. Matrix construction/inversion/CAT setup uses double, then the shared pixel kernel uses float. Fast math and multiply/add contraction are disabled in both CPU and Metal builds. The same kernel equations execute on both backends.

## Conversion tolerance

Initial round-trip target is `2e-6 + 2e-5 * abs(reference component)`. Signed RGB matrix round trips can cancel large components: tests additionally report a vector-scale bound `2e-6 + 2e-5 * max(abs(input RGB))`. This does not permit clipping or conceal a failed color-model domain.

## Metal tolerance amendment

The baseline remains `5e-6 + 5e-5 * abs(CPU component)`. On M2, independently rounded transcendental operations followed by opponent/RGB recombination produced small differences in channels near cancellation. Recombining values of hundreds into a channel near zero makes a component-relative test ill-conditioned.

For RGB channels with `abs(CPU component) < 0.02 * max(abs(CPU RGB))`, the validator additionally permits `1e-6 * max(abs(CPU RGB))`. All other channels retain the baseline. Alpha remains unchanged and is separately tested. The report retains **strict-component failure counts**, amended ratios, absolute errors, and vector-relative errors; no baseline failure is silently discarded. This is an offline candidate parity criterion, not permission to claim production GPU host acceptance.

The initial experiment also found an actual CPU problem: computing identity saturation through `L + (RGB-L)` lost encoded precision for strongly signed inputs. Identity saturation now bypasses arithmetic; nonidentity saturation uses `s*RGB + (1-s)*L`. Linked Tone's original negative-luminance guide produced enormous positive coordinate displacements on mixed-sign HDR pixels; its guide is now the explicit maximum absolute channel magnitude. No perceptual-luminance claim is made for this envelope.

The portable `softplus` uses a short Taylor branch for `log(1+x)` below 0.01 because Metal does not provide `log1p`. This is shared with CPU and tested through scalar monotonicity and parity.

## Spectral approximation

The oracle integrates 360–830 nm at 1 nm with Colour-compatible explicit quadrature. The compact model stores 129 response levels per material family. Held-out normalized response-matrix error must remain below 0.0005. This is separate from conversion tolerances and does not imply perceptual indistinguishability.

All signed spectral information is explicit: `XYZ = B * positive_coefficients + signed_residual`. A smooth positive split uses `0.5*(c + sqrt(c*c + (0.001*norm(c))^2))`; its residual is restored. It is homogeneous under positive exposure scale and continuous at signed boundaries. The runtime evaluates preintegrated basis responses; it has no wavelength loop.

## Range and failure semantics

Unknown interpretation fails before any bypass. Known default identity copies original pixel bits, including alpha and nonfinite input. Active processing with nonfinite RGB fails except named diagnostics. Unsupported pure-stop inputs fail explicitly. Arithmetic beyond the finite float representable range is an error, not an implicit RGB clamp.

Tone's approximate stop coordinates diverge from physical stops in each encoding's toe. Volume's EV selector uses D65-adapted Y encoded through the documented ACEScct toe for signed/nonpositive Y; this extension is not physical EV. Signed Oklab is an algebraic adapter, not a claim of meaningful perception for negative stimuli.
