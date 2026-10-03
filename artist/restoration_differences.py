"""Small explicit scene-RGB difference diagnostics for every swept creative control."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
import _rendition as c
from artist.common import read_scene,NAMES

def run():
 out=Path('build/control-audit-0.31');r=json.loads((out/'control-audit.json').read_text());source=read_scene(Path('build/artist-tests/aces-0005.exr'))[::12,::12];records=[]
 for row in r['controls']:
  if 'activation_settings' not in row:continue
  effect=NAMES.index(row['effect']);key=row['parameter']['id'];valid=[x for x in row['observations'] if 'max_rgb_difference' in x]
  if not valid:continue
  chosen=max(valid,key=lambda x:x['max_rgb_difference']);base=row['activation_settings']
  try:
   a=c.process(effect,source,base);b=c.process(effect,source,{**base,key:chosen['value']});delta=b[:,:,:3]-a[:,:,:3];scale=max(float(np.max(abs(delta))),1e-8)
   file=row['effect']+'-'+key+'-difference-small.png';Image.fromarray(np.uint8(np.clip(.5+.5*delta/scale,0,1)*255)).resize((320,180),Image.Resampling.NEAREST).save(out/file)
   records.append({'effect':row['effect'],'control':key,'value':chosen['value'],'display_scale_max_abs_rgb':scale,'file':file,'meaning':'Signed scene-RGB difference, normalized symmetrically; small sample diagnostic, not beauty image'})
  except Exception as ex:records.append({'effect':row['effect'],'control':key,'value':chosen['value'],'error':str(ex)})
 (out/'difference-diagnostics.json').write_text(json.dumps(records,indent=2)+'\n')
 html=(out/'index.html').read_text().split('<h2>Additional per-control scene differences</h2>')[0]+'<h2>Additional per-control scene differences</h2><p>Small sampled diagnostics with explicit independent symmetric scaling. See difference-diagnostics.json for strengths and scales.</p>'
 for record in records:
  if 'file' in record:html+=f'<details><summary>{record["effect"]} / {record["control"]} = {record["value"]:.4g}</summary><img style="width:320px" src="{record["file"]}"></details>'
 (out/'index.html').write_text(html);print('Per-control difference diagnostics',len(records))
if __name__=='__main__':run()
