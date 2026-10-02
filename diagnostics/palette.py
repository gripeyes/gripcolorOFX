"""M6 palette distance/transport assistance; no transform application API."""
import numpy as np
from scipy.special import logsumexp
from scipy.stats import wasserstein_distance
from .common import labs,fromlabs,finite_summary

def compact_palette(rgb,k=12,max_samples=6000,seed=6):
    q=labs(np.asarray(rgb).reshape(-1,3));rng=np.random.default_rng(seed)
    if len(q)>max_samples:q=q[rng.choice(len(q),max_samples,replace=False)]
    centers=[q[np.argmin(np.sum((q-np.median(q,axis=0))**2,axis=1))]]
    while len(centers)<min(k,len(q)):
        distance=np.min(np.sum((q[:,None]-np.array(centers)[None])**2,axis=-1),axis=1)
        if distance.max()<1e-14:break
        centers.append(q[distance.argmax()])
    centers=np.array(centers)
    for _ in range(25):
        assignment=np.argmin(np.sum((q[:,None]-centers[None])**2,axis=-1),axis=1)
        updated=centers.copy()
        for i in range(len(centers)):
            if np.any(assignment==i):updated[i]=q[assignment==i].mean(axis=0)
        if np.max(np.abs(updated-centers))<1e-8:break
        centers=updated
    assignment=np.argmin(np.sum((q[:,None]-centers[None])**2,axis=-1),axis=1)
    mass=np.bincount(assignment,minlength=len(centers)).astype(float);good=mass>0
    return centers[good],mass[good]/mass.sum()

def sinkhorn(source,mass_source,target,mass_target,epsilon=.01,tolerance=1e-9,max_iterations=12000):
    """Balanced entropic OT in explicit Euclidean coordinate units, stable log solver."""
    a=np.asarray(mass_source,float);b=np.asarray(mass_target,float)
    if epsilon<=0 or np.any(a<=0) or np.any(b<=0) or not np.isclose(a.sum(),1) or not np.isclose(b.sum(),1):raise ValueError('Positive normalized masses and epsilon required')
    cost=np.sum((np.asarray(source)[:,None]-np.asarray(target)[None])**2,axis=-1)
    logk=-cost/epsilon;u=np.zeros_like(a);v=np.zeros_like(b)
    for iteration in range(max_iterations):
        u=np.log(a)-logsumexp(logk+v[None,:],axis=1)
        v=np.log(b)-logsumexp(logk+u[:,None],axis=0)
        if iteration%10==0:
            plan=np.exp(logk+u[:,None]+v[None,:]);error=max(np.max(np.abs(plan.sum(1)-a)),np.max(np.abs(plan.sum(0)-b)))
            if error<tolerance:break
    plan=np.exp(logk+u[:,None]+v[None,:]);error=max(np.max(np.abs(plan.sum(1)-a)),np.max(np.abs(plan.sum(0)-b)))
    return {'plan':plan,'cost':cost,'transport_cost':float(np.sum(plan*cost)),'epsilon':epsilon,'marginal_max_error':float(error),'iterations':iteration+1,'converged':bool(error<tolerance)}

def sliced_distance(a,b,directions=64,max_samples=4096,seed=606):
    a=labs(np.asarray(a).reshape(-1,3));b=labs(np.asarray(b).reshape(-1,3));rng=np.random.default_rng(seed)
    if len(a)>max_samples:a=a[np.random.default_rng(seed).choice(len(a),max_samples,replace=False)]
    if len(b)>max_samples:b=b[np.random.default_rng(seed).choice(len(b),max_samples,replace=False)]
    axes=rng.normal(size=(directions,3));axes/=np.linalg.norm(axes,axis=1)[:,None]
    distances=[wasserstein_distance(a@axis,b@axis) for axis in axes]
    return {'mean_sliced_W1':float(np.mean(distances)),'projection_distances':finite_summary(distances),'directions':directions,'seed':seed,'metric':'Euclidean signed-algebraic Oklab coordinates; not a guaranteed perceptual metric for arbitrary signed/HDR scene RGB'}

def analyze(source,target,k=12):
    a,wa=compact_palette(source,k);b,wb=compact_palette(target,k)
    cost=np.sum((a[:,None]-b[None])**2,axis=-1);epsilon=max(float(np.median(cost))*.03,1e-5)
    transport=sinkhorn(a,wa,b,wb,epsilon)
    return a,wa,b,wb,transport,sliced_distance(source,target)
