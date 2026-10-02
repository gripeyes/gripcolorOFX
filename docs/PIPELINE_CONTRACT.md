# Rendition / Pigment / SpektraFilm / display contract

## A — Rendition only

Scene-linear source → Base → Palette → Material → optional Pigment → authored DRT. Incoming sample Read tags are explicit (ACES2065-1 originals / Linear Rec.2020 fixtures), Raw OFF; Nuke converts into the project's scene_linear role. Rendition Auto only interprets the resulting gamut. No node chooses creative math from metadata. The custom user Flawed Emulsion 2 / sRGB view remains external. Native float source and default-stack comparisons verify the sample translation; photographic/artist intention remains a human gate.

## B — Selected optical effects

Scene-linear source → Rendition → optional Pigment → independently selected, **verified scene-compatible** SpektraFilm optical/material effect → authored DRT. Do not assume a bundle name or an output knob proves scene semantics. Set explicit Linear Rec.2020 input for the tested installed diffuse plugin, or a corresponding known gamut; confirm output encoding, effects enabled and signed/HDR/alpha behavior for the exact version/settings before endorsing the branch.

Installed `org.spektrafilm.diffuse` effect v0.2 was discovered and sampled in Nuke. With its recorded default state, .18 gray remained approximately .179995 and [-.1,.2,4] remained approximately [-.099998,.199995,3.999894], alpha unchanged. This is a narrow pass-through/boundary observation, not active diffusion/spatial/temporal or complete scene-semantic acceptance. Its UI still exposes shared print/output-role controls; the actual branch must be determined from verified operation, not generic labels. Active settings, real frames, bypass equivalence, order, exposure and structure comparisons remain pending.

## C — Full reproduction

Scene-linear source → Rendition → SpektraFilm negative/print/reproduction → **technically appropriate output/display path**. Never append the authored scene DRT blindly. Installed `org.spektrafilm` v0.2 default Print simulation / Display Out SDR / Rec.709 Gamma 2.4 accepts explicit Linear Rec.2020 input. It maps .18 gray to approximately [.489829,.485690,.484884]; [-.1,.2,4] to [.077810,.758903,.875458], with preserved alpha in these probes. Its advertised output role is display-encoded; these values cannot be tagged scene-linear merely because they are carried in float RGB.

The observed UI also offers Display Out HDR and RCM/ACES (Beta), whose only exposed scene output choice is DaVinci Intermediate WideGamut. Neither that log encoding nor a matrix conversion proves scene-referred reference semantics after print reproduction. Those paths are **not validated** here. Vendor-appropriate interpretation/decoding and display management may be needed; a second authored scene DRT risks double rendition. A consciously authored appearance remapping is a separate workflow, not an implicit default.

## Explicit boundaries

Rendition remains useful without SpektraFilm. Material is generic radiance-relative authorship, not a film-stock or physical print simulation. Pigment's membership/matte guides may condition Rendition explicitly, while Pigment owns spatial processing. Base's Matte clip consumes supplied coverage only; no segmentation or filtering is added. Inspector analyses trajectories, geometry, distributions and gradients without auto-grading.

Local native interface and sample probes are reproducible with `tools/nuke_pipeline_probe.py` and `tools/nuke_pipeline_render.py`; reports record installed interfaces/output roles rather than importing commercial code. No vendor binaries, manuals or spectral assets are redistributed. Tests of two constant samples cannot establish production, artistic, spatial or temporal compatibility. This contract identifies the safe routing decision and remaining evidence instead of silently treating every output as scene-linear.
