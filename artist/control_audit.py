"""0.31 deterministic parameter response and effective-state audit; no artist approval inferred."""
from pathlib import Path
import json
import numpy as np
import _rendition as c
from artist.common import read_scene,Preview
from PIL import Image,ImageDraw
NAMES=['Scene','Tone','Volume','Density','Crossover','Crosstalk','Strip','Inspector','Primaries','Base','Palette','Material']
MAIN={
 'Base':{'exposure':'RGB × 2^E','contrast':'Slope-constrained stop contrast about pivot','pivot':'Stop contrast anchor; requires nonidentity shaping','blackStops':'Shadow-weighted stop displacement; zero stays zero','whiteLevel':'Highlight-weighted stop displacement; no cap','shadowCompression':'Soft toe slope displacement','highlightCompression':'Soft shoulder slope displacement','midBalance':'Midtone zero-Y warm/cool tint','midTint':'Midtone zero-Y magenta/green tint','saturation':'Zero-Y residual scale','colourBalance':'Colourfulness-conditioned stop gain','shadowTint':'Shadow zero-Y hue-direction amount','highlightTint':'Highlight zero-Y hue-direction amount'},
 'Palette':{'separation':'Volume chroma 1+.25S-.7C; Crosstalk rg/bg=.025S','compression':'Volume chroma 1+.25S-.7C','contamination':'Primaries midTint=.2C','accent':'Red family macro deformation ×(1-A); final source red-membership blend','bias':'Primaries midBalance=.3B','shadowHue':'Crossover darkHue=H×trajectory','highlightHue':'Crossover brightHue=H×trajectory','colourDeath':'Crossover darkChroma=1-D','trajectory':'Main and v2 expert family/trajectory hue and channel deltas ×T'},
 'Material':{'depth':'Strip separation=1-(1-S)(1-.5D); Strip density=D','density':'Density density=amount','coupling':'Density chromaCoupling=value','separation':'Strip separation=1-(1-S)(1-.5D)','leakage':'Strip leakage=value','crosstalk':'Crosstalk rg/bg=.1C','contamination':'Crosstalk gr/gb=.1C','anchor':'Strip redAnchor=value'}}

def run():
 out=Path('build/control-audit-0.31');out.mkdir(parents=True,exist_ok=True)
 prev=json.loads(Path('build/interfaces-0.3-before-0.31.json').read_text())['effects']
 t=np.geomspace(1e-6,100,96);neutral=np.repeat(t[:,None],3,axis=1)
 fam=np.array([[1,.01,.01],[1,.8,.01],[.01,1,.01],[.01,1,1],[.01,.01,1],[1,.01,1],[.65,.3,.18],[.2,.24,.06]],np.float32)
 chromatic=[]
 inv=np.linalg.inv(np.asarray(c.matrix(0)).reshape(3,3))
 for hue in np.arange(0,360,5):
  for rel in [.005,.02,.1,.5,1,2,5]:
   lab=[.55,.55*rel*np.cos(np.deg2rad(hue)),.55*rel*np.sin(np.deg2rad(hue))]
   chromatic.append(inv@np.asarray(c.opponent(lab,True)))
 structured=np.r_[neutral,chromatic,np.vstack([fam*2.**ev for ev in [-10,-3,0,5,10]]),[[-.2,.3,4],[0,0,0],[-1,-2,-3]]].astype('f4');rgba=np.c_[structured,np.ones(len(structured),np.float32)]
 view=Preview();samples=[read_scene(Path('build/artist-tests')/f'aces-{n:04d}.exr')[::3,::3] for n in [5,60]]
 rows=[];mainrows=[]
 for e in [9,10,11]:
  name=NAMES[e];defs=c.parameters(e)
  for d in defs:
   key=d['id'];base={'interpretation':1};conditions=[]
   config=d['group'] in ['Input','Custom primaries','Expert'] or key.endswith('Version')
   if config:
    rows.append({'effect':name,'parameter':d,'mapping':'Interpretation, alpha, fixed model metadata or version selection; not an image intention','domain':'External interpretation / model configuration','active_when':'Configuration-dependent; no creative pixel change promised','status':'configuration','artist_usefulness':'not applicable'});continue
   if e in [10,11]:base['modelVersion']=1
   if e==9:
    base.update(contrast=1.2,shadowCompression=.3,highlightCompression=.3,shadowTint=.25,highlightTint=.25,colourDeath=.3)
   elif e==10:base.update(separation=.2,compression=.2,shadowHue=15,highlightHue=-10,familyCyan=10)
   else:base.update(density=.3,separation=.3,depth=.2)
   if key in ['localProtection','localCenter','localSoftness','localChroma']:base.update(localExposure=1,localProtection=.5)
   if key in ['Crossover_hue','Crossover_softness']:base.update(Crossover_width=90,Crossover_midHue=20)
   if key in ['Density_hue','Density_softness']:base.update(Density_width=90,density=.5)
   if key=='Crossover_lookDomain':base['Crossover_midr']=.3
   if key=='Crosstalk_lookDomain':base['Crosstalk_domain']=1
   if key=='Crosstalk_rowSum':base['Crosstalk_mode']=2
   if key.startswith('Crossover_') and (key.endswith(('darkr','darkg','darkb','midr','midg','midb','brightr','brightg','brightb','lookDomain'))):base['Crossover_mode']=1;conditions.append('Channel trajectory mode')
   if key.startswith('Crosstalk_'):base.update(Crosstalk_m02=.15);base.setdefault('Crosstalk_mode',0);conditions.append('Active matrix; unconstrained unless mode tested')
   if 'matrixMix' in key:base[key.replace('matrixMix','m01')]=.2;conditions.append('Nonidentity local matrix')
   if '_m' in key and key.startswith('Volume_'):base[key.split('_m')[0]+'_matrixMix']=.5
   if key.startswith('Strip_m'):base['Strip_mode']=2;conditions.append('Custom record mode')
   if key in ['density','Density_density']:base['density']=0
   if key=='Strip_density':base['depth']=0
   if key=='Strip_leakage':base['leakage']=.1
   if key=='Strip_redAnchor':base['anchor']=0
   base[key]=d['default']
   try:reference=c.process(e,rgba,base)
   except Exception as ex:
    rows.append({'effect':name,'parameter':d,'status':'invalid audit fixture','error':str(ex)});continue
   values=[d['default']+(d['max']-d['default'])*s for s in [.1,.35,.7]]
   if d['min']<d['default']:values += [d['default']+(d['min']-d['default'])*s for s in [.1,.35,.7]]
   if d['choices']:values=list(range(len(d['choices'])))
   outcomes=[]
   for value in values:
    try:
     y=c.process(e,rgba,{**base,key:value});delta=y[:,:3]-reference[:,:3]
     outcomes.append({'value':value,'finite':bool(np.isfinite(y).all()),'max_rgb_difference':float(np.max(abs(delta))),'relative_difference':float(np.max(abs(delta)/np.maximum(abs(reference[:,:3]),1e-4))),'neutral_axis_difference':float(np.max(abs(y[:96,0]-y[:96,1]))),'alpha_exact':bool(np.array_equal(y[:,3],rgba[:,3]))})
    except Exception as ex:outcomes.append({'value':value,'error':str(ex)})
   mapping=MAIN[name].get(key)
   if not mapping:
    if '_' in key and key.split('_')[0] in NAMES:
     child,parameter=key.split('_',1);mapping='v2: expert selectors/choices override, chroma multiplier, Strip separation complement, otherwise macro + expert − historical default; hue/channel deltas ×trajectory where applicable'
    else:child='Base';parameter=key;mapping='Direct Base tonal parameter; XYZ/residual + monotone stop curve'
   else:child='shared stages' if e!=9 else 'Base';parameter=key
   valid=[x for x in outcomes if 'max_rgb_difference' in x];peak=max((x['max_rgb_difference'] for x in valid),default=0)
   row={'effect':name,'parameter':d,'underlying_operator':child,'underlying_parameter':parameter,'mapping':mapping,'domain':'XYZ/residual + stops' if e==9 else 'Per-stage: opponent / selected look / linear matrix / spectral-derived','expected_behavior':MAIN[name].get(key,d['label']),'active_when':conditions or ['Selection/range and stage activation; see effective state'],'activation_settings':base,'observations':outcomes,'status':'response measured' if peak>1e-7 else 'no visible numeric response in fixture','artist_usefulness':'pending visual/artist judgment; plumbing is not acceptance'}
   rows.append(row)
   if key not in MAIN[name]:
    # Advanced/expert sheets expose the same activated fixtures; failures remain visible.
    canvas=Image.new('RGB',(320*3,200*2));draw=ImageDraw.Draw(canvas)
    strengths=[d['default'],values[1] if len(values)>1 else values[0],values[-1]]
    for j,im in enumerate(samples):
     for k,value in enumerate(strengths):
      try:
       y=c.process(e,im,{**base,key:value});canvas.paste(view.image(y).resize((320,180)),(k*320,j*200+20));draw.text((k*320+4,j*200+2),f'{key} = {value:.3g}',fill='white')
      except Exception:draw.text((k*320+4,j*200+2),'Explicit invalid combined range',fill='red')
    canvas.save(out/f'{name}-{key}.png')
   if key in MAIN[name]:
    mainrows.append(row)
    # Main sheets show defaults separately from activated fixture; no view-space metrics.
    canvas=Image.new('RGB',(320*4,200*2));draw=ImageDraw.Draw(canvas)
    strengths=[d['default'],*values[:3]]
    for j,im in enumerate(samples):
     for k,value in enumerate(strengths):
      try:
       settings={**base,key:value};y=c.process(e,im,settings);img=view.image(y).resize((320,180));canvas.paste(img,(k*320,j*200+20));draw.text((k*320+4,j*200+2),f'{key} = {value:.3g}',fill='white')
      except Exception as ex:draw.text((k*320+4,j*200+2),'Explicit invalid combined range',fill='red')
    canvas.save(out/f'{name}-{key}.png')
    if d['min']<d['default']:
     canvas=Image.new('RGB',(320*4,200*2));draw=ImageDraw.Draw(canvas)
     strengths=[d['default'],*[d['default']+(d['min']-d['default'])*v for v in [.1,.35,.7]]]
     for j,im in enumerate(samples):
      for k,value in enumerate(strengths):
       try:
        y=c.process(e,im,{**base,key:value});canvas.paste(view.image(y).resize((320,180)),(k*320,j*200+20));draw.text((k*320+4,j*200+2),f'{key} = {value:.3g}',fill='white')
       except Exception:draw.text((k*320+4,j*200+2),'Explicit invalid combined range',fill='red')
     canvas.save(out/f'{name}-{key}-negative.png')
    # Signed pre-DRT RGB difference, displayed using explicit symmetric scale.
    im=samples[0];a=c.process(e,im,base);b=c.process(e,im,{**base,key:values[0]});diff=(b[:,:,:3]-a[:,:,:3]);scale=max(float(np.max(abs(diff))),1e-8)
    Image.fromarray(np.uint8(np.clip(.5+.5*diff/scale,0,1)*255)).save(out/f'{name}-{key}-difference.png')
 inventory=[]
 for name in ['Scene','Tone','Volume','Crossover','Crosstalk','Density','Strip']:
  for d in c.parameters(NAMES.index(name)):
   state='available only in Advanced'
   if name in ['Volume','Crossover','Crosstalk','Density','Strip'] and d['group'] not in ['Input','Custom primaries'] and d['id'] not in ['modelVersion','adapterVersion']:state='already exposed directly (v2 opt-in expert state)'
   if d['id']=='debug':state='diagnostic/research-only'
   inventory.append({'effect':name,'parameter':d,'classification':state,'note':'Main representation must be assessed by response; historical node remains unchanged'})
 # Saved parameter ordering/IDs/defaults remain exact; append-only choices allowed.
 compatibility=[]
 for e in [9,10,11]:
  now=c.parameters(e);old=prev[NAMES[e]]['parameters'];assert [d['id'] for d in now[:len(old)]]==[d['id'] for d in old]
  for a,b in zip(old,now):assert a['default']==b['default']
  compatibility.append({'effect':NAMES[e],'old_parameter_count':len(old),'new_parameter_count':len(now),'ordering_defaults_preserved':True})
 effective={name:c.artist_stages(e,{'interpretation':1,'modelVersion':1}) for name,e in [('Palette',10),('Material',11)]}
 report={'controls':rows,'main_controls':mainrows,'historical_inventory':inventory,'compatibility':compatibility,'effective_defaults':effective,'neutral_default':{NAMES[e]:{'bit_exact':bool(np.array_equal(c.process(e,rgba,{'interpretation':1}),rgba))} for e in [9,10,11]},'artist_acceptance':False}
 (out/'control-audit.json').write_text(json.dumps(report,indent=2)+'\n')
 html='<meta charset="utf-8"><title>Rendition 0.31 control audit</title><style>body{font:16px system-ui;background:#181a1e;color:#ddd;max-width:1300px;margin:auto}img{width:100%}a{color:#9bcafa}</style><h1>0.31 parameter response audit</h1><p>Activated fixtures, pre-DRT numerical differences. Viewed examples use external Flawed Emulsion 2. Not artist acceptance.</p><a href="control-audit.json">Mappings / sweep values / errors / inventories</a>'
 for row in mainrows:
  name=row['effect'];key=row['parameter']['id'];html+=f'<details><summary>{name} / {key}: {row["status"]}</summary><img src="{name}-{key}.png">'
  if (out/f'{name}-{key}-negative.png').exists():html+=f'<p>Negative strengths</p><img src="{name}-{key}-negative.png">'
  html+=f'<p>Signed RGB difference, symmetric normalized display</p><img src="{name}-{key}-difference.png"></details>'

 for row in rows:
  key=row['parameter']['id'];name=row['effect']
  if key not in MAIN[name] and (out/f'{name}-{key}.png').exists():html+=f'<details><summary>Advanced / {name} / {key}</summary><img src="{name}-{key}.png"></details>'
 (out/'index.html').write_text(html);print('Audited',len(rows),'controls;',len(mainrows),'Main sheets')
if __name__=='__main__':run()
