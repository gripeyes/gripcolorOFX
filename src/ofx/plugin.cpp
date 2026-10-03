#include "ofxColour.h"
#include "ofxGPURender.h"
#include "ofxImageEffect.h"
#include "ofxMessage.h"
#include "ofxMultiThread.h"
#include "ofxParam.h"
#include "rendition/operators.hpp"
#include "rendition/artist_models.hpp"
#include "rendition/ui_layout.hpp"
#include <algorithm>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <mutex>
using namespace rendition;
namespace {
OfxHost *host = nullptr;
const OfxImageEffectSuiteV1 *fx = nullptr;
const OfxPropertySuiteV1 *prop = nullptr;
const OfxParameterSuiteV1 *param = nullptr;
const OfxMessageSuiteV2 *msg = nullptr;
const OfxMessageSuiteV1 *msg1 = nullptr;
const OfxMultiThreadSuiteV1 *threads = nullptr;
std::mutex loadMutex;
void checked(OfxStatus s) {
    if (s != kOfxStatOK)
        throw std::runtime_error("OFX suite operation failed: " + std::to_string(s));
}
std::string str(OfxPropertySetHandle p, const char *k) {
    char *c = nullptr;
    if (!p || prop->propGetString(p, k, 0, &c) != kOfxStatOK || !c)
        return {};
    return c;
}
void setHost(OfxHost *h) {
    host = h;
}
void suites() {
    std::lock_guard<std::mutex> lock(loadMutex);
    if (fx)
        return;
    auto f =
        static_cast<const OfxImageEffectSuiteV1 *>(host->fetchSuite(host->host, kOfxImageEffectSuite, 1));
    auto p = static_cast<const OfxPropertySuiteV1 *>(host->fetchSuite(host->host, kOfxPropertySuite, 1));
    auto a = static_cast<const OfxParameterSuiteV1 *>(host->fetchSuite(host->host, kOfxParameterSuite, 1));
    if (!f || !p || !a)
        throw std::runtime_error("Required OFX suites unavailable");
    prop = p;
    param = a;
    msg = static_cast<const OfxMessageSuiteV2 *>(host->fetchSuite(host->host, kOfxMessageSuite, 2));
    msg1 = static_cast<const OfxMessageSuiteV1 *>(host->fetchSuite(host->host, kOfxMessageSuite, 1));
    threads =
        static_cast<const OfxMultiThreadSuiteV1 *>(host->fetchSuite(host->host, kOfxMultiThreadSuite, 1));
    fx = f;
    if (std::getenv("RENDITION_TRACE"))
        std::fprintf(stderr, "Rendition message suites V2=%p V1=%p\n", static_cast<const void *>(msg),
                     static_cast<const void *>(msg1));
}
void error(const void *h, const std::string &s) {
    if (msg)
        msg->setPersistentMessage(const_cast<void *>(h), kOfxMessageError, "rendition.validation", "%s",
                                  s.c_str());
    else if (msg1)
        msg1->message(const_cast<void *>(h), kOfxMessageError, "rendition.validation", "%s", s.c_str());
    else
        std::fprintf(stderr, "Rendition: %s\n", s.c_str());
}
struct Instance {
    Effect effect;
    std::vector<Parameter> defs;
    std::map<std::string, OfxParamHandle> params;
    OfxImageClipHandle source = nullptr, output = nullptr, reference = nullptr;
    OfxPropertySetHandle sourceProps = nullptr, referenceProps = nullptr;
    OfxParamHandle hostSceneLinear = nullptr;
    bool generator = false;
};
Instance *instance(OfxImageEffectHandle h) {
    OfxPropertySetHandle p;
    checked(fx->getPropertySet(h, &p));
    void *v = nullptr;
    checked(prop->propGetPointer(p, kOfxPropInstanceData, 0, &v));
    if (!v)
        throw std::runtime_error("Missing Rendition instance");
    return static_cast<Instance *>(v);
}
Values values(Instance &i, double t) {
    Values v;
    for (auto &d : i.defs) {
        if (d.choices.empty()) {
            double x;
            checked(param->paramGetValueAtTime(i.params.at(d.id), t, &x));
            v[d.id] = x;
        } else {
            int x;
            checked(param->paramGetValueAtTime(i.params.at(d.id), t, &x));
            v[d.id] = x;
        }
    }
    if (std::getenv("RENDITION_TRACE"))
        std::fprintf(stderr, "Rendition snapshot interpretation=%g alpha=%g exposure=%g\n",
                     v["interpretation"], v["alphaMode"], v.count("exposure") ? v["exposure"] : 0);
    return v;
}
// Nuke resolves its OCIO scene_linear role through the startup host bridge.
// 0: no bridge (native clip metadata); 1: explicitly unresolved; 2..4: known gamut.
std::string inputInterpretation(Instance &i, const Values &v, OfxPropertySetHandle clipProps) {
    if (int(v.at("interpretation")) == 0 && i.hostSceneLinear) {
        int role = 0;
        checked(param->paramGetValue(i.hostSceneLinear, &role));
        if (role == 1) return {};
        if (role == 2) return "Linear Rec.2020";
        if (role == 3) return "ACEScg";
        if (role == 4) return "Linear Rec.709";
        if (role != 0) throw std::invalid_argument("Invalid scene_linear host interpretation");
    }
    return str(clipProps, kOfxImageClipPropColourspace);
}
struct Image {
    OfxPropertySetHandle handle = nullptr;
    ImageView view{};
    OfxRectD rod{};
    Image(OfxImageClipHandle clip, double t, bool matte=false) {
        checked(fx->clipGetImage(clip, t, nullptr, &handle));
        try {
            void *data = nullptr;
            checked(prop->propGetPointer(handle, kOfxImagePropData, 0, &data));
            if (!data)
                throw std::runtime_error("Missing image data");
            if (str(handle, kOfxImageEffectPropPixelDepth) != kOfxBitDepthFloat)
                throw std::runtime_error("Rendition requires 32-bit float images");
            auto components = str(handle, kOfxImageEffectPropComponents);
            int n = components == kOfxImageComponentRGBA ? 4 : components == kOfxImageComponentRGB ? 3 : matte && components == kOfxImageComponentAlpha ? 1 : 0;
            if (!n || (matte && n==3))
                throw std::runtime_error("Rendition requires RGB or RGBA");
            int rect[4], bytes;
            checked(prop->propGetIntN(handle, kOfxImagePropBounds, 4, rect));
            checked(prop->propGetInt(handle, kOfxImagePropRowBytes, 0, &bytes));
            if (rect[2] < rect[0] || rect[3] < rect[1] ||
                std::abs(int64_t(bytes)) < int64_t(rect[2] - rect[0]) * n * sizeof(float))
                throw std::runtime_error("Invalid image bounds or row stride");
            view = {static_cast<float *>(data), rect[0], rect[1], rect[2], rect[3], bytes, n};
            checked(fx->clipGetRegionOfDefinition(clip, t, &rod));
        } catch (...) {
            fx->clipReleaseImage(handle);
            handle = nullptr;
            throw;
        }
    }
    ~Image() {
        if (handle)
            fx->clipReleaseImage(handle);
    }
    Image(const Image &) = delete;
};
bool connected(OfxPropertySetHandle p) {
    int value = 0;
    if (p)
        prop->propGetInt(p, kOfxImageClipPropConnected, 0, &value);
    return value != 0;
}
OfxStatus describe(Effect e, OfxImageEffectHandle h) {
    OfxPropertySetHandle p;
    checked(fx->getPropertySet(h, &p));
    std::string label = "Rendition " + std::string(name(e));
    checked(prop->propSetString(p, kOfxPropLabel, 0, label.c_str()));
    checked(prop->propSetString(p, kOfxImageEffectPluginPropGrouping, 0, e>=Effect::Base || e==Effect::Inspector ? "Rendition" : "Rendition/Advanced"));
    checked(prop->propSetString(p, kOfxPropPluginDescription, 0,
                                "Scene-compatible color rendition research suite. CPU reference. Production "
                                "host/model gates are not yet accepted."));
    checked(prop->propSetString(p, kOfxImageEffectPropSupportedContexts, 0,
                                e == Effect::Inspector ? kOfxImageEffectContextGeneral
                                                       : kOfxImageEffectContextFilter));
    checked(prop->propSetString(p, kOfxImageEffectPropSupportedContexts, 1,
                                e == Effect::Inspector ? kOfxImageEffectContextFilter
                                                       : kOfxImageEffectContextGeneral));
    if (e == Effect::Inspector)
        checked(
            prop->propSetString(p, kOfxImageEffectPropSupportedContexts, 2, kOfxImageEffectContextGenerator));
    checked(prop->propSetString(p, kOfxImageEffectPropSupportedPixelDepths, 0, kOfxBitDepthFloat));
    checked(prop->propSetInt(p, kOfxImageEffectPropSupportsTiles, 0, 1));
    checked(prop->propSetInt(p, kOfxImageEffectPropSupportsMultiResolution, 0, 1));
    checked(prop->propSetInt(p, kOfxImageEffectPropTemporalClipAccess, 0, 0));
    checked(
        prop->propSetString(p, kOfxImageEffectPluginRenderThreadSafety, 0, kOfxImageEffectRenderFullySafe));
    checked(prop->propSetInt(p, kOfxImageEffectPluginPropHostFrameThreading, 0, 1));
    // No preferred input color space: do not request conversions. Core native metadata only.
    prop->propSetString(p, kOfxImageEffectPropColourManagementStyle, 0, kOfxImageEffectColourManagementCore);
    prop->propSetString(p, kOfxImageEffectPropColourManagementAvailableConfigs, 0,
                        "ofx-native-v1.5_aces-v1.3_ocio-v2.3");
    prop->propSetString(p, kOfxImageEffectPropMetalRenderSupported, 0, "false");
    return kOfxStatOK;
}
OfxStatus describeContext(Effect e, OfxImageEffectHandle h, OfxPropertySetHandle in) {
    auto context = str(in, kOfxImageEffectPropContext);
    auto clip = [&](const char *n, bool optional) {
        OfxPropertySetHandle p;
        checked(fx->clipDefine(h, n, &p));
        checked(prop->propSetString(p, kOfxImageEffectPropSupportedComponents, 0, kOfxImageComponentRGBA));
        checked(prop->propSetString(p, kOfxImageEffectPropSupportedComponents, 1, kOfxImageComponentRGB));
        checked(prop->propSetInt(p, kOfxImageClipPropOptional, 0, optional));
        checked(prop->propSetInt(p, kOfxImageEffectPropSupportsTiles, 0, 1));
    };
    clip(kOfxImageEffectOutputClipName, false);
    if (context != kOfxImageEffectContextGenerator) {
        clip(kOfxImageEffectSimpleSourceClipName,
             e == Effect::Inspector && context == kOfxImageEffectContextGeneral);
        if (e == Effect::Inspector)clip("Reference", true);
        if(e==Effect::Base) {
            OfxPropertySetHandle p;checked(fx->clipDefine(h,"Matte",&p));
            checked(prop->propSetString(p,kOfxImageEffectPropSupportedComponents,0,kOfxImageComponentAlpha));
            checked(prop->propSetString(p,kOfxImageEffectPropSupportedComponents,1,kOfxImageComponentRGBA));
            checked(prop->propSetInt(p,kOfxImageClipPropOptional,0,1));
            checked(prop->propSetInt(p,kOfxImageClipPropIsMask,0,1));
            checked(prop->propSetInt(p,kOfxImageEffectPropSupportsTiles,0,1));
        }
    }
    OfxParamSetHandle set;
    checked(fx->getParamSet(h, &set));
    OfxPropertySetHandle roleProps;
    checked(param->paramDefine(set, kOfxParamTypeChoice, "hostSceneLinear", &roleProps));
    checked(prop->propSetInt(roleProps, kOfxParamPropDefault, 0, 0));
    checked(prop->propSetInt(roleProps, kOfxParamPropSecret, 0, 1));
    checked(prop->propSetInt(roleProps, kOfxParamPropPersistant, 0, 0));
    checked(prop->propSetInt(roleProps, kOfxParamPropAnimates, 0, 0));
    const char *roles[] = {"No host bridge", "Interpretation required", "Linear Rec.2020", "ACEScg", "Linear Rec.709"};
    for (int n = 0; n < 5; ++n)
        checked(prop->propSetString(roleProps, kOfxParamPropChoiceOption, n, roles[n]));
    auto defs = parameters(e);
    // Keep original eight group IDs stable; new prototype IDs use portable characters.
    auto groupId=[&](std::string group) {
        if(e>=Effect::Primaries) for(char &c:group) if(c==' ' || c=='/') c='_';
        return std::string("group_")+group;
    };
    const auto hostName=str(host->host,kOfxPropName);
    const bool nukePages=e>=Effect::Base && (hostName.find("nuke")!=std::string::npos || hostName.find("Nuke")!=std::string::npos);
    std::vector<std::string> groups;
    if(e>=Effect::Base) {
        groups.push_back("Artist");OfxPropertySetHandle p;
        checked(param->paramDefine(set,kOfxParamTypeGroup,groupId("Artist").c_str(),&p));
        prop->propSetString(p,kOfxPropLabel,0,"Artist");prop->propSetInt(p,kOfxParamPropGroupOpen,0,1);
    }
    if (e == Effect::Volume) {
        for (auto family : {"Red", "Yellow", "Green", "Cyan", "Blue", "Magenta"}) {
            groups.push_back(family);
            OfxPropertySetHandle p;
            checked(
                param->paramDefine(set, kOfxParamTypeGroup, ("group_" + std::string(family)).c_str(), &p));
            checked(prop->propSetString(p, kOfxPropLabel, 0, family));
            prop->propSetInt(p, kOfxParamPropGroupOpen, 0, 0);
        }
    }
    for (auto &d : defs)
        if (std::find(groups.begin(), groups.end(), d.group) == groups.end()) {
            groups.push_back(d.group);
            OfxPropertySetHandle p;
            checked(param->paramDefine(set, kOfxParamTypeGroup, groupId(d.group).c_str(), &p));
            checked(prop->propSetString(p, kOfxPropLabel, 0, d.group.c_str()));
            if (e == Effect::Volume && (d.group.find(" matrix") != std::string::npos ||
                                        d.group.find(" selection") != std::string::npos)) {
                auto family = d.group.substr(0, d.group.find(' '));
                checked(prop->propSetString(p, kOfxParamPropParent, 0, ("group_" + family).c_str()));
            }
            prop->propSetInt(p, kOfxParamPropGroupOpen, 0, d.group == "Artist" || d.group == "Input" || (e==Effect::Primaries && d.group!="Expert" && d.group!="Custom primaries"));
        }
    for (auto &d : defs) {
        OfxPropertySetHandle p;
        checked(param->paramDefine(set, d.choices.empty() ? kOfxParamTypeDouble : kOfxParamTypeChoice,
                                   d.id.c_str(), &p));
        checked(prop->propSetString(p, kOfxPropLabel, 0, d.label.c_str()));
        checked(prop->propSetString(p, kOfxParamPropParent, 0, groupId(d.group).c_str()));
        std::string hint = d.unit.empty() ? d.label : d.label + " (" + d.unit + ")";
        if(d.id=="pivot")hint+=". Used by nonidentity tone shaping; inactive at neutral tone settings.";
        if(d.id=="Crosstalk_mix")hint+=". Blend an authored matrix; identity matrix has no visible effect.";
        if(d.id=="coupling" || d.id=="Density_chromaCoupling")hint+=". Requires nonzero Material Density.";
        if(d.id=="leakage" || d.id=="Strip_leakage")hint+=". Requires active record separation.";
        if(d.id=="anchor" || d.id=="Strip_redAnchor" || d.id=="Strip_neutralAnchor")hint+=". Protects an existing deformation; does not create one.";
        if(d.id=="blackStops" || d.id=="whiteLevel")hint+=". Tonal exposure displacement, never an output clamp.";
        if (d.id == "interpretation")
            hint += ". Auto uses the Nuke OCIO scene_linear role; unresolved roles/metadata fail. Manual interpretation overrides and does not transform pixels.";
        checked(prop->propSetString(p, kOfxParamPropHint, 0, hint.c_str()));
        checked(prop->propSetInt(p, kOfxParamPropEvaluateOnChange, 0, 1));
        if (d.choices.empty()) {
            checked(prop->propSetDouble(p, kOfxParamPropDefault, 0, d.value));
            checked(prop->propSetDouble(p, kOfxParamPropMin, 0, d.lo));
            checked(prop->propSetDouble(p, kOfxParamPropMax, 0, d.hi));
            checked(prop->propSetDouble(p, kOfxParamPropDisplayMin, 0, d.lo));
            checked(prop->propSetDouble(p, kOfxParamPropDisplayMax, 0, d.hi));
        } else {
            checked(prop->propSetInt(p, kOfxParamPropDefault, 0, int(d.value)));
            for (size_t i = 0; i < d.choices.size(); i++)
                checked(prop->propSetString(p, kOfxParamPropChoiceOption, int(i), d.choices[i].c_str()));
        }
        if (d.id == "modelVersion" || d.id == "adapterVersion" || d.id.find("Version")!=std::string::npos) {
            prop->propSetInt(p, kOfxParamPropAnimates, 0, 0);
            prop->propSetInt(p, kOfxParamPropEnabled, 0, 0);
            if(e>=Effect::Base)prop->propSetInt(p,kOfxParamPropSecret,0,1);
        }
    }
    if(e>=Effect::Base) {
        OfxPropertySetHandle q;
        checked(param->paramDefine(set,kOfxParamTypePushButton,"enableFullControls",&q));
        prop->propSetString(q,kOfxPropLabel,0,"Enable full controls");
        prop->propSetString(q,kOfxParamPropHint,0,"Deliberate migration to bounded Main/Expert composition. Historical equations are retained until this action. Undo is supported; appearance can change with non-neutral Expert settings.");
        prop->propSetInt(q,kOfxParamPropEvaluateOnChange,0,0);
        if(e==Effect::Base)prop->propSetInt(q,kOfxParamPropSecret,0,1);
        if(e==Effect::Palette) {
            checked(param->paramDefine(set,kOfxParamTypeChoice,"editFamily",&q));
            prop->propSetString(q,kOfxPropLabel,0,"Family");
            prop->propSetInt(q,kOfxParamPropDefault,0,0);
            prop->propSetInt(q,kOfxParamPropAnimates,0,0);
            prop->propSetInt(q,kOfxParamPropEvaluateOnChange,0,0);
            int n=0;for(auto label:{"Red","Yellow","Green","Cyan","Blue","Magenta"})prop->propSetString(q,kOfxParamPropChoiceOption,n++,label);
        }
        std::vector<std::string> pages;
        for(auto &d:defs) {auto page=uiPage(e,d);if(std::find(pages.begin(),pages.end(),page)==pages.end())pages.push_back(page);}
        auto compatibility=std::find(pages.begin(),pages.end(),"Input / Compatibility");
        if(compatibility!=pages.end()){pages.erase(compatibility);pages.push_back("Input / Compatibility");}
        OfxPropertySetHandle effectProps;fx->getPropertySet(h,&effectProps);
        int pageIndex=0;
        for(auto &page:pages) {
            std::string id="page_"+page;for(char &c:id)if(c==' ' || c=='/' || c=='-')c='_';
            checked(param->paramDefine(set,kOfxParamTypePage,id.c_str(),&q));
            prop->propSetString(q,kOfxPropLabel,0,page.c_str());
            prop->propSetString(effectProps,kOfxPluginPropParamPageOrder,pageIndex++,id.c_str());
            int child=0;
            if(page=="Families")prop->propSetString(q,kOfxParamPropPageChild,child++,"editFamily");
            for(auto &d:defs)if(uiPage(e,d)==page)prop->propSetString(q,kOfxParamPropPageChild,child++,d.id.c_str());
            if(page=="Input / Compatibility")prop->propSetString(q,kOfxParamPropPageChild,child++,"enableFullControls");
        }
    }
    OfxPropertySetHandle semanticProperty;
    checked(param->paramDefine(set, kOfxParamTypeString, "semanticReference", &semanticProperty));
    checked(prop->propSetString(semanticProperty, kOfxPropLabel, 0, "Semantic reference (default model)"));
    checked(prop->propSetString(semanticProperty, kOfxParamPropParent, 0, "group_Expert"));
    checked(prop->propSetString(semanticProperty, kOfxParamPropStringMode, 0, kOfxParamStringIsMultiLine));
    if(nukePages)prop->propSetInt(semanticProperty,kOfxParamPropSecret,0,1);
    prop->propSetInt(semanticProperty, kOfxParamPropEnabled, 0, 0);
    prop->propSetInt(semanticProperty, kOfxParamPropAnimates, 0, 0);
    std::string summary = "Default model reference. Configuration-dependent details: docs/interfaces.json "
                          "and headless evaluator.\n";
    for (int index = e == Effect::Inspector ? 0 : int(e); index <= (e == Effect::Inspector ? 11 : int(e));
         index++) {
        auto model = Effect(index);
        auto semantic = semantics(model);
        summary += std::string(name(model)) + ": " + semantic.domain + "; " + semantic.reference +
                   "; exposure " + semantic.exposure + "; negative " + semantic.negative + "; HDR " +
                   semantic.hdr + "; " + semantic.status + "\n";
    }
    checked(prop->propSetString(semanticProperty, kOfxParamPropDefault, 0, summary.c_str()));
    return kOfxStatOK;
}
void updatePresentation(Instance &i,double time=0) {
    auto value=[&](const std::string &id,double fallback=0.) {
        auto it=i.params.find(id);if(it==i.params.end())return fallback;
        auto d=std::find_if(i.defs.begin(),i.defs.end(),[&](auto &p){return p.id==id;});
        if(d!=i.defs.end() && !d->choices.empty()){int n=0;param->paramGetValueAtTime(it->second,time,&n);return double(n);}
        if(id=="editFamily"){int n=0;param->paramGetValue(it->second,&n);return double(n);}
        double n=0;param->paramGetValueAtTime(it->second,time,&n);return n;
    };
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
          if(hostName.find("nuke")==std::string::npos && hostName.find("Nuke")==std::string::npos)prop->propSetInt(q,kOfxParamPropSecret,0,secret);
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
OfxStatus create(Effect e, OfxImageEffectHandle h) {
    auto i = std::make_unique<Instance>();
    i->effect = e;
    i->defs = parameters(e);
    OfxPropertySetHandle p;
    checked(fx->getPropertySet(h, &p));
    i->generator = str(p, kOfxImageEffectPropContext) == kOfxImageEffectContextGenerator;
    OfxParamSetHandle set;
    checked(fx->getParamSet(h, &set));
    checked(param->paramGetHandle(set, "hostSceneLinear", &i->hostSceneLinear, nullptr));
    for (auto &d : i->defs) {
        OfxParamHandle q;
        checked(param->paramGetHandle(set, d.id.c_str(), &q, nullptr));
        i->params[d.id] = q;
    }
    checked(fx->clipGetHandle(h, kOfxImageEffectOutputClipName, &i->output, nullptr));
    if (!i->generator) {
        checked(fx->clipGetHandle(h, kOfxImageEffectSimpleSourceClipName, &i->source, &i->sourceProps));
        if (e == Effect::Inspector || e==Effect::Base)
            checked(fx->clipGetHandle(h, e==Effect::Base?"Matte":"Reference", &i->reference, &i->referenceProps));
    }
    checked(prop->propSetPointer(p, kOfxPropInstanceData, 0, i.get()));
    if(e>=Effect::Base) {
        OfxParamHandle q;checked(param->paramGetHandle(set,"enableFullControls",&q,nullptr));i->params["enableFullControls"]=q;
        if(e==Effect::Palette){checked(param->paramGetHandle(set,"editFamily",&q,nullptr));i->params["editFamily"]=q;}
    }
    updatePresentation(*i);
    i.release();
    return kOfxStatOK;
}
// Generated chart XYZ values are supplied by the same offline provenance pipeline.
#include "chart.inc"
Vec3 diagnostic(const Snapshot &s, int mode, float u, float v, Vec3 rgb, Vec3 reference) {
    float t = std::clamp(u, 0.f, 1.f), y = std::clamp(v, 0.f, 1.f),
          ev = s.get("evMin") + (s.get("evMax") - s.get("evMin")) * t;
    if (mode == 0)
        return rgb;
    if (mode == 1) {
        float n = .18f * std::exp2(ev);
        return {n, n, n};
    }
    if (mode == 2)
        return {t, t, t};
    if (mode == 3) {
        int row = std::min(int(y * 3), 2);
        Vec3 o{};
        o[row] = t;
        return o;
    }
    if (mode == 4) {
        float a = 2 * 3.14159265358979323846f * t;
        return s.colorSpace().fromXYZ *
               (s.fromReferenceWhite() * oklabInverse({.6f, .12f * std::cos(a), .12f * std::sin(a)}));
    }
    if (mode == 5)
        return s.colorSpace().fromXYZ * (s.fromReferenceWhite() * oklabInverse({.6f, .3f * t, 0}));
    if (mode == 6) {
        int col = std::min(int(t * 6), 5), row = std::min(int(y * 4), 3), n = row * 6 + col;
        Mat3 cat = adaptation(chartWhiteX, chartWhiteY, s.colorSpace().wx, s.colorSpace().wy);
        return s.colorSpace().fromXYZ * (cat * Vec3{chartXYZ[n][0], chartXYZ[n][1], chartXYZ[n][2]});
    }
    if (mode == 7)
        return {t, y, s.get("slice")};
    if (mode == 8)
        return rgb - reference;
    return s.apply(rgb);
}
struct Job {
    OfxImageEffectHandle effect;
    const Snapshot &snap;
    const ImageView *src;
    const ImageView &dst;
    const ImageView *ref;
    OfxRectI window;
    OfxRectD rod;
    int mode;
    double scaleX, scaleY, par;
    std::exception_ptr failure;
    std::mutex mutex;
    std::atomic<bool> failed{false};
};
void worker(unsigned int tid, unsigned int n, void *opaque) {
    auto &j = *static_cast<Job *>(opaque);
    try {
        int height = j.window.y2 - j.window.y1;
        int start = j.window.y1 + int(int64_t(height) * tid / n),
            end = j.window.y1 + int(int64_t(height) * (tid + 1) / n);
        for (int y = start; y < end; y++) {
            if (j.failed || fx->abort(j.effect))
                return;
            for (int x = j.window.x1; x < j.window.x2; x++) {
                if (j.snap.effectId() != Effect::Inspector) {
                    if (!j.src)
                        throw std::runtime_error("Missing Source");
                    if(j.snap.effectId()==Effect::Base && j.snap.get("localExposure")!=0) {
                        auto a=j.src->at(x,y),b=j.dst.at(x,y);if(!a || !b)throw std::runtime_error("Missing source/output pixel");
                        auto m=j.ref?j.ref->at(x,y):nullptr;
                        float coverage=j.ref?(m?(j.ref->components==1?m[0]:m[3]):0):1;
                        auto p=j.snap.pixel({a[0],a[1],a[2],j.src->components==4?a[3]:1},coverage);for(int c=0;c<j.dst.components;++c)b[c]=p[c];
                    } else renderWindow(j.snap, *j.src, j.dst, x, y, x + 1, y + 1);
                    continue;
                }
                auto a = j.src ? j.src->at(x, y) : nullptr;
                auto b = j.dst.at(x, y);
                auto r = j.ref ? j.ref->at(x, y) : nullptr;
                if (!b)
                    throw std::runtime_error("Render window outside output image");
                Vec3 rgb = a ? Vec3{a[0], a[1], a[2]} : Vec3{},
                     reference = r ? Vec3{r[0], r[1], r[2]} : Vec3{};
                if (j.mode == 0) {
                    if (!a)
                        throw std::runtime_error("Input mode requires Source");
                    std::memcpy(b, a, size_t(j.dst.components) * sizeof(float));
                    continue;
                }
                float u = float(((x + .5) * j.par / j.scaleX - j.rod.x1) / (j.rod.x2 - j.rod.x1)),
                      v = float(1 - ((y + .5) / j.scaleY - j.rod.y1) / (j.rod.y2 - j.rod.y1));
                Vec3 out = diagnostic(j.snap, j.mode, u, v, rgb, reference);
                if (!finite(out))
                    throw std::runtime_error("Diagnostic generated nonfinite output");
                b[0] = out.x;
                b[1] = out.y;
                b[2] = out.z;
                if (j.dst.components == 4)
                    b[3] = a && j.src->components == 4 ? a[3] : 1;
            }
        }
    } catch (...) {
        j.failed = true;
        std::lock_guard<std::mutex> lock(j.mutex);
        if (!j.failure)
            j.failure = std::current_exception();
    }
}
OfxStatus render(OfxImageEffectHandle h, OfxPropertySetHandle in) {
    auto &i = *instance(h);
    double t;
    checked(prop->propGetDouble(in, kOfxPropTime, 0, &t));
    int metal = 0;
    prop->propGetInt(in, kOfxImageEffectPropMetalEnabled, 0, &metal);
    if (metal)
        throw std::runtime_error("Metal is not accepted; CPU image buffers are required");
    auto v = values(i, t);
    Snapshot s(i.effect, v, inputInterpretation(i, v, i.sourceProps));
    OfxRectI window;
    checked(prop->propGetIntN(in, kOfxImageEffectPropRenderWindow, 4, &window.x1));
    Image dst(i.output, t);
    std::unique_ptr<Image> src, ref;
    if (connected(i.sourceProps))
        src = std::make_unique<Image>(i.source, t);
    if (src && src->view.components != dst.view.components)
        throw std::runtime_error("Source/output components differ");
    if (window.x1 < dst.view.x1 || window.x2 > dst.view.x2 || window.y1 < dst.view.y1 ||
        window.y2 > dst.view.y2)
        throw std::runtime_error("Invalid output render window");
    int mode = i.effect == Effect::Inspector ? int(s.get("mode")) : 0;
    if (i.effect == Effect::Inspector && !src && (mode == 0 || mode >= 8))
        throw std::runtime_error("Selected Inspector mode requires Source");
    if (mode == 8) {
        int connected = 0;
        if (i.referenceProps)
            prop->propGetInt(i.referenceProps, kOfxImageClipPropConnected, 0, &connected);
        if (!connected)
            throw std::runtime_error("Difference requires connected Reference clip");
        auto referenceSpace =
            interpret(int(s.get("interpretation")), inputInterpretation(i, v, i.referenceProps),
                      {s.get("rx"), s.get("ry"), s.get("gx"), s.get("gy"), s.get("bx"), s.get("by"),
                       s.get("wx"), s.get("wy")});
        if (referenceSpace.toXYZ.v != s.colorSpace().toXYZ.v)
            throw std::runtime_error("Reference color interpretation differs from Source");
        ref = std::make_unique<Image>(i.reference, t);
    }
    if(i.effect==Effect::Base && s.get("localExposure")!=0 && connected(i.referenceProps))ref=std::make_unique<Image>(i.reference,t,true);
    double scale[2] = {1, 1}, par = 1;
    prop->propGetDoubleN(in, kOfxImageEffectPropRenderScale, 2, scale);
    prop->propGetDouble(dst.handle, kOfxImagePropPixelAspectRatio, 0, &par);
    Job job{h,
            s,
            src ? &src->view : nullptr,
            dst.view,
            ref ? &ref->view : nullptr,
            window,
            dst.rod,
            mode,
            scale[0],
            scale[1],
            par,
            {},
            {},
            false};
    unsigned int cpus = 1;
    if (threads)
        threads->multiThreadNumCPUs(&cpus);
    cpus = std::max(1u, std::min({cpus, 32u, unsigned(std::max(window.y2 - window.y1, 1))}));
    if (threads && cpus > 1)
        checked(threads->multiThread(worker, cpus, &job));
    else
        worker(0, 1, &job);
    if (job.failure)
        std::rethrow_exception(job.failure);
    if (msg) {
        msg->clearPersistentMessage(h);
        if(i.effect==Effect::Palette) {
          bool risk=s.get("compression")>.7 || std::abs(s.get("separation"))>.7;
          for(auto family:{"Red","Yellow","Green","Cyan","Blue","Magenta"})risk|=std::abs(s.get(std::string("family")+family)*s.get("trajectory"))>30;
          if(risk)msg->setPersistentMessage(h,kOfxMessageWarning,"rendition.palette.geometry","%s","Strong Palette settings: possible Volume folds/poor conditioning. Controls remain unrestricted; inspect actual geometry in Inspector Lab. This threshold is a heuristic, not a measured fold diagnosis.");
        }
    }
    return kOfxStatOK;
}
OfxStatus action(Effect e, const char *act, const void *handle, OfxPropertySetHandle in,
                 OfxPropertySetHandle out) {
    try {
        if (std::getenv("RENDITION_TRACE"))
            std::fprintf(stderr, "Rendition action %s\n", act);
        if (std::strcmp(act, kOfxActionLoad) == 0) {
            suites();
            return kOfxStatOK;
        }
        if (std::strcmp(act, kOfxActionUnload) == 0)
            return kOfxStatOK;
        auto h = const_cast<OfxImageEffectHandle>(static_cast<const OfxImageEffectStruct *>(handle));
        if (std::strcmp(act, kOfxActionDescribe) == 0)
            return describe(e, h);
        if (std::strcmp(act, kOfxImageEffectActionDescribeInContext) == 0)
            return describeContext(e, h, in);
        if (std::strcmp(act, kOfxActionCreateInstance) == 0)
            return create(e, h);
        if (std::strcmp(act, kOfxActionDestroyInstance) == 0) {
            auto i = instance(h);
            OfxPropertySetHandle p;
            checked(fx->getPropertySet(h, &p));
            checked(prop->propSetPointer(p, kOfxPropInstanceData, 0, nullptr));
            delete i;
            return kOfxStatOK;
        }
        if (std::strcmp(act, kOfxImageEffectActionRender) == 0)
            return render(h, in);
        if (std::strcmp(act, kOfxImageEffectActionIsIdentity) == 0) {
            auto &i = *instance(h);
            double t;
            checked(prop->propGetDouble(in, kOfxPropTime, 0, &t));
            try {
                auto v = values(i, t);
                Snapshot s(e, v, inputInterpretation(i, v, i.sourceProps));
                // A successful semantic revalidation clears a previous recoverable render error.
                // Some hosts query identity before dispatching their deferred change notification.
                if (msg)
                    msg->clearPersistentMessage(h);
                if (s.isIdentity() && connected(i.sourceProps)) {
                    checked(prop->propSetString(out, kOfxPropName, 0, kOfxImageEffectSimpleSourceClipName));
                    checked(prop->propSetDouble(out, kOfxPropTime, 0, t));
                    return kOfxStatOK;
                }
            } catch (const std::invalid_argument &) {
                // Unknown semantics cannot bypass. Report validation errors during Render,
                // not during a host's cached identity/clip-information query.
                return kOfxStatReplyDefault;
            }
            return kOfxStatReplyDefault;
        }
        if (std::strcmp(act, kOfxImageEffectActionGetOutputColourspace) == 0) {
            auto &i = *instance(h);
            const char *tag = "OfxColourspace_Source";
            if (!connected(i.sourceProps)) {
                auto v = values(i, 0);
                int interpretation = int(v.at("interpretation"));
                if (interpretation == 0) {
                    const auto role = inputInterpretation(i, v, i.sourceProps);
                    if (role == "Linear Rec.2020") interpretation = 1;
                    else if (role == "ACEScg") interpretation = 2;
                    else if (role == "Linear Rec.709") interpretation = 3;
                }
                if (interpretation == 1)
                    tag = kOfxColourspaceLinRec2020;
                else if (interpretation == 2)
                    tag = kOfxColourspaceACEScg;
                else if (interpretation == 3)
                    tag = kOfxColourspaceLinRec709Srgb;
                else
                    return kOfxStatReplyDefault;
            }
            checked(prop->propSetString(out, kOfxImageClipPropColourspace, 0, tag));
            return kOfxStatOK;
        }
        if (std::strcmp(act, kOfxImageEffectActionGetRegionOfDefinition) == 0) {
            auto &i = *instance(h);
            double t = 0;
            prop->propGetDouble(in, kOfxPropTime, 0, &t);
            OfxRectD r{0, 0, 1920, 1080};
            if (connected(i.sourceProps))
                checked(fx->clipGetRegionOfDefinition(i.source, t, &r));
            checked(prop->propSetDoubleN(out, kOfxImageEffectPropRegionOfDefinition, 4, &r.x1));
            return kOfxStatOK;
        }
        if (std::strcmp(act, kOfxActionInstanceChanged) == 0) {
            auto &i=*instance(h);
            double time=0;prop->propGetDouble(in,kOfxPropTime,0,&time);
            if(str(in,kOfxPropName)=="enableFullControls" && str(in,kOfxPropChangeReason)==kOfxChangeUserEdited && i.effect!=Effect::Base) {
                OfxParamSetHandle set;fx->getParamSet(h,&set);
                param->paramEditBegin(set,"Enable full Rendition controls");
                param->paramSetValue(i.params.at("modelVersion"),2);
                param->paramEditEnd(set);
            }
            updatePresentation(i,time);
            if (msg) {
                auto status = msg->clearPersistentMessage(h);
                if (std::getenv("RENDITION_TRACE"))
                    std::fprintf(stderr, "Rendition clear message status=%d, changed=%s\n", status,
                                 str(in, kOfxPropName).c_str());
            }
            return kOfxStatOK;
        }
        return kOfxStatReplyDefault;
    } catch (const std::bad_alloc &) {
        return kOfxStatErrMemory;
    } catch (const std::exception &x) {
        if (prop)
            error(handle, x.what());
        return kOfxStatFailed;
    } catch (...) {
        if (prop)
            error(handle, "Unknown Rendition error");
        return kOfxStatFailed;
    }
}
template <int N>
OfxStatus entry(const char *a, const void *h, OfxPropertySetHandle i, OfxPropertySetHandle o) {
    return action(static_cast<Effect>(N), a, h, i, o);
}
OfxPlugin plugins[] = {
    {kOfxImageEffectPluginApi, 1, "org.gripcolor.rendition.Scene", 1, 0, setHost, entry<0>},
    {kOfxImageEffectPluginApi, 1, "org.gripcolor.rendition.Tone", 1, 0, setHost, entry<1>},
    {kOfxImageEffectPluginApi, 1, "org.gripcolor.rendition.Volume", 1, 0, setHost, entry<2>},
    {kOfxImageEffectPluginApi, 1, "org.gripcolor.rendition.Density", 1, 0, setHost, entry<3>},
    {kOfxImageEffectPluginApi, 1, "org.gripcolor.rendition.Crossover", 1, 0, setHost, entry<4>},
    {kOfxImageEffectPluginApi, 1, "org.gripcolor.rendition.Crosstalk", 1, 0, setHost, entry<5>},
    {kOfxImageEffectPluginApi, 1, "org.gripcolor.rendition.Strip", 1, 0, setHost, entry<6>},
    {kOfxImageEffectPluginApi, 1, "org.gripcolor.rendition.Inspector", 1, 0, setHost, entry<7>},
    {kOfxImageEffectPluginApi, 1, "org.gripcolor.rendition.Primaries", 1, 0, setHost, entry<8>},
    {kOfxImageEffectPluginApi, 1, "org.gripcolor.rendition.Base", 1, 0, setHost, entry<9>},
    {kOfxImageEffectPluginApi, 1, "org.gripcolor.rendition.Palette", 1, 0, setHost, entry<10>},
    {kOfxImageEffectPluginApi, 1, "org.gripcolor.rendition.Material", 1, 0, setHost, entry<11>}};
} // namespace
extern "C" __attribute__((visibility("default"))) int OfxGetNumberOfPlugins() {
    return 12;
}
extern "C" __attribute__((visibility("default"))) OfxPlugin *OfxGetPlugin(int n) {
    return n >= 0 && n < 12 ? &plugins[n] : nullptr;
}
