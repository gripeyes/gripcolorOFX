from pathlib import Path
import json
import numpy as np
import colour
import _rendition as core
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/validation-0.2'
SPACE=colour.RGB_COLOURSPACES['ITU-R BT.2020']
M=SPACE.matrix_RGB_to_XYZ; INV=SPACE.matrix_XYZ_to_RGB; Y=M[1]
NAMES=['Scene','Tone','Volume','Density','Crossover','Crosstalk','Strip','Inspector','Primaries','Base','Palette','Material']
def process(name,rgb,parameters=None):
    rgb=np.asarray(rgb,np.float32)
    a=np.concatenate([rgb,np.ones(rgb.shape[:-1]+(1,),np.float32)],axis=-1)
    return core.process(NAMES.index(name),a,{'interpretation':1,**(parameters or {})})[...,:3]
def labs(rgb):return colour.XYZ_to_Oklab(np.asarray(rgb)@M.T)
def fromlabs(q):return colour.Oklab_to_XYZ(q)@INV.T
def save(name,report):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/(name+'.json')).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
def structured():
    ev=np.arange(-12,13,2,dtype=float);hue=np.arange(0,360,5,dtype=float);chroma=np.array([0,.01,.03,.1,.25,.5,.75])
    e,c,h=np.meshgrid(ev,chroma,hue,indexing='ij');L=.6*np.exp2(e/3)
    q=np.stack([L,c*L*np.cos(np.radians(h)),c*L*np.sin(np.radians(h))],-1)
    rgb=fromlabs(q).reshape(-1,3).astype(np.float32)
    return rgb,e.ravel(),h.ravel(),c.ravel(),(len(ev),len(chroma),len(hue))
def finite_summary(values):
    x=np.asarray(values);finite=x[np.isfinite(x)]
    return {'finite':int(finite.size),'nonfinite':int(x.size-finite.size),'min':float(finite.min()) if finite.size else None,'p50':float(np.median(finite)) if finite.size else None,'p95':float(np.quantile(finite,.95)) if finite.size else None,'max':float(finite.max()) if finite.size else None}
