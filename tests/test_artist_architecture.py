import json
from pathlib import Path
import numpy as np
import _rendition as c
import pytest

def run(i,rgb,v=None):
 a=np.asarray(rgb,np.float32)
 if a.shape[-1]==3:a=np.concatenate([a,np.full(a.shape[:-1]+(1,),.37,np.float32)],-1)
 return c.process(i,a,{'interpretation':1,**(v or {})})

def test_default_identity_versions_and_unknown_semantics():
 a=np.array([[np.nan,np.inf,-np.inf,0],[-.2,10,2,.3]],np.float32)
 for i in [9,10,11]:
  assert np.array_equal(run(i,a).view('u4'),a.view('u4'))
  with pytest.raises(Exception):c.process(i,a,{})
  with pytest.raises(Exception):run(i,a,{'modelVersion':3})
 assert len([p for p in c.parameters(9) if p['group']=='Artist'])==13

def test_base_constrained_monotone_aggressive_signed_neutral_curve():
 y=np.geomspace(1e-8,1e7,12000);a=np.repeat(y[:,None],3,axis=1)
 for p in [{'midExposure':4,'shadowSoftness':.25,'highlightSoftness':.25},
           {'midExposure':-4,'shadowSoftness':.25,'highlightSoftness':.25},
           {'blackStops':4,'whiteLevel':-4,'contrast':.1,'shadowCompression':1,'highlightCompression':1},
           {'blackStops':-4,'whiteLevel':4,'midDensity':2,'contrast':4}]:
  out=run(9,a,p)[:,:3];assert np.isfinite(out).all()
  # Float quantization may flatten very small positive slopes, never reverse materially.
  delta=np.diff(out[:,1]);assert np.all(delta>=-2e-6*np.maximum(out[:-1,1],1e-8))
  signed=run(9,-a,p)[:,:3];assert np.allclose(signed,-out,rtol=1e-5,atol=2e-6)
 assert run(9,[[.18,.18,.18]],{'midExposure':4,'shadowSoftness':.25,'highlightSoftness':.25})[0,1]>.18*8
 # Historical Primaries v1 still has its documented fold.
 old=run(8,a,{'midExposure':4,'shadowSoftness':.25,'highlightSoftness':.25})[:,1]
 assert np.any(np.diff(old)<0)

def test_old_primaries_saved_recipe_compatibility():
 fixture=json.loads((Path(__file__).parents[1]/'docs/reports/0.2.1-nuke-primaries.json').read_text())
 recipes=json.loads((Path(__file__).parents[1]/'docs/reports/0.2.1-primaries.json').read_text())['cases'][:7]
 params=[{},*[r['parameters'] for r in recipes]]
 for case,p in zip(fixture['checks'][:8],params):
  assert np.allclose(run(8,[[-.1,.2,4,.3]],p)[0],case['values'],rtol=2e-5,atol=2e-6)

def test_artist_frontends_signed_hdr_alpha_and_compound_stacks():
 rng=np.random.default_rng(39);a=np.c_[rng.normal(size=(600,3))*np.exp2(rng.uniform(-10,12,(600,1))),rng.uniform(0,1,600)].astype('f4')
 for i,p in [(9,{'midExposure':4,'highlightBurn':1,'shadowTint':.8}), (10,{'compression':1,'separation':1,'contamination':.8,'familyGreen':-45,'shadowHue':70,'colourDeath':1}), (11,{'density':1,'depth':1,'separation':1,'leakage':.8,'crosstalk':1})]:
  b=run(i,a,p);assert np.isfinite(b).all();assert np.array_equal(b[:,3].view('u4'),a[:,3].view('u4'))
  a=b
 zero=np.array([[1,-.2,8,0]],np.float32)
 assert np.array_equal(run(9,zero,{'alphaMode':1,'midExposure':4}),zero)

def test_matte_exposure_and_range_protection():
 p=[-.2,.5,4,.3]
 for stops in [-1,1]:
  out=c.local_exposure(p,1,{'interpretation':1,'localExposure':stops})
  assert np.allclose(out[:3],np.array(p[:3])*2**stops,atol=2e-6,rtol=2e-5);assert out[3]==np.float32(.3)
 assert c.local_exposure(p,0,{'interpretation':1,'localExposure':4})==list(np.array(p,np.float32))
 half=c.local_exposure(p,.5,{'interpretation':1,'localExposure':1})
 assert np.allclose(half[:3],np.array(p[:3])*2**.5,atol=2e-6,rtol=2e-5)
 for coverage in [-.1,1.1,float('nan')]:
  with pytest.raises(Exception):c.local_exposure(p,coverage,{'interpretation':1,'localExposure':1})
 protected=c.local_exposure([10,10,10,.4],1,{'interpretation':1,'localExposure':1,'localProtection':1,'localCenter':0})
 assert protected[0]<11

def test_base_exposure_tint_y_and_accent_protection():
 a=np.array([[.1,.3,2,.4],[.002,.003,.001,.4]],np.float32);M=np.array(c.matrix(0)).reshape(3,3)
 assert np.allclose(run(9,a,{'exposure':1})[:,:3],a[:,:3]*2,rtol=2e-5,atol=2e-6)
 tint=run(9,a,{'shadowTint':.5,'highlightTint':.8,'midTint':.4})
 assert np.allclose(tint[:,:3]@M[1],a[:,:3]@M[1],rtol=2e-5,atol=2e-6)
 assert not np.allclose(run(11,a,{'depth':1})[:,:3],a[:,:3])

def test_base_colourful_ray_brilliance_density_and_burn_monotonicity():
 M=np.array(c.matrix(0)).reshape(3,3);levels=np.geomspace(1e-9,1e7,8000)
 for ray in [[1,.1,.02],[.02,.6,1],[.2,.24,.04]]:
  a=levels[:,None]*np.array(ray)
  out=run(9,a,{'highlightBurn':1,'brillianceReduction':2,'colourBalance':2,'midExposure':4,'highlightSoftness':.25,'shadowSoftness':.25})[:,:3]@M[1]
  assert np.isfinite(out).all();assert np.all(np.diff(out)>=-3e-6*np.maximum(np.abs(out[:-1]),1e-9))
