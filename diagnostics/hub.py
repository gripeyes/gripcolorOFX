"""Inspector Lab: central local diagnostic report, not automatic grading."""
import json,html,hashlib
import numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
from .common import *
from . import palette,structure,bridge
from .range_tests import CASES
import sys
sys.path.insert(0,str(ROOT/'artist'))
from common import read_scene,Preview
import OpenEXR

def run_images():
    OUT.mkdir(parents=True,exist_ok=True);preview=Preview();rows=[]
    reference_path=ROOT/'build/artist-tests/aces-0004.exr'
    if not reference_path.exists():raise FileNotFoundError('Generate approved explicit Rec.2020 fixtures with artist/sample_frames.py first')
    reference=read_scene(reference_path)[...,:3]
    for num in [5,7,60]:
        path=ROOT/'build/artist-tests'/f'aces-{num:04d}.exr';rgba=read_scene(path);source=rgba[...,:3]
        for effect in ['Density','Crossover','Strip']:
            label,params=CASES[effect][0];candidate=process(effect,source,params)
            tag=f'{effect.lower()}-{num:04d}';a,wa,b,wb,ot,wd=palette.analyze(candidate,reference)
            fig,axes=plt.subplots(1,3,figsize=(15,4.5))
            axes[0].scatter(a[:,1],a[:,2],s=1000*wa,label='Candidate');axes[0].scatter(b[:,1],b[:,2],s=1000*wb,marker='x',label='Approved neon reference')
            for i in range(len(a)):
                for j in range(len(b)):
                    if ot['plan'][i,j]>.002:axes[0].plot([a[i,1],b[j,1]],[a[i,2],b[j,2]],color='grey',alpha=min(.8,ot['plan'][i,j]*8),linewidth=.6)
            axes[0].set(title='Entropic palette correspondences; not a grade',xlabel='Oklab a',ylabel='Oklab b');axes[0].legend(fontsize=8)
            im=axes[1].imshow(ot['plan'],aspect='auto',cmap='viridis');fig.colorbar(im,ax=axes[1]);axes[1].set(title='Coupling mass',xlabel='Reference palette bin',ylabel='Candidate palette bin')
            for rgb,name in [(source,'Source'),(candidate,'Candidate'),(reference,'Reference')]:
                y=rgb@Y;valid=y>0;ev=np.log2(y[valid]/.18);axes[2].hist(ev,bins=np.arange(-14,15),density=True,histtype='step',label=name)
            axes[2].set(title='Scene EV distribution (positive Y only)',xlabel='EV',ylabel='Density');axes[2].legend();fig.tight_layout();fig.savefig(OUT/(tag+'-palette.png'),dpi=135);plt.close(fig)
            gradient,maps=structure.analyze(source,candidate);np.savez_compressed(OUT/(tag+'-structure.npz'),**maps)
            fig,axes=plt.subplots(1,3,figsize=(14,4))
            for ax,(key,title,low,high,cmap) in zip(axes,[('gradient_ratio','log2 luminance gradient ratio',-4,4,'coolwarm'),('luminance_direction','Luminance gradient direction cosine',-1,1,'coolwarm'),('chromatic_direction','Opponent edge direction cosine',-1,1,'coolwarm')]):
                values=np.log2(np.maximum(maps[key],1e-8)) if key=='gradient_ratio' else maps[key]
                values=np.where(maps['valid_chromatic_edges'] if key=='chromatic_direction' else maps['valid_edges'],values,np.nan);im=ax.imshow(values,vmin=low,vmax=high,cmap=cmap);fig.colorbar(im,ax=ax);ax.set_title(title)
            fig.tight_layout();fig.savefig(OUT/(tag+'-structure.png'),dpi=135);plt.close(fig)
            sheet=Image.new('RGB',(1920,385));ImageDraw.Draw(sheet).text((8,3),tag+' | source / candidate / independent reference | Flawed Emulsion 2 / sRGB',(255,255,255))
            for col,rgb in enumerate([source,candidate,reference]):sheet.paste(preview.image(np.concatenate([rgb,np.ones(rgb.shape[:-1]+(1,))],-1)),(640*col,25))
            sheet.save(OUT/(tag+'-view.png'))
            np.savez_compressed(OUT/(tag+'-palette.npz'),candidate_centers=a,candidate_mass=wa,reference_centers=b,reference_mass=wb,plan=ot['plan'])
            row={'source_frame':num,'effect':effect,'parameters':params,'source_encoding':'Explicit scene-linear Rec.2020/D65, RGB as supplied','reference_frame':4,'reference_role':'Approved independent reference; content differs. Distribution distance does not establish reference look quality','sliced_distribution':wd,'candidate_vs_source_distribution':palette.sliced_distance(candidate,source),'transport':{k:v for k,v in ot.items() if k not in ['plan','cost']},'transport_limit':'Entropic coupling cost is regularization-dependent and self-biased, not a metric or an automatic grading transform','structure':gradient,'view':tag+'-view.png','palette_plot':tag+'-palette.png','structure_plot':tag+'-structure.png'}
            rows.append(row)
        guide,data=bridge.build(source,k=8,sigma=.15)
        data['source_alpha']=rgba[...,3];np.savez_compressed(OUT/f'bridge-{num:04d}.npz',**data)
        channels={f'weights.layer{i:02d}':data['weights'][...,i].astype(np.float32) for i in range(guide['layers'])};channels['A']=rgba[...,3].copy()
        OpenEXR.File({'comments':'Experimental data-only soft palette guide; not colour RGB; signed residual and palette in companion NPZ'},channels).write(str(OUT/f'bridge-{num:04d}-weights.exr'))
        fig,axes=plt.subplots(2,4,figsize=(14,7))
        for i,ax in enumerate(axes.flat):
            if i<guide['layers']:ax.imshow(data['weights'][...,i],cmap='gray',vmin=0,vmax=1);ax.set_title('Layer '+str(i))
            ax.axis('off')
        fig.tight_layout();fig.savefig(OUT/f'bridge-{num:04d}.png',dpi=120);plt.close(fig)
        # Frozen palette reuse and exposure changes expose the prototype's limitations explicitly.
        reuse=read_scene(ROOT/'build/artist-tests/aces-0007.exr')[...,:3]
        reuse_report,_=bridge.build(reuse,centers=data['centers_opponent'],sigma=.15)
        exposure=[]
        for stops in [-2,0,2]:
            _,adjusted=bridge.build(source*np.exp2(stops),centers=data['centers_opponent'],sigma=.15)
            exposure.append({'stops':stops,'mean_membership_change':float(np.mean(np.abs(adjusted['weights']-data['weights'])))})
        guide.update({'source_frame':num,'frozen_palette_second_content_reconstruction_error':reuse_report['reconstruction_max_rgb_error'],'exposure_membership_changes':exposure,'exports':'NPZ preserves float64 residual; auxiliary EXR stores float32 data-only weights and unchanged alpha. No processed spatial image is produced.'})
        save(f'bridge-{num:04d}',guide)
    report={'schema_version':1,'gates':['M6','M7','M8/M10'], 'palette_analysis':'Offline reference assistance only; compact scene palettes, stable log-domain balanced entropic transport and sliced 1D W1 projections','structure_analysis':'Linear luminance/opponent spatial derivative diagnostics only; no filtering or processing in core operators','soft_bridge':'Experimental Gaussian overlapping guide fields + explicit signed residual; future Pigment consumer handles spatial operations','cases':rows,'acceptance':'Diagnostic facts only; no palette matching grade or automatic artist acceptance'}
    save('inspector-images',report);return report

def build_index():
    OUT.mkdir(parents=True,exist_ok=True)
    provenance={'schema_version':1,'phase':'0.2 targeted deep validation','creative_equations_changed':False,'input':'Approved ACES fixtures explicitly converted to Rec.2020; external user view Flawed Emulsion 2/sRGB only for previews','modules':['M4 Volume differential','M11 HK oracle','M15–M17 aggressive baselines','M6 palette/OT','M7 structure','M8/M10 guide bridge'],'source_hashes':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['include/rendition/kernel_math.hpp','src/core/diagnostics.cpp','diagnostics/palette.py','diagnostics/structure.py','diagnostics/hk.py','diagnostics/bridge.py']}}
    save('provenance',provenance)
    # Never overwrite an artist's completed observations when regenerating reports.
    review=OUT/'artist-review.json'
    if not review.exists() and (OUT/'creative-range.json').exists():
        cases=json.loads((OUT/'creative-range.json').read_text())['cases']
        save('artist-review',{'phase':'0.2 aggressive-range artist gate','view':'Flawed Emulsion 2 / sRGB','basic_usability':'Accepted by user; this form evaluates stronger creative-range claims','cases':[{'effect':c['effect'],'name':c['name'],'parameters':c['parameters'],'baselines':[b['name'] for b in c['baselines']],'approved_frame':None,'preferred_candidate_or_baseline':None,'useful_behavior_beyond_baseline':None,'coherence_continuity_failures':None,'changed_controls':None,'human_minutes':None,'reuse_on_second_content':None,'source_exposure_stops':None,'expected_vs_observed':None,'status':'Awaiting artist observation'} for c in cases]})
    sections=[('Volume geometry','volume-geometry.png','volume-geometry.json'),('Density HK appearance experiments','density-hk.png','density-hk.json'),('Density creative range','density-trajectories.png','creative-range.json'),('Crossover trajectories','crossover-trajectories.png','creative-range.json'),('Strip creative range','strip-trajectories.png','creative-range.json')]
    body='<h1>Rendition Inspector Lab — 0.2</h1><p>Targeted diagnostics of existing models. Production creative equations unchanged. Reports are measurements, not automatic grades or artist acceptance.</p><nav>'
    for title,_,report in sections:body+=f'<a href="{html.escape(report)}">{html.escape(title)}</a> '
    body+='</nav><p>Native Inspector Volume modes 11–15 analyze one configured family. Offline geometry covers multi-region settings. Red marks fold/collapse, magenta unreliable finite differences. Signed Oklab is an algebraic extension; HK is a separate appearance oracle. Spatial processing stays outside Rendition.</p>'
    for title,plot,report in sections:
        if (OUT/plot).exists():body+=f'<section><h2>{html.escape(title)}</h2><a href="{html.escape(report)}">Structured report</a><img loading="lazy" src="{html.escape(plot)}"></section>'
    image_report=OUT/'inspector-images.json'
    if image_report.exists():
        body+='<h2>Palette and structural preservation</h2><a href="inspector-images.json">All measurements</a>'
        for row in json.loads(image_report.read_text())['cases']:
            body+=f'<details><summary>{html.escape(row["effect"])} / approved frame {row["source_frame"]}</summary>'
            body+=f'<p>OT marginal residual: {row["transport"]["marginal_max_error"]:.3g}; converged: {row["transport"]["converged"]}. Luminance gradient reversal locations: {row["structure"]["gradient_reversal_pixels"]}. Review with the fixed view; these measurements do not decide artist acceptance.</p>'
            for key in ['view','palette_plot','structure_plot']:body+=f'<img loading="lazy" src="{html.escape(row[key])}">'
            body+='</details>'
    body+='<h2>Experimental Pigment guide bridge</h2><p>Overlapping memberships and signed residual, no spatial output filtering or grading. Freeze and version palettes across frames; absolute memberships change with exposure.</p>'
    for num in [5,7,60]:
        if (OUT/f'bridge-{num:04d}.png').exists():body+=f'<details><summary>Guide fields — frame {num}</summary><a href="bridge-{num:04d}.json">Contract / measurements</a><img loading="lazy" src="bridge-{num:04d}.png"></details>'
    body+='<h2>Artist comparisons</h2><a href="artist-review.json">Artist review form (preserved on regeneration)</a><p>Source / fitted simple baseline / candidate. Fits reused unchanged on new content. Record usefulness, control, continuity and interaction time; numerical non-equivalence alone does not prove superiority.</p>'
    for path in sorted(OUT.glob('*-photo-*.png')):body+=f'<details><summary>{html.escape(path.stem)}</summary><img loading="lazy" src="{html.escape(path.name)}"></details>'
    body+='<p><a href="aggressive-stacks.json">Aggressive stack/order report</a> · <a href="provenance.json">Provenance</a></p>'
    document='<!doctype html><html><head><meta charset="utf-8"><title>Rendition Inspector Lab</title><style>body{background:#17191d;color:#ddd;font:16px system-ui;max-width:1450px;margin:24px auto;padding:16px}a{color:#9ac8fa;margin-right:16px}img{width:100%;display:block;margin:14px 0}section,details{background:#22252b;padding:16px;margin:18px 0;border-radius:8px}summary{cursor:pointer}h1,h2{color:#fff}p{line-height:1.5}</style></head><body>'+body+'</body></html>'
    (OUT/'index.html').write_text(document);return OUT/'index.html'

if __name__=='__main__':run_images();print(build_index())
