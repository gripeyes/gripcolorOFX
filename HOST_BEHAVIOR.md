# Host behavior and acceptance

## Nuke 17.0v1 / macOS arm64

Development tests use an isolated terminal process and `OFX_PLUGIN_PATH=build`, not system installation. Exact plugin classes are `OFXorg.gripcolor.rendition.<Effect>_v1`. Nuke plugin enumeration did not list unloaded OFX effects; creating the exact class successfully loaded the bundle.

Verified by the retained smoke report: eight-effect discovery/default float identity, signed/HDR exposure, parameter animation, matrix/neutral invariants, save/reload of model/domain settings, multiframe CPU rendering to 32-bit float EXR.

Nuke point sampling must pass the frame explicitly (`Node.sample(..., frame=nuke.frame())`); changing the root frame alone did not sample the animated plugin at the new time in this headless test.

The extended host test passes interpretation-required errors and recovery, explicit premultiplication, active creative candidates, Inspector, and user-authored Rec.2020/ACEScg OCIO environments. Its retained report, rather than this checklist alone, is the authority for which cases have passed. Color metadata is not inferred from a filename or the project working-space label.

Inspector uses General context with optional Source in Nuke; disconnected procedural modes use a fixed 1920×1080 canonical domain and alpha 1. Input/difference/gamut/nonfinite modes require Source. Procedural sampling uses pixel centers (`100.5` rather than `100`).

Recoverable interpretation errors are cleared after successful semantic revalidation in IsIdentity: Nuke can query identity before its deferred parameter-change notification. No cache flush is required to recover.

GPU rendering is not advertised. The offline Metal validator can synchronize its own command buffers; that does not validate an OFX asynchronous host path. The plugin rejects unexpected GPU-buffer render requests instead of treating GPU pointers as CPU memory.

Pending: interactive GUI/graph ergonomics, complex real-media workloads, full animation/model compatibility matrix, host tile/PAR/proxy edge cases, and actual OFX Metal buffers/queue/error behavior.

## Flame — early Gate C pending

Flame was not found in standard local installation locations. No Flame behavior is claimed verified. Gate C and production Gate H remain pending, even though independent Nuke/research work proceeds.

Run the CPU candidate immediately when access is available:

1. Discover Scene/Tone/Crosstalk under OFX; select explicit working primaries.
2. Exercise Segment FX, Source FX where applicable, Batch and Batch FX; record unsupported contexts explicitly.
3. Render the structured signed/HDR/neutral/reference fixtures as float, checking RGB range and exact alpha behavior.
4. Animate parameters; compare timeline and Batch renders; save/reload and rerender.
5. Test the user's custom OCIO project without implicit input or output conversion.
6. Record actual clip metadata and capabilities; test Auto with known and unknown tags.
7. Verify CPU operation, concurrent/multiframe behavior, image layout, cancellation, and packaging/signing.
8. Keep Metal disabled until actual buffer/queue support and error propagation are verified.

Record Flame version/build, macOS, hardware, project color management, applicable contexts, test results and numerical differences. Host limitations belong here, not in undocumented alternate creative math.
