"""Targeted Artist Primaries phase: seven direct tasks, fixed user view, no solver grade."""
import json,time
import numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
from .common import ROOT,read_scene,write_exr,process,Preview,count_controls
import _rendition as core
OUT=ROOT/'build/primaries'
RECIPES={
 'Cool the blacks':{'shadowHue':240,'shadowTint':.35,'shadowRange':-5,'shadowSoftness':.7},
 'Warm the shadows':{'shadowHue':35,'shadowTint':.3},
 'Creamier whites':{'highlightHue':50,'highlightTint':.2,'highlightBleach':.65,'highlightRange':1.5},
 'Hold highlights down':{'highlightCompression':.9,'shoulderStart':2,'shoulderSoftness':1.5,'whiteLevel':-.5},
 'Keep colour alive deeper into toe':{'shadowCompression':.55,'colourDeath':.7,'deathStart':-12,'deathSoftness':1.5,'shadowRetention':1.3},
 'Let colour die smoothly into black':{'colourDeath':1,'deathStart':-5,'deathSoftness':1.2},
 'Pale green skin highlights':{'highlightHue':120,'highlightTint':.35,'highlightBleach':.8,'highlightRange':-.5,'highlightSoftness':1.2}}

def run():
 OUT.mkdir(parents=True,exist_ok=True);preview=Preview();rows=[]
 for num in [5,7,60]:
  source=read_scene(ROOT/'build/artist-tests'/f'aces-{num:04d}.exr')
  for i,(task,params) in enumerate(RECIPES.items()):
   start=time.perf_counter();candidate=process('Primaries',source,params);seconds=time.perf_counter()-start
   assert np.isfinite(candidate).all() and np.array_equal(candidate[...,3].view('u4'),source[...,3].view('u4'))
   stem=f'primaries-{num:04d}-{i}';write_exr(OUT/(stem+'.exr'),candidate)
   sheet=Image.new('RGB',(1280,385));ImageDraw.Draw(sheet).text((8,3),task+' | source / one Primaries node | Flawed Emulsion 2 / sRGB',(255,255,255))
   sheet.paste(preview.image(source),(0,25));sheet.paste(preview.image(candidate),(640,25));sheet.save(OUT/(stem+'.png'))
   rows.append({'task':task,'source_frame':num,'parameters':params,'controls':count_controls([{'effect':'Primaries','parameters':params}]),'finite':True,'alpha_bit_exact':True,'cpu_seconds':seconds,'pixels':source.shape[0]*source.shape[1],'human_minutes':None,'artist_preference':None,'view':stem+'.png','scene_exr':stem+'.exr'})
 # Structured tone/chroma diagnostics, not an appearance transform.
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 ev=np.linspace(-20,20,2001);neutral=np.repeat((.18*np.exp2(ev))[:,None],3,axis=1)
 fig,axes=plt.subplots(1,2,figsize=(13,5));curve_cases={
  'Identity':{},'Contrast':{'contrast':1.4},'Toe/shoulder':{'shadowCompression':1,'highlightCompression':1},
  'Mid lift':{'midExposure':1},'Aggressive narrow mid lift':{'midExposure':4,'shadowSoftness':.25,'highlightSoftness':.25}}
 curves=[]
 for name,params in curve_cases.items():
  rgba=np.concatenate([neutral,np.ones((len(neutral),1))],-1).astype(np.float32);out=process('Primaries',rgba,params)
  y=out[:,1];axes[0].plot(ev,np.log2(np.maximum(y,1e-30)/.18),label=name)
  derivative=np.gradient(y,neutral[:,1]);axes[1].plot(ev,np.clip(derivative,0,8),label=name)
  curves.append({'name':name,'parameters':params,'nonpositive_luminance':int((y<=0).sum()),'luminance_reversal_intervals':int((np.diff(y)<0).sum()),'max_abs_rgb':float(np.max(np.abs(out[:,:3])))})
 axes[0].set(title='Neutral tone formation, no DRT',xlabel='Input EV',ylabel='Output EV');axes[1].set(title='Scalar slope (plot bounded 0–8)',xlabel='Input EV',ylabel='dYout/dYin');axes[0].legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'tone-ranges.png',dpi=140);plt.close(fig)
 report={'phase':'Artist Primaries / Tonal Colour v1 CPU prototype','choice':'B, dedicated native node; common interpretation/alpha/CAT and soft functions; no old model replacement','view':'External user Flawed Emulsion 2 / sRGB','semantics':core.semantics(8),'cases':rows,'tone_sweeps':curves,'artist_gate':'Seven direct tasks need human review. Tint/bleach preserve Y; no automatic assertion of successful skin appearance. Hue tint affects entire highlight range, not only skin.'}
 defaults={p['id']:p['default'] for p in core.parameters(8)}
 sample=np.array([[-.1,.2,4,.3]],np.float32)
 expected=[{'task':'Default identity','parameters':{},'defaults':{},'expected':sample[0].tolist()}]
 for task,params in RECIPES.items():expected.append({'task':task,'parameters':params,'defaults':{k:defaults[k] for k in params},'expected':process('Primaries',sample,params)[0].tolist()})
 (OUT/'expected-nuke.json').write_text(json.dumps(expected,indent=2)+'\n')
 (OUT/'primaries.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
 # Human observations survive regeneration of machine reports and previews.
 review=OUT/'artist-review.json'
 if not review.exists():
  review.write_text(json.dumps({'phase':'Artist Primaries v1','status':'Human review pending','reviews':[{'task':r['task'],'source_frame':r['source_frame'],'view':r['view'],'human_minutes':None,'useful':None,'tint_direction':None,'range_feel':None,'reusable':None,'notes':''} for r in rows]},indent=2)+'\n')
 body='<h1>Artist Primaries / Tonal Colour</h1><p>Seven direct tasks, one editable native node each. Scene-linear Rec.2020; previews through Flawed Emulsion 2 / sRGB. No hidden display transform.</p><a href="primaries.json">Settings, measured ranges and review fields</a><img src="tone-ranges.png">'
 for r in rows:body+=f'<details><summary>{r["task"]} — frame {r["source_frame"]}</summary><p>{r["controls"]["changed_creative_controls"]} changed controls; source / candidate. Human usefulness remains to review.</p><img loading="lazy" src="{r["view"]}"></details>'
 (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Artist Primaries</title><style>body{font:16px system-ui;background:#181a1e;color:#ddd;margin:30px auto;max-width:1300px}a{color:#9bcafa}img{width:100%}details{margin:24px 0;padding:12px;background:#25272d}summary{cursor:pointer}</style>'+body)
 return report
if __name__=='__main__':run()
