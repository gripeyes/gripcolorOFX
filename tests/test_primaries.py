import numpy as np
import pytest
import _rendition as c

def run(rgb,params=None,gamut=1):
    rgb=np.asarray(rgb,np.float32)
    if rgb.shape[-1]==3:rgb=np.concatenate([rgb,np.full(rgb.shape[:-1]+(1,),.37,np.float32)],-1)
    return c.process(8,rgb,{'interpretation':gamut,**(params or {})})

M=np.array(c.matrix(0)).reshape(3,3)
def test_exact_default_identity_and_inactive_range_controls():
    a=np.array([[np.nan,np.inf,-np.inf,0],[-.1,4,.2,.4],[0,0,0,0]],np.float32)
    assert np.array_equal(run(a).view('u4'),a.view('u4'))
    assert np.array_equal(run(a,{'pivot':3,'shadowRange':-5,'deathStart':-10}).view('u4'),a.view('u4'))

def test_tint_saturation_and_bleach_preserve_radiometric_y():
    rgb=np.random.default_rng(2).uniform(.001,4,(1000,3)).astype(np.float32)
    for params in [{'shadowTint':.4,'shadowRange':2},{'highlightTint':.8,'highlightHue':120,'highlightRange':0},{'midBalance':.8,'midTint':-.7},{'saturation':3},{'highlightBleach':1,'highlightRange':0},{'colourDeath':1,'deathStart':4}]:
        out=run(rgb,params);assert np.allclose(out[:,:3]@M[1],rgb@M[1],atol=2e-6,rtol=2e-6)
        assert np.all(out[:,3]==np.float32(.37))

def test_colour_death_retention_and_green_highlights_are_direct():
    y=np.geomspace(1e-7,8,500);neutral=np.repeat(y[:,None],3,-1)
    rgb=neutral*np.array([1.8,.7,.3]);alive=run(rgb);dead=run(rgb,{'colourDeath':1,'deathStart':-6,'deathSoftness':1})
    chroma=lambda x:np.linalg.norm(x[:,:3]-np.mean(x[:,:3],axis=-1,keepdims=True),axis=-1)
    assert np.median(chroma(dead[:100])/chroma(alive[:100]))<.01
    green=run(neutral,{'highlightTint':.3,'highlightHue':120,'highlightRange':0,'highlightBleach':.8})
    assert green[-1,1]>green[-1,0] and green[-1,1]>green[-1,2]
    cool=run(neutral,{'shadowTint':.3,'shadowHue':240})
    assert cool[30,2]>cool[30,0]

def test_positive_neutral_tone_curve_and_boundary_continuity():
    y=np.geomspace(1e-8,1e6,5000);rgb=np.repeat(y[:,None],3,-1)
    out=run(rgb,{'contrast':1.4,'shadowCompression':.9,'highlightCompression':1})[:,:3]
    assert np.all(np.diff(out@M[1])>0)
    low=run(rgb,{'contrast':.1,'shadowCompression':1,'highlightCompression':1})[:,:3]
    assert np.all(np.diff(low@M[1])>0)
    assert np.allclose(out[:,0],out[:,1],rtol=3e-6,atol=2e-6)
    for center in [-6,-4,-3,3,4]:
        patch=.18*np.exp2(center+np.array([-1e-4,0,1e-4]));result=run(np.repeat(patch[:,None],3,-1),{'shadowTint':.4,'highlightTint':-.3,'midExposure':1,'colourDeath':.8})
        assert np.max(np.abs(np.diff(result[:,:3],axis=0)))/max(patch)<.001

def test_signed_hdr_alpha_and_explicit_overflow():
    rng=np.random.default_rng(52);rgb=rng.normal(size=(1000,3))*np.exp2(rng.uniform(-18,16,(1000,1)))
    out=run(rgb,{'exposure':3,'contrast':1.8,'shadowTint':.5,'midExposure':-1,'blackLevel':-.005,'highlightTint':.4,'highlightCompression':.8,'colourBalance':1})
    assert np.isfinite(out).all()
    zero=np.array([[.03,-.1,3,0]],np.float32)
    assert np.array_equal(run(zero,{'alphaMode':1,'exposure':2}),zero)
    with pytest.raises(Exception,match='Nonfinite source'):run([[np.nan,0,0]],{'shadowTint':.1})
    with pytest.raises(Exception,match='nonfinite'):run([[1e30,1e30,1e30]],{'contrast':4,'exposure':20})

def test_cross_gamut_equivalent_xyz_and_invalid_ranges():
    rgb=np.random.default_rng(15).uniform(.01,2,(200,3));xyz=rgb@M.T
    params={'contrast':1.25,'highlightTint':.3,'highlightHue':120,'shadowTint':.2,'saturation':1.2,'highlightCompression':.7}
    comparisons=[]
    for g in [0,1,2]:
        matrix=np.array(c.matrix(g)).reshape(3,3)
        # AP1 D60 is adapted to the same D65 reference stimulus.
        cat=np.array(c.adaptation(.32168,.33767,.3127,.329,0)).reshape(3,3) if g==1 else np.eye(3)
        source=xyz@np.linalg.inv(cat@matrix).T;out=run(source,params,g+1)[:,:3]@(cat@matrix).T;comparisons.append(out)
    for out in comparisons[1:]:assert np.allclose(out,comparisons[0],atol=2e-6,rtol=2e-5)
    with pytest.raises(Exception,match='exceeds'):run([[.18,.18,.18]],{'shadowRange':4,'highlightRange':-4})
