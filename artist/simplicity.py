"""M17: fitted simple baselines against existing candidates, with held-out data.
Residuals measure representational differences, never artistic superiority.
"""
import json,time
from pathlib import Path
import numpy as np
import colour
from scipy.interpolate import PchipInterpolator
from scipy.optimize import least_squares
from common import ROOT,rgba,process,read_scene,write_exr,Preview,count_controls

OUT=ROOT/'build/artist-tests';OUT.mkdir(parents=True,exist_ok=True)
SPACE=colour.RGB_COLOURSPACES['ITU-R BT.2020'];M=SPACE.matrix_RGB_to_XYZ;I=SPACE.matrix_XYZ_to_RGB
Y=M[1]
CASES={
 'Density':{'density':.55,'width':360,'chromaCoupling':.3,'highlightProtection':0,'shadowWeight':0},
 'Strip':{'separation':.55,'palette':.35,'leakage':.25,'redAnchor':.65},
 'Volume':{'v0_width':120,'v0_hueDelta':20,'v0_chroma':.75,'v0_evMin':-5,'v0_evMax':0},
 'Crossover':{'width':360,'darkHue':25,'darkChroma':.35,'darkDensity':.2,'brightHue':-10,'transition':2}}

def lab(rgb):return colour.XYZ_to_Oklab(rgb@M.T)
def fromlab(q):return colour.Oklab_to_XYZ(q)@I.T

def metric(predicted,target,source):
    scale=np.maximum(np.max(np.abs(source),axis=-1),.001)
    relative=(predicted-target)/scale[...,None]
    q=lab(source);h=np.degrees(np.arctan2(q[:,2],q[:,1]))%360
    ev=np.log2(np.maximum(source@Y,1e-12)/.18)
    rows=[]
    for name,center in [('red',29),('yellow',110),('green',145),('cyan',195),('blue',265),('magenta',325)]:
        delta=np.abs((h-center+180)%360-180)
        for region,lo,hi in [('dark',-30,-3),('middle',-3,3),('HDR',3,30)]:
            mask=(delta<40)&(ev>=lo)&(ev<hi)
            if np.any(mask):rows.append({'family':name,'exposure_region':region,'samples':int(mask.sum()),'relative_rgb_rms':float(np.sqrt(np.mean(relative[mask]**2)))})
    return {'relative_rgb_rms':float(np.sqrt(np.mean(relative**2))),'max_relative_rgb_error':float(np.max(np.abs(relative))),
            'nonfinite':int(np.count_nonzero(~np.isfinite(predicted))),'by_family_and_exposure':rows}

def exposure_saturation(x,a,weight=None):
    gain=np.exp2(a[0]);sat=a[1];result=gain*(sat*x+(1-sat)*(x@Y)[:,None])
    return result if weight is None else x+weight[:,None]*(result-x)

def curve_eval(x,knots,values):
    curve=PchipInterpolator(knots,values,extrapolate=False)
    result=curve(np.clip(x,knots[0],knots[-1]))
    derivative=curve.derivative()
    result=np.where(x<knots[0],values[0]+derivative(knots[0])*(x-knots[0]),result)
    return np.where(x>knots[-1],values[-1]+derivative(knots[-1])*(x-knots[-1]),result)

KNOTS=np.array([-9,-5,-2,0,2,5,9.])
def matrix_curves(x,a):
    q=np.arcsinh((x@a[:9].reshape(3,3).T)/.18);out=np.empty_like(q)
    for channel in range(3):
        controls=a[9+7*channel:16+7*channel]
        values=np.r_[KNOTS[0]+controls[0],KNOTS[0]+controls[0]+np.cumsum(np.diff(KNOTS)*np.exp(controls[1:]))]
        out[:,channel]=.18*np.sinh(curve_eval(q[:,channel],KNOTS,values))
    return out

HUES=np.arange(0,360,30.)
def hue_curves(x,a):
    q=lab(x);h=np.degrees(np.arctan2(q[:,2],q[:,1]))%360;c=np.hypot(q[:,1],q[:,2])
    angle=np.radians(h+PchipInterpolator(np.r_[HUES-360,HUES,HUES+360],np.tile(a[:12],3))(h))
    chroma=c*np.exp(PchipInterpolator(np.r_[HUES-360,HUES,HUES+360],np.tile(a[12:],3))(h))
    q[:,1]=chroma*np.cos(angle);q[:,2]=chroma*np.sin(angle)
    return fromlab(q)

def three_keys(x,a,soft=True):
    # Independent smoothstep luminance keys, not hard masks presented as the only baseline.
    q=lab(x);ev=np.log2(np.maximum(x@Y,1e-12)/.18)
    def smooth(z):z=np.clip(z,0,1);return z*z*(3-2*z)
    d=1-smooth((ev+6)/6) if soft else (ev<-3).astype(float)
    b=smooth(ev/6) if soft else (ev>=3).astype(float);m=1-d-b
    weights=np.stack([d,m,b],1);h=np.degrees(np.arctan2(q[:,2],q[:,1]));chroma=np.hypot(q[:,1],q[:,2])
    hue=h+weights@a[:3];c=chroma*np.exp(weights@a[3:6]);L=q[:,0]*np.exp(weights@a[6:9])
    return fromlab(np.stack([L,c*np.cos(np.radians(hue)),c*np.sin(np.radians(hue))],1))

def fit(fun,x,target,initial,bounds,max_nfev=65):
    scale=np.maximum(np.max(np.abs(x),axis=1),.01)
    start=time.perf_counter();result=least_squares(lambda a:((fun(x,a)-target)/scale[:,None]).ravel(),initial,bounds=bounds,max_nfev=max_nfev)
    return result.x,{'solver_seconds':time.perf_counter()-start,'evaluations':result.nfev,'solver_converged':bool(result.success),'human_interaction_seconds':None}

def main():
    rng=np.random.default_rng(1717)
    x=rng.uniform(.015,1,(1800,3))*np.exp2(rng.uniform(-8,8,(1800,1)))
    # Split whole samples before fitting; add signed/HDR diagnostics separately.
    train=x[:600];test=x[600:];preview=Preview()
    report={'schema_version':1,'seed':1717,'training_samples':600,'heldout_samples':1200,
       'metric_policy':'Linear scene RGB normalized by source magnitude, reported per hue/exposure. No metric or fit residual passes artist acceptance.',
       'view':'Flawed Emulsion 2 / sRGB; selected by user','cases':[]}
    models={}
    for name,params in CASES.items():
        target_train=process(name,rgba(train),params)[:,:3];target_test=process(name,rgba(test),params)[:,:3]
        baselines=[]
        if name=='Density':
            a,info=fit(exposure_saturation,train,target_train,[0,1],([-8,0],[4,4]))
            baselines.append(('Exposure + Saturation',exposure_saturation,a,info,2))
            weights=process('Density',rgba(train),{**params,'debug':1})[:,0]
            fun=lambda z,a:exposure_saturation(z,a,process('Density',rgba(z),{**params,'debug':1})[:,0])
            a,info=fit(fun,train,target_train,[0,1],([-8,0],[4,4]))
            baselines.append(('Exposure + Saturation with identical selection',fun,a,info,2))
        if name=='Strip':
            matrix=np.linalg.lstsq(train/np.max(train,axis=1)[:,None],target_train/np.max(train,axis=1)[:,None],rcond=None)[0].T
            baselines.append(('3x3 Matrix',lambda z,a:z@a.reshape(3,3).T,matrix.ravel(),{'solver_seconds':0,'human_interaction_seconds':None},9))
            initial=np.r_[np.clip(matrix.ravel(),-3.9,3.9),np.zeros(21)]
            a,info=fit(matrix_curves,train,target_train,initial,(np.r_[np.full(9,-4.),np.full(21,-2.)],np.r_[np.full(9,4.),np.full(21,2.)]),max_nfev=90)
            baselines.append(('3x3 Matrix + monotone per-channel curves',matrix_curves,a,info,30))
        if name=='Volume':
            a,info=fit(hue_curves,train,target_train,np.zeros(24),(np.r_[np.full(12,-90.),np.full(12,-2.)],np.r_[np.full(12,90.),np.full(12,2.)]))
            baselines.append(('Hue-vs-Hue / Hue-vs-Chroma curves',hue_curves,a,info,24))
        if name=='Crossover':
            for soft,label in [(True,'Three smooth luminance keys'),(False,'Three hard luminance keys diagnostic')]:
                fun=lambda z,a,soft=soft:three_keys(z,a,soft)
                a,info=fit(fun,train,target_train,np.zeros(9),(np.r_[np.full(3,-90.),np.full(6,-2.)],np.r_[np.full(3,90.),np.full(6,2.)]))
                baselines.append((label,fun,a,info,9))
        row={'effect':name,'candidate_parameters':params,**count_controls([{'effect':name,'parameters':params}]),'baselines':[],
             'artist_gate':'Pending; meaningful superiority is not established by residual error'}
        for label,fun,a,info,controls in baselines:
            predicted=fun(test,a)
            entry={'name':label,'parameters':a.tolist(),'parameter_count':controls,'fit':info,'heldout':metric(predicted,target_test,test)}
            row['baselines'].append(entry);models[name+'/'+label]={'parameters':a.tolist(),'candidate_parameters':params}
            for source in ['structured','synthetic_cg']:
                image=read_scene(OUT/(source+'.exr'));shape=image.shape;flat=image[...,:3].reshape(-1,3)
                candidate=process(name,image,params);baseline=rgba(fun(flat,a)).reshape(shape);baseline[...,3]=image[...,3]
                stem=name.lower()+'-'+('curves' if 'curves' in label.lower() else 'matched' if 'identical' in label else 'smooth' if 'smooth' in label else 'hard' if 'hard' in label else 'simple')+'-'+source
                write_exr(OUT/(stem+'-baseline.exr'),baseline);write_exr(OUT/(stem+'-candidate.exr'),candidate)
                sheet=Image.new('RGB',(2304,390),(20,20,20));draw=ImageDraw.Draw(sheet)
                draw.text((10,5),name+' | source / '+label+' / candidate | user Flawed Emulsion 2 / sRGB',(220,220,220))
                for index,img in enumerate([image,baseline,candidate]):sheet.paste(preview.image(img),(index*768,25))
                sheet.save(OUT/(stem+'-comparison.png'));entry.setdefault('visual_files',[]).append(stem+'-comparison.png')
        report['cases'].append(row)
    report['conclusion']='Existing Density and Strip remain research candidates. Fits expose differences or sufficiency of simpler models; only artist evaluation of continuity, control, coherence, speed and cross-content reuse can establish superiority.'
    (OUT/'simplicity-report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');(OUT/'baseline-models.json').write_text(json.dumps(models,indent=2)+'\n')
    print('Completed M17 baseline comparisons:',OUT/'simplicity-report.json')
if __name__=='__main__':
    from PIL import Image,ImageDraw
    main()
