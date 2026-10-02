"""Package completion evidence only; no OFX binary/equation/model changes."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parents[1];files={}
for folder in [root/'build/spectral-completion']:
 for p in sorted(folder.rglob('*')):
  if p.is_file():files[str(p.relative_to(root))]=p
for name in ['docs/FULL_SPECTRAL_COMPLETION.md','docs/reports/spectral-completion-summary.json','docs/reports/spectral-completion-audit.json','research/spectral_completion.py','research/spectral_completion_report.py','research/full_reference.py','research/spectral_lab.py','research/requirements-lock.txt','tests/test_spectral_completion.py','THIRD_PARTY_REFERENCES.md','SPECTRAL_DATA_SOURCES.md']:
 files[name]=root/name
manifest={'schema_version':1,'purpose':'Offline focused spectral completion evidence; existing production models unchanged','files':{n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()}}
output=root/'build/Rendition-Full-Spectral-Completion.zip'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
 for name,p in sorted(files.items()):z.write(p,'Rendition-Spectral-Completion/'+name)
 z.writestr('Rendition-Spectral-Completion/SHA256-MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(output) as z:
 for n,h in manifest['files'].items():assert hashlib.sha256(z.read('Rendition-Spectral-Completion/'+n)).hexdigest()==h,n
print(output,'verified',len(files),'files;',round(output.stat().st_size/1024**2,2),'MiB')
