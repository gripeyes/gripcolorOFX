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
   for group,children in groups.items():
    if group in ('Artist','Input'):continue
    native=node.knobs().get(group)
    if native is not None:native.setVisible(False)
    for key in children:
     target=node.knobs().get(key)
     if target is not None:target.setVisible(False)
    label='Expert' if group in ('Custom primaries','Expert') else ('Dodge / Burn' if group=='Local exposure' else 'Advanced')
    tab_id='renditionUiTab_'+label.replace(' / ','_')
    if tab_id not in node.knobs():node.addKnob(nuke.Tab_Knob(tab_id,label))
    for key in children:
     target=node.knobs().get(key)
     if target is None:continue
     alias='renditionUi_'+key
     if alias not in node.knobs():
      link=nuke.Link_Knob(alias,target.label());node.addKnob(link);link.makeLink('this',key)
 except ValueError:return # Detached-node shutdown notifications.
 finally:_busy=False

def created():refresh(nuke.thisNode())
nuke.addOnCreate(created)
nuke.addOnScriptLoad(refresh)

refresh()
