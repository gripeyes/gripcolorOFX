"""M15–M17 targeted aggressive settings, multistart simple baselines and reuse."""
import sys,json,time
import numpy as np
from scipy.optimize import least_squares
from .common import *
sys.path.insert(0,str(ROOT/'artist'))
from simplicity import exposure_saturation,matrix_curves,three_keys,metric
from common import Preview,read_scene,write_exr,count_controls
from PIL import Image,ImageDraw

CASES={
 'Density':[
 ('depth',{'density':.9,'chromaCoupling':.7,'highlightProtection':0,'shadowWeight':0}),
 ('thin',{'density':-.8,'chromaCoupling':-.7,'highlightProtection':0,'shadowWeight':0}),
 ('skin_depth',{'hue':65,'width':110,'density':.9,'chromaCoupling':.6,'highlightProtection':.8,'shadowWeight':1})],
 'Crossover':[
 ('cyan_death',{'hue':195,'width':150,'darkHue':100,'darkChroma':.05,'darkDensity':1.2,'midHue':-20,'midChroma':1.5,'brightHue':-90,'brightChroma':2,'transition':.5}),
 ('global_trajectory',{'width':360,'darkHue':120,'darkChroma':.15,'darkDensity':1,'midHue':-20,'brightHue':-70,'brightChroma':2,'brightDensity':-.6,'transition':1}),
 ('narrow_transition',{'width':360,'darkHue':-150,'darkChroma':0,'brightHue':150,'brightChroma':4,'transition':.1})],
 'Strip':[
 ('three_records',{'separation':1,'palette':.8,'density':.8,'leakage':.6,'redAnchor':.7}),
 ('two_records',{'mode':1,'separation':1,'palette':-.8,'density':-.5,'leakage':.05,'redAnchor':.8}),
 ('contamination',{'separation':.9,'palette':-.6,'density':1,'leakage':.9,'neutralAnchor':.4,'rContribution':2,'bWeight':.5})]}

def flexible_keys(x,a):
    # Independent 3-key smoothstep baseline, with movable dark/bright centers and width, using the existing normalized ACEScct exposure coordinate.
    q=labs(x);lum=np.asarray(x)@Y
    with np.errstate(divide='ignore',invalid='ignore'):
        ev=(colour.models.log_encoding_ACEScct(lum)-colour.models.log_encoding_ACEScct(.18))*17.52
    lo=a[9];hi=lo+np.exp(a[10]);width=np.exp(a[11]);smooth=lambda z:np.clip(z,0,1)**2*(3-2*np.clip(z,0,1))
    d=1-smooth((ev-lo+width/2)/width);b=smooth((ev-hi+width/2)/width);w=np.stack([d,1-d-b,b],axis=1)
    h=np.arctan2(q[:,2],q[:,1])+np.radians(w@a[:3]);c=np.hypot(q[:,1],q[:,2])*np.exp(w@a[3:6]);L=q[:,0]*np.exp(w@a[6:9])
    return fromlabs(np.stack([L,c*np.cos(h),c*np.sin(h)],-1))

def selected_keys(fun,params):
    defaults={p['id']:p['default'] for p in core.parameters(4)}
    selection={key:params.get(key,defaults[key]) for key in ['hue','width','chromaMin','chromaMax','evMin','evMax','softness','neutral']}
    def apply(x,a):
        rgba=np.concatenate([x,np.ones((len(x),1))],axis=-1).astype(np.float32)
        weight=core.process(2,rgba,{'interpretation':1,'debug':2,**{'v0_'+k:v for k,v in selection.items()}})[:,0]
        original=labs(x);deformed=labs(fun(x,a))
        return fromlabs(original+weight[:,None]*(deformed-original))
    return apply

def fixed_keys(x,a):return flexible_keys(x,np.r_[a,-3,np.log(6),np.log(6)])

def fit_multistart(fun,x,target,starts,bounds,max_evaluations=60):
    scale=np.maximum(np.max(np.abs(x),axis=1),.01);attempts=[];best=None
    for initial in starts:
        start=time.perf_counter()
        result=least_squares(lambda a:((fun(x,a)-target)/scale[:,None]).ravel(),initial,bounds=bounds,max_nfev=max_evaluations)
        loss=float(np.mean(((fun(x,result.x)-target)/scale[:,None])**2))
        attempts.append({'train_normalized_mse':loss,'evaluations':result.nfev,'converged':bool(result.success),'solver_seconds':time.perf_counter()-start})
        if best is None or loss<best[0]:best=(loss,result.x)
    return best[1],{'attempts':attempts,'selection':'Lowest training loss only; held-out samples never used to select parameters','human_interaction_seconds':None}

def trajectory_samples():
    hues=np.arange(0,360,30);ev=np.linspace(-14,14,281);L=.6*np.exp2(ev/3)
    q=np.stack(np.broadcast_arrays(L[:,None],.22*L[:,None]*np.cos(np.radians(hues)),.22*L[:,None]*np.sin(np.radians(hues))),-1)
    return fromlabs(q).astype(np.float32),ev,hues

def run():
    OUT.mkdir(parents=True,exist_ok=True);rng=np.random.default_rng(21717)
    samples=rng.uniform(.005,1,(1500,3))*np.exp2(rng.uniform(-12,12,(1500,1)));train=samples[:400];test=samples[400:]
    signed=rng.normal(size=(600,3))*np.exp2(rng.uniform(-12,12,(600,1)));stress=np.concatenate([test,signed,np.zeros((1,3)),np.eye(3)*4096,np.ones((1,3))*1e-8])
    trajectory,ev,hues=trajectory_samples();preview=Preview();photos={}
    for num in [5,7,60]:
        path=ROOT/'build/artist-tests'/f'aces-{num:04d}.exr'
        if path.exists():photos[num]=read_scene(path)
    report={'gate':'M15–M17 creative range','seed':21717,'train_samples':len(train),'heldout_samples':len(test),'stress_samples':len(stress),'baseline_policy':'Multistart simple models selected on training loss; matched Density selection and adjustable smooth luminance keys prevent qualifier/threshold advantages masquerading as new colour math. Fits are bounded/local, not proof of irreducibility.','view':'User Flawed Emulsion 2 / sRGB','artist_status':'User reports current eight nodes usable; aggressive-range superiority and interaction timing remain to evaluate, not a reason to freeze development.','cases':[]}
    for effect,cases in CASES.items():
        fig,axes=plt.subplots(len(cases),3,figsize=(15,3.6*len(cases)))
        for row,(label,params) in enumerate(cases):
            target_train=process(effect,train,params);target_test=process(effect,test,params);baselines=[]
            if effect=='Density':
                for matched in [False,True]:
                    def fun(x,a,matched=matched):
                        if not matched:return exposure_saturation(x,a)
                        rgba=np.concatenate([x,np.ones((len(x),1))],axis=-1).astype(np.float32)
                        weights=core.process(3,rgba,{'interpretation':1,**params,'debug':1})[:,0]
                        return exposure_saturation(x,a,weights)
                    a,info=fit_multistart(fun,train,target_train,[[0,1],[-2,1.5],[1,.5]],([-8,0],[4,4]))
                    baselines.append(('Exposure+saturation'+(' matched selection' if matched else ''),fun,a,info))
            elif effect=='Strip':
                scale=np.max(train,axis=1)[:,None];matrix=np.linalg.lstsq(train/scale,target_train/scale,rcond=None)[0].T
                baselines.append(('3x3 matrix',lambda x,a:x@a.reshape(3,3).T,matrix.ravel(),{'closed_form':True,'human_interaction_seconds':None}))
                starts=[np.r_[np.clip(matrix.ravel(),-3.9,3.9),np.zeros(21)],np.r_[np.eye(3).ravel(),np.zeros(21)]]
                a,info=fit_multistart(matrix_curves,train,target_train,starts,(np.r_[np.full(9,-4.),np.full(21,-1.)],np.r_[np.full(9,4.),np.full(21,1.)]),45)
                baselines.append(('Matrix+monotone curves',matrix_curves,a,info))
            else:
                fixed=selected_keys(fixed_keys,params);movable=selected_keys(flexible_keys,params)
                a,info=fit_multistart(fixed,train,target_train,[np.zeros(9),np.r_[[90,-20,-60],np.zeros(6)]],(np.r_[np.full(3,-180.),np.full(6,-3.)],np.r_[np.full(3,180.),np.full(6,3.)]))
                baselines.append(('Three fixed smooth keys, matched selector',fixed,a,info))
                starts=[np.r_[a,-3,np.log(6),np.log(3)],np.r_[np.zeros(9),-5,np.log(10),np.log(1)]]
                a,info=fit_multistart(movable,train,target_train,starts,(np.r_[np.full(3,-180.),np.full(6,-3.),-12,np.log(.2),np.log(.1)],np.r_[np.full(3,180.),np.full(6,3.),4,np.log(20),np.log(10)]),60)
                baselines.append(('Three movable smooth keys, matched selector',movable,a,info))
            output=process(effect,stress,params);assert np.isfinite(output).all()
            q=labs(process(effect,trajectory,params));original=labs(trajectory)
            hue_change=np.degrees(np.unwrap(np.arctan2(q[...,2],q[...,1])-np.arctan2(original[...,2],original[...,1]),axis=0));chroma=np.hypot(q[...,1],q[...,2])/np.maximum(np.hypot(original[...,1],original[...,2]),1e-12)
            hue_valid=np.hypot(q[...,1],q[...,2])>1e-5*np.maximum(np.abs(q[...,0]),.001)
            hue_change=np.where(hue_valid,hue_change,np.nan)
            lum_out=process(effect,trajectory,params)@Y;lum_in=trajectory@Y
            changes=np.linalg.norm(np.diff(process(effect,trajectory,params),axis=0),axis=-1)/np.maximum(np.max(np.abs(trajectory[:-1]),axis=-1),.001)
            item={'effect':effect,'name':label,'parameters':params,**count_controls([{'effect':effect,'parameters':params}]),'stress_nonfinite':0,'output_max_abs_vs_input':float(np.max(np.abs(output))/np.max(np.abs(stress))),'trajectory_hue_unobservable_samples':int((~hue_valid).sum()),'trajectory_luminance_reversals':int(np.count_nonzero(np.diff(lum_out,axis=0)<-1e-8)),'trajectory_max_neighbor_relative_change':float(changes.max()),'baselines':[],'human_artist_range_evaluation':None,'useful_behavior_hypothesis':{'Density':'Independent chroma-coupled depth and hue-selective protection beyond one gain/saturation pair','Crossover':'Smooth hue/chroma/depth grammar through EV with compact authoring controls','Strip':'Coherent record/palette/anchor interaction beyond fixed channel coefficients'}[effect]}
            for bi,(name,fun,a,info) in enumerate(baselines):
                predicted=fun(test,a);assert np.isfinite(predicted).all()
                signed_pred=fun(stress,a);assert np.isfinite(signed_pred).all()
                entry={'name':name,'parameters':a.tolist(),'parameter_count':len(a),'fit':info,'heldout':metric(predicted,target_test,test),'signed_hdr_scaled_error':float(np.sqrt(np.mean(((signed_pred-output)/np.maximum(np.max(np.abs(stress),axis=1),.001)[:,None])**2))),'signed_hdr_nonfinite':0,'photographic_reuse':[]}
                for num,image in photos.items():
                    flat=image[...,:3].reshape(-1,3);candidate=process(effect,image[...,:3],params);baseline=fun(flat,a).reshape(candidate.shape)
                    assert np.isfinite(candidate).all() and np.isfinite(baseline).all()
                    stem=f'{effect.lower()}-{label}-b{bi}-photo-{num:04d}'
                    sheet=Image.new('RGB',(1920,385));ImageDraw.Draw(sheet).text((8,3),effect+' '+label+' | source / '+name+' / candidate | unchanged held-out fit',(255,255,255))
                    for col,x in enumerate([image[...,:3],baseline,candidate]):
                        rgba=np.concatenate([x,np.ones(x.shape[:-1]+(1,))],axis=-1);sheet.paste(preview.image(rgba),(640*col,25))
                    sheet.save(OUT/(stem+'.png'));entry['photographic_reuse'].append({'frame':num,'preview':stem+'.png','refit':False,'artist_preference':None})
                item['baselines'].append(entry)
            for col,(data,title) in enumerate([(hue_change,'Hue displacement (degrees)'),(chroma,'Chroma scale'),(lum_out/np.maximum(np.abs(lum_in),1e-12),'Linear Y ratio')]):
                for i,h in enumerate(hues):axes[row,col].plot(ev,data[:,i],label=str(h)+'°',alpha=.65)
                axes[row,col].set(title=label+' '+title,xlabel='Input EV');axes[row,col].grid(alpha=.2)
            report['cases'].append(item)
        fig.tight_layout();fig.savefig(OUT/(effect.lower()+'-trajectories.png'),dpi=135);plt.close(fig)
    save('creative-range',report);return report
if __name__=='__main__':run()
