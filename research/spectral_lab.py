"""High-resolution spectral oracle. Appearance models never silently return scene RGB.
Original synthetic colorants, standard CIE observer/illuminants from Colour.
"""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
import numpy as np
import colour
from scipy.optimize import nnls

class Kind(str,Enum):
    REFLECTANCE='reflectance'
    TRANSMITTANCE='transmittance'
    EMISSION='emission'
    DENSITY='optical_density'

@dataclass(frozen=True)
class Spectrum:
    wavelengths:np.ndarray
    values:np.ndarray
    kind:Kind
    def __post_init__(self):
        w=np.asarray(self.wavelengths,dtype=float);v=np.asarray(self.values,dtype=float)
        if w.ndim!=1 or v.shape!=w.shape or len(w)<2 or np.any(np.diff(w)<=0) or not np.all(np.isfinite(w)) or not np.all(np.isfinite(v)):
            raise ValueError('Invalid spectral distribution/grid')
        if self.kind in (Kind.REFLECTANCE,Kind.TRANSMITTANCE) and (np.any(v<0) or np.any(v>1)):
            raise ValueError('Reflectance/transmittance must be physical [0,1]')
        if np.any(v<0):raise ValueError('Physical spectrum cannot carry signed RGB residuals')
        w=w.copy();v=v.copy();w.setflags(write=False);v.setflags(write=False)
        object.__setattr__(self,'wavelengths',w);object.__setattr__(self,'values',v)
    def resample(self,grid):
        grid=np.asarray(grid,dtype=float)
        if grid[0]<self.wavelengths[0] or grid[-1]>self.wavelengths[-1]:raise ValueError('No implicit spectral extrapolation')
        return Spectrum(grid,np.interp(grid,self.wavelengths,self.values),self.kind)

class Lab:
    def __init__(self,step=1,illuminant='D65'):
        if step<=0 or (830-360)%step:raise ValueError('Grid must include 360 and 830 nm')
        self.grid=np.arange(360,831,step,dtype=float);self.shape=colour.SpectralShape(360,830,step)
        self.cmfs=colour.MSDS_CMFS['CIE 1931 2 Degree Standard Observer'].copy().align(self.shape)
        self.illuminant=colour.SDS_ILLUMINANTS[illuminant].copy().align(self.shape)
        self.illuminant_name=illuminant
        # Colour Integration's explicit rectangular quadrature, 1 nm authoritative grid.
        self.reflectance_weights=self.cmfs.values*self.illuminant.values[:,None]
        self.reflectance_weights/=np.sum(self.reflectance_weights[:,1])
        self.emission_weights=self.cmfs.values*step
        self.space=colour.RGB_COLOURSPACES['ITU-R BT.2020']
        self.basis=np.array([np.exp(-.5*((self.grid-c)/w)**2) for c,w in [(400,25),(440,30),(480,30),(520,30),(560,30),(600,30),(640,30),(690,40)]]).T
        self.basis_xyz=self.basis.T@self.emission_weights
    def xyz(self,spectrum):
        if not np.array_equal(spectrum.wavelengths,self.grid):spectrum=spectrum.resample(self.grid)
        if spectrum.kind==Kind.DENSITY:raise ValueError('Optical density is not a stimulus: convert to transmittance first')
        weights=self.emission_weights if spectrum.kind==Kind.EMISSION else self.reflectance_weights
        return spectrum.values@weights
    def rgb(self,spectrum):return self.xyz(spectrum)@self.space.matrix_XYZ_to_RGB.T
    def reconstruct(self,rgb,scale_method='max',strategy='nnls_residual'):
        """Nonunique emitted base + signed XYZ residual; never calls RGB reflectance.
        Exact no-op reconstruction holds because residual is explicit and retained.
        """
        rgb=np.asarray(rgb,dtype=float)
        if rgb.shape!=(3,) or not np.all(np.isfinite(rgb)):raise ValueError('Expected finite scene RGB')
        target=rgb@self.space.matrix_RGB_to_XYZ.T
        if scale_method=='max':scale=np.max(np.abs(rgb))
        elif scale_method=='norm':scale=np.linalg.norm(rgb)
        elif scale_method=='luminance':scale=abs(target[1])
        else:raise ValueError('Unknown scale decomposition')
        # Luminance can cancel exactly for signed colors: fallback is explicit norm.
        if scale<1e-12:scale=np.linalg.norm(rgb)
        if scale==0:return Spectrum(self.grid,np.zeros_like(self.grid),Kind.EMISSION),np.zeros(3),0
        chroma=target/scale
        if strategy=='nnls_residual':
            coeff,_=nnls(self.basis_xyz.T,chroma);base=self.basis@coeff
        elif strategy=='smits_residual':
            linear709=chroma@colour.RGB_COLOURSPACES['ITU-R BT.709'].matrix_XYZ_to_RGB.T
            # Positive component is explicit; removed signed information is in residual.
            sd=colour.recovery.RGB_to_sd_Smits1999(np.maximum(linear709,0)).copy().align(self.shape)
            base=np.maximum(sd.values,0)
            # Radiance magnitude calibrated against target using nonnegative LS scale.
            pred=base@self.emission_weights
            gain=max(0,float(pred@chroma)/max(float(pred@pred),1e-30));base*=gain
        else:raise ValueError('Unknown reconstruction strategy')
        spectrum=Spectrum(self.grid,base*scale,Kind.EMISSION)
        residual=target-self.xyz(spectrum)
        return spectrum,residual,scale
    def material_ks(self):
        w=self.grid
        def g(c,s):return np.exp(-.5*((w-c)/s)**2)
        # Independent synthetic absorption curves, deliberately imperfect and nonhistorical.
        return np.array([.03+2*g(640,55)+.2*g(420,35),.03+2*g(535,45)+.15*g(680,55),.03+2*g(435,50)+.1*g(570,45)])
    def pigment(self,weights,concentration,scatter=1):
        if concentration<0 or scatter<=0:raise ValueError('Physical concentration/scattering must be nonnegative/positive')
        k=np.asarray(weights)@self.material_ks()*concentration
        a=k/scatter
        # Stable infinite-thickness Kubelka–Munk R_infinity.
        reflectance=1/(1+a+np.sqrt(a*a+2*a))
        return Spectrum(self.grid,reflectance,Kind.REFLECTANCE)
    def dye(self,weights,optical_density=1,leakage=0):
        if optical_density<0 or not 0<=leakage<=1 or np.any(np.asarray(weights)<0):raise ValueError('Invalid physical dye parameters')
        d=self.material_ks();d=(1-leakage)*d+leakage*np.mean(d,axis=0)[None,:]
        density=np.asarray(weights)@d*optical_density
        return Spectrum(self.grid,np.power(10.,-density),Kind.TRANSMITTANCE)
    def neugebauer(self,coverage,n=1):
        a=np.asarray(coverage,dtype=float)
        if np.any(a<0) or np.any(a>1) or n<=0:raise ValueError('Invalid coverage/Yule-Nielsen exponent')
        result=np.zeros(len(self.grid))
        for i in range(8):
            bits=np.array([(i>>j)&1 for j in range(3)])
            area=np.prod(np.where(bits,a,1-a))
            result+=area*self.dye(bits).values**(1/n)
        return Spectrum(self.grid,result**n,Kind.REFLECTANCE)

FAMILIES={'cyan-blue':[1,.05,.02],'green-olive':[1,.02,.8],'red-bronze':[.02,1,1],'yellow-orange':[.02,.05,1],'magenta-purple':[.1,1,.02]}

def run(output='research/output'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=Path(output);out.mkdir(parents=True,exist_ok=True);lab=Lab();rng=np.random.default_rng(71)
    integration={}
    for ill in ['D65','D60','D50','A']:
        l=Lab(1,ill);samples=[np.ones(len(l.grid)),*l.material_ks()/np.max(l.material_ks(),axis=1)[:,None]]
        errors=[]
        for sample in samples:
            sd=colour.SpectralDistribution(dict(zip(l.grid,sample)))
            expected=colour.sd_to_XYZ(sd,l.cmfs,l.illuminant,method='Integration')/100
            errors.append(float(np.max(np.abs(l.xyz(Spectrum(l.grid,sample,Kind.REFLECTANCE))-expected))))
        integration[ill]={'max_xyz_error':max(errors),'white_xyz':l.xyz(Spectrum(l.grid,np.ones(len(l.grid)),Kind.REFLECTANCE)).tolist()}
    records=[];fig,axes=plt.subplots(2,3,figsize=(13,8))
    for family,weights in FAMILIES.items():
        for kind in ['pigment','dye','neugebauer']:
            coords=[]
            for concentration in np.linspace(.05,2,81):
                s=lab.pigment(weights,concentration) if kind=='pigment' else lab.dye(weights,concentration,.1) if kind=='dye' else lab.neugebauer(np.array(weights)*min(concentration/2,1),2)
                xyz=lab.xyz(s);rgb=lab.rgb(s);q=colour.XYZ_to_Oklab(xyz);coords.append(q)
                records.append({'family':family,'model':kind,'concentration':float(concentration),'semantics':'appearance-referred linear','xyz':xyz.tolist(),'rgb2020':rgb.tolist(),'oklab':q.tolist(),'ipt':colour.XYZ_to_IPT(xyz).tolist(),'jzazbz':colour.XYZ_to_Jzazbz(xyz).tolist()})
            coords=np.array(coords);axes[0,0].plot(coords[:,1],coords[:,2],label=family+'/'+kind);axes[0,1].plot(coords[:,0],np.hypot(coords[:,1],coords[:,2]));axes[0,2].plot(np.linspace(.05,2,81),np.unwrap(np.arctan2(coords[:,2],coords[:,1]))*180/np.pi)
    for d in lab.material_ks():axes[1,0].plot(lab.grid,d)
    for weights in FAMILIES.values():axes[1,1].plot(lab.grid,lab.pigment(weights,1).values);axes[1,2].plot(lab.grid,lab.dye(weights,1,.1).values)
    titles=['Opponent trajectories','Lightness/chroma trajectories','Hue evolution','Synthetic K/S and density bases','Pigment reflectances','Dye transmittances']
    for ax,title in zip(axes.flat,titles):ax.set_title(title)
    axes[0,0].set(xlabel='Oklab a',ylabel='Oklab b');axes[0,1].set(xlabel='Oklab L',ylabel='Oklab C');axes[0,2].set(xlabel='Model amount (density/concentration/coverage proxy)',ylabel='Unwrapped hue (degrees)')
    for ax in axes[1,:]:ax.set_xlabel('Wavelength (nm)')
    axes[1,0].set_ylabel('Synthetic absorption basis');axes[1,1].set_ylabel('Reflectance');axes[1,2].set_ylabel('Transmittance')
    axes[0,0].legend(fontsize=5);fig.tight_layout();fig.savefig(out/'spectral-trajectories.png',dpi=160);plt.close(fig)
    (out/'spectral-dataset-v1.json').write_text(json.dumps({'schema_version':1,'records':records,'source':'Original synthetic colorants; no historical/stock accuracy claim'},indent=2)+'\n')
    rgb_samples=np.r_[rng.normal(size=(80,3)),[[0,0,0],[10000,2000,-50],[1,0,0],[0,1,0],[0,0,1]]]
    adapters={}
    for strategy in ['nnls_residual','smits_residual']:
        for scale in ['max','norm','luminance']:
            errors=[];residuals=[];scale_errors=[]
            for rgb in rgb_samples:
                s,r,_=lab.reconstruct(rgb,scale,strategy);xs=lab.xyz(s)+r;target=rgb@lab.space.matrix_RGB_to_XYZ.T
                errors.append(float(np.max(np.abs(xs-target))));residuals.append(float(np.linalg.norm(r)/max(np.linalg.norm(target),1e-12)))
                s2,r2,_=lab.reconstruct(rgb*2,scale,strategy);scale_errors.append(float(np.max(np.abs(s2.values-2*s.values))))
            adapters[strategy+'/'+scale]={'identity_max_xyz_error':max(errors),'max_relative_residual':max(residuals),'exposure_spectral_shape_error':max(scale_errors),'semantics':'scene radiance base plus explicit signed XYZ residual; physical material outputs remain appearance references'}
    reduced={}
    ref=lab.xyz(lab.dye([.8,.2,.5],1,.1))
    for step in [2,5,10]:
        l=Lab(step);reduced[str(step)+'nm']=float(np.max(np.abs(l.xyz(l.dye([.8,.2,.5],1,.1))-ref)))
    report={'schema_version':1,'integration':integration,'reconstruction':adapters,'reduced_grid_errors':reduced,'negative_strategy':'NNLS positive emitted base + explicit signed XYZ residual is an exact identity candidate. Active material operation acceptance additionally needs adapter transition and image behavior tests.','hdr_strategy':'Max-absolute-channel shape/scale decomposition selected for initial oracle; doubling input doubles base and residual without changing spectral shape. Norm alternatives also tested; luminance cancellation explicitly falls back to norm.','gate_status':'S0/S2/S3 numerical reference experiments complete; signed/HDR active-operator and scene-fit acceptance pending; appearance models are not production nodes'}
    (out/'spectral-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    return report
if __name__=='__main__':run()
