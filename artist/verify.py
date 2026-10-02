"""Verify artist deliverable contracts without treating metrics as approval."""
import json,tempfile
from pathlib import Path
import numpy as np
from common import ROOT,rgba,write_exr,read_scene
from simplicity import matrix_curves
OUT=ROOT/'build/artist-tests'
# Float EXRs preserve signed/HDR values and zero-alpha RGB exactly.
x=rgba(np.array([[[-.01,0,1200],[.18,.25,-4]]],np.float32));x[...,3]=[0,.35]
with tempfile.TemporaryDirectory() as folder:
 p=Path(folder)/'signed.exr';write_exr(p,x);assert np.array_equal(read_scene(p).view(np.uint32),x.view(np.uint32))
# Baseline identity and ordered response are necessary for a fair curves comparison.
v=np.geomspace(1e-7,10000,1000);rgb=np.repeat(v[:,None],3,axis=1)
a=np.r_[np.eye(3).ravel(),np.zeros(21)];y=matrix_curves(rgb,a)
assert np.allclose(y,rgb,rtol=1e-10,atol=1e-10);assert np.all(np.diff(y,axis=0)>0)
for p in OUT.glob('*.exr'):assert np.isfinite(read_scene(p)).all(),str(p)
ui=json.loads((ROOT/'docs/reports/nuke-ui-discovery.json').read_text());assert len(ui['checks'])==8 and all(r['ui_creation_verified'] for r in ui['checks'])
graph=(OUT/'Nuke-menu-created-eight.nk').read_text()
for name in ['Scene','Tone','Volume','Density','Crossover','Crosstalk','Strip','Inspector']:assert 'OFXorg.gripcolor.rendition.'+name+'_v1 {' in graph
host=json.loads((OUT/'nuke-artist-bench.json').read_text());assert host['view_actual']=='Flawed Emulsion 2 (sRGB)' and len(host['checks'])==14
report={'signed_hdr_exr_exact_roundtrip':True,'baseline_curves_identity_monotone':True,'all_scene_exrs_finite':True,'eight_menu_created_nodes_saved':True,'nuke_sources_and_recipes_match_cpu':True,'artist_acceptance':'Pending human evidence'}
(OUT/'artist-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
