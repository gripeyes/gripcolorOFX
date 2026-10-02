import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
import numpy as np
import colour
import pytest
from spectral_lab import Lab,Spectrum,Kind
import _rendition as c

@pytest.mark.parametrize('illuminant',['D65','D60','D50','A'])
def test_spectral_integration(illuminant):
    lab=Lab(1,illuminant)
    r=np.exp(-.5*((lab.grid-570)/70)**2)
    expected=colour.sd_to_XYZ(colour.SpectralDistribution(dict(zip(lab.grid,r))),lab.cmfs,lab.illuminant,method='Integration')/100
    assert np.allclose(lab.xyz(Spectrum(lab.grid,r,Kind.REFLECTANCE)),expected,atol=2e-12)

@pytest.mark.parametrize('strategy',['nnls_residual','smits_residual'])
@pytest.mark.parametrize('scale',['max','norm','luminance'])
def test_reconstruction_signed_identity_and_hdr(strategy,scale):
    lab=Lab()
    for rgb in [[0,0,0],[-.1,.3,2],[10000,2000,-50],[1,0,0],[-1,-2,-3]]:
        rgb=np.array(rgb,float);s,r,_=lab.reconstruct(rgb,scale,strategy);s2,r2,_=lab.reconstruct(rgb*2,scale,strategy)
        assert np.allclose(lab.xyz(s)+r,rgb@lab.space.matrix_RGB_to_XYZ.T,atol=2e-12)
        assert np.allclose(s2.values,2*s.values,atol=2e-12)
        assert np.allclose(r2,2*r,atol=2e-12)

@pytest.mark.parametrize('model',['pigment','dye'])
def test_concentration_monotonic(model):
    lab=Lab();prev=np.ones(len(lab.grid))
    for d in np.linspace(0,2,100):
        s=getattr(lab,model)([.8,.2,.5],d)
        assert np.all(s.values<=prev+1e-12);prev=s.values

def test_spectrum_validation():
    with pytest.raises(ValueError):Spectrum(np.array([500,400]),np.ones(2),Kind.REFLECTANCE)
    with pytest.raises(ValueError):Spectrum(np.array([400,500]),np.array([-1,1]),Kind.REFLECTANCE)
    with pytest.raises(ValueError):Spectrum(np.array([400,500]),np.array([2,1]),Kind.TRANSMITTANCE)
    s=Spectrum(np.array([400,500]),np.array([2,1]),Kind.EMISSION)
    with pytest.raises(ValueError):s.resample([390,500])

@pytest.mark.parametrize('e,p',[(3,{'density':.6,'highlightProtection':0,'shadowWeight':0}),(6,{'separation':.6})])
def test_spectral_scene_exposure_and_adapter_continuity(e,p):
    x=np.array([[.02,.3,.5,.4],[-.05,.3,.4,.6],[2,-.1,.4,.8]],np.float32)
    params={'interpretation':1,**p};a=c.process(e,x,params);xx=x.copy();xx[:,:3]*=2;b=c.process(e,xx,params)
    assert np.allclose(b[:,:3],2*a[:,:3],atol=2e-6,rtol=5e-5)
    # Scan a signed boundary instead of merely checking that processing doesn't crash.
    ramp=np.c_[np.linspace(-.001,.001,501),np.full(501,.2),np.full(501,.4),np.ones(501)].astype(np.float32)
    out=c.process(e,ramp,params)
    assert np.max(np.abs(np.diff(out[:,:3],axis=0)))<1e-4

@pytest.mark.parametrize('e,p',[(3,{'density':.6}),(6,{'separation':.7})])
def test_spectral_not_rgb_scaling_or_constant_matrix(e,p):
    rng=np.random.default_rng(59);x=rng.uniform(.02,1,(300,3)).astype(np.float32);rgba=np.c_[x,np.ones(300)].astype(np.float32)
    out=c.process(e,rgba,{'interpretation':1,**p})[:,:3]
    matrix=np.linalg.lstsq(x[:150],out[:150],rcond=None)[0]
    residual=np.max(np.abs(x[150:]@matrix-out[150:]))
    assert residual>.005
    cross=np.linalg.norm(np.cross(x,out),axis=1)
    assert np.max(cross)>.005
