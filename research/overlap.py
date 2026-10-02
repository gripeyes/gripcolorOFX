"""Compare the four original-source Volume composition strategies."""
import json
from pathlib import Path
import numpy as np
import _rendition as c

h=np.linspace(0,2*np.pi,721)
xyz=np.array([c.opponent([.6,.12*np.cos(t),.12*np.sin(t)],True) for t in h])
M=np.array(c.matrix(0)).reshape(3,3)
rgb=(xyz@np.linalg.inv(M).T).astype(np.float32)
x=np.c_[rgb,np.ones(len(rgb),np.float32)]
report={'schema_version':1,'stimulus':'Continuous Oklab hue circle; six simultaneous wide original-coordinate families','models':{}}
for mode,name in enumerate(['weighted deltas','normalized deltas','bounded vectors','shared field']):
    p={'interpretation':1,'overlap':mode}
    for i in range(6):
        p.update({f'v{i}_width':180,f'v{i}_hueDelta':[-20,15,25,-15,10,-25][i],f'v{i}_chroma':1.2,f'v{i}_neutral':0})
    result=c.process(2,x,p)
    permuted={k:v for k,v in p.items() if not k.startswith('v')}
    for i in range(6):
        for d in c.parameters(2):
            if d['id'].startswith(f'v{i}_'):
                key=d['id'];permuted['v'+str(5-i)+key[2:]]=p.get(key,d['default'])
    reordered=c.process(2,x,permuted)
    neutral=np.c_[np.repeat(np.geomspace(1e-5,1e3,100)[:,None],3,1),np.ones(100)].astype(np.float32)
    protected={**p,**{f'v{i}_neutral':.02 for i in range(6)}}
    n=c.process(2,neutral,protected)
    report['models'][name]={
        'nonfinite':int(np.count_nonzero(~np.isfinite(result))),
        'permutation_max_rgb_error':float(np.max(np.abs(result-reordered))),
        'hue_wrap_endpoint_error':float(np.max(np.abs(result[0]-result[-1]))),
        'maximum_adjacent_rgb_delta':float(np.max(np.abs(np.diff(result[:,:3],axis=0)))),
        'maximum_rgb_norm_growth':float(np.max(np.linalg.norm(result[:,:3],axis=1)/np.linalg.norm(x[:,:3],axis=1))),
        'protected_neutral_relative_error':float(np.max(np.abs(n[:,:3]-neutral[:,:3])/neutral[:,:3]))}
report['selection']={'candidate':'Normalized weighted Cartesian deltas',
    'equation':'q_out = q_source + sum_i w_i(q_source) [D_i(q_source)-q_source] / max(1,sum_active_i w_i(q_source)). Local RGB matrix deltas use the same normalization.',
    'reason':'Independent region intent, original-source selections, hue-wrap continuity and bounded aggregate influence. Inactive regions never dilute active ones.',
    'limitations':['Continuous with derivative kink at total weight 1; not a diffeomorphism guarantee.', 'Large individual deformations can still expand gamut or fold the mapping.', 'Artist overlap acceptance and wider parameter stress remain pending.']}
Path('research/output/volume-overlap.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
