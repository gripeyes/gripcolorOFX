import numpy as np
import pytest
from research.spectral_completion import CompletionReference, compact, METHODS

@pytest.fixture(scope='module')
def oracle():return CompletionReference()

@pytest.mark.parametrize('method',METHODS)
def test_signed_physical_component_and_scale(oracle,method):
 for rgb in [[0,0,0],[-.2,.3,4],[1e4,2e3,-50],[.65,.3,.18]]:
  xyz=oracle.lab.space.matrix_RGB_to_XYZ@rgb;b,r,_=oracle.reconstruct(xyz,method);bb,rr,_=oracle.reconstruct(xyz*2,method)
  assert (b>=0).all() and np.isfinite(b).all()
  assert np.allclose(b@oracle.lab.emission_weights+r,xyz,atol=1e-10)
  assert np.allclose(bb,2*b,atol=1e-10,rtol=1e-9)
  assert np.allclose(rr,2*r,atol=1e-10,rtol=1e-9)

@pytest.mark.parametrize('parameters',[
 {'separation':.8,'leakage':.8}, {'separation':.8,'mode':1},
 {'separation':.8,'mode':2,'m01':.15,'m12':-.1},
 {'separation':.8,'palette':.7,'rWeight':.7,'bWeight':1.4,'gContribution':.7},
 {'separation':1,'redAnchor':1}, {'separation':.8,'density':1}])
def test_full_integrated_record_controls_match_compact_fit(oracle,parameters):
 rgb=np.array([[.2,.24,.06],[.01,.6,.8],[-.2,.3,4],[.65,.3,.18]])
 ref=oracle.evaluate(rgb,'Strip','compact_basis',parameters);prod=compact(rgb,'Strip',parameters)
 assert np.allclose(ref,prod,atol=4e-5,rtol=1e-4)

@pytest.mark.parametrize('method',METHODS)
def test_reference_neutrals_and_active_signed_transitions(oracle,method):
 rgb=np.array([[.18,.18,.18],[-.2,-.2,-.2],[0,0,0],[10,10,10]])
 for effect,p in [('Density',{'density':.75}),('Strip',{'separation':.75})]:
  # Published D65/Oklab constants give small neutral protection leakage, also in v1.
  result=oracle.evaluate(rgb,effect,method,p)
  assert np.allclose(result,rgb,atol=1e-8,rtol=5e-5)
  assert np.all(abs(result[:,:2]-result[:,1:]) < 2e-6+2e-5*np.maximum(abs(result[:,:2]),abs(result[:,1:])))
  ramp=np.c_[np.linspace(-.001,.001,51),np.full(51,.2),np.full(51,.4)]
  result=oracle.evaluate(ramp,effect,method,p)
  assert np.isfinite(result).all()
  assert np.max(abs(np.diff(result,axis=0)))<.003


def test_sigmoid_bounded_shape_and_nonphysical_residual(oracle):
 xyz=np.array([.3,.2,.4]);base,residual,_=oracle.reconstruct(xyz,'sigmoid_d65_pilot')
 scale=2*np.max(abs(xyz/oracle.white))
 assert np.all(base<=scale*oracle.d65*(1+1e-12))
 # Nonrepresentable signed XYZ stays exact only with its algebraic residual.
 signed=np.array([-.3,.2,.1]);base,residual,_=oracle.reconstruct(signed,'sigmoid_d65_pilot')
 assert np.linalg.norm(residual)>0
 assert np.allclose(base@oracle.lab.emission_weights+residual,signed,atol=1e-12)
