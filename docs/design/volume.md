# Rendition Volume — v1 research candidate
1. Input: known scene-linear RGB.
2. Internal: D65-adapted XYZ → Oklab algebraic signed extension; not a change of working gamut.
3. Change: continuous region-weighted vectors in Cartesian opponent coordinates plus optional local RGB matrix deltas.
4. Output: scene-compatible rendition; perceptual validity only claimed on valid color-model stimuli.
5. Exposure: hue/chroma-only normalized selection aims for equivariance; EV selection and density/exposure controls are conditioned.
6. Negatives: real cube roots are our explicit signed algebraic adapter, not a published perceptual claim.
7. HDR: homogeneous cube-root scale; selection chroma is C/|L|; EV derives from positive Y, with smooth signed luminance coordinate for invalid/nonpositive Y.
8. Inverse: forward deformation need not be globally invertible.
9. Neutrals: continuous chroma-distance protection; no undefined hue-driven change at zero chroma.
10. Gamut: colorimetric coordinate operations; local RGB matrices intentionally gamut-relative.
11. Failures: strong overlaps can fold a field; normalized accumulation bounds aggregate influence, not a proof of invertibility.
12. Purpose: localized multidimensional color-volume editing through six artist families.
All weights sample original source coordinates. Weighted deltas: sum(w_i*d_i). Normalized: sum(w_i*d_i)/max(1,sum(w_i)) with a continuous but derivative-kink normalization. Bounded: normalized direction with tanh-bounded magnitude. Shared field: accumulate weighted angular/log-chroma/exposure velocities, normalize, then apply one deformation. No region is applied sequentially. Unchanged regions do not dilute active regions. Cartesian deltas avoid discontinuous angular averaging across hue wrap. The retained comparison report supports normalized deltas as the development default; artist and wider parameter acceptance remain pending.
References: Ottosson Oklab/Colour, independently designed region field. Tests: permutations, red/magenta overlaps, hue seams, adapters, near neutrals, cross-gamut, parameter sweeps.
