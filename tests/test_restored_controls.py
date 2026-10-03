import numpy as np
import _rendition as c
import pytest

def run(e,p):return c.process(e,np.array([[.01,.4,2,.37],[-.1,.2,4,0]],np.float32),{'interpretation':1,**p})

@pytest.mark.parametrize('e',[10,11])
def test_explicit_opt_in_and_unchanged_v1(e):
 assert np.array_equal(run(e,{}),run(e,{'modelVersion':1}))
 key='Volume_v3_hueDelta' if e==10 else 'Strip_palette'
 with pytest.raises(Exception):run(e,{key:.3})
 assert not np.array_equal(run(e,{'modelVersion':1,key:.3,'separation':.5}),run(e,{'modelVersion':1,'separation':.5}))

def test_macro_expert_composition_is_deterministic_non_destructive():
 p={'modelVersion':1,'separation':.3,'Volume_v3_width':40,'Crossover_darkHue':30,'Crosstalk_m02':.2,'Crosstalk_m12':-.1,'familyCyan':10}
 a=c.artist_stages(10,{'interpretation':1,**p})
 b=c.artist_stages(10,{'interpretation':1,**p,'separation':.5})
 assert a[0]['values']['v3_width']==b[0]['values']['v3_width']==40
 assert a[1]['values']['darkHue']==b[1]['values']['darkHue']==30
 assert a[2]['values']['m02']==b[2]['values']['m02']==.2
 assert np.isfinite(run(10,p)).all()

@pytest.mark.parametrize('domain',range(6))
def test_restored_channel_and_matrix_domain_plumbing(domain):
 p={'modelVersion':1,'Crossover_mode':1,'Crossover_darkb':.4,'Crossover_lookDomain':domain,'Crosstalk_domain':1,'Crosstalk_lookDomain':domain,'Crosstalk_m02':.1}
 # Positive-only encodings tested on positive input, signed domains separately audited.
 x=np.array([[.02,.2,4,1],[.1,.3,.5,.4]],np.float32)
 y=c.process(10,x,{'interpretation':1,**p})
 assert np.isfinite(y).all() and np.array_equal(y[:,3],x[:,3])


def test_absolute_selectors_do_not_inherit_macro_width():
 p={'interpretation':1,'modelVersion':1,'separation':.6,'Volume_v3_width':40,'Crossover_width':55}
 stages=c.artist_stages(10,p)
 assert stages[0]['values']['v3_width']==40
 assert stages[1]['values']['width']==55
 assert c.artist_stages(10,{'interpretation':1,'modelVersion':1})[1]['values']['width']==360

@pytest.mark.parametrize('e,p',[(10,{'separation':.4,'compression':.2,'contamination':.3,'accent':.6,'bias':-.2,'shadowHue':20,'highlightHue':-15,'familyCyan':12,'colourDeath':.3,'trajectory':1.4}),(11,{'depth':.6,'density':.4,'coupling':.3,'separation':.5,'leakage':.2,'crosstalk':.3,'contamination':-.1,'anchor':.4})])
def test_neutral_expert_state_matches_authored_v1_exactly(e,p):
 assert np.array_equal(run(e,p),run(e,{**p,'modelVersion':1}))
