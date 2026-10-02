# Rendition Crossover — v1 research candidate
1. Input: known scene-linear RGB.
2. Internal: signed-adapted Oklab for hue trajectories; selected scalar look coordinate for channel trajectories.
3. Change: smooth dark/mid/bright hue/chroma/density or channel displacement.
4. Output: scene-compatible rendition.
5. Exposure: intentionally conditioned.
6. Negatives: signed opponent adapter / selected encoder.
7. HDR: smooth exposure trajectories; no hard luminance keys or clipping.
8. Inverse: no global inverse promised.
9. Neutrals: protected in hue mode; channel mode may deliberately tint them.
10. Gamut: hue mode colorimetric, channel mode gamut-relative.
11. Failures: excessive rotations, unsupported pure stops, extreme overflow.
12. Purpose: exposure-evolving color relationships independent of Volume and Tone.
Math: dark=1-sigmoid((EV-darkPivot)/width), bright=sigmoid((EV-brightPivot)/width), mid=1-dark-bright; ordered pivots ensure nonnegative weights. Shortest-angle hue contributions and scale/density contributions sample original input. Channel mode evaluates its trajectory from each original channel's normalized look coordinate.
References: original smooth trajectory design; MonoNodes behavioral concept only. Tests: continuity, hue wraps, exposure sweeps, channel crossover, compound stacks.
