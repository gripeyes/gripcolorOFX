# Rendition 0.32 Nuke UX correction candidate

2026-10-03. **Acceptance pending. Presets remain stopped.** This is a UI/safety correction, not a new colour or spectral research phase. Base → Palette → Material and every historical effect ID remain.

## Reproduction and corrections

| Reproduced problem | Cause | Correction | Evidence / remaining work |
|---|---|---|---|
| Palette Red chroma 4 + Main Separation 0.1 fails `Invalid parameter: v0_chroma` | Historical additive composition produces 4.1 | New stored composition model index 2 modulates remaining headroom | Old index 1 failure retained in regression; new endpoint renders finite; numeric UI endpoint verified |
| Material legacy node Expert Density 1 + Main Density 0.1 fails; restored index 1 also exceeds amount 1 | Legacy opt-in requirement; additive amount 1.1 in restored model | Inactive legacy Expert editors disabled; bounded current composition | New model renders signed/HDR cases; actual mouse Density reaches 1 with Expert amount 1 |
| Model v1/v2 is a prominent creative choice | Compatibility and creative choices conflated | Hide stored version choices; Input / Compatibility explains legacy state and offers deliberate Enable full controls | Migration click, undo, redo verified interactively |
| Custom Rx/Ry/Gx/Gy/Bx/By/Wx/Wy editable under Auto | Configuration shown without its dependency | Hidden in Nuke unless Custom; native OFX Enabled conditional | Auto and Custom screenshots |
| Pivot, protection, coupling, leakage, anchors and Matrix Mix seem inert | Dependency not communicated | Disable native editors and links until their operation is active; concise hints | Actual panels plus native Enabled checks |
| Families page contains six tall repeated blocks and retained scroll position | Repeated presentation, host global scroll; hiding blocks still leaves gaps | One selected-family Link_Knob editor points directly at selected persistent native parameters | Red/Cyan/Magenta screenshots; independent animation, undo, rename/reload tests |
| Matrix looks like nine unrelated sliders | Default OFX scalar layout | Numeric 3×3 grouping with mode/domain/constraint/mix adjacent | Crosstalk screenshots; active matrix enables Mix |
| Main blank/offscreen after native groups hidden | Group/end-marker layout and initial group ordering | Define stable Artist group first, relabel Main in Nuke; hide native presentation groups | Compact Main screenshots |
| Linked controls look enabled despite disabled alias | Link flags alone do not disable underlying editor | Apply Enabled to native target and link | Screenshot and native state checks |
| Native OFX pages/disclosures do not expose required UI in Nuke 17 | Demonstrated host presentation limitation | Retain native OFX descriptors and narrow Nuke linked-tab fallback | Probe without fallback: pages absent, group children inaccessible; no NDK migration |
| Final fresh Palette Shadow/Highlight Hue Bias incorrectly disabled | A Base-only hue-direction dependency also matched Palette macro IDs | Scope tint-direction enable rule to Base; Palette macros remain directly active | New regression distinguishes Palette macro from Base tint direction; restarted fresh-node screenshot confirms active macros |
| Identity local family matrix has meaningless Mix | Missing dependency | Disable local Matrix Mix until local matrix differs from identity | Headless dependency check plus restarted actual UI: identity Mix disabled, M13 edit enables Mix |

## Panels

- Base: Main; Tonal Colour / Ranges; Dodge-Burn; Advanced; Input / Compatibility.
- Palette: Main; Families (one editor); Trajectory (opponent or channel choice, conditional fields); Crosstalk; Advanced (selectors); Input / Compatibility.
- Material: Main; Density; Strip; Crosstalk; Input / Compatibility. No empty Advanced page.

Main remains 13 / 9 / 8 controls respectively. Historical deep nodes retain their existing presentation and processing. Expert matrix values are actual coefficients in Crosstalk; Strip custom record gain/bias coordinates in the new safety model are explicitly different.

## Safe composition, without image clipping

Only Palette/Material persistent index **2** uses the new composition. For macro state b, neutral Expert e0, Expert value e and allowed engine interval [lo,hi], let d=e−e0 and f=d/(hi−e0) for d≥0, or f=d/(e0−lo) otherwise. Effective value is b+f(hi−b) for f≥0, otherwise b+f(b−lo). Endpoints map exactly to engine endpoints. Neutral Expert preserves the macro; neutral macro preserves scalar Expert values. No other knob is rewritten.

Trajectory strength T uses Tf/[1+(T−1)|f|], with T=0 explicitly zero and neutral T=1 unchanged. Reversed selector endpoints are sorted only in the immutable evaluated stage; stored values and animations remain independent. This creates continuous intervals rather than invalid ranges.

Custom Strip record basis uses gain=2^((diagonal−1)/4); off-diagonal entry=.75×gain×raw/[1+Σ|off-diagonal raw|]. This keeps each row strictly diagonally dominant and the basis invertible throughout its editor range. Labels distinguish gain/bias coordinates from literal Crosstalk coefficients. This is an explicit versioned mapping, not a replacement of historical raw matrix semantics.

Base equations remain unchanged. Its paired range controls have dependency-aware display limits: Toe Start cannot be dragged beyond Shoulder Start; Shadow Range cannot exceed Highlight Range. This changes slider headroom, not the other parameter. Unsupported external/numeric values still fail explicitly. No RGB clipping, repair, DRT, gamut compression or spectral-runtime change is introduced.

## Compatibility architecture

| Stored model | Render behavior | Artist editing |
|---|---|---|
| Base index 0 | Original monotonic Base equations | Normal controls; compatibility metadata hidden |
| Palette/Material index 0 (0.3) | Original macros, exact historical behavior | Main available; deeper controls disabled; explicit migration enables full controls |
| Palette/Material index 1 (0.31) | Original additive restored equations | Grade controls read-only to contain unsafe range composition; Input remains editable; deliberate migration required for safe editing |
| Palette/Material index 2 | New bounded composition; existing child production engines retained | Full editor |

**Recommendation:** after actual UX/artist acceptance, the artist menu factory may explicitly initialize new Palette/Material nodes to index 2. Keep the OFX descriptor default index 0 permanently: historical default-valued parameters can be omitted from saved projects. Never migrate through OnCreate or OnScriptLoad. Migration is undoable and deliberate; it may change an existing Expert grade and must be reviewed. Do not call it an appearance-preserving conversion.

At this candidate stage new nodes still default to legacy macros; no accepted default has been promoted. There is no normal version dropdown. Compatibility status and the explicit migration button are the remaining interim workflow. Consequently the final version-workflow acceptance is **pending**, not claimed passed.

## OFX versus Nuke presentation

Standard OFX implementation uses Page, PageChild, page order, Group/Parent, group ordering, Choice, Enabled, DisplayMin/DisplayMax, Secret, Hint and PushButton, with InstanceChanged updates and parameter edit begin/end for migration. Original scalar parameter IDs/order are retained; new UI-only selector/button IDs are appended. Models remain persisted native parameters.

In Nuke 17.0v1 the native probe showed Page descriptors do not become the required tabs and expandable groups do not reveal children. Marking source parameters Secret also removes linked editors. Therefore Nuke uses Tab_Knob and self-relative Link_Knob references to **real OFX parameters**. STARTLINE layout groups numeric matrices; clearing installed host SLIDER flag on the target removes sliders. No duplicate Double_Knob values or proxy grade synchronization exist. The family selector retargets links only. Cached UI callbacks refresh dependency state after change, frame/showPanel, undo and migration; they never write a grade.

Compatibility and stage-version fields are hidden. Custom coordinates are hidden outside Custom. Native dependency Enabled also supports other hosts; their presentation has not been accepted. Flame and host Metal remain pending.

## Evidence and limits

Four CTest groups pass: independent core, native image contract, operator contract, offline Metal parity. The safety suite checks 160 legal combined configurations per new artist model, every single artist-control endpoint on finite signed/HDR stimuli, the original failing combinations, and neutral Expert behavior. The historical fixture compares RGBA float bits against an independently built pre-0.32 binary for 14 configurations and 68 stimuli. Historical equations pass exactly. This is evidence for the tested configurations, not exhaustive historical image coverage.

The Nuke host report records ten checks: finite renders with unchanged alpha, defaults/version persistence, independent family animation and direct linked edits, copy/paste, rename/save/reload, dependency states, and actual 0.3/0.31 project native-state preservation. Quantitative checks are scene-linear. The approved photographic Read is tagged ACES2065-1 and Nuke translates it into the project `scene_linear` role (Linear Rec.2020). Viewer examples use Flawed Emulsion 2.

Interactive evidence includes normal menu creation; compact Main/secondary pages; family Red/Cyan/Magenta editing and undo; matrix edits and Mix activation; custom interpretation visibility; migration undo/redo; actual sample Viewer rendering; numeric maximum endpoint grading. Actual mouse Material Density and Chroma Coupling reached 1 in the final safety mapping. All nine Palette Main sliders were also dragged to endpoints in the final restarted panel, including Separation 1 with Red chroma 4. This final fresh-node sweep was unconnected; it proves slider interaction, not Viewer rendering for that sweep. Earlier legacy Material dragging also reproduced its opt-in failure.

**Unresolved acceptance:** mouse automation intermittently returns `noWindowsAvailable` or `AXError.notImplemented`, including normal Nuke interaction. A native Grade drag succeeded between failures. This is an automation obstacle, not proof of a Rendition defect. Comprehensive final slider dragging, animation/undo under continuous dragging and every panel interaction are not accepted. New-model artist predictability also remains open. Passing tests and screenshots do not close these gates.

No presets, recipes or look-acceptance work resumes. No model default promotion. No claim of complete professional interaction readiness.

## Sources consulted before implementation

- [Foundry Nuke developer overview](https://www.foundry.com/products/nuke/developers)
- [Foundry 13.2 NDK introduction, including OFX distinction](https://learn.foundry.com/nuke/developers/13.2/ndkdevguide/intro/intro.html)
- [Foundry 13.2 knob flags](https://learn.foundry.com/nuke/developers/13.2/ndkdevguide/knobs-and-handles/knobflags.html)
- [Nuke 17 NDK guide](https://learn.foundry.com/nuke/developers/17.0/ndkdevguide/)
- [Nuke 17 knobChanged interaction guidance](https://learn.foundry.com/nuke/developers/17.0/ndkdevguide/knobs-and-handles/knobchanged.html)
- [OpenFX Effect Parameters specification](https://openfx.readthedocs.io/en/main/Reference/ofxParameter.html)

NDK material is interaction reference only. The plugin remains OFX. The attached WritingOFXNodesForNuke guide is host-validation reference and does not override Rendition mathematics or architecture.
