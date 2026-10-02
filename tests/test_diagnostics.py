import numpy as np
import _rendition as core

def test_identity_and_known_exposure_differentials():
    rgb=np.array([[.18,.18,.18],[-.1,.3,4],[1e-5,0,-2e-5]],np.float32)
    d=core.differentials(2,rgb,{'interpretation':1})
    assert np.array_equal(d[:,:9],np.tile(np.eye(3).ravel(),(3,1)))
    assert np.all(d[:,9:14]==1) and np.all(d[:,14]==0) and np.all(d[:,15]==1)
    d=core.differentials(0,rgb,{'interpretation':1,'exposure':2})
    assert np.allclose(d[:,:9],np.tile((np.eye(3)*4).ravel(),(3,1)),atol=2e-4)
    assert np.allclose(d[:,9],64,rtol=1e-4)

def test_volume_svd_matches_independent_numpy():
    rng=np.random.default_rng(4);rgb=rng.uniform(.01,2,(150,3)).astype(np.float32)
    d=core.differentials(2,rgb,{'interpretation':1,'v0_width':240,'v0_hueDelta':120,'v0_chroma':3,'v5_width':240,'v5_hueDelta':-100})
    j=d[:,:9].reshape(-1,3,3)
    assert np.allclose(d[:,10:13],np.linalg.svd(j,compute_uv=False),atol=1e-7,rtol=1e-6)
    assert np.allclose(d[:,9],np.linalg.det(j),atol=1e-9,rtol=1e-9)

def test_inspector_geometry_modes_alpha_and_identity_default():
    a=np.array([[.2,.03,.02,0],[.02,.05,3,.3]],np.float32)
    for mode in range(11,16):
        out=core.process(7,a,{'interpretation':1,'mode':mode})
        assert np.isfinite(out).all() and np.array_equal(out[:,3],a[:,3])
    assert np.array_equal(core.process(7,a,{'interpretation':1}).view(np.uint32),a.view(np.uint32))

def test_transport_marginals_and_known_translation():
    from diagnostics.palette import sinkhorn
    a=np.array([[0.,0.,0.],[1.,0.,0.]]);mass=np.array([.5,.5])
    q=sinkhorn(a,mass,a+np.array([0,2,0]),mass,.02)
    assert q['converged'] and q['marginal_max_error']<1e-9
    assert np.isclose(q['transport_cost'],4,atol=1e-8)

def test_soft_membership_partition_and_signed_reconstruction():
    from diagnostics.bridge import build,memberships
    rgb=np.array([[[-.02,.1,4],[.18,.18,.18]],[[0,0,0],[3,-.4,.2]]])
    report,data=build(rgb,k=3)
    assert report['partition_max_error']<1e-12 and report['reconstruction_max_rgb_error']<1e-12
    assert np.all(data['weights']>=0)
    centers=data['centers_opponent'];q=np.array([[.5,.1,.02]])
    a=memberships(q,centers);b=memberships(q+1e-7,centers)
    assert np.max(np.abs(a-b))<1e-4

def test_structure_identity_gain_and_reversal():
    from diagnostics.structure import analyze
    x=np.linspace(.01,1,25).reshape(5,5);rgb=np.repeat(x[...,None],3,axis=-1)
    r,_=analyze(rgb,rgb);assert r['gradient_reversal_pixels']==0 and r['lost_edge_pixels']==0
    r,_=analyze(rgb,2*rgb);assert np.isclose(r['luminance_gradient_ratio']['p50'],2)
    r,_=analyze(rgb,-rgb);assert r['gradient_reversal_pixels']==r['edge_pixels']

def test_hk_equal_luminance_colour_and_neutral_control():
    from diagnostics.hk import appearance
    from diagnostics.common import Y
    rgb=np.array([[.18,.18,.18],[.03,.06,.9]])
    rgb*=.18/(rgb@Y)[:,None];q=appearance(rgb)
    assert np.ptp(rgb@Y)<1e-12
    assert np.all(np.isfinite(q.Q_HK)) and q.J_HK[1]>q.J[1]
    # Published model's neutral is not exactly C=0 numerically; do not promise zero HK correction.
    assert q.J_HK[0]-q.J[0]<q.J_HK[1]-q.J[1]


def test_sliced_distribution_self_distance_has_no_sampling_noise():
    from diagnostics.palette import sliced_distance
    rgb=np.random.default_rng(7).uniform(0,4,(4200,3))
    assert sliced_distance(rgb,rgb)['mean_sliced_W1']==0
