"""Compare explicit approximation families on held-out spectral response matrices."""
import json
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator,CubicSpline
from spectral_lab import Lab
from fit_basis import WEIGHTS
lab=Lab();w=lab.grid;basis=np.array([np.exp(-.5*((w-c)/s)**2) for c,s in [(450,38),(545,42),(625,48)]]).T
B=(basis.T@lab.emission_weights).T;inv=np.linalg.inv(B)
train=np.linspace(0,1,129);test=np.linspace(.0003,.9997,237)
results={}
for model in ['KM','BeerLambert']:
    methods={}
    for weights in WEIGHTS:
        def oracle(d):
            spectra=[lab.pigment(weights,x*x*1.5).values if model=='KM' else lab.dye(weights,x*1.5,.1).values for x in d]
            return np.array([((basis*v[:,None]).T@lab.emission_weights).T@inv for v in spectra])
        reference=oracle(test);values=oracle(train)
        for degree in [3,5,9]:
            coefficients=np.polynomial.polynomial.polyfit(train,values.reshape(129,9),degree)
            predicted=np.polynomial.polynomial.polyval(test,coefficients).T.reshape(-1,3,3)
            label=f'polynomial degree {degree}'
            methods[label]=max(methods.get(label,0),float(np.max(np.abs(predicted-reference))))
        for count in [17,33,65,129]:
            grid=np.linspace(0,1,count);sparse=oracle(grid)
            linear=np.array([np.interp(test,grid,sparse[:,i,j]) for i in range(3) for j in range(3)]).T.reshape(-1,3,3)
            for label,predicted in [(f'linear table {count}',linear),(f'PCHIP {count}',PchipInterpolator(grid,sparse,axis=0)(test))]:
                methods[label]=max(methods.get(label,0),float(np.max(np.abs(predicted-reference))))
    results[model]=methods
report={'schema_version':1,'heldout_matrix_errors':results,'selected':'129-level linear response table / three emitted spectral basis coefficients','reason':'Simple shared CPU/Metal evaluator; convex interpolation retains nonnegative and concentration-monotone spectral response entries. Polynomial fits lack these guarantees without additional constraints. PCHIP is retained as a compact alternative, but requires more evaluator/coefficient logic. No opaque ML or runtime wavelength loop.','limits':'These are matrix-response error tests; they do not establish perceptual or artist acceptance.'}
Path('research/output/approximation-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
