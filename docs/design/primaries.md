# Rendition Primaries — Artist Primaries v1 CPU prototype

The authoritative twelve-question statement, mathematical equations, A/B/C placement decision, behavioural/UI source comparison, units and known limitations are in [Artist Primaries](../ARTIST_PRIMARIES.md).

External gamut/encoding: explicitly interpreted scene-linear RGB, unchanged on output. Internal representation: D65 XYZ signed Y plus zero-Y chromatic residual; normalized soft magnitude-stop ranges. Output: unbounded scene-compatible authored primary grade. No display conversion, physical material simulation, gamut compression or spatial processing. Default identity is bit-exact; alpha uses the existing shared workflow. Effect index 8 is appended; indices 0–7 retain their existing behaviour. Model version 0 names this v1 experimental CPU prototype; do not silently revise it after freezing production behaviour.
