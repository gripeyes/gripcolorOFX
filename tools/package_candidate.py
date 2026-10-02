"""Package the local research candidate without installing or publishing it."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parents[1]
build=root/'build';bundle=build/'Rendition.ofx.bundle'
if not (bundle/'Contents/MacOS/Rendition.ofx').is_file():raise SystemExit('Build the OFX candidate first')
files={}
for folder in [bundle,root/'docs',build/'fixtures',root/'third_party/licenses',build/'artist-tests',root/'artist',root/'integrations']:
    for source in sorted(folder.rglob('*')):
        if source.is_file() and '__pycache__' not in source.parts and source.suffix not in ('.pyc','.nk~'):
            relative=source.relative_to(build) if source.is_relative_to(build) else source.relative_to(root)
            files[str(relative)]=source
for name in ['README.md','HOST_BEHAVIOR.md','THIRD_PARTY_REFERENCES.md','SPECTRAL_DATA_SOURCES.md','research/requirements-lock.txt','third_party/openfx/LICENSE.md','tools/install_nuke.py','tools/nuke_artist_bench.py']:
    files[name]=root/name
manifest={'schema_version':1,'version':'0.1.2-artist','architecture':'macOS arm64','host_backend':'CPU','production_status':'NOT ACCEPTED; see docs/GATES.md','files':{key:hashlib.sha256(value.read_bytes()).hexdigest() for key,value in sorted(files.items())}}
output=build/'Rendition-0.1.2-artist-arm64.zip'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
    for name,source in sorted(files.items()):
        info=zipfile.ZipInfo('Rendition-artist/'+name,date_time=(2026,10,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(0o755 if source.name=='Rendition.ofx' else 0o644)<<16
        archive.writestr(info,source.read_bytes())
    info=zipfile.ZipInfo('Rendition-artist/SHA256-MANIFEST.json',date_time=(2026,10,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
    archive.writestr(info,json.dumps(manifest,indent=2)+'\n')
print(output)
