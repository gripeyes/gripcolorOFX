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
#include <thread>
#include "render_trace.hpp"
#ifndef RENDITION_HOST_FRAME_THREADING
#define RENDITION_HOST_FRAME_THREADING 1
#endif
#ifndef RENDITION_SUPPORTS_TILES
#define RENDITION_SUPPORTS_TILES 1
#endif
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
// Opt-in diagnostics. Extra read-only context/abort calls; no status recovery.
struct SuiteTraceContext {
    const char *action = "none", *subject = "none";
    const void *instance = nullptr;
    int effect = -1;
    unsigned depth = 0;
    double time = 0;
    bool timed = false;
};
thread_local SuiteTraceContext suiteTrace;
struct SuiteTraceAction {
    SuiteTraceContext previous = suiteTrace;
    SuiteTraceAction(Effect effect, const char *action, const void *instance) {
        suiteTrace = {action, "none", instance, int(effect), previous.depth + 1, 0, false};
    }
    ~SuiteTraceAction() { suiteTrace = previous; }
};
struct SuiteTraceSubject {
    SuiteTraceContext previous = suiteTrace;
    explicit SuiteTraceSubject(const char *subject) { suiteTrace.subject = subject; }
    SuiteTraceSubject(const char *subject, double time) : SuiteTraceSubject(subject) {
        suiteTrace.time = time;
        suiteTrace.timed = true;
    }
    ~SuiteTraceSubject() { suiteTrace = previous; }
};
void checkedStatus(OfxStatus s, const char *call, const char *file, int line) {
    if (s != kOfxStatOK) {
        if (std::getenv("RENDITION_SUITE_TRACE"))
            std::fprintf(stderr,
                         "Rendition suite failure: status=%d call=%s source=%s:%d "
                         "action=%s effect=%d instance=%p thread=%zu depth=%u render_id=%llu "
                         "subject=%s timed=%d time=%.17g\n",
                         s, call, file, line, suiteTrace.action, suiteTrace.effect,
                         suiteTrace.instance, std::hash<std::thread::id>{}(std::this_thread::get_id()),
                         suiteTrace.depth, (unsigned long long)(rendition::ofx_trace::current ? rendition::ofx_trace::current->renderId : 0),
                         suiteTrace.subject, int(suiteTrace.timed), suiteTrace.time);
        rendition::ofx_trace::dump();
        throw std::runtime_error("OFX suite operation failed: " + std::to_string(s));
    }
}
#define checked(call) checkedStatus((call), #call, __FILE__, __LINE__)
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
#include "persistent_state.hpp"
// Internal control flow, never a processing error or persistent host message.
struct RenderCancelled {};
[[noreturn]] void cancelRender() {
    if (rendition::ofx_trace::current) {
        auto &event = *rendition::ofx_trace::current;
        std::snprintf(event.stage, sizeof(event.stage), "render-cancelled");
        rendition::ofx_trace::record(event);
    }
    throw RenderCancelled{};
}
void checkRenderAbort(OfxImageEffectHandle effect) {
    if (effect && fx->abort && fx->abort(effect)) cancelRender();
}
enum class ImageAccess { Input, Output };
struct Image {
    OfxPropertySetHandle handle = nullptr;
    ImageView view{};
    OfxRectD rod{};
    Image(OfxImageClipHandle clip, double t, ImageAccess access, bool matte=false, const char *role="unspecified clip", OfxImageEffectHandle renderInstance=nullptr) {
        SuiteTraceSubject trace(role, t);
        const bool traced = rendition::ofx_trace::current != nullptr;
        rendition::ofx_trace::Event acquisition;
        const int abortBefore = renderInstance && fx->abort ? fx->abort(renderInstance) : -1;
        if (traced) acquisition = rendition::ofx_trace::acquisitionBefore(clip, role, fx, abortBefore);
        if (abortBefore > 0) cancelRender();
        const auto status = fx->clipGetImage(clip, t, nullptr, &handle);
        const int abortAfter = status != kOfxStatOK && renderInstance && fx->abort ? fx->abort(renderInstance) : -1;
        if (traced) rendition::ofx_trace::acquisitionAfter(acquisition, status, fx, abortAfter);
        if (status == kOfxStatFailed && abortAfter > 0) {
            handle = nullptr; // Failed fetch did not acquire an owned image.
            cancelRender();
        }
        if (status == kOfxStatFailed && access == ImageAccess::Input) {
            // The OFX contract defines unavailable input as black-transparent.
            // No image exists: do not inspect or release an invalid image handle.
            handle = nullptr;
            return;
        }
        checkedStatus(status, "fx->clipGetImage(clip, t, nullptr, &handle)", __FILE__, __LINE__);
        if (!handle) throw std::runtime_error("Host returned a null image handle after successful acquisition");
        try {
            // Constructor owns a successful handle before any cancellation/validation.
            checkRenderAbort(renderInstance);
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
    checked(prop->propSetInt(p, kOfxImageEffectPropSupportsTiles, 0, RENDITION_SUPPORTS_TILES));
    checked(prop->propSetInt(p, kOfxImageEffectPropSupportsMultiResolution, 0, 1));
    checked(prop->propSetInt(p, kOfxImageEffectPropTemporalClipAccess, 0, 0));
    checked(
        prop->propSetString(p, kOfxImageEffectPluginRenderThreadSafety, 0, kOfxImageEffectRenderFullySafe));
    checked(prop->propSetInt(p, kOfxImageEffectPluginPropHostFrameThreading, 0, RENDITION_HOST_FRAME_THREADING));
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
        checked(prop->propSetInt(p, kOfxImageEffectPropSupportsTiles, 0, RENDITION_SUPPORTS_TILES));
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
            checked(prop->propSetInt(p,kOfxImageEffectPropSupportsTiles,0,RENDITION_SUPPORTS_TILES));
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
    const bool nukePages=e>=Effect::Base && presentationUsesHostLinks(hostName);
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
#include "presentation.hpp"
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
    std::atomic<bool> cancelled{false};
};
void worker(unsigned int tid, unsigned int n, void *opaque) {
    auto &j = *static_cast<Job *>(opaque);
    try {
        int height = j.window.y2 - j.window.y1;
        int start = j.window.y1 + int(int64_t(height) * tid / n),
            end = j.window.y1 + int(int64_t(height) * (tid + 1) / n);
        for (int y = start; y < end; y++) {
            if (j.failed || j.cancelled) return;
            if (fx->abort(j.effect)) { j.cancelled = true; return; }
            for (int x = j.window.x1; x < j.window.x2; x++) {
                if ((int64_t(x) - j.window.x1) % 256 == 0) {
                    if (j.failed || j.cancelled) return;
                    if (fx->abort(j.effect)) { j.cancelled = true; return; }
                }
                if (j.snap.effectId() != Effect::Inspector) {
                    if (!j.src)
                        throw std::runtime_error("Missing Source");
                    if(!j.src->at(x,y) || (j.snap.effectId()==Effect::Base && j.snap.get("localExposure")!=0)) {
                        const float transparent[4] = {0,0,0,0};
                        const float *a=j.src->at(x,y);if(!a)a=transparent;
                        auto b=j.dst.at(x,y);if(!b)throw std::runtime_error("Missing output pixel");
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
                    if(a)std::memcpy(b, a, size_t(j.dst.components) * sizeof(float));
                    else std::fill_n(b,j.dst.components,0.f);
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
                    b[3] = a && j.src->components == 4 ? a[3] : j.src ? 0 : 1;
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
    SuiteTraceSubject trace("render", t);
    rendition::ofx_trace::RenderScope renderTrace(h, int(i.effect), t, in, prop);
    checkRenderAbort(h);
    int metal = 0;
    prop->propGetInt(in, kOfxImageEffectPropMetalEnabled, 0, &metal);
    if (metal)
        throw std::runtime_error("Metal is not accepted; CPU image buffers are required");
    OfxRectI window;
    checked(prop->propGetIntN(in, kOfxImageEffectPropRenderWindow, 4, &window.x1));
    // Acquire the host render target before parameter evaluation. In Nuke 17,
    // snapshot-first acquisition reproducibly loses Output during Viewer updates
    // even when abort() remains false. The snapshot and pixel equations are unchanged.
    Image dst(i.output, t, ImageAccess::Output, false, "Output", h);
    auto v = values(i, t);
    const int role = interpretationRole(i, v, t);
    Snapshot s(i.effect, v, inputInterpretation(v, i.sourceProps, role));
    std::unique_ptr<Image> src, ref;
    if (connected(i.sourceProps))
        src = std::make_unique<Image>(i.source, t, ImageAccess::Input, false, "Source", h);
    if(src && !src->handle)src->view.components=dst.view.components;
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
            interpret(int(s.get("interpretation")), inputInterpretation(v, i.referenceProps, role),
                      {s.get("rx"), s.get("ry"), s.get("gx"), s.get("gy"), s.get("bx"), s.get("by"),
                       s.get("wx"), s.get("wy")});
        if (referenceSpace.toXYZ.v != s.colorSpace().toXYZ.v)
            throw std::runtime_error("Reference color interpretation differs from Source");
        ref = std::make_unique<Image>(i.reference, t, ImageAccess::Input, false, "Reference", h);
    }
    if(i.effect==Effect::Base && s.get("localExposure")!=0 && connected(i.referenceProps))ref=std::make_unique<Image>(i.reference,t,ImageAccess::Input,true,"Matte",h);
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
        std::rethrow_exception(job.failure); // Genuine errors remain fatal.
    if (job.cancelled) cancelRender();
    checkRenderAbort(h);
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
    SuiteTraceAction trace(e, act, handle);
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
            SuiteTraceSubject trace("identity", t);
            try {
                auto v = values(i, t);
                const int role = interpretationRole(i, v, t);
                Snapshot s(e, v, inputInterpretation(v, i.sourceProps, role));
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
                    // This action has no time argument in the pinned colour API.
                    const auto role = inputInterpretation(v, i.sourceProps, interpretationRole(i,v,0));
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
    } catch (const RenderCancelled &) {
        return kOfxStatOK; // OFX interrupted-render pattern; RAII has unwound.
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
