"""M16 bounded authored-node palette rehearsal on approved independent frames.
Palette descriptors are diagnostic; image structure and artist intent require human review.
"""
import json,time,copy
import numpy as np
from scipy.optimize import least_squares
from PIL import Image,ImageDraw
from common import ROOT,SPEC,read_scene,stack,Preview,write_exr,count_controls
OUT=ROOT/'build/artist-tests'
CASES=[('cold_cyan',4,60,7,0),('bronze_olive',14,7,60,1),('near_black',23,60,4,5),('red_accent',7,60,14,3),('low_key_skin',5,7,60,1)]
def descriptor(rgb,preview):
    x=np.ascontiguousarray(rgb,dtype=np.float32).copy()
    import PyOpenColorIO as ocio
    preview.processor.apply(ocio.PackedImageDesc(x,x.shape[1],x.shape[0],3))
    x=np.clip(x.reshape(-1,3).astype(float),0,1)
    # Quantiles include dark/middle/bright relationships; covariance retains some channel relationships.
    return np.r_[np.quantile(x,[.1,.25,.5,.75,.9],axis=0).ravel(),np.cov(x.T).ravel()]
def main():
    preview=Preview();report={'status':'Executed bounded palette reconstruction; artist acceptance pending','references_approved':'Any from ACES_ODT_SampleFrames-main, selected by user authorization','view':SPEC['view'],'metric_limit':'Distribution quantiles/covariance after fixed DRT; no spatial or semantic matching; unrelated content can prevent correspondence','human_interaction_seconds':None,'cases':[]}
    for label,ref,src,hold,idx in CASES:
        recipe=copy.deepcopy(SPEC['targets'][idx]['recipe'])
        # Fit four meaningful colour controls plus scene exposure; all other recipe settings stay authored and explicit.
        if label in ('bronze_olive','low_key_skin'):keys=[(0,'v0_hueDelta',-90,90),(0,'v0_chroma',.1,1.5),(1,'density',0,1),(1,'chromaCoupling',0,1)]
        elif label=='red_accent':keys=[(0,'separation',0,1),(0,'palette',-1,1),(0,'leakage',0,1),(0,'redAnchor',0,1)]
        else:keys=[(0,'darkHue',-90,90),(0,'darkChroma',0,1.5),(0,'darkDensity',-1,1),(0,'transition',.5,4)]
        source=read_scene(OUT/f'aces-{src:04d}.exr');reference=read_scene(OUT/f'aces-{ref:04d}.exr');heldout=read_scene(OUT/f'aces-{hold:04d}.exr')
        sample=source[::12,::12].copy();target=descriptor(reference[::12,::12,:3],preview)
        def set_params(a):
            for (node,key,_,_),v in zip(keys,a):recipe[node]['parameters'][key]=float(v)
        def objective(a):set_params(a);return descriptor(stack(sample,recipe)[...,:3],preview)-target
        recipe.insert(0,{'effect':'Scene','parameters':{'exposure':0}})
        keys=[(0,'exposure',-6,2)]+[(n+1,k,lo,hi) for n,k,lo,hi in keys]
        initial=[recipe[n]['parameters'][k] for n,k,_,_ in keys];start=time.perf_counter()
        # Float32 CPU equations require an explicit finite difference step.
        def jacobian(a):
            columns=[]
            for k,(_,key,lo,hi) in enumerate(keys):
                step=.25 if 'Hue' in key else .01
                low=a.copy();high=a.copy();low[k]=max(lo,a[k]-step);high[k]=min(hi,a[k]+step)
                columns.append((objective(high)-objective(low))/(high[k]-low[k]))
            return np.stack(columns,axis=1)
        fit=least_squares(objective,initial,jac=jacobian,bounds=([v[2] for v in keys],[v[3] for v in keys]),max_nfev=40)
        set_params(fit.x);seconds=time.perf_counter()-start
        output=stack(source,recipe);reuse=stack(heldout,recipe)
        for tag,data in [('candidate',output),('heldout',reuse)]:
            assert np.isfinite(data).all();write_exr(OUT/(label+'-'+tag+'.exr'),data)
        sheet=Image.new('RGB',(1920,760));draw=ImageDraw.Draw(sheet)
        for col,(title,img) in enumerate([('Approved reference',reference),('Source',source),('Authored fit',output)]):sheet.paste(preview.image(img),(640*col,25));draw.text((640*col+8,4),title,(255,255,255))
        sheet.paste(preview.image(heldout),(640,395));sheet.paste(preview.image(reuse),(1280,395));draw.text((8,405),'Second content: unchanged recipe',(255,255,255));sheet.save(OUT/(label+'-reconstruction.png'))
        report['cases'].append({'id':label,'reference_frame':ref,'source_frame':src,'heldout_frame':hold,'recipe':copy.deepcopy(recipe),**count_controls(recipe),'solver_seconds':seconds,'solver_evaluations':fit.nfev,'solver_converged':bool(fit.success),'palette_descriptor_rms':float(np.sqrt(np.mean(fit.fun**2))),'same_recipe_on_second_content':True,'nonfinite':0,'human_interaction_seconds':None,'artist_success':None,'fitting_scope':'Five existing creative controls; no LUT, mask, stock look or extra production operator'})
    (OUT/'reference-reconstruction.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Completed five approved-reference palette rehearsals')
if __name__=='__main__':main()
