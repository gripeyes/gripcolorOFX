#pragma once
#include "operators.hpp"
namespace rendition {
inline std::string uiPage(Effect e,const Parameter &d) {
 if(e<Effect::Base)return d.group;
 if(d.group=="Artist")return "Main";
 if(d.group=="Input" || d.group=="Custom primaries" || d.group=="Expert" || d.id.find("Version")!=std::string::npos)return "Input / Compatibility";
 if(e==Effect::Base) {
  if(d.group=="Local exposure")return "Dodge-Burn";
  if(d.id=="highlightBurn" || d.id=="highlightBleach" || d.id=="brillianceReduction" || d.id=="midExposure" || d.id=="midDensity" || d.id=="midChroma")return "Advanced";
  return "Tonal Colour / Ranges";
 }
 if(d.id.rfind("Volume_v",0)==0)return "Families";
 if(d.id.rfind("Crossover_",0)==0)return d.group.find("Selection")!=std::string::npos?"Advanced":"Trajectory";
 if(d.id.rfind("Crosstalk_",0)==0)return "Crosstalk";
 if(d.id.rfind("Density_",0)==0)return "Density";
 if(d.id.rfind("Strip_",0)==0)return "Strip";
 return "Advanced";
}
inline bool customCoordinate(const std::string &id) {
 return id=="rx" || id=="ry" || id=="gx" || id=="gy" || id=="bx" || id=="by" || id=="wx" || id=="wy";
}
}
