# Rendition OFX

A macOS arm64 **research/development candidate** for eight separately instantiable color-rendition effects. CPU processing is available in Nuke; shared-equation Metal kernels have an offline validator, but host Metal rendering is deliberately disabled pending asynchronous error-reporting/buffer integration. This is not a production-approved release.

## Build and verify

Requires Xcode with its Metal toolchain, CMake, and Python 3.14 for the pinned research environment. The OFX runtime itself has no Python dependency.

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r research/requirements-lock.txt
cmake -S . -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_OSX_ARCHITECTURES=arm64 -DPython_EXECUTABLE="$PWD/.venv/bin/python"
cmake --build build -j 6
ctest --test-dir build --output-on-failure
```

Bundle: `build/Rendition.ofx.bundle`, ad-hoc signed for local development. Signing for distribution is separate. Disable optional research dependencies with `-DRENDITION_BUILD_PYTHON=OFF`; disable the offline Metal validator with `-DRENDITION_BUILD_METAL_VALIDATOR=OFF` if the compiler/device is unavailable. Native core tests still build.

## Nuke

Install the current-user bundle and normal menu registration, then restart Nuke:

```sh
python3 tools/install_nuke.py
```

All eight effects appear under **Nodes → Rendition** and the main **Rendition** menu. Each was created interactively through that visible menu in Nuke 17.0v1; see [UI verification](docs/reports/nuke-ui-discovery.json). `init.py` is backed up before a named registration block is appended. The installer does not alter other menu entries. To remove the integration, remove that named block and the Rendition folder/bundle in the paths printed by the installer.

Open [the artist graph](build/artist-tests/Rendition-artist-bench.nk), using your local Flawed Emulsion 2 configuration. [Artist evaluation instructions](docs/ARTIST_ACCEPTANCE.md) and [M1–M18 audit](docs/FINAL_ADDENDUM_AUDIT.md) record the outstanding gates. The artist package contains the native bundle, installer, menu, comparison fixtures, graph, reports and feedback template. The OFX binary has no Python dependency; Nuke’s bundled Python/OCIO startup integration resolves Auto interpretation outside pixel processing.

**Select source interpretation before processing.** In Nuke, Auto resolves the active OCIO `scene_linear` role through the installed startup integration and updates on project-config changes, creation, load and before rendering. Other hosts use recognized scene-linear clip metadata. Missing/unsupported/ambiguous Nuke roles fail explicitly; they never fall back to a preset. Unknown metadata fails rendering with `Unspecified / Interpretation Required`; it never assumes Rec.2020. Manual choices interpret incoming values; they do not convert the image into that gamut.

Default controls produce exact RGB/alpha identity. RGB as supplied is the default alpha mode. Explicit unpremultiply/process/premultiply preserves zero-alpha RGB. Alpha is not graded. Nonfinite image data has a diagnostic mode; invalid active processing reports errors rather than repairing pixels by clipping.

## Effects and domains

| Effect | Relationship changed | Internal representation |
|---|---|---|
| Scene | Exposure, estimated illuminant, matrix, signed SOP, saturation | Linear; optional scalar look encoding for SOP |
| Tone | Pivoted contrast, smooth toe/shoulder and density displacements | Selected scalar look encoding, normalized approximate stops |
| Volume | Six families with multidimensional selection and overlapping deformation | D65 XYZ → Oklab with our signed algebraic extension |
| Density | Material-informed depth trajectory and independent chroma coupling | Preintegrated KM basis response + signed XYZ residual |
| Crossover | Exposure-evolving hue/chroma/density or channel relationships | Signed opponent coordinates or selected scalar look encoding |
| Crosstalk | Inspectable channel mixing with explicit matrix constraints | Linear or selected scalar look encoding |
| Strip | Imperfect records, dye interaction, leakage and palette shaping | Preintegrated dye basis response + signed XYZ residual |
| Inspector | Ramps, chart, cube slice, Reference difference, gamut/nonfinite diagnostics | Explicit image diagnostics |

ACEScct is the default scalar look encoding; it does **not** impose AP1 primaries. Custom LookLog remains a comparison candidate. Pure stops and unclamped AgX stop coordinates have an explicitly positive-only domain.

Density/Strip use original synthetic colorants and a three-spectrum radiance basis, not measured film stock or print simulation. Spectral Lab's physical material outputs are appearance references; production candidates use relative attenuation of scene radiance plus a signed residual. Artist/image acceptance remains pending.

Recommended conceptual order is Scene → Tone → Volume → Density → Crossover → Crosstalk/Strip → Pigment → optical/spatial effects → authored DRT. Reordering is intentional and documented; internal Volume region ordering is not.

## Research and evaluation

```sh
PYTHONPATH=build .venv/bin/python research/domains.py
PYTHONPATH=build .venv/bin/python research/coordinates.py
.venv/bin/python research/spectral_lab.py
.venv/bin/python research/fit_basis.py
.venv/bin/python research/fit_comparison.py
.venv/bin/python research/adapters.py
PYTHONPATH=build .venv/bin/python research/overlap.py
PYTHONPATH=build .venv/bin/python research/exposure.py
PYTHONPATH=build .venv/bin/python tools/evaluate.py examples/scene.json
```

The evaluator accepts JSON samples or float32 RGBA `.npy` images. `tools/export_schema.py` exports parameters/semantics from C++ definitions. Plots, datasets, and raw reports are regenerated into `research/output/`; retained report snapshots live in `docs/reports/`.

See [gate status](docs/GATES.md), [operator designs](docs/design/), [numerical policy](docs/NUMERICS.md), [host behavior](HOST_BEHAVIOR.md), [provenance](THIRD_PARTY_REFERENCES.md), and [spectral data sources](SPECTRAL_DATA_SOURCES.md).

Pending production requirements include Flame validation, real CG/photographic/artist acceptance, remaining comparative research, complete saved-model compatibility coverage, and OFX Metal host integration. No gate is marked passed solely because an image looks attractive or an algorithm is sophisticated.

## Portable early host fixtures

`tools/nuke_fixtures.py` generates signed/HDR, exposure and alpha-band float EXRs, Scene/Tone/Crosstalk expected outputs, a Nuke graph and a JSON manifest under `build/fixtures`. Use these with the Flame checklist in `HOST_BEHAVIOR.md`; they do not claim Flame acceptance. `tools/package_candidate.py` archives the local signed CPU bundle, fixture set, documentation and retained reports with a SHA-256 manifest.
