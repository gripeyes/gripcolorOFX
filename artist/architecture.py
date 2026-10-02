"""0.3 artist workflows and targeted monotonic alternative comparisons."""
from pathlib import Path
import json,time,html
import numpy as np
from PIL import Image,ImageDraw
from scipy.interpolate import PchipInterpolator
from .common import ROOT,NAMES,read_scene,write_exr,process,Preview
from .primaries import RECIPES
import _rendition as c
OUT=ROOT/'build/architecture-0.3'
PALETTE={
 'Green to olive':{'familyGreen':-35,'compression':.2},
 'Cyan toward blue-black as exposure falls':{'familyCyan':25,'shadowHue':30,'colourDeath':.7},
 'Protect red and compress secondary colours':{'compression':.7,'accent':1},
 'Bronze / green neutral contamination':{'contamination':.5,'bias':.25},
 'One red accent, suppress the remainder':{'compression':1,'accent':1},
 'Separate major colour families':{'separation':.6}}
MATERIAL={
 'Depth':{'depth':.8},'Material density / chroma':{'density':.7,'coupling':.5},
 'Leaky separation':{'separation':.7,'leakage':.65,'anchor':.7},
 'Contaminated depth':{'depth':.5,'contamination':.6,'crosstalk':.4}}

def run():
 OUT.mkdir(parents=True,exist_ok=True);preview=Preview();rows=[]
 for frame in [5,7,60,4]:
  source=read_scene(ROOT/'build/artist-tests'/f'aces-{frame:04d}.exr')
  for effect,recipes in [('Base',RECIPES),('Palette',PALETTE),('Material',MATERIAL)]:
   for index,(task,p) in enumerate(recipes.items()):
    start=time.perf_counter();candidate=process(effect,source,p);elapsed=time.perf_counter()-start
    assert np.isfinite(candidate).all() and np.array_equal(source[...,3].view('u4'),candidate[...,3].view('u4'))
    stem=f'{effect.lower()}-{frame:04d}-{index}';write_exr(OUT/(stem+'.exr'),candidate)
    sheet=Image.new('RGB',(1280,385));ImageDraw.Draw(sheet).text((8,4),task+' | source / '+effect+' | external Flawed Emulsion 2 / sRGB',fill='white');sheet.paste(preview.image(source),(0,25));sheet.paste(preview.image(candidate),(640,25));sheet.save(OUT/(stem+'.png'))
    rows.append({'effect':effect,'task':task,'frame':frame,'parameters':p,'view':stem+'.png','scene_exr':stem+'.exr','cpu_seconds':elapsed,'finite':True,'alpha_bit_exact':True})
 y=.18*np.exp2(np.linspace(-20,20,8001));a=np.repeat(y[:,None],3,-1);p={'midExposure':4,'shadowSoftness':.25,'highlightSoftness':.25}
 old=process('Primaries',np.c_[a,np.ones(len(a))].astype('f4'),p)[:,1];base=process('Base',np.c_[a,np.ones(len(a))].astype('f4'),p)[:,1]
 ev=np.log2(y/.18);raw=np.log2(old/.18);knots=np.arange(0,len(ev),100);pchip=PchipInterpolator(ev[knots],raw[knots])(ev)
 displacement=raw-ev;bounded=ev+2*np.tanh(displacement/2)
 def reversal(x):return int(np.sum(np.diff(x)<-2e-6*np.maximum(np.abs(x[:-1]),1e-8)))
 alternatives={'historical_gain':reversal(old),'raw_knots_PCHIP':int(np.sum(np.diff(pchip)<0)),'amplitude_bounded_displacement':int(np.sum(np.diff(bounded)<0)),'integrated_positive_slope_Base':reversal(base)}
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 fig,ax=plt.subplots(figsize=(10,5));ax.plot(ev,raw,label='Primaries v1');ax.plot(ev,pchip,label='PCHIP on raw knots');ax.plot(ev,bounded,label='Amplitude bounded');ax.plot(ev,np.log2(base/.18),label='Base positive slope');ax.set(xlabel='Input stops',ylabel='Output stops',title='Same +4 stop narrow midtone intention');ax.legend();fig.tight_layout();fig.savefig(OUT/'base-monotonic.png',dpi=140);plt.close(fig)
 # Actual combined Palette geometry, source-space selection and derivative reliability.
 samples=np.array([[.8,.02,.01],[.2,.24,.06],[.01,.6,.8],[-.1,.2,4],[.18,.18,.18]],np.float32)
 geometry=[]
 for task,params in PALETTE.items():
  d=c.differentials(10,samples,{'interpretation':1,**params},.002)
  geometry.append({'task':task,'parameters':params,'samples':samples.tolist(),'columns':'Jacobian9, determinant, stretches3, condition, disagreement, reliable','data':d.tolist()})
 report={'phase':'0.3 artist architecture candidate','artist_cases':rows,'monotone_comparison':alternatives,'palette_geometry':geometry,'original_model_compatibility':'Primaries v1 retained; stored 0.2.1 reference recipes pass','artist_acceptance':'Pending human predictability / time / reuse / actual authored CG / SpektraFilm comparison','model_policy':'Stable IDs plus explicit v1 selections; no silent replacement'}
 (OUT/'architecture.json').write_text(json.dumps(report,indent=2)+'\n')
 review=OUT/'artist-review.json'
 if not review.exists():review.write_text(json.dumps({'status':'Human acceptance pending','cases':[{'effect':r['effect'],'task':r['task'],'frame':r['frame'],'human_minutes':None,'predictable':None,'useful_vs_simple_baseline':None,'reuse':None,'duplicates_spektra':None,'notes':''} for r in rows]},indent=2)+'\n')
 body='<h1>Rendition 0.3 — Inspector / artist architecture</h1><p>Base → Palette → Material. Optional Pigment organizes spatial information. Optional SpektraFilm adds photographic character. The appropriate final display path remains separate.</p><nav><a href="architecture.json">Settings / geometry / model contract</a> · <a href="artist-review.json">Preserved artist review</a> · <a href="../validation-0.2/index.html">Volume geometry, HK, trajectories, palette / OT, structural maps and Pigment bridge</a> · <a href="full-spectral.json">Full spectral vs compact</a> · <a href="nuke-architecture.json">Nuke checks</a></nav><h2>Base monotonic alternatives</h2><img src="base-monotonic.png"><h2>Full Spectral Reference</h2><p>Matched basis measures approximation; other reconstructions measure ambiguity. No recovered-spectrum or artist-superiority claim.</p><img src="full-spectral.png">'
 for effect in ['Base','Palette','Material']:
  body+='<h2>'+effect+'</h2>'
  if effect=='Material':body+='<p>Research front end. Compare with M17 simple baselines; retained complexity is provisional until artist advantage is observed.</p>'
  for r in rows:
   if r['effect']==effect:body+=f'<details><summary>{html.escape(r["task"])} / frame {r["frame"]}</summary><img loading="lazy" src="{r["view"]}"></details>'
 (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Rendition 0.3 Inspector</title><style>body{font:16px system-ui;background:#181a1e;color:#ddd;margin:30px auto;max-width:1300px}a{color:#9bcafa}img{width:100%}details{margin:24px 0;padding:12px;background:#25272d}summary{cursor:pointer}</style>'+body)
 print('Artist cases',len(rows),'Monotonic alternatives',alternatives);return report
if __name__=='__main__':run()
