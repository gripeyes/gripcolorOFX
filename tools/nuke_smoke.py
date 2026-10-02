"""Run in licensed Nuke: OFX_PLUGIN_PATH=build Nuke17.0 -t tools/nuke_smoke.py."""
import nuke, json, os, math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'build'/'host';out.mkdir(parents=True,exist_ok=True)
nuke.root()['colorManagement'].setValue('Nuke')
source=nuke.nodes.Constant();source['format'].setValue('square_256')
source['color'].setValue([-.1,.2,4,.3])
report={'host':nuke.NUKE_VERSION_STRING,'platform':'macOS arm64','checks':[],'pending':['GUI interaction','extended OCIO checks recorded separately','Flame']}
def sample(node):return [node.sample(ch,100,100,frame=nuke.frame()) for ch in ['red','green','blue','alpha']]
def record(name,expected,actual,tol=5e-5):
    ok=all(abs(a-b)<=tol+tol*abs(b) for a,b in zip(actual,expected));report['checks'].append({'name':name,'passed':ok,'expected':expected,'actual':actual});print('CHECK',name,expected,actual);assert ok,name
names=['Scene','Tone','Volume','Density','Crossover','Crosstalk','Strip','Inspector'];nodes={}
for name in names:
    node=nuke.createNode('OFXorg.gripcolor.rendition.'+name+'_v1',inpanel=False);node.setInput(0,source);node['interpretation'].setValue(1);nodes[name]=node
    record(name+' default float identity',[-.1,.2,4,.3],sample(node))
scene=nodes['Scene'];scene['exposure'].setValue(1);record('Scene exposure',[-.2,.4,8,.3],sample(scene))
scene['exposure'].setAnimated();scene['exposure'].setValueAt(0,1);scene['exposure'].setValueAt(2,3)
for f,scale in [(1,1),(2,2),(3,4)]:nuke.frame(f);scale=2**scene['exposure'].valueAt(f);record('Scene animation frame '+str(f),[-.1*scale,.2*scale,4*scale,.3],sample(scene))
scene['exposure'].clearAnimated();scene['exposure'].setValue(0)
tone=nodes['Tone'];tone['contrast'].setValue(1.2);assert all(math.isfinite(v) for v in sample(tone));report['checks'].append({'name':'Tone signed/HDR finite','passed':True})
ct=nodes['Crosstalk'];ct['rg'].setValue(.25);record('Crosstalk matrix',[-.025,.2,4,.3],sample(ct))
source['color'].setValue([.18,.18,.18,.3]);record('Crosstalk neutral magnitude',[.18,.18,.18,.3],sample(ct))
# Round-trip project serialization including explicit model/domain choices.
scene['exposure'].setValue(1.5);tone['lookDomain'].setValue(3);tone_name=tone.name();graph=out/'smoke.nk';nuke.scriptSave(str(graph));expected=sample(scene);scene_name=scene.name();nuke.scriptClear();nuke.scriptOpen(str(graph));record('Project reload preserves scene math',expected,sample(nuke.toNode(scene_name)))
assert nuke.toNode(tone_name)['lookDomain'].value()=='DaVinci Intermediate scalar encoding'
report['checks'].append({'name':'Project reload preserves look domain','passed':True})
# Render 3 frames to float EXR, not only point sampling.
writer=nuke.nodes.Write(inputs=[nuke.toNode(scene_name)]);writer['file'].setValue(str(out/'smoke.%04d.exr'));writer['file_type'].setValue('exr');writer['datatype'].setValue('32 bit float');nuke.execute(writer,1,3)
report['checks'].append({'name':'Multiframe CPU render to float EXR','passed':True})
(out/'nuke-smoke.json').write_text(json.dumps(report,indent=2)+'\n')
print('RENDITION_SMOKE',json.dumps(report))
