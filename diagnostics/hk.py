"""M11: fixed-viewing-condition HK oracle experiments; no scene operator compensation."""
import numpy as np
from .common import *

def appearance(rgb,adaptation_luminance=64):
    xyz=np.asarray(rgb)@M.T
    if np.any(xyz<0) or not np.isfinite(xyz).all():raise ValueError('HK oracle restricted to nonnegative finite XYZ stimuli')
    return colour.XYZ_to_Hellwig2022(xyz*100,colour.xy_to_XYZ([.3127,.329])*100,adaptation_luminance,20)

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    families={'red':[1,.05,.025],'yellow':[1,.7,.03],'green':[.05,.8,.08],'cyan':[.02,.5,.6],'blue':[.03,.06,.9],'magenta':[.65,.03,.5],'skin':[.6,.35,.2]}
    purity=np.linspace(0,1,31);stimuli=[];rows=[];fig,axes=plt.subplots(2,2,figsize=(13,9));data=[]
    # Match radiometric luminance exactly while varying chromatic purity.
    for fi,(family,color) in enumerate(families.items()):
        color=np.array(color);color*=.18/(color@Y)
        rgb=.18*(1-purity[:,None])+color[None]*purity[:,None]
        stimuli.append(rgb);q=appearance(rgb)
        for i,p in enumerate(purity):rows.append({'family':family,'purity':float(p),'Y':float(rgb[i]@Y),'J':float(q.J[i]),'Q':float(q.Q[i]),'J_HK':float(q.J_HK[i]),'Q_HK':float(q.Q_HK[i]),'HK_lightness_increment':float(q.J_HK[i]-q.J[i])})
        axes[0,0].plot(purity,q.Q_HK,label=family);axes[0,1].plot(purity,q.J_HK-q.J,label=family)
        for coupling in [0,.3,.8]:
            result=process('Density',rgb,{'density':.7,'width':360,'chromaCoupling':coupling,'highlightProtection':0,'shadowWeight':0})
            # Do not clip invalid outputs into the appearance model's domain.
            valid=np.all(result@M.T>=0,axis=-1)
            item={'family':family,'chromaCoupling':coupling,'invalid_oracle_outputs':int((~valid).sum()),'delta_Y':(result@Y-rgb@Y).tolist(),'delta_Q_HK':[None]*len(rgb),'delta_J':[None]*len(rgb)}
            if valid.any():
                out=appearance(result[valid]);indices=np.flatnonzero(valid)
                for local,original in enumerate(indices):item['delta_Q_HK'][original]=float(out.Q_HK[local]-q.Q_HK[original]);item['delta_J'][original]=float(out.J[local]-q.J[original])
                axes[1,0].plot(purity[valid],out.Q_HK-q.Q_HK[valid],alpha=.7,color=plt.get_cmap('tab10')(fi),linestyle={0:'-',.3:'--',.8:':'}[coupling],label=family if coupling==0 else None)
            data.append(item)
    neutral=np.repeat(np.geomspace(.005,.5,31)[:,None],3,axis=1);q=appearance(neutral)
    axes[1,1].plot(neutral@Y,q.Q,label='Q');axes[1,1].plot(neutral@Y,q.Q_HK,label='Q_HK')
    conditions=[]
    for la in [16,64,256]:
        rgb=np.array([[.18,.18,.18],[.03,.06,.9]]);rgb*=.18/(rgb@Y)[:,None];q=appearance(rgb,la)
        conditions.append({'L_A_cd_m2':la,'equal_Y':(rgb@Y).tolist(),'Q_HK':q.Q_HK.tolist(),'J_HK':q.J_HK.tolist()})
    for ax,title in zip(axes.flat,['Equal-Y purity vs HK brightness','HK lightness increment at equal Y','Current Density: change in HK brightness','Neutral control']):ax.set(title=title,xlabel='Purity (neutral control: Y)',ylabel='Hellwig model units');ax.grid(alpha=.2)
    axes[0,0].legend(fontsize=8);axes[1,0].legend(fontsize=7,ncol=2);axes[1,0].set_title('Density HK brightness change: solid c=0, dashed .3, dotted .8');axes[1,1].legend();fig.tight_layout();fig.savefig(OUT/'density-hk.png',dpi=140);plt.close(fig)
    np.savez_compressed(OUT/'hk-equal-luminance-stimuli.npz',purity=purity,rgb=np.array(stimuli),family_names=np.array(list(families)))
    report={'gate':'M11 / HK','oracle':'Colour pinned XYZ_to_Hellwig2022, J_HK and Q_HK correlates; published model includes HK term. No novel signed extension attributed to Hellwig.','conditions':{'white':'D65, Yw=100','XYZ_scale':'scene RGB Y=.18 maps to XYZ Y=18 in oracle; defined fixed reference, not display rendering','L_A_cd_m2':64,'Y_b':20,'surround':'Average model default'},'domain':'Only finite nonnegative XYZ; signed/HDR production inputs remain tested separately, without invented HK perceptual meaning','semantic_boundary':'Appearance-reference experiment only. No HK compensation or viewing-condition dependence added to scene Density.','equal_luminance_experiments':rows,'density_coupling_experiments':data,'viewing_condition_sensitivity':conditions,'artist_question':'Does chroma-coupled depth remain perceptually dense rather than just darker? Compare equal-Y patches and real skin through fixed user DRT; oracle values do not settle artist judgement.','limitations':'Fixed white/exposure mapping and model correlations; no psychophysical subject experiment or production HK correction.','references':['https://doi.org/10.1002/col.22793','https://doi.org/10.1002/col.22792'],'production_equations_changed':False}
    save('density-hk',report);return report
if __name__=='__main__':run()
