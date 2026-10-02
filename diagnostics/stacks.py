"""Aggressive settings and operator order: record failures, never repair pixels."""
import itertools,numpy as np
from .common import *
from .volume import CASES as VOLUME_CASES
from .range_tests import CASES

def run():
    rgb,ev,hue,chroma,shape=structured();rgb=rgb[::7]
    rgb=np.concatenate([rgb,np.array([[0,0,0],[-.1,.2,4],[1e-8,-1e-8,0]]),np.repeat(np.exp2(np.linspace(-12,12,33))[:,None]*.18,3,axis=1)])
    alpha=np.linspace(0,1,len(rgb)).astype(np.float32);rgba=np.concatenate([rgb,alpha[:,None]],axis=1).astype(np.float32)
    params={'Scene':{'exposure':3,'rExposure':1,'gExposure':-1,'temperature':18000,'tint':.015,'rOffset':.02,'rPower':1.8},'Tone':{'contrast':1.9,'toe':.8,'shoulder':.8,'shadowDensity':.7,'highlightDensity':-.4},'Volume':VOLUME_CASES['aggressive_overlap'],'Density':CASES['Density'][0][1],'Crossover':CASES['Crossover'][0][1],'Crosstalk':{'mode':0,'m01':.8,'m02':-.4,'m10':-.5,'m20':.2},'Strip':CASES['Strip'][2][1],'Inspector':{'mode':12}}
    report={'stimuli':len(rgb),'policy':'Float signed/HDR samples, alpha bit checks, numerical exceptions retained as failures; no clipping or pixel repair. Reversal/order effects are diagnostics, not automatically bugs.','individual':[],'orders':[]}
    for name,p in params.items():
        try:
            out=core.process(NAMES.index(name),rgba,{'interpretation':1,**p})
            row={'effect':name,'parameters':p,'finite':bool(np.isfinite(out).all()),'alpha_bit_exact':bool(np.array_equal(out[:,3].view(np.uint32),rgba[:,3].view(np.uint32))),'max_abs_rgb':float(np.max(np.abs(out[:,:3]))),'semantics':core.semantics(NAMES.index(name),p)}
        except Exception as error:row={'effect':name,'parameters':p,'finite':False,'error':str(error)}
        report['individual'].append(row)
    baseline=None
    for order in itertools.permutations(['Density','Crossover','Strip']):
        try:
            out=core.process(0,rgba,{'interpretation':1,'exposure':1})
            out=core.process(2,out,{'interpretation':1,**VOLUME_CASES['artist_overlap']})
            for name in order:out=core.process(NAMES.index(name),out,{'interpretation':1,**params[name]})
            if baseline is None:baseline=out.copy()
            neutral=out[-33:,:3]
            row={'order':['Scene','Volume',*order],'finite':bool(np.isfinite(out).all()),'alpha_bit_exact':bool(np.array_equal(out[:,3].view(np.uint32),rgba[:,3].view(np.uint32))),'max_abs_rgb':float(np.max(np.abs(out[:,:3]))),'source_scaled_order_difference_rms':float(np.sqrt(np.mean(((out[:,:3]-baseline[:,:3])/np.maximum(np.max(np.abs(rgba[:,:3]),axis=1),.001)[:,None])**2))),'neutral_axis_max_channel_spread':float(np.max(np.ptp(neutral,axis=1))),'neutral_magnitude_change_max':float(np.max(np.abs(np.mean(neutral,axis=1)-rgba[-33:,0])))}
        except Exception as error:row={'order':list(order),'finite':False,'error':str(error)}
        report['orders'].append(row)
    save('aggressive-stacks',report);return report
if __name__=='__main__':run()
