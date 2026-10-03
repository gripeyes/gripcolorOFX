"""Package the 0.32 UX correction candidate; preserve older packages."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parents[1];build=root/'build';files={}
for folder in [build/'Rendition.ofx.bundle',root/'docs',root/'integrations',root/'tests',root/'third_party/licenses']:
 for p in sorted(folder.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.nk~'):
   rel=p.relative_to(build) if p.is_relative_to(build) else p.relative_to(root);files[str(rel)]=p
out=build/'ux-0.32'
for p in sorted(out.rglob('*')):
 if p.is_file() and (p.parent==out and p.name in ('index.html','audit.json','host-checks.json','interactive-fixture.nk') or p.parent.name=='screenshots' and p.stem!='native-capture-test'):
  files[str(p.relative_to(build))]=p
for name in ['README.md','HOST_BEHAVIOR.md','THIRD_PARTY_REFERENCES.md','SPECTRAL_DATA_SOURCES.md','tools/install_nuke.py','tools/nuke_ux32.py','tools/build_ux_report.py','tools/package_ux_correction.py','third_party/openfx/LICENSE.md']:
 files[name]=root/name
manifest={'version':'0.32-ux-correction-candidate','architecture':'macOS arm64 CPU','ux_gate':'pending full Properties/mouse acceptance; presets stopped','compatibility':'Historical models unchanged; bounded model explicit opt-in; defaults not promoted','files':{name:hashlib.sha256(p.read_bytes()).hexdigest() for name,p in sorted(files.items())}}
output=build/'Rendition-0.32-nuke-ux-candidate-arm64.zip'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
 for name,p in sorted(files.items()):z.write(p,'Rendition-artist/'+name)
 z.writestr('Rendition-artist/SHA256-MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(output) as z:
 for name,digest in manifest['files'].items():assert hashlib.sha256(z.read('Rendition-artist/'+name)).hexdigest()==digest
print(output,output.stat().st_size,'bytes; all manifest hashes verified')
