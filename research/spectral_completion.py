"""Focused completion of the existing 0.3 oracle. No production equations change.
Quantitative data are unbounded scene-linear Rec.2020; PNGs use the external view.
"""
from pathlib import Path
from time import perf_counter
import json
import platform
import numpy as np
import colour
from scipy.optimize import least_squares
from scipy.special import expit
from .full_reference import FullReference, positive, smooth, WEIGHTS, hue_pair
import _rendition as core

METHODS=['compact_basis','nnls_residual','smits_residual','sigmoid_d65_pilot']
COLORS={'red':[.8,.02,.01],'yellow':[.8,.7,.01],'green':[.02,.7,.04],
 'cyan':[.01,.6,.8],'blue':[.01,.04,.9],'magenta':[.7,.01,.6],
 'skin':[.65,.3,.18],'olive':[.2,.24,.06],'ochre':[.65,.35,.03],
 'deep_chromatic_shadow':[.003,.012,.025]}

class CompletionReference(FullReference):
 """Extends coverage only. The sigmoid/D65 adapter is ours, not rgb2spec.
 Published three-coefficient sigmoid-quadratic family; direct SciPy fit, no tables.
 """
 def __init__(self):
  super().__init__();x=(self.lab.grid-595)/235
  self.poly=np.array([x*x,x,np.ones_like(x)]).T
  self.d65=self.lab.illuminant.values/np.sum(self.lab.illuminant.values*self.lab.emission_weights[:,1])
  self.white=self.d65@self.lab.emission_weights;self.fit_cache={};self.fit_diagnostics=[]
 def reconstruct(self,xyz,method):
  if method!='sigmoid_d65_pilot':return super().reconstruct(xyz,method)
  xyz=np.asarray(xyz,float);scale=2*np.max(np.abs(xyz/self.white))
  if scale==0:return np.zeros_like(self.lab.grid),np.zeros(3),None
  target=xyz/scale;key=tuple(target)
  if key not in self.fit_cache:
   def spectrum(c):
    z=self.poly@c
    return .5*(1+z/np.hypot(1,z))*self.d65
   def fun(c):return (spectrum(c)@self.lab.emission_weights-target)/self.white
   fits=[least_squares(fun,start,max_nfev=120,xtol=1e-10,ftol=1e-10,gtol=1e-10) for start in [[0,0,-.6],[2,0,-1],[-2,0,1]]]
   best=min(fits,key=lambda r:np.linalg.norm(r.fun));shape=spectrum(best.x)
   self.fit_cache[key]=shape
   self.fit_diagnostics.append({'target':target.tolist(),'coefficients':best.x.tolist(),'relative_xyz_residual':float(np.linalg.norm(best.fun)), 'jacobian_condition':float(np.linalg.cond(best.jac)) if np.isfinite(np.linalg.cond(best.jac)) else None, 'jacobian_rank':int(np.linalg.matrix_rank(best.jac)), 'success':bool(best.success),'evaluations':best.nfev})
  base=self.fit_cache[key]*scale
  return base,xyz-base@self.lab.emission_weights,None
 def evaluate(self,rgb,effect,method='compact_basis',settings=None):
  p=settings or {};rgb=np.asarray(rgb,float)
  if rgb.shape[-1]!=3 or not np.isfinite(rgb).all():raise ValueError('Finite RGB required')
  M=np.array(core.matrix(0)).reshape(3,3);inverse=np.linalg.inv(M);result=[]
  for source in rgb.reshape(-1,3):
   xyz=M@source;q=colour.XYZ_to_Oklab(xyz);c=np.hypot(q[1],q[2]);relative=c/max(abs(q[0]),1e-12);h=np.degrees(np.arctan2(q[2],q[1]))%360
   base,residual,coeff=self.reconstruct(xyz,method)
   if effect=='Density':
    d=p.get('density',.75)
    if not -1<=d<=1:raise ValueError('Density out of domain')
    filtered=(base*self.attenuation(h,abs(d),'Density'))@self.lab.emission_weights+residual
    candidate=xyz+np.sign(d)*(filtered-xyz);cq=colour.XYZ_to_Oklab(candidate);cc=np.hypot(cq[1],cq[2])
    if cc>1e-12:cq[1:]*=c*2**(d*p.get('chromaCoupling',0))/cc
    candidate=colour.Oklab_to_XYZ(cq)
    # Scalar ACEScct toe avoids evaluating an unused log on signed Y.
    encoded=10.5402377416545*xyz[1]+.0729055341958355 if xyz[1]<=.0078125 else (np.log2(xyz[1])+9.72)/17.52
    ev=(encoded-(np.log2(.18)+9.72)/17.52)*17.52
    w=smooth(0,.03,relative)*(1-smooth(4,5,relative))*smooth(-30,-20,ev)*(1-smooth(20,30,ev))
    w*=1-p.get('highlightProtection',.5)*expit((ev-3)/2)
    sw=p.get('shadowWeight',.5);w*=1-sw+sw*expit((-ev+2)/2)
    out=xyz+w*(candidate-xyz)
   elif effect=='Strip':
    amount=p.get('separation',.75);leak=p.get('leakage',.1)*amount
    if not 0<=amount<=1 or not 0<=p.get('leakage',.1)<=1:raise ValueError('Strip out of domain')
    if coeff is None:
     masks=self.basis/np.sum(self.basis,axis=1,keepdims=True)
     records=(base[:,None]*masks).T
     energy=records@self.lab.emission_weights[:,1];coeff=energy/self.B[1]
     shapes=np.divide(records,coeff[:,None],out=self.basis.T.copy(),where=coeff[:,None]>1e-30)
    else:shapes=self.basis.T
    separated=(1-leak)*coeff+leak*np.mean(coeff);mode=p.get('mode',0)
    R=np.array([[p.get('m'+str(i)+str(j),float(i==j)) for j in range(3)] for i in range(3)])
    if mode==1:
     mid=separated[1];separated=separated.copy();separated[1]=0;separated[[0,2]]+=mid*.5
    elif mode==2:separated=R@separated
    elif mode!=0:raise ValueError('Unknown record mode')
    pos=positive(separated);rr=separated-pos;total=pos.sum()
    if total>0 and p.get('palette',0)!=0:
     shape=(pos/total)**(2**(amount*p['palette']));pos=shape*total/shape.sum()
    pos*=np.array([p.get(k+'Contribution',1) for k in 'bgr'])
    active=pos@shapes;d=amount*(.6+.4*p.get('density',0))
    filtered=(active*self.attenuation(h,d,'Strip'))@self.lab.emission_weights
    # Projection is part of the existing record recombination contract.
    recombined=self.inverse@filtered+rr;recombined*=np.array([p.get(k+'Weight',1) for k in 'bgr'])
    if mode==2:recombined=np.linalg.solve(R,recombined)
    candidate=self.B@recombined+residual
    neutral=1-p.get('neutralAnchor',1)+p.get('neutralAnchor',1)*smooth(0,.05,relative)
    distance=abs((h-29+180)%360-180);red=1-p.get('redAnchor',0)*(1-smooth(20,70,distance))
    out=xyz+amount*neutral*red*p.get('mix',1)*(candidate-xyz)
   else:raise ValueError('Unknown reference effect')
   result.append(inverse@out)
  return np.array(result).reshape(rgb.shape)

def compact(rgb,effect,p):
 rgb=np.asarray(rgb,np.float32);shape=rgb.shape
 a=np.c_[rgb.reshape(-1,3),np.ones(rgb.size//3,np.float32)]
 return np.asarray(core.process(3 if effect=='Density' else 6,a,{'interpretation':1,**p}))[:,:3].reshape(shape)

def coordinates(rgb):
 xyz=np.asarray(rgb)@np.array(core.matrix(0)).reshape(3,3).T;q=colour.XYZ_to_Oklab(xyz)
 return {'xyz':xyz.tolist(),'Y':float(xyz[1]),'hue_degrees':float(np.degrees(np.arctan2(q[2],q[1]))%360),'chroma':float(np.hypot(q[1],q[2]))}

def baselines(train,out,test):
 # Unrestricted RGB matrix, followed by independently fitted smooth channel curves.
 # Fixed held-out split, no test-set fitting and no output clipping.
 A=np.linalg.lstsq(train,out,rcond=None)[0];z=train@A;zt=test@A
 lo=z.min(0);span=np.maximum(z.max(0)-lo,1e-12);u=(z-lo)/span;ut=(zt-lo)/span
 curve=np.stack([np.linalg.lstsq(np.c_[np.ones(len(u)),u[:,i],u[:,i]**2,u[:,i]**3],out[:,i],rcond=None)[0] for i in range(3)])
 curved=np.stack([np.c_[np.ones(len(ut)),ut[:,i],ut[:,i]**2,ut[:,i]**3]@curve[i] for i in range(3)],-1)
 return zt,curved,A

def run():
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 out=Path('build/spectral-completion');out.mkdir(parents=True,exist_ok=True);o=CompletionReference();rows=[];recons=[]
 print('Reconstruction pilot and expanded sweeps',flush=True)
 for family,rgb in COLORS.items():
  rgb=np.array(rgb);Y=float(np.array(core.matrix(0)).reshape(3,3)[1]@rgb)
  for chroma in [0,.5,1,1.5]:
   color=Y+(rgb-Y)*chroma;xyz=np.array(core.matrix(0)).reshape(3,3)@color
   for method in METHODS:
    t=perf_counter();b,r,_=o.reconstruct(xyz,method);elapsed=perf_counter()-t;b2,r2,_=o.reconstruct(2*xyz,method)
    shape=b/max(np.linalg.norm(b),1e-30);pred=b@o.lab.emission_weights
    recons.append({'family':family,'chroma_scale':chroma,'method':method,'base_xyz_error':float(np.linalg.norm(pred-xyz)/max(np.linalg.norm(xyz),1e-30)),'recombined_xyz_error':float(np.max(abs(pred+r-xyz))),'normalized_curvature':float(np.linalg.norm(np.diff(shape,2))), 'residual_fraction':float(np.linalg.norm(r)/max(np.linalg.norm(xyz),1e-30)), 'double_exposure_error':float(np.max(abs(b2-2*b))), 'seconds':elapsed})
   for ev in [-10,-5,0,5,10]:
    source=color*2.**ev
    for effect in ['Density','Strip']:
     for depth in [0,.25,.5,.75,1]:
      p={'density':depth} if effect=='Density' else {'separation':depth,'leakage':.1}
      prod=compact(source,effect,p)
      for method in METHODS:
       ref=o.evaluate(source,effect,method,p)
       rows.append({'family':family,'chroma_scale':chroma,'exposure_stops':ev,'depth':depth,'effect':effect,'method':method,'source':source.tolist(),'production':prod.tolist(),'reference':ref.tolist(),'production_coordinates':coordinates(prod),'reference_coordinates':coordinates(ref),'relative_rgb_error':float(np.max(abs(ref-prod))/max(np.max(abs(source)),1e-30))})
 print('Strip record interactions and held-out simple baselines',flush=True)
 rng=np.random.default_rng(317);train=rng.uniform(.005,1,(180,3));test=rng.uniform(.005,1,(90,3))
 settings={'default':{'separation':.75},'leakage':{'separation':.8,'leakage':.8},'two_record':{'separation':.8,'mode':1},'custom_record':{'separation':.8,'mode':2,'m01':.15,'m12':-.1},'palette':{'separation':.8,'palette':.7},'recombination':{'separation':.8,'rWeight':.7,'bWeight':1.4,'gContribution':.7},'anchor':{'separation':1,'redAnchor':1},'depth':{'separation':.8,'density':1}}
 controls=[];baseline=[]
 for name,p in settings.items():
  prod=compact(test,'Strip',p)
  for method in METHODS:
   ref=o.evaluate(test,'Strip',method,p);fit=o.evaluate(train,'Strip',method,p);matrix,curves,A=baselines(train,fit,test)
   controls.append({'case':name,'parameters':p,'method':method,'oracle_production_max_rgb_error':float(np.max(abs(ref-prod)))})
   baseline.append({'case':name,'method':method,'held_out_matrix_rmse':float(np.sqrt(np.mean((matrix-ref)**2))),'held_out_matrix_curves_rmse':float(np.sqrt(np.mean((curves-ref)**2))),'held_out_compact_rmse':float(np.sqrt(np.mean((prod-ref)**2))),'matrix':A.tolist()})
 # Reproduction references are appearance, never labelled scene rendition.
 reproduction=[]
 for family,rgb in COLORS.items():
  coverage=np.array(rgb)/max(max(rgb),1e-30)*.8
  for concentration in [0,.25,.5,1,2]:
   for model in ['KM','Beer-Lambert','Neugebauer','Yule-Nielsen']:
    spectrum=o.lab.pigment(coverage,concentration) if model=='KM' else o.lab.dye(coverage,concentration,.1) if model=='Beer-Lambert' else o.lab.neugebauer(coverage*min(concentration/2,1),1 if model=='Neugebauer' else 2)
    xyz=o.lab.xyz(spectrum)
    reproduction.append({'family':family,'model':model,'amount':concentration,'semantics':'appearance-referred D65 synthetic surface/reference, not directly comparable scene operator','xyz':xyz.tolist()})
 print('Signed/HDR transition and exposure diagnostics',flush=True)
 signed=[];neutral_checks=[]
 probes=np.array([[0,0,0],[-1,-2,-3],[-.2,.3,4],[10000,2000,-50],[1e-10,-1e-10,2e-10]])
 ramp=np.c_[np.linspace(-.002,.002,81),np.full(81,.2),np.full(81,.4)]
 zero=np.linspace(-1e-7,1e-7,81)[:,None]*np.array([-.2,.3,4]);boundary=np.c_[np.linspace(-.05,.05,81),np.full(81,.001),np.ones(81)]
 for effect in ['Density','Strip']:
  p={'density':.75} if effect=='Density' else {'separation':.75}
  for method in METHODS:
   gray=np.array([[-.2,-.2,-.2],[0,0,0],[.18,.18,.18],[10,10,10]])
   graded=o.evaluate(gray,effect,method,p)
   neutral_checks.append({'effect':effect,'method':method,'source':gray.tolist(),'reference':graded.tolist(),'production':compact(gray,effect,p).tolist(),'relative_magnitude_drift':float(np.max(abs(graded-gray))/10),'max_axis_difference':float(np.max(abs(graded[:,:2]-graded[:,1:])) )})
   refs=o.evaluate(probes,effect,method,p);twice=o.evaluate(probes*2,effect,method,p)
   transitions={}
   for name,rr in [('mixed_sign',ramp),('through_zero',zero),('saturated_boundary',boundary)]:
    values=o.evaluate(rr,effect,method,p);deltas=np.max(abs(np.diff(values,axis=0)),axis=1)
    transitions[name]={'max_adjacent_rgb_step':float(max(deltas)),'input_max_step':float(np.max(abs(np.diff(rr,axis=0)))),'finite':bool(np.isfinite(values).all())}
   signed.append({'effect':effect,'method':method,'probes':probes.tolist(),'reference':refs.tolist(),'double_exposure_relative_error':float(np.max(abs(twice-2*refs))/max(np.max(abs(probes)),1)),'transitions':transitions})
 print('Runtime and trajectory plots',flush=True)
 timings=[];runtime_data=test[:64]
 for effect in ['Density','Strip']:
  p={'density':.75} if effect=='Density' else {'separation':.75}
  compact(runtime_data,effect,p);times=[]
  for _ in range(7):
   t=perf_counter();compact(runtime_data,effect,p);times.append(perf_counter()-t)
  cpu=float(np.median(times))
  for method in METHODS:
   # Cold sigmoid solver vs warm cache reported separately. Cache never improves equations.
   if method=='sigmoid_d65_pilot':o.fit_cache.clear()
   t=perf_counter();o.evaluate(runtime_data,effect,method,p);cold=perf_counter()-t;times=[]
   for _ in range(3):
    t=perf_counter();o.evaluate(runtime_data,effect,method,p);times.append(perf_counter()-t)
   warm=float(np.median(times));timings.append({'effect':effect,'method':method,'pixels':64,'compact_batch_seconds':cpu,'oracle_cold_seconds':cold,'oracle_warm_seconds':warm,'warm_runtime_ratio':warm/cpu,'cold_runtime_ratio':cold/cpu})
 for effect in ['Density','Strip']:
  fig,axes=plt.subplots(3,4,figsize=(15,10))
  for ax,family in zip(axes.flat,COLORS):
   for method in METHODS:
    rr=[r for r in rows if r['family']==family and r['chroma_scale']==1 and r['exposure_stops']==0 and r['effect']==effect and r['method']==method]
    ax.plot([r['reference_coordinates']['chroma'] for r in rr],[r['reference_coordinates']['Y'] for r in rr],'-o',ms=2,label=method)
   ax.plot([r['production_coordinates']['chroma'] for r in rr],[r['production_coordinates']['Y'] for r in rr],'k--',label='production');ax.set(title=family,xlabel='signed-Oklab C',ylabel='scene Y')
  axes.flat[-1].axis('off');axes.flat[-2].axis('off');axes.flat[0].legend(fontsize=6);fig.suptitle(effect+' / depth trajectories, pre-DRT');fig.tight_layout();fig.savefig(out/(effect.lower()+'-trajectories.png'),dpi=120);plt.close(fig)
  fig,axes=plt.subplots(1,3,figsize=(14,4))
  for method in METHODS:
   rr=[r for r in rows if r['family']=='skin' and r['chroma_scale']==1 and r['effect']==effect and r['depth']==.75 and r['method']==method]
   ev=[r['exposure_stops'] for r in rr];axes[0].plot(ev,[r['reference_coordinates']['Y']/2**r['exposure_stops'] for r in rr],label=method)
   axes[1].plot(ev,[r['reference_coordinates']['hue_degrees'] for r in rr]);axes[2].plot(ev,[r['relative_rgb_error'] for r in rr])
  axes[0].set(ylabel='Y / exposure scale');axes[1].set(ylabel='Hue degrees');axes[2].set(ylabel='Relative RGB error')
  for ax in axes:ax.set_xlabel('Scene exposure stops')
  axes[0].legend(fontsize=7);fig.tight_layout();fig.savefig(out/(effect.lower()+'-exposure.png'),dpi=120);plt.close(fig)
 fig,axes=plt.subplots(2,3,figsize=(13,7))
 for ax,family in zip(axes.flat,['skin','cyan','magenta','olive','red','yellow']):
  xyz=np.array(core.matrix(0)).reshape(3,3)@COLORS[family]
  for method in METHODS:
   b,_,_=o.reconstruct(xyz,method);ax.plot(o.lab.grid,b/max(np.max(b),1e-30),label=method)
  ax.set(title=family,xlabel='nm',ylabel='Shape / own peak')
 axes.flat[0].legend(fontsize=7);fig.tight_layout();fig.savefig(out/'reconstruction-shapes.png',dpi=120);plt.close(fig)
 print('Small scene-linear image comparisons through external Flawed Emulsion 2',flush=True)
 from artist.common import read_scene,Preview,rgba,write_exr
 from PIL import Image,ImageDraw
 view=Preview();images=[]
 for num in [5,60]:
  image=read_scene(Path('build/artist-tests')/f'aces-{num:04d}.exr')[::15,::15,:3]
  for effect in ['Density','Strip']:
   p={'density':.75,'chromaCoupling':.3} if effect=='Density' else {'separation':.8,'density':.7,'palette':.4,'redAnchor':.6}
   outputs={'source':image,'production':compact(image,effect,p)}
   for method in METHODS:outputs[method]=o.evaluate(image,effect,method,p).astype('f4')
   reftrain=o.evaluate(train,effect,'nnls_residual',p);matrix,curves,_=baselines(train,reftrain,image.reshape(-1,3));outputs['matrix']=matrix.reshape(image.shape);outputs['matrix_curves']=curves.reshape(image.shape)
   canv=Image.new('RGB',(320*4,215*2));draw=ImageDraw.Draw(canv)
   for i,(name,v) in enumerate(outputs.items()):
    tag=f'{effect.lower()}-{num:04d}-{name}';write_exr(out/(tag+'.exr'),rgba(v.astype('f4')))
    preview=view.image(rgba(v.astype('f4'))).resize((320,180),Image.Resampling.NEAREST)
    x=(i%4)*320;y=(i//4)*215;canv.paste(preview,(x,y+30));draw.text((x+5,y+5),name,fill='white')
   name=f'{effect.lower()}-{num:04d}.png';canv.save(out/name);images.append({'file':name,'effect':effect,'source':f'aces-{num:04d}','parameters':p,'sampling':'Every fifteenth pixel of approved Rec.2020 fixture; nearest enlarged, not full-resolution spatial acceptance','view':'External Flawed Emulsion 2 / sRGB; quantitative EXRs pre-DRT'})
 matched=[r['relative_rgb_error'] for r in rows if r['method']=='compact_basis'];matched_controls=[r['oracle_production_max_rgb_error'] for r in controls if r['method']=='compact_basis']
 report={'schema_version':1,'baseline':'Existing 0.3 432 comparisons retained unchanged','grid':'360–830 nm / 1 nm','semantics':'Nonunique plausible metamers; signed residual has no physical interpretation. No spectrum recovery claim. Quantitative data pre-DRT scene-linear Rec.2020.','production_equations_changed':False,'machine':platform.platform(),'rows':rows,'reconstruction':recons,'sigmoid_fit_diagnostics':o.fit_diagnostics,'conditioning':{'three_basis_xyz_matrix':float(np.linalg.cond(o.B)),'eight_basis_xyz_mapping':float(np.linalg.cond(o.lab.basis_xyz.T))},'strip_controls':controls,'strip_baselines':baseline,'physical_reproduction':reproduction,'signed_hdr':signed,'neutral_checks':neutral_checks,'timing':timings,'images':images,'matched_sweep_max_relative_rgb_error':max(matched),'matched_strip_controls_max_rgb_error':max(matched_controls),'decision':{'Density':'keep current production model','Strip':'keep current production model'},'artist_acceptance':'Not established by numerical difference. Visual review recorded separately; no validated missing artist behavior, no v2 fit justified.','stop':'Broad spectral development stopped. Future work requires a concrete artist-observed or numerical failure.'}
 (out/'completion.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
 print('COMPLETE',len(rows),'sweep rows; matched error',max(matched),'controls',max(matched_controls),flush=True)
 return report

if __name__=='__main__':run()
