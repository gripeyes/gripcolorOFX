# Rendition 0.33 — architecture consolidation

This is an architecture refactor of the accepted 0.32 candidate, not a new processing generation. [RENDITION_CONTROL_SYSTEM_0_32.md](RENDITION_CONTROL_SYSTEM_0_32.md) remains the artist-control and rendered-behavior contract. Base → Palette → Material and the historical Advanced engines remain intact. Presets/recipes remain stopped.

## Responsibility boundaries

| Layer | Authority | Implementation | Must not do |
|---|---|---|---|
| Rendition Core | Color equations, operator composition, immutable evaluated snapshots | [`src/core/`](../src/core/), [`include/rendition/operators.hpp`](../include/rendition/operators.hpp) | Import Nuke, resolve UI state, depend on presentation callbacks |
| Persistent OFX State | Parameter handles, animation, compatibility generations, action-time reads, interpretation bridge | [`src/ofx/persistent_state.hpp`](../src/ofx/persistent_state.hpp); descriptor/create/action plumbing in [`plugin.cpp`](../src/ofx/plugin.cpp) | Use a Python proxy as grading state; evaluate presentation to choose processing |
| Portable presentation properties | Enabled/Secret/display-range properties in change/create actions | [`src/ofx/presentation.hpp`](../src/ofx/presentation.hpp), generated [`ui_layout.hpp`](../include/rendition/ui_layout.hpp) | Write parameter values, migrate grades during refresh, run from render |
| Host-independent presentation policy | Read-only evaluation of the declarative schema | [`rendition_presentation.py`](../integrations/nuke/rendition_presentation.py) | Import Nuke or the color core; mutate its value reader |
| Nuke presentation adapter | Tabs, direct linked editors, selected-family retargeting, matrix layout, editor flags/status | [`rendition_ui.py`](../integrations/nuke/rendition_ui.py) | Store a second grade, compose processing, rewrite another grading knob |

The persistent-state extraction preserves the original timed-read bodies. The render function still owns its Output before calling those readers. The historical Advanced presentation delegates to the existing `rendition_legacy_ui.py`; it is not remodeled by this phase. Historical native property rules remain a compatibility path in `presentation.hpp`.

The Nuke OCIO interpretation bridge, `rendition_host.py`, remains separate from presentation. Its existing nonpersistent `hostSceneLinear` value describes input interpretation only; it does not select creative models. Deliberate migration remains the existing compiled OFX button action. Neither bridge nor migration is a dependency refresh.

## One declarative presentation contract

[`presentation/control_system.json`](../presentation/control_system.json) specifies:

| Schema field | Contract |
|---|---|
| `groups`, `effects[].controls` | Exact persistent IDs, labels, default/range/choice metadata and existing group order; synthetic configuration/editor controls explicitly distinguished |
| `controls[].page`, `effects[].pages` | Portable OFX descriptor page assignments and ordered Nuke editor pages respectively; these intentionally differ for hidden family-bank links |
| `enabled`, `native_enabled` | Existing linked-editor and portable native Enabled predicates |
| `visible`, `native_secret` | Existing Nuke visibility and portable Secret predicates |
| `predicates` | Shared read-only expression definitions; comparisons, conjunction/disjunction, value reads and min/max; no grading writes |
| `display_range` | Base paired display bounds, retaining the 0.32 behavior |
| `family_editor` | Six-bank selector, persistent source prefix, one ordered reusable direct-link editor, historical matrix flag behavior |
| `matrix` | Row/column and operation role; one adapter implementation for both global Crosstalk matrices and family/Strip layouts |
| `compatibility_status` | Existing informational text; normal creative controls do not expose model generations |
| `composition_policies`, `composition_contract` | Frozen-generation/headroom/trajectory/interval/Strip safety documentation; **metadata only**, not host-side processing |
| `host_presentation` | Existing Nuke linked-editor/Secret limitations and portable OFX property policy |

Run `python tools/generate_presentation.py` after an intentional schema edit. It generates the C++ presentation header, `integrations/nuke/presentation-schema.json` and historical group metadata. `--check` detects stale output. Nuke needs no color-core Python module. `tools/export_schema.py` verifies exported parameter groups against this schema before regenerating presentation artifacts; it does not independently invent presentation rules.

The schema mirrors authoritative C++ parameter definitions, rather than replacing them. Regression tests compare every copied definition with the accepted definitions. A label/layout edit cannot silently change an OFX parameter default, ID, numeric interval or equation.

### Read-only refresh

```text
OFX action-time parameter values → portable presentation predicates → editor properties
Nuke native OFX values → schema predicates → linked/native editor flags and ranges
selected family → self-relative links → one of six persistent OFX banks
```

There is no reverse dependency path into grading values. Presentation writes are limited to editor properties, link targets and informational Text_Knob text. Links point to `this.<real parameter>`; there are no generated Double_Knob grading copies. Family selection never copies values between banks. Existing per-bank animation remains authoritative.

Matrix layout uses the same `_add_link` implementation for Palette and Material, with row/column metadata controlling STARTLINE/slider flags. Strip custom-record safety coordinates retain their existing labels and meaning; they are not reinterpreted as literal Crosstalk coefficients. Historical hidden bank-link flag quirks are retained to preserve 0.32 presentation.

Dependency watchers are derived from schema value references, not a second hand-maintained list of knob names. Native OFX and Nuke predicates retain their existing intentional differences—for example channel-mode Enabled versus linked-editor visibility. Existing conservative dependency rules are preserved; this refactor does not claim new processing-activity detection.

Nuke teardown can dispatch knobChanged with a detached Python node wrapper. The adapter treats that as an absent presentation target; render exceptions are unaffected.

## P0 closure and preserved runtime boundary

The canonical 0.32 document is amended with the subsequent P0 resolution and links to its runtime evidence. The render-source comment records why Output ownership precedes parameter evaluation: snapshot-first acquisition reproducibly failed during Nuke Viewer updates, including cases where abort remained false.

```text
Render context → Output acquisition/ownership → timed parameter evaluation
→ immutable snapshot → input acquisition → processing → RAII release
```

No acquisition order, cancellation policy, scheduling declaration or trace behavior changes in 0.33. `RENDITION_SUITE_TRACE=1` remains opt-in. The strengthened mock-host regression requires Output to be the first acquisition, still owned at every timed snapshot read, with no input acquired before those reads. Snapshot failure must release Output exactly once across all twelve registered effects.

## Compatibility

Parameter/effect IDs, parameter ordering/defaults, processing domains, Base/Primaries equations, current bounded composition and Palette/Material generations 0/1/2 are unchanged. Descriptor model default remains historical index 0. This phase does not promote index 2 as a new-node default. Historical index 1 remains renderable with its existing read-only editor containment; migration remains explicit and is not claimed to preserve appearance.

The existing `renditionUi_layout032d` presentation marker and link names remain compatible. Renaming the architecture phase does not force a node rebuild or migrate its grade. Pigment, SpektraFilm and the external authored DRT retain their existing responsibilities.

## Regression evidence

| Check | Result / scope |
|---|---|
| Accepted 0.32 baseline | All twelve parameter inventories identical; 36 Base/Palette/Material cases over seven signed/HDR/neutral samples reproduce exact float32 RGBA bits, including current index 2 |
| Historical processing | Existing independent pre-0.32 saved-equation fixtures continue to pass in `test_ux_safety.py` |
| Adapter parity | Layout order, labels, flags, links, ranges, dependencies and compatibility text compared with archived 0.32 adapter across Base/Palette/Material and generations 0/1/2 |
| No presentation grade writes | Mock real grading setters reject writes; only informational Text accepts `setValue`; tests also compare real value inventories before/after refresh |
| Portable descriptor pages | All twelve effects compared with the archived 0.32 page assignment implementation |
| Output-first contract | Strict shared mock-host regression plus existing timed-read, cancellation, unavailable-input, fatal-failure, release, concurrency and opt-in-trace tests |
| Nuke 17.0v1 smoke | Fresh terminal process: three artist nodes render; refresh preserves values; all six direct family links, animation, custom-input dependencies, matrices, copy/paste, rename and save/reload pass |

All seven configured CPU/runtime/presentation CTest suites passed. The signed candidate built successfully.

Tests: [`test_presentation.py`](../tests/test_presentation.py), [`presentation.cpp`](../tests/presentation.cpp), [`ofx_runtime.cpp`](../tests/ofx_runtime.cpp), [`test_ux_safety.py`](../tests/test_ux_safety.py). The archived 0.32 presentation implementation is a test fixture only, not a runtime fallback for current artist nodes.

Nuke smoke runner: [`tools/nuke_architecture033.py`](../tools/nuke_architecture033.py). Captured results: `build/architecture-0.33/nuke-smoke.json` and `.log`; persistence fixture: `architecture-smoke.nk`. The process mapped both the existing installed bundle and the candidate build bundle; the smoke explicitly imports the candidate presentation adapter. Candidate native code is additionally verified by the compiled contract tests. This is a concise terminal host smoke, not a new mouse-drag or visual-look acceptance campaign.

The signed candidate is staged in `build/Rendition.ofx.bundle`; this pass does not overwrite the accepted installed P0 bundle or alter an open Nuke session. Existing 0.32 secondary-page artist acceptance, default promotion, Flame and host Metal remain their separate gates. No presets, recipes or new model research begin here.
