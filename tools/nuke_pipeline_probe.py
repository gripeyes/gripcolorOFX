"""Read installed third-party effect interfaces; no inferred reproduction settings."""
import nuke,json
from pathlib import Path
out=Path(__file__).resolve().parents[1]/'build/architecture-0.3'
rows=[]
for name in ['OFXorg.spektrafilm_v0','OFXorg.spektrafilm.diffuse_v0','OFXorg.painterlyofx.ChromaDiffusion_v1','OFXorg.painterlyofx.DetailCollapse_v1']:
 try:
  node=nuke.createNode(name,inpanel=False)
  controls=[]
  for k in node.knobs().values():
   if k.Class() in ('Enumeration_Knob','Boolean_Knob') or any(x in k.name().lower() for x in ['input','output','gamma','space','mode','print','negative','enable','mix']):
    entry={'id':k.name(),'label':k.label(),'class':k.Class()}
    try:entry['value']=k.value()
    except Exception:pass
    if k.Class()=='Enumeration_Knob':entry['choices']=k.values()
    controls.append(entry)
  rows.append({'class':name,'created':True,'controls':controls})
 except Exception as ex:rows.append({'class':name,'created':False,'error':str(ex)})
(out/'pipeline-interfaces.json').write_text(json.dumps(rows,indent=2,default=str)+'\n')
print('PIPELINE_PROBE',json.dumps(rows,default=str))
