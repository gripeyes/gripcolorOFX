# Rendition versus Pigment: OFX render/image-acquisition audit

Date: 2026-10-05. Scope: source-only comparison of the confirmed Output acquisition failure. No source changes, installation, Nuke launch, runtime reproduction, or cancellation implementation were performed for this audit.

## Conclusion

**Pigment requests Output with the same ImageEffectSuiteV1 call signature as Rendition, and does not implement cancellation-aware Output acquisition.** Its support library converts `kOfxStatFailed` into a null image; Pigment then converts that null into a fatal render status. Therefore its observed successful interactive use does not demonstrate that its acquisition/cancellation policy is correct or that copying it will fix Rendition.

The strongest concrete divergences are:

1. Pigment acquires Output before reading creative parameters. Rendition evaluates its entire timed parameter set, interpretation and core Snapshot before acquiring Output.
2. Pigment disables tiles and host per-frame subdivision; Rendition enables both. Both advertise FullySafe, so Pigment is not necessarily globally serialized.
3. Rendition posts a persistent effect error when this fetch fails; Pigment returns a failed action through the support dispatcher without posting that same persistent acquisition error.

Cancellation remains the leading **unconfirmed hypothesis** for the host's failed fetch. The longer pre-acquisition interval and different host scheduling permissions are plausible contributors; neither proves the cause. There is no demonstrated malformed Output request, but the existing trace is insufficient to rule out a genuine non-aborted Output resource/context failure.

**Recommendation:** do not extract Pigment's existing lifecycle as a proven robust solution, and do not implement the proposed cancellation change on the strength of this comparison alone. First capture abort state and request context at the confirmed failure. If cancellation is confirmed, implement one tested acquisition/outcome policy usable by both adapters, following the official example's distinction between an aborted render and a genuine failure.

## Evidence and reproducibility

Rendition is `/Users/j7s/coding/gripcolorOFX`; Pigment is actually in the adjacent `/Users/j7s/coding/painterly-ofx` checkout, not a subdirectory of Rendition.

| Evidence | Revision / location |
|---|---|
| Rendition HEAD | `0e0830a865b1bd3041a087c4cfab5a768d46f148`, plus pre-existing runtime-contract/trace changes in the working tree |
| Rendition public OpenFX headers | `e40728885390ec16276d11e00025de9b4282060c`; [image-effect contract](../third_party/openfx/ofxImageEffect.h) |
| Pigment HEAD | `885ac9697fa7e855282a38f359fe35cf789f9537` |
| Pigment actual OpenFX dependency | `ab779510b2655b4d11a7e01e5c521f9aa8c88976`; `/Users/j7s/coding/painterly-ofx/build-ofx/_deps/openfx-src` |
| Pigment build integration | [CMakeLists.txt](/Users/j7s/coding/painterly-ofx/CMakeLists.txt:183), ASWF Support library compiled into the plugin |
| Rendition adapter | [plugin.cpp](../src/ofx/plugin.cpp); original C API adapter, not the ASWF C++ Support library |
| Canonical control contract | [RENDITION_CONTROL_SYSTEM_0_32.md](RENDITION_CONTROL_SYSTEM_0_32.md) |
| Earlier diagnosis and fixes | [static audit](OFX_SUITE_FAILURE_STATIC_AUDIT.md), [runtime contract fixes](OFX_RUNTIME_CONTRACT_FIXES.md) |
| Captured failures | `build/ofx-runtime-fix/nuke-diagnostic.log`, `captured-failure.json`, `installation.json` |

Line numbers below refer to these inspected working sources. Pigment references use absolute paths because it is a separate checkout. No assumption is made that its installed binary necessarily matches that source revision.

The existing failure trace reports Output, time `1`, Render action, status `1`, and the Rendition check at `plugin.cpp:179` (actual C call at `:172`). Six records contain three thread hashes. Those hashes establish different executing threads, not whether calls overlapped or whether they were tiles, frames, or replacement renders. The capture lacks abort state and request geometry.

## Exact render paths

Aliases used in tables:

- **R**: [Rendition plugin.cpp](../src/ofx/plugin.cpp).
- **P**: [Pigment.cpp](/Users/j7s/coding/painterly-ofx/src/plugins/Pigment.cpp).
- **S**: [Pigment's actual ASWF ofxsImageEffect.cpp](/Users/j7s/coding/painterly-ofx/build-ofx/_deps/openfx-src/Support/Library/ofxsImageEffect.cpp).

| Stage | Rendition | Pigment |
|---|---|---|
| Render dispatch | `action`, R:710–711 → `render(h,in)` | Support `renderAction`, S:2142–2151 → virtual `PigmentEffect::render(args)` |
| Retrieve instance / arguments | R:605–612: instance pointer, action time, optional MetalEnabled; CPU buffer requirement | S:2144–2148 / 2093–2137: instance pointer, time, window, scale, GPU state/queues, interactive/sequential/draft, field |
| Work before Output | R:613–617: all `values(i,t)`, timed Auto role, `inputInterpretation`, `Snapshot`, window | No creative parameter evaluation yet; P:558 enters render after Support argument parsing |
| Abort before Output | None | None |
| Output acquire | R:618 → `Image` R:170–179 → C call R:172 | P:559 → `Clip::fetchImage(args.time)` S:1168–1178 → C call S:1171 |
| Exact C call | `fx->clipGetImage(clip,t,nullptr,&handle)` | `gEffectSuite->clipGetImage(_clipHandle,t,NULL,&imageHandle)` |
| Output status 1 | R:179 `checkedStatus` throws; no abort check | S:1172–1173 returns null; P:560 still fetches Source; P:561 throws status 1 if either image missing; no abort check |
| Successful Output metadata | R:180–198: data, float, components, bounds, stride, extra clip RoD query | S:779–879: image properties including bounds, pixel RoD, scale, PAR, field, data; returned `Image` owned by `unique_ptr` |
| Source acquire | R:620–624: only if connected; same timed Image helper; absent image represents black-transparent input | P:560: same timed Support fetch; missing Source fatal at P:561 |
| Optional inputs | Inspector Reference R:631–643; Base Matte R:645; same Image helper | Mask P:568–573; PlaneMap P:576–591; same Support helper, connected missing images rejected |
| Parameters / local snapshot | Already built before Output | `parameters(args.time)` P:574; typed local parameters, copied into processing requests |
| Geometry / execution | Window containment R:625–627; scale/PAR R:646–648; local Job R:649–662 | Source/destination bounds + window/scale/PAR P:595–609; branch-specific CPU/Metal requests P:592–716 |
| Cancellation during processing | Worker row boundary R:557; break without exception | ExecutionContext abort callback P:631 and 681; Metal transport P:617; cancellation in Phase4 CPU paths may throw |
| Scheduling / shared resources | R:663–670 host multiThread suite; local snapshot/job; worker exception collected | Phase4 mutex P:610 protects caches/backend processing **after acquisition**; branch-specific CPU/Metal execution |
| Success exit | R:673–680 clear/update persistent message, R:681 OK; local image destructors release | End of P:718; `unique_ptr` destruction releases; Support dispatcher returns normal successful action |
| Exception exit | R:791–800: memory distinct; other exceptions → persistent error + Failed | S:2834–2840 Suite → original status; S:2877–2891 other exception → Failed; owned images unwind |

```text
RENDITION                                  PIGMENT
Render action                              Support Render action
  get instance/time/GPU flag                 parse time/window/scale/field/GPU
  timed parameters + Auto interpretation      retrieve effect instance
  construct Snapshot                       PigmentEffect::render
  read renderWindow                          fetch Output(time, NULL)
  [no abort check]                           [no abort check]
  fetch Output(time, NULL)                    Support status 1 -> null
  status 1 -> traced throw                    fetch Source(time, NULL)
  [no abort check]                           missing Output/Source -> Suite(1)
  validate Output + query clip RoD            validate formats; optional Mask
  fetch Source; Reference/Matte               timed parameters; optional PlaneMap
  build local Job                            build processing requests
  row-wise abort polling                     branch-specific abort callbacks
  release owned images                       release unique_ptr<Image>
  on error: persistent message + Failed      on error: dispatcher status Failed
```

## Eight requested answers

| Question | Answer |
|---|---|
| 1. Exactly the same Output call pattern? | **Yes at the C suite boundary:** cached instance Output clip, action time, null requested region, out image-property handle. The surrounding order and status policy differ. |
| 2. Pigment checks abort before Output? | **No.** Neither P:559 nor S:1168–1178 does. |
| 3. Pigment handles failed Output + abort specially? | **No.** Null is returned by Support, then converted into fatal status by P:561. Dispatcher Suite catch does not test abort. |
| 4. Different time/window/scale/view/plane passed? | Same action-time/null-region API. Window/scale are implicit host context, not arguments to V1 fetch. Pigment parses more context beforehand; descriptor/ROI policies differ. Actual failed request's full context is unknown. Neither fetch uses an explicit view/plane extension. |
| 5. Different handle/property handling? | Pigment wraps successful handles in Support `Image` and caches returned metadata; Rendition validates manually and makes an additional clip RoD query. These differences occur **after** successful Output fetch and cannot directly explain the recorded fetch failure. |
| 6. Helper/RAII Rendition lacks? | ASWF `Clip::fetchImage`, `Image` + `unique_ptr`, and Pigment image-view helpers. These are not a cancellation-safe policy. Rendition already has its own RAII, including constructor-failure release protection. |
| 7. Extra Rendition interactions before Output? | All timed parameter reads, Auto/configuration lookup, source colour metadata/interpretation, core Snapshot setup and validation. Pigment defers creative reads until after Output, Source and Mask. Neither changes presentation properties inside this pre-Output render path. |
| 8. Concrete explanatory divergence? | Early versus delayed Output acquisition and host tiles/frame-subdivision permissions are concrete differences capable of changing cancellation/scheduling exposure. They are **not proof** of the failed request's cause. No different fetch signature or existing Pigment cancellation fix was found. |

## Output request validity and negotiation

`clipGetImage` takes clip, time, optional **canonical** region and an out handle. It does not take renderWindow, renderScale, field, view, plane, components or depth as additional arguments. These come from action context, descriptor/clip negotiation and returned properties. A null requested region is valid.

| Context | Rendition | Pigment | What the failure capture establishes |
|---|---|---|---|
| Output clip handle | Obtained during Create R:484; retained on instance | Constructor caches `fetchClip(Output)` P:152–156 through Support | Subject is Output; handle validity not independently measured |
| Time | Render inArgs time R:607; same `t` at R:172 | Support args.time S:2095; P:559 | `time=1`, timed fetch |
| Requested region | null | null | Known from source/trace expression |
| Render window | Read R:617; checked against fetched bounds R:625 | Read S:2100–2103; processing uses args.renderWindow | Not captured |
| Render scale | Read after images R:647; host has action context independently | Read before fetch S:2097–2098; also cached returned image scale | Not captured; differing read order does not change host's scale |
| Field | Adapter does not parse Render field or returned field | Support parses action and image field; plugin does not branch on field in examined render | Not captured; no proof of differing requested field |
| View / plane | V1 fetch; no explicit view/plane fetch | Same; PlaneMap is a named auxiliary RGBA clip, **not** a multiplane API | Not captured; no explicit plane-selection divergence found |
| Components / depth | Effect/clip support float RGB/RGBA; matte Alpha; validate after successful fetch | Float RGB/RGBA Output/Source; Mask Alpha, PlaneMap RGBA; validate after fetch | No returned properties on failed fetch |
| Bounds / stride / PAR | Manual bounds/stride checks and later PAR read | Support metadata + view construction; mask and PlaneMap checks | Not captured |
| Output connection/state | Created mandatory Output clip; no pre-fetch connection branch | Same | No evidence Output disappeared/disconnected |
| Tiles | Effect R:236 and clips R:257 support tiles | Effect P:765 and clips P:754 do not | Actual window/subdivision not captured |
| Host frame threading | R:241 true | P:765 false | Different permission; no proven overlap in capture |
| Render safety | FullySafe R:240 | FullySafe P:768 | Both permit simultaneous instance renders in general |
| ROI / RoD | Source-derived RoD R:762–770; no explicit custom ROI action, host defaults | Source RoD P:544–547; full source RoD requested for Source/Mask/PlaneMap P:549–555 | Different spatial needs; no captured ROI |
| GPU state | CPU-only; advertises Metal `"false"` R:246; rejects reported MetalEnabled R:610–612 | Metal supported under build flag P:769–770; CPU and GPU paths distinct | Fetch was reached after Rendition GPU check; trace lacks actual property status/value |

The GPU support property uses the specification's string enum; Rendition's `"false"` advertisement is not a boolean-type bug. There is no evidence that the failing CPU fetch was actually a Metal-buffer request. Neither tile support nor FullySafe is intrinsically invalid for Rendition's local pixel operations. Copying Pigment's whole-image scheduling flags would change host execution policy without establishing the cause.

**Validity assessment:** the static call is well formed, uses the action time and an instance-lifetime clip handle, and occurs in Render. Nothing found proves an invalid Output request. Conversely, missing runtime geometry/abort/context means this audit cannot certify that the host had a valid output allocation for the failing invocation.

## OFX contract and cancellation evidence

Primary contract: Rendition's pinned [ofxImageEffect.h](../third_party/openfx/ofxImageEffect.h:1874), `clipGetImage` documentation around 1874–1906 and `abort` around 1945–1957.

- Status 1 is documented as an image absent at time/region, with black-transparent semantics. This is usable for missing **input**. It does not provide an Output buffer into which a plugin can write.
- Each successfully acquired handle must be released before the action returns; handle lifetime is action-scoped.
- `abort(instance)` is explicitly intended to stop work/restart in response to interactive parameter tweaking.
- The official [Basic example at Rendition's pin](https://github.com/AcademySoftwareFoundation/openfx/blob/e40728885390ec16276d11e00025de9b4282060c/Examples/Basic/basic.cpp) catches its no-image exception and returns success if the effect is aborting (around 693–699), otherwise failure; releases follow. The equivalent [example at Pigment's actual pin](/Users/j7s/coding/painterly-ofx/build-ofx/_deps/openfx-src/Examples/Basic/basic.cpp:761) does the same at 761–778.

Thus this is a supported interpretation:

```text
parameter change may abort old render
old render may fail image acquisition
if abort(instance) is true, failed acquisition may be an interrupted render
official example ends that interrupted render without an effect failure
```

This is **not** a guarantee that each drag aborts a render, that each failed Output fetch is cancellation, or that Nuke reported abort in the captured case. The example handles missing-image exceptions in the enclosing render, not an unconditional policy swallowing Output status 1.

Pigment's helper contains the standard absent-image comment, but the plugin makes missing Output/Source fatal without an abort check. Connected unavailable Mask or PlaneMap is also rejected. It therefore is not a reference implementation of all absent-input/cancelled-render semantics. Bad-handle/memory/other suite errors remain distinct in Support; Rendition separately maps memory exceptions but general failures become Failed.

## Ownership, processing cancellation and immutable state

| Concern | Finding |
|---|---|
| Rendition ownership | `Image` R:180–202 releases an acquired handle if property validation throws; destructor R:205–207 releases successful objects. Missing input status 1 nulls the handle and never releases it. |
| Pigment ownership | `unique_ptr<OFX::Image>` owns successfully constructed wrappers; `Image::~Image` S:881–884 releases. Already wrapped images unwind on later failures. |
| Pigment constructor gap | `Clip::fetchImage` S:1178 returns `new Image(imageHandle)` without a raw-handle guard. If ImageBase/Image construction throws while reading properties, Image's destructor is not invoked; ImageBase's destructor S:863–865 does not release. This is a potential construction-failure leak, not the recorded status-1 cause. |
| Rendition polling | R:557 checks abort once per assigned output row; abort breaks processing without a worker exception. There is no acquisition-stage check. After a normal break, render still reaches persistent-message handling. |
| Pigment polling | P:631/681 passes abort into CPU ExecutionContext. Phase4Interactive.cpp:47,64,75 and PigmentPhase4.cpp:91,99,108,139,159,173 throw runtime errors on cancellation; generic Support exception handling returns Failed. No special cancelled-render outcome is implemented there. Metal paths receive some cancellation callbacks but are separate from the confirmed CPU Output fetch. |
| Parameter state | Rendition constructs an action-local Snapshot from timed values before acquisition; workers read that snapshot, not live knobs. Pigment constructs action-local typed parameters from timed reads after acquisition, copied into requests; some backend/quality/execution reads occur later at P:612,629–630. Neither source comparison proves all host reads are an atomic knob snapshot. |
| Mutable instance state | Pigment caches and Metal objects are instance state; Phase4 mutex P:610 protects that branch after images are obtained. It cannot prevent an Output acquisition race. Rendition's worker failure state is synchronized/local to Job; trace context is thread-local. |
| Shared code | No common acquisition helper currently bridges these repositories. Pigment's OfxImageHelpers.cpp:9–34 converts views and validates float storage, not acquisition/cancellation. Phase4 also constructs views directly P:595–609. It is not a universal image-lifecycle wrapper. |

The absence of a visible Pigment error during past use cannot establish absence of failed/aborted actions. Rendition's persistent error reporting can also make an equivalent host failure more conspicuous or longer lived.

## Ranked diagnosis and narrow proof

| Rank | Hypothesis / finding | Source evidence | Minimal evidence to settle it |
|---|---|---|---|
| **High, confirmed manifestation** | Shared Output status 1 is converted to a persistent effect failure | R:172,179 → R:793–796; common to artist and historical effects | Existing trace already establishes the call and status. It does not establish why the host failed. |
| **High, unconfirmed host cause** | Interactive invalidation cancels a render before/during Output acquisition; Rendition lacks cancellation-aware handling | OFX abort contract/example; no acquisition abort checks in either plugin; timed Snapshot precedes R:618 | Failure-path record: abort immediately before acquisition and after status 1, action time/window/scale/interactive state and thread. A true abort result supports cancellation; a false result requires retaining fatal semantics and investigating request context. |
| **Medium, contributing difference** | Rendition's pre-Output evaluation widens the cancellation interval relative to Pigment | R:613–615 versus P:559 / P:574 | Lightweight entry-to-fetch timing paired with abort state; no profiling campaign needed. |
| **Medium, contributing difference** | Tile / host per-frame concurrency changes Output allocation/invalidation timing | R:236,241 versus P:765; three traced threads | Include renderWindow and action correlation in that same trace. Thread hashes alone are insufficient. Do not change scheduling flags speculatively. |
| **Medium, alternative** | Genuine non-aborted Output allocation/context problem | No abort/geometry capture; V1 request and supported format appear valid statically | Failed fetch with abort false plus window/scale/field/GPU/clip identity; host diagnostics if the context remains valid. |
| **Low for this exact failure** | Different returned properties, extra clip RoD, worker math or RAII causes status 1 | All occur after R:172 succeeds | Not candidates for the already captured failed fetch. They may have independent issues but are outside this correction. |

Dragging increases replacement-render pressure and the chance of a render being superseded while doing pre-acquisition work. This explains the **hypothesis**, not a measured host event. Any knob can trigger it because acquisition/error conversion is shared and independent of the changed creative operation.

Recommended next instrumentation is a narrow addition to the existing Output-fetch trace, not a fix: `abort_before_fetch`, `fetch_status`, `abort_after_fetch`, interactive flag, time, renderWindow, renderScale, field, reported GPU state, clip role/handle, thread and action correlation. Optional absent diagnostic properties must not introduce new fatal calls. No such instrumentation was added in this pass.

## Recommended shared boundary, if evidence confirms a lifecycle correction

Share an acquisition/lifecycle **policy**, not Rendition and Pigment processing engines:

1. Action-local RenderContext: instance, time, pixel window, scale, field and negotiated CPU/GPU context.
2. Typed clip role: required Output versus input with explicitly chosen absent-image semantics.
3. Immediate ownership of each successful raw handle, including constructor/property-validation failures.
4. Three distinct outcomes: acquired image; unavailable input; cancelled render. Genuine non-aborted Output failure, malformed properties, bad handles and memory failures remain errors.
5. Explicit cancellation checkpoints and clean action termination, with no persistent processing error for cancellation.
6. Failure-only diagnostic context shared by the C and C++ adapters.

Keep each plugin's snapshot, colour mathematics, spatial ROI policy, scheduling declaration, cache locking and GPU processing outside this boundary. A thin policy layer can wrap the existing C API and ASWF adapter; extracting Pigment's `fetchImage` alone would retain its missing cancellation distinction and constructor-ownership gap. Reconcile/test both pinned dependency versions before adopting a shared implementation.

If the trace confirms abort, follow the official example's cancellation semantics centrally for both plugins, with strict tests for aborted failure, non-aborted failure, successful acquisition followed by cancellation, and resource release. If it does not, diagnose the actual Output context rather than relabelling status 1 as cancellation.

## Stop / verification record

This deliverable is a comparison and ranked diagnosis only. Source, control semantics, appearance, versions, UI, host flags and dependency pins were not changed. No build, installation, Nuke interaction, or broad validation was performed. Cancellation is supported by the OFX example as a handling pattern but remains unproven for the captured Nuke failure. Pigment supplies useful contrasts in ordering and scheduling, not a demonstrated ready-made fix.
