"""0.32 parameter composition safety; historical models remain separate."""
import numpy as np
import pytest
import _rendition as c

@pytest.mark.parametrize('effect',[10,11])
def test_all_legal_composed_states_stay_inside_engine_ranges(effect):
    rng=np.random.default_rng(320)
    defs=c.parameters(effect)
    for _ in range(160):
        values={'interpretation':1,'modelVersion':2}
        for d in defs:
            if d['group'] in ('Input','Custom primaries','Expert') or d['id'].endswith('Version'):continue
            values[d['id']]=float(rng.integers(len(d['choices']))) if d['choices'] else float(rng.choice([d['min'],d['max'],d['default'],rng.uniform(d['min'],d['max'])]))
        for stage in c.artist_stages(effect,values):
            sd={d['id']:d for d in c.parameters(stage['effect'])}
            for key,value in stage['values'].items():
                assert sd[key]['min']-1e-12<=value<=sd[key]['max']+1e-12,(effect,key,value)

@pytest.mark.parametrize('effect,params',[(10,{'separation':.1,'Volume_v0_chroma':4}),(11,{'density':.1,'Density_density':1})])
def test_reproduced_ui_failures_fixed_only_in_new_composition(effect,params):
    x=np.array([[.02,.3,4,1],[-.1,.2,3,.4]],np.float32)
    with pytest.raises(Exception):c.process(effect,x,{'interpretation':1,'modelVersion':1,**params})
    assert np.isfinite(c.process(effect,x,{'interpretation':1,'modelVersion':2,**params})).all()

@pytest.mark.parametrize('effect',[10,11])
def test_safe_model_neutral_expert_retains_legacy_macro_appearance(effect):
    x=np.array([[.02,.3,4,1],[-.1,.2,3,.4]],np.float32)
    values={'interpretation':1,'separation':.6,'contamination':-.3}
    assert np.array_equal(c.process(effect,x,values),c.process(effect,x,{**values,'modelVersion':2}))

def test_crossing_selector_endpoints_is_defined_without_mutating_state():
    p={'interpretation':1,'modelVersion':2,'Volume_v3_chromaMin':4,'Volume_v3_chromaMax':0,'Crossover_darkPivot':20,'Crossover_brightPivot':-20}
    stages=c.artist_stages(10,p)
    assert stages[0]['values']['v3_chromaMin']==0
    assert stages[0]['values']['v3_chromaMax']==4
    assert stages[1]['values']['darkPivot']==-20
    assert p['Volume_v3_chromaMin']==4

def test_historical_equations_match_independently_built_pre032_binary():
    import json
    from pathlib import Path
    fixture=json.loads((Path(__file__).parent/'fixtures/legacy-0.31.json').read_text())
    x=np.array(fixture['input'],np.float32)
    for case in fixture['cases']:
        result=c.process(case['effect'],x,case['parameters'])
        assert np.array_equal(result.view(np.uint32),np.array(case['rgba_bits'],np.uint32)),case['parameters']

@pytest.mark.parametrize('effect',[9,10,11])
def test_every_single_artist_endpoint_renders_finite(effect):
    """Renderer evidence only; this cannot substitute for Properties dragging."""
    x=np.array([[0,0,0,1],[.18,.18,.18,.5],[.02,.3,4,1],[-.1,.2,3,.4],[16,2,.1,0]],np.float32)
    for d in c.parameters(effect):
        if d['group'] in ('Input','Custom primaries','Expert') or d['id'].endswith('Version'):continue
        for value in (range(len(d['choices'])) if d['choices'] else (d['min'],d['max'])):
            values={'interpretation':1,d['id']:float(value)}
            if effect in (10,11):values['modelVersion']=2
            if effect==9 and d['id']=='toeStart':values['shoulderStart']=max(value,4)
            if effect==9 and d['id']=='shoulderStart':values['toeStart']=min(value,-4)
            if effect==9 and d['id']=='shadowRange':values['highlightRange']=max(value,4)
            if effect==9 and d['id']=='highlightRange':values['shadowRange']=min(value,-4)
            assert np.isfinite(c.process(effect,x,values)).all(),(effect,d['id'],value)
