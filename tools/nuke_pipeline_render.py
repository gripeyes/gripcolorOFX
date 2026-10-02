"""Measure installed effect boundary defaults without assuming scene semantics."""
import nuke,json,math
from pathlib import Path
out=Path(__file__).resolve().parents[1]/'build/architecture-0.3';rows=[]
src=nuke.nodes.Constant();src['format'].setValue('square_256')
for effect in ['OFXorg.spektrafilm_v0','OFXorg.spektrafilm.diffuse_v0']:
 node=nuke.createNode(effect,inpanel=False);node.setInput(0,src);node['inputColorSpace'].setValue('Linear Rec.2020')
 for pixel in [[.18,.18,.18,1],[-.1,.2,4,.3]]:
  src['color'].setValue(pixel)
  try:
   values=[node.sample(ch,100.5,100.5,frame=1) for ch in ['red','green','blue','alpha']]
   rows.append({'class':effect,'input':pixel,'outputRole':node['outputRole'].value(),'process':node['process'].value(),'sample':values,'finite':all(math.isfinite(x) for x in values),'semantics_accepted':False})
  except Exception as ex:rows.append({'class':effect,'input':pixel,'render_error':str(ex),'semantics_accepted':False})
(out/'pipeline-render.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PIPELINE_RENDER',json.dumps(rows))
