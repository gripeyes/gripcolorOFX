"""Export interfaces/semantics directly from authoritative C++ definitions."""
import json
from pathlib import Path
import _rendition as c
names=['Scene','Tone','Volume','Density','Crossover','Crosstalk','Strip','Inspector']
Path('docs/interfaces.json').write_text(json.dumps({'schema_version':1,'effects':{n:{'identifier':'org.gripcolor.rendition.'+n,'effect_version':[1,0],'model_versions':[{'id':0,'name':'v1 research candidate','frozen_production':False}],'external_encoding':'Scene-linear RGB; Inspector diagnostic modes have diagnostic semantics','external_gamut':'Explicit manual interpretation or recognized scene-linear metadata; no implicit working-gamut conversion','parameters':c.parameters(i),'semantics':c.semantics(i)} for i,n in enumerate(names)}},indent=2)+'\n')
