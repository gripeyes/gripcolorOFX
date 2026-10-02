"""Reproducible Gate B comparison. Run with PYTHONPATH=build .venv/bin/python."""
from pathlib import Path
import json
import warnings
import numpy as np
import colour
import PyOpenColorIO as ocio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import _rendition as core

NAMES=['Pure stops','ACEScct','LogC4','DaVinci Intermediate','AgX unclamped stops','LookLog candidate']
OUT=Path('research/output'); OUT.mkdir(parents=True,exist_ok=True)

def candidate_report():
    positive=np.geomspace(1e-8,2**20,6000).astype(np.float32)
    signed=np.r_[-np.geomspace(1e-8,1e4,2000),0,positive].astype(np.float32)
    stops=np.linspace(-20,20,1201)
    xs=(.18*2**stops).astype(np.float32)
    references={1:colour.models.log_encoding_ACEScct,2:colour.models.log_encoding_ARRILogC4,3:colour.models.oetf_DaVinciIntermediate}
    result=[]
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for d,name in enumerate(NAMES):
        x=positive if d in (0,4) else signed
        enc=np.array([core.encode(float(v),d) for v in x],dtype=np.float32)
        dec=np.array([core.decode(float(v),d) for v in enc],dtype=np.float32)
        err=np.abs(dec.astype(float)-x)
        tolerance=2e-6+2e-5*np.abs(x)
        curve=np.array([core.encode(float(v),d) for v in xs])
        gray=core.encode(.18,d)
        h=1e-4
        slope=(core.encode(.18*2**h,d)-core.encode(.18*2**-h,d))/(2*h)
        normalized=(curve-gray)/slope
        reference_error=None
        if d in references:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore'); reference_error=float(np.max(np.abs(enc-references[d](x.astype(float)))))
        axes[0,0].plot(stops,normalized,label=name)
        axes[0,1].plot(stops,np.gradient(normalized,stops),label=name)
        axes[1,0].plot(x,err/tolerance,label=name)
        # normalized contrast and crossover response, not an output/view transform
        for contrast in [0.8,1.2]:
            toned=np.array([core.decode(float(gray+contrast*(v-gray)),d) for v in curve])
            output_stops=np.full(toned.shape,np.nan);valid=toned>0;output_stops[valid]=np.log2(toned[valid]/.18)
            axes[1,1].plot(stops,output_stops,label=f'{name} C={contrast}')
        result.append(dict(domain=name,valid_samples=len(x),nonfinite=int(np.count_nonzero(~np.isfinite(dec))),max_absolute_error=float(err.max()),max_tolerance_ratio=float((err/tolerance).max()),gray_code=gray,normal_stop_slope=slope,reference_encoding_error=reference_error,negative_support=d not in (0,4)))
    axes[0,0].set(title='Gray-normalized coordinate vs scene stops',xlabel='Scene stops',ylabel='Normalized coordinate')
    axes[0,1].set(title='Local stop sensitivity',xlabel='Scene stops',ylim=(-.05,1.5))
    axes[1,0].set(xscale='symlog',yscale='symlog',title='Float32 round-trip error / tolerance',xlabel='Scene value')
    axes[1,1].set(title='Contrast response (coordinate centered on 0.18)',xlabel='Input stops',ylabel='Output stops (nonpositive output omitted)')
    axes[0,0].legend(fontsize=7);fig.tight_layout();fig.savefig(OUT/'look-domains.png',dpi=150);plt.close(fig)
    # Independent OCIO tangent-matched custom candidate, no gamut conversion.
    b=.18/64
    tx=ocio.LogCameraTransform(linSideBreak=[b]*3,base=2,logSideSlope=[1]*3,logSideOffset=[-np.log2(.18)]*3,linSideSlope=[1]*3,linSideOffset=[0]*3)
    cpu=ocio.Config.CreateRaw().getProcessor(tx).getDefaultCPUProcessor()
    ocio_err=[]
    for x in signed[::16]:
        ref=cpu.applyRGB([float(x)]*3)[0]
        ocio_err.append(abs(ref-core.encode(float(x),5)))
    report={'schema_version':1,'domains':result,'custom_ocio_max_encoding_error':max(ocio_err),'selection':'ACEScct scalar encoding for first Tone/Crossover candidates; retain all candidates for research','rationale':'ACEScct provides an established C1 tangent toe, exact constant stop increments above the toe, negative extension, and accepted float32 round trips. Custom LookLog shows no required unique behavior after artist controls are expressed in normalized stops. Only scalar encoding is reused; AP1 primaries are not imposed.','limitations':'Pure stops and unclamped AgX stop coordinates exclude zero/negative values. AgX entry is the documented log normalization only, not full AgX, inset, clipping or display rendering. Appearance/artist acceptance remains separate from numerical comparison.'}
    (OUT/'look-domains.json').write_text(json.dumps(report,indent=2)+'\n')
    assert all(r['nonfinite']==0 and r['max_tolerance_ratio']<=1 for r in result)
    return report
if __name__=='__main__':
    report=candidate_report()
    print(json.dumps(report,indent=2))
