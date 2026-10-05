// Portable editor properties; consumes the declarative schema, never writes grade values.
// The historical Advanced-node path is retained verbatim for compatibility.
#pragma once
void updatePresentation(Instance &i,double time=0) {
    auto value=[&](const std::string &id,double fallback=0.) {
        auto it=i.params.find(id);if(it==i.params.end())return fallback;
        auto d=std::find_if(i.defs.begin(),i.defs.end(),[&](auto &p){return p.id==id;});
        if(d!=i.defs.end() && !d->choices.empty()){int n=0;param->paramGetValueAtTime(it->second,time,&n);return double(n);}
        if(id=="editFamily"){int n=0;param->paramGetValueAtTime(it->second,time,&n);return double(n);}
        double n=0;param->paramGetValueAtTime(it->second,time,&n);return n;
    };
    if(i.effect>=Effect::Base) {
        // Presentation schema changes editor properties only, never parameter values.
        const auto hostName=str(host->host,kOfxPropName);
        const bool nukeHost=presentationUsesHostLinks(hostName);
        for(const auto &d:i.defs) {
            OfxPropertySetHandle q;
            if(param->paramGetPropertySet(i.params.at(d.id),&q)!=kOfxStatOK)continue;
            prop->propSetInt(q,kOfxParamPropEnabled,0,presentationEnabled(i.effect,d.id,value));
            if(!nukeHost)prop->propSetInt(q,kOfxParamPropSecret,0,presentationSecret(i.effect,d.id,value));
            double lo,hi;
            if(presentationRange(i.effect,d.id,value,lo,hi)) {
                if(d.id=="toeStart" || d.id=="shadowRange")prop->propSetDouble(q,kOfxParamPropDisplayMax,0,hi);
                else prop->propSetDouble(q,kOfxParamPropDisplayMin,0,lo);
            }
        }
        if(i.params.count("enableFullControls")) {
            OfxPropertySetHandle q;
            if(param->paramGetPropertySet(i.params.at("enableFullControls"),&q)==kOfxStatOK)
                prop->propSetInt(q,kOfxParamPropEnabled,0,presentationEnabled(i.effect,"enableFullControls",value));
        }
        return;
    }
    bool legacy=(i.effect==Effect::Palette || i.effect==Effect::Material) && value("modelVersion")==0;
    const bool legacyFull=(i.effect==Effect::Palette || i.effect==Effect::Material) && value("modelVersion")==1;
    for(auto &d:i.defs) {
        bool enabled=true,secret=false;
        if(customCoordinate(d.id))enabled=value("interpretation")==4;
        if(d.id.find("Version")!=std::string::npos){enabled=false;secret=i.effect>=Effect::Base;}
        bool child=d.id.rfind("Volume_",0)==0 || d.id.rfind("Crossover_",0)==0 || d.id.rfind("Crosstalk_",0)==0 || d.id.rfind("Density_",0)==0 || d.id.rfind("Strip_",0)==0;
        if(legacy && child)enabled=false;
        if(i.effect==Effect::Palette && d.id.rfind("Volume_v",0)==0 && d.id.size()>8)secret=int(d.id[8]-'0')!=int(value("editFamily"));
        if(d.id=="pivot")enabled=value("contrast",1)!=1 || value("shadowCompression")!=0 || value("highlightCompression")!=0 || value("midExposure")!=0 || value("midDensity")!=0 || value("blackStops")!=0 || value("whiteLevel")!=0 || value("colourBalance")!=0 || value("brillianceReduction")!=0 || value("highlightBurn")!=0;
        if(i.effect==Effect::Base && d.id=="shadowHue")enabled=value("shadowTint")!=0;
        if(i.effect==Effect::Base && d.id=="highlightHue")enabled=value("highlightTint")!=0;
        if(d.id=="deathStart" || d.id=="deathSoftness")enabled=value("colourDeath")!=0;
        if(d.id=="localProtection" || d.id=="localChroma")enabled=value("localExposure")!=0;
        if(d.id=="localCenter" || d.id=="localSoftness")enabled=value("localExposure")!=0 && value("localProtection")!=0;
        if(i.effect==Effect::Material && d.id=="coupling")enabled=value("density")!=0 || (!legacy && value("Density_density")!=0);
        if(i.effect==Effect::Material && (d.id=="leakage" || d.id=="anchor"))enabled=value("depth")!=0 || value("separation")!=0 || (!legacy && value("Strip_separation")!=0);
        if(d.id=="Crossover_lookDomain")enabled=!legacy && value("Crossover_mode")==1;
        if(d.id=="Crosstalk_lookDomain")enabled=!legacy && value("Crosstalk_domain")==1;
        if(d.id=="Crosstalk_rowSum")enabled=!legacy && value("Crosstalk_mode")==2;
        if(d.id.rfind("Crossover_",0)==0 && d.group.find("Channels")!=std::string::npos)enabled=!legacy && value("Crossover_mode")==1;
        if(d.id.rfind("Crossover_",0)==0 && (d.id.find("Hue")!=std::string::npos || d.id.find("Chroma")!=std::string::npos || d.id.find("Density")!=std::string::npos))enabled=!legacy && value("Crossover_mode")==0;
        if(d.id.rfind("Density_",0)==0 && d.id!="Density_density" && d.id!="Density_debug")enabled=!legacy && (value("density")!=0 || value("Density_density")!=0);
        if(d.id.rfind("Strip_m",0)==0 && d.id.size()==9 && std::isdigit(d.id[7]) && std::isdigit(d.id[8]))enabled=!legacy && value("Strip_mode")==2;
        if(d.id=="Strip_leakage" || d.id=="Strip_density" || d.id=="Strip_palette" || d.id=="Strip_neutralAnchor" || d.id=="Strip_redAnchor")enabled=!legacy && (value("depth")!=0 || value("separation")!=0 || value("Strip_separation")!=0);
        if(d.id.rfind("Volume_v",0)==0 && d.id.find("_matrixMix")!=std::string::npos) {
            const auto prefix=d.id.substr(0,d.id.rfind('_')+1);bool active=false;
            for(int r=0;r<3;r++)for(int c=0;c<3;c++)active=active || value(prefix+"m"+std::to_string(r)+std::to_string(c),r==c?1:0)!=(r==c?1:0);
            enabled=!legacy && active;
        }
        if(d.id=="Crosstalk_mix") {
            bool active=value("crosstalk")!=0 || value("contamination")!=0;
            for(int r=0;r<3;r++)for(int c=0;c<3;c++)active=active || value("Crosstalk_m"+std::to_string(r)+std::to_string(c),r==c?1:0)!=(r==c?1:0);
            for(auto id:{"Crosstalk_rg","Crosstalk_rb","Crosstalk_gr","Crosstalk_gb","Crosstalk_br","Crosstalk_bg"})active=active || value(id)!=0;
            enabled=!legacy && active;
        }
        // Unsafe historical additive composition stays renderable, but immutable
        // in the ordinary UI until deliberate migration. Never rewrite old values.
        if(legacyFull && d.group!="Input" && d.group!="Custom primaries")enabled=false;
        OfxPropertySetHandle q;if(param->paramGetPropertySet(i.params.at(d.id),&q)==kOfxStatOK){
          prop->propSetInt(q,kOfxParamPropEnabled,0,enabled);
          auto hostName=str(host->host,kOfxPropName);
          if(!presentationUsesHostLinks(hostName))prop->propSetInt(q,kOfxParamPropSecret,0,secret);
          if(i.effect==Effect::Base) {
           if(d.id=="toeStart")prop->propSetDouble(q,kOfxParamPropDisplayMax,0,std::min(d.hi,value("shoulderStart")));
           if(d.id=="shoulderStart")prop->propSetDouble(q,kOfxParamPropDisplayMin,0,std::max(d.lo,value("toeStart")));
           if(d.id=="shadowRange")prop->propSetDouble(q,kOfxParamPropDisplayMax,0,std::min(d.hi,value("highlightRange")));
           if(d.id=="highlightRange")prop->propSetDouble(q,kOfxParamPropDisplayMin,0,std::max(d.lo,value("shadowRange")));
          }
        }
    }
    if(i.params.count("enableFullControls")){OfxPropertySetHandle q;param->paramGetPropertySet(i.params.at("enableFullControls"),&q);prop->propSetInt(q,kOfxParamPropEnabled,0,i.effect!=Effect::Base && value("modelVersion")!=2);}
}
