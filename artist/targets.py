"""M15 visual targets and M16 synthetic rehearsal, using the user's selected DRT."""
from pathlib import Path
import json,time
import numpy as np
import colour
from PIL import Image,ImageDraw
from common import ROOT,SPEC,rgba,stack,write_exr,Preview,count_controls

OUT=ROOT/'build/artist-tests';OUT.mkdir(parents=True,exist_ok=True)
M=colour.RGB_COLOURSPACES['ITU-R BT.2020'].matrix_XYZ_to_RGB

def structured():
    width=768;height=360;h=np.linspace(0,2*np.pi,width,endpoint=False)
    light=.6*np.exp2(np.linspace(-9,3,height)/3)
    labs=np.stack(np.broadcast_arrays(light[:,None],.22*light[:,None]*np.cos(h),.22*light[:,None]*np.sin(h)),-1)
    image=rgba(colour.Oklab_to_XYZ(labs)@M.T)
    # Dedicated neutral, skin-like, blue/cyan/magenta and signed alpha edge bands.
    x=np.linspace(0,1,width)
    image[:24,:,:3]=(.18*np.exp2(-12+24*x))[None,:,None]
    skin=np.array([[.52,.34,.22],[.34,.16,.08],[.68,.56,.40],[.20,.25,.21]])
    for i,color in enumerate(skin):image[24+i*18:42+i*18,:,:3]=color[None,None,:]*np.exp2(-5+7*x)[None,:,None]
    image[-32:,:,0]=np.linspace(-.05,.05,width);image[-32:,:,1]=.2;image[-32:,:,2]=.6
    image[-16:,:,3]=np.linspace(0,1,width)
    return image

def cg_palette():
    width=768;height=360;y,x=np.mgrid[:height,:width];u=x/width;v=y/height
    rgb=np.zeros((height,width,3))+np.array([.025,.035,.045])
    rgb*=.25+v[...,None]
    colors=[[.55,.28,.12],[.48,.40,.28],[.05,.25,.34],[.08,.14,.05],[.46,.03,.02],[.16,.03,.23]]
    for index,color in enumerate(colors):
        cx=.1+.16*index;cy=.52;dx=(u-cx)/.074;dy=(v-cy)/.24;rr=dx*dx+dy*dy;mask=rr<1
        z=np.sqrt(np.maximum(1-rr,0));normal=np.stack([dx,dy,z],-1)
        light=np.maximum(normal@np.array([-.4,-.5,.768]),0)
        specular=np.maximum(normal@np.array([-.2,-.25,.947]),0)**45
        shade=np.array(color)*(.04+1.7*light[...,None])+specular[...,None]*1.5
        rgb[mask]=shade[mask]
    # HDR accent and a darker duplicate make exposure transfer observable.
    rgb[:,int(width*.95):]*=12
    return rgba(rgb)

def main():
    preview=Preview();images={'structured':structured(),'synthetic_cg':cg_palette()}
    report={'schema_version':1,'working_gamut':SPEC['working_gamut'],'preview':{key:SPEC[key] for key in ['ocio_config','display','view']},
            'representative_photography':'Pending user-approved paths','artist_acceptance':'Pending; no synthetic score grants acceptance','targets':[]}
    for name,image in images.items():write_exr(OUT/(name+'.exr'),image);np.save(OUT/(name+'.npy'),image);preview.write(OUT/(name+'.png'),image)
    for target in SPEC['targets']:
        start=time.perf_counter();row={'id':target['id'],'intent':target['intent'],**count_controls(target['recipe']),'human_interaction_seconds':None,'outputs':[]}
        contact=[]
        for name,image in images.items():
            output=stack(image,target['recipe']);assert np.all(np.isfinite(output));assert np.array_equal(output[...,3].view(np.uint32),image[...,3].view(np.uint32))
            filename=target['id']+'-'+name;write_exr(OUT/(filename+'.exr'),output);preview.write(OUT/(filename+'.png'),output)
            contact.extend([preview.image(image),preview.image(output)])
            row['outputs'].append({'source':name,'scene_file':filename+'.exr','preview_file':filename+'.png','reused_recipe':True,'nonfinite':0,'alpha_unchanged':True})
        sheet=Image.new('RGB',(1536,770),(20,20,20));draw=ImageDraw.Draw(sheet)
        draw.text((12,5),target['id']+' | source left / editable candidate right | Flawed Emulsion 2 / sRGB',(220,220,220))
        for index,image in enumerate(contact):sheet.paste(image,((index%2)*768,25+(index//2)*370))
        sheet.save(OUT/(target['id']+'-comparison.png'))
        row['render_seconds']=time.perf_counter()-start;row['artist_score']=None;report['targets'].append(row)
    report['reference_reconstruction']={'status':'Synthetic rehearsal run; formal challenge pending approved images','view_approved_by_user':True,'reference_images_approved':False,'no_extra_stock_transforms':True,'no_masks':True,'all_recipes_reused_on_two_synthetic_contents':True}
    (OUT/'artist-target-report.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'feedback-template.json').write_text(json.dumps({'schema_version':1,'reviewer':None,'session_start':None,'view':SPEC['view'],'targets':[{'id':t['id'],'useful':None,'coherence_1_to_5':None,'continuity_1_to_5':None,'preferred_candidate_or_baseline':None,'human_interaction_seconds':None,'reusable_on_second_image':None,'repeatable_deficiency':None} for t in SPEC['targets']]},indent=2)+'\n')
    print('Generated artist targets, float EXRs and DRT previews:',OUT)
if __name__=='__main__':main()
