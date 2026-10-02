import numpy as np
import pytest
import colour
import _rendition as c

def process(e,rgb,p=None,g=1):
    x=np.asarray(rgb,dtype=np.float32)
    alpha=np.full(x.shape[:-1]+(1,),.37,dtype=np.float32)
    return c.process(e,np.concatenate([x,alpha],-1),{'interpretation':g,**(p or {})})

@pytest.mark.parametrize('e',range(8))
def test_default_exact(e):
    rng=np.random.default_rng(44)
    x=rng.normal(size=(1000,4)).astype(np.float32)*np.exp2(rng.uniform(-20,20,(1000,1))).astype(np.float32)
    x[0]=[np.nan,np.inf,-np.inf,.0]
    out=c.process(e,x,{'interpretation':1})
    assert np.array_equal(x.view(np.uint32),out.view(np.uint32))

@pytest.mark.parametrize('e',range(8))
def test_auto_unknown_fails_even_identity(e):
    with pytest.raises(ValueError,match='Interpretation Required'):c.process(e,np.ones((1,4),np.float32))

@pytest.mark.parametrize('g',range(1,4))
def test_exposure_equivariance_scene(g):
    x=np.array([[-.1,.2,1.2],[.18,.18,.18],[100,25,-1]],np.float32)
    out=process(0,x,{'exposure':1.25},g)
    assert np.allclose(out[:,:3],x*2**1.25,rtol=2e-6,atol=2e-6)
    assert np.all(out[:,3]==np.float32(.37))

def test_signed_sop_and_domain():
    out=process(0,[[-.5,0,2]],{'rPower':2})
    assert np.allclose(out[0,:3],[-.25,0,2],atol=2e-6)
    with pytest.raises(ValueError,match='positive'):process(0,[[-.5,0,2]],{'rPower':2,'cdlDomain':1,'lookDomain':0})

@pytest.mark.parametrize('mode',[1,2])
def test_matrix_neutral_properties(mode):
    ramp=np.geomspace(1e-5,1e3,100).astype(np.float32)
    x=np.repeat(ramp[:,None],3,axis=1)
    p={'rg':.3,'rb':-.2,'gr':.8,'gb':-.1,'br':-.7,'bg':.2,'mode':mode,'rowSum':.6}
    out=process(5,x,p)[:,:3]
    expected=x*(1 if mode==1 else .6)
    assert np.allclose(out,expected,rtol=2e-6,atol=2e-6)
    if mode==2:assert not np.allclose(out,x)

def test_luminance_projection():
    p={'mode':3,'m00':1.2,'m01':.5,'m12':-.6,'m21':.7}
    m=np.array(c.effective_matrix(5,{'interpretation':1,**p})).reshape(3,3)
    l=np.array(c.matrix(0)).reshape(3,3)[1]
    assert np.allclose(l@m,l,atol=2e-7)
    x=np.random.default_rng(9).normal(size=(200,3))
    assert np.allclose(process(5,x,p)[:,:3]@l,x@l,atol=2e-6)

@pytest.mark.parametrize('g',range(3))
def test_opponent_against_colour(g):
    rgb=np.random.default_rng(0).uniform(.02,1,(100,3))
    xyz=rgb@np.array(c.matrix(g)).reshape(3,3).T
    for x in xyz:
        actual=c.opponent(x.tolist(),False)
        reference=colour.XYZ_to_Oklab(x)
        assert np.allclose(actual,reference,rtol=2e-5,atol=3e-6)

def test_opponent_signed_inverse():
    xs=np.random.default_rng(2).normal(size=(1000,3))*2**np.random.default_rng(5).uniform(-15,15,(1000,1))
    for x in xs:
        q=c.opponent(x.tolist(),False);out=np.array(c.opponent(q,True))
        assert np.max(np.abs(out-x))<2e-6+2e-5*np.max(np.abs(x))

@pytest.mark.parametrize('linked',[0,1])
@pytest.mark.parametrize('strength',[0,.4,.8])
def test_tone_monotonic_and_gray(linked,strength):
    ramp=np.r_[-np.geomspace(1e2,1e-8,500),0,np.geomspace(1e-8,1e4,2000)].astype(np.float32)
    x=np.repeat(ramp[:,None],3,axis=1)
    p={'linked':linked,'toe':strength,'shoulder':strength,'contrast':.7,'shadowDensity':.9,'highlightDensity':-.9}
    out=process(1,x,p)[:,0]
    assert np.all(np.isfinite(out))
    assert np.min(np.diff(out))>=-2e-6
    gray=process(1,[[.18]*3],p)[0,:3]
    assert np.allclose(gray,.18,atol=2e-6)

@pytest.mark.parametrize('e,p',[(0,{'exposure':2}),(1,{'contrast':1.1}),(2,{'v0_hueDelta':5}),(4,{'midHue':5}),(5,{'rg':.2})])
def test_premult_and_zero_alpha(e,p):
    straight=np.array([[.8,.2,.1,.4],[.5,-.1,2,0]],np.float32)
    premult=straight.copy();premult[0,:3]*=premult[0,3]
    actual=c.process(e,premult,{'interpretation':1,'alphaMode':1,**p})
    expected=c.process(e,straight[:1],{'interpretation':1,**p})
    expected[:,:3]*=expected[:,3:4]
    assert np.allclose(actual[:1],expected,rtol=2e-5,atol=2e-6)
    assert np.array_equal(actual[1],premult[1])

@pytest.mark.parametrize('overlap',range(4))
def test_volume_permutation_and_neutral(overlap):
    rng=np.random.default_rng(31);rgb=rng.uniform(.01,2,(100,3))
    p={'overlap':overlap,'v0_width':360,'v0_hueDelta':12,'v0_chroma':1.2,'v0_exposure':.3,'v1_width':360,'v1_hueDelta':-9,'v1_chroma':.8,'v1_exposure':-.2}
    q={k.replace('v0_','tmp_').replace('v1_','v0_').replace('tmp_','v1_'):v for k,v in p.items()}
    # Move complete region definitions, including their original default family centers.
    p['v0_hue']=29;p['v1_hue']=110;q['v0_hue']=110;q['v1_hue']=29
    assert np.allclose(process(2,rgb,p),process(2,rgb,q),atol=2e-6,rtol=2e-5)
    out=process(2,[[.18]*3],p)[0,:3]
    assert np.allclose(out,.18,atol=3e-6)

@pytest.mark.parametrize('g',range(1,4))
def test_volume_cross_gamut(g):
    s=colour.RGB_COLOURSPACES['ITU-R BT.2020'];xyz=np.array([[.2,.1,.03],[.1,.2,.3],[.4,.4,.4]])
    w=colour.xy_to_XYZ([.3127,.329]);spaces=['ITU-R BT.2020','ACEScg','ITU-R BT.709']
    outs=[]
    for gi,name in enumerate(spaces,1):
        sp=colour.RGB_COLOURSPACES[name]
        cat=colour.adaptation.matrix_chromatic_adaptation_VonKries(w,colour.xy_to_XYZ(sp.whitepoint),transform='Bradford')
        local=xyz@cat.T@sp.matrix_XYZ_to_RGB.T
        q=process(2,local,{'v0_width':360,'v0_hueDelta':8,'v0_chroma':1.1},gi)[:,:3]
        outs.append(q@sp.matrix_RGB_to_XYZ.T@np.linalg.inv(cat).T)
    assert np.allclose(outs[0],outs[g-1],atol=2e-6,rtol=2e-5)

@pytest.mark.parametrize('e,p',[(3,{'density':.5}),(6,{'separation':.7})])
def test_spectral_candidates_finite(e,p):
    rgb=np.array([[.2,.5,.6],[-.1,.2,5],[.18,.18,.18],[0,0,0],[2000,50,100]],np.float32)
    out=process(e,rgb,p)
    assert np.all(np.isfinite(out))
    assert np.allclose(out[2,:3],rgb[2],atol=3e-6)
    assert np.allclose(out[3,:3],0,atol=2e-6)

def test_nonfinite_and_invalid_parameters():
    with pytest.raises(ValueError,match='Nonfinite'):process(0,[[np.inf,0,0]],{'exposure':1})
    with pytest.raises(ValueError,match='Unknown parameter'):process(0,[[1,0,0]],{'typo':1})
    with pytest.raises(ValueError,match='Invalid parameter'):process(0,[[1,0,0]],{'exposure':30})
    with pytest.raises(ValueError,match='minimum exceeds'):process(2,[[1,0,0]],{'v0_evMin':10,'v0_evMax':0})

def test_compound_order_stability():
    rng=np.random.default_rng(73);rgb=rng.normal(size=(300,3))*np.exp2(rng.uniform(-10,10,(300,1)))
    x=np.c_[rgb,np.ones(300)].astype(np.float32)
    stack=[(0,{'exposure':.4}),(2,{'v0_width':360,'v0_hueDelta':8}),(3,{'density':.4}),(6,{'separation':.3}),(4,{'width':360,'darkHue':-5,'brightChroma':.95}),(5,{'rg':.02})]
    for sequence in [stack,stack[::-1]]:
        out=x.copy()
        for e,p in sequence:out=c.process(e,out,{'interpretation':1,**p})
        assert np.all(np.isfinite(out))
        assert np.all(out[:,3]==1)


def test_supplied_rgb_preserves_nonfinite_alpha():
    x=np.array([[.1,.2,2,np.nan],[.2,-.1,4,np.inf]],np.float32)
    out=c.process(0,x,{'interpretation':1,'exposure':1})
    assert np.array_equal(out[:,3].view(np.uint32),x[:,3].view(np.uint32))
    assert np.array_equal(out[:,:3],x[:,:3]*2)
    with pytest.raises(ValueError,match='Nonfinite alpha'):
        c.process(0,x,{'interpretation':1,'exposure':1,'alphaMode':1})

def test_linked_tone_signed_hdr_cancellation():
    x=np.array([[1e4,-3e3,20],[-1e3,30,4],[0,0,0]],np.float32)
    out=process(1,x,{'contrast':1.2,'toe':.2,'shoulder':.3})
    assert np.all(np.isfinite(out))

@pytest.mark.parametrize('domain',range(6))
@pytest.mark.parametrize('effect,params',[(0,{'rPower':1.05,'cdlDomain':1}),(1,{'contrast':1.1}),(4,{'mode':1,'darkr':.15}),(5,{'domain':1,'rg':.03})])
def test_all_look_domain_exposure_sweeps(effect,params,domain):
    rgb=np.array([[.12,.24,.5],[.3,.15,.04],[.18,.18,.18]],np.float32)
    for stop in [-10,-5,0,5,10]:
        out=process(effect,rgb*2.**stop,{**params,'lookDomain':domain})
        assert np.all(np.isfinite(out))
        assert np.all(out[:,3]==np.float32(.37))

@pytest.mark.parametrize('effect,params',[(0,{'exposure':.7}),(5,{'rg':.08}),(6,{'separation':.6,'palette':.3})])
def test_declared_equivariance(effect,params):
    assert c.semantics(effect,params)['exposure']=='Equivariant'
    rgb=np.array([[.12,.24,.5],[-.03,.12,1],[0,0,0]],np.float32)
    base=process(effect,rgb,params)[:,:3]
    for stop in [-10,-5,0,5,10]:
        assert np.allclose(process(effect,rgb*2.**stop,params)[:,:3],base*2.**stop,rtol=3e-5,atol=3e-6)

@pytest.mark.parametrize('effect,params',[(2,{'v0_width':360,'v0_hueDelta':10}),(3,{'density':.4}),(6,{'separation':.6})])
def test_spectral_volume_cross_gamut(effect,params):
    xyz=np.array([[.15,.2,.3],[.35,.15,.06],[.4,.5,.2]],float)
    w=colour.xy_to_XYZ([.3127,.329]);outs=[]
    for g,name in [(1,'ITU-R BT.2020'),(2,'ACEScg'),(3,'ITU-R BT.709')]:
        space=colour.RGB_COLOURSPACES[name]
        cat=colour.adaptation.matrix_chromatic_adaptation_VonKries(w,colour.xy_to_XYZ(space.whitepoint),transform='Bradford')
        local=xyz@cat.T@space.matrix_XYZ_to_RGB.T
        result=process(effect,local,params,g)[:,:3]
        outs.append(result@space.matrix_RGB_to_XYZ.T@np.linalg.inv(cat).T)
    assert np.allclose(outs[0],outs[1],atol=3e-6,rtol=3e-5)
    assert np.allclose(outs[0],outs[2],atol=3e-6,rtol=3e-5)


@pytest.mark.parametrize('effect,params',[(0,{'exposure':1}),(1,{'contrast':1.1}),(2,{'v0_width':360,'v0_hueDelta':10}),(3,{'density':.4}),(4,{'midHue':10}),(5,{'rg':.1}),(6,{'separation':.4})])
def test_near_zero_finite(effect,params):
    rgb=np.array([[1e-40,2e-40,-1e-40],[1e-25,-2e-25,3e-25],[0,0,0]],np.float32)
    out=process(effect,rgb,params)
    assert np.all(np.isfinite(out))
