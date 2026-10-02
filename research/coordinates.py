"""Compare published color models separately from signed/HDR production adapters."""
from pathlib import Path
import json, time, warnings
import colour
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path('research/output');OUT.mkdir(parents=True,exist_ok=True)
W=colour.xy_to_XYZ([.3127,.329])

def models():
    return {
      'IPT':(colour.XYZ_to_IPT,colour.IPT_to_XYZ),
      'Oklab':(colour.XYZ_to_Oklab,colour.Oklab_to_XYZ),
      'JzAzBz':(colour.XYZ_to_Jzazbz,colour.Jzazbz_to_XYZ),
      'CAM16-UCS':(lambda x:colour.XYZ_to_CAM16UCS(x),lambda x:colour.CAM16UCS_to_XYZ(x)),
      'Hellwig JMh':(lambda x: hellwig_forward(x), lambda x: hellwig_inverse(x)),
      'Simple XYZ opponent':(lambda x:np.stack([x[...,1],x[...,0]-x[...,1],x[...,2]-x[...,1]],-1),lambda x:np.stack([x[...,0]+x[...,1],x[...,0],x[...,0]+x[...,2]],-1))
    }
def hellwig_forward(x):
    q=colour.XYZ_to_Hellwig2022(x*100,W*100,64,20)
    return np.stack([q.J,q.M*np.cos(np.radians(q.h)),q.M*np.sin(np.radians(q.h))],-1)
def hellwig_inverse(x):
    q=colour.CAM_Specification_Hellwig2022(J=x[...,0],M=np.hypot(x[...,1],x[...,2]),h=np.degrees(np.arctan2(x[...,2],x[...,1]))%360)
    return colour.Hellwig2022_to_XYZ(q,W*100,64,20)/100

def run():
    rng=np.random.default_rng(18)
    rgb=rng.uniform(.001,1,(3000,3));space=colour.RGB_COLOURSPACES['ITU-R BT.2020'];xyz=rgb@space.matrix_RGB_to_XYZ.T
    report={};fig,axes=plt.subplots(2,3,figsize=(13,8))
    colors=np.array([[.8,.05,.02],[.02,.8,.1],[.02,.1,.8],[.01,.4,.5],[.5,.02,.4],[.8,.35,.01]])
    for (name,(f,inv)),ax in zip(models().items(),axes.flat):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');start=time.perf_counter();q=f(xyz);back=inv(q);elapsed=time.perf_counter()-start
            error=np.max(np.abs(back-xyz));hue_ranges=[]
            for rgb0 in colors:
                xs=(rgb0[None,:]*2**np.linspace(-8,8,100)[:,None])@space.matrix_RGB_to_XYZ.T
                coords=f(xs);angles=np.unwrap(np.arctan2(coords[:,2],coords[:,1]));hue_ranges.append(float(np.degrees(np.ptp(angles))))
                ax.plot(coords[:,1],coords[:,2])
            ax.set(title=name,xlabel='Opponent a (model units)',ylabel='Opponent b (model units)')
            report[name]={'roundtrip_max_xyz_error':float(error),'nonfinite':int(np.count_nonzero(~np.isfinite(back))),'seconds_3000_forward_inverse':elapsed,'exposure_hue_drift_degrees':hue_ranges,'native_negative_claim':False}
    fig.tight_layout();fig.savefig(OUT/'coordinates.png',dpi=150);plt.close(fig)
    # Algebraic Oklab cbrt extension is our adapter, not a perceptual assertion.
    signed=rng.normal(size=(3000,3))*np.exp2(rng.uniform(-10,10,(3000,1)))
    signedxyz=signed@space.matrix_RGB_to_XYZ.T
    back=colour.Oklab_to_XYZ(colour.XYZ_to_Oklab(signedxyz))
    report['adapter_selection']={'candidate':'Oklab real-cube-root algebraic signed extension','max_scaled_roundtrip_error':float(np.max(np.abs(back-signedxyz)/(1+np.max(np.abs(signedxyz),axis=1)[:,None]))),'rationale':'Reversible unbounded algebra, D65 colorimetric basis, exposure hue stability, no viewing-condition parameters; perceptual meaning is restricted to valid positive stimuli. Other models remain viable with positive-base residual adapters.','status':'research candidate; perceptual and artist acceptance pending'}
    (OUT/'coordinates.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':run()
