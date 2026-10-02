"""Artist-test IO and explicit scene/preview separation; no OFX runtime dependencies."""
from pathlib import Path
import json
import numpy as np
import OpenEXR
import PyOpenColorIO as ocio
from PIL import Image
import _rendition as core

ROOT=Path(__file__).resolve().parents[1]
NAMES=['Scene','Tone','Volume','Density','Crossover','Crosstalk','Strip','Inspector','Primaries']
SPEC=json.loads((ROOT/'artist/targets.json').read_text())

def rgba(rgb):
    rgb=np.asarray(rgb,dtype=np.float32)
    return np.concatenate([rgb,np.ones(rgb.shape[:-1]+(1,),np.float32)],axis=-1)

def process(effect,image,parameters=None):
    return core.process(NAMES.index(effect),np.ascontiguousarray(image,dtype=np.float32),{'interpretation':1,**(parameters or {})})

def stack(image,recipe):
    result=image.copy()
    for node in recipe:result=process(node['effect'],result,node['parameters'])
    return result

def write_exr(path,image):
    image=np.ascontiguousarray(image,dtype=np.float32)
    OpenEXR.File({'comments':'Scene-linear Linear Rec.2020 / RGB as supplied; explicit interpretation required'},
                 {key:image[...,i].copy() for i,key in enumerate('RGBA')}).write(str(path))

def read_scene(path):
    path=Path(path)
    if path.suffix=='.npy':result=np.load(path,allow_pickle=False)
    elif path.suffix.lower()=='.exr':
        channels=OpenEXR.File(str(path),separate_channels=True).channels()
        result=np.stack([channels[key].pixels for key in 'RGB'],-1)
        result=np.concatenate([result,channels['A'].pixels[...,None] if 'A' in channels else np.ones(result.shape[:-1]+(1,))],-1)
    else:raise ValueError('Source must be explicitly interpreted scene-linear EXR or float32 RGBA .npy')
    if result.ndim!=3 or result.shape[-1]!=4 or result.dtype!=np.float32:raise ValueError('Expected float32 RGBA image')
    if not np.all(np.isfinite(result)):raise ValueError('Nonfinite scene input; inspect explicitly before the artist challenge')
    return result

class Preview:
    def __init__(self):
        config=ocio.Config.CreateFromFile(SPEC['ocio_config'])
        self.processor=config.getProcessor(ocio.DisplayViewTransform(src='Linear Rec.2020',display=SPEC['display'],view=SPEC['view'])).getDefaultCPUProcessor()
    def image(self,image):
        rgb=np.ascontiguousarray(image[...,:3],dtype=np.float32)
        desc=ocio.PackedImageDesc(rgb,rgb.shape[1],rgb.shape[0],3)
        self.processor.apply(desc)
        # Clipping is limited to PNG preview export after the explicitly selected DRT.
        return Image.fromarray(np.uint8(np.clip(rgb,0,1)*255+.5))
    def write(self,path,image):self.image(image).save(path)

def count_controls(recipe):
    result=[]
    for node in recipe:
        definitions={p['id']:p['default'] for p in core.parameters(NAMES.index(node['effect']))}
        changed=[key for key,value in node['parameters'].items() if key not in ('interpretation','alphaMode','modelVersion','adapterVersion') and value!=definitions[key]]
        result.append({'effect':node['effect'],'changed_controls':changed,'count':len(changed)})
    return {'nodes':len(recipe),'changed_creative_controls':sum(row['count'] for row in result),'details':result}
