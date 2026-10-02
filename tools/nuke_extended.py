import nuke,json,math,os
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'build'/'host';out.mkdir(parents=True,exist_ok=True)
report={'host':nuke.NUKE_VERSION_STRING,'checks':[]}
source=nuke.nodes.Constant();source['format'].setValue('square_256');source['color'].setValue([-.1,.2,4,.3])
def node(name):
    n=nuke.createNode('OFXorg.gripcolor.rendition.'+name+'_v1',inpanel=False);n.setInput(0,source);n['interpretation'].setValue(1);return n
def sample(n):return [n.sample(ch,100.5,100.5,frame=nuke.frame()) for ch in ['red','green','blue','alpha']]
def check(name,condition,details=None):
    print('CHECK',name,condition,details);report['checks'].append({'name':name,'passed':bool(condition),'details':details});assert condition,name
scene=node('Scene');scene['interpretation'].setValue(0);scene['exposure'].setValue(1)
writer=nuke.nodes.Write(inputs=[scene]);writer['file'].setValue(str(out/'must-fail.exr'));writer['file_type'].setValue('exr')
try:nuke.execute(writer,1,1)
except RuntimeError as error:check('Unknown Auto fails rendering','Interpretation Required' in str(error),str(error))
else:check('Unknown Auto fails rendering',False)
scene['interpretation'].setValue(1);scene['alphaMode'].setValue(1);source['color'].setValue([.08,.02,.01,.4]);writer['file'].setValue(str(out/'recovered.exr'));nuke.execute(writer,1,1)
values=sample(scene);check('Premult explicit workflow',all(abs(a-b)<2e-6 for a,b in zip(values,[.16,.04,.02,.4])),values)
source['color'].setValue([.08,-.1,2,0]);check('Zero alpha preserves RGB',all(abs(a-b)<2e-6 for a,b in zip(sample(scene),[.08,-.1,2,0])))
source['color'].setValue([.2,.5,.6,.3])
for name,key,value in [('Volume','v0_hueDelta',10),('Density','density',.6),('Crossover','midHue',10),('Strip','separation',.6)]:
    n=node(name);n[key].setValue(value);
    if name=='Volume':n['v0_width'].setValue(360)
    values=sample(n);check(name+' active CPU / alpha',all(math.isfinite(v) for v in values) and abs(values[3]-.3)<2e-6,values)
inspector=node('Inspector');inspector['mode'].setValue(7);values=sample(inspector);check('Inspector cube slice',abs(values[0]-100.5/256)<1e-5 and abs(values[2]-.5)<1e-5,values)
ref=nuke.nodes.Constant();ref['format'].setValue('square_256');ref['color'].setValue([.1,.2,.3,.8]);inspector.setInput(1,ref);inspector['mode'].setValue(8);values=sample(inspector);check('Inspector Reference difference and source alpha',all(abs(a-b)<2e-6 for a,b in zip(values,[.1,.3,.3,.3])),values)
inspector.setInput(0,None);inspector['mode'].setValue(7);values=sample(inspector);check('Inspector disconnected procedural source',all(math.isfinite(v) for v in values) and values[3]==1,values)
# User-authored OCIO configs are used as host environments only, no transform code copied.
for path,gamut in [('config-2020.ocio',1),('config-acescg-ocio2.4.ocio',2)]:
    config=root.parent/'authored-DRTs'/path
    if not config.exists():report['checks'].append({'name':'Custom OCIO '+path,'passed':None,'details':'config absent'});continue
    nuke.root()['colorManagement'].setValue('OCIO');nuke.root()['OCIO_config'].setValue('custom');nuke.root()['customOCIOConfigPath'].setValue(str(config))
    scene['interpretation'].setValue(gamut);scene['alphaMode'].setValue(0);values=sample(scene)
    check('Custom OCIO '+path,all(abs(a-b)<2e-6 for a,b in zip(values,[.4,1,1.2,.3])),values)
(out/'nuke-extended.json').write_text(json.dumps(report,indent=2)+'\n');print('RENDITION_EXTENDED',json.dumps(report))
