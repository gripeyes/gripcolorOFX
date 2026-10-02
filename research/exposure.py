"""Characterize exposure response for every node and selectable look-domain mode.
Errors characterize intended conditioned operators; they do not force equivariance.
"""
from pathlib import Path
import json
import numpy as np
import _rendition as c

CASES=[(0,{'exposure':.7}),(0,{'rPower':1.2}),(1,{'contrast':1.15,'toe':.2,'shoulder':.2}),
 (2,{'v0_width':360,'v0_hueDelta':10}),(3,{'density':.4}),
 (4,{'width':360,'darkHue':-10,'brightHue':15}),
 (5,{'rg':.08}),(6,{'separation':.6,'palette':.3}),(7,{'mode':0}),(7,{'mode':9})]
for domain in range(6):
    CASES.extend([(0,{'rPower':1.05,'cdlDomain':1,'lookDomain':domain}),
                  (1,{'contrast':1.1,'lookDomain':domain}),
                  (4,{'mode':1,'darkr':.15,'brightb':-.1,'lookDomain':domain}),
                  (5,{'domain':1,'rg':.03,'lookDomain':domain})])
colors=np.array([[.12,.24,.5],[.3,.15,.04],[.18,.18,.18],[-.03,.12,.5],[0,0,0]],np.float32)
report={'schema_version':1,'stops':list(range(-10,11,2)),'configurations':[]}
for effect,params in CASES:
    # Positive-only domains receive positive stimuli; unsupported signed cases are tested separately.
    x=colors[:3] if params.get('lookDomain') in (0,4) else colors
    rgba=np.c_[x,np.ones(len(x),np.float32)]
    p={'interpretation':1,**params};base=c.process(effect,rgba,p)
    sweeps=[]
    for stop in range(-10,11,2):
        k=np.float32(2.**stop);exposed=rgba.copy();exposed[:,:3]*=k
        result=c.process(effect,exposed,p);expected=base[:,:3]*k
        relative=np.max(np.abs(result[:,:3]-expected),axis=1)/np.maximum(np.max(np.abs(expected),axis=1),1e-8)
        sweeps.append({'stops':stop,'max_relative_equivariance_error':float(relative.max()),'nonfinite':int(np.count_nonzero(~np.isfinite(result)))})
    report['configurations'].append({'effect':effect,'parameters':params,'metadata':c.semantics(effect,params),'sweeps':sweeps})
Path('research/output/exposure-sweeps.json').write_text(json.dumps(report,indent=2)+'\n')
print('Recorded',len(CASES),'exposure configurations')
