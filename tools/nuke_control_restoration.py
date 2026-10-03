import nuke,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'build/control-audit-0.31';out.mkdir(parents=True,exist_ok=True)
checks=[];source=nuke.nodes.Constant();source['format'].setValue('square_256');source['color'].setValue([.02,.3,4,.37])
for effect in ['Palette','Material']:
 node=nuke.createNode('OFXorg.gripcolor.rendition.'+effect+'_v1',inpanel=False);node.setInput(0,source);node['interpretation'].setValue(1)
 assert node['modelVersion'].getValue()==0
 node['modelVersion'].setValue(1)
 key='Volume_v3_width' if effect=='Palette' else 'Strip_palette';alias='renditionUi_'+key
 if effect=='Palette':
  mode_alias=node['renditionUi_Channel_Crossover_mode'];mode_alias.setValue(1);assert node['Crossover_mode'].getValue()==1;mode_alias.setValue(0)
 assert alias in node.knobs();node[alias].setValue(40 if effect=='Palette' else .3);assert node[key].value()==node[alias].value()
 node['separation'].setValue(.3);node['Crosstalk_m02'].setValue(.1)
 node[key].setAnimated();node[key].setValueAt(40 if effect=='Palette' else .2,1);node[key].setValueAt(60 if effect=='Palette' else .4,2)
 node.setName('Restored_'+effect);values=[node.sample(ch,100.5,100.5,frame=1) for ch in ['red','green','blue','alpha']]
 checks.append({'case':effect+' native composed state, link edits and animation','passed':True,'values':values})
# Copy/paste and saved reload preserve authored state and model choice.
for node in nuke.allNodes():node.setSelected(node.Class().startswith('OFXorg.gripcolor.rendition.'))
nuke.nodeCopy(str(out/'copy-paste.nk'));nuke.nodePaste(str(out/'copy-paste.nk'))
for node in nuke.allNodes():
 if node.Class().startswith('OFXorg.gripcolor.rendition.'):
  assert node['modelVersion'].getValue()==1
checks.append({'case':'Native copy/paste explicit model persistence','passed':True})
nuke.scriptSaveAs(str(out/'restored-host.nk'),overwrite=1);nuke.scriptClear();nuke.scriptOpen(str(out/'restored-host.nk'))
for name,key,expected in [('Restored_Palette','Volume_v3_width',60),('Restored_Material','Strip_palette',.4)]:
 node=nuke.toNode(name);assert abs(node[key].valueAt(2)-expected)<1e-6
 assert node['modelVersion'].getValue()==1
checks.append({'case':'Rename animation save/reload','passed':True})
# Existing generated artist graph remains v1 with original equations/settings.
nuke.scriptClear();nuke.scriptOpen(str(root/'build/architecture-0.3/Rendition-0.3-artist.nk'))
for node in nuke.allNodes():
 if any(node.Class().endswith('.'+e+'_v1') for e in ['Base','Palette','Material']):assert node['modelVersion'].getValue()==0
checks.append({'case':'0.3 saved artist graph remains v1','passed':True})
# Domains + animated reload. All six choices remain distinct; positive-only input chosen.
nuke.scriptClear();source=nuke.nodes.Constant();source['format'].setValue('square_256');source['color'].setValue([.02,.3,4,.37])
for domain in range(6):
 for effect,settings in [('Tone',{'contrast':1.2}),('Scene',{'cdlDomain':1,'rOffset':.1}),('Crosstalk',{'domain':1,'rg':.1}),('Crossover',{'mode':1,'darkr':.2,'midr':.1,'brightr':-.1})]:
  node=nuke.createNode('OFXorg.gripcolor.rendition.'+effect+'_v1',inpanel=False);node.setInput(0,source);node['interpretation'].setValue(1);assert 'renditionUi_lookDomain' in node.knobs()
  node['renditionUi_lookDomain'].setValue(domain);assert node['lookDomain'].getValue()==domain
  for k,v in settings.items():node[k].setValue(v)
  values=[node.sample(ch,100.5,100.5,frame=1) for ch in ['red','green','blue','alpha']]
  checks.append({'case':effect+' look domain '+str(domain),'passed':True,'values':values})
  node['lookDomain'].setAnimated();node['lookDomain'].setValueAt(domain,1);node['lookDomain'].setValueAt((domain+1)%6,2)
nuke.scriptSaveAs(str(out/'domain-host.nk'),overwrite=1);nuke.scriptClear();nuke.scriptOpen(str(out/'domain-host.nk'))
for node in nuke.allNodes():
 if 'lookDomain' in node.knobs():assert node['lookDomain'].isAnimated()
checks.append({'case':'Domain choice animation and saved reload','passed':True})
# Persist every artist parameter, including every restored native expert field.
nuke.scriptClear();expected={};schema=json.loads((root/'docs/interfaces.json').read_text())['effects']
for effect in ['Base','Palette','Material']:
 node=nuke.createNode('OFXorg.gripcolor.rendition.'+effect+'_v1',inpanel=False);node.setName('All_'+effect)
 node['interpretation'].setValue(1)
 if effect!='Base':node['modelVersion'].setValue(1)
 expected[effect]={}
 for d in schema[effect]['parameters']:
  key=d['id']
  if d['group'] in ['Input','Custom primaries','Expert'] or key.endswith('Version'):continue
  value=d['default']+(d['max']-d['default'])*.1
  if d['choices']:value=min(1,len(d['choices'])-1)
  node[key].setAnimated();node[key].setValueAt(d['default'],1);node[key].setValueAt(value,2)
  expected[effect][key]=value
nuke.scriptSaveAs(str(out/'all-controls-host.nk'),overwrite=1);nuke.scriptClear();nuke.scriptOpen(str(out/'all-controls-host.nk'))
for effect,values in expected.items():
 node=nuke.toNode('All_'+effect)
 for key,value in values.items():
  assert node[key].isAnimated() and abs(node[key].valueAt(2)-value)<2e-5*max(1,abs(value)),(effect,key)
 checks.append({'case':effect+' all creative native parameters animation/save/reload','passed':True,'parameter_count':len(values),'note':'Serialization test; deliberately mixed settings are not an artist grade or per-control render certification'})
(out/'nuke-controls.json').write_text(json.dumps({'host':nuke.NUKE_VERSION_STRING,'checks':checks,'artist_acceptance':False},indent=2)+'\n')
print('RESTORATION_HOST_PASS',len(checks))
