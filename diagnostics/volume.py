"""M4: central differences of actual configured CPU equations; no invertibility claim."""
import numpy as np
from .common import *
CASES={
 'identity':{},
 'artist_overlap':{'v0_width':150,'v0_hueDelta':35,'v0_chroma':.6,'v5_width':150,'v5_hueDelta':-25,'v5_chroma':1.3},
 'aggressive_overlap':{'v0_width':240,'v0_hueDelta':120,'v0_chroma':.1,'v0_density':.7,'v5_width':240,'v5_hueDelta':-120,'v5_chroma':3,'v5_density':-.5},
 'aggressive_bounded':{'overlap':2,'v0_width':240,'v0_hueDelta':120,'v0_chroma':.1,'v0_density':.7,'v5_width':240,'v5_hueDelta':-120,'v5_chroma':3,'v5_density':-.5},
 'collapse_probe':{'v0_width':360,'v0_chroma':0,'v0_neutral':0}}
def run():
    OUT.mkdir(parents=True,exist_ok=True);rgb,ev,hue,chroma,shape=structured()
    rng=np.random.default_rng(402);signed=rng.normal(size=(1024,3))*np.exp2(rng.uniform(-12,12,(1024,1)))
    samples=np.concatenate([rgb,signed.astype(np.float32)],axis=0)
    report={'schema_version':1,'gate':'M4','coordinate_metric':'Derivative RGB->RGB in external Linear Rec.2020; not a perceptual metric','algorithm':'Central differences at h and h/2, h=.002*max(abs RGB,0.18). Jacobi SVD via J^T J. Step disagreement >5% is unreliable; no absence-of-fold proof from finite sampling.','structured_samples':len(rgb),'signed_samples':len(signed),'thresholds':{'condition_warning':100,'stretch_warning':4,'compression_warning':.25,'reliable_relative_step_error':.05},'cases':[]}
    fig,axes=plt.subplots(len(CASES),2,figsize=(14,3*len(CASES)))
    for row,(name,params) in enumerate(CASES.items()):
        d=core.differentials(2,samples,{'interpretation':1,**params},.002)
        j=d[:,:9].reshape(-1,3,3);sv=np.linalg.svd(j,compute_uv=False)
        sv_error=float(np.max(np.abs(d[:,10:13]-sv)/(1+sv)))
        determinant_error=float(np.max(np.abs(d[:,9]-np.linalg.det(j))/(1+np.abs(d[:,9]))))
        if sv_error>1e-6 or determinant_error>1e-10:raise AssertionError('Independent NumPy SVD/determinant mismatch')
        reliable=d[:,15]>0;fold=(d[:,9]<=0)&reliable;near=(d[:,12]<1e-4)&reliable
        item={'name':name,'parameters':params,'reliable_samples':int(reliable.sum()),'unreliable_samples':int((~reliable).sum()),'reliable_fold_or_collapse_samples':int(fold.sum()),'reliable_near_singular_samples':int(near.sum()),'determinant':finite_summary(d[reliable,9]),'singular_values':[finite_summary(d[reliable,i]) for i in [10,11,12]],'condition':finite_summary(d[reliable,13]),'maximum_expansion':finite_summary(d[reliable,10]),'minimum_local_scale':finite_summary(d[reliable,12]),'max_compression_ratio':finite_summary(np.divide(1,d[reliable,12],out=np.full_like(d[reliable,12],np.inf),where=d[reliable,12]>1e-12)),'numpy_svd_scaled_max_error':sv_error,'numpy_determinant_scaled_max_error':determinant_error,'family_exposure':[]}
        for family,center in [('red',29),('yellow',110),('green',145),('cyan',195),('blue',265),('magenta',325)]:
            mask_h=np.abs((hue-center+180)%360-180)<30
            for exposure in np.unique(ev):
                mask=np.r_[mask_h&(ev==exposure),np.zeros(len(signed),bool)]
                good=mask&reliable
                item['family_exposure'].append({'family':family,'ev':float(exposure),'samples':int(mask.sum()),'reliable_fraction':float(good.sum()/max(mask.sum(),1)),'fold_or_collapse':int((fold&mask).sum()),'condition':finite_summary(d[good,13]),'determinant':finite_summary(d[good,9])})
        # Save every local derivative, with coordinates/labels, not just a global score.
        np.savez_compressed(OUT/(name+'-jacobians.npz'),rgb=samples,jacobian=j,determinant=d[:,9],singular_values=sv,condition=d[:,13],step_error=d[:,14],reliable=reliable,structured_ev=ev,structured_hue=hue,structured_chroma=chroma)
        select=(chroma==.25);grid_det=d[:len(rgb),9][select].reshape(shape[0],shape[2]);grid_condition=d[:len(rgb),13][select].reshape(shape[0],shape[2])
        valid=d[:len(rgb),15][select].reshape(shape[0],shape[2])>0
        det_map=np.ma.array(np.clip(grid_det,-2,4),mask=~valid)
        condition_map=np.ma.array(np.log10(np.maximum(grid_condition,1)),mask=~valid)
        det_cmap=plt.get_cmap('coolwarm').copy();det_cmap.set_bad('#d658d6')
        condition_cmap=plt.get_cmap('magma').copy();condition_cmap.set_bad('#d658d6')
        im=axes[row,0].imshow(det_map,origin='lower',aspect='auto',extent=[0,360,-12,12],cmap=det_cmap,vmin=-2,vmax=4);fig.colorbar(im,ax=axes[row,0]);axes[row,0].set(title=name+' determinant, C/|L|=.25',xlabel='Hue degrees',ylabel='EV')
        im=axes[row,1].imshow(condition_map,origin='lower',aspect='auto',extent=[0,360,-12,12],cmap=condition_cmap,vmin=0,vmax=4);fig.colorbar(im,ax=axes[row,1]);axes[row,1].set(title=name+' log10 condition',xlabel='Hue degrees',ylabel='EV')
        # Independent step refinement is separately recorded, not hidden by the 5% display threshold.
        refined=core.differentials(2,samples[::17],{'interpretation':1,**params},.001)
        item['refinement_h_to_h_half']={'samples':len(refined),'relative_jacobian_change':finite_summary(np.linalg.norm(refined[:,:9]-d[::17,:9],axis=1)/np.maximum(np.linalg.norm(refined[:,:9],axis=1),1e-12)),'sign_disagreements':int(np.count_nonzero(np.sign(refined[:,9])!=np.sign(d[::17,9])))}
        positive=np.all(samples>=0,axis=1)
        item['domain_breakdown']={'nonnegative_rgb_samples':int(positive.sum()),'nonnegative_rgb_reliable_fold_or_collapse':int((positive&fold).sum()),'signed_rgb_reliable_fold_or_collapse':int((~positive&fold).sum())}
        candidates=np.flatnonzero(fold&positive)[:12]
        witnesses=[]
        for index in candidates:
            probe=core.differentials(2,samples[index:index+1],{'interpretation':1,**params},.00025)[0]
            witnesses.append({'rgb':samples[index].tolist(),'determinant_at_relative_step_002':float(d[index,9]),'determinant_at_relative_step_00025':float(probe[9]),'refined_step_error':float(probe[14]),'refined_reliable':bool(probe[15]),'negative_sign_persists':bool(probe[9]<0)})
        item['positive_rgb_witnesses']=witnesses
        report['cases'].append(item)
    fig.tight_layout();fig.savefig(OUT/'volume-geometry.png',dpi=130);plt.close(fig)
    report['inspector']='Append-only modes 11–15 probe one configured Volume family on Source RGB; full multi-region authored settings use this offline harness. Red=fold/collapse, magenta=unreliable differential. It does not inspect an arbitrary upstream Volume node automatically.'
    save('volume-geometry',report);return report
if __name__=='__main__':run()
