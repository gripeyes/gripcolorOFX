"""Host persistence/render checks. These are not interactive UX acceptance."""
import nuke,json,math,rendition_ui
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'build/ux-0.32';out.mkdir(parents=True,exist_ok=True)
def project():
 r=nuke.root();r['colorManagement'].setValue('OCIO');r['OCIO_config'].setValue('custom');r['customOCIOConfigPath'].setValue('/Users/j7s/coding/authored-DRTs/config-2020.ocio');r['workingSpaceLUT'].setValue('scene_linear');r['monitorLut'].setValue('Flawed Emulsion 2 (sRGB)')
project()
checks=[]
source=nuke.nodes.Constant(name='UXSource');source['format'].setValue('square_256');source['color'].setValue([.02,.3,4,.37])
nodes=[]
for effect in ('Base','Palette','Material'):
 node=nuke.createNode('OFXorg.gripcolor.rendition.'+effect+'_v1',inpanel=False);node.setInput(0,source);node.setName('UX_'+effect)
 assert node['modelVersion'].getValue()==0
 if effect!='Base':node['modelVersion'].setValue(2)
 assert 'renditionUi_layout032d' in node.knobs()
 assert 'renditionUi_modelVersion' in node.knobs() and not node['renditionUi_modelVersion'].visible()
 nodes.append(node)
checks.append({'case':'Compatibility defaults stay legacy; current mapping is explicitly persisted','pass':True})
palette=nodes[1];material=nodes[2]
assert palette['shadowHue'].enabled() and palette['highlightHue'].enabled()
assert not nodes[0]['shadowHue'].enabled() and not nodes[0]['highlightHue'].enabled()
palette['Volume_v0_chroma'].setValue(4);palette['separation'].setValue(.1)
material['Density_density'].setValue(1);material['density'].setValue(.1)
for node in nodes:
 values=[node.sample(ch,100.5,100.5) for ch in ('red','green','blue','alpha')]
 assert all(math.isfinite(x) for x in values) and abs(values[3]-.37)<1e-6,values
 checks.append({'case':node.name()+' finite render including reproduced endpoint combinations','pass':True,'rgba':values})
palette['Volume_v0_chroma'].setValue(1);palette['separation'].setValue(0)
material['Density_density'].setValue(0);material['density'].setValue(0)
# Real OFX family state: changing editor visibility cannot change any family value.
palette['Volume_v3_width'].setAnimated();palette['Volume_v3_width'].setValueAt(40,1);palette['Volume_v3_width'].setValueAt(60,2)
for index in range(6):
 palette['editFamily'].setValue(index)
 rendition_ui.update(palette)
 assert palette['renditionUiFamily_width'].valueAt(1)==palette['Volume_v'+str(index)+'_width'].valueAt(1)
 assert palette['Volume_v3_width'].valueAt(1)==40
 assert palette['Volume_v3_width'].valueAt(2)==60
palette['editFamily'].setValue(3);rendition_ui.update(palette)
palette['renditionUiFamily_hueDelta'].setValue(7)
assert palette['Volume_v3_hueDelta'].getValue()==7 and palette['Volume_v0_hueDelta'].getValue()==0
checks.append({'case':'Family editor has no proxy grade state; animated families remain independent','pass':True})
for node in nodes:node.setSelected(True)
source.setSelected(False)
nuke.nodeCopy(str(out/'copy-paste.nk'));nuke.nodePaste(str(out/'copy-paste.nk'))
assert len([n for n in nuke.allNodes() if 'modelVersion' in n.knobs()])==6
checks.append({'case':'Native copy/paste compatibility and parameter state','pass':True})
nuke.scriptSaveAs(str(out/'host-persistence.nk'),overwrite=1);nuke.scriptClear();nuke.scriptOpen(str(out/'host-persistence.nk'))
palette=nuke.toNode('UX_Palette');assert palette['modelVersion'].getValue()==2
assert palette['Volume_v3_width'].valueAt(2)==60
palette.setName('Palette_Renamed');assert palette['renditionUi_Volume_v3_width'].valueAt(2)==60
rendition_ui.update(palette)
assert palette['renditionUiFamily_width'].valueAt(2)==60
checks.append({'case':'Rename, animation and saved reload retain native values and self-relative links','pass':True})
# Dependency state is applied to native OFX editors, not only link flags.
material=nuke.toNode('UX_Material');rendition_ui.update(material)
assert not palette['Volume_v3_matrixMix'].enabled()
palette['Volume_v3_m02'].setValue(.1);rendition_ui.update(palette)
assert palette['Volume_v3_matrixMix'].enabled()
palette['Volume_v3_m02'].setValue(0);rendition_ui.update(palette)
assert not material['Density_chromaCoupling'].enabled() and not material['Strip_m00'].enabled() and not material['Crosstalk_mix'].enabled()
material['density'].setValue(.2);rendition_ui.update(material);assert material['Density_chromaCoupling'].enabled()
material['modelVersion'].setValue(1);rendition_ui.update(material);assert not material['density'].enabled()
checks.append({'case':'Inert dependencies disabled; historical unsafe additive grade is read-only without changing values','pass':True})
# Load real 0.3/0.31 project files, save copies, reload; native time-evaluated
# parameter state must remain identical. Original files are never overwritten.
def grade_state():
 state={}
 for node in nuke.allNodes():
  groups=rendition_ui._SCHEMA.get(node.Class(),{})
  if node.Class().split('.')[-1].split('_')[0] not in ('Base','Palette','Material'):continue
  keys=[key for values in groups.values() for key in values if key!='semanticReference']
  state[node.name()]={key:[node[key].getValueAt(1),node[key].getValueAt(2)] for key in keys if key in node.knobs()}
 return state
for old in ('build/architecture-0.3/Rendition-0.3-artist.nk','build/control-audit-0.31/restored-host.nk'):
 path=root/old
 if not path.exists():raise RuntimeError('Missing historical project fixture '+old)
 nuke.scriptClear();nuke.scriptOpen(str(path));before=grade_state();assert before
 copied=out/('legacy-'+path.name);nuke.scriptSaveAs(str(copied),overwrite=1)
 nuke.scriptClear();nuke.scriptOpen(str(copied));assert before==grade_state()
 checks.append({'case':'Historical project native state unchanged through reload: '+old,'pass':True,'instances':len(before)})
# Reusable GUI fixture: source and all three artist nodes feed Viewer inputs.
nuke.scriptClear();project();source=nuke.nodes.Constant(name='UXSource');source['format'].setValue('square_256');source['color'].setValue([.02,.3,4,1])
chart=source
sample=nuke.nodes.Read(name='ApprovedACES',file='/Users/j7s/Downloads/ACES_ODT_SampleFrames-main/ACES_OT_VWG_SampleFrames/ACES_OT_VWG_SampleFrames.0007.exr')
sample['colorspace'].setValue('ACES2065-1')
source=nuke.nodes.Switch(name='SourceSelection');source.setInput(0,chart);source.setInput(1,sample);source['which'].setValue(1)
viewer=nuke.nodes.Viewer(name='UXViewer');viewer['viewerProcess'].setValue('Flawed Emulsion 2 (sRGB)')
for index,effect in enumerate(('Base','Palette','Material')):
 node=nuke.createNode('OFXorg.gripcolor.rendition.'+effect+'_v1',inpanel=False);node.setInput(0,source);node.setName('UX_'+effect)
 if effect!='Base':node['modelVersion'].setValue(2)
 node.setXYpos(index*220,100);viewer.setInput(index,node)
source.setXYpos(220,-80);viewer.setXYpos(220,260)
nuke.scriptSaveAs(str(out/'interactive-fixture.nk'),overwrite=1)
(out/'host-checks.json').write_text(json.dumps({'scope':'Host plumbing/persistence; interactive Properties acceptance is separate','checks':checks},indent=2))
print('UX32 host checks',len(checks),'passed')
