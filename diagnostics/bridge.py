"""M8/M10 experimental guide fields for future Pigment; pointwise membership only."""
import numpy as np
from scipy.special import logsumexp
from .common import labs,fromlabs
from .palette import compact_palette

def memberships(coordinates,centers,sigma=.15):
    if sigma<=0 or not np.isfinite(sigma):raise ValueError('Positive finite membership width required')
    q=np.asarray(coordinates,float);centers=np.asarray(centers,float)
    if not np.isfinite(q).all() or not np.isfinite(centers).all() or len(centers)==0:raise ValueError('Finite coordinates and nonempty palette required')
    logw=-np.sum((q[...,None,:]-centers)**2,axis=-1)/(2*sigma*sigma)
    return np.exp(logw-logsumexp(logw,axis=-1,keepdims=True))

def build(rgb,k=8,sigma=.15,centers=None):
    """Return soft guide layers and signed residual; never edit the source."""
    rgb=np.asarray(rgb,float)
    centers=compact_palette(rgb,k)[0] if centers is None else np.asarray(centers,float)
    weights=memberships(labs(rgb),centers,sigma);palette_rgb=fromlabs(centers)
    base=weights@palette_rgb;residual=rgb-base;reconstruction=base+residual
    report={'schema_version':1,'status':'Experimental offline Rendition/Pigment bridge; not a production node or spatial filter','coordinates':'Absolute signed Oklab extension, D65, explicit Linear Rec.2020; outside valid positive domain these are algebraic coordinates only','membership':'Gaussian softmax distance, row-normalized partition of unity; sigma in Oklab coordinate units','reference_semantics':'Scene-compatible signed RGB reconstruction; palette layers are guide fields, not physical reflectances/colorants','exposure_behavior':'Exposure-conditioned absolute-coordinate memberships; frozen palette required for comparative/temporal tests','invertibility':'Original RGB recovered with parallel signed residual; membership weights alone are non-invertible','spatial_processing':'None; a future Pigment consumer owns spatial operations and alpha/compositing policy','sigma':sigma,'layers':len(centers),'partition_max_error':float(np.max(np.abs(weights.sum(-1)-1))),'reconstruction_max_rgb_error':float(np.max(np.abs(reconstruction-rgb))),'signed_residual_range':[float(residual.min()),float(residual.max())],'temporal_policy':'Do not refit palette independently each frame; freeze/version centers and record motion/lighting limitations'}
    return report,{'weights':weights,'centers_opponent':centers,'palette_rgb':palette_rgb,'signed_residual':residual}
