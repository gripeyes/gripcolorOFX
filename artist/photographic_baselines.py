"""Reuse M17 fitted parameters on approved photographic/CG content, without refitting."""
import json
import numpy as np
from PIL import Image,ImageDraw
from common import ROOT,read_scene,process,rgba,write_exr,Preview
from simplicity import exposure_saturation,matrix_curves,hue_curves,three_keys
OUT=ROOT/'build/artist-tests'
CASES=[('Density','Exposure + Saturation',exposure_saturation),('Strip','3x3 Matrix + monotone per-channel curves',matrix_curves),('Volume','Hue-vs-Hue / Hue-vs-Chroma curves',hue_curves),('Crossover','Three smooth luminance keys',three_keys)]
def main():
    models=json.loads((OUT/'baseline-models.json').read_text());preview=Preview();rows=[]
    for effect,label,fun in CASES:
        model=models[effect+'/'+label]
        for num in [5,7,60]:
            source=read_scene(OUT/f'aces-{num:04d}.exr');flat=source[...,:3].reshape(-1,3)
            baseline=rgba(fun(flat,np.array(model['parameters']))).reshape(source.shape);baseline[...,3]=source[...,3]
            candidate=process(effect,source,model['candidate_parameters']);assert np.isfinite(baseline).all() and np.isfinite(candidate).all()
            stem=f'{effect.lower()}-photo-{num:04d}'
            for suffix,image in [('baseline',baseline),('candidate',candidate)]:write_exr(OUT/(stem+'-'+suffix+'.exr'),image)
            sheet=Image.new('RGB',(1920,385));draw=ImageDraw.Draw(sheet);draw.text((8,3),effect+' | source / '+label+' / candidate | unchanged synthetic-fit parameters',(255,255,255))
            for i,img in enumerate([source,baseline,candidate]):sheet.paste(preview.image(img),(i*640,25))
            sheet.save(OUT/(stem+'-comparison.png'));rows.append({'effect':effect,'baseline':label,'source_frame':num,'nonfinite':0,'baseline_refit_on_photo':False,'artist_preference':None,'preview':stem+'-comparison.png'})
    (OUT/'photographic-baselines.json').write_text(json.dumps({'results':rows,'acceptance':'Pending; evaluate meaningful superiority, not residual error'},indent=2)+'\n')
if __name__=='__main__':main()
