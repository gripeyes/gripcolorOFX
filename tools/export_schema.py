"""Export interfaces/semantics directly from authoritative C++ definitions."""
import json
from pathlib import Path
import _rendition as c
names=['Scene','Tone','Volume','Density','Crossover','Crosstalk','Strip','Inspector','Primaries','Base','Palette','Material']
Path('docs/interfaces.json').write_text(json.dumps({'schema_version':1,'effects':{n:{'identifier':'org.gripcolor.rendition.'+n,'effect_version':[1,0],'model_versions':[{'id':0,'name':'v1 research candidate','frozen_production':False}],'external_encoding':'Scene-linear RGB; Inspector diagnostic modes have diagnostic semantics','external_gamut':'Explicit manual interpretation, Nuke OCIO scene_linear role, or recognized scene-linear metadata; no implicit working-gamut conversion','parameters':c.parameters(i),'semantics':c.semantics(i)} for i,n in enumerate(names)}},indent=2)+'\n')

# Runtime presentation metadata needs no Python colour-core dependency in Nuke.
groups={}
for i,name in enumerate(names):
 if name not in ('Base','Palette','Material'):continue
 mapping={}
 for d in c.parameters(i):mapping.setdefault(d['group'],[]).append(d['id'])
 mapping['Expert'].append('semanticReference')
 groups['OFXorg.gripcolor.rendition.'+name+'_v1']=mapping
Path('integrations/nuke/artist-groups.json').write_text(json.dumps(groups,indent=2)+'\n')
