"""Run with Nuke -t to create an editable artist graph from local fixtures."""
import json
from pathlib import Path
import nuke
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/artist-tests'
if not OUT.exists():OUT=ROOT/'artist-tests'
spec=json.loads((ROOT/'artist/targets.json').read_text())
r=nuke.root();r['colorManagement'].setValue('OCIO');r['OCIO_config'].setValue('custom');r['customOCIOConfigPath'].setValue(spec['ocio_config'])
print('ROOT_COLOR_KNOBS',{k:v.value() for k,v in r.knobs().items() if 'color' in k.lower() or 'ocio' in k.lower() or 'working' in k.lower()})
def read(filename,x,y):
    node=nuke.nodes.Read(file=str(OUT/filename));node['colorspace'].setValue('Linear Rec.2020');node.setXYpos(x,y);return node
def effect(name,source,params,x,y,label):
    node=nuke.createNode('OFXorg.gripcolor.rendition.'+name+'_v1',inpanel=False);node.setInput(0,source);node['interpretation'].setValue(1)
    for key,val in params.items():node[key].setValue(val)
    node['label'].setValue(label);node.setXYpos(x,y);return node
sources=[read(name+'.exr',i*160,0) for i,name in enumerate(['structured','synthetic_cg','aces-0004','aces-0005','aces-0007','aces-0014','aces-0023','aces-0060'])]
switch=nuke.nodes.Switch(inputs=sources);switch['which'].setValue(3);switch.setXYpos(400,180);switch['label'].setValue('Choose source 0–7; all explicitly Rec.2020')
outputs=[]
for i,t in enumerate(spec['targets']):
    node=switch
    for j,stage in enumerate(t['recipe']):node=effect(stage['effect'],node,stage['parameters'],i*220,350+j*120,t['id'])
    outputs.append(node)
select=nuke.nodes.Switch(inputs=outputs);select.setXYpos(550,750);select['label'].setValue('Choose artist target 0–5; editable upstream')
viewer=nuke.nodes.Viewer(inputs=[select,switch]);viewer['viewerProcess'].setValue(spec['view']+' ('+spec['display']+')');viewer.setXYpos(550,950)
# Eight identity prototypes with explicit interpretation, compact native controls.
for i,name in enumerate(['Scene','Tone','Volume','Density','Crossover','Crosstalk','Strip','Inspector']):effect(name,switch,{},i*180,1150,'Default identity / '+name)
# Frozen diagnostic renders are optional comparison inputs, not hidden processing.
for i,filename in enumerate(['density-simple-structured-baseline.exr','strip-curves-structured-baseline.exr','volume-curves-structured-baseline.exr','crossover-smooth-structured-baseline.exr']):
    if (OUT/filename).exists():read(filename,1500,i*140)
notes=nuke.nodes.StickyNote();notes['label'].setValue('Rendition artist evaluation\nSource Switch: 0 structured, 1 CG, 2 neon, 3 faces, 4 red jacket, 5 candles, 6 pumpkin, 7 LEGO.\nTarget Switch: 0 dark collapse, 1 skin, 2 palette, 3 red accent, 4 contamination, 5 colour death.\nViewer input 0 candidate / 1 original. Flawed Emulsion 2 (sRGB).\nAll RGB explicitly Linear Rec.2020; alpha unchanged. Density/Strip research.\nDefaults below; reconstruction and baseline viewers at right. Record time and feedback; no automated artist approval.');notes.setXYpos(-400,100)
for i,case in enumerate(json.loads((OUT/'reference-reconstruction.json').read_text())['cases']):
    src=read('aces-%04d.exr'%case['source_frame'],1900+i*230,700);ref=read('aces-%04d.exr'%case['reference_frame'],1900+i*230,1100)
    node=src
    for j,stage in enumerate(case['recipe']):node=effect(stage['effect'],node,stage['parameters'],1900+i*230,820+j*110,case['id'])
    v=nuke.nodes.Viewer(inputs=[node,ref,src]);v['viewerProcess'].setValue(spec['view']+' ('+spec['display']+')');v.setXYpos(1900+i*230,1300)
for i,stem in enumerate(['density-simple','strip-curves','volume-curves','crossover-smooth']):
    a=read(stem+'-structured-baseline.exr',1500+i*180,1600);b=read(stem+'-structured-candidate.exr',1500+i*180,1740)
    v=nuke.nodes.Viewer(inputs=[b,a,sources[0]]);v['viewerProcess'].setValue(spec['view']+' ('+spec['display']+')');v.setXYpos(1500+i*180,1900);v['label'].setValue('Candidate / fitted baseline / source; '+stem)
report={'host':nuke.NUKE_VERSION_STRING,'view_requested':spec['view'],'view_actual':viewer['viewerProcess'].value(),'view_choices':viewer['viewerProcess'].values(),'working_space':r['workingSpaceLUT'].value() if 'workingSpaceLUT' in r.knobs() else None,'checks':[]}
assert report['view_actual']==spec['view']+' ('+spec['display']+')',report
expected=json.loads((OUT/'expected-nuke-samples.json').read_text())
for source in sources:
    values=[source.sample(ch,100.5,100.5) for ch in ['red','green','blue','alpha']]
    reference=expected[Path(source['file'].value()).stem]
    assert all(abs(a-b)<=2e-6+2e-5*abs(b) for a,b in zip(values,reference)),(values,reference)
    report['checks'].append({'explicit_rec2020_read_verified':True,'source':source['file'].value(),'sample':values})
for node in outputs:
    vals=[node.sample(ch,100.5,100.5) for ch in ['red','green','blue','alpha']]
    assert all(__import__('math').isfinite(x) for x in vals)
    reference=expected[node['label'].value()]
    assert all(abs(a-b)<=2e-6+2e-5*abs(b) for a,b in zip(vals,reference)),(vals,reference)
    report['checks'].append({'target':node['label'].value(),'finite':True,'sample':vals})
saved_nodes=[(node.name(),[node.sample(ch,100.5,100.5) for ch in ['red','green','blue','alpha']]) for node in sources+outputs]
nuke.scriptSaveAs(str(OUT/'Rendition-artist-bench.nk'),overwrite=1)
nuke.scriptClear();nuke.scriptOpen(str(OUT/'Rendition-artist-bench.nk'))
for name,reference in saved_nodes:
    node=nuke.toNode(name);values=[node.sample(ch,100.5,100.5) for ch in ['red','green','blue','alpha']]
    assert all(abs(a-b)<=2e-6+2e-5*abs(b) for a,b in zip(values,reference)),(name,values,reference)
report['save_reload_samples_verified']=True
(OUT/'nuke-artist-bench.json').write_text(json.dumps(report,indent=2)+'\n')
print('ARTIST_BENCH_SAVED',OUT/'Rendition-artist-bench.nk')
