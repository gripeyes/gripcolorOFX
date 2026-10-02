"""Approved ACES fixtures; verify AP0/D60 then convert explicitly through user OCIO."""
import hashlib,json
from pathlib import Path
import numpy as np
import OpenEXR,PyOpenColorIO as ocio
from PIL import Image,ImageDraw
from common import ROOT,SPEC,Preview,write_exr,stack,count_controls
OUT=ROOT/'build/artist-tests'
DATA=Path('/Users/j7s/Downloads/ACES_ODT_SampleFrames-main')
FRAMES=[4,5,7,14,23,60]
def main():
    names=(DATA/'resources/nuke/SampleFramesIndex.txt').read_text().splitlines()
    config=ocio.Config.CreateFromFile(SPEC['ocio_config'])
    cpu=config.getProcessor('ACES2065-1','Linear Rec.2020').getDefaultCPUProcessor();preview=Preview()
    report={'approved_by_user':True,'original_directory':str(DATA),'conversion':'ACES2065-1 AP0/D60 -> Linear Rec.2020/D65 through selected user OCIO config; no look applied','sampling':'Every third pixel, no filtering; evaluation fixture, not final-resolution quality evidence','assets':[]}
    sheet=Image.new('RGB',(1280,1120));draw=ImageDraw.Draw(sheet)
    target_report=[]
    for i,num in enumerate(FRAMES):
        source=DATA/'ACES_OT_VWG_SampleFrames'/f'ACES_OT_VWG_SampleFrames.{num:04d}.exr'
        f=OpenEXR.File(str(source),separate_channels=True);h=f.header()
        expected=[.7347,.2653,0,1,.0001,-.077,.32168,.33767]
        if h.get('acesImageContainerFlag')!=1 or not np.allclose(h.get('chromaticities'),expected,atol=1e-6):raise ValueError('Unresolved source interpretation: '+str(source))
        channels=f.channels();rgb=np.stack([channels[k].pixels[::3,::3] for k in 'RGB'],-1).astype(np.float32)
        cpu.apply(ocio.PackedImageDesc(rgb,rgb.shape[1],rgb.shape[0],3))
        alpha=channels['A'].pixels[::3,::3] if 'A' in channels else np.ones(rgb.shape[:2],np.float32)
        image=np.concatenate([rgb,alpha[...,None]],-1).astype(np.float32)
        if not np.isfinite(image).all():raise ValueError('Nonfinite approved source')
        tag=f'aces-{num:04d}';write_exr(OUT/(tag+'.exr'),image);preview.write(OUT/(tag+'.png'),image)
        p=preview.image(image);sheet.paste(p,((i%2)*640,(i//2)*370+20));draw.text(((i%2)*640+8,(i//2)*370),f'{num}: {names[num-1]}',(255,255,255))
        report['assets'].append({'frame':num,'name':names[num-1],'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scene_file':tag+'.exr','source_encoding':'scene-linear AP0/D60, verified ACES EXR flags/chromaticities','output_encoding':'scene-linear Rec.2020/D65','range':[float(rgb.min()),float(rgb.max())]})
        for target in SPEC['targets']:
            result=stack(image,target['recipe']);assert np.isfinite(result).all();assert np.array_equal(result[...,3],image[...,3])
            stem=target['id']+'-'+tag;write_exr(OUT/(stem+'.exr'),result)
            contact=Image.new('RGB',(1280,380));contact.paste(preview.image(image),(0,20));contact.paste(preview.image(result),(640,20));ImageDraw.Draw(contact).text((8,3),target['id']+' | source / candidate | Flawed Emulsion 2 / sRGB',(255,255,255));contact.save(OUT/(stem+'-comparison.png'))
            target_report.append({'target':target['id'],'source':tag,**count_controls(target['recipe']),'same_recipe_reused':True,'nonfinite':0,'alpha_unchanged':True,'human_interaction_seconds':None})
    sheet.save(OUT/'approved-sources.png')
    (OUT/'approved-assets.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'photographic-targets.json').write_text(json.dumps({'view':SPEC['view'],'results':target_report,'acceptance':'Pending artist comparison; these are starting recipes, not reconstructed independent target looks'},indent=2)+'\n')
    print('Converted and evaluated',len(report['assets']),'approved ACES frames')
if __name__=='__main__':main()
