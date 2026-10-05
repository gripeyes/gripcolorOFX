"""One Nuke host smoke test; no image/look evaluation or UI redesign.
OFX_PLUGIN_PATH=build Nuke17.0 -ti tools/nuke_architecture033.py
"""
import json,math,os,subprocess,sys
from pathlib import Path
import nuke
ROOT=Path(__file__).resolve().parents[1]
# Exercise the candidate adapter even when a previous installation ran at startup.
old=sys.modules.get('rendition_ui')
if old is not None:
    for remove,name in (('removeOnCreate','created'),('removeOnScriptLoad','refresh'),('removeKnobChanged','changed'),('removeUpdateUI','idle_update')):
        getattr(nuke,remove)(getattr(old,name))
for module in ('rendition_ui','rendition_presentation'):sys.modules.pop(module,None)
sys.path.insert(0,str(ROOT/'integrations/nuke'))
import rendition_ui as ui
nuke.pluginAddPath(str(ROOT/'build'))
out=ROOT/'build/architecture-0.33';out.mkdir(parents=True,exist_ok=True)
source=nuke.nodes.Constant(name='ArchitectureSource');source['format'].setValue('square_256');source['color'].setValue([.02,.3,4,.37])
nodes=[];checks=[]
for name in ('Base','Palette','Material'):
    node=nuke.createNode('OFXorg.gripcolor.rendition.'+name+'_v1',inpanel=False)
    node.setName('Architecture'+name);node.setInput(0,source)
    assert node['modelVersion'].getValue()==0
    node['interpretation'].setValue(1)
    if name!='Base':node['modelVersion'].setValue(2)
    ui.refresh(node)
    assert 'renditionUi_layout032d' in node.knobs()
    assert not node['renditionUi_modelVersion'].visible()
    nodes.append(node)
palette=nodes[1];material=nodes[2]
palette['separation'].setValue(.3);material['density'].setValue(.2)
# A dependency refresh may change editor flags, never real parameter values.
for node in nodes:
    e=ui.policy.SCHEMA['effects'][node.Class()]
    before={c['id']:node[c['id']].getValue() for c in e['controls'] if 'default' in c}
    ui.update(node)
    assert before=={key:node[key].getValue() for key in before}
    rgba=[node.sample(ch,100.5,100.5) for ch in ('red','green','blue','alpha')]
    assert all(math.isfinite(x) for x in rgba) and abs(rgba[3]-.37)<1e-6
checks.append('Three current artist nodes render; refresh does not write grading values')
palette['Volume_v3_width'].setAnimated();palette['Volume_v3_width'].setValueAt(40,1);palette['Volume_v3_width'].setValueAt(60,2)
for family in range(6):
    palette['editFamily'].setValue(family);ui.update(palette)
    assert palette['renditionUiFamily_width'].valueAt(2)==palette['Volume_v'+str(family)+'_width'].valueAt(2)
palette['editFamily'].setValue(3);ui.update(palette);palette['renditionUiFamily_hueDelta'].setValue(7)
assert palette['Volume_v3_hueDelta'].getValue()==7 and palette['Volume_v0_hueDelta'].getValue()==0
assert not palette['rx'].enabled()
palette['interpretation'].setValue(4);ui.update(palette);assert palette['rx'].enabled()
palette['interpretation'].setValue(1)
for node in (palette,material):
    node['Crosstalk_m02'].setValue(.1);ui.update(node)
    assert node['Crosstalk_mix'].enabled()
    assert node['renditionUi_Crosstalk_m02'].getValue()==.1
checks.append('Direct selected-family links, animation, custom-input dependencies and shared matrix editor')
for node in nuke.allNodes():node.setSelected(node in nodes)
nuke.nodeCopy(str(out/'architecture-copy.nk'));nuke.nodePaste(str(out/'architecture-copy.nk'))
assert len([n for n in nuke.allNodes() if n.Class().startswith('OFXorg.gripcolor.rendition.')])==6
nuke.scriptSaveAs(str(out/'architecture-smoke.nk'),overwrite=1);nuke.scriptClear();nuke.scriptOpen(str(out/'architecture-smoke.nk'))
palette=nuke.toNode('ArchitecturePalette');palette.setName('RenamedPalette');ui.refresh(palette)
assert palette['modelVersion'].getValue()==2 and palette['Volume_v3_width'].valueAt(1)==40 and palette['Volume_v3_width'].valueAt(2)==60
assert palette['renditionUiFamily_width'].valueAt(2)==60 and palette['Volume_v3_hueDelta'].getValue()==7
checks.append('Copy/paste, rename, independent family keys and model generations survive save/reload')
try:
    loaded=[line for line in subprocess.check_output(['/usr/sbin/lsof','-p',str(os.getpid())],text=True).splitlines() if 'Rendition.ofx' in line]
except Exception as error:loaded=[str(error)]
report={'nuke':nuke.NUKE_VERSION_STRING,'adapter':ui.__file__,'loaded_bundle':loaded,'checks':checks,'passed':True,'scope':'Terminal host smoke; no new mouse-drag or look-acceptance campaign'}
(out/'nuke-smoke.json').write_text(json.dumps(report,indent=2)+'\n')
print('RENDITION_033_SMOKE_PASS '+json.dumps(report))
