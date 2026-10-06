"""Architecture-only regressions against the captured accepted 0.32 implementation."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types
import numpy as np
import pytest
import _rendition as core
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'integrations/nuke'))
import rendition_presentation as policy

def test_parameters_and_rendered_bits_unchanged():
    baseline=json.loads((ROOT/'tests/fixtures/accepted-0.32.json').read_text())
    for effect,definitions in baseline['parameters'].items():
        current=core.parameters(int(effect))
        assert current[:len(definitions)]==definitions
        assert [d['id'] for d in current[len(definitions):]]==(['temperature','illuminantTint','illuminantAdaptation','illuminantVersion'] if int(effect)==9 else ['illuminantVersion'] if int(effect)==0 else [])
    x=np.array(baseline['input'],np.float32)
    for case in baseline['cases']:
        actual=core.process(case['effect'],x,case['parameters'])
        assert np.array_equal(actual.view(np.uint32),np.array(case['rgba_bits'],np.uint32)),case

def test_schema_generation_and_parameter_authority():
    subprocess.run([sys.executable,str(ROOT/'tools/generate_presentation.py'),'--check'],check=True)
    groups=json.loads((ROOT/'integrations/nuke/artist-groups.json').read_text())
    assert groups==policy.GROUPS
    for e in policy.SCHEMA['effects'].values():
        parameters=core.parameters(e['effect'])
        declarations=[{key:c[key] for key in parameters[0]} for c in e['controls'] if 'default' in c]
        assert declarations==parameters
        assert all(k in {d['id'] for d in parameters} for k in policy.watched(e) if k not in ('editFamily',))

class Knob:
    def __init__(self,name,label='',value=0,kind='Double_Knob'):
        self.key=name;self.caption=label;self.v=value;self.kind=kind
        self.enable=True;self.visible=True;self.flags=set();self.range=None;self.link=None;self.node=None
    def name(self):return self.key
    def label(self):return self.caption
    def Class(self):return self.kind
    def getValue(self):return self.v
    def enabled(self):return self.enable
    def setEnabled(self,v):self.enable=bool(v)
    def setVisible(self,v):self.visible=bool(v)
    def setLabel(self,v):self.caption=v
    def clearFlag(self,v):self.flags.add(v)
    def setRange(self,*v):self.range=v
    def makeLink(self,target,key):assert target=='this';self.link=key
    def setValue(self,v):
        # Presentation may write informational Text only; all real grade knobs reject writes.
        assert self.kind=='Text_Knob',self.key
        self.v=v

class Node:
    def __init__(self,e):
        self.effect=e;self.k={}
        for c in e['controls']:
            self.addKnob(Knob(c['id'],c.get('label',c['caption']),c.get('default',0)))
        for group in policy.GROUPS[self.Class()]:self.addKnob(Knob(group,group,kind='Tab_Knob'))
    def Class(self):return 'OFXorg.gripcolor.rendition.'+self.effect['name']+'_v1'
    def fullName(self):return self.effect['name']
    def knobs(self):return self.k
    def allKnobs(self):return list(self.k.values())
    def addKnob(self,k):self.k[k.name()]=k;k.node=self
    def removeKnob(self,k):del self.k[k.name()]
    def __getitem__(self,k):return self.k[k]
    def summary(self):return [(k.name(),k.label(),k.kind,k.enable,k.visible,k.range,k.link,sorted(k.flags)) for k in self.k.values()]

@pytest.fixture
def adapters(monkeypatch):
    nuke=types.ModuleType('nuke');nuke.STARTLINE=4096
    for kind in ('Tab_Knob','Text_Knob','Link_Knob'):
        setattr(nuke,kind,lambda key,label='',value=0,kind=kind:Knob(key,label,value,kind))
    for name in ('addOnCreate','addOnScriptLoad','addKnobChanged','addUpdateUI','tprint'):setattr(nuke,name,lambda *a:None)
    nuke.allNodes=lambda **kwargs:[];nuke.frame=lambda:1
    monkeypatch.setitem(sys.modules,'nuke',nuke)
    def load(name,path):
        spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    old=load('ui032',ROOT/'tests/fixtures/presentation-0.32/rendition_ui.py')
    new=load('ui033',ROOT/'integrations/nuke/rendition_ui.py')
    return old,new

@pytest.mark.parametrize('name',['Base','Palette','Material'])
def test_layout_dependencies_and_direct_editors_match_032(name,adapters):
    old,new=adapters
    effect=next(e for e in policy.SCHEMA['effects'].values() if e['name']==name)
    a,b=Node(effect),Node(effect)
    old.refresh(a);new.refresh(b)
    additions={'temperature','illuminantTint','illuminantAdaptation','illuminantVersion','Illuminant'} if name=='Base' else set()
    def original_summary(node):return [row for row in node.summary() if row[0] not in additions and row[0].removeprefix('renditionUi_') not in additions]
    assert original_summary(a)==original_summary(b)
    rng=np.random.default_rng(33)
    watched=policy.watched(effect)
    for version in (0,1,2):
        for _ in range(12):
            for c in effect['controls']:
                if c['id'] not in watched:continue
                value=c.get('default',0)
                if 'default' in c and rng.random()>.6:
                    value=int(rng.integers(len(c['choices']))) if c['choices'] else float(rng.uniform(c['min'],c['max']))
                if c['id']=='editFamily':value=int(rng.integers(6))
                if c['id']=='modelVersion':value=version
                a[c['id']].v=b[c['id']].v=value
            before={k:v.v for k,v in b.k.items() if not k.startswith('renditionUi')}
            old.update(a);new.update(b)
            assert original_summary(a)==original_summary(b),(name,version)
            assert a['renditionUi_compatibility'].v==b['renditionUi_compatibility'].v
            assert {k:v.v for k,v in b.k.items() if k in before}==before
    host=sys.modules['nuke']
    host.thisNode=lambda:b
    host.thisKnob=lambda:b['modelVersion']
    host.allNodes=lambda **kwargs:[b]
    before={c['id']:b[c['id']].v for c in effect['controls']}
    new.changed();new.idle_update()
    assert {key:b[key].v for key in before}==before
    for k in b.k.values():
        if k.kind=='Link_Knob':assert k.link in b.k and not k.link.startswith('renditionUi')
    if effect['family_editor']:
        for index in range(6):
            b['editFamily'].v=index;new.update(b)
            for suffix in effect['family_editor']['ids']:assert b['renditionUiFamily_'+suffix].link=='Volume_v'+str(index)+'_'+suffix


def test_policy_reads_only_and_conditional_dependencies():
    for effect in policy.SCHEMA['effects'].values():
        values={c['id']:c.get('default',0) for c in effect['controls']}
        baseline=values.copy();policy.state(effect,lambda key,default:values.get(key,default));assert values==baseline
        values['interpretation']=1
        assert not policy.state(effect,lambda k,d:values.get(k,d))['rx']['enabled']
        values['interpretation']=4
        assert policy.state(effect,lambda k,d:values.get(k,d))['rx']['enabled']


def test_detached_nuke_callback_is_presentation_only(adapters):
    old,new=adapters
    class Detached:
        def Class(self):raise ValueError('A PythonObject is not attached to a node')
    assert new._effect(Detached()) is None
