# Compound operation behavior

The structured regression stack is Scene → Volume → Density → Strip → Crossover → Crosstalk. It is also evaluated in reverse on signed/HDR random stimuli. Every stage must retain finite output and unchanged alpha within the documented input domain; invariants are tested independently. Numerical stability does not imply the two orders should match.

Scene exposure before Tone changes where source colors meet the toe and shoulder. Tone before Scene exposure shapes the original exposure relationship, then scales it. Crossover before exposure selects its dark/middle/bright trajectories from the original scene range; exposure before Crossover moves colors through those trajectories. Volume before Density can change the hue family and relative chroma that select the spectral-derived attenuation. Density before Volume edits the resulting attenuated colors. Crosstalk before a selector moves its input color coordinates; after a selector it mixes that selector's completed result.

Volume region order is different: every region samples the same original source, and permutation must change output only within float rounding. There is no sequential region mode in v1.

Use Inspector's exposure/hue/chroma ramps with a connected Reference clip to compare stacks. Preserve the interpretation/domain/model controls in saved projects; do not infer them from a project working-space label. The portable Gate C fixture graph supplies a signed/HDR source and explicit CPU expectations. Real CG and photographic stack evaluation remains an artist/production gate.
