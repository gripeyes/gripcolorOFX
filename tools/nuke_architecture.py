"""0.3 native CPU and saved-model compatibility, plus editable artist graph."""
import nuke,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'build/architecture-0.3'
if not out.exists():out=root/'architecture-0.3'
out.mkdir(parents=True,exist_ok=True)
report={'host':nuke.NUKE_VERSION_STRING,'checks':[],'third_party':[]}
source=nuke.nodes.Constant();source['format'].setValue('square_256');source['color'].setValue([-.1,.2,4,.3])
expected=json.loads((out/'native-expected.json').read_text())
for case in expected:
 node=nuke.createNode('OFXorg.gripcolor.rendition.'+case['effect']+'_v1',inpanel=False);node.setInput(0,source);node['interpretation'].setValue(1)
 for key,value in case['parameters'].items():node[key].setValue(value)
 values=[node.sample(ch,100.5,100.5,frame=1) for ch in ['red','green','blue','alpha']]
 assert all(abs(a-b)<2e-6+2e-5*abs(b) for a,b in zip(values,case['expected'])),(case,values)
 report['checks'].append({'effect':case['effect'],'parameters':case['parameters'],'passed':True,'values':values})
base=nuke.createNode('OFXorg.gripcolor.rendition.Base_v1',inpanel=False);base.setInput(0,source);base['interpretation'].setValue(1);base['localExposure'].setValue(1)
matte=nuke.nodes.Constant();matte['format'].setValue('square_256');matte['color'].setValue([0,0,0,.5]);base.setInput(1,matte)
values=[base.sample(ch,100.5,100.5,frame=1) for ch in ['red','green','blue','alpha']]
assert all(abs(a-b*2**.5)<2e-5 for a,b in zip(values[:3],[-.1,.2,4])),values
report['checks'].append({'case':'Matte alpha .5 -> half-stop exposure','passed':True,'values':values})
# Nuke links share the native animated parameter and survive node renaming.
assert 'renditionUi_shadowHue' in base.knobs()
base['renditionUi_shadowHue'].setValue(35);assert base['shadowHue'].value()==35
base.setName('Base_Renamed');base['renditionUi_shadowHue'].setValue(60);assert base['shadowHue'].value()==60
base['renditionUi_shadowHue'].setValue(240)
base['exposure'].setAnimated();base['exposure'].setValueAt(0,1);base['exposure'].setValueAt(1,2)
path=out/'architecture-smoke.nk';nuke.scriptSaveAs(str(path),overwrite=1);name=base.name();nuke.scriptClear();nuke.scriptOpen(str(path));base=nuke.toNode(name)
assert base['exposure'].valueAt(2)==1 and base['modelVersion'].getValue()==0
for node in nuke.allNodes():
 if node.Class().startswith('OFXorg.gripcolor.rendition.'):
  assert node['modelVersion'].getValue()==0
base['renditionUi_shadowHue'].setValue(75);assert base['shadowHue'].value()==75
base['renditionUi_shadowHue'].setValue(240)
report['checks'].append({'case':'Nuke Advanced links: write-through, rename and reload','passed':True})
report['checks'].append({'case':'Original + new nodes, model choices and animation reload','passed':True})
writer=nuke.nodes.Write(inputs=[base]);writer['file'].setValue(str(out/'architecture-float.%04d.exr'));writer['file_type'].setValue('exr');writer['datatype'].setValue('32 bit float');nuke.execute(writer,1,2)
report['checks'].append({'case':'CPU matte two-frame float render','passed':True})
(out/'nuke-architecture.json').write_text(json.dumps(report,indent=2)+'\n')
nuke.scriptClear();config=root.parent/'authored-DRTs/config-2020.ocio'
if config.exists():
 nuke.root()['colorManagement'].setValue('OCIO');nuke.root()['OCIO_config'].setValue('custom');nuke.root()['customOCIOConfigPath'].setValue(str(config))
src=nuke.nodes.Switch();src.setXYpos(0,0)
sample_root=Path('/Users/j7s/Downloads/ACES_ODT_SampleFrames-main/ACES_OT_VWG_SampleFrames')
for i,num in enumerate([5,7,60,4,14,23]):
 original=sample_root/f'ACES_OT_VWG_SampleFrames.{num:04d}.exr'
 fallback=root/'build/artist-tests'/f'aces-{num:04d}.exr'
 if not fallback.exists():fallback=root/'artist-tests'/f'aces-{num:04d}.exr'
 read=nuke.nodes.Read(file=str(original if original.exists() else fallback));read['raw'].setValue(False)
 read['colorspace'].setValue('ACES2065-1' if original.exists() else 'Linear Rec.2020');read.setXYpos(i*180,-200);src.setInput(i,read)
last=src
for i,e in enumerate(['Base','Palette','Material']):
 node=nuke.createNode('OFXorg.gripcolor.rendition.'+e+'_v1',inpanel=False);node.setInput(0,last);node['interpretation'].setValue(0);node.setXYpos(0,150+i*150);last=node
viewer=nuke.nodes.Viewer(inputs=[last,src]);viewer['viewerProcess'].setValue('Flawed Emulsion 2 (sRGB)');viewer.setXYpos(0,650)
notes=nuke.nodes.StickyNote();notes['label'].setValue('Rendition 0.3 / Base -> Palette -> Material\nTagged AP0 originals or Rec.2020 fixtures. Raw OFF; Nuke translates to scene_linear. Flawed Emulsion 2 / sRGB is external.\nBase Matte input: alpha coverage; Dodge/Burn +1 is x2 at full coverage.\nAdvanced retains Scene/Tone/Volume/Density/Crossover/Crosstalk/Strip/Primaries.\nMaterial depth remains a research candidate; compare simple baselines.\nOptional Pigment and optical SpektraFilm follow; full print rendering needs its appropriate display path.');notes.setXYpos(350,150)
nuke.scriptSaveAs(str(out/'Rendition-0.3-artist.nk'),overwrite=1)
# Verify host-managed AP0 -> scene_linear plus Auto and saved Read tags.
first=nuke.toNode('Read1');reference=json.loads((out/'read-reference.json').read_text())
if isinstance(reference,dict):reference=reference['ap0_original' if Path(first['file'].value()).parent==sample_root else 'rec2020_fixture']
value=[first.sample(ch,100.5,100.5,frame=1) for ch in ['red','green','blue']]
assert all(abs(a-b)<2e-6+2e-5*abs(b) for a,b in zip(value,reference)),(value,reference)
report['checks'].append({'case':'Explicitly tagged Read, Raw disabled, Nuke OCIO to scene_linear Rec.2020','passed':True,'values':value})
report['checks'].append({'case':'Artist Base Auto scene_linear, source sample identity','passed':True})
value=[last.sample(ch,100.5,100.5,frame=1) for ch in ['red','green','blue']]
assert all(abs(a-b)<2e-6+2e-5*abs(b) for a,b in zip(value,reference)),(value,reference)
(out/'nuke-architecture.json').write_text(json.dumps(report,indent=2)+'\n')
print('RENDITION_03',json.dumps(report))
