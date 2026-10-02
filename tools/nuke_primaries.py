"""Native CPU Primaries smoke test and portable seven-task artist graph."""
import nuke,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'build/primaries'
if not out.exists():out=root/'primaries'
expected=json.loads((out/'expected-nuke.json').read_text());report={'host':nuke.NUKE_VERSION_STRING,'phase':'Artist Primaries v1 CPU','checks':[]}
source=nuke.nodes.Constant();source['format'].setValue('square_256');source['color'].setValue([-.1,.2,4,.3])
node=nuke.createNode('OFXorg.gripcolor.rendition.Primaries_v1',inpanel=False);node.setInput(0,source);node['interpretation'].setValue(1)
def sample():return [node.sample(ch,100.5,100.5,frame=1) for ch in ['red','green','blue','alpha']]
for case in expected:
 for param in case['parameters']:node[param].setValue(case['parameters'][param])
 values=sample();passed=all(abs(a-b)<=2e-6+2e-5*abs(b) for a,b in zip(values,case['expected']))
 report['checks'].append({'task':case['task'],'passed':passed,'values':values});assert passed,(case,values)
 for param in case['parameters']:node[param].setValue(case['defaults'][param])
node['shadowTint'].setAnimated();node['shadowTint'].setValueAt(0,1);node['shadowTint'].setValueAt(.35,2)
path=out/'Primaries-smoke.nk';nuke.scriptSaveAs(str(path),overwrite=1);name=node.name();nuke.scriptClear();nuke.scriptOpen(str(path));node=nuke.toNode(name)
assert abs(node['shadowTint'].valueAt(2)-.35)<1e-6;report['checks'].append({'task':'Animation / model save-reload','passed':True})
writer=nuke.nodes.Write(inputs=[node]);writer['file'].setValue(str(out/'Primaries-native-float.%04d.exr'));writer['file_type'].setValue('exr');writer['datatype'].setValue('32 bit float');nuke.execute(writer,1,2)
report['checks'].append({'task':'Native float CPU render two frames','passed':True})
(out/'nuke-primaries.json').write_text(json.dumps(report,indent=2)+'\n')
nuke.scriptClear()
config=root.parent/'authored-DRTs/config-2020.ocio'
if config.exists():
 nuke.root()['colorManagement'].setValue('OCIO');nuke.root()['OCIO_config'].setValue('custom');nuke.root()['customOCIOConfigPath'].setValue(str(config))
switch=nuke.nodes.Switch();switch.setXYpos(0,0)
for i,num in enumerate([5,7,60]):
 path=root/'build/artist-tests'/f'aces-{num:04d}.exr'
 if not path.exists():path=root/'artist-tests'/f'aces-{num:04d}.exr'
 src=nuke.nodes.Read(file=str(path));src['raw'].setValue(True);src.setXYpos(i*200,-150);switch.setInput(i,src)
recipes=json.loads((out/'primaries.json').read_text())['cases'][:7];target=nuke.nodes.Switch();target.setXYpos(200,600)
for i,case in enumerate(recipes):
 node=nuke.createNode('OFXorg.gripcolor.rendition.Primaries_v1',inpanel=False);node.setInput(0,switch);node['interpretation'].setValue(1);node['label'].setValue(case['task']);node.setXYpos(i*220,350)
 for k,v in case['parameters'].items():node[k].setValue(v)
 target.setInput(i,node)
viewer=nuke.nodes.Viewer(inputs=[target,switch]);viewer.setXYpos(200,750);viewer['viewerProcess'].setValue('Flawed Emulsion 2 (sRGB)')
assert viewer['viewerProcess'].value()=='Flawed Emulsion 2 (sRGB)'
notes=nuke.nodes.StickyNote();notes['label'].setValue('Artist Primaries / Tonal Colour\nSource Switch: 0 faces / 1 red jacket / 2 LEGO. Target Switch: seven labelled tasks.\nViewer A: one Primaries node. B: original. Flawed Emulsion 2 / sRGB.\nRaw Read: explicitly converted Linear Rec.2020 fixtures; no additional input transform.\nAll five artist groups open; scroll directly to the needed tonal controls. Tint alone preserves Y.\nPale-green highlight recipe affects the whole tonal range, not a skin qualifier.\nPrototype: no display white cap, no physical density simulation. Strong narrow zonal gains can reverse tone; widen Range or reduce gain.');notes.setXYpos(-400,300)
nuke.scriptSaveAs(str(out/'Rendition-Primaries-artist.nk'),overwrite=1)
print('RENDITION_PRIMARIES',json.dumps(report))
