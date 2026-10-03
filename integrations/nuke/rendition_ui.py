"""Nuke artist presentation. Link controls invoke original OFX parameters directly.
No processing state, colour algorithms or interpretation decisions live here.
"""
import json
from pathlib import Path
import nuke
_SCHEMA=json.loads(Path(__file__).with_name('artist-groups.json').read_text())
_busy=False

def refresh(node=None):
 global _busy
 if _busy:return
 _busy=True
 try:
  nodes=[node] if node is not None else nuke.allNodes(recurseGroups=True)
  for node in nodes:
   groups=_SCHEMA.get(node.Class())
   if not groups:continue
   pages={}
   for group,children in groups.items():
    if group in ('Artist','Input'):continue
    native=node.knobs().get(group)
    if native is not None:native.setVisible(False)
    for key in children:
     target=node.knobs().get(key)
     if target is not None:target.setVisible(False)
    if group.startswith('Families / '):label='Families'
    elif group.startswith('Trajectory / '):label='Channel Trajectory' if group.endswith('Channels') else 'Trajectory'
    elif group.startswith('Crosstalk Matrix / '):label='Crosstalk Matrix'
    elif group.startswith('Density / '):label='Density'
    elif group.startswith('Strip / '):label='Strip'
    else:label='Expert' if group in ('Custom primaries','Expert') else ('Dodge / Burn' if group=='Local exposure' else 'Advanced')
    pages.setdefault(label,[]).extend(children)
   if 'Trajectory' in pages and 'Crossover_lookDomain' in pages['Trajectory']:
    pages['Trajectory'].remove('Crossover_lookDomain')
    pages.setdefault('Channel Trajectory',[]).insert(0,'Crossover_lookDomain')
   for label,children in pages.items():
    tab_id='renditionUiTab_'+label.replace(' / ','_').replace(' ','_')
    if tab_id not in node.knobs():node.addKnob(nuke.Tab_Knob(tab_id,label))
    hint_id=tab_id+'_hint'
    if label in ('Families','Trajectory','Channel Trajectory','Crosstalk Matrix','Density','Strip') and hint_id not in node.knobs():
     node.addKnob(nuke.Text_Knob(hint_id,'','Select v2 restored controls in Expert. Main macros compose with this state.'))
    if label=='Channel Trajectory':
     for key,caption in [('Crossover_mode','Trajectory mode (shared with hue trajectory)'),('Crossover_darkPivot','Dark transition center'),('Crossover_brightPivot','Bright transition center'),('Crossover_transition','Transition softness')]:
      alias='renditionUi_Channel_'+key
      if key in node.knobs() and alias not in node.knobs():
       link=nuke.Link_Knob(alias,caption);node.addKnob(link);link.makeLink('this',key)
    for key in children:
     target=node.knobs().get(key)
     if target is None:continue
     alias='renditionUi_'+key
     if alias not in node.knobs():
      caption='Channel encoding (channel mode only)' if key=='Crossover_lookDomain' else target.label()
      if key.startswith('Volume_v'):
       family=['Red','Yellow','Green','Cyan','Blue','Magenta'][int(key.split('_')[1][1:])]
       caption=family+' / '+caption
      link=nuke.Link_Knob(alias,caption);node.addKnob(link);link.makeLink('this',key)
 except ValueError:return # Detached-node shutdown notifications.
 finally:_busy=False

def created():refresh(nuke.thisNode())
nuke.addOnCreate(created)
nuke.addOnScriptLoad(refresh)

refresh()
