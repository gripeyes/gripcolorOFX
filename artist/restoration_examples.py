"""Focused 0.31 diagnostic stimuli, not an accepted preset/recipe library."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw
import _rendition as c
from artist.common import Preview,read_scene,rgba

def run():
 out=Path('build/control-audit-0.31');view=Preview();cases=[
 ('Cyan continuous trajectory',10,{'Crossover_hue':195,'Crossover_width':100,'Crossover_darkHue':45,'Crossover_midHue':0,'Crossover_brightHue':-25,'Crossover_darkChroma':.3,'Crossover_darkPivot':-4,'Crossover_brightPivot':3,'Crossover_transition':2}),
 ('Six-family selector refinement',10,{'separation':.4,'Volume_v2_width':60,'Volume_v2_hueDelta':-25,'Volume_v2_density':.25,'Volume_v3_width':60,'Volume_v3_hueDelta':30}),
 ('Authored row-sum matrix',10,{'Crosstalk_mode':1,'Crosstalk_m02':.15,'Crosstalk_m12':-.1,'separation':.3}),
 ('Material selected depth and anchors',11,{'density':.5,'Density_hue':70,'Density_width':100,'Density_chromaCoupling':.4,'Density_highlightProtection':.8,'separation':.45,'Strip_palette':.3,'Strip_leakage':.3,'Strip_redAnchor':.6}),
 ('Strip custom record interaction',11,{'Strip_mode':2,'Strip_separation':.5,'Strip_m01':.15,'Strip_m12':.1,'Strip_gWeight':.9,'Strip_density':.3,'Strip_neutralAnchor':1}),
 ('Base porcelain highlight tint',9,{'highlightCompression':.5,'highlightTint':.15,'highlightHue':130,'highlightRetention':.4,'highlightBleach':.3}),
 ]
 samples=[read_scene(Path('build/artist-tests')/f'aces-{n:04d}.exr')[::3,::3] for n in [5,60]]
 ev=np.linspace(-12,12,193);seeds=np.array([[1,.01,.01],[1,.8,.01],[.01,1,.01],[.01,1,1],[.01,.01,1],[1,.01,1],[.65,.3,.18],[.2,.24,.06]])
 matrix=np.array(c.matrix(0)).reshape(3,3);metrics=[]
 for i,(label,e,settings) in enumerate(cases):
  p={'interpretation':1,**({'modelVersion':1} if e in [10,11] else {}),**settings}
  canvas=Image.new('RGB',(960,400));draw=ImageDraw.Draw(canvas)
  for j,im in enumerate(samples):
   y=c.process(e,im,p);a=c.process(e,im,{'interpretation':1})
   canvas.paste(view.image(a).resize((320,180)),(0,j*200+20));canvas.paste(view.image(y).resize((320,180)),(320,j*200+20))
   diff=y[:,:,:3]-a[:,:,:3];scale=max(np.max(abs(diff)),1e-8)
   canvas.paste(Image.fromarray(np.uint8(np.clip(.5+.5*diff/scale,0,1)*255)).resize((320,180)),(640,j*200+20))
   draw.text((4,j*200+2),'Default',fill='white');draw.text((324,j*200+2),label,fill='white');draw.text((644,j*200+2),'Normalized signed scene-RGB difference',fill='white')
  canvas.save(out/f'example-{i}.png')
  fig,axes=plt.subplots(1,3,figsize=(12,3.2));metric={'name':label,'effect':e,'parameters':p,'family_metrics':[]}
  for family,seed in enumerate(seeds):
   x=rgba(seed[None,:]*2.**ev[:,None]);y=c.process(e,x,p);xyz=y[:,:3]@matrix.T
   lab=np.array([c.opponent(q.tolist(),False) for q in xyz]);hue=np.rad2deg(np.unwrap(np.arctan2(lab[:,2],lab[:,1])));chroma=np.linalg.norm(lab[:,1:],axis=1)/np.maximum(abs(lab[:,0]),1e-6)
   axes[0].plot(ev,hue);axes[1].plot(ev,chroma);axes[2].plot(ev,xyz[:,1]/np.maximum((x[:,:3]@matrix.T)[:,1],1e-8))
   metric['family_metrics'].append({'family':family,'finite':bool(np.isfinite(y).all()),'alpha_exact':bool(np.array_equal(x[:,3],y[:,3])),'max_scene_rgb_delta':float(np.max(abs(y[:,:3]-x[:,:3])))})
  for ax,title in zip(axes,['Unwrapped signed-opponent hue (degrees)','Relative signed-opponent chroma','Scene Y output / input']):ax.set_title(title,fontsize=9);ax.set_xlabel('Exposure stops');ax.grid(alpha=.2)
  fig.suptitle(label+' — pre-DRT diagnostics');fig.tight_layout();fig.savefig(out/f'example-{i}-trajectory.png',dpi=120);plt.close(fig);metrics.append(metric)
 # Existing Volume diagnostic: individual and combined selections, not output clipping.
 im=samples[1];canvas=Image.new('RGB',(320*4,200*2));draw=ImageDraw.Draw(canvas)
 for d in range(8):
  y=c.process(10,im,{'interpretation':1,'modelVersion':1,'Volume_debug':d,'Volume_v3_width':45})
  img=view.image(y) if d==0 else Image.fromarray(np.uint8(np.clip(y[:,:,:3],0,1)*255))
  canvas.paste(img.resize((320,180)),((d%4)*320,(d//4)*200+20));draw.text(((d%4)*320+4,(d//4)*200+2),['Source','Combined','Red','Yellow','Green','Cyan','Blue','Magenta'][d],fill='white')
 canvas.save(out/'family-selections.png')
 (out/'targeted-examples.json').write_text(json.dumps({'purpose':'diagnostic authored test cases; not artist-accepted recipes','cases':metrics},indent=2)+'\n')
 index=out/'index.html'
 if index.exists():
  html=index.read_text().split('<h2>Targeted authored diagnostic examples</h2>')[0]
  html+='<h2>Targeted authored diagnostic examples</h2><p>Test stimuli, not artist-accepted presets. Quantitative trajectories remain pre-DRT.</p><img src="family-selections.png">'
  for i,metric in enumerate(metrics):html+=f'<details><summary>{metric["name"]}</summary><img src="example-{i}.png"><img src="example-{i}-trajectory.png"></details>'
  index.write_text(html)
 print('Targeted diagnostic examples',len(metrics))
if __name__=='__main__':run()
