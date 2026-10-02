# Rendition Crosstalk — v1 research candidate
1. Input: known scene-linear RGB.
2. Internal: RGB or selected scalar look coordinates.
3. Change: explicit matrix M and mix.
4. Output: scene-compatible rendition.
5. Exposure: linear matrices equivariant; encoded matrix behavior generally non-equivariant.
6. Negatives: native matrix; selected encoder supplies its documented domain.
7. HDR: unbounded within float limits.
8. Inverse: nonsingular effective matrix and invertible encoding.
9. Neutral constraints: row sums = 1 preserve both axis and magnitude. Common row sum s preserves the axis in coordinates but changes magnitude. Neither property implies preserving luminance.
10. Gamut: intentionally RGB-gamut-relative.
11. Failures: singular matrices are allowed forward transforms; overflow is an error.
12. Purpose: channel interaction independently inspectable from other operations.
Derivations: neutral preserving adjusts each diagonal so sum_j M_ij=1. Row-sum locked replaces 1 with user s. Luminance preserving projects columns: M'=M+1*(l^T-l^T M)/(l^T 1), where l is the working RGB Y row. Artist off-diagonal additions and compensating diagonals are included in the visible effective matrix report. Mix: (1-t)I+tM.
References: independent linear algebra, ASWF host interfaces. Tests distinguish identity, neutral axis, neutral magnitude, luminance, and gamut-relative behavior.
