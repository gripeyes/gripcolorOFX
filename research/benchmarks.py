"""Single-thread scalar-core throughput, including output allocation, not host FPS."""
import json,time,platform,subprocess
from pathlib import Path
import numpy as np
import _rendition as c
cases=[('Scene',0,{'exposure':.5}),('Tone',1,{'contrast':1.1,'toe':.2}),('Volume',2,{'v0_width':360,'v0_hueDelta':10}),('Density',3,{'density':.5}),('Crossover',4,{'width':360,'brightHue':10}),('Crosstalk',5,{'rg':.1}),('Strip',6,{'separation':.5})]
report={'processor':platform.machine(),'method':'Single-thread C++ scalar core through Python binding; output allocation included; no host or real-time claim','measurements':[]}
for label,width,height in [('HD',1920,1080),('4K',3840,2160),('8K',7680,4320)]:
    line=np.linspace(0,2,width,dtype=np.float32)
    row=np.c_[.01+.3*line,.03+.4*line,.05+.6*line,np.full(width,.4)].astype(np.float32)
    image=np.broadcast_to(row,(height,width,4)).copy()
    for name,e,p in cases:
        c.process(e,image[:2],{'interpretation':1,**p})
        start=time.perf_counter();out=c.process(e,image,{'interpretation':1,**p});elapsed=time.perf_counter()-start
        assert np.all(np.isfinite(out));assert np.array_equal(out[:,:,3],image[:,:,3])
        measurement={'resolution':label,'width':width,'height':height,'effect':name,'seconds':elapsed,'megapixels_per_second':width*height/elapsed/1e6}
        report['measurements'].append(measurement);print(json.dumps(measurement),flush=True);del out
    del image
Path('research/output/cpu-benchmarks.json').write_text(json.dumps(report,indent=2)+'\n')
