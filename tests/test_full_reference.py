import numpy as np
from research.full_reference import FullReference

def test_reconstruction_identity_scale_signed_and_active_finite():
 o=FullReference()
 for method in ['compact_basis','nnls_residual','smits_residual']:
  for rgb in [[-.2,.3,4],[0,0,0],[1e4,2e3,-50]]:
   xyz=o.lab.space.matrix_RGB_to_XYZ@rgb;b,r,_=o.reconstruct(xyz,method);b2,r2,_=o.reconstruct(xyz*2,method)
   assert np.allclose(b@o.lab.emission_weights+r,xyz,rtol=1e-12,atol=1e-10)
   assert np.allclose(b2,2*b,rtol=1e-10,atol=1e-10)
   for effect in ['Density','Strip']:assert np.isfinite(o.process(rgb,effect,method)).all()


def test_independent_one_nm_integration_matches_compact_fit():
 import _rendition as core
 oracle=FullReference()
 for source in [[.65,.3,.18],[.01,.6,.8],[.2,.24,.06],[-.2,.3,4]]:
  for effect,slot in [('Density',3),('Strip',6)]:
   params={'interpretation':1,'density':.75} if slot==3 else {'interpretation':1,'separation':.75,'leakage':.1}
   compact=core.process(slot,np.array([[*source,1]],np.float32),params)[0,:3]
   reference=oracle.process(source,effect,'compact_basis')
   assert np.max(np.abs(compact-reference)) < 2e-5*max(np.max(np.abs(source)),1)
