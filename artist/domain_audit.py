from pathlib import Path
import json,numpy as np
import _rendition as c

def run():
 rows=[]
 x=np.geomspace(1e-7,2**16,250).astype('f4')
 for d,name in enumerate(['Pure stops','ACEScct','LogC4','DaVinci Intermediate','AgX unclamped stops','LookLog candidate']):
  values=x if d in [0,4] else np.r_[-x[::-1],0,x]
  encoded=np.array([c.encode(float(v),d) for v in values]);back=np.array([c.decode(float(v),d) for v in encoded]);error=abs(back-values)
  h=1e-4;derivative=(c.encode(.18+h,d)-c.encode(.18-h,d))/(2*h)
  responses=[]
  for e,p in [(1,{'contrast':1.3}),(5,{'domain':1,'rg':.1}),(4,{'mode':1,'darkr':.2,'midr':.1,'brightr':-.1}),(0,{'cdlDomain':1,'rOffset':.1})]:
   rgb=np.array([[.02,.3,4,.37],[.18,.18,.18,.37],[1e-6,.002,100,.37]],np.float32)
   try:
    y=c.process(e,rgb,{'interpretation':1,'lookDomain':d,**p});responses.append({'effect':e,'finite':bool(np.isfinite(y).all()),'values':y.tolist()})
   except Exception as ex:responses.append({'effect':e,'error':str(ex)})
  # Measure each existing toe junction without changing historical equations.
  a=(262144.-16.)/117.45; b=928./1023.; cc=95./1023.
  logc_cut=(2**(14*(-cc/b)+6)-64)/a
  junction={1:.0078125,2:logc_cut,3:.00262409,5:.18/64}.get(d)
  continuity=None
  if junction is not None:
   step=max(abs(junction)*.01,1e-6)
   f=c.encode(junction,d); left=(f-c.encode(junction-step,d))/step;right=(c.encode(junction+step,d)-f)/step
   continuity={'junction':junction,'finite':bool(np.isfinite([f,left,right]).all()),'left_secant':left,'right_secant':right,'relative_slope_gap':abs(left-right)/max(abs(left),abs(right),1e-8),'step':step,'note':'Float32 secants across a finite interval; not symbolic proof of derivative continuity'}
  sensitivity=[]
  for e,key,center in [(1,'contrast',1.2),(5,'rg',.1),(4,'midr',.1),(0,'rOffset',.01)]:
   p={'interpretation':1,'lookDomain':d,**({5:{'domain':1},4:{'mode':1},0:{'cdlDomain':1}}.get(e,{}))}
   rgb=np.array([[.01,.18,4,.37],[.18,.18,.18,.37]],np.float32)
   lo=c.process(e,rgb,{**p,key:center-1e-3});hi=c.process(e,rgb,{**p,key:center+1e-3})
   sensitivity.append({'effect':e,'parameter':key,'center':center,'delta':.001,'finite':bool(np.isfinite(lo).all() and np.isfinite(hi).all()),'max_rgb_derivative':float(np.max(abs(hi[:,:3]-lo[:,:3]))/.002)})
  rows.append({'toe_continuity':continuity,'parameter_sensitivity':sensitivity,'domain':d,'name':name,'roundtrip_max_error':float(max(error)),'roundtrip_tolerance_pass':bool(np.all(error<=2e-6+2e-5*abs(values))),'middle_gray_encoded':c.encode(.18,d),'gray_derivative':derivative,'negative_support':'explicitly unsupported' if d in [0,4] else 'documented native toe / extension','operator_responses':responses,'status':'retained with documented domain; no silent alias'})
 out=Path('build/control-audit-0.31');(out/'domains.json').write_text(json.dumps(rows,indent=2)+'\n');print('Domain audit',len(rows))
if __name__=='__main__':run()
