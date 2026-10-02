"""Slow 1 nm emitted-radiance oracle; not an artist plugin or physical spectrum recovery.
The matched three-basis path isolates compact table error. Eight-basis NNLS and
Smits-shape paths measure reconstruction ambiguity, not a universal ground truth.
"""
from pathlib import Path
import json
import numpy as np
import colour
import _rendition as core
from .spectral_lab import Lab, Spectrum, Kind

HUES=np.array([29,110,145,195,265,325.])
WEIGHTS=np.array([[.02,1,1],[.02,.05,1],[1,.02,.8],[1,.05,.02],[1,.6,.02],[.1,1,.02]])

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def positive(x):return .5*(x+np.sqrt(x*x+(.001*np.linalg.norm(x))**2))
def hue_pair(h):
 h=h%360
 if h<29:h+=360
 points=np.r_[HUES,389.];i=np.searchsorted(points,h,side='right')-1
 return i%6,(i+1)%6,(h-points[i])/(points[i+1]-points[i])

class FullReference:
 def __init__(self):
  self.lab=Lab();w=self.lab.grid
  self.basis=np.array([np.exp(-.5*((w-c)/s)**2) for c,s in [(450,38),(545,42),(625,48)]]).T
  self.B=(self.basis.T@self.lab.emission_weights).T;self.inverse=np.linalg.inv(self.B)
 def attenuation(self,h,d,model):
  a,b,t=hue_pair(h)
  def material(i):return self.lab.pigment(WEIGHTS[i],d*d*1.5).values if model=='Density' else self.lab.dye(WEIGHTS[i],d*1.5,.1).values
  return (1-t)*material(a)+t*material(b)
 def reconstruct(self,xyz,method):
  if method=='compact_basis':
   coeff=positive(self.inverse@xyz);base=self.basis@coeff
   return base,xyz-base@self.lab.emission_weights,coeff
  rgb=xyz@self.lab.space.matrix_XYZ_to_RGB.T
  spectrum,residual,_=self.lab.reconstruct(rgb,'max',method)
  return spectrum.values,residual,None
 def process(self,rgb,effect,method='nnls_residual',amount=.75,leakage=.1,gamut=0):
  if effect not in ('Density','Strip'):raise ValueError('Only Density / Strip references')
  if not 0<=amount<=1 or not 0<=leakage<=1:raise ValueError('Reference amount/leakage outside physical domain')
  rgb=np.asarray(rgb,float)
  if rgb.shape[-1]!=3 or not np.isfinite(rgb).all():raise ValueError('Finite RGB required')
  M=np.array(core.matrix(gamut)).reshape(3,3)
  CAT=np.array(core.adaptation(.32168,.33767,.3127,.329,0)).reshape(3,3) if gamut==1 else np.eye(3)
  to=CAT@M;inverse=np.linalg.inv(to);result=[]
  for source in rgb.reshape(-1,3):
   xyz=to@source;q=colour.XYZ_to_Oklab(xyz);chroma=np.hypot(q[1],q[2]);relative=chroma/max(abs(q[0]),1e-12);h=np.degrees(np.arctan2(q[2],q[1]))%360
   base,residual,coeff=self.reconstruct(xyz,method)
   if effect=='Density':
    d=amount;attenuation=self.attenuation(h,d,effect)
    filtered=(base*attenuation)@self.lab.emission_weights+residual
    candidate=colour.XYZ_to_Oklab(filtered);c=np.hypot(candidate[1],candidate[2])
    if c>1e-12:candidate[1:]*=chroma/c # default production coupling=0
    candidate=colour.Oklab_to_XYZ(candidate)
    ev=(float(colour.models.log_encoding_ACEScct(xyz[1]))-float(colour.models.log_encoding_ACEScct(.18)))*17.52
    w=smooth(0,.03,relative)*(1-smooth(4,5,relative))*smooth(-30,-20,ev)*(1-smooth(20,30,ev))
    w*= (1-.5/(1+np.exp(-(ev-3)/2)))*(.5+.5/(1+np.exp((ev-2)/2)))
    out=xyz+w*(candidate-xyz)
   else:
    d=amount*.6;attenuation=self.attenuation(h,d,effect)
    if coeff is not None:
     separated=(1-leakage*amount)*coeff+leakage*amount*np.mean(coeff)
     active=self.basis@separated
    else:
     # Explicit alternative broad spectral records; positive memberships sum to 1.
     masks=self.basis/np.sum(self.basis,axis=1,keepdims=True)
     records=(base[:,None]*masks).T;energy=records@self.lab.emission_weights[:,1]
     target=(1-leakage*amount)*energy+leakage*amount*np.mean(energy)
     scales=np.divide(target,energy,out=np.ones_like(energy),where=energy>1e-30)
     active=(records*scales[:,None]).sum(axis=0)
    candidate=(active*attenuation)@self.lab.emission_weights+residual
    out=xyz+amount*smooth(0,.05,relative)*(candidate-xyz)
   result.append(inverse@out)
  return np.array(result).reshape(rgb.shape)

def run():
 out=Path('build/architecture-0.3');out.mkdir(parents=True,exist_ok=True);oracle=FullReference()
 colors={'skin':[.65,.3,.18],'cyan':[.01,.6,.8],'blue':[.01,.04,.9],'olive':[.2,.24,.06],'red':[.8,.02,.01],'ochre':[.65,.35,.03]}
 rows=[]
 # Family, chroma and radiometric scale sweeps including signed/HDR stimuli.
 for family,rgb in colors.items():
  for saturation in [0,.5,1,1.5]:
   neutral=np.dot(rgb,oracle.lab.space.matrix_RGB_to_XYZ[1]);color=neutral+(np.array(rgb)-neutral)*saturation
   for ev in [-8,0,8]:
    source=color*2.**ev
    for effect in ['Density','Strip']:
     e=3 if effect=='Density' else 6
     params={'interpretation':1,'density':.75} if effect=='Density' else {'interpretation':1,'separation':.75,'leakage':.1}
     compact=np.array(core.process(e,np.array([[*source,1]],np.float32),params))[0,:3]
     for method in ['compact_basis','nnls_residual','smits_residual']:
      reference=oracle.process(source,effect,method)
      rows.append({'family':family,'chroma':saturation,'exposure_stops':ev,'effect':effect,'reconstruction':method,'source':source.tolist(),'reference':reference.tolist(),'compact':compact.tolist(),'relative_rgb_error':float(np.max(np.abs(reference-compact))/max(np.max(np.abs(source)),1e-12))})
 signed=np.array([[-.2,.3,4],[0,0,0],[10000,2000,-50]],float);adapters=[]
 for method in ['compact_basis','nnls_residual','smits_residual']:
  for source in signed:
   xyz=oracle.lab.space.matrix_RGB_to_XYZ@source;b,r,_=oracle.reconstruct(xyz,method);b2,r2,_=oracle.reconstruct(xyz*2,method)
   adapters.append({'method':method,'source':source.tolist(),'identity_xyz_error':float(np.max(np.abs(b@oracle.lab.emission_weights+r-xyz))),'exposure_shape_error':float(np.max(np.abs(b2-2*b))),'residual_fraction':float(np.linalg.norm(r)/max(np.linalg.norm(xyz),1e-12))})
 matched=[r['relative_rgb_error'] for r in rows if r['reconstruction']=='compact_basis']
 report={'grid':'360–830 nm / 1 nm CIE 1931 2 degree','semantics':'Scene-radiance component attenuated by synthetic material transmittance/reflectance; explicit unchanged signed XYZ residual. No DRT, print appearance or spectrum recovery claim.','reconstruction_methods':['matched compact 3 basis smooth positive','8 basis NNLS residual','Smits spectral shape with signed residual'],'matched_compact_max_relative_error':max(matched),'matched_compact_rms_relative_error':float(np.sqrt(np.mean(np.square(matched)))),'alternative_interpretation':'Other reconstruction differences quantify underdetermination, not proof of production error','records':rows,'adapter_checks':adapters,'acceptance':'Numerical reference only; artist/material superiority remains pending'}
 (out/'full-spectral.json').write_text(json.dumps(report,indent=2)+'\n')
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 fig,axes=plt.subplots(1,2,figsize=(12,4))
 for ax,effect in zip(axes,['Density','Strip']):
  for method in ['compact_basis','nnls_residual','smits_residual']:
   samples=[r for r in rows if r['effect']==effect and r['reconstruction']==method];ax.plot([r['relative_rgb_error'] for r in samples],label=method)
  ax.set(title=effect+' / reference vs compact',xlabel='Family × chroma × exposure sample',ylabel='Max RGB error / source scale');ax.legend(fontsize=7)
 fig.tight_layout();fig.savefig(out/'full-spectral.png',dpi=140);plt.close(fig)
 print('Full reference matched relative error',max(matched));return report
if __name__=='__main__':run()
