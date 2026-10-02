"""Create portable float EXR Flame/Nuke Gate C fixtures and explicit expected CPU outputs."""
import json
from pathlib import Path
import nuke
root=Path(__file__).resolve().parents[1];out=root/'build'/'fixtures';out.mkdir(parents=True,exist_ok=True)
nuke.addFormat('512 256 1 RenditionFixture')
source=nuke.nodes.Constant();source['format'].setValue('RenditionFixture');source['color'].setValue([1,1,1,1])
expression=nuke.nodes.Expression(inputs=[source])
magnitude='0.18*pow(2,-12+24*x/511)'
for key,value in [('expr0',magnitude),('expr1',magnitude+'*(2*y/255-0.5)'),('expr2',magnitude+'*(1-y/255)'),('expr3','y<32?0:(y<64?0.25:1)')]:expression[key].setValue(value)
configs=[('input',expression,{}),('Scene',None,{'exposure':1}),('Tone',None,{'contrast':1.1,'toe':.2,'shoulder':.2}),('Crosstalk',None,{'rg':.1,'gb':-.05})]
manifest={'schema_version':1,'host':nuke.NUKE_VERSION_STRING,'interpretation':'Linear Rec.2020; manual','encoding':'scene-linear','channels':'float32 RGBA','stimulus':'512x256 stop ramp -12..12, signed channel relationships and zero/fractional/full alpha rows','cases':[],'flame_status':'pending access; compare float outputs with stated numerical targets'}
for name,node,params in configs:
    if node is None:
        node=nuke.createNode('OFXorg.gripcolor.rendition.'+name+'_v1',inpanel=False);node.setInput(0,expression);node['interpretation'].setValue(1)
        for key,value in params.items():node[key].setValue(value)
    writer=nuke.nodes.Write(inputs=[node]);writer['file'].setValue(str(out/(name+'.exr')));writer['file_type'].setValue('exr');writer['datatype'].setValue('32 bit float');writer['channels'].setValue('rgba');writer['colorspace'].setValue('linear');nuke.execute(writer,1,1)
    manifest['cases'].append({'file':name+'.exr','effect':name,'parameters':params,'alpha_mode':'RGB as supplied'})
nuke.scriptSaveAs(str(out/'GateC-fixtures.nk'),overwrite=1)
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
