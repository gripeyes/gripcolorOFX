"""M7: compare spatial derivatives; never process or filter output imagery."""
import numpy as np
from .common import Y,labs,finite_summary

def gradients(x):
    # Forward differences share shape H-1 x W-1 and exclude padded image borders.
    return np.stack([x[:-1,1:]-x[:-1,:-1],x[1:,:-1]-x[:-1,:-1]],axis=-1)

def analyze(source,result,relative_edge_threshold=1e-4):
    source=np.asarray(source,float);result=np.asarray(result,float)
    if source.shape!=result.shape or source.ndim!=3 or source.shape[-1]!=3 or min(source.shape[:2])<2:raise ValueError('Matching HxWx3 images, at least 2x2, required')
    if not np.isfinite(source).all() or not np.isfinite(result).all():raise ValueError('Finite linear RGB required')
    a=gradients(source@Y);b=gradients(result@Y);mag=np.linalg.norm(a,axis=-1);outmag=np.linalg.norm(b,axis=-1)
    threshold=max(float(np.max(mag))*relative_edge_threshold,1e-12);mask=mag>threshold
    ratio=np.divide(outmag,mag,out=np.zeros_like(mag),where=mask)
    dot=np.sum(a*b,axis=-1);cos=np.divide(dot,mag*outmag,out=np.zeros_like(mag),where=mask&(outmag>1e-12));cos=np.clip(cos,-1,1)
    sign=(dot<0)&mask;lost=(outmag<threshold)&mask
    chroma_a=gradients(labs(source)[...,1:]);chroma_b=gradients(labs(result)[...,1:])
    # Combined opponent/spatial direction in four dimensions; not a hue-angle metric.
    ca=chroma_a.reshape(*mag.shape,4);cb=chroma_b.reshape(*mag.shape,4);ma=np.linalg.norm(ca,axis=-1);mb=np.linalg.norm(cb,axis=-1)
    cmask=ma>max(float(ma.max())*relative_edge_threshold,1e-12)
    ccos=np.divide(np.sum(ca*cb,axis=-1),ma*mb,out=np.zeros_like(ma),where=cmask&(mb>1e-12));ccos=np.clip(ccos,-1,1)
    report={'definition':'Forward spatial differences, linear Rec.2020 luminance and signed Oklab opponent edges; no spatial processing. Contrast ratio uses gradient magnitude, not a perceptual local-contrast model.','source_shape':list(source.shape),'edge_threshold':threshold,'edge_pixels':int(mask.sum()),'luminance_gradient_ratio':finite_summary(ratio[mask]),'luminance_direction_cosine':finite_summary(cos[mask]),'gradient_reversal_pixels':int(sign.sum()),'lost_edge_pixels':int(lost.sum()),'chromatic_direction_cosine':finite_summary(ccos[cmask]),'flat_source_pixels':int((~mask).sum()),'new_edge_pixels':int(((~mask)&(outmag>threshold)).sum())}
    maps={'gradient_ratio':ratio,'luminance_direction':cos,'reversal':sign,'lost_edge':lost,'chromatic_direction':ccos,'valid_edges':mask,'valid_chromatic_edges':cmask}
    return report,maps
