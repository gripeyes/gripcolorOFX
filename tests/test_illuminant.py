"""Restored Base access to the unchanged Scene daylight/CAT operation."""
import numpy as np
import pytest
import colour
import _rendition as c
SAMPLES=np.array([[.18,.18,.18,1],[-.1,.2,4,.37],[16,2,.1,0],[0,0,0,1]],np.float32)

def process(effect,x=SAMPLES,**p):return c.process(effect,x,{'interpretation':1,**p})

@pytest.mark.parametrize('temperature',[4000,6000,6500,6504,10000,25000])
@pytest.mark.parametrize('method',[0,1,2])
def test_base_pure_illuminant_is_exact_scene(temperature,method):
    for tint in (0,-.02,.02):
        actual=process(9,temperature=temperature,illuminantTint=tint,illuminantAdaptation=method)
        expected=process(0,temperature=temperature,tint=tint,adaptation=method,illuminantVersion=1)
        assert np.array_equal(actual.view('u4'),expected.view('u4'))
        assert np.array_equal(actual[:,3].view('u4'),SAMPLES[:,3].view('u4'))

@pytest.mark.parametrize('gamut',[1,2,3])
def test_adaptation_then_base_matches_explicit_stack(gamut):
    scene=c.process(0,SAMPLES,{'interpretation':gamut,'temperature':6000,'tint':.002,'adaptation':1,'illuminantVersion':1})
    grade={'interpretation':gamut,'contrast':1.4,'shadowTint':.15,'whiteLevel':-.4}
    expected=c.process(9,scene,grade)
    actual=c.process(9,SAMPLES,{**grade,'temperature':6000,'illuminantTint':.002,'illuminantAdaptation':1})
    assert np.array_equal(actual.view('u4'),expected.view('u4'))

@pytest.mark.parametrize('method',[0,1,2])
def test_neutral_configuration_and_zero_alpha_are_exact(method):
    dirty=np.array([[np.nan,np.inf,-np.inf,0],[-.2,10,2,.3]],np.float32)
    result=process(9,dirty,illuminantAdaptation=method)
    assert np.array_equal(dirty.view('u4'),result.view('u4'))
    zero=np.array([[1,-.2,8,0]],np.float32)
    assert np.array_equal(process(9,zero,temperature=6000,alphaMode=1).view('u4'),zero.view('u4'))


def test_6000_versus_6500_independent_daylight_bradford_reference():
    rgb=np.array([[.18,.18,.18,1]],np.float32)
    matrix=np.array(c.matrix(0)).reshape(3,3);white=np.array([.3127,.3290])
    for temperature in (6000,6500):
        estimated=colour.temperature.CCT_to_xy_CIE_D(temperature)+white-colour.temperature.CCT_to_xy_CIE_D(6504)
        cat=colour.adaptation.matrix_chromatic_adaptation_VonKries(colour.xy_to_XYZ(estimated),colour.xy_to_XYZ(white),transform='Bradford')
        expected=np.linalg.inv(matrix)@cat@matrix@rgb[0,:3]
        assert np.allclose(process(9,rgb,temperature=temperature)[0,:3],expected,rtol=2e-5,atol=2e-6)
    low=process(9,rgb,temperature=6000)[0]
    high=process(9,rgb,temperature=6500)[0]
    assert low[0]<high[0] and low[2]>high[2]  # Lower source estimate is corrected cooler.


def test_illuminant_fixed_settings_preserve_exposure_scaling():
    x=process(9,temperature=6000)
    scaled=SAMPLES.copy();scaled[:,:3]*=8
    assert np.allclose(process(9,scaled,temperature=6000)[:,:3],8*x[:,:3],rtol=2e-5,atol=2e-6)


def test_legacy_daylight_remains_explicitly_reproducible():
    for temperature in (6000,6500,7000,7001,12000):
        expected=process(0,temperature=temperature)
        actual=process(9,temperature=temperature,illuminantVersion=0)
        assert np.array_equal(actual.view('u4'),expected.view('u4'))


def test_corrected_daylight_contains_legacy_7000k_jump():
    x=np.array([[.18,.18,.18,1]],np.float32)
    modern=np.max(np.abs(process(9,x,temperature=7000.01)-process(9,x,temperature=6999.99)))
    legacy=np.max(np.abs(process(0,x,temperature=7000.01)-process(0,x,temperature=6999.99)))
    assert modern<1e-4 and legacy>1e-3


def test_cie_illuminant_cross_gamut_equivalent_xyz():
    xyz=np.array([[.25,.18,.1],[.05,.15,.5],[-.1,.3,2]],np.float32)
    outputs=[]
    for gamut in range(3):
        matrix=np.array(c.matrix(gamut)).reshape(3,3)
        white=[(.3127,.3290),(.32168,.33767),(.3127,.3290)][gamut]
        to_d65=np.array(c.adaptation(*white,.3127,.3290,0)).reshape(3,3)
        rgb=(np.linalg.inv(matrix)@np.linalg.inv(to_d65)@xyz.T).T
        rgba=np.c_[rgb,np.ones(len(rgb))].astype('f4')
        out=c.process(9,rgba,{'interpretation':gamut+1,'temperature':6000,'illuminantTint':.005})[:,:3]
        outputs.append((to_d65@matrix@out.T).T)
    assert np.allclose(outputs[0],outputs[1],atol=2e-6,rtol=2e-5)
    assert np.allclose(outputs[0],outputs[2],atol=2e-6,rtol=2e-5)
