// OFX-owned persistent handles and action-time evaluation. Included by the adapter.
#pragma once
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
        SuiteTraceSubject trace(d.id.c_str(), t);
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
int interpretationRole(Instance &i, const Values &v, double time) {
    if (int(v.at("interpretation")) == 0 && i.hostSceneLinear) {
        SuiteTraceSubject trace("hostSceneLinear", time);
        int role = 0;
        checked(param->paramGetValueAtTime(i.hostSceneLinear, time, &role));
        return role;
    }
    return 0;
}
std::string inputInterpretation(const Values &v, OfxPropertySetHandle clipProps, int role) {
    if (int(v.at("interpretation")) == 0) {
        if (role == 1) return {};
        if (role == 2) return "Linear Rec.2020";
        if (role == 3) return "ACEScg";
        if (role == 4) return "Linear Rec.709";
        if (role != 0) throw std::invalid_argument("Invalid scene_linear host interpretation");
    }
    return str(clipProps, kOfxImageClipPropColourspace);
}
