"""Package the 0.31 CPU control-restoration candidate without overwriting 0.3."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parents[1];build=root/'build';files={}
for folder in [build/'Rendition.ofx.bundle',root/'docs',root/'integrations',root/'artist',root/'tests',build/'control-audit-0.31',root/'third_party/licenses']:
 for p in sorted(folder.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.nk~'):
   rel=p.relative_to(build) if p.is_relative_to(build) else p.relative_to(root);files[str(rel)]=p
for name in ['README.md','HOST_BEHAVIOR.md','THIRD_PARTY_REFERENCES.md','SPECTRAL_DATA_SOURCES.md','tools/install_nuke.py','tools/nuke_control_restoration.py','research/requirements-lock.txt','third_party/openfx/LICENSE.md']:
 files[name]=root/name
for number in [5,60]:files[f'artist-tests/aces-{number:04d}.exr']=build/f'artist-tests/aces-{number:04d}.exr'
manifest={'version':'0.31-control-restoration-candidate','architecture':'macOS arm64 CPU','recipe_gate':'pending artist-control acceptance; no recipes authored','historical_model':'Palette/Material index 0 preserved; index 1 explicit restored controls; Base unchanged','files':{name:hashlib.sha256(p.read_bytes()).hexdigest() for name,p in sorted(files.items())}}
output=build/'Rendition-0.31-control-restoration-arm64.zip'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
 for name,p in sorted(files.items()):z.write(p,'Rendition-artist/'+name)
 z.writestr('Rendition-artist/SHA256-MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(output) as z:
 for name,digest in manifest['files'].items():assert hashlib.sha256(z.read('Rendition-artist/'+name)).hexdigest()==digest
print(output,output.stat().st_size,'bytes; all manifest hashes verified')
