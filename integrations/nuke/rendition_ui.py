"""Nuke presentation fallback for OFX pages/groups not presented by Nuke 17.
Link_Knob references native persistent OFX state. This module never writes grades.
"""
import json
from pathlib import Path
import nuke
_SCHEMA=json.loads(Path(__file__).with_name('artist-groups.json').read_text())
_busy=False
_ui_signatures={}
_family_links={}
_FAMILIES=('Red','Yellow','Green','Cyan','Blue','Magenta')

def page(group,key):
 if group in ('Input','Custom primaries','Expert') or key.endswith('Version') or key=='semanticReference':return 'Input / Compatibility'
 if key.startswith('Volume_v'):return 'Families'
 if key.startswith('Crossover_'):return 'Advanced' if group.endswith('Selection') else 'Trajectory'
 if key.startswith('Crosstalk_'):return 'Crosstalk'
 if key.startswith('Density_'):return 'Density'
 if key.startswith('Strip_'):return 'Strip'
 if group=='Local exposure':return 'Dodge-Burn'
 if group=='Advanced tonal colour':return 'Advanced' if key in ('highlightBurn','highlightBleach','brillianceReduction','midExposure','midDensity','midChroma') else 'Tonal Colour / Ranges'
 return 'Advanced'

def _value(node,key,default=0):
 k=node.knobs().get(key)
 return k.getValue() if k is not None else default

def update(node):
 """Properties only: no value rewriting, proxy synchronization or processing."""
 version=_value(node,'modelVersion')
 artist=node.Class().split('.')[-1].split('_')[0]
 legacy=artist in ('Palette','Material') and version==0
 family=int(_value(node,'editFamily'))
 for group,keys in _SCHEMA.get(node.Class(),{}).items():
  for key in keys:
   target=node.knobs().get(key);link=node.knobs().get('renditionUi_'+key)
   if target is None:continue
   visible=True;enabled=True
   if key in ('rx','ry','gx','gy','bx','by','wx','wy'):
    visible=int(_value(node,'interpretation'))==4;enabled=visible
   if key.endswith('Version') or key=='semanticReference':visible=False;enabled=False
   child=key.startswith(('Volume_','Crossover_','Crosstalk_','Density_','Strip_'))
   if legacy and child:enabled=False
   if key.startswith('Volume_v'):visible=False # Historical aliases remain addressable, outside the reusable editor.
   if key=='pivot':enabled=any(_value(node,k,d)!=d for k,d in (('contrast',1),('shadowCompression',0),('highlightCompression',0),('midExposure',0),('midDensity',0),('blackStops',0),('whiteLevel',0),('colourBalance',0),('brillianceReduction',0),('highlightBurn',0)))
   if artist=='Base' and key=='shadowHue':enabled=_value(node,'shadowTint')!=0
   if artist=='Base' and key=='highlightHue':enabled=_value(node,'highlightTint')!=0
   if key in ('deathStart','deathSoftness'):enabled=_value(node,'colourDeath')!=0
   if key in ('localProtection','localChroma'):enabled=_value(node,'localExposure')!=0
   if key in ('localCenter','localSoftness'):enabled=_value(node,'localExposure')!=0 and _value(node,'localProtection')!=0
   if artist=='Material' and key=='coupling':enabled=_value(node,'density')!=0 or (not legacy and _value(node,'Density_density')!=0)
   if artist=='Material' and key in ('leakage','anchor'):enabled=_value(node,'depth')!=0 or _value(node,'separation')!=0 or (not legacy and _value(node,'Strip_separation')!=0)
   if key=='Crossover_lookDomain':enabled=not legacy and _value(node,'Crossover_mode')==1
   if key=='Crosstalk_lookDomain':enabled=not legacy and _value(node,'Crosstalk_domain')==1
   if key=='Crosstalk_rowSum':enabled=not legacy and _value(node,'Crosstalk_mode')==2
   if key.startswith('Density_') and key not in ('Density_density','Density_debug'):enabled=not legacy and (_value(node,'density')!=0 or _value(node,'Density_density')!=0)
   if (key.startswith('Strip_m') and key[-2:].isdigit()):enabled=not legacy and _value(node,'Strip_mode')==2
   if key in ('Strip_leakage','Strip_density','Strip_palette','Strip_neutralAnchor','Strip_redAnchor'):enabled=not legacy and any(_value(node,k)!=0 for k in ('depth','separation','Strip_separation'))
   if key.startswith('Volume_v') and key.endswith('_matrixMix'):
    prefix=key.rsplit('_',1)[0]+'_'
    enabled=not legacy and any(_value(node,prefix+'m'+str(r)+str(c),1 if r==c else 0)!=(1 if r==c else 0) for r in range(3) for c in range(3))
   if key=='Crosstalk_mix':enabled=not legacy and (any(_value(node,'Crosstalk_m'+str(r)+str(c),1 if r==c else 0)!=(1 if r==c else 0) for r in range(3) for c in range(3)) or any(_value(node,k)!=0 for k in ('crosstalk','contamination','Crosstalk_rg','Crosstalk_rb','Crosstalk_gr','Crosstalk_gb','Crosstalk_br','Crosstalk_bg')))
   if key.startswith('Crossover_') and group.endswith('Channels'):visible=_value(node,'Crossover_mode')==1
   if key.startswith('Crossover_') and any(s in key for s in ('Hue','Chroma','Density')):visible=_value(node,'Crossover_mode')==0
   if artist in ('Palette','Material') and version==1 and group not in ('Input','Custom primaries'):enabled=False
   # Link_Knob presentation flags do not reliably disable the native editor.
   target.setEnabled(enabled)
   if link is not None:link.setEnabled(enabled)
   if link is not None:link.setVisible(visible)
   elif group=='Artist':target.setVisible(visible)
 if artist=='Palette':
  if _family_links.get(node.fullName())!=family:
   for key in node.knobs():
    if not key.startswith('renditionUiFamily_'):continue
    source='Volume_v'+str(family)+'_'+key[len('renditionUiFamily_'):]
    node.knobs()[key].makeLink('this',source)
   _family_links[node.fullName()]=family
  for key in node.knobs():
   if key.startswith('renditionUiFamily_'):
    source='Volume_v'+str(family)+'_'+key[len('renditionUiFamily_'):]
    node.knobs()[key].setEnabled(node[source].enabled())
 if artist=='Base':
  for key,lo,hi in (('toeStart',-20,min(4,_value(node,'shoulderStart'))),('shoulderStart',max(-4,_value(node,'toeStart')),20),('shadowRange',-20,min(4,_value(node,'highlightRange'))),('highlightRange',max(-4,_value(node,'shadowRange')),20)):
   k=node.knobs().get(key)
   if k is not None:k.setRange(lo,hi)
 status=node.knobs().get('renditionUi_compatibility')
 if status is not None:
  status.setValue('Base: preserved monotonic tone.' if artist=='Base' else ('Legacy macros (0.3): deeper controls are inactive.' if version==0 else 'Legacy grade (0.31): read-only; enable full controls to edit safely.' if version==1 else 'Full controls: bounded Main/Expert interaction.'))
 migrate=node.knobs().get('renditionUi_enableFullControls')
 if migrate is not None:migrate.setVisible(artist in ('Palette','Material') and version!=2)


def refresh(node=None):
 global _busy
 if _busy:return
 _busy=True
 try:
  for node in ([node] if node is not None else nuke.allNodes(recurseGroups=True)):
   groups=_SCHEMA.get(node.Class())
   if not groups:continue
   artist=node.Class().split('.')[-1].split('_')[0]
   if artist not in ('Base','Palette','Material'):
    import rendition_legacy_ui
    rendition_legacy_ui.refresh(node)
    continue # Keep the existing historical linked presentation.
   # Remove only old presentation aliases; never remove native OFX parameters.
   if 'renditionUi_layout032d' not in node.knobs():
    for k in list(node.allKnobs()):
     if k.name().startswith(('renditionUi_','renditionUiTab_')):node.removeKnob(k)
   # Nuke emits unnamed end-group tabs. Hidden opening groups otherwise
   # leave their end markers reserving blank space before Main.
   for native in node.allKnobs():
    if native.Class()=='Tab_Knob' and not native.name() and native.label()!='Node':native.setVisible(False)
   pages={}
   for group,keys in groups.items():
    native=node.knobs().get(group)
    if native is not None:
     native.setVisible(group=='Artist')
     if group=='Artist':native.setLabel('Main')
    for key in keys:
     target=node.knobs().get(key)
     if target is None:continue
     target.setVisible(group=='Artist')
     if group!='Artist':pages.setdefault('Input / Compatibility' if key.startswith('Volume_v') else page(group,key),[]).append(key)
   if artist=='Palette':pages['Families']=['editFamily']
   if artist!='Base':pages.setdefault('Input / Compatibility',[]).append('enableFullControls')
   order={'Base':('Tonal Colour / Ranges','Dodge-Burn','Advanced','Input / Compatibility'),'Palette':('Families','Trajectory','Crosstalk','Advanced','Input / Compatibility'),'Material':('Density','Strip','Crosstalk','Advanced','Input / Compatibility')}[artist]
   for label in order:
    keys=pages.get(label,[])
    if label=='Crosstalk':
     first=('Crosstalk_mode','Crosstalk_domain','Crosstalk_lookDomain','Crosstalk_rowSum')
     keys=[k for k in first if k in keys]+[k for k in keys if k not in first]
    if not keys:continue
    tab='renditionUiTab_'+label.replace(' / ','_').replace(' ','_').replace('-','_')
    if tab not in node.knobs():node.addKnob(nuke.Tab_Knob(tab,label))
    if label=='Input / Compatibility' and 'renditionUi_compatibility' not in node.knobs():node.addKnob(nuke.Text_Knob('renditionUi_compatibility','Compatibility',''))
    for key in keys:
     if key=='semanticReference':continue
     target=node.knobs().get(key)
     if target is None:continue
     alias='renditionUi_'+key
     target.setVisible(False)
     if alias in node.knobs():continue
     caption=target.label()
     if key.startswith('Volume_v'):caption=caption.replace(' displacement',' shift')
     if key in ('rx','ry','gx','gy','bx','by','wx','wy'):caption=key[0].upper()+' '+key[1]
     if (key.startswith('Strip_m') and key[-2:].isdigit()):caption=('Record '+str(int(key[-2])+1)+' gain' if key[-2]==key[-1] else 'Record '+str(int(key[-2])+1)+' from '+str(int(key[-1])+1))
     if key in ('rx','ry','gx','gy','bx','by','wx','wy') or (key.startswith('Volume_v') and '_m' in key) or (key.startswith(('Crosstalk_m','Strip_m')) and key[-2:].isdigit()):target.clearFlag(0x2)
     link=nuke.Link_Knob(alias,caption);node.addKnob(link);link.makeLink('this',key)
     if key.startswith('Volume_v') and '_m' in key or key.startswith(('Crosstalk_m','Strip_m')) and key[-2:].isdigit():
      link.clearFlag(0x2) # SLIDER: installed Nuke 17 DDImage/Knob.h numeric flag
      if key[-1]!='0':link.clearFlag(nuke.STARTLINE)
    if label=='Families':
     for group,familyKeys in groups.items():
      for key in familyKeys:
       if not key.startswith('Volume_v0_'):continue
       alias='renditionUiFamily_'+key[len('Volume_v0_'):]
       if alias in node.knobs():continue
       target=node[key];caption=target.label().replace(' displacement',' shift')
       if '_m' in key and key[-2:].isdigit():target.clearFlag(0x2)
       link=nuke.Link_Knob(alias,caption);node.addKnob(link);link.makeLink('this',key)
       if '_m' in key and key[-2:].isdigit() and key[-1]!='0':link.clearFlag(nuke.STARTLINE)
   if artist=='Palette':
    for key in ('Crossover_mode' ,'Crossover_darkPivot','Crossover_brightPivot','Crossover_transition'):
     alias='renditionUi_Channel_'+key
     if alias not in node.knobs() and key in node.knobs():
      link=nuke.Link_Knob(alias,'');node.addKnob(link);link.makeLink('this',key);link.setVisible(False)
   if 'renditionUi_layout032d' not in node.knobs():
    marker=nuke.Text_Knob('renditionUi_layout032d','','');marker.setVisible(False);node.addKnob(marker)
   if artist=='Palette':_family_links.pop(node.fullName(),None)
   update(node)
 except ValueError as error:
  nuke.tprint("Rendition UI presentation: "+str(error))
  return
 finally:_busy=False

def idle_update():
 global _busy
 if _busy:return
 for node in nuke.allNodes(recurseGroups=True):
  if 'renditionUi_layout032d' not in node.knobs():continue
  keys=('modelVersion','editFamily','interpretation','density','depth','separation','Density_density','Strip_mode','Strip_separation','Crossover_mode','Crosstalk_mode','Crosstalk_domain','localExposure','localProtection','colourDeath','shadowTint','highlightTint','contrast','shadowCompression','highlightCompression','toeStart','shoulderStart','shadowRange','highlightRange')
  keys+=tuple('Crosstalk_m'+str(r)+str(c) for r in range(3) for c in range(3))
  keys+=tuple('Volume_v'+str(f)+'_m'+str(r)+str(c) for f in range(6) for r in range(3) for c in range(3))
  keys+=('crosstalk','contamination','midExposure','midDensity','blackStops','whiteLevel','colourBalance','brillianceReduction','highlightBurn')
  signature=(nuke.frame(),)+tuple(_value(node,k) for k in keys)
  if _ui_signatures.get(node.fullName())==signature:continue
  _ui_signatures[node.fullName()]=signature
  _busy=True
  try:update(node)
  finally:_busy=False

def created():refresh(nuke.thisNode())
def changed():
 global _busy
 if _busy:return
 node=nuke.thisNode()
 try:
  if node.Class().split('.')[-1].split('_')[0] not in ('Base','Palette','Material'):return
 except ValueError:return
 _busy=True
 try:
  key=nuke.thisKnob().name()
  relevant={'showPanel','inputChange','modelVersion','editFamily','interpretation','contrast','shadowCompression','highlightCompression','midExposure','midDensity','blackStops','whiteLevel','colourBalance','brillianceReduction','highlightBurn','shadowTint','highlightTint','colourDeath','localExposure','localProtection','density','depth','separation','Crossover_mode','Crosstalk_mode','Crosstalk_domain','Density_density','Strip_separation'}
  if key.startswith('renditionUi_'):key=key[len('renditionUi_'):]
  if key.startswith('renditionUiFamily_'):key='Volume_v'+str(int(_value(node,'editFamily')))+'_'+key[len('renditionUiFamily_'):]
  if key in relevant or key.startswith('Crosstalk_m') or (key.startswith('Volume_v') and '_m' in key):update(node)
 except ValueError:return
 finally:_busy=False

if not Path(__file__).with_name('native-ui-probe').exists():
 nuke.addOnCreate(created)
 nuke.addOnScriptLoad(refresh)
 nuke.addKnobChanged(changed)
 nuke.addUpdateUI(idle_update)
 refresh()
