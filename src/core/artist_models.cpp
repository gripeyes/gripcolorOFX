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
  // Append only: historical Base IDs, ordering and defaults remain unchanged.
  add("temperature","Illuminant (daylight)",6504,4000,25000,"Illuminant","K; source estimate, 6504 neutral; lower cools correction, higher warms");
  add("illuminantTint","Illuminant tint",0,-.02,.02,"Illuminant","CIE 1960 v offset; distinct from creative Tint");
  p.push_back({"illuminantAdaptation","Illuminant adaptation","Illuminant","",0,0,2,{"Bradford","CAT16","XYZ scaling"}});
  p.push_back({"illuminantVersion","Illuminant compatibility","Expert","",1,0,1,{"Historical daylight approximation","CIE daylight"}});
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
 // Append persistent expert state after every historical artist parameter.
 if(e==Effect::Palette || e==Effect::Material) {
  auto stages=e==Effect::Palette?std::vector<Effect>{Effect::Volume,Effect::Crossover,Effect::Crosstalk}:std::vector<Effect>{Effect::Density,Effect::Strip,Effect::Crosstalk};
  for(auto stage:stages)for(auto d:parameters(stage)) {
   if(d.group=="Input" || d.group=="Custom primaries" || d.id=="modelVersion" || d.id=="adapterVersion")continue;
   std::string prefix=std::string(name(stage))+"_";
   if(stage==Effect::Crossover && d.id=="width")d.value=360;
   d.id=prefix+d.id;
   d.group=stage==Effect::Volume?"Families / "+d.group:stage==Effect::Crossover?"Trajectory / "+d.group:stage==Effect::Crosstalk?"Crosstalk Matrix / "+d.group:std::string(name(stage))+" / "+d.group;
   d.unit+="; model v2 composed expert state";
   p.push_back(d);
  }
 }
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
// Stored indices 0/1 are immutable historical mappings; index 2 bounds composition.
static std::vector<std::pair<Effect,Values>> composeArtistStages(std::vector<std::pair<Effect,Values>> stages,const Values &v) {
 bool enabled=v.at("modelVersion")>=1;
 bool safe=v.at("modelVersion")==2;
 for(auto &stage:stages)for(auto &d:parameters(stage.first)) {
  auto id=std::string(name(stage.first))+"_"+d.id;
  if(!v.count(id))continue;
  double expert=v.at(id);
  double expertDefault=stage.first==Effect::Crossover && d.id=="width"?360:d.value;
  if(!enabled) {
   if(expert!=expertDefault)throw std::invalid_argument("Select restored controls v2 before editing "+id);
   continue;
  }
  double base=stage.second.count(d.id)?stage.second.at(d.id):d.value;
  if(!d.choices.empty() || d.id=="debug" || d.id=="hue" || d.id=="width" || d.id=="chromaMin" || d.id=="chromaMax" || d.id=="evMin" || d.id=="evMax" || d.id=="softness" || d.id=="neutral" || (stage.first==Effect::Volume && d.group!="Expert" && ((d.id.find("_hue")!=std::string::npos && d.id.find("Delta")==std::string::npos) || d.id.find("_width")!=std::string::npos || d.id.find("_chromaMin")!=std::string::npos || d.id.find("_chromaMax")!=std::string::npos || d.id.find("_evMin")!=std::string::npos || d.id.find("_evMax")!=std::string::npos || d.id.find("_softness")!=std::string::npos || d.id.find("_neutral")!=std::string::npos)))stage.second[d.id]=expert;
  else if(safe) {
   // Expert deflections consume the remaining legal headroom. Neutral expert
   // state is exact macro behavior; neutral macro state is exact expert behavior.
   double delta=expert-d.value;
   double span=delta>=0?d.hi-d.value:d.value-d.lo;
   double f=span>0?delta/span:0;
   bool trajectory=(stage.first==Effect::Crossover && (d.id=="darkHue" || d.id=="midHue" || d.id=="brightHue" || d.group=="Channels")) || (stage.first==Effect::Volume && d.id.find("_hueDelta")!=std::string::npos);
   if(trajectory) {
    double t=v.count("trajectory")?v.at("trajectory"):1;
    f=t==0?0:t*f/(1+(t-1)*std::abs(f));
   }
   if(stage.first==Effect::Strip && d.id=="separation")stage.second[d.id]=1-(1-base)*(1-expert);
   else stage.second[d.id]=f==1?d.hi:f==-1?d.lo:base+f*(f>=0?d.hi-base:base-d.lo);
  }
  else if(d.id=="chroma" || d.id=="darkChroma" || d.id=="midChroma" || d.id=="brightChroma" || (stage.first==Effect::Volume && d.id.find("_chroma")!=std::string::npos && d.id.find("Min")==std::string::npos && d.id.find("Max")==std::string::npos))stage.second[d.id]=base*expert;
  else if(stage.first==Effect::Strip && d.id=="separation")stage.second[d.id]=1-(1-base)*(1-expert);
  else {
   double delta=expert-d.value;
   if(stage.first==Effect::Crossover && (d.id=="darkHue" || d.id=="midHue" || d.id=="brightHue" || d.group=="Channels"))delta*=v.count("trajectory")?v.at("trajectory"):1;
   if(stage.first==Effect::Volume && d.id.find("_hueDelta")!=std::string::npos)delta*=v.at("trajectory");
   stage.second[d.id]=base+delta;
  }
 }
 if(safe)for(auto &stage:stages) {
  if(stage.first==Effect::Strip) {
   // A custom record basis must be invertible throughout its editor range.
   // Full-controls records use positive diagonal gains and normalized signed
   // cross-record biases; strict row dominance guarantees nonsingularity.
   for(int row=0;row<3;++row) {
    std::string diagonal="m"+std::to_string(row)+std::to_string(row);
    double gain=std::exp2((stage.second.at(diagonal)-1)/4);
    double total=1;
    for(int col=0;col<3;++col)if(col!=row)total+=std::abs(stage.second.at("m"+std::to_string(row)+std::to_string(col)));
    for(int col=0;col<3;++col) {
     auto key="m"+std::to_string(row)+std::to_string(col);
     stage.second[key]=col==row?gain:.75*gain*stage.second.at(key)/total;
    }
   }
  }
  // Range endpoints describe one interval, including when animated endpoints cross.
  // Sorting coordinates changes neither stored knob and is continuous at equality.
  for(auto &d:parameters(stage.first))if(d.id.size()>=9 && d.id.substr(d.id.size()-9)=="chromaMin") {
   auto prefix=d.id.substr(0,d.id.size()-9);
   for(auto pair:{std::make_pair("chromaMin","chromaMax"),std::make_pair("evMin","evMax")}) {
    auto a=prefix+pair.first,b=prefix+pair.second;
    double av=stage.second.count(a)?stage.second.at(a):0;
    double bv=stage.second.count(b)?stage.second.at(b):0;
    if(av>bv)std::swap(stage.second[a],stage.second[b]);
   }
  }
  if(stage.first==Effect::Crossover && stage.second["darkPivot"]>stage.second["brightPivot"])std::swap(stage.second["darkPivot"],stage.second["brightPivot"]);
 }
 // Legacy composition remains unchanged; child snapshots validate every stage.
 return stages;
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
  std::vector<std::pair<Effect,Values>> result={{Effect::Volume,volume},{Effect::Crossover,V({{"width",360},{"darkHue",v.at("shadowHue")*v.at("trajectory")},{"brightHue",v.at("highlightHue")*v.at("trajectory")},{"darkChroma",1-v.at("colourDeath")}})},
   {Effect::Crosstalk,V({{"rg",v.at("separation")*.025},{"bg",v.at("separation")*.025}})},
   {Effect::Primaries,V({{"midBalance",v.at("bias")*.3},{"midTint",v.at("contamination")*.2}})}};
  return composeArtistStages(result,v);
 }
 std::vector<std::pair<Effect,Values>> result={{Effect::Density,V({{"density",v.at("density")},{"chromaCoupling",v.at("coupling")}})},
  {Effect::Strip,V({{"separation",1-(1-v.at("separation"))*(1-.5*v.at("depth"))},{"leakage",v.at("leakage")},{"density",v.at("depth")},{"redAnchor",v.at("anchor")}})},
  {Effect::Crosstalk,V({{"rg",v.at("crosstalk")*.1},{"bg",v.at("crosstalk")*.1},{"gr",v.at("contamination")*.1},{"gb",v.at("contamination")*.1}})}};
 return composeArtistStages(result,v);
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
