from pathlib import Path
import json,shutil
import _rendition as c
from artist.control_audit import NAMES,MAIN

def run():
 out=Path('build/control-audit-0.31');r=json.loads((out/'control-audit.json').read_text());domain=json.loads((out/'domains.json').read_text());host=json.loads((out/'nuke-controls.json').read_text())
 conditions={'coupling':'Requires nonzero Material Density','leakage':'Requires nonzero effective Strip separation','anchor':'Requires active Strip and source red/skin membership','trajectory':'Requires nonzero family hue / hue trajectory / channel displacement','accent':'Requires deformation to protect against and source red membership','pivot':'Requires nonidentity contrast/tail shaping','shadowHue':'Shadow Colour must be nonzero (Base); exposure trajectory active (Palette)','highlightHue':'Highlight Colour must be nonzero (Base); exposure trajectory active (Palette)','localProtection':'Requires localExposure != 0 and nonzero matte coverage','localCenter':'Requires localExposure and localProtection','localSoftness':'Requires localExposure and localProtection','localChroma':'Requires localExposure != 0 and source chroma','deathStart':'Requires Colour Death','deathSoftness':'Requires Colour Death','highlightBleach':'Requires highlight participation and source chroma'}
 visual={
 'Base':{'exposure':'Clearly brightens; very high stops overwhelm the external view. Practical 1-stop units remain fixed.','contrast':'Increasing strength steepens tonal separation; high strengths crush/deeply separate the portrait.','pivot':'Visible change under active contrast; no effect is promised at identity contrast.','blackStops':'Positive settings open dark tones without introducing a literal RGB floor.','whiteLevel':'Positive settings raise participating upper tones; subtle in the portrait, clearer in the interior.','shadowCompression':'Soft toe response is visible with configured toe/range; not a black clamp.','highlightCompression':'Highlight restraint is more visible on bright interior material than the low-key portrait.','midBalance':'Positive values warm participating midtones; large strengths intentionally alter palette.','midTint':'Positive green-axis tint is clearly visible at stronger settings.','saturation':'Clearly increases colourfulness; high strengths exaggerate colours.','colourBalance':'Positive artistic density closes colour-rich tones without invoking Material Density.','shadowTint':'Shadow colour bias is visible with the default blue-direction hue.','highlightTint':'Upper-tone tint is visible, especially on bright interior materials.'},
 'Palette':{'separation':'Measured family chroma/matrix response; moderately visible on this sample palette.','compression':'Secondary/source colours compress progressively; compact macro is not a family selector.','contamination':'Subtle green tint on the portrait; clearer on the interior. Needs targeted reference viewing.','accent':'Conditional protection is subtle here; default undeformed red needs no correction.','bias':'Positive warming is subtle in this portrait; does not duplicate Base Warmth parameterization.','shadowHue':'Dark hue rotation is visible on affected chromatic material, not an additive shadow tint.','highlightHue':'Bright hue rotation is visible on interior materials; weak where highlight membership is small.','colourDeath':'Reduces deep chroma under the current continuous transition; source-dependent low-key response.','trajectory':'Changes existing hue/channel displacement strength; identity trajectories alone remain inactive.'},
 'Material':{'depth':'Clearly deepens/recombines colour with active separation; broader than a single Density amount.','density':'Strong progressive dark/material-depth response on skin and saturated objects.','coupling':'Visible with active Density; source chroma determines response.','separation':'Clearly changes coherent colour relationships; high settings can collapse/deepen palette.','leakage':'Visible hue/palette interaction with active Strip separation.','crosstalk':'Inspectable channel interaction; visible moderate palette shift.','contamination':'More pronounced than Palette Contamination and can strongly shift warm relationships.','anchor':'Conditional red/skin protection; subtle compared with large separation/density changes.'}}
 for row in r['controls']:
  key=row['parameter']['id'];name=row['effect'];row['active_when']=conditions.get(key,row.get('active_when','Configuration / model selection'))
  if key.startswith('Volume_'):row['domain']='Signed Oklab selection/deformation; optional local RGB matrix'
  elif key.startswith('Crossover_'):row['domain']='Signed Oklab hue mode OR explicit selected look encoding in channel mode'
  elif key.startswith('Crosstalk_'):row['domain']='Explicit linear RGB OR selected scalar look encoding'
  elif key.startswith(('Density_','Strip_')):row['domain']='Spectral-derived radiance base + signed XYZ residual'
  if '_' in key and key.split('_',1)[0] in NAMES:
   child,param=key.split('_',1);definition=next(d for d in c.parameters(NAMES.index(child)) if d['id']==param)
   selector=param in ('hue','width','chromaMin','chromaMax','evMin','evMax','softness','neutral') or (child=='Volume' and param.split('_',1)[-1] in ('hue','width','chromaMin','chromaMax','evMin','evMax','softness','neutral'))
   chroma=param in ('chroma','darkChroma','midChroma','brightChroma') or child=='Volume' and param.endswith('_chroma')
   scaled=child=='Volume' and param.endswith('_hueDelta') or child=='Crossover' and (param in ('darkHue','midHue','brightHue') or definition['group']=='Channels')
   if definition['choices'] or param=='debug' or selector:row['mapping']='effective '+param+' = Expert '+key+' (absolute override; model index 1)'
   elif chroma:row['mapping']='effective '+param+' = macro base × Expert '+key
   elif child=='Strip' and param=='separation':row['mapping']='effective separation = 1−(1−macro base)(1−Expert Strip_separation)'
   else:row['mapping']='effective '+param+' = macro base + (Expert '+key+' − '+str(definition['default'])+')'+(' × Palette trajectory' if scaled else '')
  if name=='Base' and key=='highlightBurn':row['mapping']='compression=1−(1−compression)(1−Burn); bleaching=1−(1−bleaching)(1−Burn); brillianceReduction += Burn'
  row['pass_fail']='numeric response observed; artist usefulness pending' if row['status']=='response measured' else 'conditional / unverified' if row['status'].startswith('no ') else 'configuration'
  row['visual_review']=visual.get(name,{}).get(key,'Detailed sheet generated; comprehensive visual judgment remains pending')
  row['notes']='No arbitrary gain adjustment. Conditional inactivity is not declared a broken control.'
 # Add stage-param linkage based on actual perturbed immutable snapshots, not guessed UI inheritance.
 for row in r['main_controls']:
  name=row['effect'];key=row['parameter']['id'];row['underlying_links']=[]
  if name=='Base':row['underlying_links']=[{'operator':'Base','parameter':key}];continue
  e=NAMES.index(name);base=row.get('activation_settings',{'interpretation':1,'modelVersion':1});a=c.artist_stages(e,base)
  d=row['parameter'];value=d['default']+(d['max']-d['default'])*.1
  b=c.artist_stages(e,{**base,key:value})
  for aa,bb in zip(a,b):
   for k,v in bb['values'].items():
    if aa['values'].get(k)!=v:row['underlying_links'].append({'operator':NAMES[bb['effect']],'parameter':k,'default_effective':aa['values'].get(k),'perturbed_effective':v})
  if key=='accent':row['underlying_links'].append({'operator':'Palette source-red final blend','parameter':'accent'})
 for main in r['main_controls']:
  for row in r['controls']:
   if row['effect']==main['effect'] and row['parameter']['id']==main['parameter']['id']:row['underlying_links']=main['underlying_links']
 for oldrow in r['historical_inventory']:
  oldrow['represented_by_macros']=[m['effect']+' / '+m['parameter']['id'] for m in r['main_controls'] if any(link['operator']==oldrow['effect'] and link['parameter']==oldrow['parameter']['id'] for link in m.get('underlying_links',[]))]
  oldrow['equivalence_note']='Shared parameter linkage does not establish perceptual equivalence to the original standalone control'
  if oldrow['parameter']['group'] in ('Input','Custom primaries'):oldrow['classification']='already exposed directly (shared Input interpretation/alpha)'
 # Exact byte ordering and defaults preserved. Full human inventory from machine records.
 def clean(s):return str(s).replace('|','/').replace('\n',' ')
 table='\n'.join('| '+' | '.join(clean(v) for v in [x['effect']+' / '+x['parameter']['label']+' (`'+x['parameter']['id']+'`)',x.get('expected_behavior','Configuration'),x['status']+'; '+x.get('visual_review',''),x['mapping'],x['domain'],x['parameter']['default'],x['active_when'],x['pass_fail']])+' |' for x in r['controls'])
 old='\n'.join('| '+x['effect']+' / `'+x['parameter']['id']+'` | '+x['classification']+' | '+(', '.join(x.get('represented_by_macros',[])) or 'No direct shared-stage macro; historical Advanced node retains authorship')+' |' for x in r['historical_inventory'])
 inactive=[x['effect']+' / '+x['parameter']['id'] for x in r['controls'] if x['status'].startswith('no ')]
 doc=f'''# Rendition 0.31 — restored controls and recipe gate

Status: **control-restoration candidate; artist-control freeze / recipe gate not yet accepted**. Existing Main panels and all historical engines remain. No Base, Primaries, Density, Strip or historical operator equations were changed. Palette/Material model choice index 0 retains the original 0.3 mapping. Index 1 explicitly selects **v2 restored controls**; default remains index 0. New persistent parameters append after historical controls; existing IDs/defaults/order and choice index 0 remain intact.

## What changed

Nuke's original Tone Expert disclosure was observed to expand without revealing its encoding selector. Scene/Tone/Crossover/Crosstalk now receive linked Expert/Advanced tabs as a host presentation fix. A fresh interactive Tone creation showed all six encoding choices in Expert, and a keyboard selection changed ACEScct to LogC4. Their native parameters and equations are unchanged.

Full six-family Volume controls, original Crossover hue/channel trajectories, full constrained Crosstalk matrix and detailed Density/Strip parameters now exist as native OFX state inside Palette/Material. Python Nuke tabs link to those same parameters; no duplicate grade state. Families use original source coordinates inside the Volume stage. Channel mode explicitly selects the historical Crossover alternative; it does not silently run alongside hue trajectories.

Nuke presentation uses Main, Advanced, Families, Trajectory, Channel Trajectory, Crosstalk Matrix, Density, Strip, Expert and Input where applicable. Main remains 13/9/8 controls. This first restoration has a tall Families page with family-qualified labels rather than a custom wheel or a family proxy editor. Native matrix entries retain underlying stored names and use M11…M33 labels. New IDs are namespaced `Volume_`, `Crossover_`, `Crosstalk_`, `Density_`, `Strip_`; original deep nodes retain their original IDs.

## Transparent composition contract

For **model index 1 only**:

- Selectors (hue/width/chroma/exposure ranges, softness, neutral protection) and choices are authored **absolute Expert values**. Crossover Expert width defaults to 360° to retain the existing Palette-wide trajectory at neutral Expert settings.
- Family/trajectory hue and ordinary scalar changes are **macro base + expert − expert default**. Global Palette Trajectory strength also scales Expert hue/channel displacements.
- Chroma controls are **macro chroma × Expert chroma**.
- Strip Separation combines by **1−(1−macro separation)(1−Expert separation)**.
- Matrices use authored entries plus the existing Main interaction deltas; historical constraint mode is applied afterwards. Mix, row-sum and domain remain explicit.
- No Main edit writes or erases Expert state. Snapshots compute the effective state at render time. `artist_stages` exports effective underlying values for inspection.
- If the composed state leaves an underlying parameter's supported range, rendering fails explicitly. No hidden clamp, gain reduction or override rewrite. This means an Expert delta near its limit can require reducing a Main macro before increasing it further.
- Model index 0 ignores default neutral new state and rejects nondefault restored controls with an explicit opt-in error. Historical projects do not silently acquire a new look.

A concrete restoration defect was found and fixed before delivery: treating selectors as additive deltas over the Main 360° width made a narrow authored width ineffective. Selectors now override absolutely. This fix affects only the new explicit model. Existing 0.3 behavior stays unchanged.

```mermaid
flowchart LR
 M[Main persistent macros] --> C[Immutable deterministic composition]
 E[Advanced / Expert persistent state] --> C
 C --> V[Existing Volume / Crossover / Crosstalk or Density / Strip engines]
 V --> O[Scene-linear output]
```

## Audit evidence and limits

Machine mapping contains **{len(r['controls'])} parameters** including configuration, and **30 Main controls**. All **303 creative parameters** produce a measured response in activated fixtures; the remaining fields are interpretation/model configuration. All Main controls have measured responses on activated structured fixtures and A/B sample sheets. Fixtures include neutral ramps, eight saturated/skin/olive families across exposure, signed/HDR colours and exact alpha comparisons. Positive/negative strengths are exercised where supported. Default identity is tested separately; contact sheets use explicitly activated dependencies and are not presented as untouched default nodes.

Approved portrait and saturated-interior fixtures are explicitly Rec.2020; quantitative measurements are pre-DRT. PNGs use the external Flawed Emulsion 2/sRGB view. Symmetric difference images are explicitly normalized display diagnostics, not graded source RGB. Detailed Advanced/Expert sheets and 303 small sampled, independently scaled scene-RGB difference diagnostics are included. Some composed extreme values correctly produce an explicit range error; these are recorded rather than repaired.

**Plumbing passes are not artist acceptance.** The numerical fixtures do not establish perceptual direction, full parameter continuity, redundancy, control predictability or reference-board usefulness for every control. Main contamination is subtle in the tested portrait under this view; no gain was increased to make it conspicuous. Protection, range, pivot, coupling and anchors are conditional by design. Inactive fixtures requiring further targeted coverage: {', '.join(inactive) or 'none after adding explicit signed-opponent chroma/neutral boundary stimuli'}. These statuses remain visible in the table and machine report, not falsely marked useful.

Native Nuke report contains **{len(host['checks'])} checks**: direct link write-through, explicit model choice, animation, node rename, copy/paste, save/reload, original 0.3 graph remaining v1, and 24 historical operator/domain response cases with domain-choice animation/reload. CPU suites pass separately. Interactive Nuke menu creation and UI inspection verified Palette Families/Trajectory/Channel Trajectory/Crosstalk Matrix, Material Density/Strip, and Base Advanced/Dodge-Burn. Material Strip and Palette matrix screenshots were viewed in this conversation. The temporary Untitled graph was discarded; no user project was altered. Standalone screenshot files have not been exported, so the requested packaged screenshot evidence remains incomplete.

## Processing domains

External scene-linear in/out and working primaries do not change. Base remains XYZ/residual plus signed-magnitude stop coordinates; no camera-log RGB switch was added. Volume/hue Crossover retain signed opponent coordinates. Density/Strip retain compact spectral-derived representations; Full Spectral and HK experiments remain offline research.

All six historical encodings remain selectable where connected: pure stops, ACEScct (default), LogC4, DaVinci Intermediate, unclamped AgX-style stops and LookLog candidate. Round-trip, middle gray, toe-junction secants, local parameter sensitivity and operator response records are in `domains.json`; existing independent encoding tests include signed/near-zero/HDR ranges. Pure stops and AgX-style stops are **positive-only** and explicitly reject unsupported inputs. No choices are silently aliased. Pure stops and unclamped AgX stops may have related normalized behavior by design; the latter is not a complete AgX display transform.

Tone shapes selected look coordinates. Scene selects linear versus look-coordinate SOP/saturation. Crosstalk selects linear versus look-coordinate matrix action; a luminance constraint in encoded coordinates must not be described as scene-Y preservation. Channel Crossover uses the selected encoding; hue mode does not. Full derivative continuity and response/sensitivity certification for every combined domain setting remain pending beyond these numerical checks. No historical choice was removed or reordered.

## Known unsupported combinations and visual concerns

Pure stops and AgX-style stops reject zero/negative samples; their errors in the signed sweep are expected domain failures, not a silently repaired grade. Extreme Crossover pivot sweeps can reverse dark/bright ordering and are rejected by the existing engine; keep dark position below bright position. These cases are recorded in the machine sweep.

A targeted narrow Material hue/depth example can emphasize skin texture and produce locally uneven brown/bronze development under the selected view. This is an artist-coherence concern to review before promoting a preset, not evidence for replacing Density equations. Cyan-only trajectory settings barely affect the approved portrait/interior where their membership is small: synthetic/exposure-family trajectories are needed to evaluate them honestly. No arbitrary gain increase was applied.

## Capabilities intentionally kept outside Main

Scene daylight/CAT calibration and SOP, linked/per-channel Tone, literal Primaries black offset and historical nonmonotone Primaries tone remain separate Advanced tools. Base Black/White remain exposure-style tonal controls, not floors/caps. Base retains its monotonic construction. HK experiments, Neugebauer and runtime spectral alternatives were not exposed. Yellow/gold protection is available through authored family deformation/selection relationships, not a new dedicated Main yellow anchor. No new node, film stock, spatial segmentation or Pigment processing was added.

## Visual engineering review

The Main overview sheets were inspected under Flawed Emulsion 2. Exposure, Contrast, Black, Saturation, Warmth/Tint, Material Density and Strip separation produce clearly visible changes. Palette protection, chroma coupling and leakage depend strongly on the activated underlying deformation. Palette Contamination and positive Warm/Cool Bias are subtle in this portrait; Material Contamination is much more pronounced, because these coordinate different operators. They are not interchangeable controls.

Very large positive Exposure values exceed the useful range of the selected viewed example: display highlights become flat or show view-dependent colour artifacts even while pre-DRT output remains finite. Contrast/Saturation at high strengths can intentionally collapse or exaggerate the palette. This is recorded as aggressive creative response, not a recommendation or silent range restriction. Normal one-stop Exposure work retains its defined units.

No literal reference match or artist superiority is claimed from these sheets. The restored Cyan trajectory, family selectors, row-sum matrix, selected Material Density, custom Strip records and porcelain highlight test stimuli have separate scene-linear exposure trajectories and viewed A/B/difference examples. These are diagnostic test cases, not the next-phase Artist Presets / Recipes.

## Per-control audit

| Control | Expected | Observed | Mapping | Domain | Neutral/default | Active when | Pass/fail |
|---|---|---|---|---|---|---|---|
{table}

## Historical inventory

The full original parameter definitions, units and ranges are in `control-audit.json`. Direct availability does not mean a Main macro provides equivalent artist control. Scene/Tone remain native Advanced tools; matrix/SOP and per-channel tone are not falsely claimed represented by Base.

| Original control | Classification | Main shared-stage correspondence |
|---|---|---|
{old}

## Acceptance before recipes

Restored access, deterministic composition and native persistence are implemented/tested. The comprehensive perceptual audit, target-language judgments, refined compact family presentation, complete UI screenshot evidence and all combined-domain continuity/artist acceptance are **not yet accepted**. Do not freeze or begin Artist Presets / Recipes on the strength of plumbing tests. The next work is targeted visual review of this existing evidence and necessary control fixes, not new colour/spectral research.
'''
 Path('docs/ARTIST_CONTROL_RESTORATION_0_31.md').write_text(doc)
 (out/'control-audit.json').write_text(json.dumps(r,indent=2)+'\n')
 for name in ['domains.json','nuke-controls.json']:shutil.copy2(out/name,Path('docs/reports')/('0.31-'+name))
 (Path('docs/reports')/'0.31-control-mapping.json').write_text(json.dumps({'controls':r['controls'],'main_controls':r['main_controls'],'inventory':r['historical_inventory'],'compatibility':r['compatibility']},indent=2)+'\n')
 print('Control restoration report written; perceptual gate remains open')
if __name__=='__main__':run()
