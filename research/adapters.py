"""Reproducible full-pipeline signed/HDR adapter comparisons.
Adapters are ours. None extends a published model's perceptual validity claim.
The chromatic probe is a small opponent rotation, not an accepted production look.
"""
from pathlib import Path
import json,warnings
import numpy as np
import colour
from coordinates import models
from spectral_lab import Lab

OUT=Path('research/output');OUT.mkdir(parents=True,exist_ok=True)
M=colour.RGB_COLOURSPACES['ITU-R BT.2020'].matrix_RGB_to_XYZ
I=np.linalg.inv(M)

def stats(a,b):
    scale=np.maximum(np.max(np.abs(b),axis=-1),1e-10)
    err=np.max(np.abs(a-b),axis=-1)/scale
    return {'nonfinite':int(np.count_nonzero(~np.isfinite(a))),
            'max_relative_error':float(np.max(err)) if np.all(np.isfinite(err)) else None}

def coordinate_pipeline(rgb,forward,inverse,adapter,angle=.08):
    scale=np.max(np.abs(rgb),axis=-1,keepdims=True)
    shape=rgb/np.maximum(scale,1e-30)
    positive=.5*(shape+np.sqrt(shape*shape+.02**2))
    xyz=rgb@M.T
    def probe(base):
        q=forward(base@M.T)
        c=np.cos(angle);s=np.sin(angle);p=q.copy()
        p[...,1]=c*q[...,1]-s*q[...,2];p[...,2]=s*q[...,1]+c*q[...,2]
        return inverse(p)-base@M.T
    if adapter=='positive-negative decomposition':
        negative=.5*(-shape+np.sqrt(shape*shape+.02**2))
        delta=probe(positive)-probe(negative)
    else:
        delta=probe(positive)
    if adapter in ('smooth participation','smooth bypass'):
        ratio=np.maximum(-np.min(shape,axis=-1,keepdims=True),0)
        participation=np.exp(-(ratio/(.25 if adapter=='smooth participation' else .04))**2)
        delta*=participation
    if adapter=='bounded chromatic reconstruction':
        magnitude=np.linalg.norm(delta,axis=-1,keepdims=True)
        delta*=.15/np.sqrt(.15**2+magnitude*magnitude)
    return (xyz+scale*delta)@I.T

def run():
    rng=np.random.default_rng(117)
    samples=np.r_[rng.normal(size=(128,3))*np.exp2(rng.uniform(-12,12,(128,1))),
                  [[0,0,0],[.18,.18,.18],[1,-1,0],[1e5,2e4,-100]]]
    crossing=np.c_[np.linspace(-.04,.04,401),np.full(401,.2),np.full(401,.6)]
    report={'schema_version':1,'seed':117,'probe':'0.08 rad opponent rotation at fixed first coordinate',
            'warning':'Comparative synthetic probes only; view-condition models retain appearance semantics. No new signed extension is attributed to published models.', 'coordinate_pipelines':{}}
    adapters=['positive base + residual','positive-negative decomposition','smooth participation','smooth bypass','bounded chromatic reconstruction']
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for name,(f,inv) in models().items():
            for adapter in adapters:
                try:
                    result=coordinate_pipeline(samples,f,inv,adapter)
                    twice=coordinate_pipeline(samples*2,f,inv,adapter)
                    identity=coordinate_pipeline(samples,f,inv,adapter,0)
                    seam=coordinate_pipeline(crossing,f,inv,adapter)
                    adjacent=np.max(np.abs(np.diff(seam,axis=0)),axis=1)
                    report['coordinate_pipelines'][name+'/'+adapter]={
                        'identity':stats(identity,samples),'exposure_doubling':stats(twice,result*2),
                        'active_nonfinite':int(np.count_nonzero(~np.isfinite(result))),
                        'negative_boundary_max_adjacent_delta':float(np.max(adjacent)),
                        'adjacent_input_step':.0002,
                        'maximum_output_growth':float(np.max(np.linalg.norm(result,axis=1)/np.maximum(np.linalg.norm(samples,axis=1),1e-10)))}
                except (ValueError,FloatingPointError) as error:
                    report['coordinate_pipelines'][name+'/'+adapter]={'failed':str(error)}
    f,inv=models()['Oklab'];xyz=samples@M.T
    q=f(xyz);identity=inv(q)@I.T
    report['our_signed_oklab_algebra']={'identity':stats(identity,samples),'scope':'Real cube-root algebra; perceptual interpretation only in valid stimulus domain.'}
    report['selection']={'initial_candidate':'Signed Oklab algebra',
                        'reason':'Exact algebraic reconstruction, scale-homogeneous coordinates, no viewing-condition state and inexpensive reversible matrices. Residual adapters keep other published models viable.',
                        'limitations':'Synthetic boundary/growth tests cannot establish artist usefulness. Positive/negative decomposition is an original comparison adapter, not a physical or perceptual claim. Wider gamut and real-image adapter tests remain.'}
    (OUT/'coordinate-adapters.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    lab=Lab();rgb_samples=samples[:40];spectral={}
    for reconstruction in ['nnls_residual','smits_residual']:
        for scale_method in ['max','norm','luminance']:
            for adapter in ['residual','signed auxiliary','smooth participation','smooth bypass']:
                def evaluate(rgb):
                    base,residual,_=lab.reconstruct(rgb,scale_method,reconstruction)
                    attenuation=lab.dye([.8,.2,.5],.3,.1).values
                    delta=(base.values*(attenuation-1))@lab.emission_weights
                    if adapter.startswith('smooth'):
                        scale=max(np.max(np.abs(rgb)),1e-30)
                        ratio=max(-np.min(rgb/scale),0)
                        delta*=np.exp(-(ratio/(.25 if adapter=='smooth participation' else .04))**2)
                    # Signed auxiliary uses separate storage but identical equations to residual.
                    return (lab.xyz(base)+residual+delta)@I.T
                result=np.array([evaluate(x) for x in rgb_samples])
                twice=np.array([evaluate(2*x) for x in rgb_samples])
                seam=np.array([evaluate(x) for x in crossing[::10]])
                spectral[reconstruction+'/'+scale_method+'/'+adapter]={
                    'active_nonfinite':int(np.count_nonzero(~np.isfinite(result))),
                    'exposure_doubling':stats(twice,2*result),
                    'near_negative_boundary_adjacent_delta':float(np.max(np.abs(np.diff(seam,axis=0)))),
                    'adjacent_input_step':.002}
    spectral_report={'schema_version':1,'strategies':spectral,
                     'semantics':'Attenuation of positive scene-radiance component plus retained signed information; material appearance oracle is separate.',
                     'selected_runtime_candidate':'Smooth positive three-basis coefficients + signed XYZ residual, native homogeneous coefficient-norm shape/scale decomposition.',
                     'reason':'No hard RGB clamp or residual loss; scale-separated continuous algebra shared with Metal. NNLS and Smits are oracle comparisons, not runtime requirements.',
                     'auxiliary_equivalence':'Parallel signed XYZ storage and residual restoration are algebraically identical in this experiment.',
                     'limits':['Luminance scaling must handle signed cancellation explicitly.', 'Smooth bypass can suppress useful looks on signed edges.', 'Residual dominance can attenuate chromatic influence for extreme colors.', 'Real compositing/visual acceptance and reconstruction-native methods remain pending.']}
    (OUT/'spectral-signed-hdr.json').write_text(json.dumps(spectral_report,indent=2,allow_nan=False)+'\n')
    print('Wrote coordinate-adapters.json and spectral-signed-hdr.json')
if __name__=='__main__':run()
