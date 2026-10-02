"""Real OCIO role resolution and callback refresh, without requiring a Nuke license."""
import importlib.util
from pathlib import Path
import sys,types
import PyOpenColorIO as ocio
import pytest

class Knob:
    def __init__(self,value,name=''):self.current=value;self.key=name;self.tooltip=''
    def value(self):return self.current
    def getValue(self):return self.current
    def setValue(self,value):self.current=value
    def name(self):return self.key
    def setTooltip(self,text):self.tooltip=text
class Node:
    def __init__(self,cls,values):self.cls=cls;self.values={k:Knob(v,k) for k,v in values.items()}
    def Class(self):return self.cls
    def knobs(self):return self.values
    def __getitem__(self,key):return self.values[key]

def config_file(path,name,role=True,aliases=()):
    config=ocio.Config();config.setVersion(2,0)
    space=ocio.ColorSpace(name=name)
    for alias in aliases:space.addAlias(alias)
    config.addColorSpace(space)
    if role:config.setRole('scene_linear',name)
    path.write_text(config.serialize());return str(path)

@pytest.fixture
def host(monkeypatch,tmp_path):
    root=Node('Root',{'colorManagement':'OCIO','OCIO_config':'custom','customOCIOConfigPath':config_file(tmp_path/'config.ocio','Linear Rec.2020'),'OCIOConfigPath':''})
    nodes=[Node('OFXorg.gripcolor.rendition.'+name+'_v1',{'hostSceneLinear':0,'interpretation':0,'exposure':1.25}) for name in ['Scene','Tone','Volume','Density','Crossover','Crosstalk','Strip','Inspector']]
    callbacks={};state={'node':root,'knob':root['customOCIOConfigPath']}
    nuke=types.ModuleType('nuke');nuke.root=lambda:root;nuke.allNodes=lambda **kw:nodes;nuke.thisNode=lambda:state['node'];nuke.thisKnob=lambda:state['knob']
    for key in ['addOnCreate','addOnScriptLoad','addKnobChanged','addBeforeRender']:setattr(nuke,key,lambda callback,key=key:callbacks.setdefault(key,callback))
    monkeypatch.setitem(sys.modules,'nuke',nuke)
    spec=importlib.util.spec_from_file_location('tested_rendition_host',Path(__file__).resolve().parents[1]/'integrations/nuke/rendition_host.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module,root,nodes,callbacks,state,tmp_path

def test_role_changes_refresh_all_effects_without_creative_changes(host):
    module,root,nodes,callbacks,state,path=host
    callbacks['addOnScriptLoad']();assert all(n['hostSceneLinear'].value()==2 for n in nodes)
    # Manual selection remains manual while the derived interpretation updates.
    nodes[0]['interpretation'].setValue(3)
    root['customOCIOConfigPath'].setValue(config_file(path/'ap1.ocio','ACEScg'))
    callbacks['addKnobChanged']();assert all(n['hostSceneLinear'].value()==3 for n in nodes)
    assert nodes[0]['interpretation'].value()==3
    assert all(n['exposure'].value()==1.25 for n in nodes)
    assert 'ACEScg' in nodes[0]['interpretation'].tooltip
    root['customOCIOConfigPath'].setValue(config_file(path/'ap709.ocio','Linear Rec.709'))
    callbacks['addBeforeRender']();assert all(n['hostSceneLinear'].value()==4 for n in nodes)

@pytest.mark.parametrize('kind',['missing','unknown','conflicting_alias','invalid_path','not_ocio'])
def test_unresolved_role_is_explicit_and_never_rec2020(host,kind):
    module,root,nodes,callbacks,state,path=host
    callbacks['addBeforeRender']();assert all(n['hostSceneLinear'].value()==2 for n in nodes)
    if kind=='missing':config=config_file(path/'bad.ocio','Linear Rec.2020',role=False)
    elif kind=='unknown':config=config_file(path/'bad.ocio','Mystery Log')
    elif kind=='conflicting_alias':config=config_file(path/'bad.ocio','ACEScg',aliases=['Linear Rec.2020'])
    elif kind=='invalid_path':config=str(path/'absent.ocio')
    else:root['colorManagement'].setValue('Nuke');config=root['customOCIOConfigPath'].value()
    root['customOCIOConfigPath'].setValue(config);callbacks['addBeforeRender']()
    assert all(n['hostSceneLinear'].value()==1 for n in nodes)


def test_detached_shutdown_node_does_not_refresh_or_raise(host):
    module,root,nodes,callbacks,state,path=host
    class Detached:
        def Class(self):raise ValueError('A PythonObject is not attached to a node')
    state['node']=Detached()
    callbacks['addKnobChanged']()
    assert all(n['hostSceneLinear'].value()==0 for n in nodes)
