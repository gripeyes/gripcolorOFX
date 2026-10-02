"""Targeted licensed Nuke smoke test for appended 0.2 CPU Inspector modes."""
import nuke,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'build/host';out.mkdir(parents=True,exist_ok=True)
report={'host':nuke.NUKE_VERSION_STRING,'phase':'0.2 Inspector CPU geometry','checks':[]}
source=nuke.nodes.Constant();source['format'].setValue('square_256');source['color'].setValue([.2,.03,.02,.3])
inspector=nuke.createNode('OFXorg.gripcolor.rendition.Inspector_v1',inpanel=False)
inspector.setInput(0,source);inspector['interpretation'].setValue(1);inspector['probeHueShift'].setValue(0);inspector['probeChroma'].setValue(1)
for mode,expected in [(11,.5),(12,0),(13,.5),(14,.5),(15,0)]:
    inspector['mode'].setValue(mode)
    values=[inspector.sample(ch,100.5,100.5,frame=nuke.frame()) for ch in ['red','green','blue','alpha']]
    passed=all(math.isfinite(v) for v in values) and all(abs(v-expected)<2e-6 for v in values[:3]) and abs(values[3]-.3)<2e-6
    report['checks'].append({'mode':mode,'passed':passed,'values':values});assert passed,(mode,values)
inspector['probeHueShift'].setValue(30);inspector['probeChroma'].setValue(.7);inspector['mode'].setValue(12)
# Active signed/HDR and animated probe checks through Nuke's CPU image adapter.
inspector['probeHueShift'].setAnimated();inspector['probeHueShift'].setValueAt(30,1);inspector['probeHueShift'].setValueAt(80,2)
for color in [[.2,.03,.02,.3],[-.1,.2,4,.7],[0,0,0,0]]:
    source['color'].setValue(color)
    for mode in range(11,16):
        inspector['mode'].setValue(mode)
        values=[inspector.sample(ch,100.5,100.5,frame=2) for ch in ['red','green','blue','alpha']]
        passed=all(math.isfinite(v) for v in values) and abs(values[3]-color[3])<2e-6
        report['checks'].append({'active_mode':mode,'source':color,'frame':2,'passed':passed,'values':values});assert passed,(mode,values)
source['color'].setValue([.2,.03,.02,.3]);inspector['mode'].setValue(12)
writer=nuke.nodes.Write(inputs=[inspector]);writer['file'].setValue(str(out/'inspector-geometry.exr'));writer['file_type'].setValue('exr');writer['datatype'].setValue('32 bit float');nuke.execute(writer,1,1)
path=out/'inspector-geometry.nk';nuke.scriptSaveAs(str(path),overwrite=1)
name=inspector.name();nuke.scriptClear();nuke.scriptOpen(str(path));loaded=nuke.toNode(name)
passed=loaded['mode'].getValue()==12 and abs(loaded['probeHueShift'].valueAt(2)-80)<1e-6
report['checks'].append({'name':'native float render and animated probe reload','passed':passed});assert passed
# Retest the previously license-blocked scene_linear bridge with the user's config.
config=root.parent/'authored-DRTs/config-2020.ocio'
if config.exists():
    nuke.root()['colorManagement'].setValue('OCIO');nuke.root()['OCIO_config'].setValue('custom');nuke.root()['customOCIOConfigPath'].setValue(str(config))
    scene=nuke.createNode('OFXorg.gripcolor.rendition.Scene_v1',inpanel=False);scene.setInput(0,loaded.input(0));scene['interpretation'].setValue(0);scene['exposure'].setValue(1)
    values=[scene.sample(ch,100.5,100.5,frame=1) for ch in ['red','green','blue','alpha']]
    passed=scene['hostSceneLinear'].getValue()==2 and all(abs(a-b)<2e-6 for a,b in zip(values,[.4,.06,.04,.3]))
    report['checks'].append({'name':'Auto uses user scene_linear Rec.2020 role','passed':passed,'values':values});assert passed

(out/'nuke-inspector-geometry.json').write_text(json.dumps(report,indent=2)+'\n')
print('RENDITION_GEOMETRY',json.dumps(report))
