import numpy as np
import pytest
import colour
import _rendition as c

@pytest.mark.parametrize('g,name',[(0,'ITU-R BT.2020'),(1,'ACEScg'),(2,'ITU-R BT.709')])
def test_matrix_reference(g,name):
    expected=colour.RGB_COLOURSPACES[name].matrix_RGB_to_XYZ
    assert np.max(np.abs(np.array(c.matrix(g)).reshape(3,3)-expected))<2e-6

@pytest.mark.parametrize('g',range(3))
def test_float_roundtrip(g):
    rng=np.random.default_rng(31)
    values=rng.normal(size=(2000,3))*np.exp2(rng.uniform(-15,15,(2000,1)))
    values=values.astype(np.float32)
    for x in values:
        r=np.array(c.roundtrip(x.tolist(),g))
        # Cancellation in matrix products is measured against vector scale as well.
        assert np.max(np.abs(r-x)) <= 2e-6+2e-5*np.max(np.abs(x))

@pytest.mark.parametrize('method,name',[(0,'Bradford'),(1,'CAT16'),(2,'XYZ Scaling')])
def test_cat_reference(method,name):
    s=np.array([.3127,.329]);d=np.array([.32168,.33767])
    expected=colour.adaptation.matrix_chromatic_adaptation_VonKries(colour.xy_to_XYZ(s),colour.xy_to_XYZ(d),transform=name)
    assert np.max(np.abs(np.array(c.adaptation(*s,*d,method)).reshape(3,3)-expected))<2e-6

@pytest.mark.parametrize('tag',['','sRGB','log ACEScg','arbitrary linear','OfxSceneLinear','ACES2065-1'])
def test_unknown_semantics_fail(tag):
    with pytest.raises(ValueError,match='Interpretation Required'):c.interpret(0,tag)

def test_manual_authority():
    assert c.interpret(1,'log unknown')==c.matrix(0)
    assert c.interpret(0,'ACEScg')==c.matrix(1)

@pytest.mark.parametrize('domain',range(6))
def test_encoding_roundtrip(domain):
    values=np.geomspace(1e-8,2**20,1000).astype(np.float32)
    if domain not in (0,4):values=np.r_[-values[::-1][:600],0,values].astype(np.float32)
    for x in values:
        actual=c.decode(c.encode(float(x),domain),domain)
        assert abs(actual-x)<=2e-6+2e-5*abs(x)

@pytest.mark.parametrize('d', [0,4])
def test_positive_domains_reject_negative(d):
    with pytest.raises(ValueError):c.encode(-.1,d)
