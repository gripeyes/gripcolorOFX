#include "rendition/artist_models.hpp"
#include "rendition/primaries.hpp"
namespace rendition {
std::vector<Parameter> artistParameters(Effect e) {
 std::vector<Parameter> p;
 auto add=[&](std::string id,std::string label,double value,double lo,double hi,std::string group="Artist",std::string unit="fraction") {p.push_back({id,label,group,unit,value,lo,hi,{}});};
 if(e==Effect::Base) {
  p=primariesParameters();
  for(auto &d:p) d.group="Advanced tonal colour";
  for(auto &d:p) {
   if(d.id=="exposure" || d.id=="contrast" || d.id=="pivot" || d.id=="whiteLevel" || d.id=="shadowCompression" || d.id=="highlightCompression" || d.id=="midBalance" || d.id=="midTint" || d.id=="saturation" || d.id=="colourBalance" || d.id=="shadowTint" || d.id=="highlightTint") d.group="Artist";
   if(d.id=="whiteLevel")d.label="White";
   if(d.id=="shadowCompression")d.label="Toe";
   if(d.id=="highlightCompression")d.label="Shoulder";
   if(d.id=="midBalance")d.label="Warmth";
   if(d.id=="midTint")d.label="Tint";
   if(d.id=="colourBalance")d.label="Density";
   if(d.id=="shadowTint")d.label="Shadow Colour";
   if(d.id=="highlightTint")d.label="Highlight Colour";
  }
  p.erase(std::remove_if(p.begin(),p.end(),[](auto &d){return d.id=="blackLevel";}),p.end());
  add("blackStops","Black",0,-4,4,"Artist","stops weighted by shadow range; zero stays zero");
  add("highlightBurn","Highlight Burn",0,0,1,"Advanced tonal colour","coordinated compression/brilliance/chroma loss");
  add("localExposure","Dodge / Burn",0,-20,20,"Local exposure","stops through optional Matte alpha");
  add("localProtection","Range protection",0,0,1,"Local exposure","fraction protecting selected tail");
  add("localCenter","Protection center",3,-20,20,"Local exposure","stops relative to 0.18");
  add("localSoftness","Protection softness",1,.25,8,"Local exposure","stops");
  add("localChroma","Preserve chroma magnitude",0,0,1,"Local exposure","fraction; 0 scales RGB, 1 scales Y only");
 } else if(e==Effect::Palette) {
  add("separation","Separation",0,-1,1);add("compression","Compression",0,0,1);
  add("contamination","Contamination",0,-1,1);add("accent","Protected red accent",0,0,1);
  add("bias","Warm / Cool Bias",0,-1,1);add("shadowHue","Shadow Hue Bias",0,-90,90,"Artist","degrees");
  add("highlightHue","Highlight Hue Bias",0,-90,90,"Artist","degrees");add("colourDeath","Colour Death",0,0,1);
  add("trajectory","Trajectory strength",1,0,2);
  for(auto family:{"Red","Yellow","Green","Cyan","Blue","Magenta"})add(std::string("family")+family,std::string(family)+" direction",0,-60,60,"Colour families","degrees");
 } else {
  add("depth","Depth",0,0,1);add("density","Material Density",0,-1,1);
  add("coupling","Chroma Coupling",0,-1,1);add("separation","Separation",0,0,1);
  add("leakage","Leakage",.1,0,1);add("crosstalk","Crosstalk",0,-1,1);
  add("contamination","Contamination",0,-1,1);add("anchor","Red / skin anchor",0,0,1);
 }
 if(e==Effect::Base) {
  const std::vector<std::string> order={"exposure","contrast","pivot","blackStops","whiteLevel","shadowCompression","highlightCompression","midBalance","midTint","saturation","colourBalance","shadowTint","highlightTint"};
  auto rank=[&](const Parameter &d){auto it=std::find(order.begin(),order.end(),d.id);return it==order.end()?order.size():size_t(it-order.begin());};
  std::stable_sort(p.begin(),p.end(),[&](auto &a,auto &b){return rank(a)<rank(b);});
 }
 if(e!=Effect::Base)for(auto stage:e==Effect::Palette?std::vector<std::string>{"Volume","Crossover","Crosstalk","Primaries"}:std::vector<std::string>{"Density","Strip","Crosstalk"})p.push_back({stage+"Version",stage+" model","Expert","",0,0,0,{"v1 historical equations"}});
 return p;
}
Values baseValues(const Values &v) {
 Values out;for(auto &p:primariesParameters())out[p.id]=p.value;
 for(auto &p:primariesParameters())if(v.count(p.id))out[p.id]=v.at(p.id);
 out["blackLevel"]=0;out["blackStops"]=v.at("blackStops");
 double burn=v.at("highlightBurn");
 out["highlightCompression"]=1-(1-out["highlightCompression"])*(1-burn);
 out["highlightBleach"]=1-(1-out["highlightBleach"])*(1-burn);
 out["brillianceReduction"]+=burn;
 return out;
}
std::vector<std::pair<Effect,Values>> artistStages(Effect e,const Values &v) {
 Values common;for(auto k:{"interpretation","rx","ry","gx","gy","bx","by","wx","wy"})common[k]=v.at(k);
 auto V=[&](Values extra){auto x=common;x.insert(extra.begin(),extra.end());return x;};
 if(e==Effect::Palette) {
  auto volume=common;int i=0;
  for(auto family:{"Red","Yellow","Green","Cyan","Blue","Magenta"}) {
   auto k="v"+std::to_string(i++)+"_";
   double protect=i==1?1-v.at("accent"):1;
   volume[k+"chroma"]=1+protect*(.25*v.at("separation")-.7*v.at("compression"));
   volume[k+"hueDelta"]=v.at(std::string("family")+family)*v.at("trajectory")*protect;
  }
  return {{Effect::Volume,volume},{Effect::Crossover,V({{"width",360},{"darkHue",v.at("shadowHue")*v.at("trajectory")},{"brightHue",v.at("highlightHue")*v.at("trajectory")},{"darkChroma",1-v.at("colourDeath")}})},
   {Effect::Crosstalk,V({{"rg",v.at("separation")*.025},{"bg",v.at("separation")*.025}})},
   {Effect::Primaries,V({{"midBalance",v.at("bias")*.3},{"midTint",v.at("contamination")*.2}})}};
 }
 return {{Effect::Density,V({{"density",v.at("density")},{"chromaCoupling",v.at("coupling")}})},
  {Effect::Strip,V({{"separation",1-(1-v.at("separation"))*(1-.5*v.at("depth"))},{"leakage",v.at("leakage")},{"density",v.at("depth")},{"redAnchor",v.at("anchor")}})},
  {Effect::Crosstalk,V({{"rg",v.at("crosstalk")*.1},{"bg",v.at("crosstalk")*.1},{"gr",v.at("contamination")*.1},{"gb",v.at("contamination")*.1}})}};
}
std::array<float,4> localExposure(const Snapshot &base,std::array<float,4> p,float coverage) {
 if(!std::isfinite(coverage) || coverage<0 || coverage>1)throw std::domain_error("Matte alpha must be finite coverage in [0,1]");
 double stops=base.get("localExposure");if(stops==0 || coverage==0)return p;
 if(base.get("alphaMode") && p[3]==0)return p;
 Vec3 rgb{p[0],p[1],p[2]};float alpha=base.get("alphaMode")?p[3]:1;
 if(!finite(rgb) || !std::isfinite(alpha))throw std::domain_error("Nonfinite local exposure source");
 rgb=rgb*(1/alpha);auto xyz=base.toReferenceWhite()*(base.colorSpace().toXYZ*rgb);
 double ev=std::log2((std::abs(xyz.y)+.18*std::exp2(-20.))/.18);
 double weight=1-base.get("localProtection")/(1+std::exp(-(ev-base.get("localCenter"))/base.get("localSoftness")));
 double gain=std::exp2(stops*coverage*weight);Vec3 white=base.toReferenceWhite()*(base.colorSpace().toXYZ*Vec3{1,1,1});
 double chromaGain=gain*(1-base.get("localChroma"))+base.get("localChroma");
 auto result=white*float(xyz.y*gain)+(xyz-white*xyz.y)*float(chromaGain);
 result=base.colorSpace().fromXYZ*(base.fromReferenceWhite()*result);result=result*alpha;
 if(!finite(result))throw std::overflow_error("Local exposure overflow");
 return {result.x,result.y,result.z,p[3]};
}
}
