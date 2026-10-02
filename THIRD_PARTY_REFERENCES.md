# Third-party reference ledger

Project code is private/unlicensed pending the user's licensing decision. License category is not an exclusion filter. This ledger distinguishes code reuse, data reuse, source review, and planned research; listing a planned source does not claim its algorithm has been studied or implemented.

| Reference | Pin/source | License / use | Concepts/files reviewed and reuse |
|---|---|---|---|
| ASWF OpenFX | `e40728885390ec16276d11e00025de9b4282060c`, https://github.com/AcademySoftwareFoundation/openfx | BSD-3-Clause | Vendored public headers/native config and license. Reviewed API, Basic/Invert examples, color/GPU interfaces. Adapter implementation is original. Preserve copyright/license notices. |
| Colour Science | 0.4.7, https://github.com/colour-science/colour | BSD-3-Clause; dataset-specific origins recorded separately | Offline dependency. RGB definitions, CAT16/Bradford/XYZ scaling, ACEScct/LogC4/DI scalar transfer functions, Oklab/IPT/JzAzBz/CAM16/Hellwig, CMFs/illuminants, Smits recovery, ColorChecker data. Constants/formulations independently transcribed with reference tests. |
| OpenColorIO | 2.6.0, https://opencolorio.readthedocs.io/en/v2.6.0/api/transforms.html | BSD-3-Clause | Offline dependency; LogCameraTransform tangent toe independently compares custom LookLog. No OCIO runtime linked into OFX. |
| Oklab | https://bottosson.github.io/posts/oklab/ | Original public formulation; Colour BSD implementation used as numerical reference | Published matrices/algebra reviewed. Real cube-root signed extension is ours; no perceptual claim for arbitrary negative stimuli. |
| FilmLight | https://www.filmlight.ltd.uk/pdf/datasheets/FL-BL-DS-1039-Baselight60.pdf and public Base Grade material | Commercial behavioral reference | Exposure-oriented grading, common opponent architecture, localized color editing, look authorship. No implementation code reused or proprietary reconstruction attempted. |
| PBRT | https://pbr-book.org/4ed/Radiometry%2C_Spectra%2C_and_Color | Book/software have separate licensing | Public spectral representation/illuminant distinctions reviewed. No code reused. |
| Jakob & Hanika | https://rgl.epfl.ch/publications/Jakob2019Spectral | Paper and linked code require separate attribution/license review | Spectral upsampling problem and parameterization reviewed. Full reconstruction implementation not integrated. |
| Kubelka–Munk / Beer–Lambert / Demichel / Neugebauer / Yule–Nielsen | Classical mathematical models | Formulations, not imported implementation code | Original Python reference equations and synthetic absorption/scattering curves. No historical material accuracy claimed. |
| User-authored OCIO configs | Local `authored-DRTs/config-2020.ocio`, `config-acescg-ocio2.4.ocio` | User project | Host environment tests only. No DRT processing code or transform contents reused. |

## Required follow-up research, not yet claimed complete

- ACES 2.x core: Apache-2.0; compare its actual JMh architecture separately from Hellwig's published model.
- IPT thesis / Ebner–Fairchild hue-uniformity paper; Braun/Fairchild/Ebner hue-linearized gamut mapping; Safdar JzAzBz; Hellwig/Fairchild brightness papers: deepen scientific target/trajectory validation.
- OpenDRT and gamut-compress: review GPL/other exact repository licenses before any reuse; no source code imported here.
- OFX ports of OpenDRT: host/GPU architecture references, not copied processing code.
- Yedlin Display Prep methodology, cone concepts, MIT Tetra community reconstruction, Calvin's reconstruction and free-DCTL baselines: independent geometry comparison remains open.
- MonoNodes Color Shift/Shaper/Twist/Bend/Crosstalk/Split Tone and PixelTools Three/Strip: public behavior/control benchmarks only; no reverse engineering.
- HCT/Material Color Utilities, Okhsl/Okhsv, Filmic/AgX, Mitsuba, CLF/CTF: further scoped comparisons remain open.

Record exact new files/commits, licensing and any reused code before additional implementation reuse. Existing BSD reference licenses are retained under `third_party/licenses/` and the vendored OpenFX directory. Dataset provenance is not inferred from a software license alone.

## Artist fixtures and offline IO

User approved any frames from the local ACES_ODT_SampleFrames-main dataset. Six AP0/D60 files are explicitly converted through the user OCIO config for artist fixtures. Retain the dataset MIT license (Alex Fry, 2022) and embedded contributor credits; original filenames/hashes are in approved-assets.json. User-authored DRT/config is referenced locally, not copied into the bundle. OpenEXR 3.5.1 is pinned for offline EXR IO only (BSD-3-Clause); its installed license is packaged. No OpenEXR Python dependency enters the OFX runtime.
